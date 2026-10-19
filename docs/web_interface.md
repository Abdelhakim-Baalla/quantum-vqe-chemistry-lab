# Quantum Lab web interface

**Quantum Lab** is a local Streamlit dashboard for the validated H₂ VQE
experiment. It is an additional presentation and orchestration layer over the
same scientific code used by the CLI. It is not a second VQE implementation and
it does not contain demo energies, synthetic convergence points or a simulated
success state.

## 1. Local launch

From the repository root:

```bash
source .venv/bin/activate
streamlit run app.py
```

Streamlit prints a local URL, normally <http://localhost:8501>. The app is
bound to the local machine by default and has no authentication. Do not expose
it to a public network. No cloud account, API key, paid service or quantum
hardware is used.

If dependencies are missing, install the web extra:

```bash
uv pip install -e ".[dev,web]"
# or: python -m pip install -e ".[dev,web]"
```

## 2. What the dashboard contains

The sidebar exposes only options covered by the scientific validation suite:

- molecule: H₂,
- bond distance: 0.30–5.00 Å,
- basis: STO-3G,
- ansatz: UCCSD,
- mapping: parity with optional two-qubit Z₂ reduction, or Jordan–Wigner,
- classical optimizer: L-BFGS-B, BFGS, SLSQP, COBYLA or Nelder–Mead,
- maximum iterations,
- initial point: Hartree–Fock or seeded random,
- optional output directory for saved JSON.

The five tabs are:

1. **Experiment** — real molecular information, electronic and total energies,
   absolute error in Ha and mHa, nuclear repulsion, initial energy, evaluation
   count, convergence status, timing, scientific checks and a variational-
   principle explanation.
2. **Quantum circuit** — the actual UCCSD ansatz used by the run, with qubit
   count, depth, gate counts, optimized parameters and three decomposition
   levels: as built, Pauli evolution, and basis gates.
3. **Convergence** — an interactive Altair chart of recorded cost-function
   evaluations, a best-so-far trace, exact and Hartree–Fock reference lines, and
   a table of the same recorded points.
4. **History** — completed runs in the current browser session, comparison
   table, save-to-JSON, and JSON/CSV downloads. No database is used.
5. **Learn** — concise explanations of qubits, molecular Hamiltonians,
   fermion-to-qubit mappings, parameterized circuits, classical optimization,
   exact diagonalization, simulation versus hardware, and the variational
   principle.

The dashboard does not display energy placeholders. Before a run, it states
that no energies are available. After a run, every displayed energy, error,
parameter, convergence point and check is read from the `ExperimentResult`
returned by the scientific layer.

## 3. Scientific boundary

The call chain is:

```text
app.py (Streamlit widgets and rendering)
   │
   ▼
webapp/logic.py
   ├─ validates UI values
   ├─ builds ExperimentConfig through the existing class
   ├─ calls build_chemistry(config)
   ├─ calls run_h2_experiment(config, chemistry=chemistry)
   └─ stores the returned ExperimentResult and UI artifacts
   │
   ▼
src/quantum_vqe/  (unchanged scientific implementation)
```

`run_h2_experiment` accepts an optional pre-built `ChemistryData` object. The UI
uses that hook so the circuit it displays is the exact ansatz object passed to
the VQE, not a separately reconstructed illustration. When the optional object
is omitted, the CLI path builds chemistry itself exactly as before.

`src/quantum_vqe/` does not import Streamlit. `webapp/logic.py` does not import
Streamlit either; it is testable as ordinary Python. Streamlit-specific layout
stays in `app.py`.

## 4. Rendering and thread-safety

Streamlit executes a script run in a script-run thread and may use a different
thread for the next rerun. Qiskit's compiled extensions and circuit
decomposition are not safely used across those threads in this environment:
importing Qiskit during an initial render and then decomposing a circuit in a
later rerun caused a segmentation fault during development.

The interface therefore follows two rules:

1. Qiskit-dependent operations happen in the run path, not in render helpers.
2. All circuit artifacts are precomputed while the real result is being
   produced and stored in the immutable `CircuitArtifacts` record:
   - circuit summary and decomposition counts,
   - parameter table,
   - gate-count table,
   - PNG diagrams for all three decomposition levels,
   - text diagram.

On reruns, the circuit tab displays those stored bytes and dataframes. It does
not call Qiskit. This keeps normal Streamlit interactions such as changing a
tab, selecting history, or downloading JSON stable.

The convergence chart and molecule schematic are derived from real results or
the selected configuration. The molecule drawing is explicitly labeled as an
illustrative geometry, not an orbital or electron-density visualization.

## 5. Testing

The web tests are split between fast UI wiring and real execution:

- `tests/unit/test_webapp_logic.py` covers input validation, unsupported
  combinations, delegation to the scientific layer, error propagation,
  milli-Hartree arithmetic, history records, JSON round-trips and collision-safe
  saving.
- `tests/unit/test_webapp_visuals.py` checks that convergence frames and chart
  data contain the recorded history exactly, plus molecule labels and real
  circuit summary/PNG/parameter tables.
- `tests/unit/test_webapp_app.py` uses Streamlit `AppTest` for startup, absence
  of fake metrics before a run, real-result display, execution failure,
  missing-dependency messaging, and save-button wiring.
- `tests/integration/test_webapp_real_run.py` executes a real H₂ experiment
  through the UI harness, verifies its output against the returned scientific
  result, checks that circuit artifacts exist, and reruns the script without
  adding a duplicate history entry.

Run all tests with:

```bash
.venv/bin/pytest -q
```

Graphical browser automation is not available in this environment. Verification
uses Streamlit's AppTest harness plus a local server startup and health-endpoint
check. That limitation is stated rather than replaced by an unverified
screenshot claim.

## 6. Limitations

- Only H₂/STO-3G/UCCSD is implemented. Unsupported molecules, bases and ansatze
  are rejected rather than silently mapped to another calculation.
- The VQE loop does not expose per-iteration callbacks, so the UI shows a
  spinner during execution rather than a fabricated progress percentage.
- Session history is in memory and disappears when the Streamlit process or
  browser session ends. Use the JSON export to preserve results.
- The dashboard is single-user and local. It has no authentication, database,
  job queue, deployment configuration or remote hardware integration.
- The simulation is exact statevector simulation, not quantum hardware and not
  a noise model. Agreement with exact diagonalization is a validation result,
  not evidence of quantum advantage.
- `AppTest` exercises the server-side script and widget behavior; it is not a
  substitute for cross-browser visual regression testing.
