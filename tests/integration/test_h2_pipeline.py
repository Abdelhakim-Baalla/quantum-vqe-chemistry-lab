"""End-to-end tests for the H2 chemistry, VQE, references and CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("pyscf")

from quantum_vqe import ExperimentConfig, run_h2_experiment  # noqa: E402
from quantum_vqe.plotting import plot_convergence  # noqa: E402
from quantum_vqe.results import ExperimentResult  # noqa: E402

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def h2_result() -> ExperimentResult:
    return run_h2_experiment(ExperimentConfig())


def test_default_h2_run_is_successful(h2_result: ExperimentResult) -> None:
    assert h2_result.status == "success"
    assert all(value is not False for value in h2_result.checks.values())
    assert h2_result.checks["optimizer_converged"] is True
    assert h2_result.checks["parity_reduction_matches_full_jw"] is True
    assert h2_result.optimization["converged"] is True
    assert h2_result.optimization["nfev"] >= 1
    assert h2_result.optimization["energy_evaluations"] == len(h2_result.optimization["history"])


def test_h2_problem_dimensions(h2_result: ExperimentResult) -> None:
    assert h2_result.molecule["num_electrons"] == 2
    assert h2_result.molecule["num_spatial_orbitals"] == 2
    assert h2_result.molecule["num_spin_orbitals"] == 4
    assert h2_result.molecule["num_qubits"] == 2
    assert h2_result.hamiltonian["num_qubits"] == 2
    assert h2_result.ansatz["num_qubits"] == 2
    assert h2_result.ansatz["num_parameters"] == 3
    assert h2_result.hamiltonian["hermiticity"]["hermitian"] is True
    assert h2_result.molecule["nuclear_repulsion_energy_hartree"] == pytest.approx(
        0.7199689944489797, abs=1e-12
    )


def test_h2_energy_matches_independent_references(h2_result: ExperimentResult) -> None:
    energies = h2_result.energies_hartree
    errors = h2_result.errors_hartree

    # FCI benchmark for H2/STO-3G at 0.735 Angstrom (total, including nuclear repulsion).
    assert energies["vqe_total"] == pytest.approx(-1.1373060357534, abs=1e-6)
    assert energies["exact_qubit_total"] == pytest.approx(-1.1373060357534, abs=1e-6)
    assert energies["pyscf_fci_total"] == pytest.approx(-1.1373060357534, abs=1e-6)

    assert errors["absolute_vqe_vs_exact_total"] <= 1e-6
    assert errors["absolute_exact_vs_pyscf_fci_total"] <= 1e-6
    assert errors["absolute_hf_vs_pyscf_rhf_electronic"] <= 1e-6
    assert errors["absolute_parity_vs_full_jw_electronic"] <= 1e-6

    # Variational principle, allowing only floating-point noise.
    assert errors["signed_variational_gap_electronic"] >= -1e-8
    assert h2_result.checks["energy_accuracy_target_met"] is True
    assert h2_result.checks["variational_principle"] is True


def test_h2_result_roundtrip(h2_result: ExperimentResult, tmp_path: Path) -> None:
    path = tmp_path / "h2.json"
    h2_result.save(path)
    loaded = ExperimentResult.load(path)
    assert loaded.to_dict() == h2_result.to_dict()


def test_h2_convergence_plot(h2_result: ExperimentResult, tmp_path: Path) -> None:
    path = plot_convergence(
        h2_result.optimization["history"],
        tmp_path / "h2.png",
        exact_energy=h2_result.energies_hartree["exact_qubit_electronic"],
        hf_energy=h2_result.energies_hartree["hf_electronic"],
    )
    assert path.exists()
    assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.parametrize("optimizer", ["BFGS", "L-BFGS-B", "SLSQP", "COBYLA", "Nelder-Mead"])
def test_supported_optimizers_converge(optimizer: str) -> None:
    result = run_h2_experiment(ExperimentConfig(optimizer=optimizer, max_iterations=600))
    assert result.status == "success"
    assert result.optimization["converged"] is True
    assert result.errors_hartree["absolute_vqe_vs_exact_total"] <= 1e-6


