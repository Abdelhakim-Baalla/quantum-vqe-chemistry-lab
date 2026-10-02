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


