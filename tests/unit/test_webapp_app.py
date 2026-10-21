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


def test_app_starts_and_shows_no_fake_energy_values() -> None:
    app = AppTest.from_file(APP, default_timeout=60).run()

    assert not app.exception
    assert not app.error
    assert any("Quantum Lab" in markdown.value for markdown in app.markdown)
    assert app.sidebar.button(key="run_experiment").label == "Run VQE Experiment"
    assert [tab.label for tab in app.tabs] == [
        "Experiment",
        "Quantum circuit",
        "Convergence",
        "History",
        "Learn",
    ]
    assert len(app.metric) == 0
    assert any("No energies are displayed yet" in info.value for info in app.info)


