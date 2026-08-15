"""Tests für den OpenEMS-REST-Client (requests gemockt, kein laufendes Edge nötig)."""
import numpy as np
import pandas as pd
import pytest
import requests

from voltsurfer.openems import client as client_mod
from voltsurfer.openems.client import OpenemsClient, plan_setpoint_kw

TZ = "Europe/Berlin"


class FakeResponse:
    def __init__(self, payload=None, status=200):
        self._payload = payload or {}
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")

    def json(self):
        return self._payload


def test_get_channel_success(monkeypatch):
    calls = {}

    def fake_get(url, auth=None, timeout=None):
        calls["url"] = url
        calls["auth"] = auth
        return FakeResponse({"address": "ess0/Soc", "value": 57})

    monkeypatch.setattr(client_mod.requests, "get", fake_get)
    c = OpenemsClient(password="geheim")
    assert c.soc_percent() == 57.0
    assert calls["url"] == "http://localhost:8084/rest/channel/ess0/Soc"
    assert calls["auth"] == ("x", "geheim")


def test_offline_returns_none(monkeypatch):
    def fake_get(url, auth=None, timeout=None):
        raise requests.ConnectionError("edge down")

    monkeypatch.setattr(client_mod.requests, "get", fake_get)
    c = OpenemsClient()
    assert c.soc_percent() is None
    assert c.is_online() is False


def test_auth_error_returns_none(monkeypatch):
    monkeypatch.setattr(client_mod.requests, "get", lambda *a, **k: FakeResponse(status=401))
    assert OpenemsClient().get_channel("ess0/Soc") is None


def test_set_active_power_sign_and_unit(monkeypatch):
    sent = {}

    def fake_post(url, json=None, auth=None, timeout=None):
        sent["url"] = url
        sent["json"] = json
        return FakeResponse()

    monkeypatch.setattr(client_mod.requests, "post", fake_post)
    c = OpenemsClient()
    # 3,5 kW Entladen -> +3500 W
    assert c.set_active_power_equals_kw(3.5) is True
    assert sent["json"] == {"value": 3500}
    assert sent["url"].endswith("/rest/channel/ess0/SetActivePowerEquals")
    # 2 kW Laden (VoltSurfer: charge) wird vom Aufrufer als -2.0 übergeben -> -2000 W
    c.set_active_power_equals_kw(-2.0)
    assert sent["json"] == {"value": -2000}


def test_plan_setpoint_mapping():
    idx = pd.date_range("2026-07-20 10:00", periods=4, freq="15min", tz=TZ)
    plan = pd.DataFrame(
        {
            "charge_kw": [5.0, 0.0, 0.0, 0.0],
            "discharge_kw": [0.0, 0.0, 3.0, 0.0],
        },
        index=idx,
    )
    # Laden -> negativ
    assert plan_setpoint_kw(plan, idx[0]) == -5.0
    # idle -> 0
    assert plan_setpoint_kw(plan, idx[1]) == 0.0
    # Entladen -> positiv
    assert plan_setpoint_kw(plan, idx[2]) == 3.0
    # vor Planbeginn -> 0
    assert plan_setpoint_kw(plan, idx[0] - pd.Timedelta(hours=1)) == 0.0
