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


def test_convergence_frame_uses_exact_recorded_points(
    official_result: ExperimentResult,
) -> None:
    frame = visuals.convergence_frame(official_result)
    history = official_result.optimization["history"]

    assert len(frame) == len(history)
    assert frame["evaluation"].tolist() == [point["evaluation"] for point in history]
    assert frame["energy_hartree"].tolist() == [point["energy_hartree"] for point in history]
    assert frame["best_so_far_hartree"].iloc[-1] == pytest.approx(
        min(point["energy_hartree"] for point in history)
    )
    assert (frame["best_so_far_hartree"] <= frame["energy_hartree"] + 1e-15).all()


def test_convergence_chart_contains_only_recorded_trace_and_real_references(
    official_result: ExperimentResult,
) -> None:
    spec = visuals.convergence_chart(official_result).to_dict()
    datasets = list(spec["datasets"].values())
    trace_data = next(item for item in datasets if item and "trace" in item[0])
    reference_data = next(item for item in datasets if item and "reference" in item[0])

    recorded = [row for row in trace_data if row["trace"] == "Recorded evaluation"]
    assert len(recorded) == len(official_result.optimization["history"])
    assert [row["energy"] for row in recorded] == [
        point["energy_hartree"] for point in official_result.optimization["history"]
    ]
    assert {row["reference"] for row in reference_data} == {
        "Exact diagonalization",
        "Hartree-Fock",
    }
    exact = next(row for row in reference_data if row["reference"] == "Exact diagonalization")
    hf = next(row for row in reference_data if row["reference"] == "Hartree-Fock")
    assert exact["energy"] == official_result.energies_hartree["exact_qubit_electronic"]
    assert hf["energy"] == official_result.energies_hartree["hf_electronic"]


def test_molecule_figure_is_labeled_geometry_not_an_orbital() -> None:
    figure = visuals.molecule_figure(0.735)
    labels = [text.get_text() for text in figure.axes[0].texts]
    plt.close(figure)

    assert labels.count("H") == 2
    assert "0.735 Å" in labels


def test_molecule_figure_rejects_invalid_distance() -> None:
    with pytest.raises(ValueError, match="positive finite"):
        visuals.molecule_figure(float("nan"))


def test_circuit_summary_and_png_are_derived_from_real_circuit() -> None:
    theta = Parameter("theta")
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.ry(theta, 1)

    summary = visuals.circuit_summary(circuit)
    assert summary["num_qubits"] == 2
    assert summary["num_parameters"] == 1
    assert summary["depth_as_built"] == 3
    assert summary["size_as_built"] == 3

    png = visuals.circuit_png(circuit, reps=2)
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(png) > 1000


def test_parameter_frame_maps_recorded_vectors_to_circuit(
    official_result: ExperimentResult,
) -> None:
    parameters = [Parameter(f"t[{index}]") for index in range(3)]
    circuit = QuantumCircuit(2)
    for index, parameter in enumerate(parameters):
        circuit.ry(parameter, index % 2)

    frame = visuals.parameter_frame(official_result, circuit)
    assert frame["Parameter"].tolist() == ["t[0]", "t[1]", "t[2]"]
    assert (
        frame["Initial value (rad)"].tolist() == official_result.optimization["initial_parameters"]
    )
    assert (
        frame["Optimized value (rad)"].tolist() == official_result.optimization["final_parameters"]
    )


def test_gate_counts_frame_covers_all_decomposition_levels() -> None:
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)

    frame = visuals.gate_counts_frame(circuit)
    assert set(frame["Decomposition"]) == {"As built", "Pauli evolution", "Basis gates"}
    as_built = frame[frame["Decomposition"] == "As built"].set_index("Gate")["Count"]
    assert as_built["h"] == 1
    assert as_built["cx"] == 1
    assert (frame["Count"] > 0).all()


def test_dashboard_frame_is_derived_from_recorded_history(
    official_result: ExperimentResult,
) -> None:
    frame = visuals.dashboard_frame(official_result)
    history = official_result.optimization["history"]
    exact = official_result.energies_hartree["exact_qubit_electronic"]

    assert len(frame) == len(history)
    assert frame["energy_hartree"].tolist() == [point["energy_hartree"] for point in history]
    assert frame["gap_hartree"].iloc[0] == pytest.approx(abs(history[0]["energy_hartree"] - exact))
    assert frame["best_gap_hartree"].iloc[-1] == pytest.approx(
        abs(min(point["energy_hartree"] for point in history) - exact)
    )
    assert frame["step_improvement_mha"].sum() == pytest.approx(
        (history[0]["energy_hartree"] - min(point["energy_hartree"] for point in history)) * 1000.0
    )
    assert {"t[0]", "t[1]", "t[2]"}.issubset(frame.columns)


def test_dashboard_charts_use_the_recorded_dashboard_frame(
    official_result: ExperimentResult,
) -> None:
    frame = visuals.dashboard_frame(official_result)
    error_spec = visuals.dashboard_error_chart(official_result).to_dict()
    improvement_spec = visuals.dashboard_improvement_chart(official_result).to_dict()
    ledger_spec = visuals.dashboard_energy_ledger_chart(official_result).to_dict()

    error_rows = [
        row
        for dataset in error_spec["datasets"].values()
        for row in dataset
        if row.get("trace") == "Recorded evaluation"
    ]
    positive = frame[frame["gap_hartree"] > 0]
    assert len(error_rows) == len(positive)
    assert [row["gap"] for row in error_rows] == positive["gap_hartree"].tolist()

    improvement_rows = [row for dataset in improvement_spec["datasets"].values() for row in dataset]
    assert len(improvement_rows) == len(frame)
    assert [row["step_improvement_mha"] for row in improvement_rows] == frame[
        "step_improvement_mha"
    ].tolist()

    ledger_rows = [row for dataset in ledger_spec["datasets"].values() for row in dataset]
    assert {row["method"] for row in ledger_rows} == {
        "Hartree–Fock",
        "VQE",
        "Exact qubit",
        "PySCF FCI",
    }


def test_dark_theme_changes_chart_and_circuit_rendering(
    official_result: ExperimentResult,
) -> None:
    light_spec = visuals.convergence_chart(official_result, theme="light").to_dict()
    dark_spec = visuals.convergence_chart(official_result, theme="dark").to_dict()
    assert light_spec["config"]["axis"]["labelColor"] == "#6f6f6f"
    assert dark_spec["config"]["axis"]["labelColor"] == "#a8b2c1"

    theta = Parameter("theta")
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.ry(theta, 1)
    light_png = visuals.circuit_png(circuit, theme="light")
    dark_png = visuals.circuit_png(circuit, theme="dark")
    assert light_png.startswith(b"\x89PNG\r\n\x1a\n")
    assert dark_png.startswith(b"\x89PNG\r\n\x1a\n")
    assert light_png != dark_png


def test_unknown_visual_theme_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown theme"):
        visuals._palette("sepia")
