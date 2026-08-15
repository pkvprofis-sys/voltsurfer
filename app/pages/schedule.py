"""Zeitplan & Strategie: Strategiewahl, manuelle Fenster, Plan-Übersicht."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import common, theme
from voltsurfer.sim.strategy import DT_H

plant = common.get_plant()

st.subheader("Betriebsstrategie")
strategy = st.radio(
    "Wie soll der Speicher gesteuert werden?",
    options=list(common.STRATEGY_LABELS),
    format_func=common.STRATEGY_LABELS.get,
    index=list(common.STRATEGY_LABELS).index(plant.settings["strategy"]),
    horizontal=True,
)
if strategy != plant.settings["strategy"]:
    plant.settings["strategy"] = strategy
    plant.save()
    st.rerun()

# ---------------------------------------------------------------- Strategie-Details
if strategy == "top_n":
    c1, c2 = st.columns(2)
    n_charge = c1.slider("Ladestunden pro Tag (günstigste)", 1, 6, plant.settings["top_n_charge_hours"])
    n_dis = c2.slider("Entladestunden pro Tag (teuerste)", 1, 8, plant.settings["top_n_discharge_hours"])
    if (n_charge, n_dis) != (plant.settings["top_n_charge_hours"], plant.settings["top_n_discharge_hours"]):
        plant.settings.update(top_n_charge_hours=n_charge, top_n_discharge_hours=n_dis)
        plant.save()
        st.rerun()

elif strategy == "manual":
    st.markdown("**Tägliche Lade-/Entladefenster** (werden jeden Tag wiederholt)")
    editor = st.data_editor(
        pd.DataFrame(plant.settings["manual_windows"]),
        column_config={
            "start": st.column_config.TextColumn("Von (HH:MM)"),
            "end": st.column_config.TextColumn("Bis (HH:MM)"),
            "action": st.column_config.SelectboxColumn("Aktion", options=["laden", "entladen", "gesperrt"]),
        },
        num_rows="dynamic",
        width="stretch",
        key="manual_editor",
    )
    windows = [w for w in editor.dropna().to_dict("records") if w.get("start") and w.get("end")]
    if windows != plant.settings["manual_windows"]:
        plant.settings["manual_windows"] = windows
        plant.save()
        st.rerun()

elif strategy == "ai":
    done, total = plant.learning_progress()
    learned = plant.learned_daily_kwh()
    c1, c2 = st.columns([2, 3])
    with c1:
        days = st.slider("Lernphase (Tage)", 7, 14, plant.settings["learning_days"])
        if days != plant.settings["learning_days"]:
            plant.settings["learning_days"] = days
            plant.save()
            st.rerun()
    with c2:
        st.progress(min(done / total, 1.0), text=f"Lernphase: Tag {done} von {total}")
        if learned is not None:
            st.success(
                f"Gelernter Tagesverbrauch: **{learned:.1f} kWh/Tag** — dieser Bedarf bleibt "
                f"reserviert, Überschuss darüber wird im VPP verkauft (Puffer "
                f"{plant.settings['buffer_frac']:.0%} bleibt immer)."
            )
        else:
            st.info("Noch in der Lernphase: Speicher arbeitet konservativ, kein VPP-Verkauf.")

# ---------------------------------------------------------------- Planvorschau
st.divider()
st.subheader("Fahrplan (heute + morgen)")
plan, schedule, devices, now = common.make_plan(plant)
if plan.attrs.get("lp_fallback"):
    st.warning("⚠️ Optimierung vorübergehend im Regelmodus (Top-N).")
buffer_kwh = plant.settings["buffer_frac"] * plant.battery.usable_kwh

fig = go.Figure()
fig.add_trace(go.Scatter(x=plan.index, y=plan["soc_kwh"], name="Speicherfüllstand",
                         line=dict(color=theme.COLORS["violet"]), fill="tozeroy"))
fig.add_hline(y=buffer_kwh, line_dash="dot", line_color=theme.COLORS["danger"],
              annotation_text=f"Puffer {plant.settings['buffer_frac']:.0%}",
              annotation_font_color=theme.COLORS["danger"])
fig.add_trace(go.Scatter(x=plan.index, y=plan["charge_kw"], name="Laden (kW)",
                         line=dict(color=theme.COLORS["accent"], shape="hv"), yaxis="y2"))
fig.add_trace(go.Scatter(x=plan.index, y=-plan["discharge_kw"], name="Entladen (kW)",
                         line=dict(color=theme.COLORS["danger"], shape="hv"), yaxis="y2"))
fig.add_vline(x=now, line_dash="dash", line_color=theme.COLORS["text"], annotation_text="Jetzt")
fig.update_layout(
    height=380,
    yaxis=dict(title="kWh"),
    yaxis2=dict(title="kW", overlaying="y", side="right", showgrid=False),
    legend=dict(orientation="h", y=1.12),
)
st.plotly_chart(fig, width="stretch")

# Tages-Zusammenfassung
today = plan[plan.index.date == now.date()]
k1, k2, k3, k4 = st.columns(4)
k1.metric("Laden heute", f"{float(today['charge_kw'].sum()) * DT_H:.1f} kWh")
k2.metric("Entladen heute", f"{float(today['discharge_kw'].sum()) * DT_H:.1f} kWh")
k3.metric("VPP-Verkauf heute", f"{float(today['sell_batt_kw'].sum()) * DT_H:.1f} kWh")
cost_today = float((today["grid_buy_kw"] * today["dyn_ct"]).sum()) * DT_H / 100.0
feed_in_ct = common.plant_tariff(plant).feed_in_tariff_ct
revenue_today = float((today["sell_batt_kw"] * today["price_ct"]).sum()) * DT_H / 100.0
revenue_today += float(today["sell_pv_kw"].sum()) * DT_H * feed_in_ct / 100.0
k4.metric("Saldo heute (geplant)", f"{cost_today - revenue_today:.2f} €")

# Geräteplan
active_devices = [d for d in devices if d.enabled]
if active_devices:
    st.markdown("**Geräte-Fahrplan**")
    fig = go.Figure()
    for i, dev in enumerate(active_devices):
        on = schedule[dev.key] > 0
        fig.add_trace(go.Bar(
            x=schedule.index[on],
            y=[1] * int(on.sum()),
            base=i,
            name=f"{dev.icon} {dev.label}",
            marker_color=[theme.COLORS["accent"], theme.COLORS["warn"], theme.COLORS["accent2"]][i % 3],
        ))
    fig.add_vline(x=now, line_dash="dash", line_color=theme.COLORS["text"])
    fig.update_layout(
        height=90 + 60 * len(active_devices), barmode="overlay", bargap=0, showlegend=True,
        yaxis=dict(visible=False), legend=dict(orientation="h", y=1.3),
    )
    st.plotly_chart(fig, width="stretch")
