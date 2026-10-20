"""Quantum Lab: a local Streamlit dashboard for the existing VQE experiment."""

from __future__ import annotations

import traceback
from typing import Any

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Quantum Lab",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from webapp import logic, visuals
except Exception as exc:  # pragma: no cover - exercised only with missing dependencies
    st.error(
        "The web interface dependencies could not be imported. "
        "Install them with `pip install -e '.[web]'` and restart Streamlit."
    )
    st.exception(exc)
    st.stop()


_CSS = """
<style>
:root {
    --lab-border: #1f2937;
    --lab-panel: #0f172a;
    --lab-muted: #94a3b8;
}
.block-container {
    padding-top: 1.6rem;
    padding-bottom: 3rem;
    max-width: 1500px;
}
[data-testid="stSidebar"] {
    border-right: 1px solid var(--lab-border);
}
.hero {
    border: 1px solid var(--lab-border);
    border-radius: 18px;
    padding: 1.55rem 1.7rem 1.4rem 1.7rem;
    margin-bottom: 1.15rem;
    background:
        radial-gradient(circle at 90% 10%, rgba(56, 189, 248, 0.13), transparent 38%),
        linear-gradient(135deg, #0f172a 0%, #0b1120 70%);
}
.eyebrow {
    color: #38bdf8;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 0.35rem;
}
.hero h1 {
    color: #f8fafc;
    font-size: clamp(2.2rem, 4vw, 3.4rem);
    letter-spacing: -0.035em;
    line-height: 1.05;
    margin: 0 0 0.55rem 0;
}
.hero p {
    color: #cbd5e1;
    font-size: 1.02rem;
    line-height: 1.55;
    max-width: 850px;
    margin: 0;
}
.pill-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-top: 1rem;
}
.pill {
    color: #bae6fd;
    background: rgba(14, 165, 233, 0.10);
    border: 1px solid rgba(56, 189, 248, 0.24);
    border-radius: 999px;
    padding: 0.2rem 0.62rem;
    font-size: 0.76rem;
}
.small-note {
    color: var(--lab-muted);
    font-size: 0.82rem;
    line-height: 1.5;
}
[data-testid="stMetric"] {
    border: 1px solid var(--lab-border);
    border-radius: 12px;
    padding: 0.75rem 0.9rem;
    background: rgba(15, 23, 42, 0.7);
}
[data-testid="stMetricLabel"] {
    color: #94a3b8;
}
[data-testid="stMetricValue"] {
    color: #f8fafc;
}
h2, h3 {
    letter-spacing: -0.015em;
}
</style>
"""


def _format_energy(value: float | None, digits: int = 12) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.{digits}f} Ha"


def _format_error(value: float | None) -> str:
    if value is None:
        return "n/a"
    numeric = float(value)
    if abs(numeric) < 1e-3:
        return f"{numeric:.3e} mHa"
    return f"{numeric:.6f} mHa"


