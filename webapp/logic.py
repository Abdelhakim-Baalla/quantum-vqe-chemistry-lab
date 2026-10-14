"""Streamlit-independent logic for the Quantum Lab web interface.

The scientific implementation lives in :mod:`quantum_vqe`. This module only
validates UI inputs, orchestrates one run, and formats real result records for
display and export. It deliberately does not import Streamlit.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

if TYPE_CHECKING:
    from quantum_vqe import ExperimentConfig
    from quantum_vqe.chemistry import ChemistryData
    from quantum_vqe.results import ExperimentResult

MOLECULES = ("H2",)
BASES = ("sto3g",)
ANSATZE = ("UCCSD",)
MAPPINGS = ("parity", "jordan-wigner")
OPTIMIZERS = ("L-BFGS-B", "BFGS", "SLSQP", "COBYLA", "Nelder-Mead")
INITIAL_POINTS = ("hf", "random")


class UIValidationError(ValueError):
    """Raised when a web form value cannot form a valid experiment."""


@dataclass(frozen=True)
class UIConfigInput:
    """Raw values collected from the web form."""

    molecule: str
    distance_angstrom: float
    basis: str
    ansatz: str
    mapping: str
    two_qubit_reduction: bool
    optimizer: str
    max_iterations: int
    initial_point: str
    seed: int
    output_dir: str


@dataclass(frozen=True)
class CircuitArtifacts:
    """Pre-rendered, Qiskit-free data for the circuit explorer.

    Qiskit work is performed in the run thread. The Streamlit script may rerun
    in a different thread, so the UI only consumes these immutable artifacts.
    """

    summary: dict[str, object]
    summary_frame: pd.DataFrame
    parameter_frame: pd.DataFrame
    gate_counts_frame: pd.DataFrame
    diagram_basis_png: bytes
    diagram_pauli_png: bytes
    diagram_as_built_png: bytes
    text_diagram: str


@dataclass
class UIRun:
    """One real experiment, including the exact objects used by the VQE."""

    result: ExperimentResult
    chemistry: ChemistryData
    elapsed_s: float
    circuit: CircuitArtifacts | None = None
    circuit_error: str | None = None


def resolve_output_dir(value: str | Path) -> Path:
    """Validate an output directory without creating it."""
    text = str(value).strip()
    if not text:
        raise UIValidationError("Output directory cannot be empty.")
    path = Path(text).expanduser()
    if path.exists() and not path.is_dir():
        raise UIValidationError(f"Output path exists but is not a directory: {path}")
    return path


def build_experiment_config(values: UIConfigInput) -> ExperimentConfig:
    """Validate web form values and construct the scientific configuration."""
    if values.molecule not in MOLECULES:
        raise UIValidationError(
            f"Only {', '.join(MOLECULES)} is implemented; got molecule={values.molecule!r}."
        )
    if values.basis not in BASES:
        raise UIValidationError(
            f"Basis {values.basis!r} is not exposed by this UI. "
            f"Validated options: {', '.join(BASES)}."
        )
    if values.ansatz not in ANSATZE:
        raise UIValidationError(
            f"Ansatz {values.ansatz!r} is not implemented. Validated options: {', '.join(ANSATZE)}."
        )
    if values.mapping not in MAPPINGS:
        raise UIValidationError(f"Unknown mapping: {values.mapping!r}.")
    if values.optimizer not in OPTIMIZERS:
        raise UIValidationError(f"Unknown optimizer: {values.optimizer!r}.")
    if values.initial_point not in INITIAL_POINTS:
        raise UIValidationError(f"Unknown initial point: {values.initial_point!r}.")
    if values.mapping == "jordan-wigner" and values.two_qubit_reduction:
        raise UIValidationError(
            "Jordan-Wigner mapping does not support the two-qubit Z2 reduction. "
            "Disable the reduction or select parity mapping."
        )

    resolve_output_dir(values.output_dir)

    # Import lazily so the initial Streamlit render does not load Qiskit/PySCF.
    # This also keeps imports inside the Streamlit script-run thread that will
    # execute the scientific pipeline.
    from quantum_vqe import ExperimentConfig

    try:
        return ExperimentConfig(
            distance_angstrom=values.distance_angstrom,
            basis=values.basis,
            mapping=values.mapping,
            two_qubit_reduction=(
                values.two_qubit_reduction if values.mapping == "parity" else False
            ),
            optimizer=values.optimizer,
            max_iterations=values.max_iterations,
            initial_point=values.initial_point,
            seed=values.seed,
        )
    except ValueError as exc:
        raise UIValidationError(str(exc)) from exc


def execute_experiment(config: ExperimentConfig) -> UIRun:
    """Build the chemistry once, then run the existing VQE implementation.

    The pre-built chemistry object is passed into ``run_h2_experiment`` so the
    circuit shown in the UI is the exact ansatz object used by the run, not a
    second decorative reconstruction.
    """
    # Keep scientific imports inside the run path. Loading Qiskit/PySCF on the
    # initial Streamlit render and then using them from a later script-run
    # thread can crash the embedded Qiskit Rust extension.
    from quantum_vqe import run_h2_experiment
    from quantum_vqe.chemistry import build_chemistry

    started = time.perf_counter()
    chemistry = build_chemistry(config)
    result = run_h2_experiment(config, chemistry=chemistry)

    circuit: CircuitArtifacts | None = None
    circuit_error: str | None = None
    try:
        # This import is lazy as well: visuals has no Qiskit import, and all
        # circuit introspection happens here, before the result is shown.
        from webapp import visuals

        summary = visuals.circuit_summary(chemistry.ansatz)
        summary_frame = pd.DataFrame(
            [
                {
                    "Level": "As built",
                    "Depth": summary["depth_as_built"],
                    "Size": summary["size_as_built"],
                },
                {
                    "Level": "Pauli evolution",
                    "Depth": summary["depth_pauli"],
                    "Size": summary["size_pauli"],
                },
                {
                    "Level": "Basis gates",
                    "Depth": summary["depth_decomposed"],
                    "Size": summary["size_decomposed"],
                },
            ]
        )
        circuit = CircuitArtifacts(
            summary=summary,
            summary_frame=summary_frame,
            parameter_frame=visuals.parameter_frame(result, chemistry.ansatz),
            gate_counts_frame=visuals.gate_counts_frame(chemistry.ansatz),
            diagram_basis_png=visuals.circuit_png(chemistry.ansatz, reps=2),
            diagram_pauli_png=visuals.circuit_png(chemistry.ansatz, reps=1),
            diagram_as_built_png=visuals.circuit_png(chemistry.ansatz, reps=0),
            text_diagram=str(chemistry.ansatz.draw("text")),
        )
    except Exception as exc:  # a valid scientific result should still be shown
        circuit_error = f"{type(exc).__name__}: {exc}"

    return UIRun(
        result=result,
        chemistry=chemistry,
        elapsed_s=time.perf_counter() - started,
        circuit=circuit,
        circuit_error=circuit_error,
    )


def history_rows(entries: list[UIRun]) -> list[dict[str, Any]]:
    """Return display/export rows derived only from completed real runs."""
    rows: list[dict[str, Any]] = []
    for index, entry in enumerate(entries, start=1):
        result = entry.result
        error = result.errors_hartree["absolute_vqe_vs_exact_total"]
        rows.append(
            {
                "run": index,
                "timestamp_utc": result.created_utc,
                "distance_A": result.molecule["bond_length_angstrom"],
                "basis": result.molecule["basis"],
                "mapping": result.hamiltonian["mapping"],
                "optimizer": result.optimizer["name"],
                "vqe_total_Ha": result.energies_hartree["vqe_total"],
                "exact_total_Ha": result.energies_hartree["exact_qubit_total"],
                "abs_error_Ha": error,
                "abs_error_mHa": None if error is None else error * 1000.0,
                "converged": result.optimization["converged"],
                "status": result.status,
                "elapsed_s": entry.elapsed_s,
            }
        )
    return rows


def history_frame(entries: list[UIRun]) -> pd.DataFrame:
    """Return the experiment history as a pandas DataFrame."""
    return pd.DataFrame(history_rows(entries))


