"""Kunden-Check: Fragebogen → Bedarf → Speicher-Empfehlung → Zeitraffer-Simulation.

Fragt Verbrauch, PV, Wärmepumpe, E-Auto und smarte Verbraucher ab, empfiehlt
den passenden VoltSurfer und spielt dann die letzten 12 Monate mit echten
Börsenpreisen im Zeitraffer ab: „Das hätten Sie gespart."
"""
from __future__ import annotations

import dataclasses
import datetime as dt
import time

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app import common, theme
from voltsurfer.config import BATTERY_PRESETS, SimConfig
from voltsurfer.profiles.ev import ev_dumb_charging_kw, ev_stats
from voltsurfer.profiles.heatpump import avg_electric_kwh_from_power
from voltsurfer.sim import kpi
from voltsurfer.sim.advisor import SMART_DEVICES, daily_demand_kwh, recommend_battery
from voltsurfer.sim.engine import cached_trade_run
from voltsurfer.sim.strategy import DT_H

plant = common.get_plant()
_DEFAULTS = {
    "step": 0,
    "persons": 3, "manual_kwh": False, "annual_kwh": 3500, "price_ct": 35.0,
    "pv": False, "pv_kwp": 8.0,
    "hp": False, "hp_kw": 9.0,
    "ev": False, "ev_km": 15000, "ev_batt": 60.0,
    "runs": {"washer": 3, "dryer": 0, "dishwasher": 5},
    "preset": None,
    "running": False, "done": False,
}
W = st.session_state.setdefault("wizard", dict(_DEFAULTS))
for _k, _v in _DEFAULTS.items():  # ältere Sessions um neue Schlüssel ergänzen
    W.setdefault(_k, _v)

STEPS = ["👥 Haushalt", "☀️ PV", "🔥 Wärmepumpe", "🚗 E-Auto", "🔌 Geräte", "📋 Ergebnis"]


def nav_buttons(back: bool = True, next_label: str = "Weiter →") -> None:
    c1, _, c2 = st.columns([1, 3, 1])
    if back and c1.button("← Zurück", width="stretch"):
        W["step"] -= 1
        st.rerun()
    if c2.button(next_label, type="primary", width="stretch"):
        W["step"] += 1
        st.rerun()


def make_sim_config() -> SimConfig:
    tariff = dataclasses.replace(common.plant_tariff(plant), static_price_ct=float(W["price_ct"]))
    return SimConfig(
        mode="trade",
        battery=BATTERY_PRESETS[W["preset"]],
        tariff=tariff,
        persons=0 if W["manual_kwh"] else int(W["persons"]),
        annual_consumption_kwh=float(W["annual_kwh"]),
        pv_kwp=float(W["pv_kwp"]) if W["pv"] else 0.0,
        hp_heat_kw=float(W["hp_kw"]) if W["hp"] else 0.0,
        location=tuple(plant.settings.get("location", (51.0, 9.0))),
        speicherprivileg=bool(plant.settings.get("speicherprivileg", True)),
        ev_km_per_year=float(W["ev_km"]) if W["ev"] else 0.0,
        ev_battery_kwh=float(W["ev_batt"]),
        smart_runs_per_week=tuple((k, int(v)) for k, v in W["runs"].items() if v > 0),
    )


st.progress((W["step"] + 1) / len(STEPS), text=f"Schritt {W['step'] + 1} von {len(STEPS)}: {STEPS[W['step']]}")

# ================================================================== Schritte
if W["step"] == 0:
    st.markdown("## 👥 Wie hoch ist Ihr Stromverbrauch?")
    W["manual_kwh"] = st.toggle("Ich kenne meinen Jahresverbrauch (steht auf der Stromrechnung)",
                                value=W["manual_kwh"])
    if W["manual_kwh"]:
        W["annual_kwh"] = st.number_input("Jahresverbrauch (kWh) — ohne Wärmepumpe/E-Auto",
                                          800, 15000, int(W["annual_kwh"]), 100)
    else:
        W["persons"] = st.select_slider("Personen im Haushalt", options=[1, 2, 3, 4, 5], value=W["persons"])
        st.caption(f"Wir schätzen: ~{ {1: 1500, 2: 2500, 3: 3500, 4: 4000, 5: 4500}[W['persons']]:,} kWh/Jahr (ohne Wärmepumpe/E-Auto)")
    W["price_ct"] = st.number_input(
        "Was zahlen Sie aktuell pro kWh? (ct, brutto — steht auf der Stromrechnung)",
        20.0, 60.0, float(W["price_ct"]), 0.5,
        help="Gegen diesen Preis rechnen wir Ihre Ersparnis — je ehrlicher, desto glaubwürdiger das Ergebnis.",
    )
    nav_buttons(back=False)

elif W["step"] == 1:
    st.markdown("## ☀️ Haben Sie eine PV-Anlage?")
    W["pv"] = st.toggle("Ja, PV vorhanden", value=W["pv"])
    if W["pv"]:
        W["pv_kwp"] = st.slider("Anlagengröße (kWp)", 2.0, 30.0, W["pv_kwp"], 0.5)
        st.caption("Überschuss wird im VoltSurfer-Modell zum Börsenpreis vermarktet (Direktvermarktung).")
    nav_buttons()

elif W["step"] == 2:
    st.markdown("## 🔥 Heizen Sie mit Wärmepumpe?")
    W["hp"] = st.toggle("Ja, Wärmepumpe (Luft-Wasser)", value=W["hp"])
    if W["hp"]:
        W["hp_kw"] = st.slider("Wie viel kW Heizleistung hat die Wärmepumpe? (steht auf dem Typenschild)",
                               4.0, 20.0, float(W["hp_kw"]), 0.5)
        avg = avg_electric_kwh_from_power(W["hp_kw"])
        st.info(
            f"Eine {W['hp_kw']:.0f}-kW-Luft-Wasser-WP verbraucht im Schnitt "
            f"**~{avg:,.0f} kWh Strom/Jahr** (≈ {W['hp_kw']:.0f} kW × 1.900 Volllaststunden ÷ JAZ 3,8). "
            "Die Simulation verteilt das mit den echten Temperaturen der letzten 12 Monate — "
            "kalte Tage brauchen ein Vielfaches der warmen."
        )
    nav_buttons()

elif W["step"] == 3:
    st.markdown("## 🚗 Fahren Sie ein E-Auto?")
    W["ev"] = st.toggle("Ja, E-Auto mit Wallbox", value=W["ev"])
    if W["ev"]:
        c1, c2 = st.columns(2)
        W["ev_km"] = c1.slider("Fahrleistung (km/Jahr)", 3000, 40000, int(W["ev_km"]), 1000)
        W["ev_batt"] = c2.slider("Akku-Größe (kWh)", 20.0, 110.0, W["ev_batt"], 5.0)
        daily = W["ev_km"] / 365 * 0.18
        range_days = max(int(W["ev_batt"] * 0.6 / daily), 1) if daily > 0 else 99
        st.info(
            f"⚡ Tagesbedarf ~{daily:.1f} kWh — mit {W['ev_batt']:.0f} kWh Akku muss nur etwa "
            f"alle **{min(range_days, 7)} Tage** geladen werden. Die KI legt die Ladung in die "
            "günstigsten Nächte und Wochenend-Stunden (nicht jeden Tag einstecken!)."
        )
    nav_buttons()

elif W["step"] == 4:
    st.markdown("## 🔌 Welche Geräte darf VoltSurfer zeitlich verschieben?")
    for key, spec in SMART_DEVICES.items():
        W["runs"][key] = st.number_input(
            f"{spec['label']} — Läufe pro Woche", 0, 14, int(W["runs"].get(key, 0)),
            key=f"runs_{key}",
        )
    st.caption("Diese Läufe werden automatisch in die günstigsten Stunden gelegt.")
    nav_buttons()

# ================================================================== Ergebnis
elif W["step"] == 5:
    sim_probe = SimConfig(
        persons=0 if W["manual_kwh"] else int(W["persons"]),
        annual_consumption_kwh=float(W["annual_kwh"]),
        hp_heat_kw=float(W["hp_kw"]) if W["hp"] else 0.0,
        ev_km_per_year=float(W["ev_km"]) if W["ev"] else 0.0,
        ev_battery_kwh=float(W["ev_batt"]),
        smart_runs_per_week=tuple((k, int(v)) for k, v in W["runs"].items() if v > 0),
    )
    demand = daily_demand_kwh(sim_probe)
    recommended, reason = recommend_battery(demand, has_ev=W["ev"])
    if W["preset"] is None:
        W["preset"] = recommended

    left, right = st.columns([2, 3])
    with left:
        st.markdown("### Tagesstrombedarf (Ø Jahresmittel)")
        parts = {("Wärmepumpe (Ø Jahr)" if k == "Wärmepumpe" else k): v
                 for k, v in demand.items() if k != "Gesamt" and v > 0.01}
        fig = go.Figure(go.Bar(
            x=list(parts.values()), y=list(parts.keys()), orientation="h",
            marker_color=[theme.COLORS["accent2"], theme.COLORS["warn"], theme.COLORS["accent"], theme.COLORS["violet"]][: len(parts)],
            text=[f"{v:.1f} kWh" for v in parts.values()], textposition="outside",
        ))
        fig.update_layout(height=220, margin=dict(t=10, b=10), xaxis_title="kWh/Tag")
        st.plotly_chart(fig, width="stretch")
        st.metric("Gesamt", f"{demand['Gesamt']:.1f} kWh/Tag (Ø)")
        if W["hp"]:
            st.caption("🔥 Die Wärmepumpe wird **saisonal** gerechnet: Winter ≈ 10–15× Sommer, "
                       "aus echten Tagestemperaturen.")
            with st.expander("📈 Saisonverlauf der Wärmepumpe anzeigen"):
                @st.cache_data(show_spinner=False)
                def hp_monthly(heat_kw: float) -> pd.Series:
                    from voltsurfer.profiles.heatpump import heatpump_load_kw_from_power

                    end_d = dt.date.today() - dt.timedelta(days=2)
                    idx = pd.date_range(end_d - dt.timedelta(days=365), end_d, freq="15min", tz="Europe/Berlin")
                    return (heatpump_load_kw_from_power(idx, heat_kw) * 0.25).resample("MS").sum()

                monthly_hp = hp_monthly(float(W["hp_kw"]))
                fig = go.Figure(go.Bar(x=monthly_hp.index, y=monthly_hp.values,
                                       marker_color=theme.COLORS["warn"]))
                fig.update_layout(height=200, margin=dict(t=10), yaxis_title="kWh/Monat")
                st.plotly_chart(fig, width="stretch")
    with right:
        st.markdown("### 🔋 Unsere Empfehlung")
        st.success(f"**{recommended}**\n\n{reason}")
        W["preset"] = st.radio("Speicher für die Simulation", list(BATTERY_PRESETS),
                               index=list(BATTERY_PRESETS).index(W["preset"]))

    st.divider()
    speed = st.radio("Zeitraffer-Geschwindigkeit", ["x5", "x20", "x50", "Sofort"],
                     index=1, horizontal=True)

    end = dt.date.today() - dt.timedelta(days=2)
    start = end - dt.timedelta(days=365)
    sim = make_sim_config()

    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("← Zurück", width="stretch"):
        W["step"] -= 1
        st.rerun()
    if not W["running"] and c2.button("▶ Simulation starten (letzte 12 Monate)", type="primary", width="stretch"):
        W["running"] = True
        W["done"] = False
        st.rerun()
    if W["running"] and not W["done"] and c3.button("⏭ Überspringen", width="stretch"):
        W["done"] = True
        st.rerun()

    if W["running"]:
        @st.cache_data(show_spinner=False)
        def run_wizard_backtest(key: str, s: dt.date, e: dt.date):
            progress = st.progress(0.0, text="Rechne 12 Monate mit echten Börsenpreisen …")
            result = cached_trade_run(
                make_sim_config(), s, e,
                progress_cb=lambda f: progress.progress(f, text=f"Rechne 12 Monate … {f:.0%}"),
            )
            progress.empty()
            return result

        result = run_wizard_backtest(sim.cache_key(f"{start}{end}wiz"), start, end)
        daily_eur = kpi.trade_daily_eur(result, sim)

        # ------------------------------------------------------ Zeitraffer
        if not W["done"]:
            date_ph = st.empty()
            chart_ph = st.empty()
            delay = {"x5": 0.28, "x20": 0.07, "x50": 0.028, "Sofort": 0.0}[speed]
            if delay == 0:
                W["done"] = True
                st.rerun()
            cum = 0.0
            days_list = list(daily_eur.items())
            for i, (day, eur) in enumerate(days_list):
                cum += float(eur)
                date_ph.markdown(
                    f"""
                    <div style="text-align:center;padding:0.5rem;">
                      <span style="color:{theme.COLORS['muted']};font-size:1.1rem;">{day:%d. %B %Y}</span><br>
                      <span style="font-size:3rem;font-weight:800;color:{theme.COLORS['accent']};">{cum:,.0f} €</span>
                      <span style="color:{theme.COLORS['muted']};"> gespart · Tag {i + 1}/365 · {eur:+.2f} € heute</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if i % 7 == 0:
                    week = result[result.index.date >= day.date()].head(96)
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=week.index, y=week["spot_ct"], name="Spot",
                                         marker_color=theme.COLORS["grid"]))
                    fig.add_trace(go.Scatter(x=week.index, y=week["soc_kwh"], name="Speicher (kWh)",
                                             line=dict(color=theme.COLORS["accent"]), yaxis="y2"))
                    fig.update_layout(
                        height=220, margin=dict(t=10, b=10), showlegend=False, bargap=0,
                        yaxis=dict(title="ct/kWh"),
                        yaxis2=dict(overlaying="y", side="right", showgrid=False),
                    )
                    chart_ph.plotly_chart(fig, width="stretch", key=f"anim_{i}")
                time.sleep(delay)
            W["done"] = True
            st.rerun()

        # ------------------------------------------------------ Endergebnis
        metrics = kpi.trade_kpis(result, sim)
        ev_bonus = 0.0
        if sim.ev_km_per_year > 0:
            dumb = ev_dumb_charging_kw(result["spot_ct"], sim.ev_km_per_year, sim.ev_battery_kwh)
            ev_bonus = float(((dumb - result["ev_kw"]) * result["home_price_ct"]).sum()) * DT_H / 100.0

        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg,{theme.COLORS['bg2']},{theme.COLORS['bg']});
                        border:2px solid {theme.COLORS['accent']};border-radius:16px;padding:1.4rem 1.8rem;margin:0.8rem 0;text-align:center;">
              <span style="color:{theme.COLORS['muted']};font-size:1.1rem;">Ihr Haus hätte in den letzten 12 Monaten gespart
              — gegenüber Ihrem heutigen Tarif ({W['price_ct']:.0f} ct/kWh):</span><br>
              <span style="font-size:3.4rem;font-weight:800;color:{theme.COLORS['accent']};">{metrics['total_benefit_eur']:,.0f} €</span><br>
              <span style="color:{theme.COLORS['muted']};">
                💶 Handel {metrics['trade_profit_eur']:,.0f} € ·
                🏠 Verbrauch {metrics['consumption_saving_eur']:,.0f} € ·
                ☀️ PV-Erlös {metrics['pv_revenue_eur']:,.0f} € ·
                🔌 § 14a {metrics['p14a_eur']:,.0f} €
              </span><br>
              <span style="color:{theme.COLORS['accent2']};font-size:1.0rem;">
                Konservativ gerechnet (vs. dynamischer Tarif ohne Speicher):
                <b>+{metrics['total_benefit_vs_dynamic_eur']:,.0f} €</b>
              </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Empfohlener Speicher", W["preset"].split(" (")[0],
                  delta=f"Amortisation {metrics['amortization_years']:.1f} Jahre", delta_color="off")
        k2.metric("Verkauft", f"{metrics['sold_kwh_pa']:,.0f} kWh",
                  delta=f"Ø {metrics['avg_sell_spot_ct']:.1f} ct", delta_color="off")
        k3.metric("Negativpreis-Laden", f"{metrics['neg_price_charge_kwh_pa']:,.0f} kWh")
        if sim.ev_km_per_year > 0:
            stats = ev_stats(result["ev_kw"], result["spot_ct"])
            k4.metric("E-Auto: KI-Ladebonus", f"+{ev_bonus:,.0f} €",
                      delta=f"nur {stats['charging_days']} Ladetage statt {stats['total_days']}",
                      delta_color="off",
                      help="Ersparnis gegenüber täglichem Einstecken um 18 Uhr.")
        else:
            k4.metric("Zyklen", f"{metrics['cycles_pa']:.0f}/Jahr")

        monthly = daily_eur.resample("MS").sum()
        fig = go.Figure(go.Bar(x=monthly.index, y=monthly.values, marker_color=theme.COLORS["accent"]))
        fig.update_layout(height=240, yaxis_title="€ / Monat", margin=dict(t=20))
        st.plotly_chart(fig, width="stretch")

        with st.expander("🧾 Rechnung nachvollziehen — Beispieltag im Detail"):
            best_day = daily_eur.idxmax()
            pick = st.date_input("Tag", value=best_day.date(),
                                 min_value=result.index[0].date(), max_value=result.index[-1].date(),
                                 key="wiz_statement_day")
            stmt_df = result[result.index.date == pick]
            if len(stmt_df):
                common.render_day_statement(stmt_df, sim)

        if common.is_demo():
            # Öffentliche Web-Demo: kein persistenter Anlagenbetrieb, dafür der
            # Weg zum Beratungsgespräch.
            st.success(
                "**Interessiert?** Wir rechnen Ihnen das mit Ihren echten Verbrauchswerten "
                "vor Ort durch — inklusive Blick auf Zählerschrank und Anschlusssituation."
            )
            if st.button("🔄 Neue Berechnung", width="stretch"):
                del st.session_state["wizard"]
                st.rerun()
        else:
            b1, b2 = st.columns(2)
            if b1.button("💾 Konfiguration in Anlage übernehmen", width="stretch"):
                plant.settings.update(
                    persons=int(W["persons"]),
                    hp_enabled=W["hp"], hp_heat_kw=float(W["hp_kw"]) if W["hp"] else 0.0,
                    battery_preset=W["preset"],
                )
                plant.save()
                st.toast("Übernommen — Live-Betrieb nutzt jetzt diese Konfiguration", icon="✅")
            if b2.button("🔄 Neue Simulation", width="stretch"):
                del st.session_state["wizard"]
                st.rerun()

        st.caption(
            "Echte Day-Ahead-Preise (energy-charts.info / SMARD) und echte Temperaturen (Open-Meteo) "
            "der letzten 12 Monate · 11 kW Laden/Entladen · Speicherprivileg gem. § 21 EnFG/§ 118 EnWG "
            "(BNetzA-Abgrenzung ausstehend) · PV-Überschuss zu Spot · Haushalt als Standardlastprofil."
        )
