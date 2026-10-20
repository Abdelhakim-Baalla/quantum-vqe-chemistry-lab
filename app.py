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


def _scientific_signature(values: logic.UIConfigInput) -> tuple[Any, ...]:
    return (
        values.molecule,
        values.distance_angstrom,
        values.basis,
        values.ansatz,
        values.mapping,
        values.two_qubit_reduction,
        values.optimizer,
        values.max_iterations,
        values.initial_point,
        values.seed,
    )


def _render_sidebar() -> tuple[logic.UIConfigInput, bool]:
    with st.sidebar:
        st.markdown("## Experiment configuration")
        st.caption("H₂ / STO-3G · local exact-statevector simulation")

        molecule = st.selectbox(
            "Molecule",
            logic.MOLECULES,
            format_func=lambda value: "H₂" if value == "H2" else value,
            key="cfg_molecule",
            help="H₂ is the implemented and validated molecule for this project.",
        )
        distance = st.number_input(
            "Bond distance (Å)",
            min_value=0.30,
            max_value=5.00,
            value=0.735,
            step=0.005,
            format="%.3f",
            key="cfg_distance",
            help="Internuclear separation used to build the PySCF integrals.",
        )
        basis = st.selectbox(
            "Basis set",
            logic.BASES,
            format_func=lambda value: "STO-3G",
            key="cfg_basis",
            help=(
                "Only STO-3G is exposed because it is the basis covered by the "
                "project's validation suite."
            ),
        )
        ansatz = st.selectbox(
            "Ansatz",
            logic.ANSATZE,
            key="cfg_ansatz",
            help="UCCSD is the only implemented and validated ansatz.",
        )
        st.caption("Only validated basis/ansatz options are selectable.")

        mapping = st.selectbox(
            "Fermion-to-qubit mapping",
            logic.MAPPINGS,
            format_func=lambda value: (
                "Parity + two-qubit Z2 reduction"
                if value == "parity"
                else "Jordan-Wigner (full four qubits)"
            ),
            key="cfg_mapping",
            help=(
                "Parity mapping can taper two qubits using the Hartree-Fock "
                "particle-number and spin-parity sector. Jordan-Wigner does not "
                "use that reduction here."
            ),
        )
        reduction = st.checkbox(
            "Two-qubit Z2 reduction",
            value=True,
            key="cfg_reduction",
            disabled=mapping == "jordan-wigner",
            help="Available only with parity mapping.",
        )
        reduction_effective = bool(reduction) if mapping == "parity" else False
        if mapping == "jordan-wigner":
            st.caption("Jordan-Wigner uses all four qubits; Z2 reduction is disabled.")

        optimizer = st.selectbox(
            "Classical optimizer",
            logic.OPTIMIZERS,
            key="cfg_optimizer",
        )
        max_iterations = st.number_input(
            "Maximum optimization iterations",
            min_value=1,
            max_value=5000,
            value=500,
            step=50,
            key="cfg_max_iterations",
        )

        with st.expander("Initial state and export", expanded=False):
            initial_point = st.selectbox(
                "Initial point",
                logic.INITIAL_POINTS,
                format_func=lambda value: (
                    "Hartree-Fock reference" if value == "hf" else "Random (seeded)"
                ),
                key="cfg_initial_point",
                help="The Hartree-Fock reference is the reproducible default.",
            )
            seed = st.number_input(
                "Random seed",
                min_value=0,
                max_value=2_147_483_647,
                value=7,
                step=1,
                key="cfg_seed",
                help="Used when the initial point is random; recorded in the result.",
            )
            output_dir = st.text_input(
                "Output directory (optional)",
                value="results",
                key="cfg_output_dir",
                help=(
                    "Directory used by the Save button in Experiment History. "
                    "Relative paths are resolved from the directory where "
                    "Streamlit was launched."
                ),
            )

        st.divider()
        run_clicked = st.button(
            "Run VQE Experiment",
            type="primary",
            width="stretch",
            key="run_experiment",
        )
        st.caption(
            "Runs locally on the exact statevector simulator. No cloud account, "
            "API key, or quantum hardware is used."
        )

    return (
        logic.UIConfigInput(
            molecule=molecule,
            distance_angstrom=distance,
            basis=basis,
            ansatz=ansatz,
            mapping=mapping,
            two_qubit_reduction=reduction_effective,
            optimizer=optimizer,
            max_iterations=int(max_iterations),
            initial_point=initial_point,
            seed=int(seed),
            output_dir=output_dir,
        ),
        run_clicked,
    )


