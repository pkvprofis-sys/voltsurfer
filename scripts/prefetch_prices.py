"""Lädt den vollen Preis-Zeitraum (2023-01-01 bis heute) in den Parquet-Cache."""
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voltsurfer.data import prices

start, end = dt.date(2023, 1, 1), dt.date.today()
spot = prices.get_spot_prices_ct(start, end)
print(f"SPOT: {len(spot)} Punkte, {spot.index[0]} -> {spot.index[-1]}, NaN: {spot.isna().sum()}")
print("Jahresmittel ct/kWh:", spot.groupby(spot.index.year).mean().round(2).to_dict())
print("Negativpreis-Anteil %:", spot.groupby(spot.index.year).apply(lambda s: round((s < 0).mean() * 100, 1)).to_dict())
