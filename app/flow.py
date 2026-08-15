"""Animierte 2D-Energiefluss-Grafik (reines SVG/CSS, keine externen Libraries).

Aktive Pfade animieren fließende Strichel in Flussrichtung; jeder Pfad zeigt
seinen Live-kW-Wert. Der Speicherknoten trägt einen SoC-Ring.
"""
from __future__ import annotations

from app.theme import COLORS

# Knotenpositionen im 900x520-Viewbox (Graustrom-Modell: Netz ⇄ Speicher ⇄ Haus)
NODES = {
    "grid": (130, 200, "🏭", "Netz / Börse"),
    "batt": (450, 140, "🔋", "Speicher"),
    "house": (760, 200, "🏠", "Haus"),
    "wallbox": (560, 440, "🚗", "Wallbox"),
    "heatpump": (860, 440, "🔥", "Wärmepumpe"),
}

# (flow-key, von, nach, Farbe)
EDGES = [
    ("grid_to_batt", "grid", "batt", COLORS["accent"]),
    ("batt_to_grid", "batt", "grid", COLORS["danger"]),
    ("grid_to_house", "grid", "house", COLORS["muted"]),
    ("batt_to_house", "batt", "house", COLORS["violet"]),
    ("wallbox", "house", "wallbox", COLORS["accent2"]),
    ("heatpump", "house", "heatpump", COLORS["warn"]),
]


def _edge_path(a: tuple, b: tuple) -> str:
    (x1, y1), (x2, y2) = a[:2], b[:2]
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 40
    return f"M {x1} {y1} Q {mx} {my} {x2} {y2}"


def energy_flow_html(flows: dict[str, float], soc_frac: float, soh: float) -> str:
    paths, labels = [], []
    for key, src, dst, color in EDGES:
        kw = flows.get(key, 0.0)
        active = kw > 0.05
        d = _edge_path(NODES[src], NODES[dst])
        cls = "flow active" if active else "flow"
        width = min(2.5 + kw * 0.8, 9) if active else 1.2
        paths.append(f'<path class="{cls}" d="{d}" stroke="{color if active else COLORS["grid"]}" stroke-width="{width:.1f}"/>')
        if active:
            (x1, y1), (x2, y2) = NODES[src][:2], NODES[dst][:2]
            lx, ly = (x1 + x2) / 2, (y1 + y2) / 2 - 26
            labels.append(
                f'<text x="{lx}" y="{ly}" class="kw" fill="{color}">{kw:.1f} kW</text>'
            )

    nodes_svg = []
    for key, (x, y, icon, name) in NODES.items():
        extra = ""
        if key == "batt":
            circumference = 2 * 3.14159 * 46
            dash = circumference * max(min(soc_frac, 1.0), 0.0)
            extra = (
                f'<circle cx="{x}" cy="{y}" r="46" fill="none" stroke="{COLORS["grid"]}" stroke-width="5"/>'
                f'<circle cx="{x}" cy="{y}" r="46" fill="none" stroke="{COLORS["accent"]}" stroke-width="5" '
                f'stroke-dasharray="{dash:.0f} {circumference:.0f}" stroke-linecap="round" '
                f'transform="rotate(-90 {x} {y})"/>'
                f'<text x="{x}" y="{y + 62}" class="sub">SoC {soc_frac * 100:.0f} % · SoH {soh:.1f} %</text>'
            )
        nodes_svg.append(
            f'<g>{extra}<circle cx="{x}" cy="{y}" r="38" class="node"/>'
            f'<text x="{x}" y="{y + 6}" class="icon">{icon}</text>'
            f'<text x="{x}" y="{y - 48}" class="name">{name}</text></g>'
        )

    return f"""
<div style="background:{COLORS['bg2']};border:1px solid {COLORS['grid']};border-radius:14px;padding:6px;">
<svg viewBox="0 0 900 520" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
<style>
  .node {{ fill: {COLORS['bg']}; stroke: {COLORS['grid']}; stroke-width: 2; }}
  .icon {{ font-size: 30px; text-anchor: middle; }}
  .name {{ font: 600 15px 'Segoe UI', sans-serif; fill: {COLORS['text']}; text-anchor: middle; }}
  .sub  {{ font: 12px 'Segoe UI', sans-serif; fill: {COLORS['muted']}; text-anchor: middle; }}
  .kw   {{ font: 700 14px 'Segoe UI', sans-serif; text-anchor: middle; }}
  .flow {{ fill: none; opacity: 0.35; }}
  .flow.active {{ opacity: 1; stroke-dasharray: 10 14; animation: dash 1.1s linear infinite; }}
  @keyframes dash {{ to {{ stroke-dashoffset: -24; }} }}
</style>
{''.join(paths)}
{''.join(nodes_svg)}
{''.join(labels)}
</svg>
</div>
"""
