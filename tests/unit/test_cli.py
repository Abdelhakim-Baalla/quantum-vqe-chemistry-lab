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


def test_cli_renders_official_result(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    official_result: ExperimentResult,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "run_h2_experiment", lambda config: official_result)
    output = tmp_path / "result.json"

    code = cli.main(["run-h2", "--json", str(output)])
    captured = capsys.readouterr()

    assert code == 0
    assert "Status:              SUCCESS" in captured.out
    assert "VQE total (electronic + nuclear)" in captured.out
    assert "Exact qubit total" in captured.out
    assert "converged: yes" in captured.out
    saved = ExperimentResult.load(output)
    assert saved.status == "success"
    assert saved.artifacts["json"] == str(output)


