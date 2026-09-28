"""Serializable experiment results.

The JSON layout is intentionally explicit: config, molecule, Hamiltonian,
ansatz, optimizer, energies, errors, checks, references, timing and software
versions are all separate top-level sections so results can be compared later.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

import numpy as np

SCHEMA_VERSION = "1.0"


def _json_safe(value: Any) -> Any:
    """Recursively convert NumPy values and reject non-finite floats."""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        value = float(value)
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("result contains a non-finite float; JSON output would be invalid")
        return value
    if isinstance(value, Path):
        return str(value)
    return value


