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


def test_exact_ground_state_of_two_qubit_operator() -> None:
    # H = -0.5 * (Z0 + Z1): ground state |00> has energy -1.
    result = exact_ground_state(SparsePauliOp.from_list([("IZ", -0.5), ("ZI", -0.5)]))
    assert result.ground_energy == pytest.approx(-1.0)
    assert result.first_excited_energy == pytest.approx(0.0)
    assert result.dimension == 4


def test_compare_energies() -> None:
    comparison = compare_energies(-0.9, -1.0)
    assert comparison.absolute_error == pytest.approx(0.1)
    assert comparison.signed_gap == pytest.approx(0.1)

    undershoot = compare_energies(-1.0 - 1e-12, -1.0)
    assert undershoot.signed_gap < 0.0
    assert undershoot.absolute_error == pytest.approx(1e-12)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_compare_energies_rejects_non_finite(value: float) -> None:
    with pytest.raises(ValueError):
        compare_energies(value, -1.0)


def test_expectation_from_statevector_matches_analytic_value() -> None:
    theta = Parameter("theta")
    circuit = QuantumCircuit(1)
    circuit.ry(theta, 0)
    operator = SparsePauliOp.from_list([("Z", 1.0)])

    value_zero = expectation_from_statevector(circuit, operator, [0.0])
    value_pi = expectation_from_statevector(circuit, operator, [math.pi])
    value_half = expectation_from_statevector(circuit, operator, [0.5])

    assert value_zero == pytest.approx(1.0, abs=1e-12)
    assert value_pi == pytest.approx(-1.0, abs=1e-12)
    assert value_half == pytest.approx(math.cos(0.5), abs=1e-12)


def test_expectation_from_statevector_validates_parameters() -> None:
    theta = Parameter("theta")
    circuit = QuantumCircuit(1)
    circuit.ry(theta, 0)
    operator = SparsePauliOp.from_list([("Z", 1.0)])

    with pytest.raises(ValueError, match="parameter"):
        expectation_from_statevector(circuit, operator, [0.0, 1.0])


def test_pauli_term_records() -> None:
    operator = SparsePauliOp.from_list([("II", -0.5), ("ZZ", 0.25)])
    records = pauli_term_records(operator)
    assert [record["pauli"] for record in records] == ["II", "ZZ"]
    assert records[0]["coefficient"] == pytest.approx(-0.5)
    assert records[1]["coefficient"] == pytest.approx(0.25)
    assert all(record["coefficient_imag"] == pytest.approx(0.0) for record in records)
