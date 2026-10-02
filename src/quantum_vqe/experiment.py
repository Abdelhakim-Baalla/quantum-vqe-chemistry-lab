"""End-to-end H2 VQE experiment orchestration."""

from __future__ import annotations

import time
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import numpy as np
from qiskit.primitives import StatevectorEstimator

from .chemistry import ChemistryData, ChemistryError, build_chemistry
from .config import ExperimentConfig
from .hamiltonian import (
    check_hermitian,
    compare_energies,
    exact_ground_state,
    pauli_term_records,
)
from .reference import (
    FCIReference,
    ReferenceError,
    compute_pyscf_fci,
    full_jordan_wigner_reference,
)
from .results import ExperimentResult
from .versions import collect_versions
from .vqe import VQE, VQEResult, make_initial_point


class ExperimentError(RuntimeError):
    """Raised when the experiment cannot produce a trustworthy result."""


def determine_status(checks: Mapping[str, bool | None]) -> str:
    """Return ``"success"`` only if no performed check failed.

    ``None`` denotes a check that is not applicable (for example, the parity
    versus full-JW cross-check in a Jordan-Wigner run); it does not indicate a
    failure and does not count as a pass.
    """
    return "failed" if any(value is False for value in checks.values()) else "success"


def _make_checks(
    *,
    chemistry: ChemistryData,
    config: ExperimentConfig,
    vqe_result: VQEResult,
    hf_electronic: float,
    comparison_absolute_error: float,
    comparison_signed_gap: float,
    fci: FCIReference,
    hf_vs_fci_error: float | None,
    exact_vs_fci_error: float | None,
    jw_vs_parity_error: float | None,
    parity_crosscheck_applicable: bool,
) -> dict[str, bool | None]:
    reference_tolerance = config.reference_tolerance
    checks: dict[str, bool | None] = {
        "hamiltonian_is_hermitian": True,
        "ansatz_qubit_count_matches_hamiltonian": (
            chemistry.ansatz.num_qubits == chemistry.qubit_hamiltonian.num_qubits
        ),
        "mapped_qubit_count_matches_configuration": (
            chemistry.qubit_hamiltonian.num_qubits
            == config.expected_num_qubits(chemistry.num_spatial_orbitals)
        ),
        "optimizer_converged": vqe_result.converged,
        "optimizer_reduced_energy": (
            vqe_result.energy <= hf_electronic + config.energy_accuracy_target
        ),
        "variational_principle": (comparison_signed_gap >= -config.variational_tolerance),
        "energy_accuracy_target_met": (comparison_absolute_error <= config.energy_accuracy_target),
        "hf_matches_pyscf_rhf": (
            hf_vs_fci_error is not None and hf_vs_fci_error <= reference_tolerance
        ),
        "exact_matches_pyscf_fci": (
            exact_vs_fci_error is not None and exact_vs_fci_error <= reference_tolerance
        ),
    }
    if not fci.available:
        # An unavailable independent reference cannot validate the experiment.
        checks["exact_matches_pyscf_fci"] = False
        checks["hf_matches_pyscf_rhf"] = False

    if parity_crosscheck_applicable:
        checks["parity_reduction_matches_full_jw"] = (
            jw_vs_parity_error is not None and jw_vs_parity_error <= reference_tolerance
        )
    else:
        checks["parity_reduction_matches_full_jw"] = None
    return checks


def run_h2_experiment(
    config: ExperimentConfig | None = None,
    *,
    estimator: StatevectorEstimator | None = None,
    chemistry: ChemistryData | None = None,
) -> ExperimentResult:
    """Run the complete H2/STO-3G VQE experiment and return a result record.

    Args:
        config: Validated experiment configuration.
        estimator: Optional estimator override, primarily for testing.
        chemistry: Optional pre-built chemistry object. Callers that already
            built the identical problem (for example the web interface, which
            also renders the ansatz circuit) can pass it to avoid rebuilding
            PySCF integrals and the ansatz. It must match ``config``.

    Steps:
    1. PySCF integrals via Qiskit Nature.
    2. Fermionic electronic Hamiltonian and parity/Jordan-Wigner mapping.
    3. UCCSD ansatz with a Hartree-Fock reference.
    4. Exact statevector VQE with a SciPy optimizer.
    5. Exact diagonalization of the same qubit Hamiltonian.
    6. Independent PySCF FCI and full Jordan-Wigner cross-checks.
    7. Scientific consistency checks and a serializable result.
    """
    if config is None:
        config = ExperimentConfig()
    if not isinstance(config, ExperimentConfig):
        raise TypeError("config must be an ExperimentConfig")
    if chemistry is not None and not isinstance(chemistry, ChemistryData):
        raise TypeError("chemistry must be a ChemistryData instance or None")

    total_started = time.perf_counter()

    if chemistry is None:
        try:
            chemistry = build_chemistry(config)
        except ChemistryError:
            raise
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise ExperimentError(f"chemistry pipeline failed: {exc}") from exc

    hermiticity = check_hermitian(chemistry.qubit_hamiltonian)
    if not hermiticity.hermitian:
        raise ExperimentError(
            "the mapped qubit Hamiltonian is not Hermitian within tolerance: "
            f"max asymmetry {hermiticity.max_asymmetry:.3e}"
        )

    exact = exact_ground_state(chemistry.qubit_hamiltonian)
    fci = compute_pyscf_fci(config)

    parity_crosscheck_applicable = config.mapping == "parity"
    jw_reference = None
    jw_error: str | None = None
    if parity_crosscheck_applicable:
        try:
            jw_reference = full_jordan_wigner_reference(chemistry.fermionic_hamiltonian)
        except ReferenceError as exc:
            jw_error = str(exc)

    if estimator is None:
        estimator = StatevectorEstimator()

    vqe = VQE(
        estimator,
        chemistry.ansatz,
        chemistry.qubit_hamiltonian,
        optimizer=config.optimizer,
        max_iterations=config.max_iterations,
        tolerance=config.tolerance,
    )

    zero_point = np.zeros(vqe.num_parameters, dtype=float)
    hf_electronic = vqe.evaluate(zero_point)
    initial_point = make_initial_point(config.initial_point, vqe.num_parameters, config.seed)
    vqe_result = vqe.minimize(initial_point)

    nuclear = float(chemistry.nuclear_repulsion_energy)
    vqe_electronic = float(vqe_result.energy)
    exact_electronic = float(exact.ground_energy)
    vqe_total = vqe_electronic + nuclear
    exact_total = exact_electronic + nuclear
    hf_total = hf_electronic + nuclear

    comparison = compare_energies(vqe_total, exact_total)
    electronic_comparison = compare_energies(vqe_electronic, exact_electronic)

    hf_vs_fci_error = None
    exact_vs_fci_error = None
    if fci.available and fci.rhf_electronic_energy is not None:
        hf_vs_fci_error = abs(hf_electronic - fci.rhf_electronic_energy)
    if fci.available and fci.total_energy is not None:
        exact_vs_fci_error = abs(exact_total - fci.total_energy)

    jw_vs_parity_error = None
    if jw_reference is not None:
        jw_vs_parity_error = abs(exact_electronic - jw_reference.ground_energy)

    checks = _make_checks(
        chemistry=chemistry,
        config=config,
        vqe_result=vqe_result,
        hf_electronic=hf_electronic,
        comparison_absolute_error=comparison.absolute_error,
        comparison_signed_gap=comparison.signed_gap,
        fci=fci,
        hf_vs_fci_error=hf_vs_fci_error,
        exact_vs_fci_error=exact_vs_fci_error,
        jw_vs_parity_error=jw_vs_parity_error,
        parity_crosscheck_applicable=parity_crosscheck_applicable,
    )
    failed_checks = [name for name, value in checks.items() if value is False]
    status = determine_status(checks)

    warnings: list[str] = []
    if not fci.available:
        warnings.append(
            f"Independent PySCF FCI reference unavailable; validation is incomplete: {fci.error}"
        )
    if parity_crosscheck_applicable and jw_reference is None:
        warnings.append(
            "Full Jordan-Wigner mapping cross-check unavailable; validation is incomplete: "
            f"{jw_error}"
        )
    if config.mapping == "jordan-wigner":
        warnings.append(
            "Jordan-Wigner mapping selected; the parity-reduction versus full-JW "
            "cross-check is not applicable."
        )
    if config.mapping == "parity" and not config.two_qubit_reduction:
        warnings.append(
            "Parity two-qubit Z2 reduction disabled for this run; four qubits were simulated."
        )
    if config.initial_point == "random":
        warnings.append(
            f"Random initial point used (seed={config.seed}); the optimizer may find a "
            "different local minimum on other problems."
        )

    if failed_checks:
        warnings.append("Failed checks: " + ", ".join(failed_checks))

    total_wall_time = time.perf_counter() - total_started

    hamiltonian_info: dict[str, Any] = {
        "mapping": config.mapping,
        "two_qubit_reduction": config.two_qubit_reduction,
        "mapping_description": chemistry.mapping_description,
        "num_qubits": chemistry.qubit_hamiltonian.num_qubits,
        "num_terms": len(chemistry.qubit_hamiltonian),
        "pauli_terms": pauli_term_records(chemistry.qubit_hamiltonian),
        "hermiticity": hermiticity.to_dict(),
        "num_spatial_orbitals": chemistry.num_spatial_orbitals,
        "num_spin_orbitals": chemistry.num_spin_orbitals,
        "active_space": "full minimal-basis space; no frozen core or active-space reduction",
        "electronic_only": True,
        "nuclear_repulsion_handled_separately": True,
    }

    ansatz_info: dict[str, Any] = {
        "name": "UCCSD",
        "qubit_mapper": type(chemistry.mapper).__name__,
        "num_qubits": chemistry.ansatz.num_qubits,
        "num_parameters": chemistry.ansatz.num_parameters,
        "parameter_names": [parameter.name for parameter in chemistry.ansatz.parameters],
        "initial_state": "Hartree-Fock",
        "excitation_level": "singles and doubles (SD)",
        "reps": 1,
        "description": (
            "Fermionic unitary coupled-cluster singles and doubles, exponentiated as "
            "exp(T - T^dagger) on the Hartree-Fock reference, then mapped to qubits."
        ),
    }

    references: dict[str, Any] = {
        "same_qubit_hamiltonian": exact.to_dict(),
        "pyscf_fci": fci.to_dict(),
        "full_jordan_wigner": (
            {**jw_reference.to_dict(), "available": True}
            if jw_reference is not None
            else {
                "available": False,
                "applicable": parity_crosscheck_applicable,
                "error": jw_error,
            }
        ),
        "parity_reduction_crosscheck_applicable": parity_crosscheck_applicable,
    }

    optimization = vqe_result.to_dict()
    optimization.update(
        {
            "initial_point_mode": config.initial_point,
            "seed": config.seed,
            "initial_point_is_hartree_fock": config.initial_point == "hf",
        }
    )

    result = ExperimentResult(
        experiment="h2_vqe",
        status=status,
        created_utc=datetime.now(UTC).isoformat(timespec="seconds"),
        config=config.to_dict(),
        molecule={
            "name": "H2",
            "geometry_angstrom": config.geometry_angstrom,
            "bond_length_angstrom": config.distance_angstrom,
            "basis": config.basis,
            "charge": config.charge,
            "spin": config.spin,
            "num_electrons": sum(chemistry.num_particles),
            "num_particles": list(chemistry.num_particles),
            "num_spatial_orbitals": chemistry.num_spatial_orbitals,
            "num_spin_orbitals": chemistry.num_spin_orbitals,
            "num_qubits": chemistry.num_qubits,
            "nuclear_repulsion_energy_hartree": nuclear,
            "units": "Hartree",
        },
        hamiltonian=hamiltonian_info,
        ansatz=ansatz_info,
        optimizer={
            "name": config.optimizer,
            "max_iterations": config.max_iterations,
            "tolerance": config.tolerance,
            "gradient_method": (
                "finite differences supplied by SciPy"
                if config.optimizer in {"BFGS", "L-BFGS-B", "SLSQP"}
                else "derivative-free"
            ),
            "cost_function": "<psi(theta)|H_electronic|psi(theta)>",
        },
        simulator={
            "name": "Qiskit StatevectorEstimator",
            "type": "exact statevector",
            "shots": None,
            "noise_model": None,
            "description": (
                "Noiseless statevector expectation values. No quantum hardware, "
                "shot sampling or noise model is used."
            ),
        },
        energies_hartree={
            "nuclear_repulsion": nuclear,
            "hf_electronic": hf_electronic,
            "hf_total": hf_total,
            "vqe_electronic": vqe_electronic,
            "vqe_total": vqe_total,
            "exact_qubit_electronic": exact_electronic,
            "exact_qubit_total": exact_total,
            "pyscf_fci_electronic": fci.electronic_energy,
            "pyscf_fci_total": fci.total_energy,
            "pyscf_rhf_electronic": fci.rhf_electronic_energy,
            "pyscf_rhf_total": fci.rhf_total_energy,
            "full_jordan_wigner_electronic": (
                jw_reference.ground_energy if jw_reference is not None else None
            ),
        },
        errors_hartree={
            "absolute_vqe_vs_exact_total": comparison.absolute_error,
            "signed_variational_gap_electronic": electronic_comparison.signed_gap,
            "absolute_exact_vs_pyscf_fci_total": exact_vs_fci_error,
            "absolute_hf_vs_pyscf_rhf_electronic": hf_vs_fci_error,
            "absolute_parity_vs_full_jw_electronic": jw_vs_parity_error,
        },
        checks=checks,
        check_tolerances_hartree={
            "energy_accuracy_target": config.energy_accuracy_target,
            "variational_tolerance": config.variational_tolerance,
            "reference_tolerance": config.reference_tolerance,
            "hermiticity_atol": hermiticity.tolerance,
        },
        references=references,
        optimization=optimization,
        timing_seconds={
            "chemistry": chemistry.chemistry_wall_time_s,
            "exact_diagonalization": exact.wall_time_s,
            "pyscf_fci": fci.wall_time_s,
            "full_jordan_wigner": (jw_reference.wall_time_s if jw_reference is not None else 0.0),
            "vqe": vqe_result.wall_time_s,
            "total": total_wall_time,
        },
        software=collect_versions(),
        warnings=warnings,
        artifacts={},
    )
    return result
