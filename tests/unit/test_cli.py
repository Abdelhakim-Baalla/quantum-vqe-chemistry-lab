"""Fast unit tests for the CLI using the checked-in official result."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantum_vqe import cli
from quantum_vqe.chemistry import ChemistryError
from quantum_vqe.results import ExperimentResult

OFFICIAL_RESULT = Path(__file__).resolve().parents[2] / "docs" / "assets" / "h2_result.json"


@pytest.fixture
def official_result() -> ExperimentResult:
    """Load the official result so the CLI is rendered against real fields."""
    return ExperimentResult.load(OFFICIAL_RESULT)


