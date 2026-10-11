# Architecture

The project is a small Python package with explicit boundaries between
chemistry, operator handling, optimization, validation and presentation. The
design goal is auditability: every scientific quantity in the final JSON can be
traced to a module and a computation.

## 1. Package layout

```text
quantum-vqe-chemistry-lab/
├── src/quantum_vqe/
│   ├── __init__.py       # public API: ExperimentConfig, ExperimentResult, run_h2_experiment
│   ├── __main__.py       # `python -m quantum_vqe`
│   ├── config.py         # validated, immutable, serializable configuration
│   ├── chemistry.py      # PySCF → ElectronicStructureProblem → FermionicOp → qubit Hamiltonian + UCCSD
│   ├── hamiltonian.py    # Hermiticity, exact diagonalization, statevector expectation, error helpers
│   ├── vqe.py            # explicit VQE loop, evaluation history, SciPy bookkeeping
│   ├── reference.py      # independent PySCF RHF+FCI and full-JW references
│   ├── experiment.py     # orchestration, checks, status and result assembly
│   ├── results.py        # JSON schema, atomic save, validated load
│   ├── plotting.py       # convergence plot (matplotlib imported lazily)
│   ├── versions.py       # Python/package/platform metadata
│   └── cli.py            # argparse CLI, console report, exit codes
├── app.py                 # Streamlit entry point (Quantum Lab)
├── webapp/
│   ├── __init__.py
│   ├── logic.py           # UI validation, run orchestration, history/exports
│   └── visuals.py         # real-result charts, molecule and circuit artifacts
├── .streamlit/
│   └── config.toml        # local dark theme and usage-stat privacy setting
├── tests/
│   ├── conftest.py       # small operator/circuit fixtures
│   ├── unit/             # fast tests, including web logic and AppTest wiring
│   └── integration/      # real H2/PySCF/Qiskit, CLI and real-UI-run tests
├── examples/
│   └── run_h2.py         # programmatic end-to-end example
├── docs/
│   ├── methodology.md
│   ├── architecture.md
│   ├── web_interface.md
│   ├── experiment_report.md
│   ├── roadmap.md
│   └── assets/           # checked-in official JSON result and convergence plot
├── .github/workflows/ci.yml
├── pyproject.toml
├── README.md
└── LICENSE
```

## 2. Data flow

```text
                       ExperimentConfig
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ chemistry.py                                                │
│  PySCFDriver.run()                                          │
│    → ElectronicStructureProblem                             │
│    → FermionicOp (electronic Hamiltonian)                   │
│    → ParityMapper / JordanWignerMapper                      │
│    → SparsePauliOp                                          │
│    → HartreeFock circuit + UCCSD ansatz                     │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
     hamiltonian.py     reference.py       vqe.py
     Hermiticity        PySCF RHF+FCI      StatevectorEstimator
     exact eigvalsh     full-JW eigvalsh   SciPy minimize
              │               │                │
              └───────────────┼────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ experiment.py                                               │
│  energy bookkeeping (electronic + nuclear)                  │
│  error calculations                                         │
│  scientific checks → status                                 │
│  ExperimentResult assembly                                  │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴────────────────┐
              ▼                                ▼
        results.py                        plotting.py
        atomic JSON save                  convergence PNG
              │                                │
              └───────────────┬────────────────┘
                              ▼
              ┌───────────────┴────────────────┐
              ▼                                ▼
           cli.py                     app.py + webapp/
      console report, exit code        Streamlit dashboard
                                       ├─ validates UI values
                                       ├─ calls build_chemistry() and
                                       │  run_h2_experiment(chemistry=...)
                                       ├─ precomputes circuit artifacts
                                       └─ displays/export the real result
```

The chemistry pipeline is the only place that talks to PySCF through Qiskit
Nature. `vqe.py` receives already-mapped operators and circuits, so it can be
tested with tiny synthetic Hamiltonians. `reference.py` deliberately bypasses
Qiskit Nature for the FCI cross-check and uses PySCF directly.

## 3. Module responsibilities

### `config.py`

`ExperimentConfig` is a frozen dataclass. It validates and normalizes:

- bond length, basis, charge and spin,
- mapping (`parity` or `jordan-wigner`),
- two-qubit reduction (default on for parity, forbidden for Jordan–Wigner),
- optimizer name and tolerance (with per-optimizer defaults),
- iteration cap, initial-point mode and seed,
- accuracy and reference tolerances.

`geometry_angstrom`, `expected_num_qubits()` and `summary()` derive values from
the validated configuration. `to_dict()` / `from_dict()` make the
configuration round-trippable and reject unknown fields.

### `chemistry.py`

`build_chemistry(config)` returns a `ChemistryData` record containing the
problem, fermionic and qubit Hamiltonians, mapper, Hartree–Fock circuit,
UCCSD ansatz, nuclear repulsion, particle/orbital counts and timings.

It enforces three invariants before returning:

1. the mapped Hamiltonian has the qubit count expected from the configuration,
2. the ansatz and Hamiltonian act on the same number of qubits,
3. the ansatz has at least one variational parameter.

`_extract_electronic_hamiltonian()` isolates the Qiskit Nature 0.8 tuple/dict
return shape so the rest of the code does not depend on that API detail.

### `hamiltonian.py`

Pure operator and energy helpers:

- `check_hermitian()` builds the dense matrix for up to 12 qubits and compares
  it with its adjoint; larger operators fall back to checking that Pauli
  coefficients are real.
- `exact_ground_state()` uses dense `eigvalsh` up to 1024 dimensions and sparse
  `eigsh` above that.
- `expectation_from_statevector()` is a second, independent Qiskit code path
  used by tests to validate the estimator.
- `compare_energies()` computes signed gaps and absolute errors.
- `pauli_term_records()` serializes the Hamiltonian for JSON.

### `vqe.py`

`VQE` owns the cost function and the optimization loop. It validates qubit and
parameter counts, wraps the estimator call, records every evaluation, and maps
SciPy's result into `VQEResult`. Optimizer-specific options are set in one
place, `_scipy_options()`.

The loop is intentionally not hidden behind a solver class. The history is the
primary evidence for convergence, and it is serialized unchanged.

### `reference.py`

`compute_pyscf_fci()` builds a fresh PySCF molecule and runs RHF + FCI with
`conv_tol=1e-10` and `max_cycle=200`. Failures are returned as an unavailable
reference with an error message rather than crashing the experiment; the
orchestrator then marks the dependent checks as failed.

`full_jordan_wigner_reference()` maps the same fermionic Hamiltonian with
Jordan–Wigner and diagonalizes it in the full Hilbert space. It is only called
for parity runs.

### `experiment.py`

`run_h2_experiment()` is the orchestrator. It:

1. builds chemistry,
2. checks Hermiticity and raises if the Hamiltonian is not Hermitian,
3. diagonalizes the same qubit Hamiltonian,
4. computes the independent PySCF FCI reference,
5. computes the full-JW reference when applicable,
6. evaluates the Hartree–Fock baseline,
7. runs VQE,
8. adds nuclear repulsion and computes errors,
9. evaluates all scientific checks,
10. assembles `ExperimentResult` with warnings and timings.

`determine_status()` is deliberately conservative: `success` requires that no
performed check is `False`. `None` means not applicable. A missing independent
reference is never silently treated as a pass.

### `results.py`

`ExperimentResult` is the JSON schema. It validates the schema version and the
status value, converts NumPy scalars, rejects non-finite floats, and writes
atomically via a temporary file followed by `replace()`. `load()` rejects
unknown or missing fields so schema drift is visible.

### `plotting.py`

`plot_convergence()` accepts either `EnergyEvaluation` objects or the JSON
dictionary form. It plots raw cost-function evaluations and a best-so-far step
curve, plus exact and Hartree–Fock reference lines. Matplotlib is imported
lazily and forced to the `Agg` backend, so importing the numerical modules does
not require a display.

### `cli.py`

The CLI is an `argparse` front end:

- `run-h2` is the only experiment,
- `--json` overrides the timestamped default path,
- `--plot` writes a PNG next to the JSON,
- `--mapping jordan-wigner` forces four qubits and rejects `--reduce`,
- invalid configuration returns exit code 2,
- failed scientific checks return exit code 1,
- successful runs return exit code 0.

The console report is generated from the same `ExperimentResult` that is saved,
so the printed and stored values cannot diverge.

### `webapp/` and `app.py`

The Streamlit interface is deliberately separated from the scientific package:

- `app.py` owns page configuration, CSS, widgets, tabs, error surfaces and
  downloadable output. It does not contain VQE or chemistry code.
- `webapp/logic.py` validates form values, constructs the existing
  `ExperimentConfig`, calls `build_chemistry()` and then
  `run_h2_experiment(config, chemistry=chemistry)`, and handles history and
  export. It imports no Streamlit and can be unit-tested directly.
- `webapp/visuals.py` derives charts, molecule labels, parameter tables and
  circuit images from real result records. Circuit drawing is performed during
  the run, not during later renders, because Qiskit circuit decomposition is not
  safely reusable across Streamlit's script-run threads in this environment.
  The resulting PNG bytes and dataframes are stored in `CircuitArtifacts`.

The optional `chemistry=` argument keeps one chemistry build and one ansatz
object in the UI path. The default CLI call still builds chemistry inside
`run_h2_experiment`, so CLI behavior is unchanged. The circuit shown in the UI
is therefore the executed ansatz, not a second decorative circuit.

The web extra installs Streamlit, pandas, Altair and `pylatexenc` (needed by
Qiskit's Matplotlib circuit drawer). The scientific package has no dependency on
any of them.

## 4. Result schema

The top-level JSON sections are stable and versioned (`schema_version: "1.0"`):

| Section | Contents |
| --- | --- |
| `experiment`, `status`, `created_utc` | identity and outcome |
| `config` | fully resolved run configuration |
| `molecule` | geometry, basis, particle/orbital/qubit counts, nuclear repulsion |
| `hamiltonian` | mapping, reduction description, Pauli terms, Hermiticity report |
| `ansatz` | UCCSD, qubit/parameter counts, parameter names, reference state |
| `optimizer`, `simulator` | method and simulation assumptions |
| `energies_hartree` | HF, VQE, exact-qubit, PySCF FCI and full-JW energies |
| `errors_hartree` | absolute errors and signed variational gap |
| `checks` | booleans and `null` for not-applicable checks |
| `check_tolerances_hartree` | every tolerance used by the checks |
| `references` | exact diagonalization, FCI and full-JW details |
| `optimization` | full evaluation history, parameters, counts, message |
| `timing_seconds` | chemistry, diagonalization, FCI, JW, VQE, plot, total |
| `software` | Python, platform and package versions |
| `warnings`, `artifacts` | missing-reference notices and output paths |

## 5. Error boundaries

| Error | Raised by | CLI behavior |
| --- | --- | --- |
| `ValueError` | configuration and input validation | print message, exit 2 |
| `ChemistryError` | integral generation or mapping failure | print message, exit 2 |
| `VQEError` | estimator or optimizer failure | print message, exit 2 |
| `ExperimentError` | non-Hermitian Hamiltonian or orchestration failure | print message, exit 2 |
| `OSError` | JSON write failure | print message, exit 2 |
| failed checks | scientific validation | print report, exit 1 |

A failed plot is a warning and returns exit code 2 after the JSON has been
written, so the numerical result is not lost.

## 6. Testing architecture

The suite is split by the `integration` pytest marker:

- **Unit tests** (`tests/unit/`) use tiny synthetic operators and circuits.
  They cover configuration validation, Hermiticity, exact diagonalization,
  energy comparison, estimator/statevector agreement, the VQE loop, JSON
  round-trips, status logic, plotting, web validation and exports, real-result
  chart/circuit artifacts, and Streamlit `AppTest` UI wiring. They do not run
  the PySCF chemistry pipeline.
- **Integration tests** (`tests/integration/`) run the real H₂ pipeline with
  PySCF and Qiskit Nature. They check dimensions, energies, references,
  optimizer variants, parity/JW mappings, JSON round-trip, plotting, CLI
  subprocess behavior, and a real H₂ run through the Streamlit UI harness.

The integration modules are skipped automatically if PySCF or Streamlit is
unavailable. CI installs the full `.[dev,web]` extra, so both core and UI tests
run there. In the tested environment the suite reports 99 unit and 17
integration tests (116 total), with 89% statement coverage for `quantum_vqe`.

