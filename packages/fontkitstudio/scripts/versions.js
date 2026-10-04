import { readFileSync } from 'node:fs';
import { join } from 'node:path';

export const STUDIO_FILE = 'fontkit-studio.html';
export const BRIDGE_FILE = 'fontkit-bridge.js';

// Where each shipped file states its version (D039, D044). All must equal the package's.
const LABELS = {
  'Studio title': [STUDIO_FILE, /<title>Font Kit Studio v(\d+\.\d+\.\d+[^<\s]*)<\/title>/],
  'Studio eyebrow': [STUDIO_FILE, /Font Kit Studio · v(\d+\.\d+\.\d+[^<\s]*)</],
  'bridge header': [BRIDGE_FILE, /^ \* fontkit-bridge\.js version (\d+\.\d+\.\d+\S*)\s*$/m],
};

export function readVersions(root) {
  const found = {};
  for (const [label, [file, pattern]] of Object.entries(LABELS)) {
    found[label] = pattern.exec(readFileSync(join(root, file), 'utf8'))?.[1] ?? null;
  }
  return found;
}

export function checkVersions(root, expected) {
  const found = readVersions(root);
  const wrong = Object.entries(found).filter(([, value]) => value !== expected);
  if (wrong.length) {
    throw new Error(`version mismatch: package is ${expected}, but `
      + wrong.map(([label, value]) => `${label} is ${value ?? 'missing'}`).join(', '));
  }
  return found;
}
