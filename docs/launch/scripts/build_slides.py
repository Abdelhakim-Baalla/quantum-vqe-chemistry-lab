import json
import os
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

LAUNCH = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get('QUANTUM_LAB_REPO', LAUNCH.parents[1]))
OUT = LAUNCH / 'slides'
OUT.mkdir(parents=True, exist_ok=True)
RAW = LAUNCH / 'screenshots'
CHARTS = LAUNCH / 'charts'
DATA = ROOT / 'docs/assets/h2_result.json'
if not DATA.exists():
    DATA = LAUNCH / 'source/h2_result.json'
data = json.loads(DATA.read_text())

W, H, S = 1200, 1500, 2
BG = '#f7f7f5'
SURFACE = '#ffffff'
INK = '#161616'
BODY = '#393939'
MUTED = '#6f6f6f'
SUBTLE = '#8d8d8d'
BORDER = '#d9d9d9'
BORDER_STRONG = '#bdbdbd'
BLUE = '#0f62fe'
BLUE_SOFT = '#edf5ff'
GREEN = '#198038'
RED = '#da1e28'
AMBER = '#8e6a00'
MONO = '/usr/share/fonts/noto/NotoSansMono-Regular.ttf'
MONO_BOLD = '/usr/share/fonts/noto/NotoSansMono-Bold.ttf'
SANS = '/usr/share/fonts/noto/NotoSans-Regular.ttf'
SANS_BOLD = '/usr/share/fonts/noto/NotoSans-Bold.ttf'

_font_cache = {}
def font(size, weight='regular', mono=False):
    key = (size, weight, mono)
    if key not in _font_cache:
        if mono:
            path = MONO_BOLD if weight in {'bold', 'medium'} else MONO
        else:
            path = SANS_BOLD if weight in {'bold', 'medium'} else SANS
        _font_cache[key] = ImageFont.truetype(path, int(round(size * S)))
    return _font_cache[key]

def new_slide():
    image = Image.new('RGB', (W * S, H * S), BG)
    return image, ImageDraw.Draw(image)

def xy(x, y):
    return (int(round(x * S)), int(round(y * S)))

def line(draw, points, fill=BORDER, width=1):
    draw.line([xy(x, y) for x, y in points], fill=fill, width=max(1, int(round(width * S))))

def rect(draw, box, fill=None, outline=None, width=1):
    draw.rectangle([xy(box[0], box[1]), xy(box[2], box[3])], fill=fill, outline=outline,
                   width=max(1, int(round(width * S))))

def text(draw, x, y, value, size=18, weight='regular', fill=INK, mono=False, anchor='lt'):
    draw.text(xy(x, y), value, font=font(size, weight, mono), fill=fill, anchor=anchor)

def text_width(draw, value, size=18, weight='regular', mono=False):
    return draw.textlength(value, font=font(size, weight, mono)) / S

def wrap(draw, value, max_width, size=18, weight='regular', mono=False):
    words = value.split()
    lines = []
    current = ''
    for word in words:
        candidate = word if not current else current + ' ' + word
        if text_width(draw, candidate, size, weight, mono) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def paragraph(draw, x, y, value, size=18, line_height=None, weight='regular',
              fill=BODY, mono=False, max_width=None, anchor='lt'):
    lines = [value]
    if max_width is not None:
        lines = wrap(draw, value, max_width, size, weight, mono)
    step = line_height if line_height is not None else size * 1.42
    for index, item in enumerate(lines):
        text(draw, x, y + index * step, item, size, weight, fill, mono, anchor)
    return y + len(lines) * step

def eyebrow(draw, y, value):
    rect(draw, (80, y + 2, 83, y + 15), BLUE, BLUE)
    text(draw, 94, y, value, 10.2, 'medium', BLUE, mono=True)

def title(draw, y, lines, size=62, line_height=None, fill=INK):
    step = line_height or size * 1.08
    for index, line_value in enumerate(lines):
        text(draw, 80, y + index * step, line_value, size, 'regular', fill)

def card(draw, box, fill=SURFACE, outline=BORDER):
    rect(draw, box, fill, outline, 1)

def metric_card(draw, x, y, w, h, label, value, note=None, value_size=18, accent=False):
    card(draw, (x, y, x + w, y + h))
    if accent:
        rect(draw, (x, y, x + w, y + 2), BLUE, BLUE)
    text(draw, x + 18, y + 16, label, 9.5, 'medium', MUTED, mono=True)
    text(draw, x + 18, y + 39, value, value_size, 'medium', INK, mono=True)
    if note:
        text(draw, x + 18, y + 68, note, 9.2, 'regular', MUTED, mono=True)

def paste_fit(image, path, box, pad=0, fill=SURFACE):
    target_w = int(round((box[2] - box[0] - 2 * pad) * S))
    target_h = int(round((box[3] - box[1] - 2 * pad) * S))
    source = Image.open(path).convert('RGB')
    source.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
    x = int(round((box[0] + pad) * S + (target_w - source.width) / 2))
    y = int(round((box[1] + pad) * S + (target_h - source.height) / 2))
    image.paste(source, (x, y))

# ---------------------------------------------------------------------------
# 01 — Cover
# ---------------------------------------------------------------------------
image, draw = new_slide()
eyebrow(draw, 168, 'REFERENCE IMPLEMENTATION / H₂ VQE')
title(draw, 202, ['A two-qubit VQE', 'reproduced the', 'H₂ ground state.'], 81, 87)
paragraph(
    draw, 80, 503,
    'A reproducible variational quantum eigensolver with independent exact-diagonalization '
    'and PySCF FCI validation. No hardware. No mock data.',
    21, 31, max_width=830,
)
line(draw, [(80, 618), (1120, 618)], BORDER, 1)
text(draw, 80, 652, 'ABSOLUTE ERROR VS EXACT DIAGONALIZATION', 10.2, 'medium', MUTED, mono=True)
rect(draw, (80, 688, 84, 760), BLUE, BLUE)
text(draw, 108, 673, '4.44 × 10⁻¹⁶', 92, 'regular', BLUE, mono=False)
text(draw, 858, 721, 'Ha', 34, 'regular', BLUE)
text(draw, 80, 790, 'on the total H₂ energy — the same two-qubit Hamiltonian.', 18, 'regular', BODY)
text(draw, 80, 842, 'VQE', 10.2, 'medium', MUTED, mono=True)
text(draw, 126, 838, '−1.1373060357533986 Ha', 15.2, 'medium', INK, mono=True)
text(draw, 80, 872, 'EXACT', 10.2, 'medium', MUTED, mono=True)
text(draw, 126, 868, '−1.137306035753399 Ha', 15.2, 'medium', INK, mono=True)
# Stats row
line(draw, [(80, 960), (1120, 960)], BORDER, 1)
for index, (number, label) in enumerate([
    ('2', 'QUBITS AFTER TAPERING'),
    ('3', 'UCCSD PARAMETERS'),
    ('10 / 10', 'SCIENTIFIC CHECKS'),
]):
    x = 80 + index * 350
    text(draw, x, 990, number, 31, 'regular', INK, mono=True)
    text(draw, x, 1033, label, 9.6, 'medium', MUTED, mono=True)
text(draw, 80, 1120, 'H₂ · STO-3G · UCCSD · parity + Z₂ · exact statevector', 10.8, 'regular', MUTED, mono=True)
text(draw, 80, 1160, 'The molecule is deliberately small. The validation is not.', 20, 'regular', INK)
text(draw, 80, 1235, 'Documented run · 2026-10-23 16:36 UTC', 9.8, 'regular', MUTED, mono=True)
image.save(OUT / '01_cover.png', quality=95)
print('01')

# ---------------------------------------------------------------------------
# 02 — Protocol
# ---------------------------------------------------------------------------
image, draw = new_slide()
eyebrow(draw, 152, 'THE EXPERIMENT')
title(draw, 184, ['Small system.', 'Strict validation.'], 64, 69)
paragraph(
    draw, 80, 340,
    'The toy molecule is deliberate: every intermediate result can be checked independently, '
    'from the fermionic Hamiltonian to the final JSON artifact.',
    20, 29, max_width=930,
)
items = [
    ('MOLECULE', 'H₂ at 0.735 Å', 'STO-3G · 2 electrons · 4 spin orbitals'),
    ('HAMILTONIAN', '2 qubits · 5 Pauli terms', 'Parity mapping + two-qubit Z₂ tapering'),
    ('ANSATZ', 'UCCSD · 3 parameters', 'Hartree–Fock reference · singles + doubles'),
    ('OPTIMIZER', 'L-BFGS-B · 24 evaluations', '4 iterations · converged · exact statevector'),
    ('REFERENCES', 'Exact diagonalization + PySCF FCI', 'Same qubit Hamiltonian · independent implementation'),
    ('EVIDENCE', '10 / 10 checks passed', 'JSON artifact + 123 automated tests'),
]
for index, (label, value, note) in enumerate(items):
    col = index % 2
    row = index // 2
    x = 80 + col * 530
    y = 430 + row * 222
    card(draw, (x, y, x + 510, y + 200))
    rect(draw, (x + 20, y + 20, x + 26, y + 26), BLUE, BLUE)
    text(draw, x + 36, y + 17, label, 9.8, 'medium', MUTED, mono=True)
    text(draw, x + 490, y + 17, f'{index + 1:02d}', 10.0, 'regular', '#bdbdbd', mono=True, anchor='rt')
    text(draw, x + 20, y + 52, value, 18.5, 'medium', INK)
    paragraph(draw, x + 20, y + 91, note, 12.6, 19, fill=MUTED, max_width=455)
line(draw, [(80, 1145), (1120, 1145)], BORDER, 1)
text(draw, 80, 1170, 'THE 2-QUBIT HAMILTONIAN', 9.8, 'medium', MUTED, mono=True)
text(draw, 80, 1200, 'H = −1.0523732458 II + 0.3979374248 IZ − 0.3979374248 ZI', 11.4, 'regular', BODY, mono=True)
text(draw, 80, 1226, '      − 0.0112801043 ZZ + 0.1809311998 XX', 11.4, 'regular', BODY, mono=True)
text(draw, 1120, 1200, 'same Hamiltonian', 9.8, 'regular', MUTED, mono=True, anchor='rt')
text(draw, 1120, 1226, 'for every reference', 9.8, 'regular', MUTED, mono=True, anchor='rt')
image.save(OUT / '02_protocol.png', quality=95)
print('02')

# ---------------------------------------------------------------------------
# 03 — Architecture
# ---------------------------------------------------------------------------
image, draw = new_slide()
eyebrow(draw, 152, 'SYSTEM DESIGN')
title(draw, 184, ['One scientific layer.', 'Two interfaces.'], 61, 66)
paragraph(
    draw, 80, 335,
    'The Streamlit dashboard is a view over the validated quantum_vqe package — not a second implementation.',
    20, 29, max_width=900,
)
# Pipeline panel
card(draw, (80, 420, 670, 1280))
text(draw, 105, 447, 'PIPELINE', 9.8, 'medium', MUTED, mono=True)
line(draw, [(125, 500), (125, 1110)], BORDER_STRONG, 1)
stages = [
    ('PySCF integrals', 'geometry + STO-3G basis'),
    ('Fermionic Hamiltonian', 'second-quantized operators'),
    ('Parity + Z₂ tapering', '4 spin orbitals → 2 qubits'),
    ('UCCSD + L-BFGS-B', '3 parameters · 24 evaluations'),
    ('Independent validation', 'exact diagonalization + PySCF FCI'),
    ('Typed result artifact', 'energies · checks · timing · software'),
]
for index, (name, note) in enumerate(stages):
    y = 482 + index * 116
    rect(draw, (118, y + 4, 132, y + 18), BLUE, BLUE)
    text(draw, 155, y - 2, name, 17.5, 'medium', INK)
    text(draw, 155, y + 27, note, 11.8, 'regular', MUTED, mono=True)
    if index < len(stages) - 1:
        text(draw, 118, y + 51, '↓', 16, 'regular', BORDER_STRONG, mono=True)
line(draw, [(105, 1142), (645, 1142)], BORDER, 1)
text(draw, 105, 1162, 'VALIDATED RESULT', 9.6, 'medium', MUTED, mono=True)
text(draw, 105, 1190, '−1.1373060357533986 Ha', 14.2, 'medium', INK, mono=True)
text(draw, 105, 1220, '10 / 10 checks · 123 tests', 10.5, 'regular', GREEN, mono=True)
# Right panels
card(draw, (700, 420, 1120, 730))
text(draw, 725, 447, 'INTERFACES', 9.8, 'medium', MUTED, mono=True)
text(draw, 725, 485, 'CLI', 15.5, 'medium', INK, mono=True)
text(draw, 725, 511, 'python -m quantum_vqe run-h2', 11.4, 'regular', BODY, mono=True)
text(draw, 725, 552, 'Streamlit', 15.5, 'medium', INK, mono=True)
text(draw, 725, 578, 'streamlit run app.py', 11.4, 'regular', BODY, mono=True)
line(draw, [(725, 616), (1095, 616)], BORDER, 1)
text(draw, 725, 638, 'Both call the same', 11.8, 'regular', MUTED)
text(draw, 725, 660, 'ExperimentConfig → quantum_vqe', 11.8, 'medium', BLUE, mono=True)
card(draw, (700, 760, 1120, 1155))
text(draw, 725, 787, 'OPERATIONAL ENVELOPE', 9.8, 'medium', MUTED, mono=True)
ops = ['Local CPU only', 'Exact statevector · no shots', 'No cloud account or API key', 'Deterministic HF start', 'Versioned JSON · MIT license']
for index, item in enumerate(ops):
    y = 828 + index * 48
    rect(draw, (725, y + 4, 731, y + 10), BLUE, BLUE)
    text(draw, 744, y - 2, item, 12.4, 'regular', BODY)
card(draw, (700, 1185, 1120, 1280))
text(draw, 725, 1206, '●', 14, 'regular', GREEN, mono=True)
text(draw, 748, 1207, '10 / 10 scientific checks passed', 13.2, 'medium', INK)
text(draw, 748, 1230, '123 automated tests · CI 3.11 / 3.12', 10.5, 'regular', MUTED, mono=True)
image.save(OUT / '03_architecture.png', quality=95)
print('03')

# ---------------------------------------------------------------------------
# 04 — Dashboard
# ---------------------------------------------------------------------------
image, draw = new_slide()
eyebrow(draw, 152, 'THE INTERFACE')
title(draw, 184, ['A real workbench.'], 64, 69)
paragraph(
    draw, 80, 270,
    'Configure, run, inspect the real-data dashboard, and export from a local Streamlit '
    'interface backed by the same scientific layer as the CLI.',
    20, 29, max_width=900,
)
# Browser frame
fx, fy, fw, fh = 80, 365, 1040, 820
rect(draw, (fx + 6, fy + 8, fx + fw + 6, fy + fh + 8), '#e9e9e7', '#e9e9e7')
rect(draw, (fx, fy, fx + fw, fy + fh), SURFACE, BORDER, 1)
rect(draw, (fx, fy, fx + fw, fy + 34), '#f0f0ee', BORDER, 1)
for dot_x in (fx + 17, fx + 30, fx + 43):
    rect(draw, (dot_x, fy + 15, dot_x + 5, fy + 20), '#bdbdbd', '#bdbdbd')
text(draw, fx + fw / 2, fy + 11, '127.0.0.1:8501', 9.8, 'regular', MUTED, mono=True, anchor='mt')
paste_fit(image, RAW / '01_dashboard_hero.png', (fx + 1, fy + 35, fx + fw - 1, fy + fh - 1))
# Caption row
text(draw, 80, 1218, 'STREAMLIT / LOCAL', 9.6, 'medium', BLUE, mono=True)
text(draw, 80, 1246, 'No cloud · no API key · no hardware', 13.5, 'regular', BODY)
text(draw, 1120, 1218, 'DASHBOARD → RESULT → CIRCUIT', 9.6, 'medium', MUTED, mono=True, anchor='rt')
text(draw, 1120, 1246, 'Every panel reads from ExperimentResult.', 13.5, 'regular', BODY, anchor='rt')
image.save(OUT / '04_dashboard.png', quality=95)
print('04')

# ---------------------------------------------------------------------------
# 05 — Result
# ---------------------------------------------------------------------------
image, draw = new_slide()
eyebrow(draw, 152, 'THE RESULT')
title(draw, 184, ['Agreement to the last digit.'], 61, 66)
paragraph(
    draw, 80, 270,
    'The VQE and exact diagonalization agree at 4.44 × 10⁻¹⁶ Ha on the total H₂ energy. '
    'Exact diagonalization and PySCF FCI agree at 1.33 × 10⁻¹⁵ Ha.',
    20, 29, max_width=960,
)
metric_card(draw, 80, 380, 325, 126, 'VQE TOTAL', '−1.1373060357533986 Ha', 'optimized statevector', 15.7, True)
metric_card(draw, 427, 380, 325, 126, 'EXACT QUBIT', '−1.137306035753399 Ha', 'dense diagonalization', 15.7)
metric_card(draw, 774, 380, 346, 126, 'ABSOLUTE ERROR', '4.440892098500626 × 10⁻¹⁶ Ha', 'total energy', 13.2)
card(draw, (80, 540, 1120, 1290))
text(draw, 105, 565, 'INDEPENDENT AGREEMENT CHECKS', 9.8, 'medium', MUTED, mono=True)
paste_fit(image, CHARTS / 'agreement_slide2.png', (100, 598, 1100, 1228))
text(draw, 80, 1318, 'Every comparison lands at floating-point roundoff — no hand-entered energies.', 13.2, 'regular', BODY)
text(draw, 1120, 1318, '10 / 10 checks passed', 12.0, 'medium', GREEN, mono=True, anchor='rt')
image.save(OUT / '05_result.png', quality=95)
print('05')

# ---------------------------------------------------------------------------
# 06 — Convergence
# ---------------------------------------------------------------------------
image, draw = new_slide()
eyebrow(draw, 152, 'THE OPTIMIZER')
title(draw, 184, ['What the optimizer actually did.'], 58, 63)
paragraph(
    draw, 80, 270,
    'All 24 recorded cost-function evaluations, including the line-search excursion. '
    'No smoothing, interpolation, or synthetic points.',
    20, 29, max_width=960,
)
paste_fit(image, CHARTS / 'convergence.png', (80, 355, 1120, 955))
line(draw, [(80, 990), (1120, 990)], BORDER, 1)
for index, (value, label) in enumerate([
    ('24', 'COST-FUNCTION EVALUATIONS'),
    ('4', 'OPTIMIZER ITERATIONS'),
    ('CONVERGED', 'L-BFGS-B STATUS'),
]):
    x = 80 + index * 350
    text(draw, x, 1010, value, 23, 'medium', INK, mono=True)
    text(draw, x, 1048, label, 9.5, 'medium', MUTED, mono=True)
paragraph(
    draw, 80, 1105,
    'The excursion is real: L-BFGS-B evaluated higher-energy points during a line search. '
    'The best-so-far trace never moves backwards.',
    17.5, 26, max_width=920,
)
text(draw, 80, 1185, 'BEST-SO-FAR |ERROR|', 9.6, 'medium', BLUE, mono=True)
text(draw, 80, 1213, '4.44 × 10⁻¹⁶ Ha', 22, 'medium', BLUE, mono=True)
text(draw, 720, 1185, 'FINAL VQE TOTAL', 9.6, 'medium', MUTED, mono=True)
text(draw, 720, 1211, '−1.1373060357533986 Ha', 17.0, 'medium', INK, mono=True)
image.save(OUT / '06_convergence.png', quality=95)
print('06')

# ---------------------------------------------------------------------------
# 07 — Circuit
# ---------------------------------------------------------------------------
image, draw = new_slide()
eyebrow(draw, 152, 'THE CIRCUIT')
title(draw, 184, ['The ansatz is the executed object.'], 57, 62)
paragraph(
    draw, 80, 265,
    'Rendered from the exact UCCSD circuit passed into the VQE — not a decorative illustration.',
    20, 29, max_width=930,
)
for index, (label, value) in enumerate([
    ('QUBITS', '2'), ('PARAMETERS', '3'), ('DEPTH · BASIS', '12'), ('GATES · BASIS', '17'),
]):
    x = 80 + index * 265
    metric_card(draw, x, 350, 245, 105, label, value, value_size=22, accent=index == 0)
card(draw, (80, 500, 1120, 900))
text(draw, 105, 525, 'PAULI EVOLUTION / ONE DECOMPOSITION LEVEL', 9.6, 'medium', MUTED, mono=True)
paste_fit(image, CHARTS / 'circuit_pauli_hires.png', (105, 555, 1095, 875))
line(draw, [(80, 940), (1120, 940)], BORDER, 1)
text(draw, 80, 970, 'WHAT IS EXECUTED', 9.8, 'medium', MUTED, mono=True)
paragraph(
    draw, 80, 1002,
    'The Hartree–Fock reference is prepared, then UCCSD excitation blocks act on two qubits. '
    'The estimator evaluates the same five-term Hamiltonian on the resulting statevector.',
    14.5, 22, max_width=340,
)
text(draw, 470, 970, 'WHY IT MATTERS', 9.8, 'medium', MUTED, mono=True)
paragraph(
    draw, 470, 1002,
    'Depth and gate counts are computed from the same circuit object used by the run. '
    'The dashboard and CLI cannot drift into different circuit claims.',
    14.5, 22, max_width=330,
)
text(draw, 850, 970, 'BASIS-GATE COUNTS', 9.8, 'medium', MUTED, mono=True)
for index, value in enumerate(['H 4 · CX 4', 'RY 2 · SX 2', 'RZ 2 · U 1', 'SXDG 2']):
    text(draw, 850, 1002 + index * 25, value, 12.2, 'regular', BODY, mono=True)
text(draw, 80, 1190, 'Basis-gate decomposition available in the dashboard.', 11.5, 'regular', MUTED, mono=True)
text(draw, 80, 1230, 'UCCSD · 3 parameters · 2 qubits · 17 basis gates', 18, 'regular', INK)
image.save(OUT / '07_circuit.png', quality=95)
print('07')

# ---------------------------------------------------------------------------
# 08 — Engineering / CTA
# ---------------------------------------------------------------------------
image, draw = new_slide()
eyebrow(draw, 152, 'REPRODUCIBILITY')
title(draw, 184, ['The result is the easy part.', 'The evidence is the product.'], 56, 62)
paragraph(
    draw, 80, 325,
    'The repository ships the experiment, the dashboard, the tests, and the exact artifact that '
    'produced the headline number.',
    20, 29, max_width=950,
)
items = [
    ('123', 'AUTOMATED TESTS', 'unit + integration, including a real H₂ run'),
    ('10 / 10', 'SCIENTIFIC CHECKS', 'hermiticity, convergence, references, taper cross-check'),
    ('3.11 / 3.12', 'CI MATRIX', 'green on GitHub Actions'),
    ('MIT', 'LICENSE', 'open source · local · no cloud or hardware'),
]
for index, (value, label, note) in enumerate(items):
    col = index % 2
    row = index // 2
    x = 80 + col * 530
    y = 405 + row * 230
    card(draw, (x, y, x + 510, y + 205))
    text(draw, x + 20, y + 22, value, 35, 'regular', INK, mono=True)
    text(draw, x + 20, y + 76, label, 9.8, 'medium', BLUE, mono=True)
    paragraph(draw, x + 20, y + 105, note, 13.0, 20, fill=MUTED, max_width=465)
# CTA
rect(draw, (80, 905, 1120, 1250), INK, INK)
text(draw, 112, 940, 'RUN IT YOURSELF', 10.0, 'medium', BLUE, mono=True)
text(draw, 112, 978, 'Read the code. Reproduce the result.', 35, 'regular', '#ffffff')
text(draw, 112, 1026, 'Challenge the claims.', 35, 'regular', '#ffffff')
text(draw, 112, 1100, 'github.com/Abdelhakim-Baalla/quantum-vqe-chemistry-lab', 15.2, 'medium', '#ffffff', mono=True)
text(draw, 112, 1148, 'MIT licensed · Python 3.11 / 3.12 · no quantum hardware required', 11.2, 'regular', '#a8a8a8', mono=True)
text(draw, 1092, 1200, 'H₂ / STO-3G / UCCSD / 2Q', 10.5, 'medium', '#6f6f6f', mono=True, anchor='rt')
image.save(OUT / '08_engineering.png', quality=95)
print('08')
