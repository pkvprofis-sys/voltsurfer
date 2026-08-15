"""Tests für Live-Strategien, Geräteplanung und simulierte Anlage (API gemockt)."""
import datetime as dt

import numpy as np
import pandas as pd
import pytest

from voltsurfer.config import BatteryConfig, TariffConfig
from voltsurfer.live import devices as devices_mod
from voltsurfer.live import state as state_mod
from voltsurfer.live.devices import DeviceConfig, schedule_devices
from voltsurfer.live.strategies import ManualWindow, StrategySettings, build_plan
from voltsurfer.sim.strategy import DT_H
from voltsurfer.tests.test_sim import TZ, two_level_day

BATT = BatteryConfig()
TARIFF = TariffConfig()
BUFFER_KWH = 0.20 * BATT.usable_kwh


def live_series(days: int = 2):
    idx = pd.date_range("2026-07-15", periods=days * 96, freq="15min", tz=TZ)
    prices = pd.Series(two_level_day(days=days), index=idx, name="price_ct")
    load = pd.Series(1.0, index=idx)
    pv = pd.Series(0.0, index=idx)
    return prices, load, pv


def settings(**kw) -> StrategySettings:
    return StrategySettings(**{"buffer_frac": 0.20, **kw})


def check_soc_buffer(plan, start_soc=0.0):
    """Nach der Anlaufphase (Puffer erreicht) darf der SoC nie mehr darunter fallen."""
    soc = plan["soc_kwh"].to_numpy()
    reached = np.flatnonzero(soc >= BUFFER_KWH - 1e-6)
    assert len(reached) > 0, "Puffer wird nie erreicht"
    assert (soc[reached[0] :] >= BUFFER_KWH - 1e-6).all(), "SoC fällt unter den Puffer"


def test_top_n_charges_only_cheapest_hours():
    prices, load, pv = live_series()
    plan = build_plan(prices, load, pv, BATT, TARIFF, settings(name="top_n", top_n_charge_hours=3), 0.0)
    charging = plan[plan["charge_kw"] > 1e-6]
    # two_level_day: billigste Stunden sind 0-6 und 12-15 Uhr (2 ct)
    assert set(charging.index.hour.unique()).issubset(set(range(0, 6)) | set(range(12, 15)))
    # es wird höchstens in N Stunden je Tag geladen
    for day, df in charging.groupby(charging.index.date):
        assert df.index.hour.nunique() <= 3
    check_soc_buffer(plan)


def test_top_n_discharges_expensive_and_sells_vpp():
    prices, load, pv = live_series()
    plan = build_plan(prices, load, pv, BATT, TARIFF, settings(name="top_n", vpp_enabled=True), 0.0)
    selling = plan[plan["sell_batt_kw"] > 1e-6]
    assert len(selling) > 0, "VPP verkauft nicht in Teuerstunden"
    assert (selling["price_ct"] >= 10.0).all(), "Verkauf außerhalb der Teuerstunden"
    plan_no_vpp = build_plan(prices, load, pv, BATT, TARIFF, settings(name="top_n", vpp_enabled=False), 0.0)
    assert plan_no_vpp["sell_batt_kw"].abs().sum() < 1e-9


def test_manual_windows_respected():
    prices, load, pv = live_series()
    st = settings(
        name="manual",
        manual_windows=[
            ManualWindow("01:00", "05:00", "laden"),
            ManualWindow("12:00", "14:00", "gesperrt"),
        ],
    )
    plan = build_plan(prices, load, pv, BATT, TARIFF, st, 0.0)
    hours = plan.index.hour + plan.index.minute / 60.0
    in_charge = (hours >= 1.0) & (hours < 5.0)
    in_block = (hours >= 12.0) & (hours < 14.0)
    assert plan.loc[~in_charge, "charge_kw"].abs().sum() < 1e-9, "lädt außerhalb des Ladefensters"
    assert plan.loc[in_block, ["charge_kw", "discharge_kw"]].abs().sum().sum() < 1e-9
    # außerhalb der Fenster deckt der Speicher den Haushalt (Standardverhalten)
    covered = plan[(~in_charge) & (~in_block) & (plan["discharge_kw"] > 1e-6)]
    assert len(covered) > 0


def test_ai_learning_phase_no_selling():
    prices, load, pv = live_series()
    plan = build_plan(prices, load, pv, BATT, TARIFF, settings(name="ai", learned_daily_kwh=None), 0.0)
    assert plan["sell_batt_kw"].abs().sum() < 1e-9, "Verkauf vor Ende der Lernphase"
    check_soc_buffer(plan)


def test_ai_reserves_learned_consumption():
    prices, load, pv = live_series()
    # Minimale Last: Verkauf lohnt nur für Energie, die der Haushalt nicht mehr braucht
    load = load * 0.05
    st = settings(name="ai", learned_daily_kwh=10.0, vpp_enabled=True)
    plan = build_plan(prices, load, pv, BATT, TARIFF, st, BATT.usable_kwh)
    # morgens muss Puffer + hohe Reserve gehalten werden
    morning = plan.index.hour < 6
    reserve_morning = BUFFER_KWH + 10.0 * (1.0 - 6 / 24)
    assert (plan.loc[morning, "soc_kwh"] >= min(reserve_morning, BATT.usable_kwh) - 3.0).all()
    check_soc_buffer(plan)
    assert plan["sell_batt_kw"].sum() > 0, "trotz vollem Speicher kein VPP-Verkauf"


def test_auto_lp_respects_buffer():
    prices, load, pv = live_series()
    plan = build_plan(prices, load, pv, BATT, TARIFF, settings(name="auto", vpp_enabled=True), BATT.usable_kwh / 2)
    check_soc_buffer(plan, start_soc=BATT.usable_kwh / 2)


def test_device_split_placement():
    prices, _, _ = live_series(days=1)
    dev = DeviceConfig("wallbox", "Wallbox", "🚗", 11.0, True, target_kwh_per_day=15.0)
    sched = schedule_devices(prices, [dev])
    slots = int(np.ceil(15.0 / (11.0 * DT_H)))
    active = sched[sched["wallbox"] > 0]
    assert len(active) == slots
    # alle Slots liegen in den billigsten Viertelstunden (2-ct-Fenster)
    assert (prices.loc[active.index] <= 2.0).all()
    assert active["wallbox"].sum() * DT_H >= 15.0


def test_device_contiguous_block():
    prices, _, _ = live_series(days=1)
    dev = DeviceConfig(
        "washer", "WM", "🧺", 2.0, True,
        runtime_h_per_day=2.0, contiguous=True, allowed_from="08:00", allowed_to="22:00",
    )
    sched = schedule_devices(prices, [dev])
    active = sched.index[sched["washer"] > 0]
    assert len(active) == 8
    diffs = np.diff(active.asi8)
    assert (diffs == diffs[0]).all(), "Waschmaschinen-Block ist nicht zusammenhängend"
    hours = active.hour + active.minute / 60.0
    assert (hours >= 8.0).all() and (hours < 22.0).all()
    # Block liegt im billigen Mittagsfenster (12-15 Uhr)
    assert (prices.loc[active] <= 2.0).all()


def test_no_heatpump_dummy_device():
    """Die WP ist witterungsgeführte Grundlast, kein schaltbares Gerät (Doppelzähl-Bug)."""
    from voltsurfer.live.devices import DEFAULT_DEVICES

    assert all(d.key != "heatpump" for d in DEFAULT_DEVICES)
    prices, _, _ = live_series(days=1)
    sched = schedule_devices(prices, DEFAULT_DEVICES)
    assert "heatpump" not in sched.columns


def test_energy_monitor_svg():
    from app.monitor import energy_monitor_html

    html = energy_monitor_html({
        "consumption_kw": 2.0, "grid_kw": -3.0, "storage_kw": 1.5, "soc_frac": 0.5,
        "production_kw": 0.0, "pv_kwp": 0.0, "autarky_frac": 0.8,
        "self_consumption_frac": None, "scale_kw": 11.0,
    })
    for token in ["Autarkie heute", "80 %", "Speicher", "Einspeisung", "Verbrauch", "<svg"]:
        assert token in html
    # Ratio-Clipping: absurde Werte dürfen das SVG nicht sprengen
    html2 = energy_monitor_html({"consumption_kw": 999.0, "grid_kw": 999.0, "storage_kw": 0.0,
                                 "soc_frac": 1.7, "production_kw": 0.0, "pv_kwp": 0.0,
                                 "autarky_frac": None, "scale_kw": 11.0})
    assert "<svg" in html2


def test_weather_icons_and_hp_forecast():
    from voltsurfer.data.weather import wmo_icon
    from voltsurfer.profiles.heatpump import daily_electric_kwh_for_temp

    assert wmo_icon(0)[0] == "☀️"
    assert wmo_icon(75)[0] == "❄️"
    assert wmo_icon(999)[1].startswith("Code")

    cold = daily_electric_kwh_for_temp(-5.0, heat_kw=9.0)
    warm = daily_electric_kwh_for_temp(22.0, heat_kw=9.0)
    assert cold > 15.0, "kalter Tag muss deutlich zweistellig sein"
    assert warm < 3.5, "Sommertag = fast nur Warmwasser"
    assert cold > 5 * warm
    assert daily_electric_kwh_for_temp(0.0) == 0.0  # keine WP konfiguriert


def test_plant_state_advance_and_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(state_mod, "STATE_PATH", tmp_path / "plant_state.json")

    idx = pd.date_range("2026-07-10", periods=3 * 96, freq="15min", tz=TZ)

    def fake_build_inputs(sim, start, end):
        df = pd.DataFrame(index=idx)
        df["spot_ct"] = 8.0
        df["home_price_ct"] = 30.0
        df["charge_price_ct"] = 10.0
        df["batt_home_fee_ct"] = 20.0
        df["load_kw"] = 0.5
        return df

    def fake_run_simulation(sim, inputs, progress_cb=None):
        df = inputs.copy()
        df["charge_kw"] = 0.4
        df["batt_home_kw"] = 0.2
        df["sell_batt_kw"] = 0.2
        df["discharge_kw"] = df["batt_home_kw"] + df["sell_batt_kw"]
        df["buy_home_kw"] = df["load_kw"] - df["batt_home_kw"]
        df["grid_buy_kw"] = df["buy_home_kw"] + df["charge_kw"]
        df["soc_kwh"] = 5.0
        return df

    monkeypatch.setattr(state_mod, "build_trade_inputs", fake_build_inputs)
    monkeypatch.setattr(state_mod, "run_trade_simulation", fake_run_simulation)

    plant = state_mod.SimulatedPlant()
    plant.advance(today=dt.date(2026, 7, 13))
    assert len(plant.daily_history) == 3
    assert plant.cycles > 0
    assert plant.soh_percent < 100.0
    assert plant.last_day_processed == dt.date(2026, 7, 12)

    # Roundtrip: neue Instanz lädt denselben Zustand
    plant2 = state_mod.SimulatedPlant()
    assert plant2.cycles == pytest.approx(plant.cycles, abs=1e-3)
    assert len(plant2.daily_history) == 3

    # advance ist idempotent für bereits verarbeitete Tage
    plant2.advance(today=dt.date(2026, 7, 13))
    assert len(plant2.daily_history) == 3

    # Balancing setzt Zellspreizung zurück
    spread_before = plant2.cell_spread_mv
    plant2.balance_cells()
    assert plant2.cell_spread_mv < spread_before


def test_soc_above_capacity_does_not_crash():
    """Preset-Wechsel-Szenario: Start-SoC über Nutzkapazität darf das LP nie brechen."""
    prices, load, pv = live_series()
    for name in ["auto", "ai", "top_n"]:
        plan = build_plan(prices, load, pv, BATT, TARIFF, settings(name=name), soc_start_kwh=28.5)
        assert plan["soc_kwh"].max() <= BATT.usable_kwh + 1e-6
        assert plan.attrs.get("lp_fallback") is False


def test_lp_failure_falls_back_to_rule(monkeypatch):
    from voltsurfer.live import strategies as strat_mod

    def boom(*a, **k):
        raise RuntimeError("Trade-LP nicht optimal gelöst: Infeasible")

    monkeypatch.setattr(strat_mod, "optimize_trade_window", boom)
    prices, load, pv = live_series()
    plan = build_plan(prices, load, pv, BATT, TARIFF, settings(name="auto"), 0.0)
    assert plan.attrs.get("lp_fallback") is True
    # Fallback-Plan ist physikalisch gültig
    assert plan["soc_kwh"].max() <= BATT.usable_kwh + 1e-6
    assert plan["charge_kw"].max() <= BATT.charge_power_kw + 1e-6


def test_state_load_clamps_soc(tmp_path, monkeypatch):
    monkeypatch.setattr(state_mod, "STATE_PATH", tmp_path / "plant_state.json")
    plant = state_mod.SimulatedPlant()
    plant.soc_kwh = 28.5  # Zustand vom 30-kWh-Speicher
    plant.settings["battery_preset"] = list(state_mod.BATTERY_PRESETS)[0]  # 20 kWh
    plant.save()

    plant2 = state_mod.SimulatedPlant()
    assert plant2.soc_kwh <= plant2.battery.usable_kwh + 1e-6


def test_learned_daily_kwh(tmp_path, monkeypatch):
    monkeypatch.setattr(state_mod, "STATE_PATH", tmp_path / "plant_state.json")
    plant = state_mod.SimulatedPlant()
    plant.settings["learning_days"] = 7
    assert plant.learned_daily_kwh() is None
    plant.daily_history = [
        {"date": f"2026-07-{d:02d}", "load_kwh": 10.0, "pv_kwh": 0, "cost_eur": 1,
         "revenue_eur": 0, "savings_eur": 1, "cycles": 0.5}
        for d in range(1, 9)
    ]
    assert plant.learned_daily_kwh() == pytest.approx(10.0)
