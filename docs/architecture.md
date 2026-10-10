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

