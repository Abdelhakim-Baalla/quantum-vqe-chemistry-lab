"""Software version collection for reproducible result files."""

from __future__ import annotations

import platform
import sys
from importlib.metadata import PackageNotFoundError, version


def _version(package: str) -> str | None:
    try:
        return version(package)
    except PackageNotFoundError:
        return None


def collect_versions() -> dict[str, str | None]:
    """Return versions of the scientific stack used by an experiment."""
    return {
        "python": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "quantum-vqe-chemistry-lab": _version("quantum-vqe-chemistry-lab"),
        "qiskit": _version("qiskit"),
        "qiskit-nature": _version("qiskit-nature"),
        "qiskit-algorithms": _version("qiskit-algorithms"),
        "pyscf": _version("pyscf"),
        "numpy": _version("numpy"),
        "scipy": _version("scipy"),
        "matplotlib": _version("matplotlib"),
        "python_executable": sys.executable,
    }
