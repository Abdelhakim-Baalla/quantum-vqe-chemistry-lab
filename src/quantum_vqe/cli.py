"""Command-line interface for the H2 VQE chemistry lab."""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from . import __version__
from .chemistry import ChemistryError
from .config import OPTIMIZERS, ExperimentConfig
from .experiment import ExperimentError, run_h2_experiment
from .plotting import plot_convergence
from .results import ExperimentResult
from .vqe import VQEError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quantum-vqe",
        description=(
            "Reproducible variational quantum eigensolver experiments for quantum chemistry. "
            "The primary experiment is H2 in the STO-3G basis."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_h2 = subparsers.add_parser(
        "run-h2",
        help="run the H2/STO-3G VQE experiment",
        description=(
            "Generate H2 integrals with PySCF, map the electronic Hamiltonian to qubits, "
            "optimize a UCCSD ansatz with a local statevector simulator, and compare with "
            "exact diagonalization and an independent PySCF FCI reference."
        ),
    )
    run_h2.add_argument(
        "--distance",
        type=float,
        default=0.735,
        metavar="ANGSTROM",
        help="H-H bond length in Angstrom (default: 0.735)",
    )
    run_h2.add_argument(
        "--basis",
        default="sto3g",
        metavar="NAME",
        help="PySCF basis set name (default: sto3g)",
    )
    run_h2.add_argument(
        "--mapping",
        choices=("parity", "jordan-wigner"),
        default="parity",
        help="fermionic-to-qubit mapping (default: parity)",
    )
    reduction_group = run_h2.add_mutually_exclusive_group()
    reduction_group.add_argument(
        "--reduce",
        dest="two_qubit_reduction",
        action="store_true",
        default=None,
        help="enable parity-mapping two-qubit Z2 reduction (default for parity)",
    )
    reduction_group.add_argument(
        "--no-reduce",
        dest="two_qubit_reduction",
        action="store_false",
        help="disable parity-mapping two-qubit Z2 reduction",
    )
    run_h2.add_argument(
        "--optimizer",
        default="L-BFGS-B",
        metavar="NAME",
        help=f"SciPy optimizer: {', '.join(OPTIMIZERS)} (default: L-BFGS-B)",
    )
    run_h2.add_argument(
        "--max-iterations",
        type=int,
        default=500,
        metavar="N",
        help="maximum optimizer iterations (default: 500)",
    )
    run_h2.add_argument(
        "--tolerance",
        type=float,
        default=None,
        metavar="TOL",
        help="optimizer tolerance; default depends on the optimizer",
    )
    run_h2.add_argument(
        "--init",
        dest="initial_point",
        choices=("hf", "random"),
        default="hf",
        help="initial point: Hartree-Fock (all-zero angles) or seeded random (default: hf)",
    )
    run_h2.add_argument(
        "--seed",
        type=int,
        default=7,
        help="seed for random initial points (default: 7)",
    )
    run_h2.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        metavar="DIR",
        help="directory for the timestamped JSON result (default: results)",
    )
    run_h2.add_argument(
        "--json",
        dest="json_path",
        type=Path,
        default=None,
        metavar="PATH",
        help="explicit JSON output path (overrides --output-dir)",
    )
    run_h2.add_argument(
        "--plot",
        action="store_true",
        help="write a PNG convergence plot next to the JSON result",
    )
    return parser


def _default_json_path(config: ExperimentConfig, output_dir: Path) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ")
    reduction = "_2q" if config.two_qubit_reduction else ""
    filename = (
        f"h2_d{config.distance_angstrom:.3f}A_{config.basis}_"
        f"{config.mapping}{reduction}_{stamp}.json"
    )
    return output_dir / filename


def _format_energy(value: float | None, digits: int = 9) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.{digits}f}"


def _format_error(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{float(value):.3e}"


def _print_header(config: ExperimentConfig, json_path: Path) -> None:
    print("H2 VQE chemistry experiment")
    print("  molecule:       H2")
    print(f"  bond length:    {config.distance_angstrom:.6f} Angstrom")
    print(f"  basis:          {config.basis}")
    print(f"  mapping:        {config.mapping}")
    print(f"  2-qubit reduce: {'yes' if config.two_qubit_reduction else 'no'}")
    print(
        f"  optimizer:      {config.optimizer} "
        f"(max {config.max_iterations} iterations, tolerance {config.tolerance:.3g})"
    )
    print(f"  initial point:  {config.initial_point} (seed {config.seed})")
    print(f"  JSON output:    {json_path}")
    print()


