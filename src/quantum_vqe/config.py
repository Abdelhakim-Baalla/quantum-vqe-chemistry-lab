"""Configuration objects for the H2 VQE experiment.

The configuration is deliberately small and serializable.  It is the single
source of truth for CLI runs, programmatic runs and JSON result files.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields
from typing import Any

MAPPINGS = ("parity", "jordan-wigner")
OPTIMIZERS = ("BFGS", "L-BFGS-B", "SLSQP", "COBYLA", "Nelder-Mead")
INITIAL_POINT_MODES = ("hf", "random")

# A tolerance that is achievable by each SciPy optimizer for this small
# problem.  BFGS's finite-difference gradient can stall at 1e-8 because of
# floating-point noise, so its practical default is looser.  The resolved
# value is always written to the result JSON.
DEFAULT_TOLERANCES: dict[str, float] = {
    "BFGS": 1e-6,
    "L-BFGS-B": 1e-8,
    "SLSQP": 1e-8,
    "COBYLA": 1e-8,
    "Nelder-Mead": 1e-8,
}

_OPTIMIZER_ALIASES = {
    "bfgs": "BFGS",
    "l-bfgs-b": "L-BFGS-B",
    "l_bfgs_b": "L-BFGS-B",
    "lbfgsb": "L-BFGS-B",
    "slsqp": "SLSQP",
    "cobyla": "COBYLA",
    "nelder-mead": "Nelder-Mead",
    "nelder_mead": "Nelder-Mead",
    "neldermead": "Nelder-Mead",
}


def normalize_mapping(value: str) -> str:
    """Return the canonical mapping name or raise ``ValueError``."""
    normalized = str(value).strip().lower().replace("_", "-")
    if normalized in {"jw", "jordanwigner"}:
        normalized = "jordan-wigner"
    if normalized not in MAPPINGS:
        raise ValueError(f"mapping must be one of {MAPPINGS}, got {value!r}")
    return normalized


def normalize_optimizer(value: str) -> str:
    """Return the canonical SciPy optimizer name or raise ``ValueError``."""
    normalized = str(value).strip().lower()
    if normalized not in _OPTIMIZER_ALIASES:
        raise ValueError(f"optimizer must be one of {OPTIMIZERS}, got {value!r}")
    return _OPTIMIZER_ALIASES[normalized]


def _positive_finite(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number, got {value!r}")
    value = float(value)
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0, got {value!r}")
    return value


@dataclass(frozen=True)
class ExperimentConfig:
    """Configuration for one H2/STO-3G VQE experiment.

    Args:
        distance_angstrom: H-H bond length in Angstrom.
        basis: PySCF basis set name.  ``"sto3g"`` is the validated default.
        charge: Molecular charge.
        spin: PySCF spin convention ``2S``.  H2 uses ``0``.
        mapping: Fermionic-to-qubit mapping, ``"parity"`` or ``"jordan-wigner"``.
        two_qubit_reduction: For parity mapping, remove two qubits using the
            particle-number and spin-parity Z2 symmetries.  ``None`` resolves
            to ``True`` for parity mapping and ``False`` for Jordan-Wigner.
        optimizer: SciPy optimizer name.
        max_iterations: Maximum optimizer iterations.
        tolerance: Optimizer tolerance.  ``None`` selects an optimizer-specific
            default from :data:`DEFAULT_TOLERANCES`.
        initial_point: ``"hf"`` (all-zero UCCSD angles) or ``"random"``.
        seed: Seed used only for the ``"random"`` initial point.
        energy_accuracy_target: Target absolute error in Hartree.
        variational_tolerance: Numerical tolerance for the variational-principle
            check.  Exact statevector arithmetic can undershoot the exact
            eigenvalue by a few 1e-15 Ha.
        reference_tolerance: Tolerance for independent-reference cross-checks.
    """

    distance_angstrom: float = 0.735
    basis: str = "sto3g"
    charge: int = 0
    spin: int = 0
    mapping: str = "parity"
    two_qubit_reduction: bool | None = None
    optimizer: str = "L-BFGS-B"
    max_iterations: int = 500
    tolerance: float | None = None
    initial_point: str = "hf"
    seed: int = 7
    energy_accuracy_target: float = 1e-6
    variational_tolerance: float = 1e-8
    reference_tolerance: float = 1e-6

    def __post_init__(self) -> None:
        distance = _positive_finite("distance_angstrom", self.distance_angstrom)
        object.__setattr__(self, "distance_angstrom", distance)

        basis = str(self.basis).strip().lower()
        if not basis:
            raise ValueError("basis must be a non-empty PySCF basis name")
        object.__setattr__(self, "basis", basis)

        if isinstance(self.charge, bool) or not isinstance(self.charge, int):
            raise ValueError(f"charge must be an integer, got {self.charge!r}")
        if isinstance(self.spin, bool) or not isinstance(self.spin, int):
            raise ValueError(f"spin must be an integer (2S), got {self.spin!r}")
        if self.spin < 0 or self.spin % 2:
            raise ValueError(f"spin must be a non-negative even integer (2S), got {self.spin!r}")

        mapping = normalize_mapping(self.mapping)
        object.__setattr__(self, "mapping", mapping)

        reduction = self.two_qubit_reduction
        if reduction is None:
            reduction = mapping == "parity"
        if not isinstance(reduction, bool):
            raise ValueError("two_qubit_reduction must be a bool or None")
        if mapping == "jordan-wigner" and reduction:
            raise ValueError(
                "two-qubit Z2 reduction is only implemented for parity mapping; "
                "use two_qubit_reduction=False with Jordan-Wigner"
            )
        object.__setattr__(self, "two_qubit_reduction", reduction)

        optimizer = normalize_optimizer(self.optimizer)
        object.__setattr__(self, "optimizer", optimizer)

        if (
            isinstance(self.max_iterations, bool)
            or not isinstance(self.max_iterations, int)
            or self.max_iterations < 1
        ):
            raise ValueError(f"max_iterations must be an integer >= 1, got {self.max_iterations!r}")
        if self.max_iterations > 100_000:
            raise ValueError("max_iterations above 100000 is not supported")

        tolerance = self.tolerance
        if tolerance is None:
            tolerance = DEFAULT_TOLERANCES[optimizer]
        tolerance = _positive_finite("tolerance", tolerance)
        object.__setattr__(self, "tolerance", tolerance)

        initial_point = str(self.initial_point).strip().lower()
        if initial_point not in INITIAL_POINT_MODES:
            raise ValueError(
                f"initial_point must be one of {INITIAL_POINT_MODES}, got {self.initial_point!r}"
            )
        object.__setattr__(self, "initial_point", initial_point)

        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError(f"seed must be a non-negative integer, got {self.seed!r}")

        object.__setattr__(
            self,
            "energy_accuracy_target",
            _positive_finite("energy_accuracy_target", self.energy_accuracy_target),
        )
        object.__setattr__(
            self,
            "variational_tolerance",
            _positive_finite("variational_tolerance", self.variational_tolerance),
        )
        object.__setattr__(
            self,
            "reference_tolerance",
            _positive_finite("reference_tolerance", self.reference_tolerance),
        )

    @property
    def geometry_angstrom(self) -> str:
        """PySCF geometry string for H2 at ``distance_angstrom``."""
        return f"H 0.0 0.0 0.0; H 0.0 0.0 {self.distance_angstrom:.12f}"

    def expected_num_qubits(self, num_spatial_orbitals: int) -> int:
        """Expected qubit count after the configured mapping and reduction."""
        removed = 2 if self.two_qubit_reduction else 0
        return 2 * num_spatial_orbitals - removed

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary of the resolved configuration."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ExperimentConfig:
        """Build a configuration from a mapping, rejecting unknown fields."""
        known = {field.name for field in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"unknown configuration field(s): {', '.join(sorted(unknown))}")
        return cls(**dict(data))

    def summary(self) -> str:
        """One-line human-readable summary used by the CLI."""
        reduction = "2-qubit Z2 reduction" if self.two_qubit_reduction else "no qubit reduction"
        return (
            f"H2 at {self.distance_angstrom:.6f} A, basis {self.basis}, "
            f"{self.mapping} mapping ({reduction}), {self.optimizer}"
        )
