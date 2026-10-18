# R2.7I1 code report (mode: code, BASE bd20e43)

Changed: new `tests/test_r2_entrypoints.py` (314 lines, staged in C:/fks/t7i1). Patch: `task-7i1-code.patch`
(`git apply --check -R` passes). No product code. Cases: `ViteEntrypointTests` (vite8, vite7, build),
`ProxyEntrypointTests` (Bootstrap), `NextEntrypointTests` (Next), plus a non-TestCase `RoundTrip` mixin that holds
open_studio, detect and the shared sequence (guarded context, counts == `{'aborted': 2, 'fallback': 0}`, no pageerror).

Borrowed by assignment (public members only): `test_one_command_vite.OneCommandViteBrowserTest`: start, pump, stop,
wait_badge; `test_one_command_next.OneCommandNextBrowserTest`: start_next, drain, tail, stop_next, start_command,
wait_badge; `test_one_command_proxy.OneCommandProxyBrowserTest`: stop_helper, wait_badge;
`test_vite_build_guarantee.ViteBuildGuaranteeTests`: build; `test_r2_react.ReactCorpusTest`: guarded_context.
`select_title` and `open_studio` are not borrowed. Module constants imported: vite.NODE/PACKAGE/CONNECTED,
prox.NODE/HELPER/FIXTURE/RECORD_VIOLATIONS, nxt.NODE/PACKAGE/APP/LEAD, built.FORBIDDEN.

## Evidence (characterization, GREEN; chromium only, FKS_REQUIRE_FIXTURES=1)
- `python -m unittest test_r2_entrypoints.ProxyEntrypointTests test_r2_entrypoints.ViteEntrypointTests test_support`:
  `Ran 38 tests ... OK`.
- Next class: OK (`Ran 1 test in 8.3s`) but see Concern 1 (run against a scratch copy of the fixture).
- ruff: All checks passed. pre-commit (`python -m pre_commit`): whitespace Passed, ruff Passed, node/static hooks
  skipped (no files).

## Mutants (worktree files restored byte-exact; SHA-256 before == after)
- fontkit-bridge.js `913a4d0b...ef35` before and after for M1, M3, M4. vite-plugin.js `8339a440...8ba17` before/after (M2).
- M1 (clear keeps the sheet: `&& roles.length` on the commit-point remove): Bootstrap, Vite 8, Vite 7, Next all fail at
  `wait_owned(frame, 0)` (Frame.wait_for_function timeout, "owned node count 0").
- M2 (`apply()` returns true AND `studio ?? {origin}`): build test fails
  `b'fontkit-bridge' found in vite7-react/index.html` (vite-react subtest also fails; `FAILED (failures=2)`).
- M3 (bridge removes its sheet on author mutation, in `noteRoleMutations`): fails "still 48px after the rerender":
  Bootstrap `'500' != '700'`, Vite 8 and 7 `'32px' != '48px'`, Next `'40px' != '48px'`.
- M4 (Clear ignores stale `pageVersion`): all four fail at `preview_status` (page-changed text never appears; timeout).

## Deviations and notes
- Frame waits use `polling=50`: the default raf polling stalled in the iframe right after Apply (observed: the same
  expression timed out under raf and passed with polling=50). It is a wait condition, not a sleep.
- The receipt in `#rolePreviewCss` is waited for (it arrives after the sheet installs) before asserting its text.
- The same-handle/disconnected assertion for the owned sheet is applied to all four cases (it holds for Next too).

## Concerns
1. In the worktree the Next fixture's `node_modules` junction makes Turbopack fail ("Symlink [project]/node_modules is
   invalid, it points out of the filesystem root"), so `NextEntrypointTests` errors there. I ran it, and the M1/M3/M4
   mutants, through `work/runnext_7i1.py`, which sets `nxt.APP` to a real copy of the fixture under git-ignored `work/`
   (copy deleted afterwards). On hosted CI (`npm ci`) there is no junction. The controller's tree has real installs.
2. Under the plain Vite and Next fixtures the browser logs a favicon 404 console error; not asserted (only `hydrat` is).
3. Line count 314, under the ~380 budget.

## Handoff
Commit subject: `test: run role round trips through every entrypoint`.
Body draft: Role Detect, Apply, rerender and Clear were proven only against fake origins and bridge-level messages.
These cases drive the real Studio over the real command, the Vite 7 and 8 plugins, the proxy in front of Bootstrap 5
and Next.js, and read what the page renders; a Vite build is scanned for the bridge and role sheet names.
Ledger event: role previews round-trip through every entrypoint (Vite 7/8 command, Bootstrap and Next proxies) and
Vite builds ship no bridge or role CSS.
Workflow steps as in the brief's Handoff (fixtures job: Vite + Proxy classes; next-fixture job: Next class with
NEXT_TELEMETRY_DISABLED). quality-gate discover will skip `ViteEntrypointTests.*` and `NextEntrypointTests.*` when
nothing is installed and run `ProxyEntrypointTests`.
Scratch left in WORKTREE `work/` (git-ignored): mutate_7i1.py, probe_7i1.py, probe2_7i1.py, runnext_7i1.py. No stray
processes (only my shells).

## Controller integration
