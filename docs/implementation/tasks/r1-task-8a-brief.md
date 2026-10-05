# R1 8a brief: TypeScript declarations for `fontkitstudio/vite`

Plan: `docs/plans/2026-10-04-r1-pr-c-sdd.md` (8a, R1.8a). Constraints:
`.superpowers/sdd/r1-pr-c/constraints.md` (read all of it first). Code:
`packages/fontkitstudio/package.json`, `src/vite-plugin.js`, `test/package.test.js`.

## Goal

Vite's React TypeScript template builds with `tsc -b && vite build` under `strict`. Once a
user adds `import { fontkitStudio } from 'fontkitstudio/vite'` to `vite.config.ts`, that
`tsc` fails with TS7016 ("Could not find a declaration file"), because the package ships no
types. Ship a declaration and prove it with the real TypeScript compiler on a fixture.

## Owns

- `packages/fontkitstudio/src/vite-plugin.d.ts` (new).
- `packages/fontkitstudio/package.json`: only `exports["./vite"]`, which becomes
  `{ "types": "./src/vite-plugin.d.ts", "default": "./src/vite-plugin.js" }`. Keep
  `./package.json`. `files` already ships `src/`.
- Additions to `packages/fontkitstudio/test/package.test.js`.
- `fixtures/vite-ts/` (new):
  - `package.json`, private, with exact `devDependencies`: `vite` `8.3.2`, `typescript` at
    whatever `npm view typescript version` prints today (record it), and `fontkitstudio`
    `file:../../packages/fontkitstudio`;
  - `package-lock.json`;
  - `tsconfig.json`;
  - `vite.config.ts`;
  - `bad-usage.ts`, described below.
- `tests/test_vite_types.py` (new).

## The declaration

```ts
import type { Plugin } from 'vite';
/** Font Kit Studio for `vite` dev servers; left out of `vite build`. */
export declare function fontkitStudio(): Plugin;
```

The options the command passes internally (`studio`, `bridgeFile`, `studioFile`, `log`)
are not public and stay out of the type. Keep the declaration to what a user calls.

## Fixture and type check

- **`tsconfig.json`:**
  - `strict: true`, `noEmit: true`, `module: "ESNext"`, `moduleResolution: "bundler"`
    (as Vite's template);
  - `skipLibCheck: false`, so an error inside the `.d.ts` counts;
  - `include: ["vite.config.ts"]`;
  - a second config `tsconfig.bad.json` that includes `bad-usage.ts`.
- **`vite.config.ts`:** `import { defineConfig } from 'vite'; import { fontkitStudio } from
  'fontkitstudio/vite'; export default defineConfig({ plugins: [fontkitStudio()] });`
- **`bad-usage.ts`:** a wrong use that must not type-check, for example `const n: number =
  fontkitStudio();`.
- **Symlink pitfall.** npm installs a `file:` dependency as a symlink. By default `tsc`
  follows it to `packages/fontkitstudio/src/vite-plugin.d.ts` and then cannot resolve
  `vite` from there, which an installed package never hits.
  - Make the check resolve `vite` the way an installed package does: for example
    `preserveSymlinks: true` in the fixture's tsconfig, with a comment saying why.
  - Or another way you justify.
  - Show which way you chose, and show that `Plugin` really resolves: a deliberate wrong
    plugin property type in a scratch copy errors, rather than the import silently becoming
    `any`.
- **`tests/test_vite_types.py`:**
  - `require_fixture(self, 'vite-ts')`; skip without `node`.
  - Run `node fixtures/vite-ts/node_modules/typescript/bin/tsc -p fixtures/vite-ts`; it
    exits 0.
  - `-p fixtures/vite-ts/tsconfig.bad.json` exits nonzero and names `bad-usage.ts` with a
    `TS2322`-style error.
  - Both run with `cwd` set to the fixture, and with a timeout.
- **Node test** in `test/package.test.js`:
  - `exports["./vite"].types` names a file that exists and lies under a `files` entry.
  - `exports["./vite"].default` is `./src/vite-plugin.js`.
  - The import guard's file scan also reads `src/*.d.ts`. A `.d.ts` may import only
    `vite`, by `import type`; anything else fails.

## Definition of done

- **RED:** with the `.d.ts` absent and `exports` unchanged, `tsc -p fixtures/vite-ts` fails
  with TS7016. Quote it. **GREEN:** after the change. Do this in your worktree after
  `npm install` in `fixtures/vite-ts`; a `file:` link reflects edits at once.
- **Mutations,** each shown failing and restored:
  - drop `types` from `exports`;
  - make the `.d.ts` import a non-`vite` module;
  - return `any` from `fontkitStudio`, so that `bad-usage.ts` passes and the test fails.
- **Also run:**
  - `npm --prefix packages/fontkitstudio test`;
  - `PYTHONPATH=tests python -m unittest test_vite_types test_support -v`;
  - `python -m ruff check .`;
  - `npm pack --dry-run --json` in `packages/fontkitstudio`. The file list must show the
    `.d.ts`; quote it.

## Report

- Code phase report: `.superpowers/sdd/r1-pr-c/task-8a-code-report.md`.
- Patch: `.superpowers/sdd/r1-pr-c/task-8a-code.patch` (no `node_modules`).
- Handoff:
  - **CI.** The fixtures-job change: add `npm ci --prefix fixtures/vite-ts` to its install
    step, and add `test_vite_types` to its `unittest` list.
  - **CHANGELOG.** A line under Unreleased, Added: "`fontkitstudio/vite` ships TypeScript
    declarations, so a strict `vite.config.ts` type-checks."
  - **Ledger.** A `progress.md` event draft.
  - **Commit.** The subject `feat(dev): ship types for fontkitstudio/vite`, with a why-body.
  - **Lockfile size.** The lockfile's line count, which is churn.
