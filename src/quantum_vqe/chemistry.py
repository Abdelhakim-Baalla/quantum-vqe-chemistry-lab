"""Molecular chemistry and qubit-Hamiltonian construction.

This module is the boundary between classical quantum chemistry (PySCF through
Qiskit Nature) and the rest of the VQE implementation.  It returns the
fermionic electronic Hamiltonian, the qubit Hamiltonian, the Hartree-Fock
reference state and the UCCSD ansatz.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit_nature.second_q.circuit.library import UCCSD, HartreeFock
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.mappers import JordanWignerMapper, ParityMapper, QubitMapper
from qiskit_nature.second_q.operators import FermionicOp
from qiskit_nature.second_q.problems import ElectronicStructureProblem
from qiskit_nature.units import DistanceUnit

from .config import ExperimentConfig


class ChemistryError(RuntimeError):
    """Raised when molecular integrals or the qubit Hamiltonian cannot be built."""


