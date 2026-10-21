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


def _handle_run(values: logic.UIConfigInput, run_clicked: bool) -> None:
    if not run_clicked:
        return

    st.session_state["last_error"] = None
    st.session_state["last_traceback"] = None
    try:
        config = logic.build_experiment_config(values)
    except ImportError as exc:
        st.session_state["last_error"] = (
            "Scientific dependencies are missing. Install the project with "
            f"`pip install -e '.[web]'` and restart Streamlit. Details: {exc}"
        )
        return
    except Exception as exc:
        st.session_state["last_error"] = f"{type(exc).__name__}: {exc}"
        return

    try:
        with st.spinner(
            "Running the VQE, exact diagonalization, and independent references. "
            "No synthetic progress is reported because SciPy does not expose "
            "per-iteration callbacks to this interface."
        ):
            run = logic.execute_experiment(config)
    except ImportError as exc:
        st.session_state["last_error"] = (
            "Scientific dependencies are missing. Install the project with "
            f"`pip install -e '.[web]'` and restart Streamlit. Details: {exc}"
        )
        return
    except Exception as exc:  # include validation and scientific failures
        st.session_state["last_error"] = f"{type(exc).__name__}: {exc}"
        if not isinstance(exc, (ValueError, RuntimeError)):
            st.session_state["last_traceback"] = traceback.format_exc()
        return

    st.session_state["run"] = run
    st.session_state["last_input"] = values
    st.session_state["history"].append(run)
    st.session_state["last_error"] = None
    st.session_state["last_traceback"] = None


def _render_hero() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">Local scientific workbench</div>
            <h1>Quantum Lab</h1>
            <p>
                Configure, run, and inspect a real variational quantum eigensolver
                experiment for molecular hydrogen. The dashboard calls the same
                validated scientific layer as the command-line interface.
            </p>
            <div class="pill-row">
                <span class="pill">H₂ / STO-3G</span>
                <span class="pill">UCCSD</span>
                <span class="pill">Exact statevector simulation</span>
                <span class="pill">No cloud or hardware</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_error() -> None:
    error = st.session_state.get("last_error")
    if not error:
        return
    st.error(f"Experiment failed: {error}", icon="⚠️")
    trace = st.session_state.get("last_traceback")
    if trace:
        with st.expander("Technical details"):
            st.code(trace, language="text")


def _render_overview(run: logic.UIRun) -> None:
    result = run.result
    molecule = result.molecule
    energies = result.energies_hartree
    errors = result.errors_hartree

    applicable_checks = [value for value in result.checks.values() if value is not None]
    passed_checks = sum(value is True for value in applicable_checks)
    if result.status == "success" and passed_checks == len(applicable_checks):
        st.success(
            f"Run completed successfully. {passed_checks}/{len(applicable_checks)} "
            "scientific checks passed."
        )
    elif result.status == "success":
        st.warning(
            f"Run completed with {passed_checks}/{len(applicable_checks)} "
            "scientific checks passing. Review the checks below."
        )
    else:
        st.error(f"The result is marked {result.status!r}; do not treat it as valid evidence.")

    st.caption(
        f"Recorded {result.created_utc} · UI wall time {run.elapsed_s:.2f} s · "
        f"optimizer wall time {result.optimization.get('wall_time_s', 'n/a')} s"
    )

    st.subheader("Molecular information")
    left, right = st.columns([0.9, 1.1], gap="large")
    with left:
        fig = visuals.molecule_figure(molecule["bond_length_angstrom"])
        st.pyplot(fig, clear_figure=True)
        st.caption(
            "Illustrative H-H geometry only. This is not an orbital, electron-density, "
            "or quantum-state visualization."
        )
    with right:
        info = pd.DataFrame(
            [
                {"Property": "Molecule", "Value": molecule["name"]},
                {"Property": "Bond distance", "Value": f"{molecule['bond_length_angstrom']:.3f} Å"},
                {"Property": "Basis set", "Value": molecule["basis"]},
                {
                    "Property": "Charge / spin",
                    "Value": f"{molecule['charge']} / {molecule['spin']}",
                },
                {"Property": "Electrons", "Value": molecule["num_electrons"]},
                {"Property": "Spatial orbitals", "Value": molecule["num_spatial_orbitals"]},
                {"Property": "Spin orbitals", "Value": molecule["num_spin_orbitals"]},
                {"Property": "Qubits after mapping", "Value": molecule["num_qubits"]},
                {
                    "Property": "Mapping",
                    "Value": (
                        f"{result.hamiltonian['mapping']} "
                        f"(Z2 reduction: {result.hamiltonian['two_qubit_reduction']})"
                    ),
                },
                {"Property": "Hamiltonian Pauli terms", "Value": result.hamiltonian["num_terms"]},
                {
                    "Property": "Nuclear repulsion",
                    "Value": f"{energies['nuclear_repulsion']:.12f} Ha",
                },
            ]
        )
        info["Value"] = info["Value"].astype(str)
        st.dataframe(info, hide_index=True, width="stretch")
        st.caption(f"Geometry: `{molecule['geometry_angstrom']}`")

    st.divider()
    st.subheader("Energy results")
    vqe_total = energies.get("vqe_total")
    exact_total = energies.get("exact_qubit_total")
    absolute_error = errors.get("absolute_vqe_vs_exact_total")
    absolute_error_mha = logic.absolute_error_mha(result)

    first_row = st.columns(4)
    first_row[0].metric("VQE total energy", _format_energy(vqe_total), border=True)
    first_row[1].metric("Exact total energy", _format_energy(exact_total), border=True)
    first_row[2].metric(
        "Absolute error (Ha)",
        "n/a" if absolute_error is None else f"{absolute_error:.3e} Ha",
        border=True,
    )
    first_row[3].metric(
        "Absolute error (mHa)",
        _format_error(absolute_error_mha),
        border=True,
    )

    second_row = st.columns(4)
    second_row[0].metric(
        "VQE electronic", _format_energy(energies.get("vqe_electronic")), border=True
    )
    second_row[1].metric(
        "Exact electronic", _format_energy(energies.get("exact_qubit_electronic")), border=True
    )
    second_row[2].metric(
        "PySCF FCI total", _format_energy(energies.get("pyscf_fci_total")), border=True
    )
    second_row[3].metric(
        "Hartree-Fock total", _format_energy(energies.get("hf_total")), border=True
    )

    third_row = st.columns(4)
    initial_energy = result.optimization.get("initial_energy_hartree")
    third_row[0].metric(
        "Initial electronic energy",
        _format_energy(initial_energy),
        border=True,
    )
    third_row[1].metric(
        "Energy evaluations",
        str(result.optimization.get("energy_evaluations", "n/a")),
        border=True,
    )
    third_row[2].metric(
        "Optimizer converged",
        "Yes" if result.optimization.get("converged") else "No",
        border=True,
    )
    third_row[3].metric("UI wall time", f"{run.elapsed_s:.2f} s", border=True)

    st.caption(
        f"Nuclear repulsion is {energies['nuclear_repulsion']:.12f} Ha. "
        "Electronic energies exclude it; total energies include it. "
        "The exact reference is diagonalization of the same qubit Hamiltonian, "
        "not the VQE result."
    )

    energy_table = pd.DataFrame(
        [
            {
                "Quantity": "Hartree-Fock",
                "Electronic (Ha)": energies.get("hf_electronic"),
                "Total (Ha)": energies.get("hf_total"),
            },
            {
                "Quantity": "VQE",
                "Electronic (Ha)": energies.get("vqe_electronic"),
                "Total (Ha)": energies.get("vqe_total"),
            },
            {
                "Quantity": "Exact qubit diagonalization",
                "Electronic (Ha)": energies.get("exact_qubit_electronic"),
                "Total (Ha)": energies.get("exact_qubit_total"),
            },
            {
                "Quantity": "PySCF FCI (independent)",
                "Electronic (Ha)": energies.get("pyscf_fci_electronic"),
                "Total (Ha)": energies.get("pyscf_fci_total"),
            },
        ]
    )
    st.dataframe(energy_table, hide_index=True, width="stretch")

    st.subheader("Variational principle")
    gap = errors.get("signed_variational_gap_electronic")
    tolerance = result.check_tolerances_hartree.get("variational_tolerance")
    check = result.checks.get("variational_principle")
    if check is True:
        st.success(
            "The VQE energy is consistent with the variational principle for the "
            "same Hamiltonian within the recorded numerical tolerance."
        )
    elif check is False:
        st.error(
            "The VQE energy falls below the exact reference by more than the recorded "
            "numerical tolerance. Treat this run as numerically inconsistent."
        )
    else:
        st.info("The variational-principle check was not applicable for this run.")
    st.markdown(
        "A valid VQE estimate is an expectation value of a normalized trial state. "
        "For the same Hamiltonian it should not be materially below the exact "
        "ground-state energy; a tiny negative gap can arise from floating-point "
        "roundoff. The run records both the signed gap and the tolerance used by "
        "the validation checks."
    )
    if gap is not None and tolerance is not None:
        st.caption(
            f"Signed electronic gap: {gap:.3e} Ha · variational tolerance: {tolerance:.3e} Ha."
        )

    with st.expander("Scientific checks"):
        check_frame = pd.DataFrame(
            [
                {
                    "Check": name,
                    "Result": "not applicable" if value is None else ("pass" if value else "fail"),
                }
                for name, value in result.checks.items()
            ]
        )
        st.dataframe(check_frame, hide_index=True, width="stretch")

    with st.expander("Timing and run metadata"):
        timing = pd.DataFrame(
            [{"Stage": name, "Seconds": value} for name, value in result.timing_seconds.items()]
        )
        st.dataframe(timing, hide_index=True, width="stretch")
        st.json(
            {
                "created_utc": result.created_utc,
                "status": result.status,
                "optimizer": result.optimizer,
                "simulator": result.simulator,
                "software": result.software,
                "warnings": result.warnings,
            },
            expanded=False,
        )


def _render_circuit(run: logic.UIRun) -> None:
    artifacts = run.circuit
    st.subheader("Quantum circuit explorer")
    st.caption(
        "These diagrams were generated during the run from the exact "
        "`ChemistryData.ansatz` object passed into the VQE. They are not a "
        "separate decorative circuit."
    )
    if artifacts is None:
        st.warning(
            "The scientific result is available, but the circuit artifacts could "
            "not be generated for this run."
        )
        if run.circuit_error:
            st.code(run.circuit_error, language="text")
        return

    summary = artifacts.summary
    metrics = st.columns(4)
    metrics[0].metric("Qubits", summary["num_qubits"], border=True)
    metrics[1].metric("Parameters", summary["num_parameters"], border=True)
    metrics[2].metric("Depth (basis gates)", summary["depth_decomposed"], border=True)
    metrics[3].metric("Gates (basis)", summary["size_decomposed"], border=True)

    decomposed_tab, pauli_tab, as_built_tab, parameters_tab = st.tabs(
        ["Basis-gate decomposition", "Pauli evolution", "As built", "Parameters"]
    )
    with decomposed_tab:
        st.image(artifacts.diagram_basis_png, width="stretch")
        st.caption(
            "Two decomposition levels from the executed ansatz. Decomposition "
            "preserves the unitary; it only exposes the underlying gates."
        )
    with pauli_tab:
        st.image(artifacts.diagram_pauli_png, width="stretch")
        st.caption(
            "One decomposition level: the UCCSD evolution block expanded into "
            "Pauli-evolution gates."
        )
    with as_built_tab:
        st.image(artifacts.diagram_as_built_png, width="stretch")
        st.caption(
            "The ansatz exactly as constructed. The single UCCSD evolution block "
            "is compact by design."
        )
    with parameters_tab:
        st.dataframe(
            artifacts.parameter_frame,
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Initial and optimized parameter values come from the recorded "
            "optimizer vectors and are mapped back to the circuit parameters."
        )

    with st.expander("Circuit summary and gate counts"):
        st.dataframe(artifacts.summary_frame, hide_index=True, width="stretch")
        st.dataframe(artifacts.gate_counts_frame, hide_index=True, width="stretch")
        st.code(artifacts.text_diagram, language="text")


def _render_convergence(run: logic.UIRun) -> None:
    result = run.result
    st.subheader("Convergence history")
    st.caption(
        "Every marker is a recorded cost-function evaluation. The best-so-far "
        "trace is a cumulative minimum of those same values. No smoothing, "
        "interpolation, or synthetic points are added."
    )

    try:
        frame = visuals.convergence_frame(result)
        chart = visuals.convergence_chart(result)
    except Exception as exc:
        st.error(f"Could not build the convergence view: {type(exc).__name__}: {exc}")
        return

    st.altair_chart(chart, width="stretch")

    energies = result.energies_hartree
    metrics = st.columns(3)
    metrics[0].metric("Evaluations", len(frame), border=True)
    metrics[1].metric(
        "First recorded energy",
        _format_energy(result.optimization.get("initial_energy_hartree")),
        border=True,
    )
    metrics[2].metric(
        "Best recorded energy",
        _format_energy(float(frame["best_so_far_hartree"].min())),
        border=True,
    )
    metrics = st.columns(3)
    metrics[0].metric(
        "Exact electronic", _format_energy(energies.get("exact_qubit_electronic")), border=True
    )
    metrics[1].metric(
        "Hartree-Fock electronic", _format_energy(energies.get("hf_electronic")), border=True
    )
    metrics[2].metric(
        "Final optimization energy",
        _format_energy(result.optimization.get("final_energy_hartree")),
        border=True,
    )

    display = frame.rename(
        columns={
            "evaluation": "Evaluation",
            "energy_hartree": "Electronic energy (Ha)",
            "best_so_far_hartree": "Best so far (Ha)",
        }
    )
    st.dataframe(display, hide_index=True, width="stretch")


def _render_history(values: logic.UIConfigInput) -> None:
    entries: list[logic.UIRun] = st.session_state["history"]
    st.subheader("Experiment history")
    st.caption(
        "Completed runs from this session. Nothing is written to disk until you "
        "press Save; no database is used."
    )
    if not entries:
        st.info("No completed experiments in this session yet.")
        return

    frame = logic.history_frame(entries)
    display = frame.rename(
        columns={
            "run": "Run",
            "timestamp_utc": "Timestamp (UTC)",
            "distance_A": "d (Å)",
            "basis": "Basis",
            "mapping": "Mapping",
            "optimizer": "Optimizer",
            "vqe_total_Ha": "VQE total (Ha)",
            "exact_total_Ha": "Exact total (Ha)",
            "abs_error_Ha": "|Error| (Ha)",
            "abs_error_mHa": "|Error| (mHa)",
            "converged": "Converged",
            "status": "Status",
            "elapsed_s": "UI time (s)",
        }
    )
    st.dataframe(display, hide_index=True, width="stretch")

    labels = logic.history_labels(entries)
    selected_index = st.selectbox(
        "Select a run to export",
        options=list(range(len(entries))),
        format_func=lambda index: labels[index],
        key="history_selection",
    )
    selected = entries[selected_index]

    save_col, selected_col, all_col = st.columns(3)
    with save_col:
        if st.button("Save selected result as JSON", width="stretch", key="save_selected_result"):
            try:
                path = logic.save_result(selected.result, values.output_dir)
            except Exception as exc:
                st.error(f"Could not save result: {type(exc).__name__}: {exc}")
            else:
                st.success(f"Saved result to `{path}`")
    with selected_col:
        st.download_button(
            "Download selected (JSON)",
            data=selected.result.to_json(),
            file_name=logic.result_filename(selected.result),
            mime="application/json",
            width="stretch",
            key="download_selected_json",
        )
    with all_col:
        st.download_button(
            "Download history (JSON)",
            data=logic.history_json(entries),
            file_name="quantum_lab_history.json",
            mime="application/json",
            width="stretch",
            key="download_history_json",
        )

    st.download_button(
        "Download comparison table (CSV)",
        data=logic.history_csv(entries),
        file_name="quantum_lab_history.csv",
        mime="text/csv",
        key="download_history_csv",
    )
    st.caption(
        "JSON exports preserve the complete ExperimentResult schema: configuration, "
        "molecule, Hamiltonian, ansatz, energies, errors, checks, optimizer history, "
        "timing, software versions, and artifacts."
    )


def _render_learn(run: logic.UIRun | None) -> None:
    st.subheader("Learning mode")
    st.caption(
        "Short explanations tied to what this dashboard actually computes. "
        "The simulation is classical and local."
    )

    if run is not None:
        result = run.result
        st.info(
            f"Concrete values from the current run: {result.hamiltonian['num_qubits']} "
            f"qubits, {result.hamiltonian['num_terms']} Pauli terms, mapping "
            f"`{result.hamiltonian['mapping']}`, and "
            f"{result.ansatz['num_parameters']} variational parameters."
        )

    with st.expander("What is a qubit?", expanded=True):
        st.markdown(
            "A qubit is a two-level quantum system. In this project, qubits are "
            "mathematical objects in an exact classical simulation. After the "
            "fermionic Hamiltonian is mapped, each qubit represents a two-level "
            "degree of freedom; it is not a physical device here."
        )
    with st.expander("What is a molecular Hamiltonian?"):
        st.markdown(
            "The molecular Hamiltonian is a Hermitian operator whose eigenvalues "
            "are possible energies. This project builds the electronic Hamiltonian "
            "from PySCF integrals and handles the nuclear-repulsion constant "
            "separately, so electronic and total energies are never mixed."
        )
    with st.expander("How does fermionic-to-qubit mapping work?"):
        st.markdown(
            "Electronic creation and annihilation operators obey fermionic "
            "anticommutation rules. A mapping rewrites them as Pauli operators on "
            "qubits. This project supports parity and Jordan-Wigner mappings; "
            "parity mapping can additionally taper two qubits by fixing the "
            "Hartree-Fock particle-number and spin-parity sector."
        )
    with st.expander("How does a parameterized circuit produce an energy?"):
        st.markdown(
            "The UCCSD ansatz prepares a Hartree-Fock reference and applies "
            "parameterized excitation operators. For a choice of angles, the "
            "circuit prepares a trial state. The simulator computes the expectation "
            "value of the qubit Hamiltonian in that state, which is the energy "
            "estimate for those angles."
        )
    with st.expander("Why is a classical optimizer needed?"):
        st.markdown(
            "The circuit's energy depends on continuous variational parameters. "
            "A classical SciPy optimizer proposes new parameter values and uses the "
            "recorded energy evaluations to reduce the expectation value. VQE is a "
            "hybrid loop: quantum-state simulation for energies, classical "
            "optimization for the angles."
        )
    with st.expander("How is VQE different from exact diagonalization?"):
        st.markdown(
            "Exact diagonalization computes eigenvalues of the same qubit "
            "Hamiltonian directly. It is an independent reference, not the VQE "
            "result. VQE searches a restricted, parameterized family of states and "
            "may be approximate. The dashboard reports the absolute difference so "
            "agreement can be judged quantitatively, rather than assumed."
        )
    with st.expander("Why does simulation not mean quantum hardware?"):
        st.markdown(
            "The estimator used here is `StatevectorEstimator`, which evolves an "
            "exact statevector on the CPU. There is no quantum processor, no "
            "measurement shot noise, and no hardware error model. These results are "
            "simulation results and do not demonstrate a hardware advantage."
        )
    with st.expander("What does the variational principle imply?"):
        st.markdown(
            "For a normalized trial state and the same Hamiltonian, the energy "
            "expectation value cannot be below the exact ground-state energy, apart "
            "from numerical roundoff. This project records the signed gap and a "
            "tolerance and treats a materially negative gap as a failed consistency "
            "check."
        )


