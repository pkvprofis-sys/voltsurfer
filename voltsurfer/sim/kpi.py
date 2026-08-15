"""Auswertung: Kosten je Szenario, Ersparnis, Zyklen, Amortisation.

Szenarien:
  A  Statischer Tarif, ohne Speicher (Status quo des Kunden)
  B  Statischer Tarif + Speicher klassisch (nur Eigenverbrauch, ohne Preissignal)
  C  Dynamischer Tarif, ohne Speicher
  D  Dynamischer Tarif + Speicher mit VoltSurfer-EMS (LP-optimiert)

Alle Kosten in EUR über den betrachteten Zeitraum; annualisiert über 8760 h.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from voltsurfer.config import SimConfig
from voltsurfer.sim.strategy import DT_H


def _cost_eur(
    buy_kw: np.ndarray,
    price_ct: np.ndarray,
    sell_pv_kw: np.ndarray,
    feed_in_ct,
    sell_batt_kw: np.ndarray | None = None,
    spot_ct: np.ndarray | None = None,
) -> float:
    cost_ct = float((buy_kw * price_ct).sum()) * DT_H
    cost_ct -= float((sell_pv_kw * feed_in_ct).sum()) * DT_H
    if sell_batt_kw is not None and spot_ct is not None:
        cost_ct -= float((sell_batt_kw * spot_ct).sum()) * DT_H
    return cost_ct / 100.0


def scenario_costs(result: pd.DataFrame, greedy: pd.DataFrame, sim: SimConfig) -> dict:
    """Kosten- und Kennzahlen-Übersicht über den simulierten Zeitraum."""
    t = sim.tariff
    load = result["load_kw"].to_numpy()
    pv = result["pv_kw"].to_numpy()
    spot = result["spot_ct"].to_numpy()
    dyn = result["dyn_ct"].to_numpy()

    buy_nobatt = np.maximum(load - pv, 0.0)
    sell_nobatt = np.maximum(pv - load, 0.0)

    hours = len(result) * DT_H
    ann = 8760.0 / hours

    feed_in_vpp = np.maximum(t.feed_in_tariff_ct, spot) if sim.mode == "vpp" else t.feed_in_tariff_ct

    costs = {
        "A_statisch_ohne": _cost_eur(buy_nobatt, t.static_price_ct, sell_nobatt, t.feed_in_tariff_ct),
        "B_statisch_speicher": _cost_eur(
            greedy["grid_buy_kw"].to_numpy(), t.static_price_ct,
            greedy["sell_pv_kw"].to_numpy(), t.feed_in_tariff_ct,
        ),
        "C_dynamisch_ohne": _cost_eur(buy_nobatt, dyn, sell_nobatt, t.feed_in_tariff_ct),
        "D_voltsurfer": _cost_eur(
            result["grid_buy_kw"].to_numpy(), dyn,
            result["sell_pv_kw"].to_numpy(), feed_in_vpp,
            result["sell_batt_kw"].to_numpy(), spot,
        ),
    }
    annual = {k: v * ann for k, v in costs.items()}

    discharged_kwh = float(result["discharge_kw"].sum()) * DT_H
    cycles = discharged_kwh / sim.battery.usable_kwh
    savings_annual = annual["A_statisch_ohne"] - annual["D_voltsurfer"]
    charge_mask = result["charge_kw"] > 0.01
    discharge_mask = result["discharge_kw"] > 0.01

    return {
        "costs_period_eur": costs,
        "costs_annual_eur": annual,
        "savings_annual_eur": savings_annual,
        "savings_vs_dynamic_eur": annual["C_dynamisch_ohne"] - annual["D_voltsurfer"],
        "amortization_years": sim.battery.price_eur / savings_annual if savings_annual > 0 else float("inf"),
        "cycles_per_year": cycles * ann,
        "discharged_kwh_per_year": discharged_kwh * ann,
        "avg_charge_price_ct": float(result.loc[charge_mask, "dyn_ct"].mean()) if charge_mask.any() else np.nan,
        "avg_discharge_price_ct": float(result.loc[discharge_mask, "dyn_ct"].mean()) if discharge_mask.any() else np.nan,
        "negative_price_charge_kwh_per_year": float(
            result.loc[result["spot_ct"] < 0, "charge_kw"].sum()
        ) * DT_H * ann,
        "grid_feed_in_kwh_per_year": float(result["sell_batt_kw"].sum()) * DT_H * ann,
        "hours_simulated": hours,
    }


def trade_kpis(result: pd.DataFrame, sim: SimConfig) -> dict:
    """Ertragszerlegung für den Trade-Modus.

    Baseline: Kunde ohne Speicher mit statischem Tarif (load × static_price).
    Gesamtertrag = Baseline − tatsächliche Kosten (+ § 14a-Pauschale bei Modul 1).
    Zerlegung: Handelsgewinn (Verkauf) + Verbrauchsersparnis + § 14a-Pauschale;
    die Verbrauchsersparnis ist die Restgröße (Summenprobe per Konstruktion).
    """
    t = sim.tariff
    hours = len(result) * DT_H
    ann = 8760.0 / hours
    years = hours / 8760.0

    load = result["load_kw"]
    pv = result["pv_kw"] if "pv_kw" in result else 0.0 * load
    grid_charge = result["grid_charge_kw"] if "grid_charge_kw" in result else result["charge_kw"]
    sell_pv = result["sell_pv_kw"] if "sell_pv_kw" in result else 0.0 * load

    load_kwh = float(load.sum()) * DT_H
    # Baseline: Kunde ohne Speicher, statischer Tarif; vorhandene PV klassisch
    # (Direktverbrauch + Überschuss zu EEG-Fixvergütung)
    buy_nobatt = (load - pv).clip(lower=0.0)
    surplus_nobatt = (pv - load).clip(lower=0.0)
    baseline_eur = (
        float(buy_nobatt.sum()) * t.static_price_ct - float(surplus_nobatt.sum()) * t.feed_in_tariff_ct
    ) * DT_H / 100.0

    # Konservative Vergleichs-Baseline: gleicher Haushalt mit dynamischem Tarif,
    # aber ohne Speicher (PV klassisch: Direktverbrauch + Überschuss zu EEG-Fix)
    dynamic_baseline_eur = (
        float((buy_nobatt * result["home_price_ct"]).sum())
        - float(surplus_nobatt.sum()) * t.feed_in_tariff_ct
    ) * DT_H / 100.0

    pv_revenue_eur = float((sell_pv * result["spot_ct"]).sum()) * DT_H / 100.0
    cost_eur = (
        float((result["buy_home_kw"] * result["home_price_ct"]).sum())
        + float((grid_charge * result["charge_price_ct"]).sum())
        + float((result["batt_home_kw"] * result["batt_home_fee_ct"]).sum())
        - float((result["sell_batt_kw"] * result["spot_ct"]).sum())
    ) * DT_H / 100.0 - pv_revenue_eur

    p14a_eur = t.p14a_flat_eur_per_year * years if t.p14a_module == 1 else 0.0
    total_benefit = baseline_eur - cost_eur + p14a_eur

    # Handelsgewinn: Verkaufserlöse minus anteilige Netz-Ladekosten des verkauften Stroms
    sold_kwh = float(result["sell_batt_kw"].sum()) * DT_H
    discharged_kwh = float(result["discharge_kw"].sum()) * DT_H
    charge_cost_eur = float((grid_charge * result["charge_price_ct"]).sum()) * DT_H / 100.0
    sold_share = sold_kwh / discharged_kwh if discharged_kwh > 0 else 0.0
    trade_profit = (
        float((result["sell_batt_kw"] * result["spot_ct"]).sum()) * DT_H / 100.0
        - sold_share * charge_cost_eur
        - sold_kwh * sim.battery.degradation_cost_ct_kwh / 100.0
    )
    consumption_saving = total_benefit - trade_profit - p14a_eur - pv_revenue_eur

    charge_mask = result["charge_kw"] > 0.01
    sell_mask = result["sell_batt_kw"] > 0.01
    neg_charge_kwh = float(result.loc[result["spot_ct"] < 0, "charge_kw"].sum()) * DT_H

    return {
        "total_benefit_eur": total_benefit,
        "total_benefit_eur_pa": total_benefit * ann,
        "trade_profit_eur": trade_profit,
        "trade_profit_eur_pa": trade_profit * ann,
        "consumption_saving_eur": consumption_saving,
        "consumption_saving_eur_pa": consumption_saving * ann,
        "pv_revenue_eur": pv_revenue_eur,
        "pv_revenue_eur_pa": pv_revenue_eur * ann,
        "p14a_eur": p14a_eur,
        "p14a_eur_pa": p14a_eur * ann,
        "dynamic_baseline_eur_pa": dynamic_baseline_eur * ann,
        "total_benefit_vs_dynamic_eur": dynamic_baseline_eur - cost_eur + p14a_eur,
        "total_benefit_vs_dynamic_eur_pa": (dynamic_baseline_eur - cost_eur + p14a_eur) * ann,
        "baseline_eur_pa": baseline_eur * ann,
        "cost_eur_pa": cost_eur * ann,
        "sold_kwh_pa": sold_kwh * ann,
        "cycles_pa": discharged_kwh / sim.battery.usable_kwh * ann,
        "avg_charge_spot_ct": float(result.loc[charge_mask, "spot_ct"].mean()) if charge_mask.any() else np.nan,
        "avg_sell_spot_ct": float(result.loc[sell_mask, "spot_ct"].mean()) if sell_mask.any() else np.nan,
        "neg_price_charge_kwh_pa": neg_charge_kwh * ann,
        "load_kwh_pa": load_kwh * ann,
        "amortization_years": sim.battery.price_eur / (total_benefit * ann) if total_benefit > 0 else float("inf"),
        "hours": hours,
    }


def trade_daily_eur(result: pd.DataFrame, sim: SimConfig) -> pd.Series:
    """Tagesertrag in € (Baseline statisch/klass. PV − tatsächliche Kosten) für Kalender/Replay."""
    t = sim.tariff
    pv = result["pv_kw"] if "pv_kw" in result else 0.0 * result["load_kw"]
    grid_charge = result["grid_charge_kw"] if "grid_charge_kw" in result else result["charge_kw"]
    sell_pv = result["sell_pv_kw"] if "sell_pv_kw" in result else 0.0 * result["load_kw"]
    step_cost = (
        result["buy_home_kw"] * result["home_price_ct"]
        + grid_charge * result["charge_price_ct"]
        + result["batt_home_kw"] * result["batt_home_fee_ct"]
        - result["sell_batt_kw"] * result["spot_ct"]
        - sell_pv * result["spot_ct"]
    ) * DT_H / 100.0
    baseline = (
        (result["load_kw"] - pv).clip(lower=0.0) * t.static_price_ct
        - (pv - result["load_kw"]).clip(lower=0.0) * t.feed_in_tariff_ct
    ) * DT_H / 100.0
    daily = (baseline - step_cost).resample("D").sum()
    if t.p14a_module == 1:
        daily = daily + t.p14a_flat_eur_per_year / 365.0
    return daily.rename("benefit_eur")


def day_statement(day_df: pd.DataFrame, sim: SimConfig) -> tuple[list[dict], dict]:
    """Nachvollziehbare Tagesabrechnung: jede Position mit Spot (netto) und bezahltem Preis.

    Summenprobe: Die Tagesersparnis der Abrechnung entspricht exakt trade_daily_eur.
    """
    t = sim.tariff
    d = day_df
    pv = d["pv_kw"] if "pv_kw" in d else 0.0 * d["load_kw"]
    grid_charge = d["grid_charge_kw"] if "grid_charge_kw" in d else d["charge_kw"]
    sell_pv = d["sell_pv_kw"] if "sell_pv_kw" in d else 0.0 * d["load_kw"]
    pv_charge = d["pv_charge_kw"] if "pv_charge_kw" in d else 0.0 * d["load_kw"]

    def kwh(series) -> float:
        return float(series.sum()) * DT_H

    def wavg(price, weight) -> float:
        w = float(weight.sum())
        return float((price * weight).sum() / w) if w > 1e-9 else float("nan")

    def eur(power, price_ct) -> float:
        return float((power * price_ct).sum()) * DT_H / 100.0

    rows: list[dict] = []

    def add(posten, status, kwh_v, spot_ct, paid_ct, betrag, hinweis):
        rows.append({
            "Posten": posten, "Status": status, "kWh": round(kwh_v, 1),
            "Spot netto (Ø ct)": None if np.isnan(spot_ct) else round(spot_ct, 1),
            "bezahlt/erlöst (Ø ct)": None if np.isnan(paid_ct) else round(paid_ct, 1),
            "Betrag (€)": round(betrag, 2), "Hinweis": hinweis,
        })

    if kwh(grid_charge) > 0.05:
        add("🔌 Netz → Speicher (laden)",
            "✅/🔓" if sim.speicherprivileg else "✅ heute",
            kwh(grid_charge),
            wavg(d["spot_ct"], grid_charge), wavg(d["charge_price_ct"], grid_charge),
            -eur(grid_charge, d["charge_price_ct"]),
            "bezahlt = (Spot + 1,5 ct Beschaffung) × 1,19 MwSt — für den Eigenverbrauchsanteil "
            "wirtschaftlich identisch mit heutigem dynamischen Tarif (Abgaben s. Haushalts-Zeilen); "
            "für den Verkaufsanteil Teil der Vermarktungsstruktur" if sim.speicherprivileg
            else "bezahlt = voller Endkundenpreis (konservative Rechnung)")
    if kwh(pv_charge) > 0.05:
        add("☀️ PV → Speicher", "✅ heute", kwh(pv_charge), wavg(d["spot_ct"], pv_charge), 0.0, 0.0,
            "eigener Solarstrom, kostenlos")
    if kwh(d["sell_batt_kw"]) > 0.05:
        add("💶 Speicher → Netz (Verkauf)", "🔓 Vermarktung", kwh(d["sell_batt_kw"]),
            wavg(d["spot_ct"], d["sell_batt_kw"]), wavg(d["spot_ct"], d["sell_batt_kw"]),
            eur(d["sell_batt_kw"], d["spot_ct"]),
            "Erlös = Spotpreis netto — Direktvermarktung via White-Label-Partner (ab ~20–30 Kunden aktiv)")
    if kwh(sell_pv) > 0.05:
        add("☀️ PV → Netz (Verkauf)", "🔓 Vermarktung", kwh(sell_pv), wavg(d["spot_ct"], sell_pv),
            wavg(d["spot_ct"], sell_pv), eur(sell_pv, d["spot_ct"]),
            "Erlös = Spotpreis netto (Direktvermarktung; heute alternativ EEG-Fixvergütung)")
    if kwh(d["batt_home_kw"]) > 0.05:
        add("🏠 Speicher → Haushalt", "✅ heute", kwh(d["batt_home_kw"]),
            wavg(d["spot_ct"], d["batt_home_kw"]), wavg(d["batt_home_fee_ct"], d["batt_home_kw"]),
            -eur(d["batt_home_kw"], d["batt_home_fee_ct"]),
            "nachgelagerte Abgaben (Netzentgelt + Umlagen + Steuern, ×1,19) — Ladekosten s. oben")
    if kwh(d["buy_home_kw"]) > 0.05:
        add("🏠 Netz → Haushalt (direkt)", "✅ heute", kwh(d["buy_home_kw"]),
            wavg(d["spot_ct"], d["buy_home_kw"]), wavg(d["home_price_ct"], d["buy_home_kw"]),
            -eur(d["buy_home_kw"], d["home_price_ct"]), "voller Endkundenpreis inkl. aller Abgaben + MwSt")

    p14a = t.p14a_flat_eur_per_year / 365.0 if t.p14a_module == 1 else 0.0
    if p14a > 0:
        add("🔌 § 14a-Rabatt (anteilig)", "✅ heute", 0.0, float("nan"), float("nan"), p14a,
            f"Pauschale {t.p14a_flat_eur_per_year:.0f} €/Jahr ÷ 365 (Antrag beim Netzbetreiber)")

    cost_today = -sum(r["Betrag (€)"] for r in rows)
    baseline_today = (
        eur((d["load_kw"] - pv).clip(lower=0.0), t.static_price_ct)
        - eur((pv - d["load_kw"]).clip(lower=0.0), t.feed_in_tariff_ct)
    )
    totals = {
        "kosten_heute_eur": cost_today,
        "baseline_heute_eur": baseline_today,
        "ersparnis_heute_eur": baseline_today - cost_today,
        "load_kwh": kwh(d["load_kw"]),
    }
    return rows, totals


def monthly_costs(result: pd.DataFrame, greedy: pd.DataFrame, sim: SimConfig) -> pd.DataFrame:
    """Monatliche Kosten je Szenario (EUR) für den Vergleichs-Chart."""
    t = sim.tariff
    buy_nobatt = (result["load_kw"] - result["pv_kw"]).clip(lower=0.0)
    sell_nobatt = (result["pv_kw"] - result["load_kw"]).clip(lower=0.0)
    feed_in_vpp = (
        np.maximum(t.feed_in_tariff_ct, result["spot_ct"]) if sim.mode == "vpp" else t.feed_in_tariff_ct
    )

    frame = pd.DataFrame(
        {
            "A Statisch ohne Speicher": (buy_nobatt * t.static_price_ct - sell_nobatt * t.feed_in_tariff_ct) * DT_H / 100.0,
            "B Statisch + Speicher": (
                greedy["grid_buy_kw"] * t.static_price_ct - greedy["sell_pv_kw"] * t.feed_in_tariff_ct
            ) * DT_H / 100.0,
            "C Dynamisch ohne Speicher": (buy_nobatt * result["dyn_ct"] - sell_nobatt * t.feed_in_tariff_ct) * DT_H / 100.0,
            "D VoltSurfer EMS": (
                result["grid_buy_kw"] * result["dyn_ct"]
                - result["sell_pv_kw"] * feed_in_vpp
                - result["sell_batt_kw"] * result["spot_ct"]
            ) * DT_H / 100.0,
        }
    )
    return frame.resample("MS").sum()
