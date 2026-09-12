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


