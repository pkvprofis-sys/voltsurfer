"""Simulierte VoltSurfer-Anlage mit Persistenz.

Solange keine echte Hardware angeschlossen ist, führt `SimulatedPlant` den
Anlagenzustand (SoC, Zyklen, Zellzustand, Tageshistorie) als JSON in
data_cache/plant_state.json. Vergangene Tage werden mit echten historischen
Preisen und dem Haushaltsprofil nachsimuliert (LP, Eigenverbrauch + Puffer),
damit Ertragskalender und KI-Lernphase sofort echte Daten haben.
"""
from __future__ import annotations

import datetime as dt
import json
import math

import numpy as np
import pandas as pd

from voltsurfer.config import BATTERY_PRESETS, BatteryConfig, SimConfig, TariffConfig
from voltsurfer.data.prices import CACHE_DIR
from voltsurfer.live.strategies import ManualWindow, StrategySettings
from voltsurfer.sim.engine import build_trade_inputs, run_trade_simulation
from voltsurfer.sim.strategy import DT_H

STATE_PATH = CACHE_DIR / "plant_state.json"
BACKFILL_DAYS = 35
LFP_CYCLE_LIFE = 6000.0

DEFAULT_SETTINGS: dict = {
    "battery_preset": list(BATTERY_PRESETS)[0],
    "persons": 3,
    "hp_enabled": True,
    "hp_area_m2": 140.0,
    "hp_heat_kw": 0.0,  # >0 = WP über Heizleistung modellieren (aus dem Kunden-Check)
    "hp_renovation": "Saniert",
    "location": [51.0, 9.0],
    "speicherprivileg": True,
    "strategy": "auto",  # auto | top_n | manual | ai
    "vpp_enabled": True,
    "buffer_frac": 0.20,
    "top_n_charge_hours": 3,
    "top_n_discharge_hours": 4,
    "learning_days": 10,
    "manual_windows": [
        {"start": "01:00", "end": "05:00", "action": "laden"},
        {"start": "18:00", "end": "21:00", "action": "entladen"},
    ],
    "devices": {
        "wallbox": {"enabled": True, "target_kwh_per_day": 15.0},
        "washer": {"enabled": False, "runtime_h_per_day": 2.0},
    },
}


class SimulatedPlant:
    def __init__(self, demo: bool = False) -> None:
        """demo=True: reiner Sitzungszustand ohne Platte — für die öffentliche
        Web-Demo, damit parallele Besucher sich nicht gegenseitig überschreiben."""
        self.demo = demo
        self.soc_kwh = 0.0
        self.cycles = 0.0
        self.throughput_kwh = 0.0
        self.throughput_since_balancing_kwh = 0.0
        self.last_day_processed: dt.date | None = None
        self.daily_history: list[dict] = []
        self.settings: dict = dict(DEFAULT_SETTINGS)
        self._load()

    # ------------------------------------------------------------- Persistenz
    def _load(self) -> None:
        if self.demo or not STATE_PATH.exists():
            return
        try:
            # utf-8-sig toleriert ein BOM (z. B. von PowerShell-Editoren)
            raw = json.loads(STATE_PATH.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError):
            return  # korrupte Datei: mit frischem Zustand starten statt crashen
        self.soc_kwh = raw.get("soc_kwh", 0.0)
        self.cycles = raw.get("cycles", 0.0)
        self.throughput_kwh = raw.get("throughput_kwh", 0.0)
        self.throughput_since_balancing_kwh = raw.get("throughput_since_balancing_kwh", 0.0)
        last = raw.get("last_day_processed")
        self.last_day_processed = dt.date.fromisoformat(last) if last else None
        self.daily_history = raw.get("daily_history", [])
        self.settings = {**DEFAULT_SETTINGS, **raw.get("settings", {})}
        # Preset-Wechsel: gespeicherter SoC darf die (neue) Nutzkapazität nicht übersteigen
        self.soc_kwh = min(max(self.soc_kwh, 0.0), self.battery.usable_kwh)

    def save(self) -> None:
        if self.demo:
            return  # Demo-Sitzungen schreiben nichts auf die Platte
        CACHE_DIR.mkdir(exist_ok=True)
        STATE_PATH.write_text(
            json.dumps(
                {
                    "soc_kwh": round(self.soc_kwh, 3),
                    "cycles": round(self.cycles, 3),
                    "throughput_kwh": round(self.throughput_kwh, 2),
                    "throughput_since_balancing_kwh": round(self.throughput_since_balancing_kwh, 2),
                    "last_day_processed": self.last_day_processed.isoformat() if self.last_day_processed else None,
                    "daily_history": self.daily_history[-400:],
                    "settings": self.settings,
                },
                indent=1,
            )
        )

    def reset(self) -> None:
        if not self.demo and STATE_PATH.exists():
            STATE_PATH.unlink()
        self.__init__(demo=self.demo)

    # ------------------------------------------------------------- Konfiguration
    @property
    def battery(self) -> BatteryConfig:
        preset = self.settings["battery_preset"]
        if preset not in BATTERY_PRESETS:  # alte Preset-Namen (z. B. 15-kW-Variante)
            preset = next((k for k in BATTERY_PRESETS if k[: len("VoltSurfer 30")] in preset), list(BATTERY_PRESETS)[0])
            self.settings["battery_preset"] = preset
        return BATTERY_PRESETS[preset]

    @property
    def tariff(self) -> TariffConfig:
        return TariffConfig(**self.settings.get("tariff", {}))

    def strategy_settings(self) -> StrategySettings:
        s = self.settings
        return StrategySettings(
            name=s["strategy"],
            vpp_enabled=s["vpp_enabled"],
            buffer_frac=s["buffer_frac"],
            top_n_charge_hours=s["top_n_charge_hours"],
            top_n_discharge_hours=s["top_n_discharge_hours"],
            manual_windows=[ManualWindow(**w) for w in s["manual_windows"]],
            learning_days=s["learning_days"],
            learned_daily_kwh=self.learned_daily_kwh(),
            speicherprivileg=s.get("speicherprivileg", True),
        )

    def sim_config(self) -> SimConfig:
        """Trade-SimConfig aus den Anlagen-Einstellungen (für Backfill und Playground)."""
        s = self.settings
        hp_on = s.get("hp_enabled", False)
        return SimConfig(
            mode="trade",
            battery=self.battery,
            tariff=self.tariff,
            persons=int(s.get("persons", 3)),
            hp_area_m2=float(s.get("hp_area_m2", 0.0)) if hp_on else 0.0,
            hp_heat_kw=float(s.get("hp_heat_kw", 0.0)) if hp_on else 0.0,
            hp_renovation=s.get("hp_renovation", "Saniert"),
            location=tuple(s.get("location", (51.0, 9.0))),
            speicherprivileg=s.get("speicherprivileg", True),
        )

    # ------------------------------------------------------------- Kennzahlen
    @property
    def soh_percent(self) -> float:
        return max(100.0 - 20.0 * self.cycles / LFP_CYCLE_LIFE, 80.0)

    @property
    def cell_spread_mv(self) -> float:
        return min(4.0 + 0.08 * math.sqrt(max(self.throughput_since_balancing_kwh, 0.0)), 60.0)

    def balance_cells(self) -> None:
        self.throughput_since_balancing_kwh = 0.0
        self.save()

    def learning_progress(self) -> tuple[int, int]:
        return min(len(self.daily_history), self.settings["learning_days"]), self.settings["learning_days"]

    def learned_daily_kwh(self) -> float | None:
        """Gelernter Tagesverbrauch: Mittel der letzten Lerntage; None solange Lernphase läuft."""
        days = self.settings["learning_days"]
        if len(self.daily_history) < days:
            return None
        recent = self.daily_history[-days:]
        return float(np.mean([d["load_kwh"] for d in recent]))

    # ------------------------------------------------------------- Fortschreibung
    def advance(self, today: dt.date | None = None) -> None:
        """Simuliert alle fehlenden vollen Tage bis gestern nach (max. BACKFILL_DAYS)."""
        today = today or dt.date.today()
        yesterday = today - dt.timedelta(days=1)
        start = (
            self.last_day_processed + dt.timedelta(days=1)
            if self.last_day_processed
            else yesterday - dt.timedelta(days=BACKFILL_DAYS - 1)
        )
        start = max(start, yesterday - dt.timedelta(days=BACKFILL_DAYS - 1))
        if start > yesterday:
            return

        sim = self.sim_config()
        inputs = build_trade_inputs(sim, start, yesterday)
        result = run_trade_simulation(sim, inputs)

        t = self.tariff
        for day, df in result.groupby(result.index.date):
            discharged = float(df["discharge_kw"].sum()) * DT_H
            day_cycles = discharged / self.battery.usable_kwh
            cost_base = float(df["load_kw"].sum()) * DT_H * t.static_price_ct / 100.0
            revenue = float((df["sell_batt_kw"] * df["spot_ct"]).sum()) * DT_H / 100.0
            cost = (
                float((df["buy_home_kw"] * df["home_price_ct"]).sum())
                + float((df["charge_kw"] * df["charge_price_ct"]).sum())
                + float((df["batt_home_kw"] * df["batt_home_fee_ct"]).sum())
            ) * DT_H / 100.0 - revenue
            self.daily_history.append(
                {
                    "date": day.isoformat(),
                    "load_kwh": round(float(df["load_kw"].sum()) * DT_H, 2),
                    "cost_eur": round(cost, 2),
                    "revenue_eur": round(revenue, 2),
                    "savings_eur": round(cost_base - cost, 2),
                    "cycles": round(day_cycles, 2),
                }
            )
            self.cycles += day_cycles
            self.throughput_kwh += discharged
            self.throughput_since_balancing_kwh += discharged
            self.soc_kwh = float(df["soc_kwh"].iloc[-1])
            self.last_day_processed = day

        # Duplikate (z. B. nach Reset) entfernen, Reihenfolge stabil halten
        seen: dict[str, dict] = {}
        for entry in self.daily_history:
            seen[entry["date"]] = entry
        self.daily_history = [seen[k] for k in sorted(seen)]
        self.save()

    def update_intraday(self, plan: pd.DataFrame, now: pd.Timestamp) -> None:
        """SoC aus dem heutigen Plan zum aktuellen Zeitpunkt übernehmen (nicht persistiert je Schritt)."""
        past = plan[plan.index <= now]
        if len(past):
            self.soc_kwh = float(past["soc_kwh"].iloc[-1])

    def history_frame(self) -> pd.DataFrame:
        if not self.daily_history:
            return pd.DataFrame(columns=["load_kwh", "pv_kwh", "cost_eur", "revenue_eur", "savings_eur", "cycles"])
        df = pd.DataFrame(self.daily_history)
        df["date"] = pd.to_datetime(df["date"])
        return df.set_index("date").sort_index()
