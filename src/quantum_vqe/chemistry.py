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


@dataclass
class ChemistryData:
    """All scientific objects needed by one VQE experiment."""

    problem: ElectronicStructureProblem
    fermionic_hamiltonian: FermionicOp
    qubit_hamiltonian: SparsePauliOp
    mapper: QubitMapper
    hf_circuit: QuantumCircuit
    ansatz: QuantumCircuit
    nuclear_repulsion_energy: float
    num_spatial_orbitals: int
    num_particles: tuple[int, int]
    num_spin_orbitals: int
    num_qubits: int
    mapping_description: str
    two_qubit_reduction: bool
    chemistry_wall_time_s: float


