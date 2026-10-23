import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd

LAUNCH = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get('QUANTUM_LAB_REPO', LAUNCH.parents[1]))
OUT = LAUNCH / 'charts'
OUT.mkdir(parents=True, exist_ok=True)
DATA = ROOT / 'docs/assets/h2_result.json'
if not DATA.exists():
    DATA = LAUNCH / 'source/h2_result.json'
data = json.loads(DATA.read_text())

INK = '#161616'
BODY = '#393939'
MUTED = '#6f6f6f'
BORDER = '#bdbdbd'
GRID = '#e8e8e8'
BLUE = '#0f62fe'
RED = '#da1e28'
AMBER = '#8e6a00'
GRAY = '#8d8d8d'
SURFACE = '#ffffff'

plt.rcParams.update({
    'font.family': 'Noto Sans',
    'font.size': 11,
    'axes.edgecolor': BORDER,
    'axes.labelcolor': BODY,
    'axes.titlecolor': INK,
    'xtick.color': MUTED,
    'ytick.color': MUTED,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.facecolor': SURFACE,
    'axes.facecolor': SURFACE,
    'savefig.facecolor': SURFACE,
    'mathtext.fontset': 'dejavusans',
})

SUP = str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹')

def sci(value: float) -> str:
    exponent = int(np.floor(np.log10(abs(value))))
    mantissa = value / (10 ** exponent)
    return f'{mantissa:.2f} × 10{str(exponent).translate(SUP)}'

hist = pd.DataFrame(data['optimization']['history'])
exact = float(data['energies_hartree']['exact_qubit_electronic'])
hf = float(data['energies_hartree']['hf_electronic'])
best = hist['energy_hartree'].cummin()
error_best = np.maximum(np.abs(best.to_numpy() - exact), 1e-17)

fig = plt.figure(figsize=(13.2, 7.6), dpi=220)
gs = fig.add_gridspec(1, 2, width_ratios=[3.15, 1.0], wspace=0.28)
ax = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])

ax.axvspan(3.5, 7.5, color='#f4f4f2', zorder=0)
line_recorded, = ax.plot(
    hist['evaluation'], hist['energy_hartree'],
    color=GRAY, linewidth=1.25, marker='o', markersize=3.4,
    markerfacecolor=SURFACE, markeredgecolor=GRAY, markeredgewidth=0.8,
    label='Recorded evaluation', zorder=2,
)
line_best, = ax.plot(
    hist['evaluation'], best,
    color=BLUE, linewidth=2.0, marker='o', markersize=3.9,
    markerfacecolor=BLUE, markeredgecolor=BLUE,
    label='Best so far', zorder=3,
)
line_exact = ax.axhline(exact, color=RED, linestyle=(0, (6, 4)), linewidth=1.45,
                        label='Exact diagonalization', zorder=1)
line_hf = ax.axhline(hf, color=AMBER, linestyle=(0, (2, 3)), linewidth=1.55,
                     label='Hartree–Fock', zorder=1)

ax.set_xlim(-0.8, len(hist) - 0.2)
ax.set_ylim(-1.885, -0.78)
ax.set_xlabel('Cost-function evaluation', labelpad=9)
ax.set_ylabel('Electronic energy (Ha)', labelpad=9)
ax.yaxis.set_major_locator(mtick.MultipleLocator(0.2))
ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.1f'))
ax.grid(axis='y', color=GRID, linewidth=0.8)
ax.set_axisbelow(True)

ax.annotate(
    'L-BFGS-B line-search excursion',
    xy=(5.1, -0.875), xytext=(8.9, -0.98),
    fontsize=9.4, color=BODY,
    arrowprops=dict(arrowstyle='-', color=GRAY, lw=0.8, shrinkA=2, shrinkB=3),
)
ax.text(
    0.985, 0.13,
    f'final |error| = {sci(4.440892098500626e-16)} Ha',
    transform=ax.transAxes, ha='right', va='bottom',
    fontsize=10.0, color=BLUE,
    bbox=dict(boxstyle='square,pad=0.52', facecolor=SURFACE, edgecolor='#d9d9d9', linewidth=0.8),
)

ax2.plot(
    hist['evaluation'], error_best,
    color=BLUE, linewidth=1.8, marker='o', markersize=3.3,
    markerfacecolor=BLUE, markeredgecolor=BLUE,
)
ax2.set_yscale('log')
ax2.set_ylim(1e-17, 4e-2)
ax2.set_xlim(-0.8, len(hist) - 0.2)
ax2.set_xlabel('Evaluation', labelpad=9)
ax2.set_title('Best-so-far |error| (Ha)', loc='left', fontsize=11.5, pad=9, color=INK)
ax2.grid(axis='y', color=GRID, linewidth=0.8)
ax2.set_axisbelow(True)
ax2.tick_params(axis='both', labelsize=9.5)
ax2.text(
    0.04, 0.09, f'final {sci(4.440892098500626e-16)} Ha',
    transform=ax2.transAxes, ha='left', va='bottom',
    fontsize=8.9, color=BLUE,
)
ax2.text(
    0.04, 0.02, 'floating-point floor', transform=ax2.transAxes,
    fontsize=8.6, color=MUTED,
)

fig.legend(
    handles=[line_recorded, line_best, line_exact, line_hf],
    labels=['Recorded evaluation', 'Best so far', 'Exact diagonalization', 'Hartree–Fock'],
    loc='upper left', bbox_to_anchor=(0.068, 0.988), ncol=4,
    frameon=False, fontsize=9.1, handlelength=2.4, columnspacing=1.8,
)
fig.subplots_adjust(left=0.075, right=0.985, top=0.875, bottom=0.13)
fig.savefig(OUT / 'convergence.png', dpi=220, facecolor=SURFACE)
plt.close(fig)

# Agreement lollipop chart
comparisons = [
    ('VQE total vs exact diagonalization', data['errors_hartree']['absolute_vqe_vs_exact_total'], BLUE),
    ('HF vs independent PySCF RHF', data['errors_hartree']['absolute_hf_vs_pyscf_rhf_electronic'], GRAY),
    ('Parity + Z₂ vs full Jordan-Wigner', data['errors_hartree']['absolute_parity_vs_full_jw_electronic'], GRAY),
    ('Exact qubit vs PySCF FCI', data['errors_hartree']['absolute_exact_vs_pyscf_fci_total'], GRAY),
]
comparisons = comparisons[::-1]
labels = [item[0] for item in comparisons]
values = [item[1] for item in comparisons]
colors = [item[2] for item in comparisons]
ys = np.arange(len(labels))

fig2, ax3 = plt.subplots(figsize=(12.4, 6.0), dpi=220)
fig2.subplots_adjust(left=0.33, right=0.93, top=0.79, bottom=0.20)
ax3.set_xscale('log')
ax3.set_xlim(1.8e-16, 2.2e-15)
ax3.set_ylim(-0.65, len(labels) - 0.35)
ax3.hlines(ys, 1.8e-16, values, color='#c6c6c6', linewidth=1.0, zorder=1)
ax3.scatter(values, ys, s=58, color=colors, edgecolors=colors, linewidths=0, zorder=2)
for y, value in zip(ys, values):
    ax3.text(
        value * 1.15, y + 0.01, sci(value) + ' Ha',
        va='bottom', ha='left', fontsize=9.8,
        color=INK, fontfamily='Noto Sans Mono',
    )
ax3.set_yticks(ys, labels)
ax3.set_xlabel('Absolute difference (Ha, log scale)', labelpad=10)
ax3.grid(axis='x', color=GRID, linewidth=0.8, zorder=0)
ax3.set_axisbelow(True)
ax3.tick_params(axis='y', labelsize=10.0, length=0, pad=8)
ax3.tick_params(axis='x', labelsize=9.3)
ax3.xaxis.set_major_formatter(mtick.LogFormatterMathtext(base=10))
ax3.set_title('Independent agreement checks', loc='left', fontsize=17, pad=28, color=INK, fontweight='medium')
ax3.text(
    0.0, 1.045, 'Every comparison lands at floating-point roundoff.',
    transform=ax3.transAxes, fontsize=10.8, color=MUTED,
)
ax3.text(
    0.995, -0.28, 'Source: docs/assets/h2_result.json · same validated H₂ run',
    transform=ax3.transAxes, ha='right', va='top', fontsize=9.0, color=MUTED,
)
fig2.savefig(OUT / 'agreement.png', dpi=220, facecolor=SURFACE, bbox_inches='tight', pad_inches=0.2)
plt.close(fig2)
print('wrote charts')
