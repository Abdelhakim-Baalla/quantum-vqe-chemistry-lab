"""Operator inspection, exact diagonalization, and energy-error helpers."""

from __future__ import annotations

import math
import time
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp, Statevector


class OperatorError(ValueError):
    """Raised for invalid operator or energy inputs."""


