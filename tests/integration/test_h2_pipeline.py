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


