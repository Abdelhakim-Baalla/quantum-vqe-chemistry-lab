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

