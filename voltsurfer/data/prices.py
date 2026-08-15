"""Day-Ahead-Preise und nationale Solarerzeugung von der Energy-Charts-API.

Quelle: Fraunhofer ISE energy-charts.info (Daten: SMARD / Bundesnetzagentur, CC BY 4.0).
Kein API-Key nötig. Abruf monatsweise, Cache als Parquet in data_cache/.

Day-Ahead-Auflösung: stündlich bis 30.09.2025, viertelstündlich ab 01.10.2025
(15-min-MTU). Alles wird auf ein einheitliches 15-min-Raster gebracht
(stündliche Werte per forward-fill), Zeitzone Europe/Berlin.
"""
from __future__ import annotations

import datetime as dt
import time
from pathlib import Path

import pandas as pd
import requests

API_BASE = "https://api.energy-charts.info"
TZ = "Europe/Berlin"
CACHE_DIR = Path(__file__).resolve().parents[2] / "data_cache"
_REQUEST_PAUSE_S = 1.5  # Schonfrist zwischen Requests (API drosselt sonst mit 429)


def _month_range(start: dt.date, end: dt.date) -> list[dt.date]:
    months = []
    d = start.replace(day=1)
    while d <= end:
        months.append(d)
        d = (d + dt.timedelta(days=32)).replace(day=1)
    return months


def _month_end(month: dt.date) -> dt.date:
    return (month + dt.timedelta(days=32)).replace(day=1) - dt.timedelta(days=1)


def _fetch_json(path: str, params: dict, max_attempts: int = 6) -> dict:
    for attempt in range(max_attempts):
        resp = requests.get(f"{API_BASE}/{path}", params=params, timeout=120)
        if resp.status_code == 429 or resp.status_code >= 500:
            wait = float(resp.headers.get("Retry-After", 0)) or min(15 * 2**attempt, 120)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        time.sleep(_REQUEST_PAUSE_S)
        return resp.json()
    resp.raise_for_status()
    raise RuntimeError(f"Energy-Charts-API nicht erreichbar: {path}")


def _to_series(unix_seconds: list, values: list, name: str) -> pd.Series:
    idx = pd.to_datetime(unix_seconds, unit="s", utc=True).tz_convert(TZ)
    s = pd.Series(values, index=idx, name=name, dtype="float64")
    return s[~s.index.duplicated(keep="first")].sort_index()


def _cached_month(kind: str, month: dt.date, fetch) -> pd.Series:
    """Monats-Series aus Cache laden oder per fetch() holen.

    Abgeschlossene Monate sind unveränderlich; der laufende Monat wird höchstens
    alle 6 h aktualisiert. Schlägt der Abruf fehl (z. B. 429), dient der letzte
    Cache-Stand als Fallback.
    """
    CACHE_DIR.mkdir(exist_ok=True)
    path = CACHE_DIR / f"{kind}_{month:%Y-%m}.parquet"
    if path.exists():
        is_final = month < dt.date.today().replace(day=1)
        if is_final or time.time() - path.stat().st_mtime < 6 * 3600:
            return pd.read_parquet(path)[kind]
    try:
        s = fetch(month)
    except Exception:
        if path.exists():
            return pd.read_parquet(path)[kind]
        raise
    s.to_frame().to_parquet(path)
    return s


def _fetch_price_month(month: dt.date) -> pd.Series:
    end = min(_month_end(month), dt.date.today())
    js = _fetch_json("price", {"bzn": "DE-LU", "start": month.isoformat(), "end": end.isoformat()})
    s = _to_series(js["unix_seconds"], js["price"], "spot_eur_mwh")
    return s.rename("price")


def _fetch_solar_month(month: dt.date) -> pd.Series:
    end = min(_month_end(month), dt.date.today())
    js = _fetch_json("public_power", {"country": "de", "start": month.isoformat(), "end": end.isoformat()})
    solar = next(pt for pt in js["production_types"] if pt["name"] == "Solar")
    s = _to_series(js["unix_seconds"], solar["data"], "solar_mw")
    return s.rename("solar")


def _resample_15min(s: pd.Series) -> pd.Series:
    full = pd.date_range(s.index[0], s.index[-1] + pd.Timedelta(minutes=45), freq="15min", tz=TZ)
    return s.reindex(full).ffill(limit=3).dropna()


def get_spot_prices_ct(start: dt.date, end: dt.date) -> pd.Series:
    """Day-Ahead-Spotpreise DE-LU in ct/kWh auf 15-min-Raster, Index Europe/Berlin."""
    parts = [_cached_month("price", m, _fetch_price_month) for m in _month_range(start, end)]
    s = pd.concat(parts)
    s = s[~s.index.duplicated(keep="first")].sort_index()
    s = _resample_15min(s)
    s = s.loc[str(start) : str(end)]
    return (s / 10.0).rename("spot_ct")  # EUR/MWh -> ct/kWh


def get_solar_generation_mw(start: dt.date, end: dt.date) -> pd.Series:
    """Nationale PV-Erzeugung (DE) in MW auf 15-min-Raster."""
    parts = [_cached_month("solar", m, _fetch_solar_month) for m in _month_range(start, end)]
    s = pd.concat(parts)
    s = s[~s.index.duplicated(keep="first")].sort_index()
    s = _resample_15min(s)
    return s.loc[str(start) : str(end)].rename("solar_mw")


def get_installed_solar_gw() -> pd.Series:
    """Installierte PV-Leistung (DE) je Monat in GW, Index = Monatsanfang."""
    js = _fetch_json(
        "installed_power",
        {"country": "de", "time_step": "monthly", "installation_decommission": "false"},
    )
    solar = next(pt for pt in js["production_types"] if "solar" in pt["name"].lower())
    idx = pd.to_datetime(js["time"], format="%m.%Y").tz_localize(TZ)
    s = pd.Series(solar["data"], index=idx, name="installed_gw", dtype="float64")
    return s.dropna()
