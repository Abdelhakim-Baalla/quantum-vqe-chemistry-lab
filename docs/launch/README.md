# Quantum Lab — launch media

Final launch package for the **Quantum Lab** web interface and the checked-in
H₂/STO-3G VQE reference run. Everything here is committed inside the
repository; there is no external media dependency.

- **Repository:** <https://github.com/Abdelhakim-Baalla/quantum-vqe-chemistry-lab>
- **Post copy, alt text, first comment, hashtags, posting plan:**
  [`LINKEDIN_POST.md`](LINKEDIN_POST.md)
- **Checksums:** [`MANIFEST.sha256`](MANIFEST.sha256)
- **Scientific source of truth:** `docs/assets/h2_result.json` (snapshot in
  [`source/h2_result.json`](source/h2_result.json))
- **Official run:** 2026-10-23T16:36:19+00:00

The package is derived from the app's real H₂ run. There are no mock energies,
synthetic convergence points or hardware claims.

---

## Publish

### Carousel — recommended primary post

```text
carousel/Quantum_Lab_LinkedIn_Carousel.pdf
```

- 8 pages, 4:5 portrait, 576 x 720 pt PDF, 2.73 MB; 2400 x 3000 source
  slides and 1200 x 1500 PNG exports.
- Upload as a **document post** on LinkedIn.
- Alternative: upload the eight 1200 x 1500 PNGs in `carousel/` individually.
- Contact sheet for a quick visual review:
  [`carousel/contact_sheet.jpg`](carousel/contact_sheet.jpg).

Page sequence:

1. Cover — the validated result and the honest boundary.
2. Protocol — six steps from H₂ geometry to independent FCI validation.
3. Architecture — one scientific layer shared by the CLI and the UI.
4. Dashboard — real H₂ VQE results, twelve metrics and six diagnostics.
5. Result — VQE, exact diagonalization and PySCF FCI agreement.
6. Convergence — the raw optimizer trace.
7. Circuit — the executed two-qubit UCCSD ansatz.
8. Engineering — tests, checks, CI, license and call to action.

### Video — native LinkedIn upload

```text
video/Quantum_Lab_Launch.mp4
```

- **53.12 s**, 1920 x 1080, 25 fps, H.264, yuv420p, faststart, no audio,
  7.78 MB.
- Poster: [`video/Quantum_Lab_Launch_poster.jpg`](video/Quantum_Lab_Launch_poster.jpg).
- Optional captions:
  [`video/Quantum_Lab_Launch.srt`](video/Quantum_Lab_Launch.srt).
- A real Playwright capture of the local Streamlit app with a synthetic cursor,
  visible click ripples and a subtle click zoom. The recording is deliberately
  silent; section captions are rendered on screen.
- Sequence: title card → local workbench and real run → dashboard → energy
  result → optimizer trace → executed circuit/Pauli evolution → closing CTA.

The video is a separate live run from the documented 16:36 UTC run. It produces
the same energies and checks with a later timestamp.

### Copy

Open [`LINKEDIN_POST.md`](LINKEDIN_POST.md) for:

- the main carousel post (2,288 characters, 2,395 with hashtags);
- a shorter 667-character variant;
- a 476-character video caption;
- the pinned first comment with reproduction commands;
- eight hashtags;
- alt text for every slide and the video;
- posting, timing, SEO and claims-boundary guidance.

---

## Official result

| Quantity | Value |
| --- | ---: |
| VQE total energy | **−1.1373060357533986 Ha** |
| Exact diagonalization total | **−1.137306035753399 Ha** |
| PySCF FCI total | **−1.1373060357534004 Ha** |
| Absolute VQE error | **4.440892098500626e-16 Ha** |
| Scientific checks | **10 / 10** |
| Automated tests | **123** (106 unit + 17 integration) |

Configuration: H₂ at 0.735 Å, STO-3G, UCCSD, parity mapping with Z₂ tapering,
2 qubits, 5 Pauli terms, 3 parameters, exact statevector simulation, L-BFGS-B,
24 evaluations, 4 iterations. CI covers Python 3.11 and 3.12.

---

## Asset map

### Final upload assets

| Path | What it is |
| --- | --- |
| `carousel/Quantum_Lab_LinkedIn_Carousel.pdf` | Final 8-page LinkedIn document post |
| `carousel/01_cover.png` … `08_engineering.png` | Final 1200 x 1500 slides |
| `carousel/contact_sheet.jpg` | Eight-slide preview sheet |
| `video/Quantum_Lab_Launch.mp4` | Final 53.12 s silent walkthrough |
| `video/Quantum_Lab_Launch_poster.jpg` | 1920 x 1080 thumbnail |
| `video/Quantum_Lab_Launch.srt` | Optional accessibility captions |
| `screenshots/quantum-lab-dashboard-light.png` | Final README dashboard, light |
| `screenshots/quantum-lab-dashboard-dark.png` | Final README dashboard, dark |

### Screenshots and source artwork

| Path | What it is |
| --- | --- |
| `screenshots/01_dashboard_hero.png` | Wide dashboard capture used by the carousel |
| `screenshots/02_energy_results.png` | Real UI energy result capture |
| `screenshots/03_circuit.png` | Real UI circuit capture |
| `screenshots/04_convergence.png` | Real UI optimizer-trace capture |
| `screenshots/05_experiment_wide.png` | Wide experiment-view capture |
| `charts/convergence.png` | Raw optimizer trace for the slides |
| `charts/agreement.png`, `charts/agreement_slide2.png` | Energy-agreement charts |
| `charts/circuit_basis_hires.png` | High-resolution basis-gate circuit |
| `charts/circuit_pauli_hires.png` | High-resolution Pauli-evolution circuit |
| `slides/01_cover.png` … `08_engineering.png` | 2400 x 3000 PDF source slides |
| `video/title_card.png`, `video/end_card.png` | 3840 x 2160 video-card sources |
| `video/title_card_1080.png`, `video/end_card_1080.png` | Cards used by the final encode |

### Scientific provenance and generators

| Path | What it is |
| --- | --- |
| `source/h2_result.json` | Snapshot of the checked-in official result |
| `source/h2_result.png` | Snapshot of the checked-in convergence plot |
| `source/experiment_report.md` | Snapshot of the checked-in experiment report |
| `scripts/` | Archived Playwright, chart, slide and video generators |
| `scripts/README.md` | Build environment and regeneration order |

---

## What is real

- The dashboard screenshots and the video show a real `ExperimentResult`
  produced by the app's own H₂ pipeline.
- The energy values, optimizer history, circuit, atom counts and timings are
  read from that run. Nothing is hand-entered into the charts.
- The carousel and post cite the documented 16:36 UTC run. The video is a later
  live run with the same energies and checks.

## Claims boundary

This is a **reference implementation and validation harness**, not a quantum
advantage result.

- H₂/STO-3G is classically trivial.
- The simulation is an exact local statevector calculation; no quantum hardware
  or cloud service is used.
- The 4.44 x 10⁻¹⁶ Ha agreement is floating-point roundoff against exact
  diagonalization of the same qubit Hamiltonian, not a physical error bar.
- The independent PySCF FCI check supports the chemistry and mapping layers; it
  does not turn this into a hardware benchmark.
- Do not claim chemical accuracy for a realistic molecule, hardware performance,
  quantum supremacy or a new algorithm.

---

## Reproduce the science

```bash
git clone https://github.com/Abdelhakim-Baalla/quantum-vqe-chemistry-lab
cd quantum-vqe-chemistry-lab

python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,web]"

python -m quantum_vqe run-h2 --distance 0.735 --basis sto3g --plot
streamlit run app.py

pytest -q
ruff check .
ruff format --check .
```

The checked-in result does not need to match wall-clock timestamps or runtime
values byte-for-byte. It must match the energies, checks and configuration.

## Rebuild the media

The full build environment and command order are in
[`scripts/README.md`](scripts/README.md). The principal tools were Playwright
Chromium for real UI captures and video, matplotlib/PIL for charts and cards,
and ffmpeg/libx264 for the final H.264 encode.

After regenerating anything, update the checksums and verify the package:

```bash
(cd docs/launch && sha256sum -c MANIFEST.sha256)
```

### Preview note

Some Linux image viewers and chat previews add a false text shadow when
downscaling these images. The source PNGs are crisp. The video text was checked
against direct 1920 x 1080 browser captures; any apparent shadow in a downscaled
preview is a viewer artifact, not an encoding defect.

The repository is MIT licensed.
