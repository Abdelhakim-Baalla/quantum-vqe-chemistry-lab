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


