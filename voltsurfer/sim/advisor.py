"""Bedarfsrechnung und Speicher-Empfehlung für den Kunden-Check.

Aus den Fragebogen-Antworten wird der Tagesstrombedarf aufgeschlüsselt und
daraus das passende VoltSurfer-Modell abgeleitet (beide laden/entladen 11 kW).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from voltsurfer.config import BATTERY_PRESETS, SimConfig
from voltsurfer.profiles.heatpump import PERSONS_TO_KWH, SPECIFIC_HEAT_KWH_M2, cop_air_water
from voltsurfer.sim.strategy import DT_H

# Smarte Verbraucher: (Label, kWh je Lauf, Dauer h, erlaubtes Fenster)
SMART_DEVICES: dict[str, dict] = {
    "washer": {"label": "🧺 Waschmaschine", "kwh_per_run": 1.0, "hours": 2.0, "window": (8, 22)},
    "dryer": {"label": "🌀 Trockner", "kwh_per_run": 2.5, "hours": 2.0, "window": (8, 22)},
    "dishwasher": {"label": "🍽️ Spülmaschine", "kwh_per_run": 1.2, "hours": 2.0, "window": (6, 23)},
}


def daily_demand_kwh(sim: SimConfig) -> dict[str, float]:
    """Tagesbedarf-Aufschlüsselung in kWh/Tag (Jahresmittel)."""
    base = PERSONS_TO_KWH.get(sim.persons, sim.annual_consumption_kwh) / 365.0

    hp = 0.0
    if sim.hp_heat_kw > 0:
        from voltsurfer.profiles.heatpump import avg_electric_kwh_from_power

        hp = avg_electric_kwh_from_power(sim.hp_heat_kw) / 365.0
    elif sim.hp_area_m2 > 0:
        annual_heat = sim.hp_area_m2 * SPECIFIC_HEAT_KWH_M2[sim.hp_renovation] + 2500.0
        hp = annual_heat / float(cop_air_water(6.0)) / 365.0  # Ø-Temperatur ~6 °C Heizsaison-gewichtet

    ev = sim.ev_km_per_year / 365.0 * sim.ev_kwh_per_100km / 100.0

    smart = sum(
        SMART_DEVICES[key]["kwh_per_run"] * runs / 7.0
        for key, runs in dict(sim.smart_runs_per_week).items()
        if key in SMART_DEVICES
    )
    total = base + hp + ev + smart
    return {"Haushalt": base, "Wärmepumpe": hp, "E-Auto": ev, "Smarte Geräte": smart, "Gesamt": total}


def recommend_battery(demand: dict[str, float], has_ev: bool) -> tuple[str, str]:
    """Empfohlenes Preset + Begründung."""
    presets = list(BATTERY_PRESETS)
    total = demand["Gesamt"]
    if total >= 12.0 or has_ev:
        reason = (
            f"Tagesbedarf ~{total:.0f} kWh"
            + (" plus E-Auto" if has_ev else "")
            + " — der 30-kWh-Speicher deckt den Tag aus einem einzigen Billigfenster"
            " und lässt zusätzlich Handelsvolumen für den Verkauf übrig."
        )
        return presets[1], reason
    reason = (
        f"Tagesbedarf ~{total:.0f} kWh — der 20-kWh-Speicher reicht für die Tagesdeckung"
        " plus tägliche Arbitrage; das größere Modell würde sich langsamer amortisieren."
    )
    return presets[0], reason


def smart_runs_kw(prices_ct: pd.Series, runs_per_week: dict[str, int]) -> pd.Series:
    """Smarte Geräteläufe in die günstigsten Slots legen (je Lauf ein Block im Tagesfenster).

    Läufe werden gleichmäßig über die Woche verteilt (jeder n-te Tag) und je
    Lauftag in den billigsten zusammenhängenden Block des erlaubten Fensters gelegt.
    """
    idx = prices_ct.index
    total = np.zeros(len(idx))
    if not runs_per_week:
        return pd.Series(total, index=idx, name="smart_kw")

    prices = prices_ct.to_numpy()
    days = pd.Index(idx.date)
    unique_days = days.unique()
    hours = idx.hour.to_numpy()

    for key, runs in runs_per_week.items():
        spec = SMART_DEVICES.get(key)
        if spec is None or runs <= 0:
            continue
        power_kw = spec["kwh_per_run"] / spec["hours"]
        slots = int(spec["hours"] / DT_H)
        lo, hi = spec["window"]
        # exakt `runs` Lauftage je 7-Tage-Woche, gleichmäßig verteilt
        run_days: list = []
        for w_start in range(0, len(unique_days), 7):
            week = unique_days[w_start : w_start + 7]
            picks = np.unique(np.linspace(0, len(week) - 1, min(runs, len(week)), dtype=int))
            run_days.extend(week[p] for p in picks)
        for day in run_days:
            day_mask = (days == day) & (hours >= lo) & (hours < hi)
            positions = np.flatnonzero(day_mask)
            if len(positions) < slots:
                continue
            # billigster zusammenhängender Block
            windows = np.lib.stride_tricks.sliding_window_view(prices[positions], slots)
            best = int(np.argmin(windows.sum(axis=1)))
            total[positions[best : best + slots]] += power_kw
    return pd.Series(total, index=idx, name="smart_kw")
