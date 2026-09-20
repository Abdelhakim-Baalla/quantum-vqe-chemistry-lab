"""A transparent VQE loop built on Qiskit's exact statevector estimator.

The loop is deliberately implemented here rather than hidden behind a solver
class.  That makes the cost function, optimizer history, convergence flag and
energy evaluations explicit and easy to test.
"""

from __future__ import annotations

import math
import time
import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp
from scipy.optimize import minimize
from scipy.sparse import SparseEfficiencyWarning

from .config import DEFAULT_TOLERANCES, normalize_optimizer


class VQEError(RuntimeError):
    """Raised when the VQE loop cannot evaluate or optimize the ansatz."""


@dataclass(frozen=True)
class EnergyEvaluation:
    """One call to the VQE cost function."""

    evaluation: int
    energy: float
    parameters: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation": self.evaluation,
            "energy_hartree": self.energy,
            "parameters": list(self.parameters),
        }


