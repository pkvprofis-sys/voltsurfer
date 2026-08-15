"""Simulierte steuerbare Geräte + Platzierung in den günstigsten Stunden.

Wallbox: lädt Ziel-kWh je Nacht/Tag, teilbar auf beliebige Viertelstunden.
Wärmepumpe: Ziel-Laufzeit pro Tag, teilbar.
Waschmaschine: ein zusammenhängendes Programm (Block), nur im erlaubten Zeitfenster.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from voltsurfer.sim.strategy import DT_H


@dataclass
class DeviceConfig:
    key: str
    label: str
    icon: str
    power_kw: float
    enabled: bool = True
    target_kwh_per_day: float | None = None  # Wallbox: Energieziel
    runtime_h_per_day: float | None = None  # WP/WM: Laufzeitziel
    contiguous: bool = False  # WM: ein Block
    allowed_from: str = "00:00"
    allowed_to: str = "23:59"


# Hinweis: Die Wärmepumpe ist KEIN schaltbares Gerät — sie läuft witterungsgeführt
# als Grundlast (voltsurfer/profiles/heatpump.py) und wird unter „Haushalt" konfiguriert.
DEFAULT_DEVICES = [
    DeviceConfig("wallbox", "Wallbox (E-Auto)", "🚗", 11.0, True, target_kwh_per_day=15.0),
    DeviceConfig(
        "washer", "Waschmaschine", "🧺", 2.0, False,
        runtime_h_per_day=2.0, contiguous=True, allowed_from="08:00", allowed_to="22:00",
    ),
]


def _allowed_mask(idx: pd.DatetimeIndex, dev: DeviceConfig) -> np.ndarray:
    minutes = idx.hour * 60 + idx.minute
    s = _mins(dev.allowed_from)
    e = _mins(dev.allowed_to)
    return (minutes >= s) & (minutes < e) if s <= e else (minutes >= s) | (minutes < e)


def _mins(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def schedule_devices(prices_ct: pd.Series, devices: list[DeviceConfig]) -> pd.DataFrame:
    """Je Gerät eine kW-Spalte auf dem Preisindex; Laufzeiten in den Billigstunden."""
    idx = prices_ct.index
    out = pd.DataFrame(index=idx)
    for dev in devices:
        col = np.zeros(len(idx))
        if dev.enabled:
            for day in np.unique(idx.date):
                day_mask = (idx.date == day) & _allowed_mask(idx, dev)
                positions = np.flatnonzero(day_mask)
                if len(positions) == 0:
                    continue
                if dev.contiguous:
                    col = _place_block(col, prices_ct, positions, dev)
                else:
                    col = _place_split(col, prices_ct, positions, dev)
        out[dev.key] = col
    out["devices_total_kw"] = out.sum(axis=1)
    return out


def _slots_needed(dev: DeviceConfig) -> int:
    if dev.target_kwh_per_day is not None:
        return int(np.ceil(dev.target_kwh_per_day / (dev.power_kw * DT_H)))
    return int(np.ceil((dev.runtime_h_per_day or 0.0) / DT_H))


def _place_split(col: np.ndarray, prices: pd.Series, positions: np.ndarray, dev: DeviceConfig) -> np.ndarray:
    n = min(_slots_needed(dev), len(positions))
    cheapest = positions[np.argsort(prices.iloc[positions].to_numpy())[:n]]
    col[cheapest] = dev.power_kw
    return col


def _place_block(col: np.ndarray, prices: pd.Series, positions: np.ndarray, dev: DeviceConfig) -> np.ndarray:
    n = min(_slots_needed(dev), len(positions))
    if n == 0:
        return col
    # billigster zusammenhängender Block innerhalb der erlaubten Slots
    best_start, best_cost = None, np.inf
    price_arr = prices.to_numpy()
    for i in range(len(positions) - n + 1):
        window = positions[i : i + n]
        if window[-1] - window[0] != n - 1:  # Lücke im erlaubten Bereich
            continue
        cost = price_arr[window].sum()
        if cost < best_cost:
            best_start, best_cost = i, cost
    if best_start is not None:
        col[positions[best_start : best_start + n]] = dev.power_kw
    return col


def next_run_window(schedule: pd.DataFrame, key: str, now: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    """Nächstes geplantes Laufzeitfenster eines Geräts (für die Dashboard-Kachel)."""
    if key not in schedule.columns:
        return None
    active = schedule.index[(schedule[key] > 0) & (schedule.index >= now)]
    if len(active) == 0:
        return None
    start = active[0]
    step = pd.Timedelta(minutes=15)
    end = start
    for ts in active:
        if ts - end <= step:
            end = ts
        else:
            break
    return start, end + step
