"""Unit tests for result serialization, validation and status logic."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from quantum_vqe.experiment import determine_status
from quantum_vqe.results import SCHEMA_VERSION, ExperimentResult


def make_result(**overrides: Any) -> ExperimentResult:
    payload: dict[str, Any] = {
        "experiment": "unit_test",
        "status": "success",
        "created_utc": "2026-01-01T00:00:00+00:00",
        "config": {"distance_angstrom": 0.735},
        "molecule": {"name": "H2"},
        "hamiltonian": {"num_qubits": 2},
        "ansatz": {"name": "UCCSD"},
        "optimizer": {"name": "L-BFGS-B"},
        "simulator": {"name": "StatevectorEstimator"},
        "energies_hartree": {"vqe_total": -1.0, "exact_qubit_total": -1.0},
        "errors_hartree": {"absolute_vqe_vs_exact_total": 0.0},
        "checks": {"optimizer_converged": True, "not_applicable": None},
        "check_tolerances_hartree": {"energy_accuracy_target": 1e-6},
        "references": {"same_qubit_hamiltonian": {"ground_energy": -1.0}},
        "optimization": {"nfev": 3, "history": [{"evaluation": 0, "energy_hartree": -0.5}]},
        "timing_seconds": {"total": 0.1},
        "software": {"python": "3.12.0"},
        "warnings": [],
        "artifacts": {},
    }
    payload.update(overrides)
    return ExperimentResult(**payload)


def test_result_schema_and_roundtrip(tmp_path: Path) -> None:
    result = make_result()
    path = tmp_path / "nested" / "result.json"
    saved = result.save(path)
    assert saved == path
    assert path.exists()

    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["schema_version"] == SCHEMA_VERSION
    assert raw["checks"]["not_applicable"] is None

    loaded = ExperimentResult.load(path)
    assert loaded.to_dict() == result.to_dict()


def test_result_to_json_is_valid_json() -> None:
    text = make_result().to_json()
    assert text.endswith("\n")
    assert json.loads(text)["experiment"] == "unit_test"


def test_result_rejects_non_finite_float() -> None:
    result = make_result(energies_hartree={"vqe_total": float("nan")})
    with pytest.raises(ValueError, match="non-finite"):
        result.to_json()


def test_result_rejects_invalid_status() -> None:
    with pytest.raises(ValueError, match="status"):
        make_result(status="maybe")


def test_result_load_rejects_wrong_schema(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    payload = make_result().to_dict()
    payload["schema_version"] = "999"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="schema"):
        ExperimentResult.load(path)


def test_result_load_rejects_missing_field(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"
    payload = make_result().to_dict()
    del payload["molecule"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="missing"):
        ExperimentResult.load(path)


def test_result_load_rejects_unknown_field(tmp_path: Path) -> None:
    path = tmp_path / "unknown.json"
    payload = make_result().to_dict()
    payload["surprise"] = 1
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown"):
        ExperimentResult.load(path)


def test_result_load_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid JSON"):
        ExperimentResult.load(path)


