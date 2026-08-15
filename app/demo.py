"""Öffentliche Web-Demo: nur der Kunden-Check, zum Einbetten auf der Website.

Start lokal:   VOLTSURFER_DEMO=1 streamlit run app/demo.py
(PowerShell:   $env:VOLTSURFER_DEMO=1; streamlit run app/demo.py)

Jede Browser-Sitzung bekommt eine eigene, nicht gespeicherte Anlage — parallele
Besucher beeinflussen sich also nicht und es wird nichts auf die Platte geschrieben.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("VOLTSURFER_DEMO", "1")

import streamlit as st

from app import theme

st.set_page_config(page_title="VoltSurfer — Ersparnis berechnen", page_icon="⚡", layout="wide")
theme.register_plotly_template()
theme.inject_header()

st.navigation([st.Page("pages/wizard.py", title="Kunden-Check", icon="🧭", default=True)]).run()
