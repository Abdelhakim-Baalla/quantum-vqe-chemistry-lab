"""Streamlit AppTest coverage for the Quantum Lab dashboard."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("streamlit")

from streamlit.testing.v1 import AppTest  # noqa: E402

from quantum_vqe.results import ExperimentResult  # noqa: E402
from webapp import logic  # noqa: E402

APP = Path(__file__).resolve().parents[2] / "app.py"
OFFICIAL_RESULT = Path(__file__).resolve().parents[2] / "docs" / "assets" / "h2_result.json"


@pytest.fixture
def official_result() -> ExperimentResult:
    return ExperimentResult.load(OFFICIAL_RESULT)


def _run_without_circuit(result: ExperimentResult) -> logic.UIRun:
    return logic.UIRun(
        result=result,
        chemistry=None,  # type: ignore[arg-type]
        elapsed_s=0.5,
        circuit=None,
        circuit_error="circuit artifacts intentionally omitted in this test",
    )


