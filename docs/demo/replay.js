const canvas = document.querySelector('canvas');
const slider = document.querySelector('input');
const reading = document.querySelector('output');

async function main() {
  const response = await fetch('run.json');
  if (!response.ok) throw new Error('The experiment could not be loaded.');
  const run = await response.json();
  const steps = run.evaluations;
  const ctx = canvas.getContext('2d');
  const min = Math.min(...steps.map(step => step.total));
  const max = Math.max(...steps.map(step => step.total));
  const pad = 24;
  document.getElementById('setup').textContent = run.bondLength + ' Å bond length · ' + run.qubits + ' qubits after parity reduction · ' + steps.length + ' evaluations';
  const methods = {hf_total:'Hartree–Fock',vqe_total:'VQE (statevector)',exact_qubit_total:'Exact qubit diagonalization',pyscf_fci_total:'PySCF full configuration interaction'};
  const table = document.getElementById('energies');
  for (const [key, label] of Object.entries(methods)) {
    const row = table.insertRow();
    const heading = document.createElement('th');
    heading.scope = 'row';
    heading.textContent = label;
    row.append(heading);
    row.insertCell().textContent = run.energies[key].toFixed(12);
  }
  function draw() {
    const {width,height} = canvas.getBoundingClientRect();
    const scale = devicePixelRatio || 1;
    canvas.width = Math.round(width * scale);
    canvas.height = Math.round(height * scale);
    ctx.scale(scale,scale);
    const x = i => pad + (width - 2 * pad) * i/(steps.length-1);
    const y = energy => pad + (height - 2 * pad) * (max-energy)/(max-min);
    function trace(count,color) {
      ctx.beginPath();
      ctx.lineWidth=2;
      ctx.strokeStyle=color;
      for (let i=0;i<=count;i++) {
        if (i===0) ctx.moveTo(x(i),y(steps[i].total));
        else ctx.lineTo(x(i),y(steps[i].total));
      }
      ctx.stroke();
    }
    const current = Number(slider.value);
    trace(steps.length-1,'#bacbc1');
    trace(current,'#216149');
    ctx.beginPath();
    ctx.arc(x(current),y(steps[current].total),5,0,Math.PI*2);
    ctx.fillStyle='#216149';
    ctx.fill();
    reading.textContent = (current+1) + ' / ' + steps.length + ' · ' + steps[current].total.toFixed(10) + ' Ha';
    slider.setAttribute('aria-valuetext',reading.textContent);
  }
  slider.max = steps.length-1;
  slider.disabled = false;
  slider.oninput = draw;
  new ResizeObserver(draw).observe(canvas);
}
main().catch(error => { reading.textContent = error.message; });
