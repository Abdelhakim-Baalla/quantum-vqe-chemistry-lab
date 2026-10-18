"""Tests for real-result-only visualizations in the web interface."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("altair")
pytest.importorskip("matplotlib")

import matplotlib.pyplot as plt  # noqa: E402
from qiskit import QuantumCircuit  # noqa: E402
from qiskit.circuit import Parameter  # noqa: E402

from quantum_vqe.results import ExperimentResult  # noqa: E402
from webapp import visuals  # noqa: E402

OFFICIAL_RESULT = Path(__file__).resolve().parents[2] / "docs" / "assets" / "h2_result.json"


@pytest.fixture
def official_result() -> ExperimentResult:
    return ExperimentResult.load(OFFICIAL_RESULT)


