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


def _extract_electronic_hamiltonian(problem: ElectronicStructureProblem) -> FermionicOp:
    """Extract the electronic Hamiltonian from Qiskit Nature's operator bundle.

    Qiskit Nature 0.8 returns ``(electronic_hamiltonian, auxiliary_ops)`` from
    ``second_q_ops()``.  Older/newer releases have used a dictionary, so this
    helper keeps the experiment readable across those layouts.
    """
    operators = problem.second_q_ops()
    if isinstance(operators, tuple):
        candidate = operators[0]
    elif isinstance(operators, dict):
        if "ElectronicEnergy" in operators:
            candidate = operators["ElectronicEnergy"]
        else:
            candidate = next(iter(operators.values()))
    else:
        candidate = operators

    if not isinstance(candidate, FermionicOp):
        raise ChemistryError(
            "Qiskit Nature did not return a FermionicOp as the electronic Hamiltonian; "
            f"got {type(candidate).__name__}"
        )
    return candidate


def build_chemistry(config: ExperimentConfig) -> ChemistryData:
    """Run PySCF, build the electronic problem, map it to qubits, and build UCCSD.

    The pipeline keeps the full minimal-basis orbital space: no frozen-core or
    active-space approximation is applied.  For H2/STO-3G this is two spatial
    orbitals (four spin orbitals), i.e. the exact STO-3G electronic problem.
    """
    started = time.perf_counter()

    try:
        driver = PySCFDriver(
            atom=config.geometry_angstrom,
            unit=DistanceUnit.ANGSTROM,
            basis=config.basis,
            charge=config.charge,
            spin=config.spin,
        )
        problem = driver.run()
    except Exception as exc:  # pragma: no cover - depends on optional binary stack
        raise ChemistryError(
            "Could not generate molecular integrals with PySCF/Qiskit Nature. "
            f"Underlying error: {exc}"
        ) from exc

    num_spatial_orbitals = int(problem.num_spatial_orbitals)
    num_particles = tuple(int(value) for value in problem.num_particles)
    num_spin_orbitals = 2 * num_spatial_orbitals

    if num_spatial_orbitals < 1:
        raise ChemistryError(f"invalid number of spatial orbitals: {num_spatial_orbitals}")
    if len(num_particles) != 2 or sum(num_particles) < 1:
        raise ChemistryError(f"invalid particle-number tuple: {num_particles}")

    try:
        fermionic_hamiltonian = _extract_electronic_hamiltonian(problem)
    except ChemistryError:
        raise
    except Exception as exc:  # pragma: no cover - Qiskit Nature API guard
        raise ChemistryError(f"Could not extract the electronic Hamiltonian: {exc}") from exc

    if config.mapping == "jordan-wigner":
        mapper: QubitMapper = JordanWignerMapper()
    elif config.two_qubit_reduction:
        mapper = ParityMapper(num_particles=num_particles)
    else:
        mapper = ParityMapper()

    try:
        qubit_hamiltonian = mapper.map(fermionic_hamiltonian)
        hf_circuit = HartreeFock(num_spatial_orbitals, num_particles, mapper)
        ansatz = UCCSD(
            num_spatial_orbitals,
            num_particles,
            mapper,
            initial_state=hf_circuit,
        )
    except Exception as exc:  # pragma: no cover - Qiskit Nature API guard
        raise ChemistryError(f"Could not build the mapped Hamiltonian/ansatz: {exc}") from exc

    expected_qubits = config.expected_num_qubits(num_spatial_orbitals)
    if qubit_hamiltonian.num_qubits != expected_qubits:
        raise ChemistryError(
            "qubit-count mismatch after mapping: expected "
            f"{expected_qubits}, got {qubit_hamiltonian.num_qubits}"
        )
    if ansatz.num_qubits != qubit_hamiltonian.num_qubits:
        raise ChemistryError(
            "ansatz/Hamiltonian qubit-count mismatch: "
            f"ansatz={ansatz.num_qubits}, Hamiltonian={qubit_hamiltonian.num_qubits}"
        )
    if ansatz.num_parameters < 1:
        raise ChemistryError("the UCCSD ansatz has no variational parameters")

    nuclear_repulsion = problem.nuclear_repulsion_energy
    if nuclear_repulsion is None:
        raise ChemistryError("the electronic problem has no nuclear repulsion energy")
    nuclear_repulsion = float(nuclear_repulsion)

    if config.mapping == "jordan-wigner":
        description = (
            f"Jordan-Wigner mapping of {num_spin_orbitals} spin orbitals to "
            f"{qubit_hamiltonian.num_qubits} qubits; no symmetry-based qubit reduction was applied."
        )
    elif config.two_qubit_reduction:
        description = (
            f"Parity mapping of {num_spin_orbitals} spin orbitals to {num_spin_orbitals} qubits, "
            "followed by two-qubit Z2 tapering of the particle-number and spin-parity symmetries "
            f"to {qubit_hamiltonian.num_qubits} qubits. The (N_alpha, N_beta) = {num_particles} "
            "sector is fixed by the Hartree-Fock particle numbers."
        )
    else:
        description = (
            f"Parity mapping of {num_spin_orbitals} spin orbitals to "
            f"{qubit_hamiltonian.num_qubits} qubits; the optional two-qubit Z2 reduction was "
            "disabled."
        )

    return ChemistryData(
        problem=problem,
        fermionic_hamiltonian=fermionic_hamiltonian,
        qubit_hamiltonian=qubit_hamiltonian,
        mapper=mapper,
        hf_circuit=hf_circuit,
        ansatz=ansatz,
        nuclear_repulsion_energy=nuclear_repulsion,
        num_spatial_orbitals=num_spatial_orbitals,
        num_particles=num_particles,
        num_spin_orbitals=num_spin_orbitals,
        num_qubits=qubit_hamiltonian.num_qubits,
        mapping_description=description,
        two_qubit_reduction=config.two_qubit_reduction,
        chemistry_wall_time_s=time.perf_counter() - started,
    )
