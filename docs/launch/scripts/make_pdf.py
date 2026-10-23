#!/usr/bin/env python3
"""Build the 4:5 LinkedIn carousel PDF from the 2400x3000 source slides."""

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CAROUSEL = ROOT / "carousel"
SLIDES = ROOT / "slides"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else CAROUSEL / "Quantum_Lab_LinkedIn_Carousel.pdf"

# The PDF embeds the 2400x3000 source slides at 300 ppi. At 300 ppi a
# 2400x3000 image is exactly 8x10 inches, i.e. 576x720 pt (4:5).
pages = sorted(SLIDES.glob("[0-9][0-9]_*.png"))
if len(pages) != 8:
    raise SystemExit(f"expected 8 source slides, found {len(pages)}")

images = [Image.open(path).convert("RGB") for path in pages]
for path, image in zip(pages, images):
    if image.size != (2400, 3000):
        raise SystemExit(f"{path.name}: expected 2400x3000, got {image.size}")

images[0].save(
    OUT,
    save_all=True,
    append_images=images[1:],
    resolution=300.0,
    quality=95,
    optimize=True,
)

print(f"wrote {OUT} ({OUT.stat().st_size} bytes, {len(images)} pages)")
