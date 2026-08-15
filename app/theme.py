"""VoltSurfer-Branding: Farben, Plotly-Template, Header, Karten-System (OpenEMS-Look)."""
from __future__ import annotations

from contextlib import contextmanager

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

COLORS = {
    "bg": "#0B1D33",
    "bg2": "#122A47",
    "grid": "#1E3A5C",
    "text": "#E6EEF8",
    "muted": "#8FA6C2",
    "accent": "#00E5A0",  # Elektro-Grün
    "accent2": "#38BDF8",  # Himmel-Cyan
    "warn": "#F4A261",
    "danger": "#EF6461",
    "violet": "#A78BFA",
}

SCENARIO_COLORS = {
    "A Statisch ohne Speicher": COLORS["muted"],
    "B Statisch + Speicher": COLORS["violet"],
    "C Dynamisch ohne Speicher": COLORS["accent2"],
    "D VoltSurfer EMS": COLORS["accent"],
}


def register_plotly_template() -> None:
    pio.templates["voltsurfer"] = go.layout.Template(
        layout=dict(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=COLORS["text"], family="Segoe UI, sans-serif"),
            colorway=[
                COLORS["accent"], COLORS["accent2"], COLORS["warn"],
                COLORS["violet"], COLORS["danger"], COLORS["muted"],
            ],
            xaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
            yaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=40, r=20, t=50, b=40),
        )
    )
    pio.templates.default = "voltsurfer"


@contextmanager
def card(title: str, icon: str = ""):
    """OpenEMS-Style-Widget-Karte: umrandeter Container mit Icon-Titelzeile."""
    with st.container(border=True):
        st.markdown(f'<div class="vs-card-title">{icon} {title}</div>', unsafe_allow_html=True)
        yield


def row(label: str, value: str) -> None:
    """„Label … Wert"-Zeile im OpenEMS-Listenstil."""
    st.markdown(f'<div class="vs-row"><span class="l">{label}</span><span class="r">{value}</span></div>',
                unsafe_allow_html=True)


def inject_header() -> None:
    st.markdown(
        f"""
        <style>
            .vs-header {{
                display: flex; align-items: baseline; gap: 0.9rem;
                padding-bottom: 0.3rem; border-bottom: 1px solid {COLORS['grid']};
                margin-bottom: 0.8rem;
            }}
            .vs-logo {{
                font-size: 2.1rem; font-weight: 800; letter-spacing: -0.02em;
                background: linear-gradient(90deg, {COLORS['accent']}, {COLORS['accent2']});
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            }}
            .vs-tagline {{ color: {COLORS['muted']}; font-size: 1.0rem; }}
            div[data-testid="stMetric"] {{
                background: {COLORS['bg2']}; border: 1px solid {COLORS['grid']};
                border-radius: 12px; padding: 0.8rem 1rem;
            }}
            /* Karten im OpenEMS-Widget-Stil */
            div[data-testid="stVerticalBlockBorderWrapper"] {{
                background: {COLORS['bg2']}; border-radius: 14px;
            }}
            .vs-card-title {{
                font-weight: 700; font-size: 1.02rem; color: {COLORS['text']};
                border-bottom: 1px solid {COLORS['grid']};
                padding-bottom: 0.35rem; margin-bottom: 0.45rem;
            }}
            .vs-row {{
                display: flex; justify-content: space-between;
                border-bottom: 1px dotted {COLORS['grid']};
                padding: 0.18rem 0; font-size: 0.95rem;
            }}
            .vs-row .l {{ color: {COLORS['muted']}; }}
            .vs-row .r {{ color: {COLORS['text']}; font-weight: 600; }}
        </style>
        <div class="vs-header">
            <span class="vs-logo">⚡ VoltSurfer</span>
            <span class="vs-tagline">Dein Speicher surft die Strompreiswelle</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
