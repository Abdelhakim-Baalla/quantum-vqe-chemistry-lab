"""A transparent VQE loop built on Qiskit's exact statevector estimator.

The loop is deliberately implemented here rather than hidden behind a solver
class.  That makes the cost function, optimizer history, convergence flag and
energy evaluations explicit and easy to test.
"""

from __future__ import annotations

import math
import time
import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp
from scipy.optimize import minimize
from scipy.sparse import SparseEfficiencyWarning

from .config import DEFAULT_TOLERANCES, normalize_optimizer


class VQEError(RuntimeError):
    """Raised when the VQE loop cannot evaluate or optimize the ansatz."""


@dataclass(frozen=True)
class EnergyEvaluation:
    """One call to the VQE cost function."""

    evaluation: int
    energy: float
    parameters: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation": self.evaluation,
            "energy_hartree": self.energy,
            "parameters": list(self.parameters),
        }


@dataclass
class VQEResult:
    """Outcome of one VQE optimization."""

    energy: float
    initial_energy: float
    parameters: tuple[float, ...]
    initial_parameters: tuple[float, ...]
    converged: bool
    success: bool
    message: str
    status_code: int
    nfev: int
    nit: int | None
    njev: int | None
    history: list[EnergyEvaluation]
    wall_time_s: float
    optimizer: str
    tolerance: float
    max_iterations: int

    @property
    def energy_evaluations(self) -> int:
        """Number of recorded cost-function evaluations."""
        return len(self.history)

    def to_dict(self) -> dict[str, Any]:
        return {
            "optimizer": self.optimizer,
            "tolerance": self.tolerance,
            "max_iterations": self.max_iterations,
            "initial_energy_hartree": self.initial_energy,
            "final_energy_hartree": self.energy,
            "initial_parameters": list(self.initial_parameters),
            "final_parameters": list(self.parameters),
            "converged": self.converged,
            "success": self.success,
            "message": self.message,
            "status_code": self.status_code,
            "nfev": self.nfev,
            "nit": self.nit,
            "njev": self.njev,
            "energy_evaluations": self.energy_evaluations,
            "history": [evaluation.to_dict() for evaluation in self.history],
            "wall_time_s": self.wall_time_s,
        }


def make_initial_point(mode: str, num_parameters: int, seed: int) -> np.ndarray:
    """Return a deterministic initial point.

    ``"hf"`` starts at all-zero UCCSD angles, which prepares the Hartree-Fock
    reference state.  ``"random"`` samples small angles uniformly from
    ``[-0.05, 0.05]`` using the supplied seed.
    """
    if num_parameters < 1:
        raise ValueError("num_parameters must be >= 1")
    normalized = str(mode).strip().lower()
    if normalized == "hf":
        return np.zeros(num_parameters, dtype=float)
    if normalized == "random":
        if seed < 0:
            raise ValueError("seed must be non-negative")
        rng = np.random.default_rng(seed)
        return rng.uniform(-0.05, 0.05, size=num_parameters)
    raise ValueError(f"initial point mode must be 'hf' or 'random', got {mode!r}")


class VQE:
    """Minimize ``<psi(theta)|H|psi(theta)>`` with a Qiskit estimator."""

    def __init__(
        self,
        estimator: StatevectorEstimator,
        ansatz: QuantumCircuit,
        hamiltonian: SparsePauliOp,
        *,
        optimizer: str = "L-BFGS-B",
        max_iterations: int = 500,
        tolerance: float | None = None,
    ) -> None:
        if ansatz.num_qubits != hamiltonian.num_qubits:
            raise ValueError(
                "ansatz/Hamiltonian qubit mismatch: "
                f"{ansatz.num_qubits} != {hamiltonian.num_qubits}"
            )
        if ansatz.num_parameters < 1:
            raise ValueError("ansatz must have at least one variational parameter")
        if max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")

        optimizer = normalize_optimizer(optimizer)
        if tolerance is None:
            tolerance = DEFAULT_TOLERANCES[optimizer]
        if not math.isfinite(float(tolerance)) or tolerance <= 0:
            raise ValueError("tolerance must be finite and > 0")

        self.estimator = estimator
        self.ansatz = ansatz
        self.hamiltonian = hamiltonian
        self.optimizer = optimizer
        self.max_iterations = int(max_iterations)
        self.tolerance = float(tolerance)
        self.history: list[EnergyEvaluation] = []

    @property
    def num_parameters(self) -> int:
        return self.ansatz.num_parameters

    def evaluate(self, parameters: Sequence[float], *, record: bool = False) -> float:
        """Evaluate the Hamiltonian expectation value in Hartree."""
        values = np.asarray(parameters, dtype=float).reshape(-1)
        if values.size != self.num_parameters:
            raise ValueError(f"expected {self.num_parameters} parameter values, got {values.size}")
        if not np.all(np.isfinite(values)):
            raise ValueError("parameter values must be finite")

        try:
            # Qiskit's PauliEvolutionGate builds its matrix with
            # scipy.sparse.linalg.expm, which emits a harmless CSC-format
            # efficiency warning.  Suppress only that warning around the
            # primitive call.
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=SparseEfficiencyWarning)
                job = self.estimator.run([(self.ansatz, self.hamiltonian, values)])
                result = job.result()
            energies = np.asarray(result[0].data.evs).reshape(-1)
        except Exception as exc:
            raise VQEError(f"estimator evaluation failed: {exc}") from exc

        if energies.size != 1:
            raise VQEError(f"expected one expectation value, got {energies.size}")
        energy = float(np.real(energies[0]))
        if not math.isfinite(energy):
            raise VQEError(f"estimator returned a non-finite energy: {energy!r}")

        if record:
            self.history.append(
                EnergyEvaluation(
                    evaluation=len(self.history),
                    energy=energy,
                    parameters=tuple(float(value) for value in values),
                )
            )
        return energy

    def _objective(self, parameters: np.ndarray) -> float:
        return self.evaluate(parameters, record=True)

    def _scipy_options(self) -> dict[str, Any]:
        options: dict[str, Any] = {
            "maxiter": self.max_iterations,
        }
        if self.optimizer in {"BFGS", "L-BFGS-B"}:
            options["gtol"] = self.tolerance
        elif self.optimizer == "SLSQP":
            options["ftol"] = self.tolerance
        elif self.optimizer == "COBYLA":
            options["tol"] = self.tolerance
        elif self.optimizer == "Nelder-Mead":
            options["xatol"] = self.tolerance
            options["fatol"] = self.tolerance
            options["adaptive"] = True
        return options

    def minimize(self, initial_point: Sequence[float] | None = None) -> VQEResult:
        """Run the optimizer and return a fully populated result."""
        if initial_point is None:
            x0 = np.zeros(self.num_parameters, dtype=float)
        else:
            x0 = np.asarray(initial_point, dtype=float).reshape(-1)
        if x0.size != self.num_parameters:
            raise ValueError(f"expected {self.num_parameters} initial parameters, got {x0.size}")
        if not np.all(np.isfinite(x0)):
            raise ValueError("initial parameters must be finite")

        self.history = []
        started = time.perf_counter()
        try:
            result = minimize(
                self._objective,
                x0,
                method=self.optimizer,
                options=self._scipy_options(),
            )
        except Exception as exc:
            raise VQEError(f"optimizer '{self.optimizer}' failed: {exc}") from exc
        wall_time = time.perf_counter() - started

        energy = float(result.fun)
        if not math.isfinite(energy):
            raise VQEError(f"optimizer returned a non-finite energy: {energy!r}")
        parameters = np.asarray(result.x, dtype=float).reshape(-1)
        if parameters.size != self.num_parameters:
            raise VQEError(
                f"optimizer returned {parameters.size} parameters, expected {self.num_parameters}"
            )
        if not np.all(np.isfinite(parameters)):
            raise VQEError("optimizer returned non-finite parameters")

        # SciPy evaluates x0 before iterating; fall back defensively if it did not.
        initial_energy = self.history[0].energy if self.history else self.evaluate(x0)

        converged = bool(result.success)
        return VQEResult(
            energy=energy,
            initial_energy=initial_energy,
            parameters=tuple(float(value) for value in parameters),
            initial_parameters=tuple(float(value) for value in x0),
            converged=converged,
            success=converged,
            message=str(result.message),
            status_code=int(getattr(result, "status", -1)),
            nfev=int(result.nfev),
            nit=getattr(result, "nit", None),
            njev=getattr(result, "njev", None),
            history=list(self.history),
            wall_time_s=wall_time,
            optimizer=self.optimizer,
            tolerance=self.tolerance,
            max_iterations=self.max_iterations,
        )
