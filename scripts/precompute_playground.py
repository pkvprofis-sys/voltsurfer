"""Rechnet den Playground-Backtest (2023 bis heute) für die aktuelle Anlagen-Config vor."""
import datetime as dt
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voltsurfer.live.state import SimulatedPlant
from voltsurfer.sim import kpi
from voltsurfer.sim.engine import cached_trade_run

plant = SimulatedPlant()
sim = plant.sim_config()
start, end = dt.date(2023, 1, 1), dt.date.today() - dt.timedelta(days=2)

t0 = time.time()
result = cached_trade_run(sim, start, end)
k = kpi.trade_kpis(result, sim)
print(f"{time.time() - t0:.0f}s | {plant.settings['battery_preset']} | Privileg={sim.speicherprivileg}")
print(f"Gesamtertrag: {k['total_benefit_eur_pa']:,.0f} EUR/a "
      f"(Handel {k['trade_profit_eur_pa']:,.0f} + Verbrauch {k['consumption_saving_eur_pa']:,.0f} "
      f"+ P14a {k['p14a_eur_pa']:,.0f}) | Amortisation {k['amortization_years']:.1f} J")
for year in sorted(result.index.year.unique()):
    ky = kpi.trade_kpis(result[result.index.year == year], sim)
    print(f"  {year}: {ky['total_benefit_eur_pa']:,.0f} EUR/a | Verkauf {ky['sold_kwh_pa']:,.0f} kWh "
          f"| Ø Kauf {ky['avg_charge_spot_ct']:.1f} ct | Ø Verkauf {ky['avg_sell_spot_ct']:.1f} ct")
