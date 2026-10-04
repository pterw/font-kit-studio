# R1.2 brief: Studio rename and bundling

Plan: `docs/plans/2026-10-03-r1-one-command.md` (R1.2); execution:
`docs/plans/2026-10-04-r1-pr-a-sdd.md`. Constraints:
`.superpowers/sdd/r1-pr-a/constraints.md` (read all of it first). Decision: D041.

## Goal

Studio is `fontkit-studio.html`. The old `font_kit_studio_v0.1.1.html` is a stub that
forwards to it with its query and hash, for one release. The package's bundle step copies
Studio and the bridge into `packages/fontkitstudio/dist/` and refuses when the package,
Studio's two labels and the bridge's header disagree on the version.

## Definition of done

- `git mv` rename; `fontkit-studio.html` has the same SHA-256 as the old file had at BASE.
- Opening the old name (file URL) lands on `fontkit-studio.html` with the same query and
  hash, in a real browser (test).
- Every live reference uses the new name (list below); point-in-time records are not
  touched (constraints ruling 5). The sweeper confirms no live hit remains.
- `scripts/verify.py` checks the new file and still verifies provenance against the old
  name at the `supplied-v0.1.1` tag.
- The bridge carries ` * fontkit-bridge.js version 0.2.1` in its header comment.
- `node packages/fontkitstudio/scripts/bundle.js` writes `dist/fontkit-studio.html`,
  `dist/fontkit-bridge.js` and the package's `LICENSE`, byte-equal to the sources; a
  version mismatch throws before anything is written. `npm pack --dry-run` lists them.
- A Node test fails when the repository's Studio labels, bridge header and package version
  drift apart (this runs in the CI matrix from R1.1).

## Owns

`font_kit_studio_v0.1.1.html` (becomes the stub), `fontkit-studio.html` (rename only),
`fontkit-bridge.js` (one header line only), `tests/support.py` (the `HTML` constant only),
`tests/test_frontend_gate_helpers.py`, `tests/test_frontend_gate_runner.py`,
`tests/test_preview_server.py` (file-name references only), `tests/test_studio_rename.py`
(new), `scripts/serve.py` (`STUDIO_HTML` only), `scripts/dev/_frontend_gate_shared.py`
(`STUDIO_HTML` only), `scripts/verify.py`, `docs/assets/screenshots/capture.py`,
`README.md` (file-name references and a migration note), `.gitignore`,
`packages/fontkitstudio/package.json` (`scripts.prepack` only),
`packages/fontkitstudio/scripts/versions.js`, `packages/fontkitstudio/scripts/bundle.js`,
`packages/fontkitstudio/test/versions.test.js`, `packages/fontkitstudio/test/bundle.test.js`.

Not yours: `AGENTS.md` and `CHANGELOG.md` (shared; draft their lines in the Handoff),
`docs/implementation/**`, older dated plans, `docs/specs/**`.

## Steps

- [ ] **1. Rename.** `git mv font_kit_studio_v0.1.1.html fontkit-studio.html`. Record
  `sha256sum fontkit-studio.html` and compare with `git show BASE:font_kit_studio_v0.1.1.html | sha256sum`.

- [ ] **2. Write the failing stub test** `tests/test_studio_rename.py`:

```python
"""The old Studio file name forwards to fontkit-studio.html for one release (D041)."""
import unittest

from support import ENGINES, HTML, REPO, close_contexts, new_context

OLD = REPO / 'font_kit_studio_v0.1.1.html'


class OldNameForwards(unittest.TestCase):
    def setUp(self):
        self.contexts = []

    def tearDown(self):
        close_contexts(self.contexts)

    def open_old(self, engine, suffix):
        context = new_context(engine)
        self.contexts.append(context)
        page = context.new_page()
        page.goto(OLD.as_uri() + suffix)
        page.wait_for_url(lambda url: '/fontkit-studio.html' in url)
        return page

    def test_forwards_with_query_and_hash(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                suffix = '?target=http%3A%2F%2Flocalhost%3A9%2F&x=1#composer'
                page = self.open_old(engine, suffix)
                self.assertEqual(page.url, HTML.as_uri() + suffix)
                self.assertTrue(page.title().startswith('Font Kit Studio v'))

    def test_forwards_without_query(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.open_old(engine, '')
                self.assertEqual(page.url, HTML.as_uri())

    def test_stub_is_small_and_names_the_new_file(self):
        text = OLD.read_text(encoding='utf-8')
        self.assertLess(len(text.splitlines()), 20)
        self.assertIn('location.replace("fontkit-studio.html" + location.search + location.hash)', text)
        self.assertIn('<a href="fontkit-studio.html">', text)
```

  Check `support.py`'s helper names (`new_context`, `close_contexts`, `ENGINES`, `HTML`,
  `REPO`) before relying on them; use what is there. Update `support.HTML` to
  `REPO / 'fontkit-studio.html'` first. Run it: RED because the old file is gone (step 1).

- [ ] **3. Write the stub** at `font_kit_studio_v0.1.1.html`:

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Font Kit Studio has moved</title>
<script>location.replace("fontkit-studio.html" + location.search + location.hash);</script>
</head>
<body>
<p>Font Kit Studio is now <a href="fontkit-studio.html">fontkit-studio.html</a>. This page forwards there and goes away in the release after 0.3.0.</p>
</body>
</html>
```

  The forward target is a fixed relative file name; the page's own query and hash are
  appended after it, so no input can change the scheme or host (anti-pattern 4). GREEN.

- [ ] **4. Update live references** to `fontkit-studio.html`:
  `tests/support.py:23`; `tests/test_frontend_gate_helpers.py:214,221`;
  `tests/test_frontend_gate_runner.py:232`; `tests/test_preview_server.py:152,155,170,487,503,524`
  (line 593 is a list of overrides paths the server must refuse: use the new name there,
  since it is the Studio file the case protects); `scripts/serve.py:34`;
  `scripts/dev/_frontend_gate_shared.py:21`; `docs/assets/screenshots/capture.py:87`;
  `README.md:46` and `README.md:66`. Rewrite README line 66's sentence: the file is now
  `fontkit-studio.html`; the old name forwards until the release after 0.3.0.
  Then `git grep -n "font_kit_studio_v0.1.1"` and list every remaining hit in the report
  with why it stays (point-in-time, provenance, the stub, or shared-file Handoff).

- [ ] **5. `scripts/verify.py`.** Set `APP = "fontkit-studio.html"`, add
  `SUPPLIED_APP = "font_kit_studio_v0.1.1.html"  # Studio's name at the supplied-v0.1.1 tag (D041)`,
  and in `provenance()` map `name == SUPPLIED_APP` to that path. Run
  `python scripts/verify.py --static-only`: all PASS lines, provenance still verified.

- [ ] **6. Bridge header.** Insert after line 2 of `fontkit-bridge.js`
  (` * Font Kit Studio — Design Bridge Protocol v1 Target SDK`) the line
  ` * fontkit-bridge.js version 0.2.1`. Run `node --check fontkit-bridge.js`.

- [ ] **7. Failing version tests** `packages/fontkitstudio/test/versions.test.js`:

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

- [ ] **8. Implement** `packages/fontkitstudio/scripts/versions.js`:

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

- [ ] **9. Failing bundle tests** `packages/fontkitstudio/test/bundle.test.js`:

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

- [ ] **10. Implement** `packages/fontkitstudio/scripts/bundle.js`:

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

- [ ] **11. Show the guards bite**: change the bridge header to `0.2.0`, run
  `npm --prefix packages/fontkitstudio test`, record the failing line, restore it.

- [ ] **12. Full gates** (constraints.md), including both suite halves: the rename touches
  every browser test's entry point.

- [ ] **13. Handoff text** (the landing writes these): a CHANGELOG `[Unreleased]` line
  under "Changed" (Studio is `fontkit-studio.html`; the old name forwards until the release
  after 0.3.0); the `AGENTS.md` line 4 file name; the progress.md event.

Commit subject: `refactor(studio): rename Studio to fontkit-studio.html`. Body: why the
name changes (D041: a versionless name that says what the file is and pairs with the
bridge), that the old name forwards for one release, and that the package bundles both
files at one checked version.

## Report

Code phase: `.superpowers/sdd/r1-pr-a/task-2-code-report.md`. Landing:
`docs/implementation/tasks/r1-task-2-report.md`.
