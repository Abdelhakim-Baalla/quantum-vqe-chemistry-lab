"""Unit tests for operator properties and energy comparisons."""

from __future__ import annotations

import math

import pytest
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import SparsePauliOp

from quantum_vqe.hamiltonian import (
    check_hermitian,
    compare_energies,
    exact_ground_state,
    expectation_from_statevector,
    pauli_term_records,
)


def test_hermitian_operator_passes() -> None:
    operator = SparsePauliOp.from_list([("Z", 0.5), ("X", 0.2)])
    report = check_hermitian(operator)
    assert report.hermitian is True
    assert report.max_asymmetry == pytest.approx(0.0, abs=1e-12)
    assert report.num_qubits == 1
    assert report.num_terms == 2


def test_non_hermitian_operator_fails() -> None:
    operator = SparsePauliOp.from_list([("X", 1.0j)])
    report = check_hermitian(operator)
    assert report.hermitian is False
    assert report.max_asymmetry > 1e-3


def test_exact_ground_state_of_pauli_z() -> None:
    result = exact_ground_state(SparsePauliOp.from_list([("Z", 1.0)]))
    assert result.ground_energy == pytest.approx(-1.0)
    assert result.first_excited_energy == pytest.approx(1.0)
    assert result.gap == pytest.approx(2.0)
    assert result.dimension == 2
    assert result.method == "dense_eigvalsh"
    assert result.wall_time_s >= 0.0


