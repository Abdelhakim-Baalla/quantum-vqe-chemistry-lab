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


def test_parser_defaults() -> None:
    parser = cli._build_parser()
    args = parser.parse_args(["run-h2"])
    assert args.distance == pytest.approx(0.735)
    assert args.basis == "sto3g"
    assert args.mapping == "parity"
    assert args.two_qubit_reduction is None
    assert args.optimizer == "L-BFGS-B"
    assert args.json_path is None
    assert args.plot is False


