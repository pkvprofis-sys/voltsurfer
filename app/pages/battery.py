"""Batteriespeicher-Zustand: SoH, Zyklen, Zellen, Historie."""
from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from app import common, theme
from voltsurfer.live.state import LFP_CYCLE_LIFE

plant = common.get_plant()
plan, schedule, devices, now = common.make_plan(plant)
batt = plant.battery

live_soc = common.openems_live_soc(plant)
if live_soc is not None:
    plant.soc_kwh = live_soc
    st.success("⚡ OpenEMS live — SoC kommt direkt vom Edge (ess0)")

# ------------------------------------------------------------------ Kopf-KPIs
c1, c2, c3, c4 = st.columns(4)

soc_frac = plant.soc_kwh / batt.usable_kwh
fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=soc_frac * 100,
    number=dict(suffix=" %", font=dict(color=theme.COLORS["text"])),
    title=dict(text="Ladezustand (SoC)", font=dict(size=14)),
    gauge=dict(
        axis=dict(range=[0, 100]),
        bar=dict(color=theme.COLORS["accent"]),
        bgcolor=theme.COLORS["bg"],
        threshold=dict(line=dict(color=theme.COLORS["danger"], width=3),
                       value=plant.settings["buffer_frac"] * 100),
    ),
))
fig.update_layout(height=210, margin=dict(t=40, b=10, l=30, r=30))
c1.plotly_chart(fig, width="stretch")

fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=plant.soh_percent,
    number=dict(suffix=" %", font=dict(color=theme.COLORS["text"])),
    title=dict(text="Gesundheit (SoH)", font=dict(size=14)),
    gauge=dict(
        axis=dict(range=[80, 100]),
        bar=dict(color=theme.COLORS["accent2"]),
        bgcolor=theme.COLORS["bg"],
    ),
))
fig.update_layout(height=210, margin=dict(t=40, b=10, l=30, r=30))
c2.plotly_chart(fig, width="stretch")

with c3:
    st.metric("Vollzyklen", f"{plant.cycles:,.0f}")
    st.progress(min(plant.cycles / LFP_CYCLE_LIFE, 1.0),
                text=f"{plant.cycles / LFP_CYCLE_LIFE:.1%} von {LFP_CYCLE_LIFE:.0f} Zyklen (LFP-Garantie)")
    st.metric("Durchsatz gesamt", f"{plant.throughput_kwh:,.0f} kWh")

with c4:
    power_now = float(plan.loc[plan.index <= now, ["charge_kw", "discharge_kw"]].iloc[-1].max()) if len(plan) else 0.0
    temp = 24.0 + 8.0 * power_now / batt.discharge_power_kw
    st.metric("Temperatur", f"{temp:.1f} °C", help="Simuliert: Grundtemperatur + Lastanteil")
    st.metric("Zellspreizung", f"{plant.cell_spread_mv:.1f} mV",
              help="Spannungsdrift zwischen den Zellblöcken; wächst mit dem Durchsatz")
    if st.button("⚖️ Zell-Balancing starten", width="stretch"):
        with st.spinner("Balanciere Zellen …"):
            plant.balance_cells()
        st.toast("Balancing abgeschlossen — Zellspreizung zurückgesetzt", icon="✅")
        st.rerun()

# ------------------------------------------------------------------ Zellen
st.subheader("Zellblöcke (LFP, simuliert)")
spread = plant.cell_spread_mv
offsets = np.array([-0.5, -0.15, 0.2, 0.45]) * spread
cell_v = 3200 + offsets  # mV, nominal 3,2 V LFP
cols = st.columns(4)
for i, (col, mv) in enumerate(zip(cols, cell_v), start=1):
    with col:
        with st.container(border=True):
            st.markdown(f"**Zelle {i}**")
            st.metric("Spannung", f"{mv / 1000:.3f} V",
                      delta=f"{mv - 3200:+.1f} mV", delta_color="off")
            st.progress(min(max(soc_frac + (mv - 3200) / 8000, 0.0), 1.0))

# ------------------------------------------------------------------ Historie
st.subheader("Lade-/Entladehistorie")
hist = plant.history_frame()
if len(hist):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=hist.index, y=hist["cycles"], name="Vollzyklen/Tag",
                         marker_color=theme.COLORS["accent"]))
    fig.add_trace(go.Scatter(x=hist.index, y=hist["load_kwh"], name="Verbrauch (kWh/Tag)",
                             line=dict(color=theme.COLORS["accent2"]), yaxis="y2"))
    fig.update_layout(
        height=300,
        yaxis=dict(title="Zyklen"),
        yaxis2=dict(title="kWh", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.15),
    )
    st.plotly_chart(fig, width="stretch")
else:
    st.info("Noch keine Historie — sie füllt sich mit jedem simulierten Betriebstag.")
