/* Counts are deterministic; style tuples live in authored CSS, not this generator. */
const corpus = document.querySelector('#corpus');
const fragment = document.createDocumentFragment();
for (let group = 0; group < 20; group += 1) {
  for (let index = 0; index < 250; index += 1) {
    if (group === 0 && index === 1) continue; // This parent is nested in sample zero.
    const parent = document.createElement('p');
    const groupId = `g${String(group).padStart(2, '0')}`;
    parent.className = groupId;
    parent.dataset.designId = `${groupId}.${String(index).padStart(3, '0')}`;
    parent.textContent = `Group ${group} sample ${index}`;
    if (group === 0 && index === 0) {
      parent.textContent = 'Outer prefix ';
      const child = document.createElement('span');
      child.className = 'g00';
      child.dataset.designId = 'g00.001';
      child.textContent = 'Nested sample';
      parent.append(child, document.createTextNode(' outer suffix'));
    }
    if (group === 0 && index === 2) parent.classList.add('contents-text');
    if (group === 0 && index === 3) {
      const hidden = document.createElement('span');
      hidden.id = 'nested-hidden';
      hidden.hidden = true;
      hidden.textContent = 'Excluded nested text';
      parent.appendChild(hidden);
    }
    fragment.appendChild(parent);
  }
}
corpus.appendChild(fragment);

// State-only liveness probe: no label/output can become another eligible parent.
window.fixtureProbe = {heartbeat: 0, acknowledged: '', inputEvents: 0};
function heartbeat() {
  window.fixtureProbe.heartbeat += 1;
  requestAnimationFrame(heartbeat);
}
requestAnimationFrame(heartbeat);
document.querySelector('#responsiveness').addEventListener('input', event => {
  window.fixtureProbe.acknowledged = event.target.value;
  window.fixtureProbe.inputEvents += 1;
});
const shadow = document.querySelector('#shadow-host').attachShadow({mode: 'open'});
const shadowText = document.createElement('p');
shadowText.textContent = 'Shadow text outside the first detector';
shadow.appendChild(shadowText);
