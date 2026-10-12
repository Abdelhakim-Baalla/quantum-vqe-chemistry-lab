# Quantum VQE Chemistry Lab

A reproducible laboratory for **variational quantum eigensolver (VQE)**
experiments in quantum chemistry. The first target is molecular hydrogen
(H₂) in the STO-3G basis, with independent validation against exact
diagonalization and a PySCF full-configuration-interaction calculation.

The implementation is under active development.
## Quick start

The project targets Python 3.11 and 3.12. The tested environment is Python
3.12.14. Create an isolated environment:

```bash
cd quantum-vqe-chemistry-lab
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev,web]"
```

With plain `pip`, the equivalent is:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,web]"
```

The `dev` extra provides the test and lint tools. The `web` extra provides
Streamlit, pandas, Altair and `pylatexenc` for the local dashboard and its
circuit renderer. A CLI-only environment can use `.[dev]` instead.

Run the experiment:

```bash
python -m quantum_vqe run-h2 --distance 0.735 --basis sto3g --plot
```

The console prints the configuration, Hamiltonian and ansatz information,
Hartree-Fock and VQE energies, exact and PySCF FCI references, the absolute
error, optimizer convergence status, evaluation counts and wall-clock time. A
timestamped JSON file is written under `results/`, and `--plot` adds a PNG
convergence plot next to it.

Useful variants:

```bash
# Explicit output path and plot
python -m quantum_vqe run-h2 --json results/h2_0735.json --plot

# Jordan-Wigner mapping, no parity reduction (4 qubits instead of 2)
python -m quantum_vqe run-h2 --mapping jordan-wigner

# A different optimizer and a seeded random starting point
python -m quantum_vqe run-h2 --optimizer BFGS --tolerance 1e-6 --init random --seed 11
```

The installed entry point is equivalent to the module invocation:

```bash
quantum-vqe run-h2 --distance 0.735
```

## What VQE does

A quantum chemistry problem can be written as a **Hamiltonian** \(\hat H\):
an operator whose eigenvalues are the allowed energies of the molecule. The
lowest eigenvalue is the ground-state energy.

VQE is a hybrid quantum/classical algorithm:

1. A quantum circuit prepares a parameterized state
   \(|\psi(\boldsymbol\theta)\rangle\).
2. The quantum simulator measures the expectation value
   \(E(\boldsymbol\theta)=\langle\psi(\boldsymbol\theta)|\hat H|\psi(\boldsymbol\theta)\rangle\).
3. A classical optimizer changes \(\boldsymbol\theta\) to lower \(E\).
4. Steps 2–3 repeat until convergence.

The variational principle says that for any normalized trial state,

\[
E(\boldsymbol\theta) \ge E_0,
\]

where \(E_0\) is the exact ground-state energy. A lower energy is therefore
better, and the exact result provides an independent certificate: a correct
VQE result cannot be below \(E_0\) beyond numerical noise. VQE is a heuristic;
it does not guarantee finding the global minimum, and its accuracy depends on
the ansatz and optimizer.

## The H₂ experiment

### 1. Molecular problem and integrals

The geometry is `H 0 0 0; H 0 0 0.735` with coordinates in Ångström. Qiskit
Nature's `PySCFDriver` runs a restricted Hartree-Fock (RHF) calculation with
PySCF and produces the one- and two-electron molecular-orbital integrals.

In second quantization, the electronic Hamiltonian is

\[
\hat H_{\mathrm{elec}} =
\sum_{pq} h_{pq} a_p^\dagger a_q
+ \frac12 \sum_{pqrs} h_{pqrs} a_p^\dagger a_q^\dagger a_r a_s ,
\]

where \(a_p^\dagger\) and \(a_p\) create and annihilate electrons in spin
orbital \(p\). The total molecular energy adds the classical nuclear repulsion:

\[
E_{\mathrm{total}} = E_{\mathrm{elec}} + E_{\mathrm{nuc}}.
\]

The experiment reports both. For H₂/STO-3G, \(E_{\mathrm{nuc}}\approx 0.72\)
Ha at 0.735 Å; the electronic energy is negative. Comparing a VQE electronic
energy to a total FCI energy without adding \(E_{\mathrm{nuc}}\) would be a
unit/definition mistake, so the JSON keeps the two quantities separate.

### 2. Fermions to qubits

Electrons are fermions; qubits are distinguishable two-level systems. A
**fermionic-to-qubit mapping** encodes occupation numbers in qubit states. This
project supports:

- **Jordan-Wigner (JW):** each spin orbital becomes one qubit and fermionic
  anticommutation is enforced with Pauli-Z strings.
- **Parity:** occupation parity is stored instead of occupation number. With
  the number of alpha and beta electrons fixed, two qubits can be removed by
  **Z2 symmetry tapering**.

The default H₂ run uses parity mapping with the two-qubit reduction. STO-3G
has two spatial orbitals, i.e. four spin orbitals:

```text
4 spin orbitals --parity--> 4 qubits --Z2 tapering--> 2 qubits
```

The removed qubits correspond to the total particle-number parity and the
alpha-spin parity. The Hartree-Fock sector fixes their eigenvalues, so the
reduced Hamiltonian is isospectral to the full Hamiltonian *within that
symmetry sector*. The experiment also diagonalizes the full four-qubit
Jordan-Wigner Hamiltonian as a cross-check. Use `--no-reduce` to simulate four
qubits with parity mapping, or `--mapping jordan-wigner` to compare mappings.

### 3. UCCSD ansatz

The default ansatz is **unitary coupled-cluster singles and doubles (UCCSD)**:

\[
|\psi(\boldsymbol\theta)\rangle =
e^{T(\boldsymbol\theta)-T^\dagger(\boldsymbol\theta)}
| \mathrm{HF}\rangle,
\qquad T = T_1 + T_2.
\]

The Hartree-Fock state is the reference determinant. The singles and doubles
excitations are mapped to qubit operators, and their angles are optimized. For
the reduced H₂ problem Qiskit Nature constructs three parameters (two singles
and one double). Brillouin's theorem makes the singles stationary at the RHF
reference, so the double excitation carries the correlation energy; the
optimizer keeps the singles near zero. UCCSD is chemically motivated and, for
this two-electron minimal-basis problem, can represent the exact ground state.

### 4. Local simulation and optimization

VQE evaluates the cost function with Qiskit's `StatevectorEstimator`. This is a
noiseless local simulator: it evolves the statevector exactly, so there is no
shot noise and no hardware error. The classical optimizer is SciPy's
`L-BFGS-B` by default, with finite-difference gradients. The implementation
records every energy evaluation, the initial and final parameters, the number
of function evaluations, and the optimizer's own convergence flag.

A run is labeled **success** only when the optimizer reports convergence and
all scientific checks pass. A converged run with an inaccurate energy is still
reported as failed. An unconverged run is never silently presented as success.

### 5. Exact validation

The primary reference is the exact lowest eigenvalue of the **same** qubit
Hamiltonian, obtained by sparse/dense Hermitian diagonalization. This isolates
the variational algorithm from chemistry and mapping choices.

Two further independent checks are performed:

- The same electronic Hamiltonian is mapped with **Jordan-Wigner** and
  diagonalized in the full Hilbert space. Its ground energy must match the
  parity-reduced result.
- A direct **PySCF RHF + FCI** calculation is run from the same geometry and
  basis, without using Qiskit Nature. Its total energy must match the exact
  qubit total energy. The Hartree-Fock energy from the ansatz at zero angles is
  also compared with the independent RHF energy.

These are consistency checks, not a proof that the chosen basis set is
physically complete. STO-3G is a minimal basis and is not quantitatively
accurate for real chemistry.

## Installation

### Requirements

- Linux, macOS, or Windows
- Python 3.11–3.12
- Prebuilt wheels for the tested Linux, macOS and Windows Python versions; no
  compiler is required when wheels are available. PySCF is installed through
  the `qiskit-nature[pyscf]` extra.
- No GPU, quantum cloud credentials, or network access at run time

### Dependencies

The tested versions are listed in the experiment report. The declared ranges
are intentionally compatible with current releases:

| Package | Role | Declared range |
| --- | --- | --- |
| `qiskit` | circuits, operators, primitives, exact statevector simulator | `>=2.1,<3.0` |
| `qiskit-nature[pyscf]` | chemistry problem, mappings, Hartree-Fock/UCCSD, PySCF driver | `>=0.8,<0.9` |
| `pyscf` | mean-field integrals and independent FCI reference | via Qiskit Nature extra |
| `numpy` | linear algebra and arrays | `>=2.0,<3.0` |
| `scipy` | optimizer and sparse diagonalization | `>=1.11,<2.0` |
| `matplotlib` | convergence plots and molecular schematic | `>=3.8,<4.0` |
| `streamlit` | local interactive dashboard | `>=1.66,<2.0` (`.[web]`) |
| `pandas` | dashboard tables and exports | `>=2.0,<3.0` (`.[web]`) |
| `altair` | interactive convergence chart | `>=5.0,<7.0` (`.[web]`) |
| `pylatexenc` | Qiskit Matplotlib circuit rendering | `>=2.10,<3.0` (`.[web]`) |
| `pytest`, `pytest-cov`, `ruff` | development and CI | `.[dev]` |

Qiskit Nature 0.8 is the current release used here. Older tutorials that call
`QubitConverter` or the removed `qiskit_nature.algorithms` VQE classes target
older APIs; this project uses the current `second_q` API and a small explicit
VQE loop.

## Running experiments

```bash
python -m quantum_vqe run-h2 [options]
```

| Option | Default | Meaning |
| --- | --- | --- |
| `--distance ANGSTROM` | `0.735` | H–H bond length |
| `--basis NAME` | `sto3g` | PySCF basis set |
| `--mapping {parity,jordan-wigner}` | `parity` | fermion-to-qubit mapping |
| `--reduce` / `--no-reduce` | reduction on for parity | two-qubit Z2 tapering |
| `--optimizer NAME` | `L-BFGS-B` | SciPy optimizer |
| `--max-iterations N` | `500` | optimizer iteration cap |
| `--tolerance TOL` | optimizer-specific | optimizer convergence tolerance |
| `--init {hf,random}` | `hf` | initial UCCSD angles |
| `--seed N` | `7` | seed for random initial angles |
| `--output-dir DIR` | `results` | directory for timestamped JSON |
| `--json PATH` | timestamped file | explicit JSON path |
| `--plot` | off | write a PNG convergence plot |

Examples:

```bash
python -m quantum_vqe run-h2 --distance 0.735 --basis sto3g --plot
python -m quantum_vqe run-h2 --mapping jordan-wigner --json results/h2_jw.json
python -m quantum_vqe run-h2 --optimizer SLSQP --max-iterations 200
```

The program is deterministic for the default Hartree-Fock start and exact
simulator. Random starts are reproducible when the seed is fixed.

## Examples

The CLI is the primary interface, but the experiment is also a normal Python
API. The checked-in example mirrors the full workflow without argparse:

```bash
python examples/run_h2.py
python examples/run_h2.py --distance 0.9 --optimizer BFGS
python examples/run_h2.py --mapping jordan-wigner --output-dir results/jw
```

It prints a short summary and writes a JSON result plus a convergence plot
under `results/`, which is ignored by git. The script is intentionally small:
it calls `run_h2_experiment`, saves the result, and plots the recorded
optimization history.

## Output fields

A JSON result contains:

- `experiment`, `schema_version`, `status`, `created_utc`
- `config`: resolved run configuration, including the chosen tolerance
- `molecule`: geometry, basis, charge, spin, orbital/electron counts, nuclear
  repulsion, qubit count
- `hamiltonian`: mapping, reduction description, Pauli terms, Hermiticity check
- `ansatz`: UCCSD, qubit count, parameter count and names, reference state
- `optimizer` and `simulator`: method and simulation assumptions
- `energies_hartree`: HF, VQE, exact-qubit and PySCF FCI energies, both
  electronic and total where applicable
- `errors_hartree`: absolute VQE error, signed variational gap, reference
  cross-check errors
- `checks`: booleans for Hermiticity, qubit consistency, convergence,
  variational principle, accuracy target and independent references
- `references`: exact diagonalization and FCI details
- `optimization`: history (evaluation number, energy, parameters), counts,
  convergence message, initial/final energies and parameters
- `timing_seconds`: phase timings
- `software`: Python and package versions
- `warnings` and `artifacts`

A minimal programmatic example:

```python
from quantum_vqe import ExperimentConfig, run_h2_experiment
from quantum_vqe.plotting import plot_convergence

config = ExperimentConfig(distance_angstrom=0.735, basis="sto3g")
result = run_h2_experiment(config)
print(result.status)
print(result.energies_hartree["vqe_total"])
print(result.energies_hartree["exact_qubit_total"])
result.save("results/h2.json")
plot_convergence(
    result.optimization["history"],
    "results/h2.png",
    exact_energy=result.energies_hartree["exact_qubit_electronic"],
    hf_energy=result.energies_hartree["hf_electronic"],
)
```

## Tests

Fast unit tests and the full chemistry integration tests are separated with the
`integration` marker.

```bash
# Full suite (unit + integration)
pytest -q

# Fast checks only, no PySCF chemistry pipeline
pytest -q -m "not integration"

# Chemistry pipeline and CLI only
pytest -q -m integration
```

Coverage and linting:

```bash
pytest --cov=quantum_vqe --cov-report=term-missing
ruff check .
ruff format --check .
```

The unit suite checks configuration validation, operator Hermiticity, exact
diagonalization, energy errors, estimator/statevector agreement, the VQE loop,
serialization, no-false-success status logic and the Streamlit-independent web
helpers. Integration tests run the actual H₂ pipeline, compare against FCI and
JW references, exercise the CLI, reload the JSON result, and run a real H₂
experiment through Streamlit's `AppTest` UI harness. In the tested environment
the suite reports **99 unit tests** and **17 integration tests** (116 total),
all passing, with 89% statement coverage for the `quantum_vqe` package. CLI
subprocess behavior and the server-side AppTest UI harness are tested directly
but are not attributed to that in-process coverage total.

The CI workflow in `.github/workflows/ci.yml` installs `.[dev,web]` and runs
linting, formatting checks, unit tests and the chemistry/UI integration tests
on Python 3.11 and 3.12. The workflow file is checked in, but a GitHub Actions
run is not claimed as verified from this local environment.

