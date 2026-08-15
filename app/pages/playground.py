"""Playground/Start: Was hätte VoltSurfer die letzten Jahre verdient?

Backtest mit echten Day-Ahead-Preisen (2023 bis heute) und echtem Wetter —
dieselbe Engine, die auch den Live-Betrieb steuert.
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from app import common, theme
from voltsurfer.config import BATTERY_PRESETS
from voltsurfer.profiles.heatpump import SPECIFIC_HEAT_KWH_M2
from voltsurfer.sim import kpi
from voltsurfer.sim.engine import cached_trade_run
from voltsurfer.sim.strategy import DT_H

DATA_START = dt.date(2023, 1, 1)

plant = common.get_plant()
s = plant.settings

# ---------------------------------------------------------------- Eingaben
st.markdown("### Deine Anlage — drei Angaben genügen")
c1, c2, c3 = st.columns(3)
with c1:
    persons = st.select_slider("👥 Personen im Haushalt", options=[1, 2, 3, 4, 5], value=int(s.get("persons", 3)))
with c2:
    hp_on = st.toggle("🔥 Wärmepumpe (Luft-Wasser)", value=bool(s.get("hp_enabled", True)))
    if hp_on:
        hc1, hc2 = st.columns(2)
        hp_area = hc1.number_input("Wohnfläche (m²)", 60.0, 400.0, float(s.get("hp_area_m2", 140.0)), 10.0)
        hp_renov = hc2.selectbox(
            "Haus-Zustand", list(SPECIFIC_HEAT_KWH_M2),
            index=list(SPECIFIC_HEAT_KWH_M2).index(s.get("hp_renovation", "Saniert")),
        )
    else:
        hp_area, hp_renov = 0.0, "Saniert"
with c3:
    preset_name = st.radio("🔋 Dein VoltSurfer", list(BATTERY_PRESETS),
                           index=list(BATTERY_PRESETS).index(s["battery_preset"]) if s["battery_preset"] in BATTERY_PRESETS else 0)

privileg = st.toggle(
    "Speicherprivileg ansetzen (Abgabenfreiheit der Rückspeisung)", value=bool(s.get("speicherprivileg", True)),
    help=(
        "Nach § 21 EnFG / § 118 EnWG zahlt rückgespeister Speicherstrom keine Umlagen/"
        "Steuern doppelt — nur selbst verbrauchter Strom trägt volle Abgaben. "
        "Ausgeschaltet: konservative Rechnung mit vollen Abgaben auf allen Ladestrom."
    ),
)

# Einstellungen persistieren, Anlage aktualisieren
new_vals = dict(persons=persons, hp_enabled=hp_on, hp_area_m2=hp_area, hp_renovation=hp_renov,
                battery_preset=preset_name, speicherprivileg=privileg)
if any(s.get(k) != v for k, v in new_vals.items()):
    s.update(new_vals)
    plant.save()

sim = plant.sim_config()

# ---------------------------------------------------------------- Backtest
today = dt.date.today() - dt.timedelta(days=2)


@st.cache_data(show_spinner=False)
def run_backtest(key: str, start: dt.date, end: dt.date):
    progress = st.progress(0.0, text="Rechne Backtest mit echten Börsenpreisen …")
    result = cached_trade_run(
        plant.sim_config(), start, end,
        progress_cb=lambda f: progress.progress(f, text=f"Rechne Backtest … {f:.0%}"),
    )
    progress.empty()
    return result


with st.spinner("Lade Preise, Wetter & optimiere …"):
    result = run_backtest(sim.cache_key(f"{DATA_START}{today}pg"), DATA_START, today)

years = sorted(result.index.year.unique())
period = st.radio("Zeitraum", [str(y) for y in years] + ["Gesamt"], horizontal=True,
                  index=len(years), label_visibility="collapsed")
view = result if period == "Gesamt" else result[result.index.year == int(period)]
metrics = kpi.trade_kpis(view, sim)

# ---------------------------------------------------------------- Großes Ergebnis
st.markdown(
    f"""
    <div style="background:linear-gradient(135deg,{theme.COLORS['bg2']},{theme.COLORS['bg']});
                border:1px solid {theme.COLORS['accent']};border-radius:16px;padding:1.2rem 1.6rem;margin:0.5rem 0;">
      <span style="color:{theme.COLORS['muted']};font-size:1rem;">Dein Ertrag mit VoltSurfer ({period})</span><br>
      <span style="font-size:2.6rem;font-weight:800;color:{theme.COLORS['accent']};">
        {metrics['total_benefit_eur_pa']:,.0f} € / Jahr
      </span>
      <span style="color:{theme.COLORS['muted']};font-size:1rem;margin-left:1rem;">
        = 💶 Handel {metrics['trade_profit_eur_pa']:,.0f} €
        + 🏠 Verbrauchsersparnis {metrics['consumption_saving_eur_pa']:,.0f} €
        + 🔌 § 14a {metrics['p14a_eur_pa']:,.0f} €
      </span><br>
      <span style="color:{theme.COLORS['accent2']};font-size:0.95rem;">
        Konservativ (vs. dynamischer Tarif ohne Speicher): +{metrics['total_benefit_vs_dynamic_eur_pa']:,.0f} €/Jahr
      </span>
    </div>
    """,
    unsafe_allow_html=True,
)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Amortisation", f"{metrics['amortization_years']:.1f} Jahre",
          help=f"Speicherpreis {sim.battery.price_eur:,.0f} €")
k2.metric("Verkauft", f"{metrics['sold_kwh_pa']:,.0f} kWh/a", delta=f"{metrics['cycles_pa']:.0f} Zyklen/a", delta_color="off")
k3.metric("Ø Einkauf (Spot)", f"{metrics['avg_charge_spot_ct']:.1f} ct/kWh")
k4.metric("Ø Verkauf (Spot)", f"{metrics['avg_sell_spot_ct']:.1f} ct/kWh")
k5.metric("Negativpreis-Laden", f"{metrics['neg_price_charge_kwh_pa']:,.0f} kWh/a",
          help="Für diese kWh gab es beim Laden Geld zurück.")

# ---------------------------------------------------------------- Jahresvergleich + Monatsverlauf
daily_eur = kpi.trade_daily_eur(result, sim)
left, right = st.columns([2, 3])
with left:
    st.markdown("**Ertrag je Jahr (annualisiert)**")
    year_rows = []
    for y in years:
        yv = result[result.index.year == y]
        year_rows.append((str(y), kpi.trade_kpis(yv, sim)["total_benefit_eur_pa"]))
    fig = go.Figure(go.Bar(
        x=[r[1] for r in year_rows], y=[r[0] for r in year_rows], orientation="h",
        marker_color=theme.COLORS["accent"], text=[f"{r[1]:,.0f} €" for r in year_rows], textposition="outside",
    ))
    fig.update_layout(height=260, xaxis_title="€ / Jahr", yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, width="stretch")
with right:
    st.markdown("**Monatsertrag (€)**")
    monthly = daily_eur.resample("MS").sum()
    fig = go.Figure(go.Bar(x=monthly.index, y=monthly.values, marker_color=theme.COLORS["accent2"]))
    fig.update_layout(height=260, yaxis_title="€ / Monat")
    st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------- Tages-Replay
st.divider()
st.markdown("### 🎬 Tages-Replay — so hätte VoltSurfer gehandelt")
default_day = result.loc[result["spot_ct"] < 0].index[-1].date() if (result["spot_ct"] < 0).any() else result.index[-1].date()
day = st.date_input("Tag wählen", value=default_day, min_value=result.index[0].date(), max_value=result.index[-1].date())
day_df = result[result.index.date == day]

if len(day_df):
    day_eur = float(daily_eur.loc[str(day)]) if str(day) in daily_eur.index.strftime("%Y-%m-%d") else float(daily_eur[daily_eur.index.date == day].iloc[0])
    action = np.where(day_df["charge_kw"] > 0.05, "Laden",
                      np.where(day_df["sell_batt_kw"] > 0.05, "Verkauf",
                               np.where(day_df["batt_home_kw"] > 0.05, "Haushalt aus Speicher", "Neutral")))
    colors = {"Laden": theme.COLORS["accent"], "Verkauf": theme.COLORS["danger"],
              "Haushalt aus Speicher": theme.COLORS["violet"], "Neutral": theme.COLORS["grid"]}

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.6, 0.4],
                        subplot_titles=[f"Spotpreis & Aktionen — Tagesertrag {day_eur:+.2f} €", "Speicherfüllstand (kWh)"])
    for name, color in colors.items():
        mask = action == name
        fig.add_trace(go.Bar(x=day_df.index[mask], y=day_df["spot_ct"][mask], name=name, marker_color=color), row=1, col=1)
    fig.add_trace(go.Scatter(x=day_df.index, y=day_df["soc_kwh"], name="SoC",
                             line=dict(color=theme.COLORS["violet"]), fill="tozeroy"), row=2, col=1)
    fig.update_layout(height=480, barmode="overlay", bargap=0, legend=dict(orientation="h", y=1.12))
    fig.update_yaxes(title_text="ct/kWh", row=1, col=1)
    st.plotly_chart(fig, width="stretch")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Geladen", f"{float(day_df['charge_kw'].sum()) * DT_H:.1f} kWh",
              delta=f"Ø {float(day_df.loc[day_df['charge_kw'] > 0.05, 'spot_ct'].mean()):.1f} ct" if (day_df["charge_kw"] > 0.05).any() else None,
              delta_color="off")
    r2.metric("Verkauft", f"{float(day_df['sell_batt_kw'].sum()) * DT_H:.1f} kWh",
              delta=f"Ø {float(day_df.loc[day_df['sell_batt_kw'] > 0.05, 'spot_ct'].mean()):.1f} ct" if (day_df["sell_batt_kw"] > 0.05).any() else None,
              delta_color="off")
    r3.metric("Haushalt + WP", f"{float(day_df['load_kw'].sum()) * DT_H:.1f} kWh")
    r4.metric("Tagesertrag", f"{day_eur:+.2f} €")

    with st.expander("🧾 Rechnung im Detail — so kommt der Tagesertrag zustande"):
        common.render_day_statement(day_df, sim)

st.caption(
    "Echte Day-Ahead-Preise DE-LU (energy-charts.info, SMARD/Bundesnetzagentur) und echte "
    "Temperaturen (Open-Meteo) · 11 kW Laden/Entladen · Verkaufserlös = Spotpreis (Direktvermarktung) · "
    "Speicherprivileg gem. § 21 EnFG/§ 118 EnWG, finale BNetzA-Abgrenzung ausstehend — "
    "der Schalter oben zeigt die konservative Bandbreite. Dieselbe Engine steuert den Live-Betrieb."
)
