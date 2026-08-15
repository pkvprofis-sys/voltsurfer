"""E-Auto-KI-Ladeplaner: lädt nicht täglich, sondern in den günstigsten Fenstern.

Verfügbarkeit: werktags 18–08 Uhr zuhause, Wochenende ganztägig.
Wochenweise wird der Fahrbedarf (km/Jahr → kWh/Tag) in die billigsten erlaubten
Viertelstunden gelegt (Wallbox 11 kW). Ein großer Akku überbrückt mehrere Tage —
geladen wird dann nur in den 1–2 günstigsten Nächten der Woche. Fällt der SoC
unter die Reserve (30 %), wird notgeladen, egal was der Strom kostet.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from voltsurfer.sim.strategy import DT_H

RESERVE_FRAC = 0.30
DRIVE_HOUR = 17  # tägliche Fahrleistung wird um 17 Uhr verbucht


def availability_mask(index: pd.DatetimeIndex) -> np.ndarray:
    """True, wenn das Auto zuhause an der Wallbox steht."""
    weekend = index.dayofweek.to_numpy() >= 5
    hour = index.hour.to_numpy()
    night = (hour >= 18) | (hour < 8)
    return weekend | night


def ev_charging_kw(
    prices_ct: pd.Series,
    km_per_year: float,
    battery_kwh: float,
    kwh_per_100km: float = 18.0,
    wallbox_kw: float = 11.0,
) -> pd.Series:
    """Geplante EV-Ladeleistung (kW) je Viertelstunde auf dem Preisindex."""
    idx = prices_ct.index
    if km_per_year <= 0 or battery_kwh <= 0:
        return pd.Series(0.0, index=idx, name="ev_kw")

    daily_need = km_per_year / 365.0 * kwh_per_100km / 100.0
    prices = prices_ct.to_numpy()
    avail = availability_mask(idx)
    hours = idx.hour.to_numpy()
    week_keys = (idx.isocalendar().year * 100 + idx.isocalendar().week).to_numpy()

    # je Kalenderwoche: Preisschwelle = Preis des k-t günstigsten erlaubten Slots
    slots_per_week = int(np.ceil(daily_need * 7.0 / (wallbox_kw * DT_H)))
    threshold = np.full(len(idx), np.inf)
    for wk in np.unique(week_keys):
        mask = (week_keys == wk) & avail
        if not mask.any():
            continue
        wk_prices = np.sort(prices[mask])
        k = min(slots_per_week, len(wk_prices)) - 1
        threshold[week_keys == wk] = wk_prices[max(k, 0)]

    # Lade-Sessions mit Hysterese: erst wenn der Puffer zur Neige geht, wird eine
    # Session geöffnet und in den billigsten Slots bis zum Ziel gefüllt. Großer
    # Akku ⇒ seltene Sessions, kleiner Akku ⇒ häufige.
    reserve = battery_kwh * RESERVE_FRAC
    target = min(battery_kwh, reserve + 7.0 * daily_need)
    low_watermark = min(reserve + 1.5 * daily_need, battery_kwh * 0.8)
    soc = min(target, battery_kwh * 0.6)
    charge = np.zeros(len(idx))
    minutes = idx.minute.to_numpy()
    session = False

    for t in range(len(idx)):
        # tägliche Fahrt um 17:00 verbuchen
        if hours[t] == DRIVE_HOUR and minutes[t] == 0:
            soc = max(soc - daily_need, 0.0)
        if soc <= low_watermark:
            session = True
        if not avail[t] or soc >= battery_kwh - 1e-9:
            continue
        emergency = soc < reserve
        if emergency or (session and prices[t] <= threshold[t]):
            charge[t] = min(wallbox_kw, (battery_kwh - soc) / DT_H)
            soc += charge[t] * DT_H
            if soc >= target:
                session = False

    return pd.Series(charge, index=idx, name="ev_kw")


def ev_dumb_charging_kw(
    prices_ct: pd.Series,
    km_per_year: float,
    battery_kwh: float,
    kwh_per_100km: float = 18.0,
    wallbox_kw: float = 11.0,
) -> pd.Series:
    """Vergleich „dumm laden": jeden Tag um 18 Uhr einstecken, Tagesbedarf nachladen."""
    idx = prices_ct.index
    if km_per_year <= 0 or battery_kwh <= 0:
        return pd.Series(0.0, index=idx, name="ev_dumb_kw")
    daily_need = km_per_year / 365.0 * kwh_per_100km / 100.0
    charge = np.zeros(len(idx))
    hours = idx.hour.to_numpy()
    minutes = idx.minute.to_numpy()
    slots_needed = int(np.ceil(daily_need / (wallbox_kw * DT_H)))
    day_slot = hours * 4 + minutes // 15
    start_slot = 18 * 4
    in_window = (day_slot >= start_slot) & (day_slot < start_slot + slots_needed)
    charge[in_window] = min(wallbox_kw, daily_need / (slots_needed * DT_H))
    return pd.Series(charge, index=idx, name="ev_dumb_kw")


def ev_stats(charge: pd.Series, prices_ct: pd.Series) -> dict:
    active = charge > 0.05
    days_active = pd.Index(charge.index[active].date).nunique()
    total_days = pd.Index(charge.index.date).nunique()
    return {
        "kwh": float(charge.sum()) * DT_H,
        "charging_days": int(days_active),
        "total_days": int(total_days),
        "avg_price_ct": float(prices_ct[active].mean()) if active.any() else float("nan"),
    }
