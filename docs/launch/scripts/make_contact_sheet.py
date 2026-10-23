#!/usr/bin/env python3
"""Build the 8-slide carousel contact sheet used for preview and QA."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
CAROUSEL = ROOT / "carousel"
OUT = CAROUSEL / "contact_sheet.jpg"

FILES = sorted(CAROUSEL.glob("[0-9][0-9]_*.png"))
if len(FILES) != 8:
    raise SystemExit(f"expected 8 carousel pages, found {len(FILES)}")

THUMB_W, THUMB_H = 300, 375
COLS, ROWS = 4, 2
MARGIN = 36
HEADER = 78
GAP_X = 28
GAP_Y = 46

WIDTH = MARGIN * 2 + COLS * THUMB_W + (COLS - 1) * GAP_X
HEIGHT = HEADER + MARGIN * 2 + ROWS * THUMB_H + (ROWS - 1) * GAP_Y

sheet = Image.new("RGB", (WIDTH, HEIGHT), "#f7f7f5")
draw = ImageDraw.Draw(sheet)
sans = ImageFont.truetype("/usr/share/fonts/noto/NotoSans-Regular.ttf", 30)
mono = ImageFont.truetype("/usr/share/fonts/noto/NotoSansMono-Regular.ttf", 11)
mono_bold = ImageFont.truetype("/usr/share/fonts/noto/NotoSansMono-Bold.ttf", 11)

draw.text((MARGIN, 28), "Quantum Lab", font=sans, fill="#161616")
draw.text((WIDTH - MARGIN, 36), "LINKEDIN CAROUSEL / 8 PAGES / 4:5",
          font=mono, fill="#6f6f6f", anchor="rt")
draw.line([(MARGIN, 64), (WIDTH - MARGIN, 64)], fill="#bdbdbd", width=1)

labels = [
    "COVER", "PROTOCOL", "ARCHITECTURE", "DASHBOARD",
    "RESULT", "TRACE", "CIRCUIT", "ENGINEERING",
]
for index, (path, label) in enumerate(zip(FILES, labels)):
    image = Image.open(path).convert("RGB").resize(
        (THUMB_W, THUMB_H), Image.Resampling.LANCZOS
    )
    x = MARGIN + (index % COLS) * (THUMB_W + GAP_X)
    y = HEADER + MARGIN + (index // COLS) * (THUMB_H + GAP_Y)
    sheet.paste(image, (x, y))
    draw.rectangle([x, y, x + THUMB_W - 1, y + THUMB_H - 1],
                   outline="#d9d9d9", width=1)
    draw.text((x, y + THUMB_H + 10), f"{index + 1:02d} / {label}",
              font=mono_bold, fill="#161616")

sheet.save(OUT, quality=92, optimize=True)
print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {sheet.size[0]}x{sheet.size[1]})")
