import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkVersions, readVersions } from '../scripts/versions.js';
import { fakeRoot } from './helpers/fake-root.js';

const REPO = fileURLToPath(new URL('../../..', import.meta.url));
const { version } = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));

test('the repository files and the package agree on the version', () => {
  assert.deepEqual(readVersions(REPO),
    { 'Studio title': version, 'Studio eyebrow': version, 'bridge header': version });
  checkVersions(REPO, version);
});

test('a drifted label is named in the error', () => {
  assert.throws(() => checkVersions(fakeRoot({ eyebrow: '1.2.2' }), '1.2.3'),
    /package is 1\.2\.3, but Studio eyebrow is 1\.2\.2/);
  assert.throws(() => checkVersions(fakeRoot({ bridge: '1.3.0' }), '1.2.3'),
    /bridge header is 1\.3\.0/);
});

test('a missing label is reported as missing', () => {
  const dir = fakeRoot();
  writeFileSync(join(dir, 'fontkit-bridge.js'), '// no header\n');
  assert.throws(() => checkVersions(dir, '1.2.3'), /bridge header is missing/);
});
