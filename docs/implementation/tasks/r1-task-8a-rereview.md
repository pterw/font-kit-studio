### Re-review of Minor 1 (fixture vs Vite's template)

- PASS: tsconfig matches create-vite 9.2.1 `template-react-ts/tsconfig.node.json` (re-read from the packed tarball). Same options: target es2023, lib ES2023, types node, module nodenext, allowImportingTsExtensions, verbatimModuleSyntax, moduleDetection force, noEmit, noUnusedLocals, noUnusedParameters, erasableSyntaxOnly, noFallthroughCasesInSwitch. Deliberate differences, all stricter or neutral: `strict: true` added, `skipLibCheck: false` (template true), `preserveSymlinks` kept with its comment, `tsBuildInfoFile` omitted (only matters for `tsc -b`, and `noEmit` is set) (fixtures/vite-ts/tsconfig.json).
- PASS: typescript pinned 6.0.3 in package.json and package-lock.json:745-746, which is what `~6.0.2` resolves to; installed copy reports `Version 6.0.3`. Lockfile now 845 lines.
- PASS: `tsc -p .` in C:/fks/t8a/fixtures/vite-ts exits 0.
- PASS: `tsc -p tsconfig.bad.json` exits 2 with `bad-usage.ts(4,7): error TS2322: Type 'Plugin<any>' is not assignable to type 'number'.` So `Plugin` resolves to Vite's type, not `any`.
- PASS: `--traceResolution` shows `fontkitstudio/vite` matched on condition `types`, subpath `./vite`, target `./src/vite-plugin.d.ts`, under nodenext.
- PASS: `PYTHONPATH=tests python -m unittest test_vite_types` -> 2 tests OK.
- Nothing started that needs stopping (short tsc and unittest runs only).
- Residual (Minor, no action): the fixture no longer covers TypeScript 7 or `moduleResolution: bundler`; I checked both earlier in the first review and they passed, and the template a user starts from is TS 6 with nodenext, which is now what is tested.

**Task quality:** Approved
