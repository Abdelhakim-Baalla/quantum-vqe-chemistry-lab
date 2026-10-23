# Contributing to Quantum VQE Chemistry Lab

Thank you for considering a contribution. This project is a small scientific
reference implementation, so contributions are reviewed for **reproducibility
and honesty** as well as code quality.

## Areas that are welcome

- Documentation corrections and clearer derivations.
- Tests that strengthen validation or cover a real edge case.
- Web-interface accessibility, layout and usability improvements.
- Performance improvements that preserve the numerical result.
- Carefully scoped extensions listed in [`docs/roadmap.md`](docs/roadmap.md).

Please open an issue before starting a large change, especially one that touches
the scientific pipeline, the result schema or the validated UI options.

## Development setup

Requirements: Python 3.11 or 3.12, and a C/Fortran build chain suitable for
PySCF if a wheel is not available.

```bash
git clone https://github.com/Abdelhakim-Baalla/quantum-vqe-chemistry-lab.git
cd quantum-vqe-chemistry-lab
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev,web]"
```

With plain `pip`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,web]"
```

## Before opening a pull request

Run all of the following from the repository root:

```bash
ruff check .
ruff format --check .
pytest -q
```

Integration tests execute the real H₂/PySCF/Qiskit pipeline. They are included
in the default test run and in CI. If you intentionally change a scientific
result, include the regenerated JSON and explain why in the pull request.

## Scientific integrity rules

These rules are not negotiable:

1. **No fabricated results.** Do not add hard-coded energies, invented
   convergence points, placeholder checks or a fake success state.
2. **Derive UI data from `ExperimentResult`.** Dashboard metrics and charts must
   be transforms of the recorded run, with the transformation documented in
   code.
3. **Preserve independent validation.** VQE must remain checked against exact
   diagonalization and the independent PySCF FCI reference.
4. **Separate electronic and total energies.** Nuclear repulsion must be handled
   explicitly, never silently folded into a comparison.
5. **Do not claim quantum advantage or hardware execution.** This repository
   uses a local exact statevector simulator.
6. **Update the checked-in reference only from a real run.** Regenerate
   `docs/assets/h2_result.json`, `docs/assets/h2_result.png` and the report with
   the actual command and record the environment.

## Code style

- Python 3.11+, fully type-annotated public functions where practical.
- Ruff handles linting and formatting with the repository configuration.
- Keep the scientific package (`src/quantum_vqe/`) independent of Streamlit.
- Keep Streamlit imports out of `webapp/logic.py` and `webapp/visuals.py`.
- Prefer explicit, auditable code over clever abstractions in numerical paths.
- Add or update tests for behavior changes. UI-only changes should include a
  screenshot when practical.

## Commit and pull-request conventions

Use clear, imperative commit subjects, for example:

```text
fix(webapp): keep the collapsed sidebar reopen control visible
feat(webapp): add real-data diagnostics dashboard
docs: document theme and launch-asset layout
```

A pull request should include:

- what changed and why,
- the exact commands used to verify it,
- whether any numerical result changed,
- screenshots for visible UI changes,
- any limitations or follow-up work.

Use the pull-request template. By contributing, you agree that your
contribution is licensed under the MIT License and that you will follow the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Reporting bugs and security issues

- Functional bugs: open a GitHub issue using the bug template.
- Security issues: do **not** open a public issue. Follow
  [`SECURITY.md`](SECURITY.md).
- Scientific disagreements: include the result JSON, the command, the expected
  value and a derivation or reference.
