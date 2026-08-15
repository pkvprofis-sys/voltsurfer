"""Einstellungen — bewusst einfach: Haushalt, Speicher, Netzdienlichkeit, Hardware."""
from __future__ import annotations

import streamlit as st

from app import common
from voltsurfer.config import BATTERY_PRESETS
from voltsurfer.profiles.heatpump import SPECIFIC_HEAT_KWH_M2

plant = common.get_plant()
s = plant.settings
changed = False

st.subheader("👥 Haushalt")
c1, c2, c3 = st.columns(3)
persons = c1.select_slider("Personen", options=[1, 2, 3, 4, 5], value=int(s.get("persons", 3)))
hp_on = c2.toggle("Wärmepumpe (Luft-Wasser)", value=bool(s.get("hp_enabled", True)))
if hp_on:
    hp_area = c2.number_input("Wohnfläche (m²)", 60.0, 400.0, float(s.get("hp_area_m2", 140.0)), 10.0)
    hp_renov = c2.selectbox("Haus-Zustand", list(SPECIFIC_HEAT_KWH_M2),
                            index=list(SPECIFIC_HEAT_KWH_M2).index(s.get("hp_renovation", "Saniert")))
else:
    hp_area, hp_renov = float(s.get("hp_area_m2", 140.0)), s.get("hp_renovation", "Saniert")
loc = s.get("location", [51.0, 9.0])
lat = c3.number_input("Standort Breitengrad", 47.0, 55.0, float(loc[0]), 0.1,
                      help="Für die Wetterdaten der Wärmepumpe (Default: Mitte Deutschlands)")
lon = c3.number_input("Standort Längengrad", 6.0, 15.0, float(loc[1]), 0.1)
changed |= (persons, hp_on, hp_area, hp_renov, [lat, lon]) != (
    s.get("persons"), s.get("hp_enabled"), s.get("hp_area_m2"), s.get("hp_renovation"), loc)
s.update(persons=persons, hp_enabled=hp_on, hp_area_m2=hp_area, hp_renovation=hp_renov, location=[lat, lon])

st.subheader("🔋 Speicher & Strategie")
c1, c2, c3 = st.columns(3)
preset = c1.selectbox("VoltSurfer-Modell", list(BATTERY_PRESETS),
                      index=list(BATTERY_PRESETS).index(s["battery_preset"]) if s["battery_preset"] in BATTERY_PRESETS else 0)
buffer_pct = c2.slider("Sicherheitspuffer (%)", 5, 40, int(s["buffer_frac"] * 100), 5,
                       help="Bleibt immer im Speicher — für Notfälle und Batterieschonung.")
vpp = c3.toggle("Verkauf erlauben (VPP)", value=s["vpp_enabled"],
                help="Überschüssige Energie zu Spitzenpreisen an der Börse verkaufen.")
privileg = c3.toggle("Speicherprivileg ansetzen", value=bool(s.get("speicherprivileg", True)),
                     help="Abgabenfreiheit der Rückspeisung (§ 21 EnFG / § 118 EnWG). Aus = konservative Rechnung.")
changed |= (preset, buffer_pct / 100.0, vpp, privileg) != (
    s["battery_preset"], s["buffer_frac"], s["vpp_enabled"], s.get("speicherprivileg"))
s.update(battery_preset=preset, buffer_frac=buffer_pct / 100.0, vpp_enabled=vpp, speicherprivileg=privileg)

st.subheader("🔌 Netzdienlichkeit (§ 14a EnWG)")
t = s.get("tariff", {})
c1, c2 = st.columns([2, 3])
module_labels = {0: "Kein § 14a", 1: "Modul 1: Pauschalrabatt (~150 €/Jahr)",
                 2: "Modul 2: −60 % Netzentgelt auf Speicherstrom", 3: "Modul 3: Zeitvariables Netzentgelt"}
module = c1.radio("Modul", list(module_labels), format_func=module_labels.get,
                  index=int(t.get("p14a_module", 1)))
c2.caption(
    "Der Speicher ist eine steuerbare Verbrauchseinrichtung: Im Engpassfall darf der "
    "Netzbetreiber den Netzbezug auf 4,2 kW dimmen — dafür gibt es reduzierte Netzentgelte. "
    "Bei Modul 3 legt das EMS die Ladefenster automatisch in die Niedertarif-Zeiten."
)

with st.expander("⚙️ Experten: Tarif & Kosten"):
    e1, e2, e3, e4 = st.columns(4)
    static_ct = e1.number_input("Statischer Vergleichspreis (ct/kWh)", 25.0, 60.0, float(t.get("static_price_ct", 35.0)), 0.5)
    grid_fee = e2.number_input("Netzentgelt (ct/kWh)", 4.0, 18.0, float(t.get("grid_fee_ct", 10.0)), 0.5)
    markup = e3.number_input("Beschaffungsaufschlag (ct/kWh)", 0.0, 5.0, float(t.get("procurement_markup_ct", 1.5)), 0.25)
    flat_eur = e4.number_input("§ 14a Modul-1-Rabatt (€/Jahr)", 0.0, 400.0, float(t.get("p14a_flat_eur_per_year", 150.0)), 10.0)

new_tariff = {
    "static_price_ct": static_ct,
    "grid_fee_ct": grid_fee,
    "procurement_markup_ct": markup,
    "p14a_module": int(module),
    "p14a_flat_eur_per_year": flat_eur,
}
changed |= new_tariff != t
s["tariff"] = new_tariff

st.subheader("🖥️ Hardware-Kopplung (OpenEMS)")
oe = common.openems_settings(plant)
c1, c2, c3 = st.columns(3)
oe_enabled = c1.toggle("Kopplung aktiv", value=oe["enabled"], key="oe_enabled")
oe_url = c2.text_input("Edge-REST-URL", value=oe["base_url"])
oe_pw = c3.text_input("Edge-Passwort", value=oe["password"], type="password")
if (oe_enabled, oe_url, oe_pw) != (oe["enabled"], oe["base_url"], oe["password"]):
    oe.update(enabled=oe_enabled, base_url=oe_url, password=oe_pw)
    changed = True

st.subheader("🚗 Geräte")
cols = st.columns(3)
with cols[0]:
    wb = s["devices"].setdefault("wallbox", {})
    wb_target = st.number_input("Wallbox: Ladeziel (kWh/Tag)", 0.0, 60.0, float(wb.get("target_kwh_per_day", 15.0)), 1.0)
    changed |= wb_target != wb.get("target_kwh_per_day")
    wb["target_kwh_per_day"] = wb_target
with cols[1]:
    st.caption("Ein-/Ausschalten der Geräte direkt im Live-Betrieb. Die Wärmepumpe wird oben unter dem Punkt Haushalt konfiguriert.")

if changed:
    plant.save()
    common._live_inputs.clear()
    st.toast("Einstellungen gespeichert", icon="💾")

st.divider()
with st.expander("⚠️ Zurücksetzen"):
    st.warning("Setzt den simulierten Anlagenzustand zurück (SoC, Zyklen, Historie, Einstellungen).")
    if st.button("Anlagenzustand komplett zurücksetzen"):
        plant.reset()
        st.session_state.pop("plant_advanced", None)
        st.cache_resource.clear()
        st.cache_data.clear()
        st.rerun()
