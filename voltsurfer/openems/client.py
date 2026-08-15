"""REST-Client für OpenEMS Edge (Controller.Api.Rest, Default-Port 8084).

Kanaladressen: "<komponente>/<Channel>", z. B. "ess0/Soc".
Auth: HTTP Basic mit Benutzer "x" und dem Edge-Passwort (Default "admin").

Vorzeichenkonvention:
- VoltSurfer-Plan: charge_kw ≥ 0 (laden), discharge_kw ≥ 0 (entladen)
- OpenEMS ActivePower/SetActivePowerEquals: **negativ = laden, positiv = entladen**
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import requests

TIMEOUT_S = 3.0


@dataclass
class OpenemsConfig:
    enabled: bool = False
    base_url: str = "http://localhost:8084"
    password: str = "admin"


class OpenemsClient:
    def __init__(self, base_url: str = "http://localhost:8084", password: str = "admin") -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = ("x", password)

    # ------------------------------------------------------------- Basis
    def get_channel(self, address: str):
        """Wert eines Kanals oder None bei Fehler/offline."""
        try:
            resp = requests.get(
                f"{self.base_url}/rest/channel/{address}", auth=self.auth, timeout=TIMEOUT_S
            )
            resp.raise_for_status()
            return resp.json().get("value")
        except requests.RequestException:
            return None

    def set_channel(self, address: str, value) -> bool:
        try:
            resp = requests.post(
                f"{self.base_url}/rest/channel/{address}",
                json={"value": value},
                auth=self.auth,
                timeout=TIMEOUT_S,
            )
            resp.raise_for_status()
            return True
        except requests.RequestException:
            return False

    def is_online(self) -> bool:
        return self.get_channel("_sum/State") is not None

    # ------------------------------------------------------------- Komfort
    def soc_percent(self) -> float | None:
        value = self.get_channel("ess0/Soc")
        return float(value) if value is not None else None

    def ess_active_power_kw(self) -> float | None:
        value = self.get_channel("ess0/ActivePower")
        return float(value) / 1000.0 if value is not None else None

    def grid_active_power_kw(self) -> float | None:
        value = self.get_channel("meter0/ActivePower")
        return float(value) / 1000.0 if value is not None else None

    def set_active_power_equals_kw(self, kw: float) -> bool:
        """Sollwert in kW nach OpenEMS-Konvention (positiv = entladen) senden."""
        return self.set_channel("ess0/SetActivePowerEquals", int(round(kw * 1000.0)))


def plan_setpoint_kw(plan: pd.DataFrame, now: pd.Timestamp) -> float:
    """Sollwert des aktuellen 15-min-Schritts in OpenEMS-Konvention (kW).

    Laden (charge_kw) → negativ, Entladen (discharge_kw) → positiv, sonst 0.
    """
    past = plan[plan.index <= now]
    if not len(past):
        return 0.0
    row = past.iloc[-1]
    return float(row["discharge_kw"]) - float(row["charge_kw"])
