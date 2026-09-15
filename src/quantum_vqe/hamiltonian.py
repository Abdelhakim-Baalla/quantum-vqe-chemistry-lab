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


@dataclass(frozen=True)
class EnergyComparison:
    """Signed and absolute comparison of a variational and exact energy."""

    vqe_energy: float
    exact_energy: float
    signed_gap: float
    absolute_error: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "vqe_energy": self.vqe_energy,
            "exact_energy": self.exact_energy,
            "signed_gap": self.signed_gap,
            "absolute_error": self.absolute_error,
        }


def check_hermitian(operator: SparsePauliOp, *, atol: float = 1e-10) -> HermiticityReport:
    """Check Hermiticity numerically.

    For small operators (up to 12 qubits) the full matrix is constructed and
    compared with its conjugate transpose.  Larger operators fall back to
    checking that all Pauli coefficients are real.
    """
    if not isinstance(operator, SparsePauliOp):
        raise TypeError(f"operator must be a SparsePauliOp, got {type(operator).__name__}")
    if operator.num_qubits < 1:
        raise OperatorError("operator must act on at least one qubit")
    if atol <= 0:
        raise ValueError("atol must be > 0")

    if operator.num_qubits <= 12:
        matrix = operator.to_matrix(sparse=False)
        asymmetry = matrix - matrix.conj().T
        max_asymmetry = float(np.max(np.abs(asymmetry)))
        method = "dense_matrix_vs_adjoint"
    else:
        max_asymmetry = float(np.max(np.abs(np.imag(operator.coeffs))))
        method = "imaginary_part_of_pauli_coefficients"

    return HermiticityReport(
        hermitian=bool(max_asymmetry <= atol),
        max_asymmetry=max_asymmetry,
        num_qubits=operator.num_qubits,
        num_terms=len(operator),
        method=method,
        tolerance=atol,
    )


def exact_ground_state(
    operator: SparsePauliOp, *, dense_threshold: int = 1024
) -> ExactDiagonalization:
    """Diagonalize a qubit Hamiltonian exactly.

    Small Hamiltonians use dense ``numpy.linalg.eigvalsh``; larger ones use
    ``scipy.sparse.linalg.eigsh``.  The H2 experiments use only 2 or 4 qubits,
    so the dense path is exercised.
    """
    if not isinstance(operator, SparsePauliOp):
        raise TypeError(f"operator must be a SparsePauliOp, got {type(operator).__name__}")
    if operator.num_qubits < 1:
        raise OperatorError("operator must act on at least one qubit")

    dimension = 2**operator.num_qubits
    started = time.perf_counter()

    if dimension <= dense_threshold:
        matrix = operator.to_matrix(sparse=False)
        eigenvalues = np.linalg.eigvalsh(matrix)
        method = "dense_eigvalsh"
    else:
        from scipy.sparse.linalg import eigsh

        matrix = operator.to_matrix(sparse=True).tocsc()
        k = min(2, dimension - 1)
        eigenvalues = eigsh(matrix, k=k, which="SA", return_eigenvectors=False)
        eigenvalues = np.sort(eigenvalues)
        method = "sparse_eigsh"

    if eigenvalues.size == 0:
        raise OperatorError("diagonalization returned no eigenvalues")
    ground = float(eigenvalues[0])
    first_excited = float(eigenvalues[1]) if eigenvalues.size > 1 else None
    gap = (first_excited - ground) if first_excited is not None else None
    if not math.isfinite(ground):
        raise OperatorError("diagonalization returned a non-finite ground energy")

    return ExactDiagonalization(
        ground_energy=ground,
        first_excited_energy=first_excited,
        gap=gap,
        dimension=dimension,
        method=method,
        wall_time_s=time.perf_counter() - started,
    )


