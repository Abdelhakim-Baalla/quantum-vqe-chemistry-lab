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


def convergence_frame(result: ExperimentResult) -> pd.DataFrame:
    """Return the recorded optimizer history with a cumulative best-so-far."""
    history = result.optimization.get("history")
    if not history:
        raise ValueError("The result contains no optimizer history to plot.")

    frame = pd.DataFrame(history)
    required = {"evaluation", "energy_hartree"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Optimizer history is missing required columns: {sorted(missing)}")

    frame = frame[["evaluation", "energy_hartree"]].copy()
    frame["evaluation"] = frame["evaluation"].astype(int)
    frame["energy_hartree"] = frame["energy_hartree"].astype(float)
    frame["best_so_far_hartree"] = frame["energy_hartree"].cummin()
    return frame


def convergence_chart(result: ExperimentResult) -> alt.Chart:
    """Build an interactive chart of real evaluations and an exact reference.

    The raw trace is shown as recorded. The best-so-far trace is a cumulative
    minimum of those same points. The horizontal rules are the exact qubit
    diagonalization energy and the Hartree-Fock reference from the same run.
    """
    frame = convergence_frame(result)
    exact_energy = float(result.energies_hartree["exact_qubit_electronic"])
    hf_energy = float(result.energies_hartree["hf_electronic"])

    long_frame = frame.melt(
        id_vars=["evaluation"],
        value_vars=["energy_hartree", "best_so_far_hartree"],
        var_name="trace",
        value_name="energy",
    )
    trace_labels = {
        "energy_hartree": "Recorded evaluation",
        "best_so_far_hartree": "Best so far",
    }
    long_frame["trace"] = long_frame["trace"].map(trace_labels)

    traces = (
        alt.Chart(long_frame)
        .mark_line(point=alt.OverlayMarkDef(size=26, filled=True), strokeWidth=1.7)
        .encode(
            x=alt.X("evaluation:Q", title="Cost-function evaluation"),
            y=alt.Y("energy:Q", title="Electronic energy (Ha)", scale=alt.Scale(zero=False)),
            color=alt.Color(
                "trace:N",
                scale=alt.Scale(
                    domain=["Recorded evaluation", "Best so far"],
                    range=["#64748b", "#38bdf8"],
                ),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                alt.Tooltip("evaluation:Q", title="Evaluation"),
                alt.Tooltip("trace:N", title="Trace"),
                alt.Tooltip("energy:Q", title="Energy (Ha)", format=".12f"),
            ],
        )
    )

    references = pd.DataFrame(
        [
            {"reference": "Exact diagonalization", "energy": exact_energy},
            {"reference": "Hartree-Fock", "energy": hf_energy},
        ]
    )
    reference_lines = (
        alt.Chart(references)
        .mark_rule(strokeDash=[6, 4], strokeWidth=1.6)
        .encode(
            y=alt.Y("energy:Q"),
            color=alt.Color(
                "reference:N",
                scale=alt.Scale(
                    domain=["Exact diagonalization", "Hartree-Fock"],
                    range=["#f87171", "#fbbf24"],
                ),
                legend=alt.Legend(title=None, orient="bottom"),
            ),
            tooltip=[
                alt.Tooltip("reference:N", title="Reference"),
                alt.Tooltip("energy:Q", title="Energy (Ha)", format=".12f"),
            ],
        )
    )

    return (
        alt.layer(traces, reference_lines)
        .resolve_scale(color="independent")
        .properties(height=420, title="Energy during optimization")
        .configure(background="transparent")
        .configure_axis(
            labelColor="#cbd5e1",
            titleColor="#e5e7eb",
            gridColor="#1f2937",
            domainColor="#475569",
            tickColor="#475569",
        )
        .configure_title(color="#e2e8f0", fontSize=16, anchor="start")
        .configure_legend(labelColor="#cbd5e1", titleColor="#e5e7eb")
        .configure_view(strokeWidth=0)
    )


def molecule_figure(distance_angstrom: float) -> plt.Figure:
    """Draw a clearly illustrative H-H geometry at the selected distance."""
    distance = float(distance_angstrom)
    if not math.isfinite(distance) or distance <= 0:
        raise ValueError("distance_angstrom must be a positive finite number")

    radius = 0.20
    fig, ax = plt.subplots(figsize=(5.4, 2.4), dpi=150)
    fig.patch.set_facecolor("#0b1120")
    ax.set_facecolor("#0b1120")

    left = -distance / 2.0
    right = distance / 2.0
    ax.plot(
        [left, right],
        [0.0, 0.0],
        color="#475569",
        linewidth=5,
        solid_capstyle="round",
        zorder=1,
    )
    for x_position in (left, right):
        ax.add_patch(
            Circle(
                (x_position, 0.0),
                radius,
                facecolor="#0ea5e9",
                edgecolor="#7dd3fc",
                linewidth=1.5,
                zorder=2,
            )
        )
        ax.text(
            x_position,
            0.0,
            "H",
            ha="center",
            va="center",
            color="#f8fafc",
            fontsize=16,
            fontweight="bold",
            zorder=3,
        )

    ax.text(
        0.0,
        -0.58,
        f"{distance:.3f} Å",
        ha="center",
        va="center",
        color="#cbd5e1",
        fontsize=11,
    )
    x_span = max(distance / 2.0 + 0.75, 1.15)
    ax.set_xlim(-x_span, x_span)
    ax.set_ylim(-0.85, 0.65)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout(pad=0.4)
    return fig


def circuit_summary(circuit: QuantumCircuit) -> dict[str, object]:
    """Summarize the actual ansatz and its decompositions."""
    pauli_circuit = circuit.decompose(reps=1)
    gate_circuit = circuit.decompose(reps=2)
    return {
        "num_qubits": circuit.num_qubits,
        "num_parameters": circuit.num_parameters,
        "depth_as_built": circuit.depth(),
        "size_as_built": circuit.size(),
        "depth_pauli": pauli_circuit.depth(),
        "size_pauli": pauli_circuit.size(),
        "depth_decomposed": gate_circuit.depth(),
        "size_decomposed": gate_circuit.size(),
        "ops_as_built": dict(circuit.count_ops()),
        "ops_pauli": dict(pauli_circuit.count_ops()),
        "ops_decomposed": dict(gate_circuit.count_ops()),
    }


