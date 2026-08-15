"""Kreis-Energiemonitor im OpenEMS-Look (SVG, VoltSurfer-Farben).

Nachbau des OpenEMS-UI-Energymonitors (ui/src/app/edge/live/energymonitor):
vier Sektionen als Kreisbögen — Erzeugung oben, Verbrauch rechts, Netz links,
Speicher unten — mit Wert-Bögen, Icons, animierten Energieflüssen zur Mitte
und Autarkie-/Eigenverbrauchsanzeige im Zentrum.
"""
from __future__ import annotations

import math

from app.theme import COLORS

CX, CY, R = 280, 250, 190  # Zentrum und Ringradius im 560x500-Viewbox
ARC_W = 10


def _pt(angle_deg: float, radius: float) -> tuple[float, float]:
    a = math.radians(angle_deg - 90)  # 0° = oben
    return CX + radius * math.cos(a), CY + radius * math.sin(a)


def _arc_path(start_deg: float, end_deg: float, radius: float) -> str:
    x1, y1 = _pt(start_deg, radius)
    x2, y2 = _pt(end_deg, radius)
    large = 1 if abs(end_deg - start_deg) > 180 else 0
    return f"M {x1:.1f} {y1:.1f} A {radius} {radius} 0 {large} 1 {x2:.1f} {y2:.1f}"


def _section(center_deg: float, ratio: float, color: str, icon: str, label: str,
             value_text: str, active: bool) -> str:
    """Ein Sektions-Bogen (±40° um center_deg) mit Wert-Bogen, Icon und Text."""
    span = 40.0
    start, end = center_deg - span, center_deg + span
    ratio = max(0.0, min(ratio, 1.0))
    parts = [
        f'<path d="{_arc_path(start, end, R)}" stroke="{COLORS["grid"]}" '
        f'stroke-width="{ARC_W}" fill="none" stroke-linecap="round"/>'
    ]
    if active and ratio > 0.01:
        v_end = start + 2 * span * ratio
        parts.append(
            f'<path d="{_arc_path(start, v_end, R)}" stroke="{color}" '
            f'stroke-width="{ARC_W}" fill="none" stroke-linecap="round"/>'
        )
    ix, iy = _pt(center_deg, R + 42)
    tcolor = COLORS["text"] if active else COLORS["muted"]
    parts.append(f'<text x="{ix:.0f}" y="{iy - 8:.0f}" class="icon">{icon}</text>')
    parts.append(f'<text x="{ix:.0f}" y="{iy + 16:.0f}" class="name" fill="{tcolor}">{label}</text>')
    parts.append(f'<text x="{ix:.0f}" y="{iy + 34:.0f}" class="val" fill="{color if active else COLORS["muted"]}">{value_text}</text>')
    return "".join(parts)


def _flow(center_deg: float, color: str, outward: bool, active: bool) -> str:
    """Animierter Energiefluss zwischen Sektion und Zentrum."""
    if not active:
        return ""
    x1, y1 = _pt(center_deg, R - ARC_W - 6)
    x2, y2 = _pt(center_deg, 78)
    if outward:
        x1, y1, x2, y2 = x2, y2, x1, y1
    return (
        f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
        f'stroke="{color}" stroke-width="4" class="flow" stroke-linecap="round"/>'
    )


def energy_monitor_html(data: dict) -> str:
    """OpenEMS-Style-Monitor. data-Schlüssel:

    consumption_kw, grid_kw (+Bezug/−Einspeisung), storage_kw (+Entladen/−Laden),
    soc_frac, production_kw, pv_kwp, autarky_frac, self_consumption_frac (oder None),
    scale_kw (Bezugsgröße für Bögen, Default 11)
    """
    scale = max(data.get("scale_kw", 11.0), 0.1)
    cons = data.get("consumption_kw", 0.0)
    grid = data.get("grid_kw", 0.0)
    stor = data.get("storage_kw", 0.0)
    soc = data.get("soc_frac", 0.0)
    prod = data.get("production_kw", 0.0)
    pv_kwp = data.get("pv_kwp", 0.0)

    sections = [
        _section(0, prod / max(pv_kwp, 0.1), "#FFD166", "☀️", "Erzeugung",
                 f"{prod:.1f} kW" if pv_kwp > 0 else "—", pv_kwp > 0),
        _section(90, cons / scale, COLORS["accent2"], "🏠", "Verbrauch", f"{cons:.1f} kW", True),
        _section(270, abs(grid) / scale,
                 COLORS["danger"] if grid < -0.05 else COLORS["muted"], "⚡",
                 "Einspeisung" if grid < -0.05 else "Netz",
                 f"{abs(grid):.1f} kW", abs(grid) > 0.05),
        _section(180, soc, COLORS["accent"], "🔋", "Speicher",
                 f"{soc * 100:.0f} % · {abs(stor):.1f} kW", True),
    ]
    flows = [
        _flow(0, "#FFD166", outward=False, active=prod > 0.05),
        _flow(90, COLORS["accent2"], outward=True, active=cons > 0.05),
        _flow(270, COLORS["muted"] if grid > 0 else COLORS["danger"],
              outward=grid < 0, active=abs(grid) > 0.05),
        _flow(180, COLORS["accent"], outward=stor < 0, active=abs(stor) > 0.05),
    ]

    autarky = data.get("autarky_frac")
    selfc = data.get("self_consumption_frac")
    center = [
        f'<circle cx="{CX}" cy="{CY}" r="64" fill="{COLORS["bg"]}" stroke="{COLORS["grid"]}" stroke-width="2"/>',
    ]
    if autarky is not None:
        center.append(f'<text x="{CX}" y="{CY - 10}" class="big" fill="{COLORS["accent"]}">{autarky * 100:.0f} %</text>')
        center.append(f'<text x="{CX}" y="{CY + 12}" class="name" fill="{COLORS["muted"]}">Autarkie heute</text>')
    if selfc is not None:
        center.append(f'<text x="{CX}" y="{CY + 32}" class="name" fill="{COLORS["muted"]}">EV-Quote {selfc * 100:.0f} %</text>')

    return f"""
<div style="background:{COLORS['bg2']};border:1px solid {COLORS['grid']};border-radius:14px;padding:4px;">
<svg viewBox="0 0 560 500" width="100%" xmlns="http://www.w3.org/2000/svg">
<style>
  .icon {{ font-size: 26px; text-anchor: middle; }}
  .name {{ font: 600 13px 'Segoe UI', sans-serif; text-anchor: middle; }}
  .val  {{ font: 700 14px 'Segoe UI', sans-serif; text-anchor: middle; }}
  .big  {{ font: 800 26px 'Segoe UI', sans-serif; text-anchor: middle; }}
  .flow {{ stroke-dasharray: 8 12; animation: fl 1.1s linear infinite; opacity: 0.9; }}
  @keyframes fl {{ to {{ stroke-dashoffset: -20; }} }}
</style>
{''.join(sections)}
{''.join(flows)}
{''.join(center)}
</svg>
</div>
"""


def monitor_data_from_plan(plan, schedule, now, plant, live_soc_kwh=None) -> dict:
    """Monitor-Daten aus dem aktuellen Planschritt ableiten (heutige Autarkie inklusive)."""
    ts = now if now in plan.index else plan.index[0]
    row = plan.loc[ts]
    cons = float(row["load_kw"])
    charge = float(row["charge_kw"])
    discharge = float(row["discharge_kw"])
    sell = float(row["sell_batt_kw"]) + float(row.get("sell_pv_kw", 0.0))
    grid = float(row["grid_buy_kw"]) - sell  # + Bezug, − Einspeisung
    prod = float(row.get("pv_kw", 0.0))
    soc_kwh = live_soc_kwh if live_soc_kwh is not None else plant.soc_kwh

    today = plan[plan.index.date == now.date()]
    load_today = float(today["load_kw"].sum())
    buy_today = float(today["buy_home_kw"].sum()) if "buy_home_kw" in today else float(today["grid_buy_kw"].sum())
    autarky = 1.0 - buy_today / load_today if load_today > 0 else None

    pv_kwp = float(getattr(plant.sim_config(), "pv_kwp", 0.0))
    selfc = None
    if pv_kwp > 0 and float(today["pv_kw"].sum()) > 0:
        selfc = 1.0 - float(today.get("sell_pv_kw", 0.0 * today["pv_kw"]).sum()) / float(today["pv_kw"].sum())

    return {
        "consumption_kw": cons,
        "grid_kw": grid,
        "storage_kw": discharge - charge,
        "soc_frac": soc_kwh / plant.battery.usable_kwh,
        "production_kw": prod,
        "pv_kwp": pv_kwp,
        "autarky_frac": autarky,
        "self_consumption_frac": selfc,
        "scale_kw": max(plant.battery.charge_power_kw, cons, abs(grid), 0.1),
    }
