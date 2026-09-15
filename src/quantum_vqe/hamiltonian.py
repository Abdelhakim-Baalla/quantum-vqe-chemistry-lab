"""Operator inspection, exact diagonalization, and energy-error helpers."""

from __future__ import annotations

import math
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector


class OperatorError(ValueError):
    """Raised for invalid operator or energy inputs."""


@dataclass(frozen=True)
class HermiticityReport:
    """Result of checking whether a qubit operator is Hermitian."""

    hermitian: bool
    max_asymmetry: float
    num_qubits: int
    num_terms: int
    method: str
    tolerance: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "hermitian": self.hermitian,
            "max_asymmetry": self.max_asymmetry,
            "num_qubits": self.num_qubits,
            "num_terms": self.num_terms,
            "method": self.method,
            "tolerance": self.tolerance,
        }


@dataclass(frozen=True)
class ExactDiagonalization:
    """Ground-state result from exact diagonalization of a qubit Hamiltonian."""

    ground_energy: float
    first_excited_energy: float | None
    gap: float | None
    dimension: int
    method: str
    wall_time_s: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "ground_energy": self.ground_energy,
            "first_excited_energy": self.first_excited_energy,
            "gap": self.gap,
            "dimension": self.dimension,
            "method": self.method,
            "wall_time_s": self.wall_time_s,
        }


