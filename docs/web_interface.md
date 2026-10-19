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

