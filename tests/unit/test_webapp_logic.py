"""Tests for the Streamlit-independent Quantum Lab web logic."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("pandas")

from quantum_vqe.results import ExperimentResult  # noqa: E402
from webapp import logic  # noqa: E402

OFFICIAL_RESULT = Path(__file__).resolve().parents[2] / "docs" / "assets" / "h2_result.json"


@pytest.fixture
def official_result() -> ExperimentResult:
    return ExperimentResult.load(OFFICIAL_RESULT)


@pytest.fixture
def valid_values() -> logic.UIConfigInput:
    return logic.UIConfigInput(
        molecule="H2",
        distance_angstrom=0.735,
        basis="sto3g",
        ansatz="UCCSD",
        mapping="parity",
        two_qubit_reduction=True,
        optimizer="L-BFGS-B",
        max_iterations=500,
        initial_point="hf",
        seed=7,
        output_dir="results",
    )


def test_build_config_maps_form_values(valid_values: logic.UIConfigInput) -> None:
    config = logic.build_experiment_config(valid_values)

    assert config.distance_angstrom == pytest.approx(0.735)
    assert config.basis == "sto3g"
    assert config.mapping == "parity"
    assert config.two_qubit_reduction is True
    assert config.optimizer == "L-BFGS-B"
    assert config.max_iterations == 500
    assert config.initial_point == "hf"
    assert config.seed == 7


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("molecule", "LiH", "Only H2"),
        ("basis", "6-31g", "not exposed"),
        ("ansatz", "QAOA", "not implemented"),
        ("mapping", "bravyi-kitaev", "Unknown mapping"),
        ("optimizer", "Powell", "Unknown optimizer"),
        ("initial_point", "zero", "Unknown initial point"),
    ],
)
def test_build_config_rejects_unsupported_options(
    valid_values: logic.UIConfigInput,
    field: str,
    value: str,
    message: str,
) -> None:
    with pytest.raises(logic.UIValidationError, match=message):
        logic.build_experiment_config(replace(valid_values, **{field: value}))


def test_build_config_rejects_jordan_wigner_with_reduction(
    valid_values: logic.UIConfigInput,
) -> None:
    values = replace(valid_values, mapping="jordan-wigner", two_qubit_reduction=True)
    with pytest.raises(logic.UIValidationError, match="does not support"):
        logic.build_experiment_config(values)


