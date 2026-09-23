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


def test_vqe_optimizes_one_qubit_hamiltonian(
    one_qubit_hamiltonian: SparsePauliOp,
    one_qubit_ansatz: tuple[QuantumCircuit, Parameter],
) -> None:
    ansatz, _ = one_qubit_ansatz
    vqe = VQE(
        StatevectorEstimator(),
        ansatz,
        one_qubit_hamiltonian,
        optimizer="L-BFGS-B",
        max_iterations=200,
        tolerance=1e-9,
    )
    result = vqe.minimize([0.2])

    assert result.converged is True
    assert result.success is True
    assert result.energy == pytest.approx(-1.0, abs=1e-8)
    assert len(result.parameters) == 1
    assert result.parameters[0] == pytest.approx(math.pi, abs=1e-5)
    assert result.initial_energy == pytest.approx(math.cos(0.2), abs=1e-12)
    assert result.nfev >= 1
    assert result.energy_evaluations == len(result.history)
    assert result.history
    assert all(math.isfinite(entry.energy) for entry in result.history)
    assert all(len(entry.parameters) == 1 for entry in result.history)
    assert min(entry.energy for entry in result.history) == pytest.approx(result.energy)


def test_vqe_history_records_parameters(
    one_qubit_hamiltonian: SparsePauliOp,
    one_qubit_ansatz: tuple[QuantumCircuit, Parameter],
) -> None:
    ansatz, _ = one_qubit_ansatz
    vqe = VQE(StatevectorEstimator(), ansatz, one_qubit_hamiltonian)
    vqe.minimize([0.1])
    serialized = [entry.to_dict() for entry in vqe.history]
    assert serialized
    assert serialized[0]["evaluation"] == 0
    assert serialized[0]["parameters"] == [pytest.approx(0.1)]


def test_vqe_rejects_wrong_parameter_count(
    one_qubit_hamiltonian: SparsePauliOp,
    one_qubit_ansatz: tuple[QuantumCircuit, Parameter],
) -> None:
    ansatz, _ = one_qubit_ansatz
    vqe = VQE(StatevectorEstimator(), ansatz, one_qubit_hamiltonian)
    with pytest.raises(ValueError, match="expected 1"):
        vqe.evaluate([0.0, 1.0])
    with pytest.raises(ValueError, match="expected 1"):
        vqe.minimize([0.0, 1.0])


def test_vqe_rejects_non_finite_parameters(
    one_qubit_hamiltonian: SparsePauliOp,
    one_qubit_ansatz: tuple[QuantumCircuit, Parameter],
) -> None:
    ansatz, _ = one_qubit_ansatz
    vqe = VQE(StatevectorEstimator(), ansatz, one_qubit_hamiltonian)
    with pytest.raises(ValueError, match="finite"):
        vqe.evaluate([float("nan")])


def test_vqe_rejects_qubit_mismatch(one_qubit_ansatz: tuple[QuantumCircuit, Parameter]) -> None:
    ansatz, _ = one_qubit_ansatz
    two_qubit_hamiltonian = SparsePauliOp.from_list([("IZ", 1.0)])
    with pytest.raises(ValueError, match="mismatch"):
        VQE(StatevectorEstimator(), ansatz, two_qubit_hamiltonian)


def test_vqe_reflects_optimizer_failure(
    monkeypatch: pytest.MonkeyPatch,
    one_qubit_hamiltonian: SparsePauliOp,
    one_qubit_ansatz: tuple[QuantumCircuit, Parameter],
) -> None:
    ansatz, _ = one_qubit_ansatz
    vqe = VQE(StatevectorEstimator(), ansatz, one_qubit_hamiltonian)

    def fake_minimize(function, x0, *, method, options):  # noqa: ANN001
        function(np.asarray(x0, dtype=float))
        return SimpleNamespace(
            fun=0.5,
            x=np.asarray([0.1]),
            success=False,
            message="iteration limit reached",
            status=1,
            nfev=1,
            nit=1,
            njev=0,
        )

    monkeypatch.setattr("quantum_vqe.vqe.minimize", fake_minimize)
    result = vqe.minimize([0.1])

    assert result.converged is False
    assert result.success is False
    assert "iteration limit" in result.message
    assert result.energy == pytest.approx(0.5)


