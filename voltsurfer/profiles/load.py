"""Synthetisches Haushaltslastprofil (H0-artig) auf 15-min-Raster.

Tagesform mit Morgen- und Abendspitze (Werktag) bzw. flacherem, späterem
Verlauf (Wochenende), saisonale Modulation (Winter höher). Deterministisch,
skaliert exakt auf den vorgegebenen Jahresverbrauch.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Stunden-Stützstellen (relative Einheiten), per Interpolation aufs 15-min-Raster
_WEEKDAY = np.array(
    [0.35, 0.30, 0.28, 0.28, 0.30, 0.45, 0.75, 0.95, 0.85, 0.75, 0.70, 0.75,
     0.85, 0.75, 0.65, 0.65, 0.75, 1.00, 1.30, 1.40, 1.25, 1.00, 0.70, 0.45]
)
_WEEKEND = np.array(
    [0.40, 0.33, 0.30, 0.28, 0.30, 0.35, 0.50, 0.70, 0.95, 1.05, 1.05, 1.10,
     1.15, 1.00, 0.85, 0.80, 0.85, 1.05, 1.30, 1.35, 1.20, 1.00, 0.75, 0.50]
)
_HOURS = np.arange(24)


def household_load_kw(index: pd.DatetimeIndex, annual_kwh: float) -> pd.Series:
    """Lastprofil in kW für den gegebenen 15-min-Index, skaliert auf annual_kwh pro Jahr."""
    hour_frac = index.hour.to_numpy() + index.minute.to_numpy() / 60.0
    weekday = np.interp(hour_frac, _HOURS, _WEEKDAY, period=24)
    weekend = np.interp(hour_frac, _HOURS, _WEEKEND, period=24)
    shape = np.where(index.dayofweek.to_numpy() >= 5, weekend, weekday)

    doy = index.dayofyear.to_numpy()
    seasonal = 1.0 + 0.12 * np.cos(2 * np.pi * (doy - 20) / 365.0)
    shape = shape * seasonal

    dt_h = 0.25
    target_kwh = annual_kwh * len(index) * dt_h / 8760.0
    scale = target_kwh / (shape.sum() * dt_h)
    return pd.Series(shape * scale, index=index, name="load_kw")
