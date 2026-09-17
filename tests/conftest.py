"""Shared test fixtures."""

from __future__ import annotations

import pytest
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.quantum_info import SparsePauliOp


@pytest.fixture
def one_qubit_hamiltonian() -> SparsePauliOp:
    """A one-qubit Hamiltonian with ground energy -1."""
    return SparsePauliOp.from_list([("Z", 1.0)])


@pytest.fixture
def one_qubit_ansatz() -> tuple[QuantumCircuit, Parameter]:
    """A single RY rotation; the ground state of Z is at theta=pi."""
    theta = Parameter("theta")
    circuit = QuantumCircuit(1)
    circuit.ry(theta, 0)
    return circuit, theta
