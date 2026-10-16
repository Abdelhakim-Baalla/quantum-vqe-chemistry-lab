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


