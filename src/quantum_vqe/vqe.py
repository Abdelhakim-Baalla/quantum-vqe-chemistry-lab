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


@dataclass
class VQEResult:
    """Outcome of one VQE optimization."""

    energy: float
    initial_energy: float
    parameters: tuple[float, ...]
    initial_parameters: tuple[float, ...]
    converged: bool
    success: bool
    message: str
    status_code: int
    nfev: int
    nit: int | None
    njev: int | None
    history: list[EnergyEvaluation]
    wall_time_s: float
    optimizer: str
    tolerance: float
    max_iterations: int

    @property
    def energy_evaluations(self) -> int:
        """Number of recorded cost-function evaluations."""
        return len(self.history)

    def to_dict(self) -> dict[str, Any]:
        return {
            "optimizer": self.optimizer,
            "tolerance": self.tolerance,
            "max_iterations": self.max_iterations,
            "initial_energy_hartree": self.initial_energy,
            "final_energy_hartree": self.energy,
            "initial_parameters": list(self.initial_parameters),
            "final_parameters": list(self.parameters),
            "converged": self.converged,
            "success": self.success,
            "message": self.message,
            "status_code": self.status_code,
            "nfev": self.nfev,
            "nit": self.nit,
            "njev": self.njev,
            "energy_evaluations": self.energy_evaluations,
            "history": [evaluation.to_dict() for evaluation in self.history],
            "wall_time_s": self.wall_time_s,
        }


