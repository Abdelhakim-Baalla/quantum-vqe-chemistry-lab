"""Unit tests for the explicit VQE loop."""

from __future__ import annotations

import math
from types import SimpleNamespace

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp

from quantum_vqe.hamiltonian import expectation_from_statevector
from quantum_vqe.vqe import VQE, make_initial_point


def test_vqe_evaluate_matches_statevector_expectation(
    one_qubit_hamiltonian: SparsePauliOp,
    one_qubit_ansatz: tuple[QuantumCircuit, Parameter],
) -> None:
    ansatz, _ = one_qubit_ansatz
    vqe = VQE(StatevectorEstimator(), ansatz, one_qubit_hamiltonian)
    value = vqe.evaluate([0.37])
    independent = expectation_from_statevector(ansatz, one_qubit_hamiltonian, [0.37])
    assert value == pytest.approx(independent, abs=1e-12)
    assert value == pytest.approx(math.cos(0.37), abs=1e-12)


