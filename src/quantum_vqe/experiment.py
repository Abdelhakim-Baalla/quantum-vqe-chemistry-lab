"""End-to-end H2 VQE experiment orchestration."""

from __future__ import annotations

import time
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import numpy as np
from qiskit.primitives import StatevectorEstimator

from .chemistry import ChemistryData, ChemistryError, build_chemistry
from .config import ExperimentConfig
from .hamiltonian import (
    check_hermitian,
    compare_energies,
    exact_ground_state,
    pauli_term_records,
)
from .reference import (
    FCIReference,
    ReferenceError,
    compute_pyscf_fci,
    full_jordan_wigner_reference,
)
from .results import ExperimentResult
from .versions import collect_versions
from .vqe import VQE, VQEResult, make_initial_point


class ExperimentError(RuntimeError):
    """Raised when the experiment cannot produce a trustworthy result."""


def determine_status(checks: Mapping[str, bool | None]) -> str:
    """Return ``"success"`` only if no performed check failed.

    ``None`` denotes a check that is not applicable (for example, the parity
    versus full-JW cross-check in a Jordan-Wigner run); it does not indicate a
    failure and does not count as a pass.
    """
    return "failed" if any(value is False for value in checks.values()) else "success"


def _make_checks(
    *,
    chemistry: ChemistryData,
    config: ExperimentConfig,
    vqe_result: VQEResult,
    hf_electronic: float,
    comparison_absolute_error: float,
    comparison_signed_gap: float,
    fci: FCIReference,
    hf_vs_fci_error: float | None,
    exact_vs_fci_error: float | None,
    jw_vs_parity_error: float | None,
    parity_crosscheck_applicable: bool,
) -> dict[str, bool | None]:
    reference_tolerance = config.reference_tolerance
    checks: dict[str, bool | None] = {
        "hamiltonian_is_hermitian": True,
        "ansatz_qubit_count_matches_hamiltonian": (
            chemistry.ansatz.num_qubits == chemistry.qubit_hamiltonian.num_qubits
        ),
        "mapped_qubit_count_matches_configuration": (
            chemistry.qubit_hamiltonian.num_qubits
            == config.expected_num_qubits(chemistry.num_spatial_orbitals)
        ),
        "optimizer_converged": vqe_result.converged,
        "optimizer_reduced_energy": (
            vqe_result.energy <= hf_electronic + config.energy_accuracy_target
        ),
        "variational_principle": (comparison_signed_gap >= -config.variational_tolerance),
        "energy_accuracy_target_met": (comparison_absolute_error <= config.energy_accuracy_target),
        "hf_matches_pyscf_rhf": (
            hf_vs_fci_error is not None and hf_vs_fci_error <= reference_tolerance
        ),
        "exact_matches_pyscf_fci": (
            exact_vs_fci_error is not None and exact_vs_fci_error <= reference_tolerance
        ),
    }
    if not fci.available:
        # An unavailable independent reference cannot validate the experiment.
        checks["exact_matches_pyscf_fci"] = False
        checks["hf_matches_pyscf_rhf"] = False

    if parity_crosscheck_applicable:
        checks["parity_reduction_matches_full_jw"] = (
            jw_vs_parity_error is not None and jw_vs_parity_error <= reference_tolerance
        )
    else:
        checks["parity_reduction_matches_full_jw"] = None
    return checks


