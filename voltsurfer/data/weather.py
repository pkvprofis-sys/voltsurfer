"""Historische Tagesmittel-Temperaturen von Open-Meteo (Archiv-API, kein Key).

Grundlage für das Wärmepumpen-Lastprofil: Heizgradtage und COP hängen an der
Außentemperatur. Cache als Parquet je Standort-Jahr; die letzten Tage werden
höchstens einmal täglich neu geholt.
"""
from __future__ import annotations

import datetime as dt
import time

import pandas as pd
import requests

from voltsurfer.data.prices import CACHE_DIR, TZ

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
DEFAULT_LAT, DEFAULT_LON = 51.0, 9.0  # Mitte Deutschlands

# WMO-Wettercode -> (Emoji, Kurztext)
WMO_CODES: dict[int, tuple[str, str]] = {
    0: ("☀️", "klar"), 1: ("🌤️", "überwiegend klar"), 2: ("⛅", "teils bewölkt"), 3: ("☁️", "bedeckt"),
    45: ("🌫️", "Nebel"), 48: ("🌫️", "Reifnebel"),
    51: ("🌦️", "leichter Niesel"), 53: ("🌦️", "Niesel"), 55: ("🌧️", "starker Niesel"),
    61: ("🌧️", "leichter Regen"), 63: ("🌧️", "Regen"), 65: ("🌧️", "starker Regen"),
    66: ("🌧️", "gefr. Regen"), 67: ("🌧️", "gefr. Regen"),
    71: ("🌨️", "leichter Schnee"), 73: ("❄️", "Schnee"), 75: ("❄️", "starker Schnee"), 77: ("❄️", "Schneegriesel"),
    80: ("🌦️", "Schauer"), 81: ("🌧️", "Schauer"), 82: ("⛈️", "starke Schauer"),
    85: ("🌨️", "Schneeschauer"), 86: ("❄️", "Schneeschauer"),
    95: ("⛈️", "Gewitter"), 96: ("⛈️", "Gewitter m. Hagel"), 99: ("⛈️", "Gewitter m. Hagel"),
}


def wmo_icon(code: int) -> tuple[str, str]:
    return WMO_CODES.get(int(code), ("🌡️", f"Code {code}"))


def get_forecast(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON) -> dict:
    """Aktuelles Wetter + 5-Tage-Vorhersage (Open-Meteo, kein Key, 30-min-Cache).

    Rückgabe: {"current": {...}, "daily": [ {date, tmin, tmax, tmean, code, icon,
    text, precip_mm, sun_h}, ... ]}
    """
    import json

    CACHE_DIR.mkdir(exist_ok=True)
    path = CACHE_DIR / f"forecast_{lat:.1f}_{lon:.1f}.json"
    if path.exists() and time.time() - path.stat().st_mtime < 1800:
        return json.loads(path.read_text(encoding="utf-8"))

    try:
        resp = requests.get(
            FORECAST_URL,
            params={
                "latitude": lat, "longitude": lon,
                "current": "temperature_2m,weather_code,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum,sunshine_duration",
                "timezone": "Europe/Berlin", "forecast_days": 5,
            },
            timeout=15,
        )
        resp.raise_for_status()
        js = resp.json()
    except requests.RequestException:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        raise

    cur = js["current"]
    icon, text = wmo_icon(cur["weather_code"])
    daily = []
    d = js["daily"]
    for i, date in enumerate(d["time"]):
        di, dt_text = wmo_icon(d["weather_code"][i])
        daily.append({
            "date": date,
            "tmin": d["temperature_2m_min"][i],
            "tmax": d["temperature_2m_max"][i],
            "tmean": (d["temperature_2m_min"][i] + d["temperature_2m_max"][i]) / 2.0,
            "code": d["weather_code"][i], "icon": di, "text": dt_text,
            "precip_mm": d["precipitation_sum"][i],
            "sun_h": (d["sunshine_duration"][i] or 0.0) / 3600.0,
        })
    result = {
        "current": {
            "temp_c": cur["temperature_2m"], "code": cur["weather_code"],
            "icon": icon, "text": text, "wind_kmh": cur["wind_speed_10m"],
        },
        "daily": daily,
    }
    path.write_text(json.dumps(result), encoding="utf-8")
    return result


def _fetch_year(year: int, lat: float, lon: float) -> pd.Series:
    end = min(dt.date(year, 12, 31), dt.date.today())
    resp = requests.get(
        ARCHIVE_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "start_date": f"{year}-01-01",
            "end_date": end.isoformat(),
            "daily": "temperature_2m_mean",
            "timezone": "Europe/Berlin",
        },
        timeout=60,
    )
    resp.raise_for_status()
    js = resp.json()["daily"]
    idx = pd.to_datetime(js["time"]).tz_localize(TZ)
    return pd.Series(js["temperature_2m_mean"], index=idx, name="temp_c", dtype="float64").dropna()


def daily_mean_temp_c(
    start: dt.date, end: dt.date, lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON
) -> pd.Series:
    """Tagesmittel-Temperatur (°C) je Kalendertag, Index tz-aware Europe/Berlin."""
    CACHE_DIR.mkdir(exist_ok=True)
    parts = []
    for year in range(start.year, end.year + 1):
        path = CACHE_DIR / f"temp_{lat:.1f}_{lon:.1f}_{year}.parquet"
        is_current = year == dt.date.today().year
        fresh = path.exists() and (not is_current or time.time() - path.stat().st_mtime < 86400)
        if fresh:
            parts.append(pd.read_parquet(path)["temp_c"])
            continue
        try:
            s = _fetch_year(year, lat, lon)
            s.to_frame().to_parquet(path)
            parts.append(s)
        except requests.RequestException:
            if path.exists():
                parts.append(pd.read_parquet(path)["temp_c"])
            else:
                raise
    temp = pd.concat(parts)
    temp = temp[~temp.index.duplicated(keep="last")].sort_index()
    # Archiv hinkt ~5 Tage hinterher: fehlende letzte Tage mit letztem Wert füllen
    full = pd.date_range(start, end, freq="D", tz=TZ)
    return temp.reindex(full).ffill().bfill().rename("temp_c")
