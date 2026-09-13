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


