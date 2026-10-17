"""Visualization helpers for the Quantum Lab dashboard.

This module is Streamlit-independent. Every chart and table is derived from a
completed :class:`quantum_vqe.results.ExperimentResult`; no synthetic points or
placeholder meanings are introduced.
"""

from __future__ import annotations

import io
import math
from typing import TYPE_CHECKING

import altair as alt
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Circle

if TYPE_CHECKING:
    from qiskit import QuantumCircuit

    from quantum_vqe.results import ExperimentResult

_CIRCUIT_STYLE = {
    "name": "iqp-dark",
    "backgroundcolor": "#0b1120",
    "textcolor": "#e5e7eb",
    "gatetextcolor": "#e5e7eb",
    "subtextcolor": "#cbd5e1",
    "linecolor": "#94a3b8",
    "gatefacecolor": "#1e293b",
    "gateedgecolor": "#38bdf8",
    "barrierfacecolor": "#334155",
    "displaycolor": {
        "x": ["#38bdf8", "#0b1120"],
        "h": ["#2dd4bf", "#0b1120"],
        "cx": ["#38bdf8", "#0b1120"],
        "ry": ["#a78bfa", "#0b1120"],
        "rz": ["#a78bfa", "#0b1120"],
        "u": ["#a78bfa", "#0b1120"],
        "sx": ["#38bdf8", "#0b1120"],
        "sxdg": ["#38bdf8", "#0b1120"],
    },
}


