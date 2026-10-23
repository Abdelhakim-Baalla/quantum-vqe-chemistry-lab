# Launch-media build scripts

These are the archived generators used to produce the checked-in launch media.
They are included for transparency and reproducibility, not as a packaged
one-command installer. They are excluded from the package lint/format run because
they depend on local browser, font and video tooling rather than the library
itself.

## Environment

- Python 3.12 with the project's `.[dev,web]` dependencies, plus Playwright.
- Chromium installed under Playwright. Set `CHROME_PATH` if it is not discoverable
  automatically.
- `ffmpeg` with `libx264`.
- Noto Sans and Noto Sans Mono fonts under `/usr/share/fonts/noto/`.
- The Streamlit app running locally at `http://127.0.0.1:8501`.

Optional environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `QUANTUM_LAB_REPO` | repository root inferred from this directory | Location of `app.py` and `docs/assets/h2_result.json` |
| `CHROME_PATH` | Playwright's selected Chromium | Explicit browser executable |
| `QUANTUM_LAB_RAW_DIR` | `/tmp/opencode/video_raw` | Scratch directory for the raw screen recording |

## Build order

From the repository root, with the app already running:

```bash
# README dashboard screenshots and carousel source captures
python docs/launch/scripts/final_capture.py

# Scientific charts and high-resolution circuits
python docs/launch/scripts/make_charts.py
python docs/launch/scripts/make_agreement_slide2.py
python docs/launch/scripts/make_circuit_hires.py

# 2400 x 3000 source slides, PDF and contact sheet
python docs/launch/scripts/build_slides.py
python docs/launch/scripts/make_pdf.py
python docs/launch/scripts/make_contact_sheet.py

# Video cards, live capture and final encode
python docs/launch/scripts/make_video_cards.py
python docs/launch/scripts/record_demo.py
docs/launch/scripts/assemble_video.sh
```

`record_demo.py` writes `demo_raw.webm` and `timeline.json` to
`$QUANTUM_LAB_RAW_DIR`. `assemble_video.sh` trims that capture from 6.4 s to
49.0 s, prepends the 4.0 s title card and appends the 6.5 s CTA card. The final
duration is 53.12 s at 1920 x 1080, 25 fps, H.264, yuv420p, with no audio.

Regenerating assets overwrites files under `docs/launch/`. Re-run the verification
checks, inspect the result, and update `MANIFEST.sha256` before committing.
