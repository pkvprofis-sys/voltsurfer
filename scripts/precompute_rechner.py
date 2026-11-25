"""Rechnet die Ersparnis für den Rechner auf der Website vorab, mit der echten Simulation.

Für jede Kombination aus Personen (1-5), Solaranlage (nein/8 kWp), Wärmepumpe
(nein/9 kW Heizleistung), E-Auto (nein/15.000 km) und Speichergröße (20/30 kWh)
läuft das Trade-LP über dieselben zwölf Monate wie alle Zahlen der Website,
einmal ohne Verkauf ins Netz (das, was ab dem ersten Tag entsteht) und einmal
mit Verkauf (mit dem VoltSurfer-Verbund). Vergleich jeweils gegen 35 ct/kWh
Festpreis, § 14a Modul 1 – genau wie der Referenzhaushalt der Seite.

Aufruf:  .venv\\Scripts\\python.exe scripts\\precompute_rechner.py [--test] [--workers 10]
Ergebnis: website/public/rechner.json (wird von der Startseite geladen)
"""
from __future__ import annotations

import argparse
import datetime as dt
import itertools
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

START = dt.date(2025, 8, 15)
END = dt.date(2026, 8, 14)  # 365 Tage, wie ZEITRAUM in website/lib/preise.ts
OUT = ROOT / "website" / "public" / "rechner.json"

PERSONS = [1, 2, 3, 4, 5]
PV_KWP = [0.0, 8.0]
HP_KW = [0.0, 9.0]
EV_KM = [0.0, 15000.0]
SIZES = {"20": "VoltSurfer 20 (20 kWh / 11 kW)", "30": "VoltSurfer 30 (30 kWh / 11 kW)"}
SMART_RUNS: tuple = ()  # wie der Referenzhaushalt der Website: keine verschobenen Geräte


def key(persons: int, pv: float, hp: float, ev: float, size: str) -> str:
    return f"p{persons}-pv{int(pv > 0)}-wp{int(hp > 0)}-ea{int(ev > 0)}-s{size}"


def run_one(persons: int, pv: float, hp: float, ev: float, size: str) -> tuple[str, dict]:
    import pandas as pd

    from voltsurfer.config import BATTERY_PRESETS, SimConfig, TariffConfig
    from voltsurfer.sim import kpi, strategy
    from voltsurfer.sim.engine import build_trade_inputs

    sim = SimConfig(
        mode="trade",
        battery=BATTERY_PRESETS[SIZES[size]],
        tariff=TariffConfig(static_price_ct=35.0, p14a_module=1),
        persons=persons,
        pv_kwp=pv,
        hp_heat_kw=hp,
        ev_km_per_year=ev,
        smart_runs_per_week=SMART_RUNS,
    )
    inputs = build_trade_inputs(sim, START, END)

    def simulate(sell_enabled: bool) -> pd.DataFrame:
        # wie engine.run_trade_simulation, aber mit Schalter für den Verkauf ins Netz
        day_ids = inputs.index.normalize()
        days = day_ids.unique()
        out, soc = [], 0.0
        for i, day in enumerate(days):
            win_mask = day_ids.isin(days[i : i + sim.horizon_days])
            win = inputs[win_mask]
            res = strategy.optimize_trade_window(
                win["spot_ct"].to_numpy(), win["home_price_ct"].to_numpy(),
                win["charge_price_ct"].to_numpy(), win["batt_home_fee_ct"].to_numpy(),
                win["load_kw"].to_numpy(), sim.battery, soc_start_kwh=soc,
                sell_enabled=sell_enabled, pv_kw=win["pv_kw"].to_numpy(),
            )
            n = int((day_ids[win_mask] == day).sum())
            committed = pd.DataFrame({k: v[:n] for k, v in res.items()}, index=win.index[:n])
            out.append(committed)
            soc = float(committed["soc_kwh"].iloc[-1])
        return inputs.join(pd.concat(out), how="inner")

    entry: dict = {"verbrauch_kwh": round(float(inputs["load_kw"].sum()) * 0.25)}
    for name, sell in (("heute", False), ("verbund", True)):
        result = simulate(sell)
        k = kpi.trade_kpis(result, sim)
        daily = kpi.trade_daily_eur(result, sim)
        # zwölf Monate Sep bis Aug; der halbe August am Anfang und am Ende ergibt zusammen einen August
        by_month = daily.groupby(daily.index.month).sum()
        order = [9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8]
        entry[name] = {
            "jahr_eur": round(k["total_benefit_eur_pa"]),
            "monate_eur": [round(float(by_month.get(m, 0.0))) for m in order],
            "amortisation_jahre": round(k["amortization_years"], 1) if k["amortization_years"] != float("inf") else None,
        }
    return key(persons, pv, hp, ev, size), entry


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="nur der Referenzhaushalt der Website")
    ap.add_argument("--workers", type=int, default=10)
    args = ap.parse_args()

    if args.test:
        t0 = time.time()
        k, e = run_one(3, 0.0, 9.0, 0.0, "30")
        print(k, json.dumps(e, ensure_ascii=False), f"{time.time() - t0:.0f} s")
        return

    combos = list(itertools.product(PERSONS, PV_KWP, HP_KW, EV_KM, SIZES))
    rows: dict[str, dict] = {}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(run_one, *c) for c in combos]
        for i, f in enumerate(as_completed(futures), 1):
            k, e = f.result()
            rows[k] = e
            print(f"[{i}/{len(combos)}] {k}: heute {e['heute']['jahr_eur']} €, verbund {e['verbund']['jahr_eur']} €  ({time.time() - t0:.0f} s)", flush=True)

    OUT.write_text(json.dumps({
        "zeitraum": f"{START:%d.%m.%Y} – {END:%d.%m.%Y}",
        "monate": ["Sep", "Okt", "Nov", "Dez", "Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug"],
        "festpreis_ct": 35, "p14a_modul": 1,
        "annahmen": {"solar_kwp": 8, "waermepumpe_kw": 9, "eauto_km": 15000, "geraete": {}},
        "haushalte": dict(sorted(rows.items())),
    }, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"geschrieben: {OUT} ({len(rows)} Haushalte, {time.time() - t0:.0f} s)")


if __name__ == "__main__":
    main()
