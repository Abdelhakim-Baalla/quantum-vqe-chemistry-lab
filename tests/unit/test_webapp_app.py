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


def test_app_displays_values_from_a_real_result(
    monkeypatch: pytest.MonkeyPatch,
    official_result: ExperimentResult,
) -> None:
    received: dict[str, object] = {}

    def fake_execute(config):  # noqa: ANN001
        received["config"] = config
        return _run_without_circuit(official_result)

    monkeypatch.setattr(logic, "execute_experiment", fake_execute)
    app = AppTest.from_file(APP, default_timeout=60).run()
    app.sidebar.button(key="run_experiment").click()
    app.run(timeout=60)

    assert not app.exception
    assert not app.error
    config = received["config"]
    assert config.distance_angstrom == pytest.approx(0.735)
    assert config.mapping == "parity"
    assert config.optimizer == "L-BFGS-B"

    metrics = {metric.label: metric.value for metric in app.metric}
    energies = official_result.energies_hartree
    errors = official_result.errors_hartree
    assert metrics["VQE total energy"] == f"{energies['vqe_total']:.12f} Ha"
    assert metrics["Exact total energy"] == f"{energies['exact_qubit_total']:.12f} Ha"
    assert metrics["VQE electronic"] == f"{energies['vqe_electronic']:.12f} Ha"
    assert metrics["Exact electronic"] == f"{energies['exact_qubit_electronic']:.12f} Ha"
    assert metrics["Energy evaluations"] == str(official_result.optimization["energy_evaluations"])
    assert metrics["Optimizer converged"] == "Yes"

    error_ha = errors["absolute_vqe_vs_exact_total"]
    assert metrics["Absolute error (Ha)"] == f"{error_ha:.3e} Ha"
    expected_mha = (
        f"{error_ha * 1000.0:.3e} mHa"
        if abs(error_ha * 1000.0) < 1e-3
        else f"{error_ha * 1000.0:.6f} mHa"
    )
    assert metrics["Absolute error (mHa)"] == expected_mha
    assert len(app.session_state["history"]) == 1
    assert app.session_state["run"].result is official_result


def test_app_reports_execution_failure_without_adding_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(config):  # noqa: ANN001
        raise RuntimeError("simulated optimizer failure")

    monkeypatch.setattr(logic, "execute_experiment", fail)
    app = AppTest.from_file(APP, default_timeout=60).run()
    app.sidebar.button(key="run_experiment").click()
    app.run(timeout=60)

    assert not app.exception
    assert any("simulated optimizer failure" in error.value for error in app.error)
    assert app.session_state.get("run") is None
    assert len(app.session_state["history"]) == 0


def test_app_reports_missing_dependency_with_actionable_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing(config):  # noqa: ANN001
        raise ImportError("No module named 'qiskit'")

    monkeypatch.setattr(logic, "execute_experiment", missing)
    app = AppTest.from_file(APP, default_timeout=60).run()
    app.sidebar.button(key="run_experiment").click()
    app.run(timeout=60)

    assert any("Scientific dependencies are missing" in error.value for error in app.error)
    assert any("pip install -e" in error.value for error in app.error)


def test_app_saves_selected_result_as_json(
    monkeypatch: pytest.MonkeyPatch,
    official_result: ExperimentResult,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        logic,
        "execute_experiment",
        lambda config: _run_without_circuit(official_result),
    )
    app = AppTest.from_file(APP, default_timeout=60).run()
    app.sidebar.text_input(key="cfg_output_dir").set_value(str(tmp_path))
    app.run(timeout=60)
    app.sidebar.button(key="run_experiment").click()
    app.run(timeout=60)
    app.button(key="save_selected_result").click()
    app.run(timeout=60)

    files = sorted(tmp_path.glob("*.json"))
    assert len(files) == 1
    assert ExperimentResult.load(files[0]).to_dict() == official_result.to_dict()
