"""Unit tests for chemistry helper functions that do not require PySCF."""

from __future__ import annotations

import pytest
from qiskit_nature.second_q.operators import FermionicOp

from quantum_vqe.chemistry import ChemistryError, _extract_electronic_hamiltonian


class FakeProblem:
    def __init__(self, operators: object) -> None:
        self._operators = operators

    def second_q_ops(self) -> object:
        return self._operators


