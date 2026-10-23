"""Visualization helpers for the Quantum Lab dashboard.

This module is Streamlit-independent. Every chart and table is derived from a
completed :class:`quantum_vqe.results.ExperimentResult`; no synthetic points or
placeholder meanings are introduced.

The light and dark palettes are deliberately explicit. Charts are rendered
against a transparent background so the surrounding Streamlit surface owns the
contrast, while axes and labels switch with the selected interface theme.
"""

from __future__ import annotations

import io
import math
from typing import TYPE_CHECKING, Any

import altair as alt
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Circle

if TYPE_CHECKING:
    from qiskit import QuantumCircuit

    from quantum_vqe.results import ExperimentResult

_LIGHT = {
    "ink": "#161616",
    "body": "#393939",
    "muted": "#6f6f6f",
    "border": "#d9d9d9",
    "grid": "#e8e8e8",
    "accent": "#0f62fe",
    "accent_soft": "#edf5ff",
    "danger": "#da1e28",
    "amber": "#8e6a00",
    "success": "#198038",
    "gray": "#8d8d8d",
    "surface": "#ffffff",
    "bar": "#0f62fe",
}

_DARK = {
    "ink": "#f4f4f4",
    "body": "#d0d0d0",
    "muted": "#a8b2c1",
    "border": "#3d4a5f",
    "grid": "#253044",
    "accent": "#78a9ff",
    "accent_soft": "#17233a",
    "danger": "#ff8389",
    "amber": "#f1c21b",
    "success": "#42be65",
    "gray": "#8d9aab",
    "surface": "#121821",
    "bar": "#78a9ff",
}


def _palette(theme: str = "light") -> dict[str, str]:
    """Return the validated visual palette for a theme name."""
    key = str(theme or "light").strip().lower()
    if key == "light":
        return _LIGHT
    if key == "dark":
        return _DARK
    raise ValueError(f"Unknown theme {theme!r}; expected 'light' or 'dark'.")


def _chart_theme(theme: str = "light") -> dict[str, str]:
    return _palette(theme)


def _style_chart(chart: alt.Chart, theme: str = "light", *, height: int = 320) -> alt.Chart:
    """Apply the shared editorial chart styling and selected palette."""
    p = _chart_theme(theme)
    return (
        chart.properties(height=height)
        .configure(background="transparent")
        .configure_axis(
            labelColor=p["muted"],
            titleColor=p["ink"],
            gridColor=p["grid"],
            domainColor=p["border"],
            tickColor=p["border"],
            labelFont="Noto Sans",
            titleFont="Noto Sans",
            labelFontSize=11,
            titleFontSize=11,
            titleFontWeight=500,
        )
        .configure_title(
            color=p["ink"],
            fontSize=14,
            font="Noto Sans",
            fontWeight=500,
            anchor="start",
        )
        .configure_legend(
            labelColor=p["body"],
            titleColor=p["ink"],
            labelFont="Noto Sans",
            titleFont="Noto Sans",
            labelFontSize=11,
        )
        .configure_view(strokeWidth=0)
    )


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


def convergence_chart(result: ExperimentResult, *, theme: str = "light") -> alt.Chart:
    """Build an interactive chart of real evaluations and an exact reference.

    The raw trace is shown as recorded. The best-so-far trace is a cumulative
    minimum of those same points. The horizontal rules are the exact qubit
    diagonalization energy and the Hartree-Fock reference from the same run.
    """
    frame = convergence_frame(result)
    p = _chart_theme(theme)
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
                    range=[p["gray"], p["accent"]],
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
                    range=[p["danger"], p["amber"]],
                ),
                legend=alt.Legend(title=None, orient="bottom"),
            ),
            tooltip=[
                alt.Tooltip("reference:N", title="Reference"),
                alt.Tooltip("energy:Q", title="Energy (Ha)", format=".12f"),
            ],
        )
    )

    chart = (
        alt.layer(traces, reference_lines)
        .resolve_scale(color="independent")
        .properties(title="Energy during optimization")
    )
    return _style_chart(chart, theme, height=420)


def molecule_figure(distance_angstrom: float, *, theme: str = "light") -> plt.Figure:
    """Draw a clearly illustrative H-H geometry at the selected distance."""
    distance = float(distance_angstrom)
    if not math.isfinite(distance) or distance <= 0:
        raise ValueError("distance_angstrom must be a positive finite number")

    p = _palette(theme)
    radius = 0.20
    fig, ax = plt.subplots(figsize=(5.4, 2.4), dpi=180)
    fig.patch.set_facecolor(p["surface"])
    ax.set_facecolor(p["surface"])

    left = -distance / 2.0
    right = distance / 2.0
    ax.plot(
        [left, right],
        [0.0, 0.0],
        color=p["gray"],
        linewidth=4,
        solid_capstyle="round",
        zorder=1,
    )
    for x_position in (left, right):
        ax.add_patch(
            Circle(
                (x_position, 0.0),
                radius,
                facecolor=p["accent"],
                edgecolor=p["accent"],
                linewidth=1.0,
                zorder=2,
            )
        )
        ax.text(
            x_position,
            0.0,
            "H",
            ha="center",
            va="center",
            color=p["surface"],
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
        color=p["muted"],
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


def _circuit_style(theme: str = "light") -> dict[str, Any]:
    p = _palette(theme)
    return {
        "backgroundcolor": p["surface"],
        "textcolor": p["ink"],
        "gatetextcolor": p["ink"],
        "subtextcolor": p["muted"],
        "linecolor": p["gray"],
        "gatefacecolor": p["accent"],
        "gateedgecolor": p["accent"],
        "barrierfacecolor": p["border"],
        "displaycolor": {
            "x": [p["accent"], p["surface"]],
            "h": [p["ink"], p["surface"]],
            "cx": [p["accent"], p["surface"]],
            "ry": [p["accent_soft"], p["ink"]],
            "rz": [p["accent_soft"], p["ink"]],
            "u": [p["accent_soft"], p["ink"]],
            "sx": [p["accent"], p["surface"]],
            "sxdg": [p["accent"], p["surface"]],
        },
    }


def circuit_figure(circuit: QuantumCircuit, *, reps: int = 2, theme: str = "light") -> plt.Figure:
    """Render the executed ansatz with Qiskit's Matplotlib drawer.

    ``reps=0`` draws the ansatz exactly as built. ``reps=1`` expands the UCCSD
    evolution block into Pauli-evolution gates. ``reps=2`` expands those into
    basis rotations and entangling gates. Decomposition preserves the unitary.
    """
    p = _palette(theme)
    display_circuit = circuit if reps == 0 else circuit.decompose(reps=reps)
    try:
        fig = display_circuit.draw(
            "mpl",
            style=_circuit_style(theme),
            fold=60,
            scale=0.72,
        )
    except Exception:
        # The text drawer is a robust fallback and still shows the real gates.
        fig, axis = plt.subplots(figsize=(10.0, 2.6), dpi=150)
        fig.patch.set_facecolor(p["surface"])
        axis.set_facecolor(p["surface"])
        axis.text(
            0.0,
            1.0,
            str(display_circuit.draw("text")),
            family="monospace",
            color=p["ink"],
            fontsize=8,
            va="top",
            ha="left",
            transform=axis.transAxes,
        )
        axis.axis("off")
    fig.patch.set_facecolor(p["surface"])
    return fig


def circuit_png(circuit: QuantumCircuit, *, reps: int = 2, theme: str = "light") -> bytes:
    """Render a circuit to PNG bytes during the scientific run thread.

    Streamlit can rerun the script in a different thread. Keeping Qiskit work in
    the run path and displaying pre-rendered bytes on later reruns avoids
    cross-thread use of the Qiskit extension.
    """
    fig = circuit_figure(circuit, reps=reps, theme=theme)
    buffer = io.BytesIO()
    fig.savefig(
        buffer,
        format="png",
        facecolor=fig.get_facecolor(),
        bbox_inches="tight",
        dpi=150,
    )
    plt.close(fig)
    return buffer.getvalue()


def parameter_frame(result: ExperimentResult, circuit: QuantumCircuit) -> pd.DataFrame:
    """Map the optimized parameter vector back to the circuit parameters."""
    names = [parameter.name for parameter in circuit.parameters]
    initial = list(result.optimization.get("initial_parameters") or [])
    final = list(result.optimization.get("final_parameters") or [])
    if not (len(names) == len(initial) == len(final)):
        raise ValueError(
            "Circuit parameters and optimizer parameter vectors have different lengths."
        )
    return pd.DataFrame(
        {
            "Parameter": names,
            "Initial value (rad)": initial,
            "Optimized value (rad)": final,
        }
    )


def gate_counts_frame(circuit: QuantumCircuit) -> pd.DataFrame:
    """Return gate counts for the ansatz and its two decomposition levels."""
    summary = circuit_summary(circuit)
    rows: list[dict[str, object]] = []
    for level, key in (
        ("As built", "ops_as_built"),
        ("Pauli evolution", "ops_pauli"),
        ("Basis gates", "ops_decomposed"),
    ):
        for gate, count in summary[key].items():  # type: ignore[union-attr]
            rows.append({"Decomposition": level, "Gate": gate, "Count": count})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Dashboard analysis
# ---------------------------------------------------------------------------


def dashboard_frame(result: ExperimentResult) -> pd.DataFrame:
    """Return the recorded run as a tidy frame for advanced diagnostics.

    Every derived column is a direct transform of the recorded optimizer
    history: the best-so-far trace is a cumulative minimum, the gap is measured
    against the exact result from the same run, and step improvement is the
    reduction in that best-so-far value. No points are interpolated.
    """
    history = result.optimization.get("history")
    if not history:
        raise ValueError("The result contains no optimizer history to analyze.")

    frame = pd.DataFrame(history).copy()
    required = {"evaluation", "energy_hartree"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Optimizer history is missing required columns: {sorted(missing)}")

    frame["evaluation"] = frame["evaluation"].astype(int)
    frame["energy_hartree"] = frame["energy_hartree"].astype(float)
    frame = frame.sort_values("evaluation").reset_index(drop=True)
    frame["best_so_far_hartree"] = frame["energy_hartree"].cummin()

    exact = float(result.energies_hartree["exact_qubit_electronic"])
    frame["gap_hartree"] = (frame["energy_hartree"] - exact).abs()
    frame["best_gap_hartree"] = (frame["best_so_far_hartree"] - exact).abs()

    previous_best = frame["best_so_far_hartree"].shift(1)
    frame["step_improvement_hartree"] = (previous_best - frame["best_so_far_hartree"]).fillna(0.0)
    frame["step_improvement_mha"] = frame["step_improvement_hartree"] * 1000.0

    parameter_names = [str(name) for name in result.ansatz.get("parameter_names", [])]
    if "parameters" in frame.columns and parameter_names:
        vectors = frame["parameters"].tolist()
        if all(
            isinstance(vector, (list, tuple)) and len(vector) == len(parameter_names)
            for vector in vectors
        ):
            for index, name in enumerate(parameter_names):
                frame[name] = [float(vector[index]) for vector in vectors]
    return frame


def parameter_columns(result: ExperimentResult) -> list[str]:
    """Return only parameter columns that were actually reconstructed."""
    names = [str(name) for name in result.ansatz.get("parameter_names", [])]
    return [name for name in names if name]


def dashboard_error_chart(result: ExperimentResult, *, theme: str = "light") -> alt.Chart:
    """Plot the recorded and best-so-far absolute gap on a log scale."""
    frame = dashboard_frame(result)
    p = _chart_theme(theme)
    plot = frame[frame["gap_hartree"] > 0].copy()
    if plot.empty:
        raise ValueError("The recorded history has no positive energy gap to plot.")

    long_frame = plot.melt(
        id_vars=["evaluation"],
        value_vars=["gap_hartree", "best_gap_hartree"],
        var_name="trace",
        value_name="gap",
    )
    long_frame["trace"] = long_frame["trace"].map(
        {
            "gap_hartree": "Recorded evaluation",
            "best_gap_hartree": "Best so far",
        }
    )
    chart = (
        alt.Chart(long_frame)
        .mark_line(point=alt.OverlayMarkDef(size=28, filled=True), strokeWidth=1.8)
        .encode(
            x=alt.X("evaluation:Q", title="Cost-function evaluation"),
            y=alt.Y(
                "gap:Q",
                title="|VQE − exact| (Ha, log)",
                scale=alt.Scale(type="log", zero=False),
            ),
            color=alt.Color(
                "trace:N",
                scale=alt.Scale(
                    domain=["Recorded evaluation", "Best so far"],
                    range=[p["gray"], p["accent"]],
                ),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                alt.Tooltip("evaluation:Q", title="Evaluation"),
                alt.Tooltip("trace:N", title="Trace"),
                alt.Tooltip("gap:Q", title="Absolute gap (Ha)", format=".4e"),
            ],
        )
        .properties(title="Energy gap to exact diagonalization")
    )
    return _style_chart(chart, theme)


def dashboard_improvement_chart(result: ExperimentResult, *, theme: str = "light") -> alt.Chart:
    """Plot the reduction in best-so-far energy at each recorded evaluation."""
    frame = dashboard_frame(result)
    p = _chart_theme(theme)
    chart = (
        alt.Chart(frame)
        .mark_bar()
        .encode(
            x=alt.X("evaluation:Q", title="Cost-function evaluation"),
            y=alt.Y("step_improvement_mha:Q", title="Best-energy reduction (mHa)"),
            color=alt.value(p["bar"]),
            tooltip=[
                alt.Tooltip("evaluation:Q", title="Evaluation"),
                alt.Tooltip("step_improvement_mha:Q", title="Reduction (mHa)", format=".6f"),
                alt.Tooltip("best_so_far_hartree:Q", title="Best (Ha)", format=".12f"),
            ],
        )
        .properties(title="Where the optimizer made progress")
    )
    return _style_chart(chart, theme)


def dashboard_parameter_chart(result: ExperimentResult, *, theme: str = "light") -> alt.Chart:
    """Plot the recorded variational parameter trajectories."""
    frame = dashboard_frame(result)
    p = _chart_theme(theme)
    names = parameter_columns(result)
    if not names or not set(names).issubset(frame.columns):
        raise ValueError("The result does not contain reconstructable parameter histories.")

    long_frame = frame.melt(
        id_vars=["evaluation"],
        value_vars=names,
        var_name="parameter",
        value_name="angle_rad",
    )
    chart = (
        alt.Chart(long_frame)
        .mark_line(point=alt.OverlayMarkDef(size=22, filled=True), strokeWidth=1.6)
        .encode(
            x=alt.X("evaluation:Q", title="Cost-function evaluation"),
            y=alt.Y("angle_rad:Q", title="Parameter value (rad)", scale=alt.Scale(zero=False)),
            color=alt.Color(
                "parameter:N",
                scale=alt.Scale(range=[p["accent"], p["danger"], p["success"]]),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                alt.Tooltip("evaluation:Q", title="Evaluation"),
                alt.Tooltip("parameter:N", title="Parameter"),
                alt.Tooltip("angle_rad:Q", title="Angle (rad)", format=".8f"),
            ],
        )
        .properties(title="Variational parameter trajectories")
    )
    return _style_chart(chart, theme)


def dashboard_pauli_chart(result: ExperimentResult, *, theme: str = "light") -> alt.Chart:
    """Plot the coefficients of the actual mapped qubit Hamiltonian."""
    p = _chart_theme(theme)
    terms = result.hamiltonian.get("pauli_terms") or []
    if not terms:
        raise ValueError("The result contains no Pauli terms to plot.")
    frame = pd.DataFrame(terms)
    chart = (
        alt.Chart(frame)
        .mark_bar()
        .encode(
            x=alt.X("pauli:N", title="Pauli term", sort=None),
            y=alt.Y("coefficient:Q", title="Coefficient (Ha)"),
            color=alt.condition(
                alt.datum.coefficient >= 0,
                alt.value(p["accent"]),
                alt.value(p["danger"]),
            ),
            tooltip=[
                alt.Tooltip("pauli:N", title="Term"),
                alt.Tooltip("coefficient:Q", title="Coefficient (Ha)", format=".12f"),
            ],
        )
        .properties(title="Hamiltonian decomposition")
    )
    return _style_chart(chart, theme)


def dashboard_energy_ledger_chart(result: ExperimentResult, *, theme: str = "light") -> alt.Chart:
    """Compare the recorded energies as correlation energy relative to HF."""
    p = _chart_theme(theme)
    energies = result.energies_hartree
    hf = float(energies["hf_electronic"])
    rows = [
        {"method": "Hartree–Fock", "energy": hf},
        {"method": "VQE", "energy": float(energies["vqe_electronic"])},
        {"method": "Exact qubit", "energy": float(energies["exact_qubit_electronic"])},
    ]
    if energies.get("pyscf_fci_electronic") is not None:
        rows.append(
            {
                "method": "PySCF FCI",
                "energy": float(energies["pyscf_fci_electronic"]),
            }
        )
    frame = pd.DataFrame(rows)
    frame["relative_mha"] = (frame["energy"] - hf) * 1000.0

    chart = (
        alt.Chart(frame)
        .mark_bar(size=24)
        .encode(
            y=alt.Y("method:N", title=None, sort=None),
            x=alt.X("relative_mha:Q", title="Energy relative to HF (mHa)"),
            color=alt.Color(
                "method:N",
                scale=alt.Scale(
                    domain=frame["method"].tolist(),
                    range=[p["gray"], p["accent"], p["success"], p["amber"]][: len(frame)],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("method:N", title="Method"),
                alt.Tooltip("energy:Q", title="Electronic energy (Ha)", format=".12f"),
                alt.Tooltip("relative_mha:Q", title="Relative to HF (mHa)", format=".6f"),
            ],
        )
        .properties(title="Correlation energy ledger")
    )
    return _style_chart(chart, theme, height=250)


def dashboard_correlation_chart(result: ExperimentResult, *, theme: str = "light") -> alt.Chart:
    """Plot the Pearson correlation matrix of the recorded parameter paths."""
    frame = dashboard_frame(result)
    names = parameter_columns(result)
    if len(names) < 2 or not set(names).issubset(frame.columns):
        raise ValueError("At least two recorded parameters are required for a correlation view.")

    correlation = frame[names].corr().round(6).reset_index(names="row")
    long_frame = correlation.melt(id_vars="row", var_name="column", value_name="correlation")
    chart = (
        alt.Chart(long_frame)
        .mark_rect()
        .encode(
            x=alt.X("column:N", title=None, sort=names),
            y=alt.Y("row:N", title=None, sort=names),
            color=alt.Color(
                "correlation:Q",
                title="r",
                scale=alt.Scale(scheme="blueorange", domain=[-1, 1]),
            ),
            tooltip=[
                alt.Tooltip("row:N", title="Parameter"),
                alt.Tooltip("column:N", title="Against"),
                alt.Tooltip("correlation:Q", title="Pearson r", format=".4f"),
            ],
        )
        .properties(title="Parameter correlation")
    )
    return _style_chart(chart, theme, height=300)
