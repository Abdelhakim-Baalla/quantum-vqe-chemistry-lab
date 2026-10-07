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


def _print_result(result: ExperimentResult, plot_path: Path | None) -> None:
    energies = result.energies_hartree
    errors = result.errors_hartree
    optimization = result.optimization
    molecule = result.molecule
    hamiltonian = result.hamiltonian
    ansatz = result.ansatz

    print("=" * 78)
    print(" H2 VQE RESULT")
    print("=" * 78)
    print(f"Status:              {result.status.upper()}")
    print(f"Created (UTC):       {result.created_utc}")
    print(
        f"Molecule:            {molecule['name']} at "
        f"{molecule['bond_length_angstrom']:.6f} Angstrom, basis {molecule['basis']}"
    )
    print(
        f"Hamiltonian:         {hamiltonian['mapping']} mapping, "
        f"{hamiltonian['num_qubits']} qubits, {hamiltonian['num_terms']} Pauli terms"
    )
    print(
        f"Ansatz:              {ansatz['name']}, {ansatz['num_parameters']} parameters, "
        f"{ansatz['initial_state']} reference"
    )
    print(f"Simulator:           {result.simulator['name']} ({result.simulator['type']}, no shots)")
    print(
        f"Optimizer:           {optimization['optimizer']} "
        f"(converged: {'yes' if optimization['converged'] else 'no'}, "
        f"nfev: {optimization['nfev']}, nit: {optimization['nit']})"
    )
    if not optimization["converged"]:
        print(f"Optimizer message:   {optimization['message']}")

    print("-" * 78)
    print("Energies (Hartree)")
    print(f"  Nuclear repulsion:                 {_format_energy(energies['nuclear_repulsion'])}")
    print(f"  Hartree-Fock electronic:           {_format_energy(energies['hf_electronic'])}")
    print(
        "  Initial VQE electronic:            "
        f"{_format_energy(optimization['initial_energy_hartree'])}"
    )
    print(f"  VQE electronic:                    {_format_energy(energies['vqe_electronic'])}")
    print(f"  VQE total (electronic + nuclear):  {_format_energy(energies['vqe_total'])}")
    print(
        f"  Exact qubit electronic:            {_format_energy(energies['exact_qubit_electronic'])}"
    )
    print(f"  Exact qubit total:                 {_format_energy(energies['exact_qubit_total'])}")
    print(f"  PySCF FCI total (independent):     {_format_energy(energies['pyscf_fci_total'])}")
    if energies.get("full_jordan_wigner_electronic") is not None:
        print(
            "  Full JW electronic (cross-check):  "
            f"{_format_energy(energies['full_jordan_wigner_electronic'])}"
        )

    print("-" * 78)
    print("Errors (Hartree)")
    print(
        "  |VQE - exact| total:               "
        f"{_format_error(errors['absolute_vqe_vs_exact_total'])}"
    )
    print(
        "  Signed variational gap (VQE-exact):"
        f" {_format_error(errors['signed_variational_gap_electronic'])}"
    )
    print(
        "  |exact - PySCF FCI|:               "
        f"{_format_error(errors['absolute_exact_vs_pyscf_fci_total'])}"
    )
    print(
        "  |Hartree-Fock - PySCF RHF|:        "
        f"{_format_error(errors['absolute_hf_vs_pyscf_rhf_electronic'])}"
    )
    print(
        "  |parity - full JW|:                "
        f"{_format_error(errors['absolute_parity_vs_full_jw_electronic'])}"
    )
    print(
        "  Final UCCSD parameters:            "
        f"{[round(value, 10) for value in optimization['final_parameters']]}"
    )

    print("-" * 78)
    print("Checks")
    for name, value in result.checks.items():
        label = "PASS" if value is True else ("FAIL" if value is False else "N/A ")
        print(f"  [{label}] {name}")
    if result.warnings:
        print("-" * 78)
        print("Warnings")
        for warning in result.warnings:
            print(f"  - {warning}")

    print("-" * 78)
    print(f"JSON result:         {result.artifacts.get('json', 'n/a')}")
    print(f"Convergence plot:    {plot_path if plot_path is not None else 'not requested'}")
    print(f"Wall clock:          {result.timing_seconds['total']:.3f} s")
    print("=" * 78)


