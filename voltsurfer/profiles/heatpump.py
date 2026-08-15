"""Wärmepumpen-Lastprofil aus echten historischen Temperaturen.

Modell (bewusst einfach und erklärbar):
- Jahres-Heizwärmebedarf = Wohnfläche × spezifischer Bedarf (Sanierungsstand)
- Verteilung über Heizgradtage (Heizgrenze 15 °C) der echten Tagesmitteltemperaturen
- Warmwasser: konstante Wärmemenge übers Jahr (Default 2.500 kWh/a)
- Strom = Wärme / COP(T); Luft-Wasser-COP linear mit Außentemperatur
  (≈ JAZ 3,3 bei 45 °C Vorlauf)
- Intraday: leichte Tag-Gewichtung (WP moduliert, nachts abgesenkt)
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from voltsurfer.data import weather

HEATING_LIMIT_C = 15.0
HOT_WATER_KWH_TH_PER_YEAR = 2500.0
# Faustformel: Jahres-Wärmemenge (inkl. WW) ≈ Heizleistung × Vollbenutzungsstunden
FULL_LOAD_HOURS = 1900.0

# kWh Heizwärme je m² und Jahr nach Sanierungsstand
SPECIFIC_HEAT_KWH_M2: dict[str, float] = {
    "Neubau (ab 2016)": 50.0,
    "Saniert": 100.0,
    "Teilsaniert": 130.0,
    "Altbau unsaniert": 160.0,
}

# Stundengewichte (24): nachts abgesenkt, tagsüber gleichmäßig
_HOURLY = np.array(
    [0.6, 0.6, 0.6, 0.6, 0.8, 1.0, 1.2, 1.2, 1.1, 1.1, 1.0, 1.0,
     1.0, 1.0, 1.0, 1.0, 1.1, 1.2, 1.2, 1.1, 1.0, 0.9, 0.7, 0.6]
)


def cop_air_water(temp_c: float | np.ndarray) -> np.ndarray:
    """Luft-Wasser-COP in Abhängigkeit der Tagesmitteltemperatur (eff. JAZ ≈ 3,8)."""
    return np.clip(3.3 + 0.08 * (np.asarray(temp_c, dtype=float) - 2.0), 1.8, 4.6)


def _electric_load(
    index: pd.DatetimeIndex, heating_kwh_th: float, ww_kwh_th: float, lat: float, lon: float
) -> pd.Series:
    """Kern: Jahres-Heizwärme + WW über Heizgradtage/COP auf das 15-min-Raster verteilen."""
    start, end = index[0].date(), index[-1].date()
    temp = weather.daily_mean_temp_c(start, end, lat, lon)

    # Heizgradtage je Tag; normiert über ein typisches Jahr (~2.900 Kd für Mitte-DE)
    hdd = (HEATING_LIMIT_C - temp).clip(lower=0.0)
    heat_per_hdd = heating_kwh_th / 2900.0

    daily_heat = hdd * heat_per_hdd + ww_kwh_th / 365.0
    daily_electric = daily_heat / cop_air_water(temp.to_numpy())

    # auf 15-min-Raster: Tageswert × Stundengewicht
    day_keys = index.tz_convert(weather.TZ).normalize()
    per_day = daily_electric.reindex(day_keys).to_numpy()
    hour_w = _HOURLY[index.hour.to_numpy()]
    hour_w_norm = hour_w / _HOURLY.mean()
    kw = per_day / 24.0 * hour_w_norm  # kWh/Tag -> mittlere kW, moduliert
    return pd.Series(kw, index=index, name="hp_kw")


def heatpump_load_kw(
    index: pd.DatetimeIndex,
    area_m2: float,
    renovation: str = "Saniert",
    lat: float = weather.DEFAULT_LAT,
    lon: float = weather.DEFAULT_LON,
) -> pd.Series:
    """WP-Strombedarf aus Wohnfläche + Sanierungsstand (0, wenn area_m2 <= 0)."""
    if area_m2 <= 0:
        return pd.Series(0.0, index=index, name="hp_kw")
    heating = area_m2 * SPECIFIC_HEAT_KWH_M2[renovation]
    return _electric_load(index, heating, HOT_WATER_KWH_TH_PER_YEAR, lat, lon)


def heatpump_load_kw_from_power(
    index: pd.DatetimeIndex,
    heat_kw: float,
    lat: float = weather.DEFAULT_LAT,
    lon: float = weather.DEFAULT_LON,
) -> pd.Series:
    """WP-Strombedarf aus der Heizleistung (kW) der Wärmepumpe.

    Jahres-Wärmemenge inkl. Warmwasser ≈ heat_kw × 1.900 Volllaststunden.
    """
    if heat_kw <= 0:
        return pd.Series(0.0, index=index, name="hp_kw")
    total_heat = heat_kw * FULL_LOAD_HOURS
    heating = max(total_heat - HOT_WATER_KWH_TH_PER_YEAR, 0.0)
    return _electric_load(index, heating, min(HOT_WATER_KWH_TH_PER_YEAR, total_heat), lat, lon)


def avg_electric_kwh_from_power(heat_kw: float) -> float:
    """Typischer Jahresstromverbrauch einer Luft-Wasser-WP mit dieser Heizleistung."""
    return heat_kw * FULL_LOAD_HOURS / 3.8  # effektive JAZ des Modells


def daily_electric_kwh_for_temp(
    temp_c: float, area_m2: float = 0.0, renovation: str = "Saniert", heat_kw: float = 0.0
) -> float:
    """Erwarteter WP-Tagesstrombedarf bei gegebener Tagesmitteltemperatur (für die Wetter-Vorschau)."""
    if heat_kw > 0:
        total = heat_kw * FULL_LOAD_HOURS
        heating = max(total - HOT_WATER_KWH_TH_PER_YEAR, 0.0)
        ww = min(HOT_WATER_KWH_TH_PER_YEAR, total)
    elif area_m2 > 0:
        heating = area_m2 * SPECIFIC_HEAT_KWH_M2[renovation]
        ww = HOT_WATER_KWH_TH_PER_YEAR
    else:
        return 0.0
    hdd = max(HEATING_LIMIT_C - temp_c, 0.0)
    daily_heat = hdd * heating / 2900.0 + ww / 365.0
    return float(daily_heat / cop_air_water(temp_c))


# Personen -> Jahres-Haushaltsstrom (ohne WP), intuitiv statt kWh-Eingabe
PERSONS_TO_KWH: dict[int, float] = {1: 1500.0, 2: 2500.0, 3: 3500.0, 4: 4000.0, 5: 4500.0}
