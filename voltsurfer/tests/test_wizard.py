"""Tests für E-Auto-Ladeplaner, PV im Trade-LP, Bedarfsrechnung und Empfehlung."""
import numpy as np
import pandas as pd
import pytest

from voltsurfer.config import BATTERY_PRESETS, SimConfig, TariffConfig
from voltsurfer.profiles.ev import availability_mask, ev_charging_kw, ev_dumb_charging_kw, ev_stats
from voltsurfer.sim import kpi
from voltsurfer.sim.advisor import SMART_DEVICES, daily_demand_kwh, recommend_battery, smart_runs_kw
from voltsurfer.sim.strategy import DT_H, optimize_trade_window
from voltsurfer.tests.test_sim import TZ, two_level_day
from voltsurfer.tests.test_trade import make_sim, trade_inputs

BATT = BATTERY_PRESETS["VoltSurfer 20 (20 kWh / 11 kW)"]


def week_prices(days: int = 14) -> pd.Series:
    idx = pd.date_range("2025-03-03", periods=days * 96, freq="15min", tz=TZ)  # Montag
    return pd.Series(np.tile(two_level_day(days=1), days), index=idx, name="price_ct")


# ------------------------------------------------------------------ E-Auto
def test_ev_covers_demand_in_allowed_windows():
    prices = week_prices()
    ev = ev_charging_kw(prices, km_per_year=15000, battery_kwh=60.0)
    needed = 15000 / 365 * 18 / 100 * 14
    assert float(ev.sum()) * DT_H >= needed * 0.9, "Fahrbedarf nicht gedeckt"
    # nur in erlaubten Fenstern
    assert float(ev[~availability_mask(prices.index)].abs().sum()) == 0.0
    assert ev.max() <= 11.0 + 1e-9


def test_ev_big_battery_charges_rarely():
    prices = week_prices()
    big = ev_stats(ev_charging_kw(prices, 15000, battery_kwh=80.0), prices)
    small = ev_stats(ev_charging_kw(prices, 15000, battery_kwh=20.0), prices)
    assert big["charging_days"] < big["total_days"] / 2, "großer Akku sollte selten laden"
    assert small["charging_days"] >= big["charging_days"], "kleiner Akku muss öfter laden"


def test_ev_smart_cheaper_than_dumb():
    prices = week_prices()
    smart = ev_charging_kw(prices, 15000, 60.0)
    dumb = ev_dumb_charging_kw(prices, 15000, 60.0)
    cost_smart = float((smart * prices).sum())
    cost_dumb = float((dumb * prices).sum())
    assert cost_smart < cost_dumb, "KI-Ladeplanung muss billiger sein als tägliches 18-Uhr-Laden"
    # dummes Laden beginnt täglich um 18 Uhr
    assert set(dumb[dumb > 0].index.hour.unique()) <= {18, 19, 20}


# ------------------------------------------------------------------ PV im Trade-LP
def test_trade_lp_with_pv_balances():
    sim = make_sim(True)
    spot = two_level_day(cheap_ct=1.0, expensive_ct=25.0, days=2)
    inputs = trade_inputs(spot, 0.5, sim.tariff, True)
    # Mittags-PV 6 kW (Slots 40-64 je Tag)
    pv = np.zeros(len(spot))
    day = np.zeros(96)
    day[40:64] = 6.0
    pv[:] = np.tile(day, 2)

    res = optimize_trade_window(
        inputs["spot_ct"].to_numpy(),
        inputs["home_price_ct"].to_numpy(),
        inputs["charge_price_ct"].to_numpy(),
        inputs["batt_home_fee_ct"].to_numpy(),
        inputs["load_kw"].to_numpy(),
        BATT,
        soc_start_kwh=0.0,
        pv_kw=pv,
    )
    # PV-Bilanz schließt
    assert np.allclose(res["pv_home_kw"] + res["pv_charge_kw"] + res["sell_pv_kw"], pv, atol=1e-4)
    # Lastbilanz schließt
    assert np.allclose(res["buy_home_kw"] + res["batt_home_kw"] + res["pv_home_kw"], 0.5, atol=1e-4)
    # PV wird genutzt (verkauft oder gespeichert), nicht verworfen
    assert float((res["sell_pv_kw"] + res["pv_charge_kw"]).sum()) * DT_H > 20.0


# ------------------------------------------------------------------ Bedarf & Empfehlung
def test_daily_demand_breakdown():
    sim = SimConfig(
        persons=3, hp_area_m2=140.0, ev_km_per_year=15000,
        smart_runs_per_week=(("washer", 3), ("dishwasher", 7)),
    )
    d = daily_demand_kwh(sim)
    assert d["Haushalt"] == pytest.approx(3500 / 365, rel=0.01)
    assert d["E-Auto"] == pytest.approx(15000 / 365 * 0.18, rel=0.01)
    assert d["Wärmepumpe"] > 5.0
    assert d["Gesamt"] == pytest.approx(sum(v for k, v in d.items() if k != "Gesamt"))


def test_heatpump_from_power(monkeypatch):
    from voltsurfer.profiles import heatpump as hp_mod

    idx_days = pd.date_range("2025-01-01", "2025-12-31", freq="D", tz=TZ)
    temps = 8.5 - 13.5 * np.cos(2 * np.pi * (idx_days.dayofyear - 15) / 365.0)
    monkeypatch.setattr(hp_mod.weather, "daily_mean_temp_c",
                        lambda *a, **k: pd.Series(temps, index=idx_days, name="temp_c"))

    idx = pd.date_range("2025-01-01", "2025-12-31 23:45", freq="15min", tz=TZ)
    hp = hp_mod.heatpump_load_kw_from_power(idx, heat_kw=9.0)
    annual = float(hp.sum()) * DT_H
    # 9 kW x 1900 h Wärme / JAZ ~3-4.5; Testjahr ist kälter als das Normjahr
    assert 3000 < annual < 6000, f"unplausibel: {annual:.0f} kWh"
    expected = hp_mod.avg_electric_kwh_from_power(9.0)
    assert annual == pytest.approx(expected, rel=0.25)
    assert float(hp_mod.heatpump_load_kw_from_power(idx, 0.0).abs().sum()) == 0.0


def test_manual_consumption_used():
    sim = SimConfig(persons=0, annual_consumption_kwh=5200.0)
    d = daily_demand_kwh(sim)
    assert d["Haushalt"] == pytest.approx(5200 / 365, rel=0.01)


def test_static_price_override_and_dynamic_baseline():
    import dataclasses

    from voltsurfer.sim.engine import run_trade_simulation

    spot = two_level_day(cheap_ct=1.0, expensive_ct=25.0, days=2)
    base_tariff = TariffConfig()
    inputs = trade_inputs(spot, 1.0, base_tariff, True)
    sim35 = make_sim(True)
    res = run_trade_simulation(sim35, inputs)

    k35 = kpi.trade_kpis(res, sim35)
    sim28 = dataclasses.replace(sim35, tariff=dataclasses.replace(base_tariff, static_price_ct=28.0))
    k28 = kpi.trade_kpis(res, sim28)

    # niedrigerer Kundenpreis -> kleinere Baseline -> kleinere Ersparnis
    assert k28["total_benefit_eur"] < k35["total_benefit_eur"]
    # die Differenz entspricht exakt 7 ct auf jede verbrauchte kWh
    load_kwh = float(res["load_kw"].sum()) * DT_H
    assert k35["total_benefit_eur"] - k28["total_benefit_eur"] == pytest.approx(load_kwh * 0.07, rel=1e-6)

    # konservative Baseline: Ø-dyn-Preis liegt hier unter 35 ct statisch
    assert k35["total_benefit_vs_dynamic_eur"] < k35["total_benefit_eur"]
    # Kundenpreis ändert die konservative Zahl nicht (sie hängt nicht am statischen Preis)
    assert k28["total_benefit_vs_dynamic_eur"] == pytest.approx(k35["total_benefit_vs_dynamic_eur"])
    # Summenprobe bleibt intakt
    assert k28["total_benefit_eur"] == pytest.approx(
        k28["trade_profit_eur"] + k28["consumption_saving_eur"] + k28["p14a_eur"] + k28["pv_revenue_eur"], abs=1e-6
    )


def test_day_statement_matches_daily_eur():
    from voltsurfer.sim.engine import run_trade_simulation

    spot = two_level_day(cheap_ct=1.0, expensive_ct=25.0, days=2)
    sim = make_sim(True)
    inputs = trade_inputs(spot, 1.0, sim.tariff, True)
    res = run_trade_simulation(sim, inputs)

    daily = kpi.trade_daily_eur(res, sim)
    day = res.index[0].date()
    day_df = res[res.index.date == day]
    rows, totals = kpi.day_statement(day_df, sim)

    # Summenprobe: Abrechnung == Tagesertrag aus trade_daily_eur (Rundung je Posten toleriert)
    assert totals["ersparnis_heute_eur"] == pytest.approx(float(daily.iloc[0]), abs=0.06)
    # Statuskennzeichnung: Verkauf ist als Vermarktungs-Posten markiert
    sell_rows = [r for r in rows if "Verkauf" in r["Posten"]]
    assert sell_rows and all(r["Status"] == "🔓 Vermarktung" for r in sell_rows)
    haushalt_rows = [r for r in rows if "Haushalt" in r["Posten"]]
    assert haushalt_rows and all(r["Status"] == "✅ heute" for r in haushalt_rows)


def test_recommendation_rules():
    small = {"Gesamt": 8.0}
    big = {"Gesamt": 15.0}
    preset_small, _ = recommend_battery(small, has_ev=False)
    preset_big, _ = recommend_battery(big, has_ev=False)
    preset_ev, _ = recommend_battery(small, has_ev=True)
    assert "20" in preset_small
    assert "30" in preset_big
    assert "30" in preset_ev, "mit E-Auto immer das große Modell"


def test_smart_runs_placed_cheap():
    prices = week_prices(days=7)
    load = smart_runs_kw(prices, {"washer": 3})
    total_kwh = float(load.sum()) * DT_H
    assert total_kwh == pytest.approx(3 * SMART_DEVICES["washer"]["kwh_per_run"], rel=0.1)
    active = load > 0
    # läuft nur im erlaubten Fenster und in billigen Stunden (12-15-Uhr-Senke)
    assert set(prices.index[active].hour.unique()) <= set(range(8, 22))
    assert float(prices[active].mean()) <= 5.0
