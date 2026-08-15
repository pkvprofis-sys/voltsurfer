"""Simulations-Engine: fährt die LP-Strategie über den gesamten Zeitraum.

Rolling Horizon: je Kalendertag wird ein Fenster von `horizon_days` Tagen
optimiert, committet wird nur der erste Tag, der SoC wird fortgeschrieben.
Ergebnisse werden per Config-Hash als Parquet gecacht (data_cache/).

Zusätzlich: klassische Eigenverbrauchs-Steuerung ohne Preisoptimierung
(greedy) als Vergleichsszenario "statischer Tarif + Speicher".
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from voltsurfer.config import BatteryConfig, SimConfig
from voltsurfer.data import prices
from voltsurfer.data.prices import CACHE_DIR
from voltsurfer.profiles.load import household_load_kw
from voltsurfer.profiles.pv import pv_generation_kw
from voltsurfer.sim import strategy
from voltsurfer.sim.strategy import DT_H


def build_inputs(sim: SimConfig, start: dt.date, end: dt.date) -> pd.DataFrame:
    """Preise, Last und PV auf gemeinsamem 15-min-Raster."""
    spot = prices.get_spot_prices_ct(start, end)
    df = pd.DataFrame({"spot_ct": spot})
    df["dyn_ct"] = sim.tariff.dynamic_price_ct(df["spot_ct"].to_numpy())
    df["load_kw"] = household_load_kw(df.index, sim.annual_consumption_kwh)
    df["pv_kw"] = pv_generation_kw(df.index, sim.pv_kwp)
    return df


def run_simulation(sim: SimConfig, inputs: pd.DataFrame, progress_cb=None) -> pd.DataFrame:
    """LP-Fahrweise über alle Tage; liefert inputs + Entscheidungsreihen."""
    # Fenstergrenzen über Kalendertag-Labels statt +24 h — an DST-Tagen hat ein Tag
    # 92 bzw. 100 Viertelstunden, absolute Zeitdeltas würden dort falsch schneiden.
    day_ids = inputs.index.normalize()
    days = day_ids.unique()
    out: list[pd.DataFrame] = []
    soc = 0.0  # Start: leerer Speicher (nutzbarer Bereich)

    for i, day in enumerate(days):
        win_mask = day_ids.isin(days[i : i + sim.horizon_days])
        win = inputs[win_mask]
        res = strategy.optimize_window(
            win["spot_ct"].to_numpy(),
            win["dyn_ct"].to_numpy(),
            win["load_kw"].to_numpy(),
            win["pv_kw"].to_numpy(),
            sim.battery,
            sim.tariff,
            sim.mode,
            soc_start_kwh=soc,
        )
        n = int((day_ids[win_mask] == day).sum())
        committed = pd.DataFrame({k: v[:n] for k, v in res.items()}, index=win.index[:n])
        out.append(committed)
        soc = float(committed["soc_kwh"].iloc[-1])
        if progress_cb:
            progress_cb((i + 1) / len(days))

    result = pd.concat(out)
    return inputs.join(result, how="inner")


def run_greedy_self_consumption(inputs: pd.DataFrame, battery: BatteryConfig) -> pd.DataFrame:
    """Klassischer Speicher ohne Preissignal: PV-Überschuss laden, Defizit entladen."""
    load = inputs["load_kw"].to_numpy()
    pv = inputs["pv_kw"].to_numpy()
    n = len(load)
    charge = np.zeros(n)
    discharge = np.zeros(n)
    soc_arr = np.zeros(n)
    soc = 0.0
    for t in range(n):
        surplus = pv[t] - load[t]
        if surplus > 0:
            headroom_kw = (battery.usable_kwh - soc) / (battery.eta_charge * DT_H)
            charge[t] = min(surplus, battery.charge_power_kw, headroom_kw)
            soc += charge[t] * battery.eta_charge * DT_H
        elif surplus < 0:
            avail_kw = soc * battery.eta_discharge / DT_H
            discharge[t] = min(-surplus, battery.discharge_power_kw, avail_kw)
            soc -= discharge[t] / battery.eta_discharge * DT_H
        soc_arr[t] = soc

    df = inputs.copy()
    df["charge_kw"] = charge
    df["discharge_kw"] = discharge
    df["soc_kwh"] = soc_arr
    df["grid_buy_kw"] = np.maximum(load + charge - pv - discharge, 0.0)
    df["sell_pv_kw"] = np.maximum(pv - load - charge + discharge, 0.0)
    df["sell_batt_kw"] = 0.0
    return df


def build_trade_inputs(sim: SimConfig, start: dt.date, end: dt.date) -> pd.DataFrame:
    """Inputs für den Trade-Modus: Spot, Preiskomponenten, Last (Haushalt + WP + EV + Geräte), PV."""
    from voltsurfer.profiles.ev import ev_charging_kw
    from voltsurfer.profiles.heatpump import PERSONS_TO_KWH, heatpump_load_kw, heatpump_load_kw_from_power
    from voltsurfer.sim.advisor import smart_runs_kw

    spot = prices.get_spot_prices_ct(start, end)
    df = pd.DataFrame({"spot_ct": spot})
    idx = df.index
    t = sim.tariff
    ne = t.netzentgelt_ct_series(idx)
    df["ne_ct"] = ne
    df["home_price_ct"] = t.home_price_ct(df["spot_ct"].to_numpy(), ne)
    df["charge_price_ct"] = t.charge_price_ct(df["spot_ct"].to_numpy(), ne, sim.speicherprivileg)
    df["batt_home_fee_ct"] = t.batt_to_home_fee_ct(ne, sim.speicherprivileg)
    annual_kwh = PERSONS_TO_KWH.get(sim.persons, sim.annual_consumption_kwh)
    df["base_load_kw"] = household_load_kw(idx, annual_kwh)
    if sim.hp_heat_kw > 0:
        df["hp_kw"] = heatpump_load_kw_from_power(idx, sim.hp_heat_kw, *sim.location)
    else:
        df["hp_kw"] = heatpump_load_kw(idx, sim.hp_area_m2, sim.hp_renovation, *sim.location)
    df["ev_kw"] = ev_charging_kw(df["spot_ct"], sim.ev_km_per_year, sim.ev_battery_kwh, sim.ev_kwh_per_100km)
    df["smart_kw"] = smart_runs_kw(df["spot_ct"], dict(sim.smart_runs_per_week))
    df["load_kw"] = df["base_load_kw"] + df["hp_kw"] + df["ev_kw"] + df["smart_kw"]
    df["pv_kw"] = pv_generation_kw(idx, sim.pv_kwp)
    return df


def run_trade_simulation(sim: SimConfig, inputs: pd.DataFrame, progress_cb=None) -> pd.DataFrame:
    """Trade-LP über alle Tage (Rolling Horizon wie run_simulation, DST-fest)."""
    day_ids = inputs.index.normalize()
    days = day_ids.unique()
    out: list[pd.DataFrame] = []
    soc = 0.0

    for i, day in enumerate(days):
        win_mask = day_ids.isin(days[i : i + sim.horizon_days])
        win = inputs[win_mask]
        res = strategy.optimize_trade_window(
            win["spot_ct"].to_numpy(),
            win["home_price_ct"].to_numpy(),
            win["charge_price_ct"].to_numpy(),
            win["batt_home_fee_ct"].to_numpy(),
            win["load_kw"].to_numpy(),
            sim.battery,
            soc_start_kwh=soc,
            pv_kw=win["pv_kw"].to_numpy() if "pv_kw" in win else None,
        )
        n = int((day_ids[win_mask] == day).sum())
        committed = pd.DataFrame({k: v[:n] for k, v in res.items()}, index=win.index[:n])
        out.append(committed)
        soc = float(committed["soc_kwh"].iloc[-1])
        if progress_cb:
            progress_cb((i + 1) / len(days))

    return inputs.join(pd.concat(out), how="inner")


def cached_trade_run(sim: SimConfig, start: dt.date, end: dt.date, progress_cb=None) -> pd.DataFrame:
    key = sim.cache_key(extra=f"{start}{end}trade-v2")
    path = CACHE_DIR / f"sim_{key}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    inputs = build_trade_inputs(sim, start, end)
    result = run_trade_simulation(sim, inputs, progress_cb)
    CACHE_DIR.mkdir(exist_ok=True)
    result.to_parquet(path)
    return result


def cached_run(sim: SimConfig, start: dt.date, end: dt.date, progress_cb=None) -> pd.DataFrame:
    """Simulationslauf mit Parquet-Cache über den Config-Hash."""
    key = sim.cache_key(extra=f"{start}{end}v2")
    path = CACHE_DIR / f"sim_{key}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    inputs = build_inputs(sim, start, end)
    result = run_simulation(sim, inputs, progress_cb)
    CACHE_DIR.mkdir(exist_ok=True)
    result.to_parquet(path)
    return result
