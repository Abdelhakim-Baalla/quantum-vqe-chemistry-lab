"""Independent classical reference calculations.

Two references are used:

1. Exact diagonalization of the *same* qubit Hamiltonian (same mapping and
   symmetry reduction as the VQE).  This is the primary reference for the
   variational comparison.
2. A direct PySCF Hartree-Fock + full configuration interaction (FCI)
   calculation that does not use Qiskit Nature or the qubit mapping.  This
   cross-checks the molecular integrals and the mapped Hamiltonian.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from qiskit_nature.second_q.mappers import JordanWignerMapper
from qiskit_nature.second_q.operators import FermionicOp

from .config import ExperimentConfig
from .hamiltonian import ExactDiagonalization, exact_ground_state


class ReferenceError(RuntimeError):
    """Raised when an independent reference cannot be computed."""


@dataclass
class FCIReference:
    """PySCF RHF + FCI reference, including electronic and total energies."""

    available: bool
    total_energy: float | None = None
    electronic_energy: float | None = None
    nuclear_repulsion_energy: float | None = None
    rhf_total_energy: float | None = None
    rhf_electronic_energy: float | None = None
    converged: bool | None = None
    method: str = "PySCF RHF + FCI"
    error: str | None = None
    wall_time_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "total_energy": self.total_energy,
            "electronic_energy": self.electronic_energy,
            "nuclear_repulsion_energy": self.nuclear_repulsion_energy,
            "rhf_total_energy": self.rhf_total_energy,
            "rhf_electronic_energy": self.rhf_electronic_energy,
            "converged": self.converged,
            "method": self.method,
            "error": self.error,
            "wall_time_s": self.wall_time_s,
        }


def compute_pyscf_fci(config: ExperimentConfig) -> FCIReference:
    """Compute a direct PySCF RHF + FCI total energy.

    This deliberately bypasses Qiskit Nature: it builds a new PySCF molecule
    from the same geometry and basis, runs Hartree-Fock, and diagonalizes the
    full CI problem.  For H2/STO-3G this is the exact basis-set ground state.
    """
    started = time.perf_counter()
    try:
        from pyscf import fci, gto, scf
    except ImportError as exc:  # pragma: no cover - shown only without PySCF
        return FCIReference(
            available=False,
            method="PySCF RHF + FCI",
            error=f"PySCF is not installed: {exc}",
            wall_time_s=time.perf_counter() - started,
        )

    try:
        mol = gto.M(
            atom=config.geometry_angstrom,
            basis=config.basis,
            unit="Angstrom",
            charge=config.charge,
            spin=config.spin,
            verbose=0,
        )
        scf_class = scf.RHF if config.spin == 0 else scf.ROHF
        mean_field = scf_class(mol)
        mean_field.conv_tol = 1e-10
        mean_field.max_cycle = 200
        mean_field.kernel()
        converged = bool(mean_field.converged)
        if not converged:
            return FCIReference(
                available=False,
                converged=False,
                method=f"PySCF {scf_class.__name__} + FCI",
                error="PySCF Hartree-Fock did not converge",
                wall_time_s=time.perf_counter() - started,
            )

        nuclear = float(mol.energy_nuc())
        cisolver = fci.FCI(mean_field)
        fci_total, _ = cisolver.kernel()
        fci_total = float(fci_total)

        return FCIReference(
            available=True,
            total_energy=fci_total,
            electronic_energy=fci_total - nuclear,
            nuclear_repulsion_energy=nuclear,
            rhf_total_energy=float(mean_field.e_tot),
            rhf_electronic_energy=float(mean_field.e_tot) - nuclear,
            converged=converged,
            method=f"PySCF {scf_class.__name__} + FCI",
            wall_time_s=time.perf_counter() - started,
        )
    except Exception as exc:  # pragma: no cover - depends on PySCF internals
        return FCIReference(
            available=False,
            method="PySCF RHF + FCI",
            error=f"PySCF FCI reference failed: {exc}",
            wall_time_s=time.perf_counter() - started,
        )


