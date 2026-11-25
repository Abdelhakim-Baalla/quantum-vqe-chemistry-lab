"""Export the recorded H₂ run without local environment metadata."""
import json
from pathlib import Path
from shutil import copyfile

source = Path(__file__).resolve().parent
output = source / "dist"
output.mkdir(exist_ok=True)
run = json.loads((source.parent / "assets/h2_result.json").read_text())
public = {
    "bondLength": run["molecule"]["bond_length_angstrom"],
    "qubits": run["molecule"]["num_qubits"],
    "energies": {key: run["energies_hartree"][key] for key in ("hf_total", "vqe_total", "exact_qubit_total", "pyscf_fci_total")},
    "evaluations": [
        {"evaluation": step["evaluation"], "total": step["energy_hartree"] + run["energies_hartree"]["nuclear_repulsion"]}
        for step in run["optimization"]["history"]
    ],
}
(output / "run.json").write_text(json.dumps(public))
for name in ("index.html", "replay.js"):
    copyfile(source / name, output / name)
