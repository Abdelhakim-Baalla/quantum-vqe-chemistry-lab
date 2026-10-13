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


