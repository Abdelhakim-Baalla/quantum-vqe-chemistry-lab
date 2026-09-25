# Methodology

This document describes the scientific and numerical choices behind the H₂
VQE experiment. The goal is a transparent, reproducible reference
implementation, not a claim of quantum advantage or hardware performance.

## 1. Molecular problem

The molecule is H₂ at a bond length of **0.735 Å**, in the **STO-3G** minimal
basis. The geometry passed to PySCF is

```text
H 0.0 0.0 0.0
H 0.0 0.0 0.735
```

with coordinates in Ångström. The Born–Oppenheimer approximation is used: the
nuclei are fixed, and their classical repulsion is added to the electronic
energy afterwards.

Qiskit Nature's `PySCFDriver` runs a restricted Hartree–Fock (RHF) calculation
and returns:

- the one-electron integrals \(h_{pq}\),
- the two-electron integrals \(h_{pqrs}\),
- the nuclear repulsion energy,
- the number of spatial orbitals, spin orbitals and particles.

STO-3G gives two spatial orbitals and therefore four spin orbitals for H₂.
With two electrons, the Hartree–Fock occupation is
\((N_\alpha, N_\beta) = (1, 1)\).

The electronic Hamiltonian in second quantization is

\[
\hat H_{\mathrm{elec}}
= \sum_{pq} h_{pq}\, a_p^\dagger a_q
+ \frac{1}{2}\sum_{pqrs} h_{pqrs}\, a_p^\dagger a_q^\dagger a_r a_s ,
\]

where \(a_p^\dagger\) and \(a_p\) create and annihilate an electron in spin
orbital \(p\). The total molecular energy is

\[
E_{\mathrm{total}} = E_{\mathrm{elec}} + E_{\mathrm{nuc}}.
\]

All energies in the result files are in **Hartree**. The nuclear repulsion is
kept separate throughout the code and added only when a total energy is
reported. This avoids the common mistake of comparing an electronic VQE energy
with a total FCI energy.

For H₂/STO-3G at 0.735 Å the measured nuclear repulsion is

\[
E_{\mathrm{nuc}} = 0.7199689944489797\ \mathrm{Ha}.
\]

## 2. Fermions to qubits

Two mappings are supported.

### Jordan–Wigner

Each spin orbital becomes one qubit. Fermionic anticommutation is enforced by
Pauli-Z strings. H₂/STO-3G therefore uses **four qubits** with no symmetry
reduction. This is the simplest mapping to explain and serves as a full-space
cross-check.

### Parity with two-qubit reduction

The parity mapping stores occupation parities rather than occupation numbers.
Qiskit Nature's `ParityMapper(num_particles=(1, 1))` then applies its standard
two-qubit reduction. In block-spin orbital ordering the mapper tapers the
middle and last qubits using the parities

\[
(N_\alpha + N_\beta) \bmod 2,
\qquad
N_\alpha \bmod 2.
\]

For the Hartree–Fock sector \((1,1)\), both parities are fixed. The result is a
**two-qubit** Hamiltonian whose spectrum, in that symmetry sector, matches the
ground-state energy of the full four-qubit problem. The reduction is a
symmetry projection, not an additional physical approximation.

The measured reduced Hamiltonian has five Pauli terms:

| Pauli label | Coefficient (Ha) |
| --- | ---: |
| `II` | \(-1.0523732457728596\) |
| `IZ` | \(0.39793742484317934\) |
| `ZI` | \(-0.3979374248431794\) |
| `ZZ` | \(-0.011280104256235268\) |
| `XX` | \(0.18093119978423144\) |

The experiment always checks the qubit count against the configuration and
checks the reduced result against a full Jordan–Wigner diagonalization when
parity mapping is used.

## 3. UCCSD ansatz

The ansatz is unitary coupled-cluster singles and doubles (UCCSD) with a
Hartree–Fock reference:

\[
|\psi(\boldsymbol\theta)\rangle
= e^{T(\boldsymbol\theta) - T^\dagger(\boldsymbol\theta)}
|\mathrm{HF}\rangle,
\qquad
T = T_1 + T_2.
\]

`T₁` contains single excitations and `T₂` double excitations. The circuit is
built with Qiskit Nature's `UCCSD` using one repetition, the parity mapper and
a `HartreeFock` initial state. For this problem it has **three parameters**
(two singles and one double).

Brillouin's theorem makes the singles stationary at the RHF reference, so the
double excitation carries the correlation energy. In the measured run the two
single-excitation angles remain near zero and the double-excitation angle
converges to approximately \(-0.11177\) rad. For two electrons in two spatial
orbitals, this UCCSD form can represent the exact singlet ground state; the
numerical result confirms this to floating-point precision.

The all-zero angle vector prepares the Hartree–Fock state exactly. That state
is used both as the default starting point and as the baseline for the
"optimizer reduced the energy" check. A seeded random start is available for
experiments, but it is not used for the official result.

## 4. Cost function and simulator

VQE minimizes the electronic expectation value

\[
E(\boldsymbol\theta)
= \langle \psi(\boldsymbol\theta) |
\hat H_{\mathrm{elec}} |
\psi(\boldsymbol\theta) \rangle .
\]

The expectation value is evaluated with Qiskit's `StatevectorEstimator`. This
is an **exact statevector simulator**:

- no shot sampling,
- no noise model,
- no hardware,
- no gate or readout error.

The cost function therefore returns the mathematically exact expectation
value for the current parameters, up to floating-point round-off. Nuclear
repulsion is added after optimization.

The simulator is deliberately classical and small. A two-qubit Hamiltonian can
be diagonalized instantly on a laptop; the value of this project is the
end-to-end, auditable workflow and its validation, not computational speed.

## 5. Classical optimizer

The optimizer is SciPy's `scipy.optimize.minimize`. Gradient-based methods use
SciPy's finite-difference gradients; derivative-free methods call the objective
directly. The default is **L-BFGS-B**.

| Optimizer | Tolerance option | Default tolerance |
| --- | --- | ---: |
| `BFGS` | `gtol` | `1e-6` |
| `L-BFGS-B` | `gtol` | `1e-8` |
| `SLSQP` | `ftol` | `1e-8` |
| `COBYLA` | `tol` | `1e-8` |
| `Nelder-Mead` | `xatol`, `fatol` (adaptive) | `1e-8` |

The maximum number of iterations defaults to 500. The BFGS default is looser
than the others because its finite-difference gradient can stall at `1e-8` on
this problem even when the energy is already exact; the resolved tolerance is
always written to the JSON file.

Every call to the cost function during optimization is recorded with its
evaluation number, energy and parameter vector. This history includes trial points generated by a line
search, which can temporarily be worse than the best point seen so far. The
convergence plot therefore shows both the raw evaluations and the best energy
so far, instead of drawing a misleading monotone curve.

The optimizer result fields are taken from SciPy:

- `nfev`: number of cost-function evaluations,
- `nit`: number of iterations,
- `njev`: number of Jacobian/gradient evaluations,
- `success` / `converged`: SciPy's convergence flag,
- `message`: SciPy's convergence message,
- `status_code`: SciPy's status code.

"Converged" means that the local optimizer met its stopping criterion. It does
**not** prove that the global minimum was found. For this two-qubit problem the
exact reference independently establishes the ground-state energy.

## 6. Independent references

Three references are computed.

### 6.1 Exact diagonalization of the same qubit Hamiltonian

The primary reference is the lowest eigenvalue of the **same** qubit
Hamiltonian used by VQE, obtained by constructing its dense matrix and calling
`numpy.linalg.eigvalsh`. For the reduced H₂ Hamiltonian this is a 4×4 matrix.
This reference isolates the variational algorithm from chemistry and mapping
choices: if VQE is correct, it must reproduce this eigenvalue.

### 6.2 Full Jordan–Wigner cross-check

When the run uses parity mapping, the original fermionic Hamiltonian is mapped
again with `JordanWignerMapper` and diagonalized in the full 16-dimensional
space. Its ground energy must agree with the parity-reduced result. This checks
that the two-qubit reduction did not change the ground-state energy in the
chosen symmetry sector. For a Jordan–Wigner run this check is not applicable
and is recorded as `null`, not as a pass.

### 6.3 Independent PySCF RHF + FCI

A separate PySCF calculation is run directly from the geometry and basis,
without Qiskit Nature and without the qubit mapping. It performs RHF, then
full configuration interaction (FCI) in the same STO-3G basis. The RHF energy
is compared with the ansatz energy at zero angles, and the FCI total energy is
compared with the exact qubit total energy.

For H₂/STO-3G, FCI in the minimal basis is the exact basis-set ground state.
This is an independent check of the integrals, the mapping and the energy
bookkeeping. It is not a check against experimental chemistry: STO-3G is a
minimal basis and is not quantitatively accurate for real H₂.

