"""Konfiguriert ein laufendes OpenEMS Edge als VoltSurfer-Simulator-Anlage.

Legt per Felix-ConfigAdmin (Web-Console, Port 8080, admin/admin) die Komponenten
an — Spiegel des VoltSurfer-20-Presets (20 kWh / 10 kW):

  datasource0  Simulator.Datasource.CSV.Predefined (H0-Haushaltsprofil)
  meter0       Simulator.GridMeter.Acting
  ess0         Simulator.EssSymmetric.Reacting (20 kWh, SoC 50 %)
  ctrlDebugLog0  Controller.Debug.Log
  ctrlApiRest0   Controller.Api.Rest.ReadWrite (Port 8084)
  scheduler0     Scheduler.AllAlphabetically

Idempotent: Ist die REST-API bereits erreichbar, wird nichts erneut angelegt.

Aufruf:  python scripts/openems_bootstrap.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voltsurfer.openems.client import OpenemsClient

FELIX_URL = "http://localhost:8080/system/console/configMgr"
FELIX_AUTH = ("admin", "admin")
FACTORY_ENDPOINT = f"{FELIX_URL}/%5BTemporary%20PID%20replacement%5D"

# (factoryPid, Komponenten-ID, zusätzliche Properties)
COMPONENTS: list[tuple[str, str, dict]] = [
    (
        "Simulator.Datasource.CSV.Predefined",
        "datasource0",
        {
            "source": "H0_HOUSEHOLD_SUMMER_WEEKDAY_STANDARD_LOAD_PROFILE",
            "factor": "10000",
            "timeDelta": "-1",
            "format": "GERMAN_EXCEL",
        },
    ),
    (
        "Simulator.GridMeter.Acting",
        "meter0",
        {"datasource.id": "datasource0", "needFrequencyStepResponse": "false"},
    ),
    (
        "Simulator.EssSymmetric.Reacting",
        "ess0",
        {
            "capacity": "20000",
            "maxApparentPower": "10000",
            "maxChargePower": "10000",
            "maxDischargePower": "10000",
            "initialSoc": "50",
            "gridMode": "ON_GRID",
        },
    ),
    ("Controller.Debug.Log", "ctrlDebugLog0", {}),
    ("Controller.Api.Rest.ReadWrite", "ctrlApiRest0", {"port": "8084", "apiTimeout": "60"}),
    ("Scheduler.AllAlphabetically", "scheduler0", {}),
]

# OpenEMS' eigener Time-of-Use-Optimierer (Phase 6): Preisquelle aWATTar (kostenlos),
# Timedata + Prädiktor für Verbrauchsprognosen, dann der ToU-Controller selbst.
TOU_COMPONENTS: list[tuple[str, str, dict]] = [
    ("Timedata.Rrd4j", "rrd4j0", {}),
    ("Predictor.PersistenceModel", "predictor0", {}),
    ("TimeOfUseTariff.Awattar", "timeOfUseTariff0", {"zone": "GERMANY"}),
    ("Controller.Ess.Time-Of-Use-Tariff", "ctrlEssTimeOfUseTariff0", {"ess.id": "ess0", "mode": "AUTOMATIC"}),
]


def create_component(factory_pid: str, comp_id: str, props: dict) -> None:
    data = {
        "apply": "true",
        "factoryPid": factory_pid,
        "id": comp_id,
        "alias": "",
        "enabled": "true",
        **props,
        "propertylist": ",".join(["id", "alias", "enabled", *props.keys()]),
    }
    resp = requests.post(FACTORY_ENDPOINT, data=data, auth=FELIX_AUTH, timeout=15)
    resp.raise_for_status()
    print(f"  angelegt: {comp_id} ({factory_pid})")


def wait_for(check, label: str, attempts: int = 30, delay: float = 2.0) -> bool:
    for _ in range(attempts):
        if check():
            print(f"  OK: {label}")
            return True
        time.sleep(delay)
    print(f"  FEHLER: {label} nicht erreichbar")
    return False


def install_tou(client: OpenemsClient) -> int:
    """Installiert den OpenEMS-ToU-Optimierer (idempotent)."""
    if client.get_channel("ctrlEssTimeOfUseTariff0/State") is not None:
        print("ToU-Optimierer bereits installiert.")
        return 0
    print("Installiere OpenEMS Time-of-Use-Optimierer …")
    for factory_pid, comp_id, props in TOU_COMPONENTS:
        create_component(factory_pid, comp_id, props)
        time.sleep(1.0)
    if not wait_for(lambda: client.get_channel("ctrlEssTimeOfUseTariff0/State") is not None,
                    "ToU-Controller aktiv"):
        return 1
    print("Fertig. Hinweis: Der Prädiktor braucht einige Stunden Timedata-Historie,")
    print("bis die Prognosen greifen — solange fährt der Controller konservativ.")
    return 0


def main() -> int:
    client = OpenemsClient()

    if client.is_online():
        if "--tou" in sys.argv:
            return install_tou(client)
        print("REST-API bereits erreichbar — Basis-Bootstrap übersprungen.")
        print(f"  ess0/Soc = {client.soc_percent()} %")
        print("ToU-Optimierer installieren mit:  python scripts/openems_bootstrap.py --tou")
        return 0

    print("Warte auf Felix-Console (Port 8080) …")
    def felix_up() -> bool:
        try:
            return requests.get(FELIX_URL, auth=FELIX_AUTH, timeout=3).status_code == 200
        except requests.RequestException:
            return False

    if not wait_for(felix_up, "Felix-Console"):
        print("Läuft OpenEMS Edge? Start: scripts/run_openems.ps1")
        return 1

    print("Lege Komponenten an …")
    for factory_pid, comp_id, props in COMPONENTS:
        create_component(factory_pid, comp_id, props)
        time.sleep(1.0)

    print("Warte auf REST-API (Port 8084) …")
    if not wait_for(client.is_online, "REST-API"):
        return 1

    if not wait_for(lambda: client.soc_percent() is not None, "ess0/Soc"):
        return 1
    print(f"Fertig. ess0/Soc = {client.soc_percent()} %")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
