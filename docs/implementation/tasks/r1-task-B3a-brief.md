# R1 B3a brief: Vite fixtures, the build guarantee and the CI job

Plan: `docs/plans/2026-10-04-r1-pr-b-sdd.md` (B3a, R1.4c; After: B1, B2); what R1 builds:
`docs/plans/2026-10-03-r1-one-command.md` (R1.4, R1.7 addendum 2). Constraints:
`.superpowers/sdd/r1-pr-b/constraints.md` (read all of it first). Builds on B2's plugin
(`packages/fontkitstudio/src/vite-plugin.js`, read it first).

## Goal

Two small React apps on the project's own Vite, one on Vite 8 and one on Vite 7, with
`fontkitStudio()` in their `vite.config.js` the way a user adds it permanently. They are
the real projects that B3b's command and later tasks run against. This task proves the
first product promise on both: `vite build` output carries nothing from Font Kit Studio
(spec 4.2, "never in production"). A new CI job installs both fixtures and runs their
tests with `FKS_REQUIRE_FIXTURES=1`, so CI can never pass by skipping (anti-pattern 14).

## Definition of done

- `fixtures/vite-react/` (Vite 8.3.2) and `fixtures/vite7-react/` (Vite 7.3.6) build and
  run with `npm ci` then `npx vite`; React and ReactDOM 19.3.0; exact versions (no `^`).
- `tests/test_vite_build_guarantee.py` builds each fixture with its config (plugin
  included) and finds no trace of Font Kit Studio in any output file, with a positive
  control that proves the scan read the real bundle.
- Mutation evidence: with `apply: 'serve'` removed and `transformIndexHtml` made to return
  the tag even with no Studio known (placeholder origin `http://127.0.0.1:1`), the test
  fails; restored by editing.
- Locally without `node_modules` the module skips with
  `run npm ci in fixtures/<name>`; with `FKS_REQUIRE_FIXTURES=1` it fails instead (show
  both in the report).
- The `fixtures` CI job exists and the YAML parses (`python -c "import yaml"` is not
  available; check with `node -e` or by reading it carefully, and say which).

## Owns

`fixtures/vite-react/**`, `fixtures/vite7-react/**` (except `node_modules/` and
`dist/`), `tests/test_vite_build_guarantee.py`, `tests/fixture_support.py`, the new
`fixtures` job in `.github/workflows/quality-gate.yml` (do not edit the other jobs), and
two lines in `.gitignore` (`fixtures/*/node_modules/`, `fixtures/*/dist/`).

## Interface (binding; B3b imports it)

```python
# tests/fixture_support.py
FIXTURES = REPO / 'fixtures'
def require_fixture(test_case, name):
    """Skip the test when fixtures/<name>/node_modules is missing; fail instead when
    FKS_REQUIRE_FIXTURES=1 (CI), so a fixture test can never pass by skipping."""
def vite_bin(name) -> Path:   # fixtures/<name>/node_modules/vite/bin/vite.js
```

Messages: skip reason `run npm ci in fixtures/<name>`; failure
`fixtures/<name>/node_modules is missing and FKS_REQUIRE_FIXTURES=1: run npm ci in fixtures/<name>`.
Do not import `support` (it starts Playwright); compute `REPO` from `__file__`.

## Fixture files (both fixtures; only the Vite version and the name differ)

`package.json`:

```json
{
  "name": "fks-fixture-vite-react",
  "private": true,
  "type": "module",
  "scripts": { "dev": "vite", "build": "vite build" },
  "dependencies": { "react": "19.3.0", "react-dom": "19.3.0" },
  "devDependencies": { "vite": "8.3.2" }
}
```

(`fks-fixture-vite7-react` and `"vite": "7.3.6"` for the other.) Generate
`package-lock.json` with `npm install` in the fixture folder (churn, D050); never commit
`node_modules`.

`vite.config.js`:

```js
// The permanent setup a user adds; imported by path so the fixture needs no install of
// the package. `vite build` must leave it out entirely (apply: 'serve').
import { fontkitStudio } from '../../packages/fontkitstudio/src/vite-plugin.js';

export default { plugins: [fontkitStudio()] };
```

`index.html`: a `<!doctype html>` page, `<title>Vite fixture</title>`,
`<div id="root"></div>`, `<script type="module" src="/src/main.jsx"></script>`. No other
script.

`src/main.jsx`:

```jsx
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import './app.css';

createRoot(document.getElementById('root')).render(<App />);
```

`src/App.jsx`: `import React, { useState } from 'react';` (explicit, so JSX works whether
Vite's default JSX runtime is classic or automatic; no `@vitejs/plugin-react`, to keep the
lockfile small); an `<h1 data-design-id="vite.hero.title">Type that fits the page</h1>`, a
`<p data-design-id="vite.hero.lead">` paragraph, and a
`<button data-design-id="vite.hero.cta">` that counts clicks with `useState` (B3b's hot
update test needs state). `src/app.css`: a few plain rules (system font stack, max width).

## Steps

- [ ] **1. Fixtures** as above; `npm install` in each; `npx vite build` in each by hand to
  see JSX compile; record the Vite and esbuild/oxc versions npm installed.
- [ ] **2. `tests/fixture_support.py`** to the interface.
- [ ] **3. Failing test** `tests/test_vite_build_guarantee.py`, one test per fixture
  (`subTest` is fine): `require_fixture`; build with
  `[node, str(vite_bin(name)), 'build', '--outDir', out, '--emptyOutDir']`, `cwd` the
  fixture, `out` a `tempfile.mkdtemp()` removed in `addCleanup`, `timeout=180`,
  `capture_output=True, text=True`, `encoding='utf-8'`; assert return code 0 (print
  stderr on failure). Walk every file under `out` as bytes: assert none contains
  `b'fontkit-bridge'`, `b'@fontkit'`, `b'data-allowed-origins'` or `b'Font Kit Studio'`;
  positive control: some file contains `b'vite.hero.title'` and `index.html` contains a
  `<script type="module"`. The process returning at all proves the build started no
  Studio server that kept it alive. RED first: run the module before the fixture exists
  (it fails or skips; say which), then the mutation from the definition of done.
- [ ] **4. CI job** in `.github/workflows/quality-gate.yml`, after `node-package`:

```yaml
  fixtures:
    name: Fixtures (Vite 7 and 8)
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '24'
          cache: npm
          cache-dependency-path: fixtures/*/package-lock.json
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install the fixtures
        run: |
          npm ci --prefix fixtures/vite-react
          npm ci --prefix fixtures/vite7-react
      - name: Bundle Studio and the bridge
        run: npm --prefix packages/fontkitstudio run prepack
      - name: Fixture tests (never skipped here)
        env:
          FKS_REQUIRE_FIXTURES: '1'
          PYTHONPATH: tests
        run: python -m unittest test_vite_build_guarantee -v
```

  B3b and B5 add their modules to the last step; Playwright is installed by the task that
  first needs a browser here (B3b).
- [ ] **5. GREEN** on both fixtures; then `FKS_REQUIRE_FIXTURES=1` with one fixture's
  `node_modules` renamed away shows the failure text (rename back after).
- [ ] **6. Gates for the code phase:** `PYTHONPATH=tests python -m unittest
  test_vite_build_guarantee test_support -v`; `python -m ruff check .`;
  `npm --prefix packages/fontkitstudio test`. The controller's gate-runners run suite-a and
  suite-b at landing.
- [ ] **7. Report** with a Handoff: the patch (lockfiles included; list them as churn
  with their line counts), a `progress.md` event draft, the commit subject
  `test: build two Vite fixtures and prove the bridge stays out of builds` and a why-body
  (the plugin is added permanently by users, so `vite build` with it must ship nothing of
  Font Kit Studio; both tested Vite majors; CI installs the fixtures and refuses to skip).

## Report

Code phase: `.superpowers/sdd/r1-pr-b/task-B3a-code-report.md`, patch
`.superpowers/sdd/r1-pr-b/task-B3a-code.patch`. Landing:
`docs/implementation/tasks/r1-task-B3a-report.md`.
