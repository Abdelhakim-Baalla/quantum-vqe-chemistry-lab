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


