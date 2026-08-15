"""Live-Betrieb im OpenEMS-Look: Kreis-Energiemonitor + Widget-Karten."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from app import common, theme
from app.monitor import energy_monitor_html, monitor_data_from_plan
from voltsurfer.data import weather
from voltsurfer.live import prices_live
from voltsurfer.live.devices import next_run_window
from voltsurfer.profiles.heatpump import daily_electric_kwh_for_temp
from voltsurfer.sim.strategy import DT_H


@st.cache_data(ttl=1800, show_spinner=False)
def get_cached_forecast(lat: float, lon: float) -> dict:
    return weather.get_forecast(lat, lon)


plant = common.get_plant()
plan, schedule, devices, now = common.make_plan(plant)

if plan.attrs.get("lp_fallback"):
    st.warning("⚠️ Optimierung vorübergehend im Regelmodus (Top-N).")

live_soc = common.openems_live_soc(plant)
if live_soc is not None:
    plant.soc_kwh = live_soc

sim_cfg = plant.sim_config()
hp_active = sim_cfg.hp_heat_kw > 0 or sim_cfg.hp_area_m2 > 0
today_mask = plan.index.date == now.date()
today = plan[today_mask]
oe_cfg = common.openems_settings(plant)

# ================================================================ Monitor + Widgets
mon_col, w1, w2 = st.columns([5, 3, 3])

with mon_col:
    data = monitor_data_from_plan(plan, schedule, now, plant, live_soc)
    components.html(energy_monitor_html(data), height=470)

with w1:
    with theme.card("Speicher", "🔋"):
        soc_frac = plant.soc_kwh / plant.battery.usable_kwh
        st.progress(min(soc_frac, 1.0), text=f"SoC {soc_frac * 100:.0f} % · {plant.soc_kwh:.1f} kWh")
        theme.row("Leistung jetzt", f"{data['storage_kw']:+.2f} kW")
        theme.row("Laden heute (Plan)", f"{float(today['charge_kw'].sum()) * DT_H:.1f} kWh")
        theme.row("Verkauf heute (Plan)", f"{float(today['sell_batt_kw'].sum()) * DT_H:.1f} kWh")
        theme.row("Gesundheit (SoH)", f"{plant.soh_percent:.1f} %")
        if live_soc is not None:
            st.caption("⚡ SoC live von OpenEMS (ess0)")

    with theme.card("Netz & Preis", "⚡"):
        theme.row("Spotpreis jetzt (netto)", f"{data.get('price_ct', float(plan.loc[plan.index <= now, 'price_ct'].iloc[-1])):.1f} ct/kWh")
        grid_kw = data["grid_kw"]
        theme.row("Netz jetzt", f"{'Bezug' if grid_kw >= 0 else 'Einspeisung'} {abs(grid_kw):.2f} kW")
        buy_col = "buy_home_kw" if "buy_home_kw" in today else "grid_buy_kw"
        theme.row("Bezug heute", f"{float(today[buy_col].sum()) * DT_H:.1f} kWh")
        theme.row("Verbrauch heute", f"{float(today['load_kw'].sum()) * DT_H:.1f} kWh")

with w2:
    with theme.card("Verbrauch", "🏠"):
        base_kw = float(plan.loc[plan.index <= now, "base_load_kw"].iloc[-1]) if "base_load_kw" in plan else 0.0
        hp_kw_now = float(plan.loc[plan.index <= now, "hp_kw"].iloc[-1]) if "hp_kw" in plan else 0.0
        theme.row("Haushalt", f"{base_kw:.2f} kW")
        if hp_active:
            theme.row("Wärmepumpe (witterungsgeführt)", f"{hp_kw_now:.2f} kW")
        for dev in devices:
            if dev.enabled:
                dev_kw = float(schedule.loc[schedule.index <= now, dev.key].iloc[-1]) if len(schedule) else 0.0
                theme.row(f"{dev.icon} {dev.label}", f"{dev_kw:.2f} kW")
        theme.row("Gesamt", f"{data['consumption_kw']:.2f} kW")

    with theme.card("EMS-Steuerung", "🤖"):
        if oe_cfg.get("enabled") and oe_cfg.get("mode") == "openems_tou":
            client = common.openems_client(plant)
            sm = client.get_channel("ctrlEssTimeOfUseTariff0/StateMachine")
            if sm is not None:
                icon, text = common.TOU_STATES.get(int(sm), ("❔", f"Status {sm}"))
                theme.row("Modus", "OpenEMS Time-of-Use")
                theme.row("Zustand", f"{icon} {text}")
            else:
                theme.row("Modus", "OpenEMS (ToU nicht installiert)")
        elif oe_cfg.get("enabled"):
            theme.row("Modus", "VoltSurfer-Fahrplan-Push")
            theme.row("Push aktiv", "ja" if oe_cfg.get("control") else "nein")
        else:
            theme.row("Modus", "Simulation (keine Hardware)")
        theme.row("Strategie", common.STRATEGY_LABELS[plant.settings["strategy"]])

# ================================================================ Preisphasen + Lastvorschau
p1, p2 = st.columns([1, 1])
with p1:
    with theme.card("Strompreis & Fahrplan (heute + morgen)", "📈"):
        action = np.where(
            plan["charge_kw"] > 0.05, "Laden",
            np.where(plan["sell_batt_kw"] > 0.05, "Verkauf",
                     np.where(plan["discharge_kw"] > 0.05, "Haushalt aus Speicher", "Neutral")),
        )
        colors = {"Laden": theme.COLORS["accent"], "Verkauf": theme.COLORS["danger"],
                  "Haushalt aus Speicher": theme.COLORS["violet"], "Neutral": theme.COLORS["grid"]}
        fig = go.Figure()
        for name, color in colors.items():
            mask = action == name
            fig.add_trace(go.Bar(x=plan.index[mask], y=plan["price_ct"][mask], name=name, marker_color=color))
        fig.add_vline(x=now, line_dash="dash", line_color=theme.COLORS["text"])
        fig.update_layout(height=280, barmode="overlay", bargap=0, yaxis_title="ct/kWh",
                          legend=dict(orientation="h", y=1.15), margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")
        if not prices_live.has_tomorrow(plan["price_ct"]):
            st.caption("⏳ Morgen-Preise erscheinen nach der Day-Ahead-Auktion (~13:15 Uhr).")

with p2:
    with theme.card("Last & Speicherleistung", "📊"):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=plan.index, y=plan["load_kw"], name="Last gesamt",
                                 line=dict(color=theme.COLORS["accent2"])))
        if "hp_kw" in plan and plan["hp_kw"].max() > 0.05:
            fig.add_trace(go.Scatter(x=plan.index, y=plan["hp_kw"], name="Wärmepumpe",
                                     line=dict(color=theme.COLORS["warn"], dash="dot")))
        fig.add_trace(go.Scatter(x=plan.index, y=plan["charge_kw"], name="Laden",
                                 line=dict(color=theme.COLORS["accent"], shape="hv"), fill="tozeroy"))
        fig.add_trace(go.Scatter(x=plan.index, y=-plan["discharge_kw"], name="Entladen",
                                 line=dict(color=theme.COLORS["danger"], shape="hv"), fill="tozeroy"))
        fig.add_vline(x=now, line_dash="dash", line_color=theme.COLORS["text"])
        fig.update_layout(height=280, legend=dict(orientation="h", y=1.15), yaxis_title="kW", margin=dict(t=10))
        st.plotly_chart(fig, width="stretch")

# ================================================================ Geräte + Wetter
d1, d2 = st.columns([1, 1])
with d1:
    with theme.card("Smart Devices", "🔌"):
        for dev in devices:
            enabled = st.toggle(f"{dev.icon} {dev.label}", value=dev.enabled, key=f"dev_{dev.key}")
            if enabled != dev.enabled:
                plant.settings["devices"].setdefault(dev.key, {})["enabled"] = enabled
                plant.save()
                st.rerun()
            if enabled:
                window = next_run_window(schedule, dev.key, now)
                today_kwh = float(schedule.loc[schedule.index.date == now.date(), dev.key].sum()) * DT_H
                if window:
                    theme.row("Nächstes Fenster", f"{window[0]:%H:%M}–{window[1]:%H:%M} Uhr · heute {today_kwh:.1f} kWh")
                else:
                    theme.row("Heute geplant", f"{today_kwh:.1f} kWh")
        if hp_active:
            hp_today = float(today["hp_kw"].sum()) * DT_H if "hp_kw" in today else 0.0
            theme.row("🔥 Wärmepumpe (witterungsgeführt)", f"heute ~{hp_today:.1f} kWh")

with d2:
    with theme.card("Wetter am Standort", "🌤️"):
        try:
            lat, lon = plant.settings.get("location", [51.0, 9.0])
            forecast = get_cached_forecast(float(lat), float(lon))
            cur = forecast["current"]
            theme.row("Jetzt", f"{cur['icon']} {cur['temp_c']:.0f} °C · {cur['text']} · Wind {cur['wind_kmh']:.0f} km/h")
            weekdays_de = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
            for day in forecast["daily"]:
                date = pd.Timestamp(day["date"])
                hp_need = daily_electric_kwh_for_temp(
                    day["tmean"], sim_cfg.hp_area_m2, sim_cfg.hp_renovation, sim_cfg.hp_heat_kw)
                extra = f" · 🔥 WP ~{hp_need:.0f} kWh" if hp_need > 0.1 else (
                    f" · ☀️ {day['sun_h']:.0f} h Sonne" if day["sun_h"] > 0.1 else "")
                theme.row(f"{weekdays_de[date.weekday()]} {date:%d.%m.}",
                          f"{day['icon']} {day['tmax']:.0f}°/{day['tmin']:.0f}°{extra}")
            if hp_active:
                st.caption("Erwarteter WP-Bedarf fließt in die Ladeplanung ein.")
        except Exception:
            st.caption("Wetterdaten momentan nicht verfügbar (Open-Meteo).")

st.caption(
    "Preise live: energy-charts.info / aWATTar · Wetter: Open-Meteo · "
    "Monitor-Design nach OpenEMS-UI-Vorbild (EPL-2.0), Farben VoltSurfer."
)
