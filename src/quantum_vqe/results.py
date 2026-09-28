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


