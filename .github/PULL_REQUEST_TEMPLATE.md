## Summary

<!-- What changed and why? Link related issues. -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Tests
- [ ] Scientific result or schema change
- [ ] UI / visual change
- [ ] Maintenance

## Verification

<!-- List exact commands and relevant outcomes. -->

```bash
ruff check .
ruff format --check .
pytest -q
```

- [ ] Linting and formatting pass.
- [ ] Unit tests pass.
- [ ] Integration tests pass (or explain why they cannot run here).
- [ ] Visible UI changes include a light and/or dark screenshot.

## Scientific integrity checklist

- [ ] No fabricated energies, convergence points, checks or success states.
- [ ] Any new display value is derived from a recorded `ExperimentResult`.
- [ ] Electronic and total energies remain clearly separated.
- [ ] Independent validation against exact diagonalization and PySCF FCI is preserved.
- [ ] No quantum-advantage or hardware-execution claim was introduced.
- [ ] If `docs/assets/h2_result.json` changed, the regenerating command and environment are documented.

## Notes for reviewers

<!-- Limitations, follow-up work, or specific areas to inspect. -->
