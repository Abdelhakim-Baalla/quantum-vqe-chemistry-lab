# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Planned

- QAOA Max-Cut as a separate, documented experiment.
- Optional shot-based and noisy simulation paths.
- Additional molecules beyond H₂/STO-3G.

## [0.1.0] - 2026-10-23

### Added

- Reproducible H₂/STO-3G VQE pipeline with a UCCSD ansatz, parity mapping,
  two-qubit Z₂ tapering and exact statevector execution.
- Independent validation against exact qubit diagonalization, full
  Jordan–Wigner diagonalization and PySCF RHF + FCI.
- Checked-in official result (`docs/assets/h2_result.json`) and convergence plot,
  with full optimizer history, timings, software versions and ten scientific
  checks.
- CLI (`python -m quantum_vqe run-h2`) with JSON and convergence-plot output.
- Local Streamlit **Quantum Lab** interface with real-result-only metrics,
  molecular information, circuit explorer, convergence analysis, run history and
  JSON/CSV export.
- Light/Dark appearance switcher. Light remains the default; dark mode includes
  theme-aware charts, molecule and circuit diagrams.
- Advanced **Dashboard** tab with twelve run-derived metrics and six real-data
  views: log energy gap, step improvement, parameter trajectories, correlation
  energy ledger, Hamiltonian coefficients and parameter-correlation matrix.
- Persistent sidebar reopen control after collapsing the sidebar.
- Professional repository documentation: architecture, methodology, experiment
  report, web-interface guide, contribution guide, security policy, citation
  metadata and GitHub issue/PR templates.
- Launch media package under `docs/launch/`: 8-page 4:5 carousel, 53-second
  silent 1080p walkthrough with on-screen captions, poster, SRT captions,
  screenshots, LinkedIn copy, alt text and checksums. All media is derived from
  the checked-in official run.

### Fixed

- Sidebar could not be reopened after collapse because the Streamlit expand
  control is hosted inside the toolbar element that the theme had hidden.
- Dark-mode headings and form controls inherited light-theme colors.
- README and architecture notes described the interface as dark-only; the
  default is now explicitly the approved light theme.

### Scientific result

The official H₂ run at 0.735 Å reaches a VQE total energy of
−1.1373060357533986 Ha. Exact diagonalization gives −1.137306035753399 Ha and
independent PySCF FCI gives −1.1373060357534004 Ha; the absolute VQE error is
4.440892098500626 × 10⁻¹⁶ Ha. Ten of ten checks pass. This is a validation
result on a two-qubit Hamiltonian, not a quantum-advantage claim.

[Unreleased]: https://github.com/Abdelhakim-Baalla/quantum-vqe-chemistry-lab/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Abdelhakim-Baalla/quantum-vqe-chemistry-lab/releases/tag/v0.1.0
