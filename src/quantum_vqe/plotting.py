"""Convergence plots for VQE experiments."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np


def plot_convergence(
    history: Sequence[Any],
    output_path: str | Path,
    *,
    exact_energy: float,
    hf_energy: float | None = None,
    title: str = "H2 VQE convergence",
    xlabel: str = "Energy evaluation",
    ylabel: str = "Electronic energy (Ha)",
) -> Path:
    """Plot energy versus cost-function evaluation and save a PNG.

    ``history`` may contain :class:`quantum_vqe.vqe.EnergyEvaluation` objects
    or dictionaries with ``evaluation`` and ``energy_hartree`` keys.
    """
    if not history:
        raise ValueError("cannot plot an empty optimization history")

    evaluations: list[int] = []
    energies: list[float] = []
    for index, item in enumerate(history):
        if isinstance(item, dict):
            evaluations.append(int(item.get("evaluation", index)))
            energies.append(float(item["energy_hartree"]))
        else:
            evaluations.append(int(item.evaluation))
            energies.append(float(item.energy))

    # Import matplotlib lazily so the core numerical modules do not depend on
    # a display backend.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=150)
    best_so_far = np.minimum.accumulate(np.asarray(energies, dtype=float))
    ax.plot(
        evaluations,
        energies,
        color="#9fb7cc",
        linewidth=0.9,
        marker="o",
        markersize=2.2,
        alpha=0.8,
        label="Cost-function evaluations",
    )
    ax.step(
        evaluations,
        best_so_far,
        where="post",
        color="#1f5f99",
        linewidth=1.8,
        label="Best energy so far",
    )
    ax.axhline(
        exact_energy,
        color="#b23a48",
        linestyle="--",
        linewidth=1.4,
        label=f"Exact (same Hamiltonian): {exact_energy:.9f} Ha",
    )
    if hf_energy is not None:
        ax.axhline(
            hf_energy,
            color="#6b6b6b",
            linestyle=":",
            linewidth=1.2,
            label=f"Hartree-Fock: {hf_energy:.9f} Ha",
        )

    best_error = abs(float(best_so_far[-1]) - exact_energy)
    error_label = (
        "best |error| < 1e-15 Ha" if best_error < 1e-15 else f"best |error| = {best_error:.2e} Ha"
    )
    ax.annotate(
        error_label,
        xy=(evaluations[-1], float(best_so_far[-1])),
        xytext=(0.98, 0.62),
        textcoords="axes fraction",
        ha="right",
        fontsize=8.5,
        color="#333333",
    )
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8.5, loc="best")
    ax.margins(y=0.08)
    fig.tight_layout()
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    return output
