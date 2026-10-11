# Roadmap

The current release is deliberately narrow: one molecule, one basis, one
ansatz family, an exact simulator and three independent references. The
following extensions are ordered by how directly they build on the validated
core. None of the items below is implemented unless explicitly stated.

## Near term

### 1. Bond-length scan and dissociation curve

Run the validated H₂ pipeline over a grid of bond lengths and compare the VQE,
exact and FCI curves. This would demonstrate that the implementation is not
tuned to a single geometry and would expose the behavior near dissociation,
where static correlation becomes important.

A scan should:

- reuse the same convergence and validation checks at every point,
- store one JSON record per distance,
- plot VQE, exact and FCI total energies together,
- report the equilibrium distance found by interpolation,
- keep STO-3G limitations explicit.

### 2. More molecular systems

Generalize the chemistry and CLI layers beyond H₂:

- HeH⁺ and H₃⁺ as small multi-electron checks,
- LiH with a frozen core and a small active space,
- H₂O in a minimal basis,
- active-space and frozen-core configuration,
- point-group and spin-symmetry handling.

This requires more than changing a geometry string: the qubit-reduction rules,
reference calculations and result schema need to become molecule-aware.

### 3. Ansatz and optimizer comparisons

Add a controlled comparison of:

- UCCSD versus ADAPT-VQE versus a hardware-efficient ansatz,
- gradient-based versus derivative-free optimizers,
- finite-difference versus analytic or parameter-shift gradients,
- random restarts and multi-start optimization.

The comparison should report energy error, evaluation count, wall time and
sensitivity to the initial point, using the same exact reference.

### 4. Shot-based and noisy simulation

The current simulator is exact. A shot-based study would add:

- finite-shot estimators and sampling variance,
- confidence intervals for the energy,
- depolarizing and readout noise models,
- error mitigation (for example zero-noise extrapolation),
- a clear separation between algorithmic error and statistical error.

This is the natural bridge to hardware experiments, but it is not implemented
in the current release.

## QAOA Max-Cut (future work)

QAOA for Max-Cut is a natural second experiment because it is small,
well-defined and easy to validate by brute force. It is **not implemented** in
this version. The current package and CLI are intentionally focused on the H₂
VQE workflow; adding QAOA should be a separate experiment rather than
overloading `run_h2_experiment()`.

A future implementation should include:

- a small weighted or unweighted graph, with the graph stored in the config,
- a cost Hamiltonian built from the Max-Cut objective,
- a mixer Hamiltonian and a depth-\(p\) QAOA circuit,
- a classical optimizer over the \(2p\) angles,
- brute-force enumeration of all cuts as the exact reference,
- a comparison of the QAOA expectation value and the best sampled bitstring,
- tests for the cost Hamiltonian, the mixer, the circuit depth and the
  brute-force reference,
- a JSON result schema and a convergence/landscape plot.

The experiment should state clearly that small Max-Cut instances are easy
classically and that QAOA performance at this scale says nothing about quantum
advantage.

## Medium term

### Hardware execution

- Transpile the UCCSD circuit for a selected backend.
- Add measurement mitigation and readout calibration.
- Report shot counts, hardware noise and confidence intervals.
- Compare hardware, noisy simulation and exact simulation on the same problem.
- Keep credentials and backend access out of the repository.

### Excited states and properties

- Deflation or subspace methods for excited states.
- Dipole moments and other observables.
- Finite-temperature and thermal-state methods.
- Molecular dynamics or geometry optimization with a quantum energy oracle.

### Error mitigation and resilience

- Zero-noise extrapolation.
- Probabilistic error cancellation.
- Symmetry verification.
- Comparison of raw and mitigated energies against exact references.

## Long term

- Larger active spaces and embedding methods.
- Relativistic effects.
- Real-time dynamics.
- Integration with classical quantum-chemistry workflows.
- Reproducible benchmark suites across simulators and hardware.
- Packaging and documentation suitable for community contributions.

