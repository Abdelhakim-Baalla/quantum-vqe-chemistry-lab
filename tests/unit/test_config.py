"""Unit tests for configuration validation and serialization."""

from __future__ import annotations

import json

import pytest

from quantum_vqe.config import DEFAULT_TOLERANCES, ExperimentConfig


def test_default_configuration() -> None:
    config = ExperimentConfig()
    assert config.distance_angstrom == pytest.approx(0.735)
    assert config.basis == "sto3g"
    assert config.mapping == "parity"
    assert config.two_qubit_reduction is True
    assert config.optimizer == "L-BFGS-B"
    assert config.tolerance == pytest.approx(DEFAULT_TOLERANCES["L-BFGS-B"])
    assert config.expected_num_qubits(2) == 2
    assert "0.735000000000" in config.geometry_angstrom


def test_jordan_wigner_resolves_to_no_reduction() -> None:
    config = ExperimentConfig(mapping="jordan-wigner")
    assert config.two_qubit_reduction is False
    assert config.expected_num_qubits(2) == 4


def test_jordan_wigner_rejects_two_qubit_reduction() -> None:
    with pytest.raises(ValueError, match="two-qubit"):
        ExperimentConfig(mapping="jordan-wigner", two_qubit_reduction=True)


def test_mapping_and_optimizer_aliases() -> None:
    config = ExperimentConfig(mapping="jordan_wigner", optimizer="bfgs")
    assert config.mapping == "jordan-wigner"
    assert config.optimizer == "BFGS"
    assert config.tolerance == pytest.approx(DEFAULT_TOLERANCES["BFGS"])


@pytest.mark.parametrize(
    "overrides",
    [
        {"distance_angstrom": 0.0},
        {"distance_angstrom": -0.5},
        {"distance_angstrom": float("nan")},
        {"distance_angstrom": float("inf")},
        {"basis": "   "},
        {"charge": 1.5},
        {"spin": 1},
        {"spin": -2},
        {"mapping": "bogus"},
        {"two_qubit_reduction": "yes"},
        {"optimizer": "adam"},
        {"max_iterations": 0},
        {"max_iterations": 100_001},
        {"tolerance": 0.0},
        {"tolerance": -1e-6},
        {"initial_point": "middle"},
        {"seed": -1},
        {"energy_accuracy_target": 0.0},
        {"variational_tolerance": -1e-8},
        {"reference_tolerance": 0.0},
    ],
)
def test_invalid_configurations_raise(overrides: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        ExperimentConfig(**overrides)


def test_configuration_dict_roundtrip() -> None:
    config = ExperimentConfig(
        distance_angstrom=0.8,
        basis="sto3g",
        optimizer="SLSQP",
        initial_point="random",
        seed=123,
    )
    payload = config.to_dict()
    assert json.loads(json.dumps(payload)) == payload
    assert ExperimentConfig.from_dict(payload) == config


def test_configuration_from_dict_rejects_unknown_fields() -> None:
    with pytest.raises(ValueError, match="unknown"):
        ExperimentConfig.from_dict({"distance_angstrom": 0.735, "not_a_field": 1})
