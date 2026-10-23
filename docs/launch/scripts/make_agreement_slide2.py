import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np

LAUNCH = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get('QUANTUM_LAB_REPO', LAUNCH.parents[1]))
OUT = LAUNCH / 'charts'
OUT.mkdir(parents=True, exist_ok=True)
DATA = ROOT / 'docs/assets/h2_result.json'
if not DATA.exists():
    DATA = LAUNCH / 'source/h2_result.json'
data = json.loads(DATA.read_text())
INK='#161616'; BODY='#393939'; MUTED='#6f6f6f'; BORDER='#bdbdbd'; GRID='#e8e8e8'
BLUE='#0f62fe'; GRAY='#8d8d8d'; SURFACE='#ffffff'
plt.rcParams.update({
    'font.family': 'Noto Sans', 'font.size': 12,
    'axes.edgecolor': BORDER, 'axes.labelcolor': BODY, 'xtick.color': MUTED,
    'ytick.color': MUTED, 'axes.spines.top': False, 'axes.spines.right': False,
    'figure.facecolor': SURFACE, 'axes.facecolor': SURFACE, 'savefig.facecolor': SURFACE,
})
SUP = str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹')
def sci(value):
    exponent = int(np.floor(np.log10(abs(value))))
    mantissa = value / (10 ** exponent)
    return f'{mantissa:.2f} × 10{str(exponent).translate(SUP)}'
comparisons = [
    ('VQE total vs exact diagonalization', data['errors_hartree']['absolute_vqe_vs_exact_total'], BLUE),
    ('HF vs independent PySCF RHF', data['errors_hartree']['absolute_hf_vs_pyscf_rhf_electronic'], GRAY),
    ('Parity + Z₂ vs full Jordan-Wigner', data['errors_hartree']['absolute_parity_vs_full_jw_electronic'], GRAY),
    ('Exact qubit vs PySCF FCI', data['errors_hartree']['absolute_exact_vs_pyscf_fci_total'], GRAY),
][::-1]
labels=[x[0] for x in comparisons]; values=[x[1] for x in comparisons]; colors=[x[2] for x in comparisons]
ys=np.arange(len(labels))
fig, ax = plt.subplots(figsize=(12.4, 7.35), dpi=240)
fig.subplots_adjust(left=0.335, right=0.955, top=0.965, bottom=0.145)
ax.set_xscale('log')
ax.set_xlim(1.8e-16, 2.2e-15)
ax.set_ylim(-0.68, len(labels)-0.32)
ax.hlines(ys, 1.8e-16, values, color='#c6c6c6', linewidth=1.2, zorder=1)
ax.scatter(values, ys, s=95, color=colors, edgecolors=colors, linewidths=0, zorder=2)
for y, value in zip(ys, values):
    ax.text(value*1.13, y+0.02, sci(value)+' Ha', va='bottom', ha='left', fontsize=12.0,
            color=INK, fontfamily='Noto Sans Mono')
ax.set_yticks(ys, labels)
ax.set_xlabel('Absolute difference (Ha, log scale)', labelpad=12, fontsize=12.5)
ax.grid(axis='x', color=GRID, linewidth=0.9, zorder=0); ax.set_axisbelow(True)
ax.tick_params(axis='y', labelsize=12.0, length=0, pad=10)
ax.tick_params(axis='x', labelsize=11.0)
ax.xaxis.set_major_formatter(mtick.LogFormatterMathtext(base=10))
fig.savefig(OUT/'agreement_slide2.png', dpi=240, facecolor=SURFACE, bbox_inches='tight', pad_inches=0.03)
print('wrote agreement_slide2.png')
