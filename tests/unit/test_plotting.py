"""Unit tests for plotting without running the chemistry pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantum_vqe.plotting import plot_convergence


def test_plot_convergence_writes_png(tmp_path: Path) -> None:
    history = [
        {"evaluation": 0, "energy_hartree": -1.0},
        {"evaluation": 1, "energy_hartree": -1.1},
        {"evaluation": 2, "energy_hartree": -1.2},
    ]
    output = plot_convergence(
        history,
        tmp_path / "plots" / "convergence.png",
        exact_energy=-1.2,
        hf_energy=-1.0,
        title="unit test",
    )
    assert output.exists()
    assert output.stat().st_size > 100
    assert output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_plot_rejects_empty_history(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="empty"):
        plot_convergence([], tmp_path / "empty.png", exact_energy=-1.0)
