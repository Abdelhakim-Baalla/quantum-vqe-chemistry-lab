# Security Policy

## Supported versions

Security fixes are applied to the current `main` branch and the latest tagged
release. This is a local scientific reference project with no hosted service,
user accounts or production data.

| Version | Supported |
| --- | --- |
| `main` / `0.1.x` | Yes |
| Older snapshots | No |

## Reporting a vulnerability

Please **do not open a public issue** for a security vulnerability.

Use GitHub's private vulnerability reporting:
<https://github.com/Abdelhakim-Baalla/quantum-vqe-chemistry-lab/security/advisories/new>

Include, where possible:

- affected version or commit,
- a minimal reproduction,
- impact and attack preconditions,
- any suggested mitigation.

You can expect an acknowledgement within seven days. Please allow time for a
fix and coordinated disclosure before publishing details.

## Scope and deployment assumptions

Quantum Lab is designed to run locally:

```bash
streamlit run app.py
```

It has **no authentication, authorization, multi-user isolation, TLS or
database**. Do not expose it to an untrusted network without putting an
authenticated reverse proxy in front of it and reviewing the deployment.

The scientific pipeline executes local Python, PySCF and Qiskit code. Only run
experiment configurations and output directories that you trust. The optional
JSON export writes to a user-selected directory; review that path before use.

No API keys, cloud credentials or quantum-hardware tokens are required or
stored by this project. Do not commit secrets, private data or generated
credentials to the repository.

## Dependency security

Dependencies are declared in `pyproject.toml` and installed by CI. Report a
suspected vulnerable dependency through the private advisory link above so it
can be assessed alongside any project-level impact.
