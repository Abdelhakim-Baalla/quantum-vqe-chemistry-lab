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


def test_build_config_allows_jordan_wigner_without_reduction(
    valid_values: logic.UIConfigInput,
) -> None:
    values = replace(valid_values, mapping="jordan-wigner", two_qubit_reduction=False)
    config = logic.build_experiment_config(values)
    assert config.mapping == "jordan-wigner"
    assert config.two_qubit_reduction is False


def test_build_config_rejects_invalid_distance(valid_values: logic.UIConfigInput) -> None:
    with pytest.raises(logic.UIValidationError, match="distance_angstrom"):
        logic.build_experiment_config(replace(valid_values, distance_angstrom=-0.5))


def test_build_config_rejects_empty_output_directory(
    valid_values: logic.UIConfigInput,
) -> None:
    with pytest.raises(logic.UIValidationError, match="cannot be empty"):
        logic.build_experiment_config(replace(valid_values, output_dir="   "))


def test_build_config_rejects_output_file(
    valid_values: logic.UIConfigInput, tmp_path: Path
) -> None:
    output_file = tmp_path / "already-a-file"
    output_file.write_text("not a directory", encoding="utf-8")
    with pytest.raises(logic.UIValidationError, match="not a directory"):
        logic.build_experiment_config(replace(valid_values, output_dir=str(output_file)))


def test_execute_experiment_calls_existing_scientific_layer(
    monkeypatch: pytest.MonkeyPatch,
    valid_values: logic.UIConfigInput,
    official_result: ExperimentResult,
) -> None:
    config = logic.build_experiment_config(valid_values)
    chemistry = SimpleNamespace()
    calls: dict[str, object] = {}

    def fake_build(received_config):  # noqa: ANN001
        calls["build"] = received_config
        return chemistry

    def fake_run(received_config, *, chemistry):  # noqa: ANN001
        calls["run"] = (received_config, chemistry)
        return official_result

    monkeypatch.setattr("quantum_vqe.chemistry.build_chemistry", fake_build)
    monkeypatch.setattr("quantum_vqe.run_h2_experiment", fake_run)

    run = logic.execute_experiment(config)

    assert calls["build"] is config
    assert calls["run"] == (config, chemistry)
    assert run.result is official_result
    assert run.chemistry is chemistry
    assert run.elapsed_s >= 0.0
    assert run.circuit is None
    assert run.circuit_error is not None


def test_execute_experiment_propagates_scientific_failure(
    monkeypatch: pytest.MonkeyPatch,
    valid_values: logic.UIConfigInput,
) -> None:
    config = logic.build_experiment_config(valid_values)
    monkeypatch.setattr("quantum_vqe.chemistry.build_chemistry", lambda config: SimpleNamespace())

    def fail(config, *, chemistry):  # noqa: ANN001
        raise RuntimeError("solver failed")

    monkeypatch.setattr("quantum_vqe.run_h2_experiment", fail)

    with pytest.raises(RuntimeError, match="solver failed"):
        logic.execute_experiment(config)


def test_absolute_error_mha_matches_result(official_result: ExperimentResult) -> None:
    expected = official_result.errors_hartree["absolute_vqe_vs_exact_total"] * 1000.0
    assert logic.absolute_error_mha(official_result) == pytest.approx(expected)


