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


