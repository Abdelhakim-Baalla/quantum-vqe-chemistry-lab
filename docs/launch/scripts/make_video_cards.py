#!/usr/bin/env python3
"""Build the minimalist title card and the closing CTA card."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

LAUNCH = Path(__file__).resolve().parents[1]
OUT = LAUNCH / "video"
OUT.mkdir(parents=True, exist_ok=True)
W, H, S = 1920, 1080, 2

BG = "#f7f7f5"
INK = "#161616"
BODY = "#393939"
MUTED = "#6f6f6f"
BORDER = "#bdbdbd"
BLUE = "#0f62fe"
GREEN = "#198038"
SANS = "/usr/share/fonts/noto/NotoSans-Regular.ttf"
SANS_BOLD = "/usr/share/fonts/noto/NotoSans-Bold.ttf"
MONO = "/usr/share/fonts/noto/NotoSansMono-Regular.ttf"
MONO_BOLD = "/usr/share/fonts/noto/NotoSansMono-Bold.ttf"


def font(size, bold=False, mono=False):
    path = (MONO_BOLD if bold else MONO) if mono else (SANS_BOLD if bold else SANS)
    return ImageFont.truetype(path, int(round(size * S)))


def xy(x, y):
    return (int(round(x * S)), int(round(y * S)))


def line(d, pts, fill=BORDER, width=1):
    d.line([xy(x, y) for x, y in pts], fill=fill, width=max(1, int(round(width * S))))


def rect(d, box, fill=None, outline=None, width=1):
    d.rectangle(
        [xy(box[0], box[1]), xy(box[2], box[3])],
        fill=fill,
        outline=outline,
        width=max(1, int(round(width * S))),
    )


def text(d, x, y, value, size=20, weight="regular", fill=INK, mono=False, anchor="lt"):
    d.text(
        xy(x, y),
        value,
        font=font(size, weight in {"medium", "bold"}, mono),
        fill=fill,
        anchor=anchor,
    )


# ---------------------------------------------------------------------------
# Title card: deliberately centered and minimal.
# ---------------------------------------------------------------------------
im = Image.new("RGB", (W * S, H * S), BG)
d = ImageDraw.Draw(im)
text(d, W / 2, 300, "REFERENCE IMPLEMENTATION / H₂ VQE", 12, "medium", BLUE, mono=True, anchor="mt")
text(d, W / 2, 338, "Quantum Lab", 146, "regular", INK, anchor="mt")
line(d, [(W / 2 - 100, 555), (W / 2 + 100, 555)], BLUE, 2)
text(d, W / 2, 590, "Abdelhakim Baalla", 32, "regular", BODY, anchor="mt")
text(
    d,
    W / 2,
    650,
    "H₂ / STO-3G / UCCSD  ·  2 qubits  ·  exact statevector",
    15,
    "regular",
    MUTED,
    mono=True,
    anchor="mt",
)
text(d, W / 2, 930, "OPEN SOURCE / MIT", 11, "regular", MUTED, mono=True, anchor="mt")
im.save(OUT / "title_card.png", quality=95)
im.resize((W, H), Image.Resampling.LANCZOS).save(OUT / "title_card_1080.png", quality=95)
im.resize((W, H), Image.Resampling.LANCZOS).convert("RGB").save(
    OUT / "Quantum_Lab_Launch_poster.jpg", quality=92, optimize=True
)

# ---------------------------------------------------------------------------
# End card: the approved closing layout, with current test count.
# ---------------------------------------------------------------------------
im = Image.new("RGB", (W * S, H * S), "#161616")
d = ImageDraw.Draw(im)
line(d, [(120, 92), (1800, 92)], "#393939", 1)
text(d, 120, 48, "QUANTUM LAB", 12, "medium", "#ffffff", mono=True)
text(d, 1800, 48, "OPEN SOURCE / MIT", 12, "regular", "#a8a8a8", mono=True, anchor="rt")
rect(d, (120, 270, 124, 300), BLUE, BLUE)
text(d, 144, 266, "REPRODUCIBILITY", 12, "medium", "#78a9ff", mono=True)
text(d, 120, 310, "Read the code.", 84, "regular", "#ffffff")
text(d, 120, 406, "Reproduce the result.", 84, "regular", "#ffffff")
text(d, 120, 502, "Challenge the claims.", 84, "regular", "#78a9ff")
line(d, [(120, 660), (1800, 660)], "#393939", 1)
text(
    d,
    120,
    700,
    "github.com/Abdelhakim-Baalla/quantum-vqe-chemistry-lab",
    26,
    "medium",
    "#ffffff",
    mono=True,
)
text(
    d,
    120,
    754,
    "H₂ / STO-3G / UCCSD / parity + Z₂ / exact statevector",
    15,
    "regular",
    "#a8a8a8",
    mono=True,
)
text(d, 120, 892, "123 automated tests", 17, "regular", "#a8a8a8", mono=True)
text(d, 520, 892, "CI green · Python 3.11 / 3.12", 17, "regular", "#a8a8a8", mono=True)
text(d, 1120, 892, "10 / 10 scientific checks", 17, "regular", "#a8a8a8", mono=True)
text(d, 1800, 980, "MIT · LOCAL · NO HARDWARE", 12, "regular", "#6f6f6f", mono=True, anchor="rt")
im.save(OUT / "end_card.png", quality=95)
im.resize((W, H), Image.Resampling.LANCZOS).save(OUT / "end_card_1080.png", quality=95)
print("wrote title/end cards and poster")
