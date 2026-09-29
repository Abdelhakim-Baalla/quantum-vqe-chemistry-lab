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


@dataclass
class ExperimentResult:
    """One complete, reproducible VQE experiment record."""

    experiment: str
    status: str
    created_utc: str
    config: dict[str, Any]
    molecule: dict[str, Any]
    hamiltonian: dict[str, Any]
    ansatz: dict[str, Any]
    optimizer: dict[str, Any]
    simulator: dict[str, Any]
    energies_hartree: dict[str, float | None]
    errors_hartree: dict[str, float | None]
    checks: dict[str, bool | None]
    check_tolerances_hartree: dict[str, float]
    references: dict[str, Any]
    optimization: dict[str, Any]
    timing_seconds: dict[str, float]
    software: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    artifacts: dict[str, str | None] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"unsupported result schema {self.schema_version!r}; expected {SCHEMA_VERSION!r}"
            )
        if self.status not in {"success", "failed"}:
            raise ValueError(f"status must be 'success' or 'failed', got {self.status!r}")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe dictionary (including schema version)."""
        return _json_safe(asdict(self))

    def to_json(self, *, indent: int = 2) -> str:
        """Return pretty-printed JSON."""
        return json.dumps(self.to_dict(), indent=indent, allow_nan=False) + "\n"

    def save(self, path: str | Path) -> Path:
        """Atomically write the result to ``path`` and return the path."""
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(destination.name + ".tmp")
        temporary.write_text(self.to_json(), encoding="utf-8")
        temporary.replace(destination)
        return destination

    @classmethod
    def load(cls, path: str | Path) -> ExperimentResult:
        """Load a result file and validate its schema version."""
        source = Path(path)
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON in {source}: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"result file {source} must contain a JSON object")
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(
                f"unsupported result schema in {source}: {data.get('schema_version')!r}"
            )
        known = {item.name for item in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"unknown result field(s): {', '.join(sorted(unknown))}")
        missing = known - set(data)
        if missing:
            raise ValueError(f"missing result field(s): {', '.join(sorted(missing))}")
        return cls(**data)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> ExperimentResult:
        """Build a result from a mapping with schema/field validation."""
        payload = dict(data)
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"unsupported result schema: {payload.get('schema_version')!r}")
        known = {item.name for item in fields(cls)}
        unknown = set(payload) - known
        if unknown:
            raise ValueError(f"unknown result field(s): {', '.join(sorted(unknown))}")
        missing = known - set(payload)
        if missing:
            raise ValueError(f"missing result field(s): {', '.join(sorted(missing))}")
        return cls(**payload)
