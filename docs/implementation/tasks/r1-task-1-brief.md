# R1.1 brief: package skeleton

Plan: `docs/plans/2026-10-03-r1-one-command.md` (R1.1); execution:
`docs/plans/2026-10-04-r1-pr-a-sdd.md`. Constraints:
`.superpowers/sdd/r1-pr-a/constraints.md` (read all of it first).

## Goal

`packages/fontkitstudio/` exists as an installable, zero-dependency ESM package with a
`fontkitstudio` bin that answers `--version` and `--help`, tests on Node's built-in runner,
and a CI job that runs them on the Node and OS matrix of D043.

## Definition of done

- `npm --prefix packages/fontkitstudio test` passes locally (Node 24).
- A test fails if `package.json` gains a runtime dependency (spec 4.5), and another fails
  if code under `bin/` or `src/` imports anything but `node:*` or a relative path.
- `node packages/fontkitstudio/bin/fontkitstudio.js --version` prints `0.2.1`.
- `.github/workflows/quality-gate.yml` has a new `node-package` job: Ubuntu on Node 22,
  24 and 26; macOS and Windows on Node 24. The existing job is untouched.
- RED/GREEN evidence for the dependency guard and the import guard.

## Owns

`packages/fontkitstudio/package.json`, `packages/fontkitstudio/README.md`,
`packages/fontkitstudio/bin/fontkitstudio.js`, `packages/fontkitstudio/src/cli.js`,
`packages/fontkitstudio/test/package.test.js`, `packages/fontkitstudio/test/cli.test.js`,
`.github/workflows/quality-gate.yml` (a new job only).

## Steps

- [ ] **1. Write `package.json`.**

```json
{
  "name": "fontkitstudio",
  "version": "0.2.1",
  "description": "Font Kit Studio: try type on your running web app, in development only.",
  "license": "MIT",
  "type": "module",
  "bin": { "fontkitstudio": "bin/fontkitstudio.js" },
  "exports": { "./package.json": "./package.json" },
  "files": ["bin/", "src/", "dist/"],
  "engines": { "node": ">=22.12" },
  "repository": {
    "type": "git",
    "url": "git+https://github.com/pterw/font-kit-studio.git",
    "directory": "packages/fontkitstudio"
  },
  "homepage": "https://github.com/pterw/font-kit-studio#readme",
  "scripts": { "test": "node --test test/*.test.js" }
}
```

The test glob is unquoted on purpose: `sh` expands it on Linux and macOS, and on Windows
`cmd` passes it through and Node expands it. Helpers in `test/helpers/` are not matched.

- [ ] **2. Write the failing package tests** in `test/package.test.js`:

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const PKG_DIR = fileURLToPath(new URL('..', import.meta.url));
const pkg = JSON.parse(readFileSync(join(PKG_DIR, 'package.json'), 'utf8'));

test('has no runtime dependencies (spec 4.5, D030)', () => {
  for (const field of ['dependencies', 'optionalDependencies', 'bundleDependencies',
    'bundledDependencies', 'devDependencies']) {
    const value = pkg[field];
    assert.ok(value === undefined || Object.keys(value).length === 0,
      `${field} must stay empty: Font Kit Studio ships with zero dependencies`);
  }
  const peers = Object.keys(pkg.peerDependencies ?? {});
  for (const name of peers) {
    assert.equal(name, 'vite', `only the project's own Vite may be a peer, found ${name}`);
    assert.equal(pkg.peerDependenciesMeta?.[name]?.optional, true,
      `peer ${name} must be optional so npm never installs it`);
  }
});

function sourceFiles(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? sourceFiles(path) : path.endsWith('.js') ? [path] : [];
  });
}

const SPECIFIER = /\bimport\s*(?:[^'"()]*?\bfrom\s*)?['"]([^'"]+)['"]|\bimport\(\s*['"]([^'"]+)['"]\s*\)|\brequire\(\s*['"]([^'"]+)['"]\s*\)/g;

test('shipped code imports only node built-ins and its own files', () => {
  for (const file of ['bin', 'src'].flatMap((dir) => sourceFiles(join(PKG_DIR, dir)))) {
    for (const match of readFileSync(file, 'utf8').matchAll(SPECIFIER)) {
      const spec = match[1] ?? match[2] ?? match[3];
      assert.ok(spec.startsWith('node:') || spec.startsWith('.'),
        `${file} imports ${spec}: only node:* and relative imports are allowed`);
    }
  }
});

test('declares what npm needs to run and ship it', () => {
  assert.equal(pkg.type, 'module');
  assert.equal(pkg.engines.node, '>=22.12');
  assert.equal(pkg.bin.fontkitstudio, 'bin/fontkitstudio.js');
  assert.deepEqual(pkg.files, ['bin/', 'src/', 'dist/']);
  const bin = readFileSync(join(PKG_DIR, pkg.bin.fontkitstudio), 'utf8');
  assert.ok(bin.startsWith('#!/usr/bin/env node\n'), 'the bin needs a node shebang');
});
```

- [ ] **3. Run and see it fail** (no bin yet): `npm --prefix packages/fontkitstudio test`.
  Expected: the third test fails with ENOENT on `bin/fontkitstudio.js`.

- [ ] **4. Write the CLI test** in `test/cli.test.js`:

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const BIN = fileURLToPath(new URL('../bin/fontkitstudio.js', import.meta.url));
const { version } = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
const run = (...args) => spawnSync(process.execPath, [BIN, ...args], { encoding: 'utf8' });

test('--version prints the package version', () => {
  const result = run('--version');
  assert.equal(result.status, 0);
  assert.equal(result.stdout, `${version}\n`);
});

test('--help prints usage', () => {
  const result = run('--help');
  assert.equal(result.status, 0);
  assert.match(result.stdout, /^Usage: fontkitstudio/);
});

test('an unknown argument exits 2 and names it', () => {
  const result = run('--bogus');
  assert.equal(result.status, 2);
  assert.match(result.stderr, /unknown argument "--bogus"/);
  assert.match(result.stderr, /Usage: fontkitstudio/);
});
```

- [ ] **5. Implement** `bin/fontkitstudio.js`:

```js
#!/usr/bin/env node
import { main } from '../src/cli.js';

process.exitCode = await main(process.argv.slice(2), { out: process.stdout, err: process.stderr });
```

and `src/cli.js`:

```js
import { readFileSync } from 'node:fs';

const { version } = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));

export const USAGE = `Usage: fontkitstudio [--help] [--version]

Font Kit Studio ${version}: try type on your running web app, in development only.
`;

// Returns the exit code; R1.4 adds the runners behind the no-argument form.
export async function main(argv, { out, err }) {
  const [arg] = argv;
  if (argv.length === 1 && (arg === '--version' || arg === '-v')) {
    out.write(`${version}\n`);
    return 0;
  }
  if (argv.length === 0 || (argv.length === 1 && (arg === '--help' || arg === '-h'))) {
    out.write(USAGE);
    return 0;
  }
  err.write(`fontkitstudio: unknown argument ${JSON.stringify(arg)}\n\n${USAGE}`);
  return 2;
}
```

- [ ] **6. Run until green.** Then show each guard bites: add `"dependencies": {"left-pad": "1.0.0"}`
  to `package.json`, run, record the failing assertion, remove it; add
  `import 'left-pad';` to `src/cli.js`, run, record the failure, remove it.

- [ ] **7. Write `packages/fontkitstudio/README.md`** (npm shows it): one paragraph saying what
  Font Kit Studio is, that the one command arrives in 0.3.0, and a link to the repository
  README. Say "Font Kit Studio", not bare "fontkit" (D040), and say `fontkit-bridge.js`
  belongs to Font Kit Studio, not to the `fontkit` font engine on npm.

- [ ] **8. Add the CI job** to `.github/workflows/quality-gate.yml`, after the existing job,
  matching its comment style:

```yaml
  # The npm package (packages/fontkitstudio): zero dependencies, so no install
  # step. Node lines and systems are fixed by D043.
  node-package:
    name: Node package (${{ matrix.os }}, Node ${{ matrix.node }})
    runs-on: ${{ matrix.os }}
    timeout-minutes: 10
    strategy:
      fail-fast: false
      matrix:
        include:
          - { os: ubuntu-latest, node: '22' }
          - { os: ubuntu-latest, node: '24' }
          - { os: ubuntu-latest, node: '26' }
          - { os: macos-latest, node: '24' }
          - { os: windows-latest, node: '24' }
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}
      - name: Test the package
        working-directory: packages/fontkitstudio
        run: npm test
```

  Check the YAML parses: `python -c "import yaml"` may be missing; if so, verify by reading
  it back and by `node -e` with no parser; say which you did.

- [ ] **9. Gates and commit** (constraints.md). Subject:
  `feat(dev): add the fontkitstudio package skeleton`. The body says why: a zero-dependency
  package is the base for `npx fontkitstudio` (R1), and the guard tests hold rule 8.

## Report

`docs/implementation/tasks/r1-task-1-report.md` (format in your agent instructions).
