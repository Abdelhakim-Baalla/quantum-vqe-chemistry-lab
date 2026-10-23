import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt

LAUNCH = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get('QUANTUM_LAB_REPO', LAUNCH.parents[1]))
sys.path.insert(0, str(ROOT))
from webapp import logic, visuals

out = LAUNCH / 'charts'
out.mkdir(parents=True, exist_ok=True)
values = logic.UIConfigInput(
    molecule='H2', distance_angstrom=0.735, basis='sto3g', ansatz='UCCSD',
    mapping='parity', two_qubit_reduction=True, optimizer='L-BFGS-B',
    max_iterations=500, initial_point='hf', seed=7, output_dir='results',
)
run = logic.execute_experiment(logic.build_experiment_config(values))
for reps, name in [(1, 'circuit_pauli_hires.png'), (2, 'circuit_basis_hires.png')]:
    fig = visuals.circuit_figure(run.chemistry.ansatz, reps=reps)
    fig.savefig(out / name, dpi=480, facecolor=fig.get_facecolor(), bbox_inches='tight', pad_inches=0.12)
    plt.close(fig)
    print('wrote', name)
