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


