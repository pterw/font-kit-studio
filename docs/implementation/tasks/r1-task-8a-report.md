# Task 8a code report (mode: code)

Files (patch `task-8a-code.patch`, 10 files): `packages/fontkitstudio/src/vite-plugin.d.ts` (new),
`packages/fontkitstudio/package.json` (only `exports["./vite"]`), `packages/fontkitstudio/test/package.test.js`,
`tests/test_vite_types.py` (new), `fixtures/vite-ts/{package.json,package-lock.json,tsconfig.json,tsconfig.bad.json,vite.config.ts,bad-usage.ts}`.
Ran `npm install` in `fixtures/vite-ts` (lockfile created) in the worktree. typescript pinned to `7.0.2` (`npm view typescript version` today).

## Deviations
- Added `@types/node` `24.19.1` to the fixture devDependencies, `types: ["node"]` and `target: ES2023` to tsconfig. Without
  them tsc fails inside Vite's and rolldown's own .d.ts (TS2688 / TS2591 / TS2550), as in Vite's template, so the check could never reach 0.
- Brief said Node test "import guard's file scan also reads src/*.d.ts". `sourceFiles` now returns .d.ts too; the
  JS guard skips them (a `.d.ts` would legitimately import `vite`), and a new test applies the stricter rule: only `vite`, only `import type`, no `import(`/`require`.

## Symlink choice
`preserveSymlinks: true` in `tsconfig.json`, commented. Evidence:
- With `preserveSymlinks:false` (scratch config): `../../packages/fontkitstudio/src/vite-plugin.d.ts(1,29): error TS2307: Cannot find module 'vite'`.
- `Plugin` really resolves: scratch `const n: number = fontkitStudio().name;` gives `TS2322: Type 'string' is not assignable to type 'number'`; scratch files deleted.
- `bad-usage.ts(4,7): error TS2322: Type 'Plugin<any>' is not assignable to type 'number'.`

## RED / GREEN
RED (no .d.ts, exports unchanged): `node node_modules/typescript/bin/tsc -p .` (cwd fixtures/vite-ts), exit 1:
`vite.config.ts(2,31): error TS7016: Could not find a declaration file for module 'fontkitstudio/vite'. '.../node_modules/fontkitstudio/src/vite-plugin.js' implicitly has an 'any' type.`
GREEN (after): `tsc -p .` exit 0; `tsc -p tsconfig.bad.json` exit 1 with the TS2322 line above.
`npm --prefix packages/fontkitstudio test`: pass 208, fail 0. `PYTHONPATH=tests FKS_REQUIRE_FIXTURES=1 python -m unittest test_vite_types test_support -v`: Ran 36, OK.

## Mutations (each restored; confirmed byte-identical)
1. Drop `types` from exports: node test fails `exports["./vite"].types is missing`. NOTE: `test_vite_types` still passes here, because
   with `preserveSymlinks` tsc falls back to the sibling `vite-plugin.d.ts` next to the `.js`. The Node test is the guard for `types`.
2. `.d.ts` imports `node:fs`: node test fails `imports node:fs: a declaration may import only vite`. Plain `import { Plugin }` (no `type`): fails `must be an import type`.
3. `fontkitStudio(): any`: `test_misuse_is_a_type_error_not_any` fails (`0 == 0 : bad-usage.ts type-checked: types are any?`).

## Gates
- `python -m ruff check .`: All checks passed.
- pre-commit (`python -m pre_commit run --files ...`; `pre-commit` is not on PATH): whitespace, ruff, node --check Passed; static checks skipped (no files).
- suite-a (`FKS_REQUIRE_FIXTURES=1 ... test_[a-r]*.py`): Ran 445, failures=5, all the missing-fixture guard
  (`fixtures/vite-react|vite7-react/node_modules is missing`; this worktree only has `npm ci` for vite-ts). Not a real failure; rerun in the main checkout. suite-b NOT RUN.
- `npm pack --dry-run --json` file list includes `src/vite-plugin.d.ts` (also bin/fontkitstudio.js, dist/*, src/{cli,csp,open-browser,project,proxy,run-proxy,run-vite,studio-server,vite-plugin}.js, package.json, README.md, LICENSE).
- Lockfile: 1206 lines (churn).

## Self-review
AP 13: no processes started except short tsc runs with timeout. AP 14: fixture test uses `require_fixture`; suite-a result stated honestly above.
Rule 3: package deps untouched; the Node test still passes. D040: n/a. Rule 6: nothing written outside the fixture/worktree.
Note: no-`node_modules` in the patch.

## Handoff
- CI: add `npm ci --prefix fixtures/vite-ts` to the fixtures job install step and `test_vite_types` to its `unittest` list.
- CHANGELOG, Unreleased, Added: "`fontkitstudio/vite` ships TypeScript declarations, so a strict `vite.config.ts` type-checks."
- progress.md event draft: "R1.8a: `fontkitstudio/vite` ships `src/vite-plugin.d.ts`; `fixtures/vite-ts` runs the real tsc (typescript 7.0.2, strict, skipLibCheck off) green on `vite.config.ts` and red on `bad-usage.ts`; Node test guards `exports` types and .d.ts imports."
- Commit subject: `feat(dev): ship types for fontkitstudio/vite`. Body: a strict `tsc -b` in a Vite TypeScript project failed with TS7016 once
  `vite.config.ts` imported `fontkitstudio/vite`; ship a declaration, export it as `types`, and check it with the real compiler on a fixture.
  Mention: fixture adds @types/node; preserveSymlinks for the file: link.

## Fix round 1 (review Minor 1)
- create-vite 9.2.1 (`npm view create-vite version`; template-react-ts) uses `typescript ~6.0.2`, `@types/node ^24.13.3`; `~6.0.2` resolves to 6.0.3 today.
  Fixture now pins `typescript` `6.0.3` (was 7.0.2; @types/node stays 24.19.1).
- `fixtures/vite-ts/tsconfig.json` mirrors the template's `tsconfig.node.json` (`module: nodenext`, es2023 target/lib, `types: ["node"]`,
  verbatimModuleSyntax, moduleDetection force, noUnused*, erasableSyntaxOnly, noFallthrough, allowImportingTsExtensions), plus `strict: true`,
  `skipLibCheck: false`; a comment line names the template and version; `preserveSymlinks` and its comment are kept. (`moduleResolution: bundler` dropped: nodenext implies its own.)
- RED (.d.ts moved away): `vite.config.ts(2,31): error TS7016 ...` exit 2. GREEN (restored): `tsc -p .` exit 0.
  `tsc -p tsconfig.bad.json`: `bad-usage.ts(4,7): error TS2322: Type 'Plugin<any>' is not assignable to type 'number'.` exit 2.
- `test_vite_types test_support`: OK; Node tests: pass 208, fail 0; ruff: All checks passed.
- Patch regenerated at the same path (git apply --check -R passes). New lockfile: 845 lines (was 1206).
