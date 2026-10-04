import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

export function fakeRoot({ title = '1.2.3', eyebrow = '1.2.3', bridge = '1.2.3' } = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'fks-versions-'));
  writeFileSync(join(dir, 'fontkit-studio.html'),
    `<title>Font Kit Studio v${title}</title>\n<p class="eyebrow">Font Kit Studio · v${eyebrow}</p>\n`);
  writeFileSync(join(dir, 'fontkit-bridge.js'),
    `/**\n * Font Kit Studio\n * fontkit-bridge.js version ${bridge}\n */\n`);
  writeFileSync(join(dir, 'LICENSE'), 'MIT\n');
  return dir;
}
