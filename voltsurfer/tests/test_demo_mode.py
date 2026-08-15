"""Tests für den Demo-Modus: Web-Besucher dürfen den Anlagenzustand nicht teilen."""
import json

from voltsurfer.live import state as state_mod
from voltsurfer.live.state import SimulatedPlant


def test_demo_plant_writes_nothing(tmp_path, monkeypatch):
    """save() darf im Demo-Modus keine Datei anlegen — sonst überschreiben sich Besucher."""
    pfad = tmp_path / "plant_state.json"
    monkeypatch.setattr(state_mod, "STATE_PATH", pfad)

    plant = SimulatedPlant(demo=True)
    plant.soc_kwh = 12.5
    plant.settings["persons"] = 5
    plant.save()

    assert not pfad.exists(), "Demo-Modus hat auf die Platte geschrieben"


def test_demo_plant_ignores_existing_state(tmp_path, monkeypatch):
    """Ein vorhandener Betriebszustand darf nicht in die öffentliche Demo lecken."""
    pfad = tmp_path / "plant_state.json"
    pfad.write_text(json.dumps({"soc_kwh": 17.0, "cycles": 99.0, "settings": {"persons": 5}}))
    monkeypatch.setattr(state_mod, "STATE_PATH", pfad)

    demo = SimulatedPlant(demo=True)
    assert demo.soc_kwh == 0.0
    assert demo.cycles == 0.0
    assert demo.settings["persons"] == state_mod.DEFAULT_SETTINGS["persons"]

    # Der normale Betrieb liest den Zustand weiterhin
    echt = SimulatedPlant()
    assert echt.cycles == 99.0


def test_demo_plants_are_independent(tmp_path, monkeypatch):
    """Zwei Besucher = zwei Anlagen, die sich nicht beeinflussen."""
    monkeypatch.setattr(state_mod, "STATE_PATH", tmp_path / "plant_state.json")

    besucher_a = SimulatedPlant(demo=True)
    besucher_b = SimulatedPlant(demo=True)

    besucher_a.settings["persons"] = 5
    besucher_a.soc_kwh = 9.0

    assert besucher_b.settings["persons"] != 5
    assert besucher_b.soc_kwh == 0.0


def test_demo_reset_stays_in_demo_mode(tmp_path, monkeypatch):
    pfad = tmp_path / "plant_state.json"
    pfad.write_text(json.dumps({"soc_kwh": 5.0}))
    monkeypatch.setattr(state_mod, "STATE_PATH", pfad)

    plant = SimulatedPlant(demo=True)
    plant.reset()

    assert plant.demo is True
    assert pfad.exists(), "reset() im Demo-Modus darf fremde Zustandsdateien nicht löschen"
