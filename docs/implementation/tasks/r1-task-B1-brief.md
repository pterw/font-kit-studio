# R1 B1 brief: find and check the project's own Vite

Plan: `docs/plans/2026-10-04-r1-pr-b-sdd.md` (B1, R1.4a); what R1 builds:
`docs/plans/2026-10-03-r1-one-command.md` (R1.4). Constraints:
`.superpowers/sdd/r1-pr-b/constraints.md` (read all of it first).

## Goal

`packages/fontkitstudio/src/project.js` finds the user's project from the folder the
command runs in, says whether it is a Vite project, and finds and loads the project's own
Vite (never a copy of ours: zero dependencies, D030). Every failure is a `ProjectError`
whose message says what is wrong and what to do; no stack trace reaches the user. Vite 7
and 8 are the tested majors; any other is refused with a message naming them (D043).

`src/project.js` is the only shipped file allowed to load code by a computed path. B1
extends the R1.1 import guard so that stays true.

## Definition of done

- Node tests in `test/project.test.js` cover every row of the table below, the
  subdirectory case, both `isViteProject` signals and `loadVite`. Each test fails if the
  code it covers is removed (RED, then GREEN).
- Mutation evidence, one at a time, each named in the report with the failing test:
  the major check (accept every major), the invalid-JSON catch (let `JSON.parse` throw),
  and the new guard (add `await import(x)` to `src/cli.js`).
- `test/package.test.js` gains the computed-load guard; the existing guards still pass.
- No CLI wiring (B3b does that), no change to `package.json`.

## Owns

`packages/fontkitstudio/src/project.js`, `packages/fontkitstudio/test/project.test.js`,
`packages/fontkitstudio/test/helpers/fake-project.js`, and one new test in
`packages/fontkitstudio/test/package.test.js` (do not change the existing tests there).

## Interface (binding; B3b and B6 build on it)

```js
export const TESTED_VITE_MAJORS = [7, 8];
export class ProjectError extends Error {}     // name 'ProjectError'
// Nearest folder at or above startDir that holds a package.json.
export function findProjectDir(startDir): string;              // throws ProjectError
// true when the nearest project lists vite in dependencies or devDependencies, or has a
// vite.config.{js,mjs,cjs,ts,mts,cts}; false when there is no package.json at all.
export function isViteProject(startDir): boolean;              // throws ProjectError on bad JSON
export function findVite(startDir): { projectDir, version, major, entryUrl };   // throws ProjectError
// import()s entryUrl; the only computed import in the package.
export async function loadVite(startDir): Promise<{ vite, projectDir, version, major }>;
```

`entryUrl` is a `file:` URL string. Resolve through the project, never through this
package:

```js
const require = createRequire(join(projectDir, 'package.json'));
const pkgPath = require.resolve('vite/package.json');   // Vite 7 and 8 export ./package.json
const entry = require.resolve('vite');                  // exports["."] is a plain path in 7 and 8
```

`major` is `Number.parseInt(version, 10)` (so `8.0.0-beta.2` is 8).

## Messages (exact text; `<...>` is filled in)

| Case | `ProjectError.message` |
|---|---|
| No `package.json` at or above the folder | `No package.json in <startDir> or a folder above it. Run Font Kit Studio from your project's folder.` |
| `package.json` is not JSON | `<path to package.json> is not valid JSON, so Font Kit Studio cannot read the project.` |
| Vite not resolvable from the project | `Vite is not installed in <projectDir>. Run npm install there, then try again.` |
| Untested major | `This project uses Vite <version>. Font Kit Studio is tested with Vite 7 and 8; use one of those versions.` (build "7 and 8" from `TESTED_VITE_MAJORS`) |

Never include `error.stack` or the parser's message (it can quote file contents).

## Steps

- [ ] **1. Fake projects** `test/helpers/fake-project.js`:

```js
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

// A project folder in a temp dir. vite: a version string for a fake node_modules/vite, or null.
export function fakeProject({ vite = '8.3.2', field = 'devDependencies', packageJson, config } = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'fks-project-'));
  const pkg = { name: 'app', private: true, [field]: vite ? { vite: `^${vite}` } : {} };
  writeFileSync(join(dir, 'package.json'), packageJson ?? JSON.stringify(pkg, null, 2));
  if (config) writeFileSync(join(dir, config), 'export default {};\n');
  if (vite) {
    const viteDir = join(dir, 'node_modules', 'vite');
    mkdirSync(join(viteDir, 'dist', 'node'), { recursive: true });
    writeFileSync(join(viteDir, 'package.json'), JSON.stringify({
      name: 'vite', version: vite, type: 'module',
      exports: { '.': './dist/node/index.js', './package.json': './package.json' },
    }));
    writeFileSync(join(viteDir, 'dist', 'node', 'index.js'),
      `export const version = ${JSON.stringify(vite)};\nexport function createServer() { return 'fake'; }\n`);
  }
  return dir;
}
```

- [ ] **2. Failing tests** `test/project.test.js` (`node:test`, `assert/strict`; remove every
  temp dir in `after`/`t.after` with `rmSync(dir, { recursive: true, force: true })`):
  1. Vite 7.3.6 and 8.3.2: `findVite` returns the version, the major, `projectDir` equal to
     the fake dir, and an `entryUrl` that starts with `file:` and ends with
     `node_modules/vite/dist/node/index.js`;
  2. Vite 6.4.0 and 9.0.0: `ProjectError` with the untested-major text (assert the whole
     message, and `error instanceof ProjectError`);
  3. no `node_modules/vite`: the not-installed text naming the folder;
  4. `findVite(join(dir, 'src', 'deep'))` (create the folders) resolves the project at `dir`;
  5. `findProjectDir` on a fresh `mkdtempSync` dir with no `package.json`: the exact
     no-package text. If a `package.json` exists in a folder above `os.tmpdir()` on the
     machine, skip this one test with `t.skip('package.json above <tmpdir>')` (and say so
     in the report);
  6. hostile: `packageJson: '{ "name": "app", '` (not JSON): `findVite` and `isViteProject`
     both throw `ProjectError` with the invalid-JSON text, and the message does not contain
     `SyntaxError` or `"name"`;
  7. `isViteProject`: true with vite in `dependencies`, true with it in `devDependencies`,
     true with no vite dependency but `config: 'vite.config.ts'`, false with neither
     (`vite: null`), false with no `package.json` (fresh temp dir, normal case);
  8. `loadVite` on the 8.3.2 fake returns `vite.createServer()` equal to `'fake'` and
     `vite.version` equal to `'8.3.2'`;
  9. `TESTED_VITE_MAJORS` deep-equals `[7, 8]`.
  Run `node --test test/project.test.js` from `packages/fontkitstudio`: RED (module missing).

- [ ] **3. Implement** `src/project.js` to the interface and the table. Keep it flat
  (global rule 8): small functions, `node:fs`, `node:module`, `node:path`, `node:url` only.
  `isViteProject` returns false when `findProjectDir` finds nothing and no `vite.config.*`
  sits in `startDir`; it lets the invalid-JSON `ProjectError` through.

- [ ] **4. GREEN**, then the three mutations from the definition of done, each restored by
  editing (no `git stash`).

- [ ] **5. The guard** in `test/package.test.js` (add, do not reorder the existing tests):

```js
// The project's own Vite is loaded by a computed path (createRequire + import()); only
// src/project.js may do that, so every other file stays checkable by the guard above.
test('only src/project.js loads code by a computed path', () => {
  const allowed = join(PKG_DIR, 'src', 'project.js');
  for (const file of ['bin', 'src'].flatMap((dir) => sourceFiles(join(PKG_DIR, dir)))) {
    if (file === allowed) continue;
    const text = readFileSync(file, 'utf8');
    assert.doesNotMatch(text, /\bcreateRequire\b/, `${file} uses createRequire`);
    assert.doesNotMatch(text, /\bimport\(\s*(?!['"])/, `${file} has a computed import()`);
    assert.doesNotMatch(text, /\brequire\(\s*(?!['"])/, `${file} has a computed require()`);
  }
});
```

  Mutation: add `await import(process.argv[2]);` to `src/cli.js`, run, record the failure,
  restore.

- [ ] **6. Gates for the code phase:** `npm --prefix packages/fontkitstudio test` (the
  whole Node suite; quote the `fail 0` line) and `node --check` on each new file. No
  Python gates (no Python changes).

- [ ] **7. Report** with a Handoff: the patch, a `progress.md` event draft, and the commit
  subject `feat(dev): find and check the project's own Vite` with a why-body (the command
  must use the project's Vite, not a bundled one, D030; untested majors are refused with a
  message, D043; one file holds the computed import so the import guard keeps meaning
  something).

## Report

Code phase: `.superpowers/sdd/r1-pr-b/task-B1-code-report.md`, patch
`.superpowers/sdd/r1-pr-b/task-B1-code.patch`. Landing:
`docs/implementation/tasks/r1-task-B1-report.md`.
