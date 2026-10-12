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

