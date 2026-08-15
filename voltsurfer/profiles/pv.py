"""PV-Erzeugungsprofil aus der nationalen Solarerzeugung (Energy-Charts).

Kapazitätsfaktor = nationale PV-Erzeugung / installierte Leistung des Monats.
Dadurch ist das Profil wetterecht und korreliert real mit den Börsenpreisen
(PV-Überschuss fällt in Billigstunden). `adjust` kalibriert den Flotten-Mittelwert
auf eine gut ausgerichtete Dachanlage (Default 1.05).
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from voltsurfer.data import prices

# Kalibrierung Flotten-Mittelwert -> gut ausgerichtete Dachanlage
FLEET_ADJUST = 1.05


def pv_generation_kw(index: pd.DatetimeIndex, kwp: float, adjust: float = FLEET_ADJUST) -> pd.Series:
    """PV-Leistung in kW für eine Anlage mit kwp Spitzenleistung auf dem gegebenen Index."""
    if kwp <= 0:
        return pd.Series(0.0, index=index, name="pv_kw")

    start, end = index[0].date(), index[-1].date()
    solar_mw = prices.get_solar_generation_mw(start, end).reindex(index).ffill().fillna(0.0)

    installed_gw = prices.get_installed_solar_gw()
    monthly = installed_gw.reindex(index, method="ffill")
    # falls der Index vor der ersten/nach der letzten Monatsangabe liegt
    monthly = monthly.bfill().ffill()

    cf = (solar_mw / (monthly * 1000.0)).clip(lower=0.0, upper=1.0)
    return (cf * kwp * adjust).rename("pv_kw")
