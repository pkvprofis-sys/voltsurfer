"""Tests für das Graustrom-Trade-Kostenmodell, § 14a und das Wärmepumpen-Profil."""
import datetime as dt

import numpy as np
import pandas as pd
import pytest

from voltsurfer.config import BATTERY_PRESETS, SimConfig, TariffConfig
from voltsurfer.profiles import heatpump as hp_mod
from voltsurfer.sim import kpi
from voltsurfer.sim.engine import run_trade_simulation
from voltsurfer.sim.strategy import DT_H
from voltsurfer.tests.test_sim import TZ, two_level_day

BATT = BATTERY_PRESETS["VoltSurfer 20 (20 kWh / 11 kW)"]


def trade_inputs(spot: np.ndarray, load_kw: float, tariff: TariffConfig, privileg: bool) -> pd.DataFrame:
    idx = pd.date_range("2025-06-02", periods=len(spot), freq="15min", tz=TZ)
    df = pd.DataFrame(index=idx)
    df["spot_ct"] = spot
    ne = tariff.netzentgelt_ct_series(idx)
    df["ne_ct"] = ne
    df["home_price_ct"] = tariff.home_price_ct(spot, ne)
    df["charge_price_ct"] = tariff.charge_price_ct(spot, ne, privileg)
    df["batt_home_fee_ct"] = tariff.batt_to_home_fee_ct(ne, privileg)
    df["load_kw"] = load_kw
    return df


def make_sim(privileg: bool = True, tariff: TariffConfig | None = None) -> SimConfig:
    return SimConfig(mode="trade", battery=BATT, tariff=tariff or TariffConfig(), speicherprivileg=privileg)


def test_privileg_arbitrage_profitable_and_11kw():
    sim = make_sim(True)
    inputs = trade_inputs(two_level_day(cheap_ct=1.0, expensive_ct=25.0, days=2), 0.3, sim.tariff, True)
    res = run_trade_simulation(sim, inputs)

    assert res["charge_kw"].max() <= 11.0 + 1e-6
    assert res["discharge_kw"].max() <= 11.0 + 1e-6
    sold = float(res["sell_batt_kw"].sum()) * DT_H
    assert sold > 10.0, "Privileg-Modell muss deutlich verkaufen"
    # kauft billig, verkauft klar darüber; die Peak-Stunden werden voll genutzt
    avg_charge = float(res.loc[res["charge_kw"] > 0.05, "spot_ct"].mean())
    avg_sell = float(res.loc[res["sell_batt_kw"] > 0.05, "spot_ct"].mean())
    assert avg_charge < 5.0
    assert avg_sell > avg_charge + 8.0
    peak = res["spot_ct"] >= 25.0
    assert float(res.loc[peak, "sell_batt_kw"].mean()) > 5.0, "Peak-Stunden nicht voll genutzt"

    k = kpi.trade_kpis(res, sim)
    assert k["trade_profit_eur"] > 0
    # Summenprobe der Zerlegung
    assert k["total_benefit_eur"] == pytest.approx(
        k["trade_profit_eur"] + k["consumption_saving_eur"] + k["p14a_eur"], abs=1e-6
    )


def test_conservative_kills_trading():
    sim = make_sim(False)
    inputs = trade_inputs(two_level_day(cheap_ct=1.0, expensive_ct=25.0, days=2), 0.3, sim.tariff, False)
    res = run_trade_simulation(sim, inputs)
    sold = float(res["sell_batt_kw"].sum()) * DT_H
    # volle Abgaben auf Ladestrom: Verkauf zu Spot lohnt praktisch nie
    assert sold < 1.0


def test_energy_balance_and_soc():
    sim = make_sim(True)
    inputs = trade_inputs(two_level_day(days=2), 1.0, sim.tariff, True)
    res = run_trade_simulation(sim, inputs)
    assert np.allclose(res["buy_home_kw"] + res["batt_home_kw"], res["load_kw"], atol=1e-4)
    soc = res["soc_kwh"].to_numpy()
    assert (soc >= -1e-6).all() and (soc <= BATT.usable_kwh + 1e-6).all()
    prev = np.concatenate([[0.0], soc[:-1]])
    delta = (res["charge_kw"].to_numpy() * BATT.eta_charge
             - res["discharge_kw"].to_numpy() / BATT.eta_discharge) * DT_H
    assert np.allclose(soc, prev + delta, atol=1e-4)


def test_p14a_module3_shifts_home_supply():
    """Bei zeitvariablem Netzentgelt deckt der Speicher den Haushalt in HT-Fenstern."""
    tariff = TariffConfig(p14a_module=3)
    idx = pd.date_range("2025-01-06", periods=96, freq="15min", tz=TZ)  # Januar -> HT aktiv
    ne = tariff.netzentgelt_ct_series(idx)
    assert ne.min() == pytest.approx(10.0 * 0.25)
    assert ne.max() == pytest.approx(10.0 * 2.5)

    sim = make_sim(True, tariff)
    spot = np.full(96, 10.0)
    spot[0:24] = 2.0  # billige Nacht
    inputs = trade_inputs(spot, 1.0, tariff, True)
    inputs.index = idx
    inputs["home_price_ct"] = tariff.home_price_ct(spot, ne)
    inputs["batt_home_fee_ct"] = tariff.batt_to_home_fee_ct(ne, True)
    inputs["charge_price_ct"] = tariff.charge_price_ct(spot, ne, True)
    res = run_trade_simulation(sim, inputs)
    ht = (idx.hour >= 17) & (idx.hour < 20)
    # im HT-Fenster kommt der Haushalt aus dem Speicher, nicht aus dem Netz
    assert float(res.loc[ht, "buy_home_kw"].sum()) < 0.1
    assert float(res.loc[ht, "batt_home_kw"].sum()) > 0.5


def test_heatpump_profile(monkeypatch):
    idx_days = pd.date_range("2025-01-01", "2025-12-31", freq="D", tz=TZ)
    # synthetisches Jahr: Winter -5 Grad, Sommer 22 Grad
    temps = 8.5 - 13.5 * np.cos(2 * np.pi * (idx_days.dayofyear - 15) / 365.0)
    temp_series = pd.Series(temps, index=idx_days, name="temp_c")
    monkeypatch.setattr(hp_mod.weather, "daily_mean_temp_c", lambda *a, **k: temp_series)

    idx = pd.date_range("2025-01-01", "2025-12-31 23:45", freq="15min", tz=TZ)
    hp = hp_mod.heatpump_load_kw(idx, area_m2=140, renovation="Saniert")
    annual = float(hp.sum()) * DT_H
    assert 2500 < annual < 6500, f"WP-Jahresstrom unplausibel: {annual:.0f} kWh"
    jan = float(hp[hp.index.month == 1].sum()) * DT_H
    jul = float(hp[hp.index.month == 7].sum()) * DT_H
    assert jan > 5 * jul, "Winter muss deutlich über Sommer liegen"
    assert (hp >= 0).all()

    # ohne Fläche keine WP-Last
    zero = hp_mod.heatpump_load_kw(idx, area_m2=0)
    assert float(zero.abs().sum()) == 0.0


def test_charge_price_components():
    t = TariffConfig()
    # Privileg: nur Spot + Aufschlag (x MwSt)
    assert t.charge_price_ct(2.0, 10.0, True) == pytest.approx((2.0 + 1.5) * 1.19)
    # konservativ: voller Endkundenpreis
    assert t.charge_price_ct(2.0, 10.0, False) == pytest.approx(t.home_price_ct(2.0, 10.0))
    # Negativpreis: Laden wird bezahlt
    assert t.charge_price_ct(-5.0, 10.0, True) < 0
