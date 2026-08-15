"""Gemeinsame Helfer für alle App-Seiten: Anlage, Live-Daten, Plan-Pipeline."""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from voltsurfer.config import TariffConfig
from voltsurfer.data.prices import TZ
from voltsurfer.live import prices_live
from voltsurfer.live.devices import DEFAULT_DEVICES, DeviceConfig, schedule_devices
from voltsurfer.live.state import SimulatedPlant
from voltsurfer.live.strategies import build_plan
from voltsurfer.openems.client import OpenemsClient
from voltsurfer.profiles.load import household_load_kw

STRATEGY_LABELS = {
    "auto": "Auto (Preisoptimiert)",
    "top_n": "Top-N Billigstunden",
    "manual": "Manuelle Fenster",
    "ai": "KI-Adaptiv (lernend)",
}


def is_demo() -> bool:
    """Öffentliche Web-Demo (VOLTSURFER_DEMO=1): kein gemeinsamer Anlagenzustand."""
    return os.environ.get("VOLTSURFER_DEMO") == "1"


@st.cache_resource
def _shared_plant() -> SimulatedPlant:
    return SimulatedPlant()


def get_plant() -> SimulatedPlant:
    if not is_demo():
        return _shared_plant()
    # Demo: je Browser-Sitzung eine eigene Anlage, nichts wird gespeichert
    if "demo_plant" not in st.session_state:
        st.session_state["demo_plant"] = SimulatedPlant(demo=True)
    return st.session_state["demo_plant"]


def ensure_advanced(plant: SimulatedPlant) -> None:
    """Einmal je Session: fehlende Tage nachsimulieren (erster Start: ~35 Tage Backfill)."""
    if st.session_state.get("plant_advanced"):
        return
    with st.spinner("Aktualisiere Anlagenhistorie …"):
        plant.advance()
    st.session_state["plant_advanced"] = True


def plant_tariff(plant: SimulatedPlant) -> TariffConfig:
    overrides = plant.settings.get("tariff", {})
    return TariffConfig(**overrides)


TOU_STATES = {
    0: ("⏸️", "Entladung verzögert (wartet auf Teuerstunden)"),
    1: ("🏠", "Eigenverbrauchsoptimierung"),
    3: ("🔌", "Lädt Billigstrom aus dem Netz"),
    4: ("💶", "Entlädt ins Netz (Verkauf)"),
}


def openems_settings(plant: SimulatedPlant) -> dict:
    cfg = plant.settings.setdefault(
        "openems",
        {"enabled": False, "base_url": "http://localhost:8084", "password": "admin", "control": False},
    )
    cfg.setdefault("mode", "openems_tou")  # openems_tou | voltsurfer_push
    return cfg


def openems_client(plant: SimulatedPlant) -> OpenemsClient:
    cfg = openems_settings(plant)
    return OpenemsClient(cfg["base_url"], cfg["password"])


def openems_live_soc(plant: SimulatedPlant) -> float | None:
    """Echter SoC (kWh) vom Edge, falls Kopplung aktiv und online — sonst None."""
    if not openems_settings(plant)["enabled"]:
        return None
    soc_pct = openems_client(plant).soc_percent()
    if soc_pct is None:
        return None
    return soc_pct / 100.0 * plant.battery.usable_kwh


def plant_devices(plant: SimulatedPlant) -> list[DeviceConfig]:
    devices = []
    for proto in DEFAULT_DEVICES:
        cfg = plant.settings["devices"].get(proto.key, {})
        # nur bekannte Felder übernehmen (Migration: alte Einträge wie "heatpump"
        # oder entfernte Felder dürfen nicht crashen)
        cfg = {k: v for k, v in cfg.items() if k in proto.__dict__}
        dev = DeviceConfig(**{**proto.__dict__, **cfg})
        devices.append(dev)
    return devices


@st.cache_data(ttl=600, show_spinner=False)
def _live_inputs(persons: int, hp_area_m2: float, hp_heat_kw: float, hp_renovation: str, location: tuple) -> pd.DataFrame:
    from voltsurfer.profiles.heatpump import PERSONS_TO_KWH, heatpump_load_kw, heatpump_load_kw_from_power

    prices = prices_live.get_live_prices_ct()
    df = pd.DataFrame({"price_ct": prices})
    df["base_load_kw"] = household_load_kw(df.index, PERSONS_TO_KWH.get(persons, 3500.0))
    if hp_heat_kw > 0:
        df["hp_kw"] = heatpump_load_kw_from_power(df.index, hp_heat_kw, *location)
    else:
        df["hp_kw"] = heatpump_load_kw(df.index, hp_area_m2, hp_renovation, *location)
    return df


def make_plan(plant: SimulatedPlant):
    """Live-Plan für das aktuelle Preisfenster: Preise, Last (Haushalt+WP), Geräte, Strategie."""
    sim = plant.sim_config()
    # Preset-Wechsel innerhalb der Session: SoC an die aktuelle Kapazität klammern
    plant.soc_kwh = min(max(plant.soc_kwh, 0.0), plant.battery.usable_kwh)
    inputs = _live_inputs(sim.persons, sim.hp_area_m2, sim.hp_heat_kw, sim.hp_renovation, tuple(sim.location))
    devices = plant_devices(plant)
    schedule = schedule_devices(inputs["price_ct"], devices)
    load_total = inputs["base_load_kw"] + inputs["hp_kw"] + schedule["devices_total_kw"]

    plan = build_plan(
        inputs["price_ct"],
        load_total,
        pd.Series(0.0, index=inputs.index),  # PV entfällt im Produkt
        plant.battery,
        plant_tariff(plant),
        plant.strategy_settings(),
        soc_start_kwh=plant.soc_kwh,
    )
    plan["base_load_kw"] = inputs["base_load_kw"]
    plan["hp_kw"] = inputs["hp_kw"]
    now = pd.Timestamp.now(tz=TZ).floor("15min")
    plant.update_intraday(plan, now)
    return plan, schedule, devices, now


def render_day_statement(day_df: pd.DataFrame, sim) -> None:
    """Nachvollziehbare Tagesabrechnung als Tabelle + Summen rendern."""
    from voltsurfer.sim import kpi

    rows, totals = kpi.day_statement(day_df, sim)
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Ohne VoltSurfer (Ihr Tarif)", f"{totals['baseline_heute_eur']:.2f} €",
              help=f"{totals['load_kwh']:.1f} kWh Verbrauch × statischer Tarif")
    c2.metric("Mit VoltSurfer", f"{totals['kosten_heute_eur']:.2f} €")
    c3.metric("Tagesersparnis", f"{totals['ersparnis_heute_eur']:+.2f} €")
    st.caption(
        "**Status:** ✅ heute = funktioniert sofort mit dynamischem Tarif + § 14a · "
        "🔓 Vermarktung = braucht die VoltSurfer-Direktvermarktung (White-Label-Partner, "
        "aktiv ab ~20–30 Kunden ≈ 100 kWh Handelsvolumen/Tag). "
        "*Spot netto* = nackter Börsenpreis; *bezahlt/erlöst* = tatsächlich verrechneter Preis "
        "inkl. Abgaben/MwSt. Kalkulatorischer Batterieverschleiß (2 ct/kWh Entladung) ist nicht "
        "zahlungswirksam und daher kein Posten — in der Wirtschaftlichkeits-Zerlegung aber abgezogen."
    )


def flows_at(plan: pd.DataFrame, schedule: pd.DataFrame, now: pd.Timestamp) -> dict[str, float]:
    """Energieflüsse (kW) am aktuellen Zeitschritt für die Flussgrafik (ohne PV)."""
    ts = now if now in plan.index else plan.index[0]
    row = plan.loc[ts]
    dev_row = schedule.loc[ts] if ts in schedule.index else None
    load = float(row["load_kw"])
    charge = float(row["charge_kw"])
    batt_to_house = min(float(row["discharge_kw"]) - float(row["sell_batt_kw"]), load)
    hp = float(row["hp_kw"]) if "hp_kw" in row else 0.0
    return {
        "load": load,
        "grid_to_batt": charge,
        "grid_to_house": max(load - batt_to_house, 0.0),
        "batt_to_house": max(batt_to_house, 0.0),
        "batt_to_grid": float(row["sell_batt_kw"]),
        "wallbox": float(dev_row["wallbox"]) if dev_row is not None and "wallbox" in dev_row else 0.0,
        "heatpump": hp + (float(dev_row["heatpump"]) if dev_row is not None and "heatpump" in dev_row else 0.0),
        "price_ct": float(row["price_ct"]),
    }
