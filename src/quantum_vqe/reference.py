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


