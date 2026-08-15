"""Live-Daten von der Energy-Charts-API: aktuelles Preisfenster und Solarprognose.

`/price` ohne Datumsangabe liefert das rollierende Day-Ahead-Fenster — nach der
~13-Uhr-Auktion inklusive der Morgen-Preise. `/public_power_forecast` liefert die
nationale Day-Ahead-Solarprognose (15-min, MW), die wir über die installierte
PV-Leistung auf die Kundenanlage (kWp) skalieren.

Kurzer TTL-Cache (10 min) in data_cache/, damit App-Reruns die API nicht fluten.
"""
from __future__ import annotations

import datetime as dt
import json
import time
from pathlib import Path

import pandas as pd

from voltsurfer.data.prices import CACHE_DIR, TZ, _fetch_json, _to_series
from voltsurfer.profiles.pv import FLEET_ADJUST

LIVE_TTL_S = 600


def _cached_live(name: str, fetch) -> pd.Series:
    CACHE_DIR.mkdir(exist_ok=True)
    path = CACHE_DIR / f"live_{name}.json"
    if path.exists() and time.time() - path.stat().st_mtime < LIVE_TTL_S:
        payload = json.loads(path.read_text())
    else:
        try:
            payload = fetch()
            path.write_text(json.dumps(payload))
        except Exception:
            if not path.exists():
                raise
            payload = json.loads(path.read_text())  # Fallback: letzter Stand
    return _to_series(payload["unix_seconds"], payload["values"], name)


def get_live_prices_ct() -> pd.Series:
    """Day-Ahead-Preise heute + morgen in ct/kWh (15-min-Raster).

    Expliziter Datumsbereich: Die Morgen-Preise erscheinen nach der Auktion
    (~13 Uhr); vorher liefert die API nur den heutigen Tag.
    """

    def fetch() -> dict:
        today = dt.date.today()
        js = _fetch_json(
            "price",
            {
                "bzn": "DE-LU",
                "start": today.isoformat(),
                "end": (today + dt.timedelta(days=1)).isoformat(),
            },
        )
        return {"unix_seconds": js["unix_seconds"], "values": js["price"]}

    s = _cached_live("price", fetch)
    return _resample_live(s / 10.0).rename("price_ct")


def get_pv_forecast_kw(kwp: float, installed_gw: float | None = None) -> pd.Series:
    """Solarprognose skaliert auf eine Kundenanlage mit kwp Spitzenleistung (kW)."""
    if kwp <= 0:
        prices = get_live_prices_ct()
        return pd.Series(0.0, index=prices.index, name="pv_kw")

    def fetch() -> dict:
        today = dt.date.today()
        js = _fetch_json(
            "public_power_forecast",
            {
                "country": "de",
                "production_type": "solar",
                "forecast_type": "day-ahead",
                "start": today.isoformat(),
                "end": (today + dt.timedelta(days=1)).isoformat(),
            },
        )
        return {"unix_seconds": js["unix_seconds"], "values": js["forecast_values"]}

    solar_mw = _cached_live("solar_forecast", fetch)
    if installed_gw is None:
        installed_gw = _current_installed_gw()
    cf = (solar_mw / (installed_gw * 1000.0)).clip(lower=0.0, upper=1.0)
    return _resample_live(cf * kwp * FLEET_ADJUST).rename("pv_kw")


def _current_installed_gw() -> float:
    """Aktuell installierte PV-Leistung DE in GW (24-h-Cache, Fallback 125 GW)."""
    path = CACHE_DIR / "live_installed_gw.json"
    if path.exists() and time.time() - path.stat().st_mtime < 86400:
        return json.loads(path.read_text())["gw"]
    try:
        from voltsurfer.data.prices import get_installed_solar_gw

        gw = float(get_installed_solar_gw().iloc[-1])
        CACHE_DIR.mkdir(exist_ok=True)
        path.write_text(json.dumps({"gw": gw}))
        return gw
    except Exception:
        return 125.0


def _resample_live(s: pd.Series) -> pd.Series:
    full = pd.date_range(s.index[0], s.index[-1] + pd.Timedelta(minutes=45), freq="15min", tz=TZ)
    return s.reindex(full).ffill(limit=3).dropna()


def has_tomorrow(prices: pd.Series) -> bool:
    """True, wenn das Preisfenster bereits Morgen-Preise enthält (Auktion ~13 Uhr)."""
    now = pd.Timestamp.now(tz=TZ)
    return prices.index[-1].date() > now.date()
