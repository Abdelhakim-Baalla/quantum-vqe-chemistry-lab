# Quantum Lab — LinkedIn launch copy

Prepared 2026-10-23. Every number in this package traces to the checked-in
official run in `docs/assets/h2_result.json` in the public repository.

The video is a separate live capture. It produces the same energies with a later
timestamp. The carousel uses the documented **2026-10-23 16:36 UTC** run.

---

## Main post — carousel

Copy everything inside the block. Character count: 2,288 (2,395 with hashtags),
inside LinkedIn's 3,000-character limit.

```text
A two-qubit VQE is not a hard problem. Reproducing one from PySCF integrals to a checked JSON artifact is the part worth sharing.

I built a reference implementation for H₂/STO-3G and a local Quantum Lab workbench around it. The variational quantum eigensolver (VQE) total energy is −1.1373060357533986 Ha. Exact diagonalization of the same qubit Hamiltonian gives −1.137306035753399 Ha. The absolute difference is 4.44 × 10⁻¹⁶ Ha — floating-point roundoff, not a physical error claim.

The point is not the number. It is the chain:

1. PySCF integrals → fermionic Hamiltonian.
2. Parity mapping + Z₂ tapering → 2 qubits, 5 Pauli terms.
3. UCCSD on a Hartree–Fock reference → 3 parameters.
4. L-BFGS-B with Qiskit's exact StatevectorEstimator → 24 evaluations, 4 iterations.
5. Exact diagonalization + independent PySCF FCI → 10/10 checks passed.

Independent agreement checks:
• VQE total vs exact diagonalization: 4.44 × 10⁻¹⁶ Ha.
• HF vs PySCF RHF, electronic: 4.44 × 10⁻¹⁶ Ha.
• Parity + Z₂ vs full Jordan-Wigner, electronic: 8.88 × 10⁻¹⁶ Ha.
• Exact qubit vs PySCF FCI, total: 1.33 × 10⁻¹⁵ Ha.

What I am not claiming: quantum advantage, hardware performance, or chemical accuracy for a chemically realistic model. H₂/STO-3G is classically trivial. This is a reproducibility and validation artifact — the two-qubit Hamiltonian is small precisely so every step can be inspected.

The workbench is a local Streamlit interface over the same scientific layer as the CLI:
• real execution, no placeholder energies;
• a dashboard with twelve run-derived metrics and six diagnostic views;
• electronic and total energies kept separate;
• the raw optimizer trace, with no smoothing or synthetic points;
• circuit diagrams rendered from the actual UCCSD ansatz object;
• JSON/CSV export and a documented run.

123 automated tests. CI green on Python 3.11 and 3.12. Open source under MIT. No cloud, no quantum hardware, no mock data.

The result is the easy part. The evidence is the product.

8-page carousel below: protocol → architecture → dashboard → result → optimizer trace → executed circuit → engineering checks.

If you work on VQE, quantum chemistry, or scientific software, I would value the sharpest technical critique — especially on where the validation boundary should be drawn.
```

**Hashtags** (append after the post, separated by a blank line):

```text
#QuantumComputing #VQE #QuantumChemistry #Qiskit #PySCF #OpenSource #Reproducibility #ScientificComputing
```

**Video swap:** replace the carousel line with:

```text
53-second live walkthrough below: run → dashboard → result → optimizer trace → executed circuit.
```

---

## Shorter variant — quick share or video post

Character count: 667. Use this when the carousel is not attached, or when the
post needs to stay above the fold.

```text
A two-qubit VQE is not a hard problem. Making every step from PySCF integrals to a checked JSON artifact inspectable is the part worth sharing.

H₂ / STO-3G / UCCSD / parity + Z₂:
• VQE total: −1.1373060357533986 Ha
• Exact diagonalization: −1.137306035753399 Ha
• Absolute difference: 4.44 × 10⁻¹⁶ Ha
• 10/10 checks, 123 tests, CI green

Local exact-statevector simulation. No hardware, no cloud, no mock data, no quantum-advantage claim.

Open source (MIT). The workbench exposes the raw optimizer trace, the executed ansatz, and the validation report. Repo in the first comment.

#QuantumComputing #VQE #QuantumChemistry #Qiskit #PySCF #OpenSource #Reproducibility
```

---

## Video-specific caption

Use with `video/Quantum_Lab_Launch.mp4` when the video is the primary asset.
Character count: 476.

```text
53 seconds inside the local Quantum Lab: run the H₂ VQE, inspect the dashboard, read the energy result, follow the raw optimizer trace, and render the executed two-qubit ansatz.

The documented run: −1.1373060357533986 Ha total, 4.44 × 10⁻¹⁶ Ha from exact diagonalization, 10/10 checks, 123 tests.

No hardware. No cloud. No mock data. No quantum-advantage claim. Repo in the first comment.

#QuantumComputing #VQE #QuantumChemistry #Qiskit #PySCF #OpenSource #Reproducibility
```

---

## First comment — post immediately and pin

Character count: 416.

```text
Repo: https://github.com/Abdelhakim-Baalla/quantum-vqe-chemistry-lab
Checked-in result: docs/assets/h2_result.json
Report: docs/experiment_report.md

Reproduce:
python -m quantum_vqe run-h2 --distance 0.735 --basis sto3g
streamlit run app.py

The UI and CLI call the same scientific layer. The documented run is the source of the carousel numbers; the video is a separate live run with the same values. MIT licensed.
```

Do not put the repository URL in the post body. Keep the body focused on the
technical claim; put the link in the pinned first comment.

---

## LinkedIn document metadata

Use these when the upload form asks for a title or description.

**Document title**

```text
Quantum Lab — H₂ VQE, validated
```

**Document description**

```text
An 8-page technical walkthrough: protocol, architecture, live dashboard, energy result, raw optimizer trace, executed circuit, and engineering checks.
```

---

## Alt text

LinkedIn's image alt-text limit is 120 characters. Every description below is
within that limit.

| Asset | Alt text |
| --- | --- |
| `carousel/01_cover.png` | Cover: H₂ ground state validated to 4.44 × 10⁻¹⁶ Ha; 2 qubits, 3 parameters, 10/10 checks. |
| `carousel/02_protocol.png` | Protocol: six steps from H₂ geometry to independent FCI validation, with a two-qubit Hamiltonian. |
| `carousel/03_architecture.png` | Architecture: one scientific Python layer shared by the CLI and the Streamlit Quantum Lab interface. |
| `carousel/04_dashboard.png` | Dashboard: real H₂ VQE results, twelve metrics and six analytical views in the Quantum Lab. |
| `carousel/05_result.png` | Result: VQE, exact diagonalization and PySCF FCI agree at floating-point precision. |
| `carousel/06_convergence.png` | Convergence: 24 recorded evaluations, a line-search excursion and the best-so-far trace. |
| `carousel/07_circuit.png` | Circuit: executed two-qubit UCCSD ansatz with 3 parameters, depth 12 and 17 basis gates. |
| `carousel/08_engineering.png` | Engineering: 123 tests, 10/10 checks, CI green, MIT license, and repository call to action. |
| `carousel/Quantum_Lab_LinkedIn_Carousel.pdf` | Document: Quantum Lab, a reproducible H₂ VQE validated to 4.44e-16 Ha against exact diagonalization and PySCF FCI. |
| `video/Quantum_Lab_Launch.mp4` | Live Quantum Lab walkthrough: H₂ VQE run, dashboard, result, optimizer trace and executed circuit. |

If LinkedIn exposes only one alt-text field for the uploaded PDF, use the PDF
description above. If the eight PNGs are uploaded individually, use the
per-slide descriptions.

---

## Posting playbook

### Pre-publish checklist

- [ ] The PDF has 8 pages at 4:5; page 1 is readable at feed size.
- [ ] The main post is pasted in full; hashtags are at the end.
- [ ] No repository URL sits in the post body.
- [ ] Alt text is attached to the document or each image.
- [ ] The first comment is posted immediately and pinned.
- [ ] The repository link, JSON path, and report path all open.
- [ ] The video plays end-to-end; the SRT timing ends at 53.12 s.
- [ ] The post makes no quantum-advantage, hardware-performance, or
      chemical-accuracy claim.
- [ ] A named person will answer technical comments with specifics.

### Choose the format

1. **Carousel first.** Upload `carousel/Quantum_Lab_LinkedIn_Carousel.pdf` as a
   **document post**. LinkedIn treats documents as swipeable carousels and gives
   them strong dwell time. The PDF is 8 pages at 4:5, matching LinkedIn's
   recommended document aspect ratio.
2. **Video second.** Post `video/Quantum_Lab_Launch.mp4` natively, not as a
   YouTube link. Upload `video/Quantum_Lab_Launch_poster.jpg` as the thumbnail if
   LinkedIn asks. Upload `video/Quantum_Lab_Launch.srt` as captions if the
   composer supports it. The video is intentionally silent and already carries
   on-screen section labels.
3. Space the two posts **3–5 days apart**. Use the main post for the carousel
   and the video-specific caption for the video. Do not publish both with
   identical copy.

### Timing and distribution

- Post **Tuesday–Thursday, 08:00–10:00 local time**. Avoid Friday afternoon and
  weekends unless your audience is global and you have data showing otherwise.
- Keep the first two lines as the hook. LinkedIn collapses the rest behind
  "see more"; the current hook is intentionally specific and slightly
  contrarian.
- Add the first comment immediately and pin it. The repository link belongs
  there, not in the body.
- Use the eight hashtags in the main post. Do not add unrelated trending tags.
- Tag only people or organizations with a genuine technical connection. Do not
  use engagement pods or generic tagging.
- Reply to substantive comments with specifics. Link to the JSON/report when
  asked for evidence; avoid repeating marketing language.

### Discovery and SEO

- The post text contains the searchable terms: **variational quantum
  eigensolver**, **VQE**, **H₂**, **STO-3G**, **UCCSD**, **parity tapering**,
  **Z₂**, **Qiskit**, **PySCF**, **exact diagonalization**, **FCI**,
  **L-BFGS-B**, **reproducibility**, and **open source**.
- The document title and description repeat the primary terms without stuffing.
- Alt text describes the actual content, not a keyword list. This improves
  accessibility and gives LinkedIn additional context.
- The carousel first page is the hook; the last page is the CTA. Both are
  readable at feed size.
- The first comment contains the repository URL and the exact reproduction
  commands, which keeps the post body focused while still making the work
  discoverable.

### What not to claim

- Do **not** call this quantum advantage, quantum supremacy, or a hardware
  result.
- Do **not** say "zero error." The agreement is at the floating-point roundoff
  floor for this calculation.
- Do **not** claim chemical accuracy for a realistic molecule. H₂/STO-3G is a
  deliberately small, classically trivial benchmark.
- Do **not** describe the pipeline as a new algorithm. It is a reference
  implementation and validation harness around standard methods.
- Do **not** imply the video timestamp matches the documented run. The video is
  a separate live run; the values are identical, the timestamp is later.

---

## Fact sheet

| Item | Value |
| --- | --- |
| Experiment | H₂ VQE |
| Bond length | 0.735 Å |
| Basis | STO-3G |
| Ansatz | UCCSD, Hartree–Fock reference, 3 parameters |
| Qubit mapping | Parity + Z₂ tapering |
| Qubits | 2 |
| Pauli terms | 5 |
| Optimizer | L-BFGS-B, tolerance 1e-8, max 500 iterations |
| Simulator | Qiskit exact statevector, no shots, no noise |
| Evaluations / iterations | 24 / 4 |
| VQE total energy | −1.1373060357533986 Ha |
| Exact diagonalization total | −1.137306035753399 Ha |
| PySCF FCI total | −1.1373060357534004 Ha |
| Absolute VQE error | 4.440892098500626e-16 Ha |
| Scientific checks | 10 / 10 |
| Automated tests | 123 (106 unit + 17 integration) |
| CI | Python 3.11 and 3.12, GitHub Actions |
| License | MIT |
| Official run timestamp | 2026-10-23T16:36:19+00:00 |
| Software | Qiskit 2.6.1, qiskit-nature 0.8.0, qiskit-algorithms 0.4.0, PySCF 2.14.0, Python 3.12.14 |

**Repository:** <https://github.com/Abdelhakim-Baalla/quantum-vqe-chemistry-lab>

The electronic energies are kept separate from the total energies in the app and
the report. The headline number is the total energy, including nuclear
repulsion.
