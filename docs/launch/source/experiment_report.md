# Experiment report: H₂ VQE in the STO-3G basis

This report records the official H₂ run that is checked into this repository.
All numbers below are taken from
[`docs/assets/h2_result.json`](assets/h2_result.json), which was written by the
experiment itself. No energy was hard-coded into the code or copied into the
calculation.

## 1. Summary

| Item | Value |
| --- | --- |
| Status | **SUCCESS** |
| Created (UTC) | `2026-10-23T16:36:19+00:00` |
| Molecule | H₂ |
| Bond length | 0.735 Å |
| Basis | STO-3G |
| Mapping | Parity with two-qubit Z2 reduction |
| Qubits | 2 |
| Pauli terms | 5 |
| Ansatz | UCCSD, Hartree–Fock reference, 3 parameters |
| Optimizer | L-BFGS-B, tolerance `1e-8`, max 500 iterations |
| Simulator | Qiskit `StatevectorEstimator`, exact statevector, no shots |
| VQE total energy | **−1.1373060357533986 Ha** |
| Exact qubit total energy | **−1.137306035753399 Ha** |
| PySCF FCI total energy | **−1.1373060357534004 Ha** |
| Absolute VQE error | **4.440892098500626 × 10⁻¹⁶ Ha** |
| Optimizer evaluations | 24 cost-function calls, 4 iterations |
| Wall clock | 0.632 s |

The VQE result agrees with exact diagonalization of the same qubit Hamiltonian
to machine precision. The exact qubit result agrees with an independent PySCF
RHF + FCI calculation to \(1.33\times10^{-15}\) Ha, and the parity-reduced
Hamiltonian agrees with a full four-qubit Jordan–Wigner calculation to
\(8.88\times10^{-16}\) Ha.

This is a **validation result**, not a claim of quantum advantage or hardware
performance. The two-qubit Hamiltonian is classically trivial; the scientific
value is the complete, reproducible workflow and the independent checks.

## 2. Artifacts

| Artifact | Path |
| --- | --- |
| Machine-readable result | [`docs/assets/h2_result.json`](assets/h2_result.json) |
| Convergence plot | [`docs/assets/h2_result.png`](assets/h2_result.png) |
| Source code | [`src/quantum_vqe/`](../src/quantum_vqe/) |
| Methodology | [`docs/methodology.md`](methodology.md) |

The JSON contains the full optimization history, all Pauli terms, all checks,
the resolved tolerances, phase timings and software versions.

## 3. Environment

The run was executed in the project's isolated Python 3.12 environment:

| Component | Version |
| --- | --- |
| Python | 3.12.14 (CPython) |
| Platform | Linux 7.2.5-3-omarchy, x86_64, glibc 2.44 |
| `quantum-vqe-chemistry-lab` | 0.1.0 |
| Qiskit | 2.6.1 |
| Qiskit Nature | 0.8.0 |
| Qiskit Algorithms | 0.4.0 |
| PySCF | 2.14.0 |
| NumPy | 2.5.4 |
| SciPy | 1.18.1 |
| Matplotlib | 3.11.2 |

Qiskit Algorithms is installed in the environment and recorded by the version
collector, but the VQE loop itself is implemented directly in
`src/quantum_vqe/vqe.py`; it does not use `qiskit_algorithms`' VQE class.

The local dashboard was tested with Streamlit 1.66.1, pandas 2.3.3, Altair 6.3.0
and `pylatexenc` 2.11. These are UI-layer dependencies; the official energy
run does not depend on them.

The exact Python executable path is recorded in the JSON for local
reproducibility.

## 4. Command

From the project root:

```bash
.venv/bin/python -m quantum_vqe run-h2 \
  --distance 0.735 \
  --basis sto3g \
  --json docs/assets/h2_result.json \
  --plot
```

This resolves to the default parity mapping with two-qubit reduction, UCCSD,
L-BFGS-B, tolerance `1e-8`, Hartree–Fock initial point and seed 7. The resolved
configuration is stored in the `config` section of the JSON, so the defaults
cannot silently drift from the report.

The installed console entry point is equivalent:

```bash
quantum-vqe run-h2 --distance 0.735 --basis sto3g
```

## 5. Configuration and model

| Setting | Value |
| --- | --- |
| Geometry | `H 0.0 0.0 0.0; H 0.0 0.0 0.735000000000` Å |
| Charge / spin (2S) | 0 / 0 |
| Electrons | 2, with \((N_\alpha,N_\beta)=(1,1)\) |
| Spatial / spin orbitals | 2 / 4 |
| Mapping | Parity, then two-qubit Z2 tapering |
| Qubits | 2 |
| Pauli terms | 5 |
| Ansatz | UCCSD, one repetition |
| Parameters | 3 (`t[0]`, `t[1]`, `t[2]`) |
| Initial point | Hartree–Fock, all-zero angles |
| Optimizer | L-BFGS-B, `gtol=1e-8`, `maxiter=500` |
| Accuracy target | `1e-6` Ha |
| Variational tolerance | `1e-8` Ha |
| Reference tolerance | `1e-6` Ha |
| Hermiticity tolerance | `1e-10` |

The reduced Hamiltonian recorded in the JSON is

\[
\hat H_{\mathrm{elec}} =
-1.0523732457728596\, II
+0.39793742484317934\, IZ
-0.3979374248431794\, ZI
-0.011280104256235268\, ZZ
+0.18093119978423144\, XX .
\]

The maximum Hermiticity asymmetry is `0.0`, so the Hamiltonian is exactly
Hermitian in double precision for this representation.

## 6. Energy results

All values are in Hartree. "Electronic" excludes nuclear repulsion; "total"
includes it. The nuclear repulsion is `0.7199689944489797` Ha.

| Quantity | Electronic | Total |
| --- | ---: | ---: |
| Hartree–Fock (ansatz at zero angles) | −1.8369679912029833 | −1.1169989967540035 |
| **VQE** | **−1.8572750302023782** | **−1.1373060357533986** |
| Exact diagonalization (same 2-qubit Hamiltonian) | −1.8572750302023788 | −1.137306035753399 |
| PySCF RHF | −1.8369679912029837 | −1.116998996754004 |
| PySCF FCI (independent) | −1.8572750302023802 | −1.1373060357534004 |
| Full Jordan–Wigner (4 qubits) | −1.8572750302023797 | — |

The exact 2-qubit Hamiltonian has a first excited energy of
`-1.2445845498133266` Ha (electronic), giving a gap of
`0.6126904803890523` Ha. The full four-qubit Jordan–Wigner spectrum has a first
excited energy of `-1.2563390730032498` Ha and a gap of
`0.60093595719913` Ha. These gaps are recorded in the JSON and are not used as
VQE targets; the experiment is a ground-state calculation.

## 7. Error analysis

| Error | Value (Ha) | Meaning |
| --- | ---: | --- |
| `absolute_vqe_vs_exact_total` | \(4.440892098500626\times10^{-16}\) | headline VQE accuracy |
| `signed_variational_gap_electronic` | \(+6.661338147750939\times10^{-16}\) | VQE above exact by numerical noise |
| `absolute_exact_vs_pyscf_fci_total` | \(1.3322676295501878\times10^{-15}\) | mapping/integral cross-check |
| `absolute_hf_vs_pyscf_rhf_electronic` | \(4.440892098500626\times10^{-16}\) | HF reference cross-check |
| `absolute_parity_vs_full_jw_electronic` | \(8.881784197001252\times10^{-16}\) | reduction cross-check |

The signed variational gap is positive, as required for an approximate trial
state. It is \(6.66\times10^{-16}\) Ha, which is below the `1e-8` Ha
variational tolerance and is floating-point noise, not a physical violation.

The absolute VQE error is \(4.44\times10^{-16}\) Ha, about ten orders of
magnitude below the `1e-6` Ha target. This is expected here: the UCCSD ansatz
can represent the exact ground state of this two-electron, two-orbital problem,
and the simulator is exact. The result should not be read as "VQE is always
this accurate"; it is a best-case validation of the implementation.

## 8. Optimization behavior

| Field | Value |
| --- | --- |
| Optimizer | L-BFGS-B |
| Initial energy | −1.8369679912029833 Ha |
| Final energy | −1.8572750302023782 Ha |
| Energy decrease | 0.0203070389993949 Ha |
| Initial parameters | `[0.0, 0.0, 0.0]` |
| Final parameters | `[2.34784170419411e-09, -2.599610718135767e-08, -0.11176850357089839]` |
| Converged | `true` |
| SciPy success | `true` |
| Message | `CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH` |
| Status code | `0` |
| `nfev` | 24 |
| `nit` | 4 |
| `njev` | 6 |
| Recorded evaluations | 24 |
| VQE wall time | 0.19616324407979846 s |

The two single-excitation angles remain at approximately \(2.3\times10^{-9}\)
and \(-2.6\times10^{-8}\) rad. The double-excitation angle is
\(-0.11176850357089839\) rad and carries essentially all of the correlation
energy. This is consistent with Brillouin's theorem for the RHF reference.

The optimization history contains 24 cost-function calls. Some are
finite-difference probes or line-search trial points and can be worse than the
current best (for example, evaluation 4 is about −0.8744 Ha). The convergence
plot therefore shows the raw evaluations together with a best-so-far curve;
the best-so-far curve is monotone and ends at the exact energy.

## 9. Scientific checks

All ten checks passed:

| Check | Result |
| --- | --- |
| `hamiltonian_is_hermitian` | PASS |
| `ansatz_qubit_count_matches_hamiltonian` | PASS |
| `mapped_qubit_count_matches_configuration` | PASS |
| `optimizer_converged` | PASS |
| `optimizer_reduced_energy` | PASS |
| `variational_principle` | PASS |
| `energy_accuracy_target_met` | PASS |
| `hf_matches_pyscf_rhf` | PASS |
| `exact_matches_pyscf_fci` | PASS |
| `parity_reduction_matches_full_jw` | PASS |

The status is `success` because no check is `False`. A `None` value would mean
"not applicable" (for example, the parity/JW cross-check in a Jordan–Wigner
run) and would not count as a pass.

## 10. Phase timings

| Phase | Time (s) |
| --- | ---: |
| Chemistry (PySCF integrals, mapping, UCCSD construction) | 0.17216657707467675 |
| Exact diagonalization | 0.00022521300707012415 |
| PySCF FCI | 0.23108672793023288 |
| Full Jordan–Wigner diagonalization | 0.0004148520529270172 |
| VQE optimization | 0.19616324407979846 |
| Plot | 0.15403200406581163 |
| **Total** | **0.6320048500783741** |

These timings are for this machine and this exact run; they are not benchmark
claims.

## 11. Verification performed

The following commands were executed in the project environment.

```bash
# Fast unit tests
.venv/bin/pytest -q -m "not integration"

# Real H2/PySCF/Qiskit/CLI integration tests
.venv/bin/pytest -q -m integration

# Lint and formatting
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

In the current repository, the suite reports **106 passed** for the unit tests
and **17 passed** for the integration tests (123 total), with **89% statement
coverage** for the `quantum_vqe` package. CLI subprocess behavior and the
server-side Streamlit AppTest harness are tested directly but are not attributed
to the in-process coverage total. The integration suite covers:

- the default H₂ run and all scientific checks,
- molecular dimensions and nuclear repulsion,
- agreement with exact, FCI and full-JW references,
- JSON round-trip and convergence plotting,
- all five supported optimizers,
- parity mapping with and without two-qubit reduction,
- Jordan–Wigner mapping,
- CLI JSON/plot output and exit codes,
- rejection of invalid distance and invalid `--reduce`/JW combinations,
- Streamlit `AppTest` startup, validation, failure and export wiring,
- a real H₂ experiment executed through the local UI, with its actual circuit
  artifacts and displayed metrics checked against the scientific result.

The automated suite verifies the UI with Streamlit's server-side `AppTest`
harness, and the local server was started on `127.0.0.1` and checked through its
`/_stcore/health` endpoint and HTTP page response. This checks execution
behavior rather than only pixels. The launch screenshots and video were captured
separately with Playwright against the real local server; they are not part of
the automated test matrix and do not replace cross-browser visual regression
testing.

Additional smoke runs executed for this report:

| Run | Result |
| --- | --- |
| CLI default with JSON and plot | SUCCESS, 2 qubits |
| CLI Jordan–Wigner | SUCCESS, 4 qubits, 15 Pauli terms, error \(4.441\times10^{-16}\) Ha |
| CLI BFGS | SUCCESS, 20 evaluations, error \(3.553\times10^{-15}\) Ha |
| CLI seeded random start (`--seed 11`) | SUCCESS, 36 evaluations, error \(2.618\times10^{-12}\) Ha |
| `python examples/run_h2.py` | SUCCESS, wrote JSON and PNG under `results/` |
| Invalid distance and invalid `--reduce` with JW | exit code 2, clear error message |

The exact commands and final results are also listed in the top-level README.

## 12. Known warnings

The integration suite emits upstream `DeprecationWarning`s from Qiskit Nature
0.8: its `BlueprintCircuit` and `NLocal` subclasses are deprecated in Qiskit
2.1 and will be removed in Qiskit 3.0. The warnings come from library code, do
not affect the computed energies or checks, and are not suppressed by this
project. They are recorded here so a future dependency upgrade can address
them rather than having them appear as an unexplained test failure.

## 13. What is implemented, executed, tested, and unverified

### Implemented

- PySCF/Qiskit Nature integral generation for H₂/STO-3G.
- Parity and Jordan–Wigner mappings, with optional two-qubit parity reduction.
- UCCSD ansatz with Hartree–Fock reference.
- Explicit VQE loop with `StatevectorEstimator`, SciPy optimizers and complete
  evaluation history.
- Exact diagonalization, full-JW cross-check and independent PySCF RHF + FCI.
- Scientific checks, conservative status logic, JSON schema, atomic save/load,
  convergence plotting and CLI.
- Local Streamlit dashboard with real experiment execution, actual circuit
  rendering, convergence analysis, session history, JSON/CSV export and
  learning mode.
- Unit and integration tests, example script, CI workflow and documentation.

### Executed

- The official H₂ run whose numbers appear in this report.
- The full unit and integration test suites.
- Lint and format checks.
- CLI variants for JSON/plot output, Jordan–Wigner mapping, optimizer selection
  and invalid-input handling.
- A real H₂ experiment through Streamlit `AppTest`, including circuit artifact
  generation and a normal post-run rerun.
- Local Streamlit server startup on `127.0.0.1`, with `/_stcore/health` and the
  HTTP page response checked.

### Tested

- Hermiticity, qubit counts, variational principle, energy bookkeeping,
  optimizer convergence, reference agreement and no-false-success status logic.
- Determinism of the default Hartree–Fock start and reproducibility of seeded
  random starts.
- JSON schema validation and plotting output.
- Streamlit `AppTest` startup, validation, failure and export wiring, plus a
  real result rendered through the UI and a real-UI-run integration test.

### Unverified / out of scope

- **Automated cross-browser visual regression.** Playwright was used against the
  local Chromium build for the launch screenshots and screen recording, but no
  cross-browser screenshot-diff or layout-regression suite runs in CI. The
  server-side AppTest harness remains the automated UI check.
- **GitHub Actions execution.** The workflow is configured for Python 3.11 and
  3.12 and its commands pass locally; the repository badge and Actions run are
  the authoritative remote result.
- **Quantum hardware.** No IBM Quantum account, cloud service, hardware,
  shot noise, gate error, decoherence or readout error is used.
- **Shot-based simulation.** The estimator is exact statevector; finite-shot
  statistics are not studied.
- **Other molecules, basis sets and bond lengths.** The CLI accepts a basis and
  distance, but only H₂/STO-3G at 0.735 Å is validated by the official run and
  the integration assertions.
- **Excited states, dynamics and finite temperature.** Only the electronic
  ground state is computed.
- **Global optimality on non-trivial problems.** The optimizer is local and
  the ansatz is fixed.
- **QAOA Max-Cut.** Not implemented in this version; it is listed as future
  work in [`docs/roadmap.md`](roadmap.md).
- **Quantum advantage.** Not claimed and not possible to demonstrate with this
  classically trivial two-qubit problem.

## 14. Reproduction notes

A fresh environment can reproduce the workflow with:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev,web]"
python -m quantum_vqe run-h2 --distance 0.735 --basis sto3g --plot
```

Last-bit floating-point values may differ across BLAS/LAPACK builds, Python
patch versions or package versions. The JSON records the versions used for this
run so such differences are visible. The scientific checks use tolerances of
`1e-6` Ha for references and `1e-8` Ha for the variational principle, not
bitwise equality.
