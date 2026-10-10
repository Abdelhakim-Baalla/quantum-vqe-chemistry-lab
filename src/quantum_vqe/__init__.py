"""Quantum VQE Chemistry Lab.

A small, reproducible implementation of the variational quantum eigensolver
(VQE) for molecular hydrogen in the STO-3G basis.
"""

from .config import ExperimentConfig
from .experiment import ExperimentResult, run_h2_experiment

__all__ = ["ExperimentConfig", "ExperimentResult", "run_h2_experiment"]
__version__ = "0.1.0"
