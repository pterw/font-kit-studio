### Spec Compliance
- PASS: fixtures/vite-react (vite 8.3.2) and fixtures/vite7-react (vite 7.3.6); react and react-dom 19.3.0, no carets (package.json:6-7 in each). Lockfiles resolve to vite 8.3.2 / rolldown 1.2.12 and vite 7.3.6 / esbuild 0.28.2, react and react-dom 19.3.0.
- PASS: no @vitejs/plugin-react in either lockfile.
- PASS: fixture files match the brief verbatim. index.html has only the module script; vite.config.js imports the plugin by relative path; main.jsx and App.jsx have explicit `import React`; data-design-ids vite.hero.title, vite.hero.lead and vite.hero.cta are present; the button keeps useState (App.jsx:1-12). The two fixtures differ only in name and Vite version.
- PASS: tests/fixture_support.py matches the interface (FIXTURES, require_fixture, vite_bin) and the exact skip and fail texts. It imports only os and pathlib, not `support` (checked at run time: `support` and `playwright` are not in sys.modules after import).
- PASS: tests/test_vite_build_guarantee.py follows step 3. The command is an args list with no shell, cwd is the fixture, timeout=180, capture_output, text and encoding utf-8; the temp dir is cleaned with addCleanup; the return code is asserted. FORBIDDEN is exactly the four byte strings in the brief. Every file under out is read as bytes. The positive control checks `vite.hero.title` in some file and `<script type="module"` in index.html.
- PASS: CI job text matches the brief's YAML (quality-gate.yml +29 lines). It is appended after node-package; the other jobs are untouched. There are no secrets and no extra permissions (the workflow-level `contents: read` is unchanged). Both npm ci --prefix steps, the prepack step, FKS_REQUIRE_FIXTURES='1' and PYTHONPATH: tests are present. The glob `fixtures/*/package-lock.json` is valid for setup-node.
- PASS: .gitignore has exactly the two lines. node_modules and dist are absent from the patch (the patch file list shows no such paths).
- PASS: the brief's other items are done (the report's evidence matches what I re-ran below).

### Checks run
- Build guarantee GREEN -> `PYTHONPATH=tests python -m unittest test_vite_build_guarantee -v` in C:/fks/tB3a -> 2 tests OK (2.6 s).
- Mutation credibility (the worktree must not be edited) -> scratch copy under the scratchpad (tests, plugin src, both fixtures, node_modules junctioned to the worktree's). In the plugin I removed `apply: 'serve'`, made transformIndexHtml always tag, and used a placeholder origin of http://127.0.0.1:1. Result: FAILED (failures=2). The failure shows the built index.html carrying `<script src="/@fontkit/fontkit-bridge.js" data-allowed-origins="http://127.0.0.1:1">`, so the scan reads the real built output and catches the leak on both majors. The report's mutation claim is credible.
- require_fixture texts -> python harness over a nonexistent fixture name. With the env var unset or '0' the result is skip `run npm ci in fixtures/nonexistent`. With FKS_REQUIRE_FIXTURES=1 it fails with `fixtures/nonexistent/node_modules is missing and FKS_REQUIRE_FIXTURES=1: run npm ci in fixtures/nonexistent`. There is no path where CI passes by skipping: the CI job sets '1', and `fail` is raised before `skipTest`.
- Lockfiles -> parsed the patch JSON. Only react, react-dom, scheduler, vite and Vite's dependencies appear. For Vite 8 these are rolldown, @rolldown/*, @oxc-project/types, lightningcss*, postcss, nanoid, picocolors, picomatch, fdir, tinyglobby, source-map-js, detect-libc and fsevents. For Vite 7 these are esbuild, @esbuild/*, rollup, @rollup/*, @types/estree, and @napi-rs/lzma-linux-x64-gnu (checked: it is rollup 4.64's own optionalDependency). The only registry host is registry.npmjs.org. Every non-root package has resolved and integrity fields (43 of 43 and 67 of 67). Nothing unexpected.
- Discovery risk (a v-named module falls into suite-b's `test_[s-z]*.py` glob) -> the module skips where fixtures are not installed, and CI's fixtures job is the only place the env var is set. No false failure elsewhere; the test_support run in the report passed (36 tests).
- Subprocess leaks -> subprocess.run runs to completion with a timeout. The plugin starts its Studio server only in configureServer, which `vite build` never calls, and the mutation shows the plugin is the only path for that.

### Strengths
- The positive control makes the scan non-vacuous, and the mutation fails on both Vite majors with the leaked file named.
- The fixture_support skip/fail split is minimal and safe against CI skipping, and it avoids the Playwright-importing module.
- The fixtures are tiny, pinned and plugin-free, with a clean lockfile.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- tests/test_vite_build_guarantee.py:38: assertNotIn with a custom msg also prints the whole file bytes repr (seen in the mutation output); on a real regression with a large bundle the failure is very noisy. Asserting `needle in data` as a boolean with the message would be tidier.
- tests/test_vite_build_guarantee.py:10: `NODE = shutil.which('node')` is None when node is missing, giving a TypeError in subprocess.run rather than a clear skip or fail. Not reachable in CI (setup-node); local-only polish.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The build guarantee reads real output and fails under the brief's mutation on both Vite majors; require_fixture, the fixtures, the CI job and the .gitignore lines match the brief with no deviations. Only cosmetic Minor findings remain.
