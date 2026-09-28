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


