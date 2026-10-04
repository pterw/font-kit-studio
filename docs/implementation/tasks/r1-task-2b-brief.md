# R1.2b brief: bundle Studio and the bridge at one checked version

Plan: `docs/plans/2026-10-03-r1-one-command.md` (R1.2); execution:
`docs/plans/2026-10-04-r1-pr-a-sdd.md`. Constraints:
`.superpowers/sdd/r1-pr-a/constraints.md` (read all of it first; it has the stall rule and
which gates apply to your diff). Decision: D041.

## Goal

The package's bundle step copies Studio and the bridge into `packages/fontkitstudio/dist/`
and refuses when the package, Studio's two labels and the bridge's header disagree on the
version. Builds on R1.2a (Studio is already `fontkit-studio.html` at your BASE).

## Definition of done

- The bridge carries ` * fontkit-bridge.js version 0.2.1` in its header comment.
- `node packages/fontkitstudio/scripts/bundle.js` writes `dist/fontkit-studio.html`,
  `dist/fontkit-bridge.js` and the package's `LICENSE`, byte-equal to the sources; a
  version mismatch throws before anything is written. `npm pack --dry-run` lists them.
- A Node test fails when the repository's Studio labels, bridge header and package version
  drift apart (it runs in the CI matrix from R1.1).
- Gates for this diff: static, bridge-syntax, node-package, frontend-gate (the bridge
  changes by one comment line), commit-messages. No Python suite.

## Owns

`fontkit-bridge.js` (one header line only), `.gitignore`,
`packages/fontkitstudio/package.json` (`scripts.prepack` only),
`packages/fontkitstudio/scripts/versions.js`, `packages/fontkitstudio/scripts/bundle.js`,
`packages/fontkitstudio/test/versions.test.js`, `packages/fontkitstudio/test/bundle.test.js`,
`packages/fontkitstudio/test/helpers/fake-root.js`, `.gitattributes` (new),
`packages/fontkitstudio/test/package.test.js` (the shebang assertion only).

## Steps

- [ ] **1. Bridge header.** Insert after line 2 of `fontkit-bridge.js`
  (` * Font Kit Studio — Design Bridge Protocol v1 Target SDK`) the line
  ` * fontkit-bridge.js version 0.2.1`. Run `node --check fontkit-bridge.js`.

- [ ] **2. Failing version tests** `packages/fontkitstudio/test/versions.test.js`:

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { checkVersions, readVersions } from '../scripts/versions.js';

const REPO = fileURLToPath(new URL('../../..', import.meta.url));
const { version } = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));

export function fakeRoot({ title = '1.2.3', eyebrow = '1.2.3', bridge = '1.2.3' } = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'fks-versions-'));
  writeFileSync(join(dir, 'fontkit-studio.html'),
    `<title>Font Kit Studio v${title}</title>\n<p class="eyebrow">Font Kit Studio · v${eyebrow}</p>\n`);
  writeFileSync(join(dir, 'fontkit-bridge.js'),
    `/**\n * Font Kit Studio\n * fontkit-bridge.js version ${bridge}\n */\n`);
  writeFileSync(join(dir, 'LICENSE'), 'MIT\n');
  return dir;
}

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
```

  `fakeRoot` goes in `test/helpers/fake-root.js` if `bundle.test.js` needs it too (it does);
  import it from there in both tests.

- [ ] **3. Implement** `packages/fontkitstudio/scripts/versions.js`:

```js
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
```

- [ ] **4. Failing bundle tests** `packages/fontkitstudio/test/bundle.test.js`:

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { bundle } from '../scripts/bundle.js';
import { fakeRoot } from './helpers/fake-root.js';

function fakePackage(version) {
  const dir = mkdtempSync(join(tmpdir(), 'fks-pkg-'));
  writeFileSync(join(dir, 'package.json'), JSON.stringify({ version }));
  return dir;
}

test('copies Studio, the bridge and the licence byte for byte', () => {
  const root = fakeRoot();
  const packageDir = fakePackage('1.2.3');
  bundle({ root, packageDir });
  for (const file of ['fontkit-studio.html', 'fontkit-bridge.js']) {
    assert.deepEqual(readFileSync(join(packageDir, 'dist', file)), readFileSync(join(root, file)));
  }
  assert.deepEqual(readFileSync(join(packageDir, 'LICENSE')), readFileSync(join(root, 'LICENSE')));
});

test('refuses a version mismatch before writing anything', () => {
  const packageDir = fakePackage('1.2.4');
  assert.throws(() => bundle({ root: fakeRoot(), packageDir }), /version mismatch/);
  assert.equal(existsSync(join(packageDir, 'dist')), false);
  assert.equal(existsSync(join(packageDir, 'LICENSE')), false);
});

test('npm pack ships the bundled files and nothing from test/ or scripts/', () => {
  const cwd = fileURLToPath(new URL('..', import.meta.url));
  const result = spawnSync('npm', ['pack', '--dry-run', '--json'],
    { cwd, encoding: 'utf8', shell: process.platform === 'win32' });
  assert.equal(result.status, 0, result.stderr);
  const files = JSON.parse(result.stdout)[0].files.map((f) => f.path).sort();
  for (const want of ['LICENSE', 'README.md', 'bin/fontkitstudio.js', 'dist/fontkit-bridge.js',
    'dist/fontkit-studio.html', 'package.json', 'src/cli.js']) {
    assert.ok(files.includes(want), `tarball lacks ${want}: ${files.join(', ')}`);
  }
  assert.equal(files.some((f) => f.startsWith('test/') || f.startsWith('scripts/')), false);
});
```

  `npm pack --dry-run` runs `prepack` (check this is true on npm 10; if it is not, the test
  runs `bundle()` first and the report says so). Its JSON output can be preceded by
  lifecycle output on stdout; if so, parse from the first `[`, and say so in the report.

- [ ] **5. Implement** `packages/fontkitstudio/scripts/bundle.js`:

```js
import { copyFileSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { BRIDGE_FILE, STUDIO_FILE, checkVersions } from './versions.js';

const PACKAGE_DIR = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const REPO_ROOT = resolve(PACKAGE_DIR, '..', '..');

// Copies Studio and the bridge into dist/ so a page never talks to a Studio from another
// release (spec 1.1). Runs as `prepack`, so npm pack and npm publish always bundle.
export function bundle({ root = REPO_ROOT, packageDir = PACKAGE_DIR } = {}) {
  const { version } = JSON.parse(readFileSync(join(packageDir, 'package.json'), 'utf8'));
  checkVersions(root, version);
  const dist = join(packageDir, 'dist');
  mkdirSync(dist, { recursive: true });
  for (const file of [STUDIO_FILE, BRIDGE_FILE]) copyFileSync(join(root, file), join(dist, file));
  copyFileSync(join(root, 'LICENSE'), join(packageDir, 'LICENSE'));
  return version;
}

if (resolve(process.argv[1] ?? '') === fileURLToPath(import.meta.url)) {
  try {
    console.log(`fontkitstudio: bundled Studio and the bridge at ${bundle()}`);
  } catch (error) {
    console.error(`fontkitstudio: ${error.message}`);
    process.exitCode = 1;
  }
}
```

  Add `"prepack": "node scripts/bundle.js"` to `package.json` `scripts`. Add to `.gitignore`:
  `packages/fontkitstudio/dist/` and `packages/fontkitstudio/LICENSE`.

- [ ] **6. Show the guards bite**: change the bridge header to `0.2.0`, run
  `npm --prefix packages/fontkitstudio test`, record the failing line, restore it.

- [ ] **7. LF line endings for the package.** A tarball packed from a Windows checkout
  would carry a CRLF shebang, and `env: node` breaks the bin on Linux and macOS (R1.1
  report). Create `.gitattributes` with `packages/fontkitstudio/** text eol=lf`, run
  `git add --renormalize packages/fontkitstudio`, and restore the strict shebang assertion
  in `test/package.test.js` (`bin.startsWith('#!/usr/bin/env node
')`). Show it bites:
  write the bin with CRLF, run the test, record the failure, restore.

- [ ] **8. Gates** (constraints.md): static, bridge-syntax, node-package, frontend-gate,
  commit-messages. The Python suite halves do not apply to this diff.

- [ ] **9. Handoff text** (the landing writes it): the progress.md event. No CHANGELOG
  line: nothing user-visible changes until the package ships.

Commit subject: `feat(dev): bundle Studio and the bridge at one checked version`. Body:
why (spec 1.1: the package ships Studio and the bridge at matching versions, so a page
never talks to a Studio from another release; the check runs before anything is copied).

## Report

Code phase: `.superpowers/sdd/r1-pr-a/task-2b-code-report.md`. Landing:
`docs/implementation/tasks/r1-task-2b-report.md`.
