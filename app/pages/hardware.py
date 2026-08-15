"""Hardware-Kopplung: OpenEMS Edge per REST (Simulator oder echte Anlage)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app import common, theme
from voltsurfer.openems.client import plan_setpoint_kw

plant = common.get_plant()
cfg = common.openems_settings(plant)
client = common.openems_client(plant)

st.subheader("⚙️ OpenEMS-Kopplung")

c1, c2 = st.columns([1, 2])
with c1:
    enabled = st.toggle("Kopplung aktiv", value=cfg["enabled"],
                        help="Verbindet VoltSurfer mit einem laufenden OpenEMS Edge (REST, Port 8084).")
    if enabled != cfg["enabled"]:
        cfg["enabled"] = enabled
        plant.save()
        st.rerun()

if not cfg["enabled"]:
    st.info(
        "Kopplung ist ausgeschaltet — VoltSurfer nutzt die interne Simulation. "
        "Zum Aktivieren: Toggle oben einschalten (Edge muss laufen)."
    )
    with st.expander("So startest du das lokale OpenEMS Edge (Simulator)"):
        st.markdown(
            """
1. **Edge starten:** `powershell scripts/run_openems.ps1`
2. **Einmalig konfigurieren:** `.venv\\Scripts\\python.exe scripts\\openems_bootstrap.py`
   (legt Simulator-ESS 20 kWh, Netzzähler mit H0-Profil und die REST-API an)
3. Hier die **Kopplung aktivieren** — Status springt auf „online"

Details: `docs/openems-integration.md`
            """
        )
    st.stop()

online = client.is_online()
with c2:
    if online:
        st.success("🟢 OpenEMS Edge online — " + cfg["base_url"])
    else:
        st.error("🔴 OpenEMS Edge nicht erreichbar — läuft der Edge-Prozess? (scripts/run_openems.ps1, dann Bootstrap)")

if not online:
    st.stop()

# ------------------------------------------------------------------ Betriebsmodus
mode_labels = {
    "openems_tou": "🤖 OpenEMS optimiert selbst (Time-of-Use, wie FENECON)",
    "voltsurfer_push": "📤 VoltSurfer-Fahrplan-Push (unser Planer sendet Sollwerte)",
}
mode = st.radio("Betriebsmodus", list(mode_labels), format_func=mode_labels.get,
                index=list(mode_labels).index(cfg.get("mode", "openems_tou")))
if mode != cfg.get("mode"):
    cfg["mode"] = mode
    plant.save()
    st.rerun()

tou_installed = client.get_channel("ctrlEssTimeOfUseTariff0/State") is not None
if mode == "openems_tou":
    if tou_installed:
        sm = client.get_channel("ctrlEssTimeOfUseTariff0/StateMachine")
        icon, text = common.TOU_STATES.get(int(sm) if sm is not None else -1, ("❔", f"Status {sm}"))
        price = client.get_channel("ctrlEssTimeOfUseTariff0/QuarterlyPrices")
        t1, t2, t3 = st.columns(3)
        t1.metric("ToU-Controller", f"{icon} aktiv", delta=text, delta_color="off")
        t2.metric("Preissignal (aWATTar)", f"{float(price) / 10:.1f} ct/kWh" if price is not None else "—",
                  help="Aktueller Viertelstundenpreis, den der OpenEMS-Optimierer sieht.")
        t3.metric("Prädiktor", "sammelt Daten",
                  help="Der Verbrauchs-Prädiktor braucht einige Stunden Historie (Timedata.Rrd4j), "
                       "bis die Prognosen die Ladeplanung voll steuern.")
        st.caption("OpenEMS entscheidet autonom: Billigstunden laden, Teuerstunden Eigenverbrauch/Verkauf — "
                   "kein Sollwert-Push von VoltSurfer in diesem Modus.")
    else:
        st.warning("ToU-Optimierer noch nicht installiert — einmalig ausführen: "
                   "`.venv\\Scripts\\python.exe scripts\\openems_bootstrap.py --tou`")
    control = False
else:
    control = st.toggle(
        "🎛️ Fahrplan-Sollwerte senden",
        value=cfg.get("control", False),
        help="Sendet alle 30 s den aktuellen 15-min-Sollwert des Fahrplans an ess0/SetActivePowerEquals. "
             "Der Push übersteuert den ToU-Controller (Scheduler-Reihenfolge).",
    )
    if control != cfg.get("control", False):
        cfg["control"] = control
        plant.save()
        st.rerun()


@st.fragment(run_every="30s")
def live_view() -> None:
    soc = client.soc_percent()
    ess_kw = client.ess_active_power_kw()
    grid_kw = client.grid_active_power_kw()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("SoC (ess0)", f"{soc:.0f} %" if soc is not None else "—")
    if ess_kw is not None:
        direction = "entlädt" if ess_kw > 0.05 else ("lädt" if ess_kw < -0.05 else "idle")
        k2.metric("Speicherleistung", f"{ess_kw:+.2f} kW", delta=direction, delta_color="off")
    else:
        k2.metric("Speicherleistung", "—")
    k3.metric("Netzleistung (meter0)", f"{grid_kw:+.2f} kW" if grid_kw is not None else "—",
              help="Positiv = Bezug, negativ = Einspeisung")

    if cfg.get("mode") == "voltsurfer_push" and cfg.get("control", False):
        plan, _, _, now = common.make_plan(plant)
        setpoint = plan_setpoint_kw(plan, now)
        ok = client.set_active_power_equals_kw(setpoint)
        label = "Laden" if setpoint < -0.05 else ("Entladen" if setpoint > 0.05 else "Idle")
        k4.metric("Gesendeter Sollwert", f"{setpoint:+.2f} kW",
                  delta=f"{label} · {'OK' if ok else 'Fehler!'}",
                  delta_color="off" if ok else "inverse")
    elif cfg.get("mode") == "openems_tou":
        k4.metric("Steuerung", "🤖 OpenEMS ToU", delta="autonom", delta_color="off")
    else:
        k4.metric("Gesendeter Sollwert", "—", delta="Steuerung aus", delta_color="off")

    st.caption(f"Aktualisiert alle 30 s · zuletzt {pd.Timestamp.now(tz='Europe/Berlin'):%H:%M:%S} Uhr")


live_view()

if cfg.get("mode") == "voltsurfer_push" and st.button("Sollwert jetzt einmalig senden"):
    plan, _, _, now = common.make_plan(plant)
    setpoint = plan_setpoint_kw(plan, now)
    if client.set_active_power_equals_kw(setpoint):
        st.toast(f"Gesendet: {setpoint:+.2f} kW an ess0/SetActivePowerEquals", icon="⚡")
    else:
        st.toast("Senden fehlgeschlagen", icon="⚠️")

st.divider()
st.markdown(
    f"""
**Architektur:** VoltSurfer-Planer → REST (`{cfg['base_url']}/rest/channel/…`) →
OpenEMS Edge → Simulator-ESS (später: echte Wechselrichter über OpenEMS-Treiber).
Vorzeichen: negativ = laden, positiv = entladen (OpenEMS-Konvention).
Felix-Console zum Inspizieren: [http://localhost:8080/system/console](http://localhost:8080/system/console) (admin/admin).
    """
)
