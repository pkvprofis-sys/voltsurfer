"""Vier Betriebsstrategien für den Live-Planer.

Alle Strategien liefern denselben Plan-DataFrame auf 15-min-Raster mit den
Spalten: price_ct (Spot), dyn_ct, load_kw, pv_kw, charge_kw, discharge_kw,
grid_buy_kw, sell_pv_kw, sell_batt_kw, soc_kwh.

- auto:   LP-Kostenoptimierung (sim/strategy.py) mit SoC-Puffer
- top_n:  regelbasiert — N günstigste Stunden laden, M teuerste entladen
- manual: feste tägliche Lade-/Entlade-/Sperrfenster des Nutzers
- ai:     LP mit gelerntem Tagesverbrauch als abfallendem Reserveprofil;
          erst nach der Lernphase wird Verkauf freigegeben
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from voltsurfer.config import BatteryConfig, TariffConfig
from voltsurfer.sim.strategy import DT_H, optimize_trade_window


@dataclass
class ManualWindow:
    start: str = "01:00"  # "HH:MM", täglich wiederkehrend
    end: str = "05:00"
    action: str = "laden"  # laden | entladen | gesperrt


@dataclass
class StrategySettings:
    name: str = "auto"  # auto | top_n | manual | ai
    vpp_enabled: bool = True
    buffer_frac: float = 0.20  # Puffer, Anteil der Nutzkapazität
    top_n_charge_hours: int = 3
    top_n_discharge_hours: int = 4
    manual_windows: list[ManualWindow] = field(default_factory=lambda: [ManualWindow()])
    learning_days: int = 10
    learned_daily_kwh: float | None = None  # None = Lernphase läuft noch
    speicherprivileg: bool = True  # Erlösmodell für die LP-Strategien (trade)


def build_plan(
    prices_ct: pd.Series,
    load_kw: pd.Series,
    pv_kw: pd.Series,
    battery: BatteryConfig,
    tariff: TariffConfig,
    settings: StrategySettings,
    soc_start_kwh: float,
) -> pd.DataFrame:
    idx = prices_ct.index
    load = load_kw.reindex(idx).ffill().fillna(0.0).to_numpy()
    pv = pv_kw.reindex(idx).ffill().fillna(0.0).to_numpy()
    spot = prices_ct.to_numpy()
    buffer_kwh = settings.buffer_frac * battery.usable_kwh

    # Stale Zustände klammern; LP-Fehler dürfen den Live-Betrieb nie crashen
    soc_start_kwh = min(max(soc_start_kwh, 0.0), battery.usable_kwh)
    lp_fallback = False

    if settings.name == "top_n":
        res = _rule_plan(idx, spot, load, pv, battery, settings, soc_start_kwh, buffer_kwh, *_top_n_masks(idx, spot, settings))
    elif settings.name == "manual":
        res = _rule_plan(idx, spot, load, pv, battery, settings, soc_start_kwh, buffer_kwh, *_manual_masks(idx, settings))
    elif settings.name in ("auto", "ai"):
        try:
            if settings.name == "auto":
                res = _lp_plan(idx, spot, load, pv, battery, tariff, settings, soc_start_kwh, buffer_kwh)
            else:
                res = _ai_plan(idx, spot, load, pv, battery, tariff, settings, soc_start_kwh, buffer_kwh)
        except RuntimeError:
            try:  # Retry: nur Puffer als Untergrenze, ohne KI-Reserveprofil
                res = _lp_plan(idx, spot, load, pv, battery, tariff, settings, soc_start_kwh, buffer_kwh)
            except RuntimeError:  # letzte Rettung: regelbasierter Plan
                res = _rule_plan(idx, spot, load, pv, battery, settings, soc_start_kwh, buffer_kwh, *_top_n_masks(idx, spot, settings))
                lp_fallback = True
    else:
        raise ValueError(f"Unbekannte Strategie: {settings.name}")

    plan = pd.DataFrame(res, index=idx)
    plan["price_ct"] = spot
    plan["dyn_ct"] = tariff.dynamic_price_ct(spot)
    plan["load_kw"] = load
    plan["pv_kw"] = pv
    plan.attrs["lp_fallback"] = lp_fallback
    return plan


# ------------------------------------------------------------------ LP-Varianten
def _lp_plan(idx, spot, load, pv, battery, tariff, settings, soc0, buffer_kwh, min_soc=None):
    """Trade-LP (Graustrom-Modell): PV spielt im Produkt keine Rolle mehr."""
    ne = tariff.netzentgelt_ct_series(idx)
    res = optimize_trade_window(
        spot,
        tariff.home_price_ct(spot, ne),
        tariff.charge_price_ct(spot, ne, settings.speicherprivileg),
        tariff.batt_to_home_fee_ct(ne, settings.speicherprivileg),
        load,
        battery,
        soc_start_kwh=soc0,
        min_soc_kwh=buffer_kwh if min_soc is None else min_soc,
        sell_enabled=settings.vpp_enabled,
    )
    res["sell_pv_kw"] = np.zeros(len(idx))
    return res


def _ai_plan(idx, spot, load, pv, battery, tariff, settings, soc0, buffer_kwh):
    if settings.learned_daily_kwh is None:
        # Lernphase: konservativ, kein Verkauf, nur Puffer halten
        conservative = StrategySettings(**{**settings.__dict__, "vpp_enabled": False})
        return _lp_plan(idx, spot, load, pv, battery, tariff, conservative, soc0, buffer_kwh)

    # Reserveprofil: Puffer + Resttagesbedarf (fällt über den Tag auf 0)
    day_frac = (idx.hour * 60 + idx.minute).to_numpy() / (24 * 60)
    reserve = buffer_kwh + settings.learned_daily_kwh * (1.0 - day_frac)
    min_soc = np.minimum(reserve, battery.usable_kwh)
    return _lp_plan(idx, spot, load, pv, battery, tariff, settings, soc0, buffer_kwh, min_soc=min_soc)


# ------------------------------------------------------------------ Regelbasiert
def _top_n_masks(idx, spot, settings) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Lade-/Entlade-/Sperrmasken: je Kalendertag N günstigste bzw. M teuerste Stunden."""
    df = pd.DataFrame({"spot": spot}, index=idx)
    hourly = df["spot"].groupby([idx.date, idx.hour]).transform("mean")
    charge = np.zeros(len(idx), dtype=bool)
    discharge = np.zeros(len(idx), dtype=bool)
    for day in np.unique(idx.date):
        day_mask = idx.date == day
        hours = pd.Series(hourly[day_mask], index=idx[day_mask])
        by_hour = hours.groupby(hours.index.hour).first().sort_values()
        cheap = set(by_hour.index[: settings.top_n_charge_hours])
        expensive = set(by_hour.index[-settings.top_n_discharge_hours :])
        charge |= day_mask & np.isin(idx.hour, list(cheap))
        discharge |= day_mask & np.isin(idx.hour, list(expensive))
    discharge &= ~charge
    return charge, discharge, np.zeros(len(idx), dtype=bool)


def _manual_masks(idx, settings) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    charge = np.zeros(len(idx), dtype=bool)
    discharge = np.zeros(len(idx), dtype=bool)
    blocked = np.zeros(len(idx), dtype=bool)
    minutes = idx.hour * 60 + idx.minute
    for w in settings.manual_windows:
        try:
            s = _to_minutes(w.start)
            e = _to_minutes(w.end)
        except (ValueError, AttributeError):
            continue
        in_window = (minutes >= s) & (minutes < e) if s <= e else (minutes >= s) | (minutes < e)
        action = w.action.lower()
        if action == "laden":
            charge |= in_window
        elif action == "entladen":
            discharge |= in_window
        else:
            blocked |= in_window
    charge &= ~blocked
    discharge &= ~blocked & ~charge
    return charge, discharge, blocked


def _to_minutes(hhmm: str) -> int:
    h, m = hhmm.strip().split(":")
    return int(h) * 60 + int(m)


def _rule_plan(idx, spot, load, pv, battery, settings, soc0, buffer_kwh, charge_mask, discharge_mask, blocked_mask):
    """Vorwärtssimulation der Regelstrategien.

    Immer aktiv: PV-Überschuss lädt den Speicher (außer gesperrt), Defizit wird
    in Entladefenstern (top_n) bzw. außerhalb von Sperrfenstern (manual) aus dem
    Speicher gedeckt. Verkauf nur im VPP-Modus in Entladefenstern, nie unter Puffer.
    """
    n = len(idx)
    charge = np.zeros(n)
    discharge = np.zeros(n)
    grid_buy = np.zeros(n)
    sell_pv = np.zeros(n)
    sell_batt = np.zeros(n)
    soc_arr = np.zeros(n)
    soc = soc0
    cover_load_outside = settings.name == "manual"  # manual: Haushaltsdeckung ist Default

    for t in range(n):
        surplus = pv[t] - load[t]
        headroom_kw = max((battery.usable_kwh - soc) / (battery.eta_charge * DT_H), 0.0)
        avail_above_buffer = max((soc - buffer_kwh) * battery.eta_discharge / DT_H, 0.0)

        if blocked_mask[t]:
            if surplus > 0:
                sell_pv[t] = surplus
            else:
                grid_buy[t] = -surplus
        elif charge_mask[t]:
            charge[t] = min(battery.charge_power_kw, headroom_kw)
            grid_buy[t] = max(load[t] + charge[t] - pv[t], 0.0)
            sell_pv[t] = max(pv[t] - load[t] - charge[t], 0.0)
        elif discharge_mask[t]:
            want = battery.discharge_power_kw if settings.vpp_enabled else max(-surplus, 0.0)
            discharge[t] = min(want, battery.discharge_power_kw, avail_above_buffer)
            balance = pv[t] + discharge[t] - load[t]
            if balance >= 0:
                sell_pv[t] = min(balance, max(pv[t] - load[t], 0.0))
                sell_batt[t] = balance - sell_pv[t]
            else:
                grid_buy[t] = -balance
        else:
            if surplus > 0:
                charge[t] = min(surplus, battery.charge_power_kw, headroom_kw)
                sell_pv[t] = surplus - charge[t]
            else:
                deficit = -surplus
                if cover_load_outside:
                    discharge[t] = min(deficit, battery.discharge_power_kw, avail_above_buffer)
                grid_buy[t] = deficit - discharge[t]

        soc += (charge[t] * battery.eta_charge - discharge[t] / battery.eta_discharge) * DT_H
        soc = min(max(soc, 0.0), battery.usable_kwh)
        soc_arr[t] = soc

    return {
        "charge_kw": charge,
        "discharge_kw": discharge,
        "grid_buy_kw": grid_buy,
        "sell_pv_kw": sell_pv,
        "sell_batt_kw": sell_batt,
        "soc_kwh": soc_arr,
    }
