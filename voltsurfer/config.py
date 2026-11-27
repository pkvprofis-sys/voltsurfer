"""Zentrale Konfiguration: Batterie, Tarif, Simulation.

Alle Preisangaben in ct/kWh (netto, sofern nicht anders vermerkt).
Spotpreise werden intern ebenfalls in ct/kWh geführt (EUR/MWh / 10).
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class BatteryConfig:
    capacity_kwh: float = 20.0
    dod: float = 0.95  # nutzbarer Anteil der Bruttokapazität
    charge_power_kw: float = 10.0
    discharge_power_kw: float = 10.0
    roundtrip_efficiency: float = 0.90
    degradation_cost_ct_kwh: float = 2.0  # kalkulatorischer Verschleiß je entladener kWh
    price_eur: float = 8000.0  # Systempreis inkl. Installation (für Amortisation)

    @property
    def usable_kwh(self) -> float:
        return self.capacity_kwh * self.dod

    @property
    def eta_charge(self) -> float:
        return math.sqrt(self.roundtrip_efficiency)

    @property
    def eta_discharge(self) -> float:
        return math.sqrt(self.roundtrip_efficiency)


BATTERY_PRESETS: dict[str, BatteryConfig] = {
    "VoltSurfer 20 (20 kWh / 11 kW)": BatteryConfig(
        capacity_kwh=20.0, charge_power_kw=11.0, discharge_power_kw=11.0, price_eur=9000.0
    ),
    "VoltSurfer 30 (30 kWh / 11 kW)": BatteryConfig(
        capacity_kwh=30.0, charge_power_kw=11.0, discharge_power_kw=11.0, price_eur=12000.0
    ),
}


@dataclass(frozen=True)
class TariffConfig:
    # Komponenten des dynamischen Arbeitspreises (alle netto, ct/kWh)
    procurement_markup_ct: float = 1.5  # Beschaffungsaufschlag des Anbieters
    grid_fee_ct: float = 10.0  # Netzentgelt Arbeitspreis
    levies_ct: float = 2.7  # Umlagen (KWKG, Offshore, §19 StromNEV, ...)
    concession_ct: float = 1.66  # Konzessionsabgabe
    electricity_tax_ct: float = 2.05  # Stromsteuer
    vat: float = 0.19
    # Vergleichs- und Vergütungssätze
    static_price_ct: float = 35.0  # statischer Arbeitspreis (brutto)
    feed_in_tariff_ct: float = 7.86  # EEG-Vergütung Überschusseinspeisung (netto)

    # Netzdienlichkeit § 14a EnWG
    p14a_module: int = 1  # 0 = keins, 1 = Pauschalrabatt, 2 = -60 % NE auf Speicherstrom, 3 = zeitvariabel
    p14a_flat_eur_per_year: float = 150.0  # Modul 1
    # Modul 3: Netzentgelt-Faktoren und Fenster (Stunden, lokale Zeit)
    p14a_nt_factor: float = 0.25
    p14a_ht_factor: float = 2.5
    p14a_nt_hours: tuple = (0, 1, 2, 3, 4, 5, 12, 13, 14)
    p14a_ht_hours: tuple = (17, 18, 19)  # nur November-Februar

    def dynamic_price_ct(self, spot_ct):
        """Brutto-Arbeitspreis des dynamischen Tarifs (funktioniert auf Skalar und numpy-Array)."""
        net = (
            spot_ct
            + self.procurement_markup_ct
            + self.grid_fee_ct
            + self.levies_ct
            + self.concession_ct
            + self.electricity_tax_ct
        )
        return net * (1.0 + self.vat)

    def netzentgelt_ct_series(self, index) -> "np.ndarray":
        """Netzentgelt je Zeitschritt (ct/kWh) — zeitvariabel bei § 14a Modul 3."""
        import numpy as np

        base = np.full(len(index), self.grid_fee_ct)
        if self.p14a_module != 3:
            return base
        hours = index.hour.to_numpy()
        months = index.month.to_numpy()
        base[np.isin(hours, self.p14a_nt_hours)] *= self.p14a_nt_factor
        ht = np.isin(hours, self.p14a_ht_hours) & np.isin(months, (11, 12, 1, 2))
        base[ht] *= self.p14a_ht_factor
        return base

    def home_price_ct(self, spot_ct, ne_ct):
        """Endkundenpreis für direkten Netzbezug des Haushalts (brutto)."""
        net = spot_ct + self.procurement_markup_ct + ne_ct + self.levies_ct + self.concession_ct + self.electricity_tax_ct
        return net * (1.0 + self.vat)

    def charge_price_ct(self, spot_ct, ne_ct, speicherprivileg: bool):
        """Preis je geladener Speicher-kWh.

        Speicherprivileg (§ 118 EnWG / § 21 EnFG): nur Spot + Beschaffungsaufschlag —
        Abgaben fallen erst bei Letztverbrauch an. Konservativ: voller Endkundenpreis.
        """
        if speicherprivileg:
            return (spot_ct + self.procurement_markup_ct) * (1.0 + self.vat)
        return self.home_price_ct(spot_ct, ne_ct)

    def batt_to_home_fee_ct(self, ne_ct, speicherprivileg: bool):
        """Nachgelagerter Abgabenblock je kWh Speicher→Haushalt (brutto).

        Bei § 14a Modul 2 ist das Netzentgelt auf den (separat gemessenen)
        Speicherstrom um 60 % reduziert.
        """
        import numpy as np

        if not speicherprivileg:
            return np.zeros_like(np.asarray(ne_ct, dtype=float))
        ne_eff = np.asarray(ne_ct, dtype=float) * (0.4 if self.p14a_module == 2 else 1.0)
        return (ne_eff + self.levies_ct + self.concession_ct + self.electricity_tax_ct) * (1.0 + self.vat)


@dataclass(frozen=True)
class SimConfig:
    mode: str = "trade"  # "trade" = Graustrom-Arbitrage; alt: "self"/"vpp" (PV-Modell)
    annual_consumption_kwh: float = 4000.0
    pv_kwp: float = 0.0  # nur für Alt-Modus, im Produkt ungenutzt
    horizon_days: int = 2  # LP-Fenster (Tage), committet wird jeweils 1 Tag
    battery: BatteryConfig = field(default_factory=BatteryConfig)
    tariff: TariffConfig = field(default_factory=TariffConfig)
    # Trade-Modus: Haushalt + Wärmepumpe, Erlösmodell
    persons: int = 3  # 0 = Jahresverbrauch manuell über annual_consumption_kwh
    hp_area_m2: float = 0.0  # 0 = keine Wärmepumpe (Flächen-Modell)
    hp_heat_kw: float = 0.0  # >0 = WP über Heizleistung statt Fläche modellieren
    hp_renovation: str = "Saniert"
    location: tuple = (51.0, 9.0)
    speicherprivileg: bool = True
    # E-Auto (0 km = kein E-Auto) und smarte Verbraucher (Läufe pro Woche)
    ev_km_per_year: float = 0.0
    ev_battery_kwh: float = 60.0
    ev_kwh_per_100km: float = 18.0
    smart_runs_per_week: tuple = ()  # z. B. (("washer", 3), ("dryer", 2), ("dishwasher", 5))

    def cache_key(self, extra: str = "") -> str:
        payload = json.dumps(asdict(self), sort_keys=True) + extra
        return hashlib.sha256(payload.encode()).hexdigest()[:16]
