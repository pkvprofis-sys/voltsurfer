"""Rechnet die 2-Jahres-Simulation für beide Betriebsmodi vor (füllt den Disk-Cache)."""
import datetime as dt
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voltsurfer.config import SimConfig
from voltsurfer.sim import kpi
from voltsurfer.sim.engine import cached_run, run_greedy_self_consumption

today = dt.date.today() - dt.timedelta(days=2)
start = max(dt.date(2024, 7, 1), today - dt.timedelta(days=730))

for mode in ["self", "vpp"]:
    sim = SimConfig(mode=mode, pv_kwp=10.0)
    t0 = time.time()
    res = cached_run(sim, start, today)
    greedy = run_greedy_self_consumption(res, sim.battery)
    k = kpi.scenario_costs(res, greedy, sim)
    print(
        f"{mode}: {time.time() - t0:.0f}s | "
        f"Ersparnis {k['savings_annual_eur']:,.0f} EUR/a | "
        f"Zyklen {k['cycles_per_year']:.0f}/a | "
        f"Amortisation {k['amortization_years']:.1f} J | "
        f"Einspeisung {k['grid_feed_in_kwh_per_year']:,.0f} kWh/a | "
        f"Kosten A={k['costs_annual_eur']['A_statisch_ohne']:,.0f} "
        f"B={k['costs_annual_eur']['B_statisch_speicher']:,.0f} "
        f"C={k['costs_annual_eur']['C_dynamisch_ohne']:,.0f} "
        f"D={k['costs_annual_eur']['D_voltsurfer']:,.0f} EUR/a"
    )
