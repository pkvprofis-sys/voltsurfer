"""Tests für Simulations-Engine und LP-Strategie (ohne API-Zugriff, rein synthetisch)."""
import numpy as np
import pandas as pd
import pytest

from voltsurfer.config import BatteryConfig, SimConfig, TariffConfig
from voltsurfer.sim import kpi
from voltsurfer.sim.engine import run_greedy_self_consumption, run_simulation
from voltsurfer.sim.strategy import DT_H

TZ = "Europe/Berlin"


def make_inputs(spot_ct: np.ndarray, load_kw: float, pv_kw: np.ndarray | float, tariff: TariffConfig) -> pd.DataFrame:
    idx = pd.date_range("2025-03-03", periods=len(spot_ct), freq="15min", tz=TZ)
    df = pd.DataFrame(index=idx)
    df["spot_ct"] = spot_ct
    df["dyn_ct"] = tariff.dynamic_price_ct(df["spot_ct"].to_numpy())
    df["load_kw"] = load_kw
    df["pv_kw"] = pv_kw
    return df


def two_level_day(cheap_ct: float = 2.0, expensive_ct: float = 20.0, days: int = 2) -> np.ndarray:
    """Spotpreis: billig 0-6 Uhr und 12-15 Uhr, teuer 18-21 Uhr, sonst mittel."""
    day = np.full(96, 10.0)
    day[0:24] = cheap_ct       # 00-06 Uhr
    day[48:60] = cheap_ct      # 12-15 Uhr
    day[72:84] = expensive_ct  # 18-21 Uhr
    return np.tile(day, days)


@pytest.fixture
def sim_cfg() -> SimConfig:
    return SimConfig(mode="self", battery=BatteryConfig(), tariff=TariffConfig())


def check_physics(df: pd.DataFrame, batt: BatteryConfig, soc_start: float = 0.0):
    """Energiebilanz und SoC-Fortschreibung müssen exakt schließen."""
    balance = (
        df["pv_kw"] + df["discharge_kw"] + df["grid_buy_kw"]
        - df["load_kw"] - df["charge_kw"] - df["sell_pv_kw"] - df["sell_batt_kw"]
    )
    assert np.allclose(balance, 0.0, atol=1e-4), "Energiebilanz verletzt"

    soc = df["soc_kwh"].to_numpy()
    assert (soc >= -1e-6).all() and (soc <= batt.usable_kwh + 1e-6).all(), "SoC außerhalb Grenzen"

    prev = np.concatenate([[soc_start], soc[:-1]])
    delta = (df["charge_kw"].to_numpy() * batt.eta_charge - df["discharge_kw"].to_numpy() / batt.eta_discharge) * DT_H
    assert np.allclose(soc, prev + delta, atol=1e-4), "SoC-Fortschreibung inkonsistent"


def test_arbitrage_charges_cheap_discharges_expensive(sim_cfg):
    inputs = make_inputs(two_level_day(), load_kw=1.0, pv_kw=0.0, tariff=sim_cfg.tariff)
    result = run_simulation(sim_cfg, inputs)
    check_physics(result, sim_cfg.battery)

    cheap = result["spot_ct"] <= 2.0
    expensive = result["spot_ct"] >= 20.0
    assert result.loc[cheap, "charge_kw"].sum() > 0, "lädt nicht in Billigstunden"
    assert result.loc[expensive, "discharge_kw"].sum() > 0, "entlädt nicht in Teuerstunden"
    assert result.loc[expensive, "charge_kw"].sum() < 1e-6, "lädt in Teuerstunden"


def test_lp_never_worse_than_no_battery(sim_cfg):
    inputs = make_inputs(two_level_day(days=3), load_kw=1.5, pv_kw=0.0, tariff=sim_cfg.tariff)
    result = run_simulation(sim_cfg, inputs)
    cost_with = float((result["grid_buy_kw"] * result["dyn_ct"]).sum()) * DT_H
    cost_without = float((result["load_kw"] * result["dyn_ct"]).sum()) * DT_H
    # inkl. kalkulatorischer Verschleißkosten darf das EMS nie schlechter sein
    wear = float(result["discharge_kw"].sum()) * DT_H * sim_cfg.battery.degradation_cost_ct_kwh
    assert cost_with + wear <= cost_without + 1e-6


def test_flat_prices_no_cycling(sim_cfg):
    inputs = make_inputs(np.full(192, 10.0), load_kw=1.0, pv_kw=0.0, tariff=sim_cfg.tariff)
    result = run_simulation(sim_cfg, inputs)
    # bei flachem Preis lohnt kein Zyklus (Verschleiß + Verluste) -> Speicher bleibt aus
    assert result["charge_kw"].sum() < 1e-6
    assert result["discharge_kw"].sum() < 1e-6


def test_self_mode_never_exports_battery(sim_cfg):
    inputs = make_inputs(two_level_day(), load_kw=0.5, pv_kw=0.0, tariff=sim_cfg.tariff)
    result = run_simulation(sim_cfg, inputs)
    assert result["sell_batt_kw"].abs().sum() < 1e-9
    # ohne PV darf es keine PV-Einspeisung geben
    assert result["sell_pv_kw"].abs().sum() < 1e-9
    # Entladung nie über Haushaltslast
    assert (result["discharge_kw"] <= result["load_kw"] + 1e-6).all()


def test_vpp_mode_exports_at_peak():
    cfg = SimConfig(mode="vpp")
    inputs = make_inputs(two_level_day(cheap_ct=1.0, expensive_ct=40.0), load_kw=0.2, pv_kw=0.0, tariff=cfg.tariff)
    result = run_simulation(cfg, inputs)
    check_physics(result, cfg.battery)
    assert result["sell_batt_kw"].sum() * DT_H > 1.0, "VPP speist nicht ein trotz 40 ct Spot"


def test_greedy_self_consumption(sim_cfg):
    pv = np.tile(np.concatenate([np.zeros(32), np.full(32, 4.0), np.zeros(32)]), 2)
    inputs = make_inputs(np.full(192, 10.0), load_kw=1.0, pv_kw=pv, tariff=sim_cfg.tariff)
    greedy = run_greedy_self_consumption(inputs, sim_cfg.battery)
    check_physics(greedy, sim_cfg.battery)
    # nachts wird aus dem Speicher gedeckt
    night = inputs["pv_kw"] == 0.0
    assert greedy.loc[night, "discharge_kw"].sum() > 0


def test_kpi_scenarios(sim_cfg):
    inputs = make_inputs(two_level_day(days=3), load_kw=1.0, pv_kw=0.0, tariff=sim_cfg.tariff)
    result = run_simulation(sim_cfg, inputs)
    greedy = run_greedy_self_consumption(inputs, sim_cfg.battery)
    k = kpi.scenario_costs(result, greedy, sim_cfg)
    # ohne PV: statisch mit/ohne Speicher identisch, EMS besser als dynamisch ohne Speicher
    assert k["costs_annual_eur"]["D_voltsurfer"] < k["costs_annual_eur"]["C_dynamisch_ohne"]
    assert k["cycles_per_year"] > 0
    assert k["avg_charge_price_ct"] < k["avg_discharge_price_ct"]


@pytest.mark.parametrize("start,end", [("2025-03-29", "2025-04-01"), ("2025-10-25", "2025-10-28")])
def test_dst_days_commit_cleanly(sim_cfg, start, end):
    """An DST-Tagen (92/100 Viertelstunden) darf kein Schritt doppelt oder gar nicht committet werden."""
    idx = pd.date_range(start, end, freq="15min", tz=TZ, inclusive="left")
    df = pd.DataFrame(index=idx)
    df["spot_ct"] = np.tile(two_level_day(days=1), 5)[: len(idx)]
    df["dyn_ct"] = sim_cfg.tariff.dynamic_price_ct(df["spot_ct"].to_numpy())
    df["load_kw"] = 1.0
    df["pv_kw"] = 0.0

    result = run_simulation(sim_cfg, df)
    assert result.index.equals(idx), "Ergebnis-Index weicht vom Eingabe-Raster ab"
    assert result.index.is_monotonic_increasing
    assert not result.index.duplicated().any()


def test_load_profile_scaling():
    from voltsurfer.profiles.load import household_load_kw

    idx = pd.date_range("2025-01-01", "2025-12-31 23:45", freq="15min", tz=TZ)
    load = household_load_kw(idx, annual_kwh=4000.0)
    assert abs(load.sum() * DT_H - 4000.0) < 1.0
    assert (load > 0).all()
