"""VoltSurfer — Einstieg der Multi-Page-App.

Start:  streamlit run app/main.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from app import common, theme

st.set_page_config(page_title="VoltSurfer", page_icon="⚡", layout="wide")
theme.register_plotly_template()
theme.inject_header()

plant = common.get_plant()
common.ensure_advanced(plant)

pages = st.navigation(
    [
        st.Page("pages/wizard.py", title="Kunden-Check", icon="🧭", default=True),
        st.Page("pages/playground.py", title="Playground (Experten)", icon="🏠"),
        st.Page("pages/dashboard.py", title="Live-Betrieb", icon="⚡"),
        st.Page("pages/schedule.py", title="Zeitplan & Strategie", icon="📅"),
        st.Page("pages/battery.py", title="Batterie", icon="🔋"),
        st.Page("pages/hardware.py", title="Hardware (OpenEMS)", icon="🔌"),
        st.Page("pages/settings.py", title="Einstellungen", icon="⚙️"),
    ]
)

with st.sidebar:
    st.caption(
        f"**{plant.settings['battery_preset']}**  \n"
        f"Strategie: {common.STRATEGY_LABELS[plant.settings['strategy']]}"
    )

pages.run()
