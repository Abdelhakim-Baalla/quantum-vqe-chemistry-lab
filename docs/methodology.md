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

