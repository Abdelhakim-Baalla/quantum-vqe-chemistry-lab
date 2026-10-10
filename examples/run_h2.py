"""Run the H2/STO-3G VQE experiment programmatically.

This is the same pipeline as the CLI, but without argparse handling of the
scientific result. It is useful as a starting point for notebooks and scripts.

Usage:
    python examples/run_h2.py
    python examples/run_h2.py --distance 0.9 --optimizer BFGS
    python examples/run_h2.py --mapping jordan-wigner --output-dir results/jw
"""

from __future__ import annotations

import argparse
from pathlib import Path

from quantum_vqe import ExperimentConfig, run_h2_experiment
from quantum_vqe.plotting import plot_convergence


def _format_energy(value: float | None) -> str:
    return f"{value:.12f} Ha" if value is not None else "n/a"


def _format_error(value: float | None) -> str:
    return f"{value:.3e} Ha" if value is not None else "n/a"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distance", type=float, default=0.735, help="H-H distance in Angstrom")
    parser.add_argument("--basis", default="sto3g", help="PySCF basis set (default: sto3g)")
    parser.add_argument(
        "--mapping",
        choices=("parity", "jordan-wigner"),
        default="parity",
        help="fermion-to-qubit mapping (default: parity)",
    )
    parser.add_argument(
        "--optimizer",
        default="L-BFGS-B",
        help="SciPy optimizer (default: L-BFGS-B)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="directory for the JSON and PNG outputs (default: results)",
    )
    args = parser.parse_args()

    config = ExperimentConfig(
        distance_angstrom=args.distance,
        basis=args.basis,
        mapping=args.mapping,
        optimizer=args.optimizer,
    )
    print(f"Running: {config.summary()}")

    result = run_h2_experiment(config)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"h2_example_d{args.distance:.3f}_{config.mapping}"
    json_path = args.output_dir / f"{stem}.json"
    plot_path = args.output_dir / f"{stem}.png"

    plot_convergence(
        result.optimization["history"],
        plot_path,
        exact_energy=result.energies_hartree["exact_qubit_electronic"],
        hf_energy=result.energies_hartree["hf_electronic"],
        title=f"H2 VQE convergence ({config.basis}, r = {config.distance_angstrom:.3f} A)",
    )
    result.artifacts["json"] = str(json_path)
    result.artifacts["plot"] = str(plot_path)
    result.save(json_path)

    energies = result.energies_hartree
    errors = result.errors_hartree
    print(f"Status:              {result.status.upper()}")
    print(f"Qubits:              {result.molecule['num_qubits']}")
    print(f"VQE total:           {_format_energy(energies['vqe_total'])}")
    print(f"Exact qubit total:   {_format_energy(energies['exact_qubit_total'])}")
    print(f"PySCF FCI total:     {_format_energy(energies['pyscf_fci_total'])}")
    print(f"|VQE - exact|:       {_format_error(errors['absolute_vqe_vs_exact_total'])}")
    print(f"JSON:                {json_path}")
    print(f"Plot:                {plot_path}")
    return 0 if result.status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
