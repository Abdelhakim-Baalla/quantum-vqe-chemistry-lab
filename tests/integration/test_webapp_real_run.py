"""End-to-end UI test: run the real H2 VQE through Streamlit AppTest."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("streamlit")

from streamlit.testing.v1 import AppTest  # noqa: E402

pytestmark = pytest.mark.integration

APP = Path(__file__).resolve().parents[2] / "app.py"


def test_real_h2_experiment_through_ui() -> None:
    app = AppTest.from_file(APP, default_timeout=180).run()
    assert not app.exception
    assert not app.error

    app.sidebar.button(key="run_experiment").click()
    app.run(timeout=300)

    assert not app.exception
    assert not app.error
    run = app.session_state["run"]
    result = run.result
    assert result.status == "success"
    assert result.errors_hartree["absolute_vqe_vs_exact_total"] <= 1e-6
    assert result.energies_hartree["vqe_total"] == pytest.approx(-1.1373060357534, abs=1e-6)
    assert run.circuit is not None
    assert run.circuit.diagram_basis_png.startswith(b"\x89PNG\r\n\x1a\n")
    assert run.circuit.parameter_frame["Parameter"].tolist() == ["t[0]", "t[1]", "t[2]"]

    metrics = {metric.label: metric.value for metric in app.metric}
    assert metrics["VQE total energy"] == f"{result.energies_hartree['vqe_total']:.12f} Ha"
    assert (
        metrics["Exact total energy"] == f"{result.energies_hartree['exact_qubit_total']:.12f} Ha"
    )
    assert metrics["Qubits"] == "2"
    assert metrics["Parameters"] == "3"
    assert metrics["Energy evaluations"] == str(result.optimization["energy_evaluations"])
    assert len(app.session_state["history"]) == 1
    assert len(app.image) >= 4

    # A normal Streamlit rerun after the run must not execute the experiment again
    # or lose the displayed result.
    app.run(timeout=60)
    assert not app.exception
    assert not app.error
    assert len(app.session_state["history"]) == 1
    assert app.session_state["run"] is run
