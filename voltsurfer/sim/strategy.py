"""LP-Optimierung der Speicherfahrweise (Formulierung nach EMHASS-Vorbild, PuLP).

Je Fenster (typ. 48 h) wird die Fahrweise kostenminimal geplant; committet wird
nur der erste Tag, der Rest dient als Horizont gegen Endeffekte. Die Day-Ahead-
Preise sind real am Vortag bekannt, daher ist die Preis-Voraussicht legitim;
Last und PV werden vereinfachend mit Ist-Werten gerechnet.

Betriebsmodi:
- "self": Speicher entlädt nur gegen den Haushaltsverbrauch (heutige Regulatorik,
  keine Rückspeisung von netzgeladenem Strom).
- "vpp":  Speicher darf zusätzlich zum Spotpreis ins Netz verkaufen
  (Direktvermarktungs-Szenario, virtuelles Kraftwerk).
"""
from __future__ import annotations

import numpy as np
import pulp

from voltsurfer.config import BatteryConfig, TariffConfig

DT_H = 0.25  # 15-min-Schritte

_solver_cache: pulp.LpSolver | None = None


def _solver() -> pulp.LpSolver:
    global _solver_cache
    if _solver_cache is None:
        try:
            highs = pulp.HiGHS(msg=False)
            _solver_cache = highs if highs.available() else pulp.PULP_CBC_CMD(msg=False)
        except Exception:
            _solver_cache = pulp.PULP_CBC_CMD(msg=False)
    return _solver_cache


def optimize_window(
    spot_ct: np.ndarray,
    dyn_ct: np.ndarray,
    load_kw: np.ndarray,
    pv_kw: np.ndarray,
    battery: BatteryConfig,
    tariff: TariffConfig,
    mode: str,
    soc_start_kwh: float,
    min_soc_kwh: float | np.ndarray = 0.0,
) -> dict[str, np.ndarray]:
    """Löst ein Fenster und liefert alle Entscheidungsreihen (kW bzw. kWh) zurück.

    min_soc_kwh: Puffer-Untergrenze für den SoC, skalar oder je Zeitschritt
    (z. B. KI-Reserveprofil). Liegt der Start-SoC darunter, wird die Grenze über
    eine Rampe angefahren (sonst wäre das LP unlösbar).
    """
    # Stale Zustände (z. B. nach Preset-Wechsel) physikalisch klammern
    soc_start_kwh = min(max(soc_start_kwh, 0.0), battery.usable_kwh)
    T = len(spot_ct)
    prob = pulp.LpProblem("voltsurfer_window", pulp.LpMinimize)

    min_soc = np.broadcast_to(np.asarray(min_soc_kwh, dtype=float), (T,))
    min_soc = np.minimum(min_soc, battery.usable_kwh)
    max_step_kwh = battery.charge_power_kw * battery.eta_charge * DT_H
    soc_lb = [
        min(float(min_soc[t]), soc_start_kwh + (t + 1) * max_step_kwh) for t in range(T)
    ]

    buy = [prob.add_variable(f"buy_{t}", lowBound=0) for t in range(T)]
    sell_pv = [prob.add_variable(f"sell_pv_{t}", lowBound=0) for t in range(T)]
    sell_batt = [prob.add_variable(f"sell_batt_{t}", lowBound=0) for t in range(T)]
    charge = [
        prob.add_variable(f"charge_{t}", lowBound=0, upBound=battery.charge_power_kw) for t in range(T)
    ]
    discharge = [
        prob.add_variable(f"discharge_{t}", lowBound=0, upBound=battery.discharge_power_kw)
        for t in range(T)
    ]
    soc = [
        prob.add_variable(f"soc_{t}", lowBound=soc_lb[t], upBound=battery.usable_kwh)
        for t in range(T)
    ]

    for t in range(T):
        # Energiebilanz am Hausanschluss (alles in kW)
        prob += (
            pv_kw[t] + discharge[t] + buy[t]
            == load_kw[t] + charge[t] + sell_pv[t] + sell_batt[t]
        )
        # PV-Einspeisung ist physisch durch die PV-Erzeugung begrenzt
        prob += sell_pv[t] <= pv_kw[t]
        if mode != "vpp":
            prob += sell_batt[t] == 0
        # SoC-Fortschreibung mit Lade-/Entladewirkungsgrad
        prev = soc_start_kwh if t == 0 else soc[t - 1]
        prob += soc[t] == prev + (
            charge[t] * battery.eta_charge - discharge[t] / battery.eta_discharge
        ) * DT_H

    # Kosten in ct: Netzbezug minus Einspeiseerlöse plus kalkulatorischer Verschleiß
    prob += pulp.lpSum(
        DT_H
        * (
            buy[t] * dyn_ct[t]
            - sell_pv[t] * max(tariff.feed_in_tariff_ct, 0.0 if mode != "vpp" else spot_ct[t])
            - sell_batt[t] * spot_ct[t]
            + discharge[t] * battery.degradation_cost_ct_kwh
        )
        for t in range(T)
    )

    status = prob.solve(_solver())
    if pulp.LpStatus[status] != "Optimal":
        raise RuntimeError(f"LP nicht optimal gelöst: {pulp.LpStatus[status]}")

    def vals(v):
        return np.array([v[t].value() for t in range(T)])

    return {
        "grid_buy_kw": vals(buy),
        "sell_pv_kw": vals(sell_pv),
        "sell_batt_kw": vals(sell_batt),
        "charge_kw": vals(charge),
        "discharge_kw": vals(discharge),
        "soc_kwh": vals(soc),
    }


def optimize_trade_window(
    spot_ct: np.ndarray,
    home_price_ct: np.ndarray,
    charge_price_ct: np.ndarray,
    batt_home_fee_ct: np.ndarray,
    load_kw: np.ndarray,
    battery: BatteryConfig,
    soc_start_kwh: float,
    min_soc_kwh: float | np.ndarray = 0.0,
    sell_enabled: bool = True,
    pv_kw: np.ndarray | None = None,
    pv_feed_ct: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Graustrom-Arbitrage, optional mit PV (Speicherprivileg-Kostenmodell).

    Kostenterme je kWh:
      Netz→Haushalt direkt: home_price_ct(t)
      Netz→Speicher:        charge_price_ct(t)  (Privileg: Spot+Aufschlag; sonst Endpreis)
      PV→Speicher:          0 (Opportunität = entgangener Einspeiseerlös, löst das LP)
      Speicher→Haushalt:    batt_home_fee_ct(t) (nachgelagerter Abgabenblock; konservativ 0)
      Speicher→Netz:        Erlös spot_ct(t);  PV→Netz: Erlös pv_feed_ct(t)
      plus kalkulatorischer Verschleiß je entladener kWh.
    """
    # Stale Zustände (z. B. nach Preset-Wechsel) physikalisch klammern
    soc_start_kwh = min(max(soc_start_kwh, 0.0), battery.usable_kwh)
    T = len(spot_ct)
    has_pv = pv_kw is not None and np.asarray(pv_kw).max() > 1e-9
    pv = np.zeros(T) if pv_kw is None else np.asarray(pv_kw, dtype=float)
    pv_feed = spot_ct if pv_feed_ct is None else pv_feed_ct
    prob = pulp.LpProblem("voltsurfer_trade", pulp.LpMinimize)

    min_soc = np.broadcast_to(np.asarray(min_soc_kwh, dtype=float), (T,))
    min_soc = np.minimum(min_soc, battery.usable_kwh)
    max_step_kwh = battery.charge_power_kw * battery.eta_charge * DT_H
    soc_lb = [min(float(min_soc[t]), soc_start_kwh + (t + 1) * max_step_kwh) for t in range(T)]

    buy_home = [prob.add_variable(f"buyh_{t}", lowBound=0) for t in range(T)]
    grid_charge = [prob.add_variable(f"gch_{t}", lowBound=0, upBound=battery.charge_power_kw) for t in range(T)]
    batt_home = [prob.add_variable(f"bh_{t}", lowBound=0) for t in range(T)]
    sell = [
        prob.add_variable(f"sell_{t}", lowBound=0, upBound=battery.discharge_power_kw if sell_enabled else 0)
        for t in range(T)
    ]
    soc = [prob.add_variable(f"soc_{t}", lowBound=soc_lb[t], upBound=battery.usable_kwh) for t in range(T)]
    if has_pv:
        pv_home = [prob.add_variable(f"pvh_{t}", lowBound=0) for t in range(T)]
        pv_charge = [prob.add_variable(f"pvc_{t}", lowBound=0) for t in range(T)]
        pv_sell = [prob.add_variable(f"pvs_{t}", lowBound=0) for t in range(T)]
    else:
        pv_home = pv_charge = pv_sell = [0.0] * T

    for t in range(T):
        # Haushaltslast: direkt, aus dem Speicher oder aus PV
        prob += buy_home[t] + batt_home[t] + pv_home[t] == load_kw[t]
        if has_pv:
            # PV-Erzeugung vollständig verteilen
            prob += pv_home[t] + pv_charge[t] + pv_sell[t] == pv[t]
            prob += grid_charge[t] + pv_charge[t] <= battery.charge_power_kw
        # Entladeleistung ist gemeinsames Limit für Haushalt + Verkauf
        prob += batt_home[t] + sell[t] <= battery.discharge_power_kw
        prev = soc_start_kwh if t == 0 else soc[t - 1]
        prob += soc[t] == prev + (
            (grid_charge[t] + pv_charge[t]) * battery.eta_charge
            - (batt_home[t] + sell[t]) / battery.eta_discharge
        ) * DT_H

    prob += pulp.lpSum(
        DT_H
        * (
            buy_home[t] * home_price_ct[t]
            + grid_charge[t] * charge_price_ct[t]
            + batt_home[t] * batt_home_fee_ct[t]
            - sell[t] * spot_ct[t]
            - (pv_sell[t] * pv_feed[t] if has_pv else 0.0)
            + (batt_home[t] + sell[t]) * battery.degradation_cost_ct_kwh
        )
        for t in range(T)
    )

    status = prob.solve(_solver())
    if pulp.LpStatus[status] != "Optimal":
        raise RuntimeError(f"Trade-LP nicht optimal gelöst: {pulp.LpStatus[status]}")

    def vals(v):
        return np.array([v[t].value() if hasattr(v[t], "value") else v[t] for t in range(T)])

    batt_home_v = vals(batt_home)
    sell_v = vals(sell)
    grid_charge_v = vals(grid_charge)
    pv_charge_v = vals(pv_charge)
    return {
        "grid_buy_kw": vals(buy_home) + grid_charge_v,
        "buy_home_kw": vals(buy_home),
        "grid_charge_kw": grid_charge_v,
        "pv_charge_kw": pv_charge_v,
        "pv_home_kw": vals(pv_home),
        "sell_pv_kw": vals(pv_sell),
        "charge_kw": grid_charge_v + pv_charge_v,
        "batt_home_kw": batt_home_v,
        "sell_batt_kw": sell_v,
        "discharge_kw": batt_home_v + sell_v,
        "soc_kwh": vals(soc),
    }
