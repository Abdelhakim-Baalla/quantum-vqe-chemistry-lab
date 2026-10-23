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

