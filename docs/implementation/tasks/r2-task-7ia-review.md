### Spec Compliance
- PASS: Only two steps were added, to job `quality-gate`; nothing else in the file changed. PyYAML on BASE blob f157dee vs the working file: steps 18 -> 20; the 18 BASE steps are equal as parsed dicts and in the same relative order; the other three jobs, all top-level keys and the job's non-step keys (`runs-on`, `timeout-minutes: 30`) are equal. The DIFF is 16 insertions and 0 deletions (one hunk, @@ -155,6 +155,22 @@; quality-gate.yml:158-173 after the change).
- PASS: Step 1 `Install the React CSS-module fixture` runs exactly `npm ci --prefix fixtures/vite-react-css-modules` (quality-gate.yml:162-164).
- PASS: Step 2 `React CSS-module fixture tests (blocking, never skipped here)` runs exactly `python -m unittest test_r2_react -v` with env `FKS_ENGINES: chromium`, `FKS_REQUIRE_FIXTURES: '1'`, `PYTHONPATH: tests`, all parsed as strings, and no other env (quality-gate.yml:166-172).
- PASS: Placement. Parsed step order is [14] Run tests (Chromium, blocking), [15] Install the React CSS-module fixture, [16] React CSS-module fixture tests, [17] Prepare the localhost cookie fixture, [18] Run Firefox canary. The cookie step's own comment (174-175) still sits directly above its step.
- PASS: Both new steps carry `if: ${{ !cancelled() }}` (163, 167), the same expression as the suite (152), cookie (177), canary (190) and upload (204) steps. Neither has `continue-on-error` or `timeout-minutes`. The only `continue-on-error` in the job is still the Firefox canary's, unchanged.
- PASS: The change matches the plan text it cites: R2.7Ia (docs/plans/2026-10-03-r2-engine.md at afd64be, lines 1194-1204) "Install ... with `npm ci` in the job that runs the Chromium suite, and run `test_r2_react` there with `FKS_REQUIRE_FIXTURES=1` ... Preserve every existing install and test", and Addendum 17 item 4 (381-387) "its own step after the suite". The only addition beyond the brief is a 4-line explanatory comment, in the file's existing comment style.
- CANNOT VERIFY FROM DIFF: the hosted outcome (`Ran 5 tests` and `OK` in the new step). The brief defers it to the exact-head run and the report says so; I did not run browser tests.

### Checks run
Item 2, required-fixture semantics
- Does a missing install fail instead of skip? -> read tests/fixture_support.py:13-24 -> with FKS_REQUIRE_FIXTURES == '1' and no node_modules it calls `test_case.fail(...)`; otherwise `skipTest`. The step sets the string '1' (parsed type str).
- Do all four corpus cases reach that check? -> read tests/test_r2_react.py:143-146 (`app()` calls `require_fixture` before anything else) and 188-190, 193-196, 217-219, 241-243 (each test enters `self.app(engine)` inside `subTest`) -> a missing install is a subtest failure in all four, never a skip.
- Any vacuous-pass path (empty engine loop, missing node or browser)? -> read tests/support.py:22-35 -> `parse_engines` raises on an empty or unknown FKS_ENGINES; the step sets `chromium`, so each loop runs once. `assertIsNotNone(NODE)` (test_r2_react.py:58) and browser launch errors fail; none skip. No path to a green skip.
- Does a failed `npm ci` fail the job? -> step 162-164 has no `continue-on-error` and uses the default `bash -e` shell, so a non-zero exit fails the step and the job. The test step still runs (`!cancelled()`); with no node_modules it fails with the require_fixture message, so one run reports both and cannot end green.
- Defence in depth -> removing only the env var leaves the install step, which blocks on its own; removing only the install step makes the tests fail closed. A single-line mutation cannot produce a silent skip-pass.
- Does the suite step still skip the four corpus cases? -> hosted log of run 38989714639 (.superpowers/sdd/r2/b10-quality-gate.log lines 1763-1769): the four `ReactCorpusTest` subtests `... skipped 'run npm ci in fixtures/vite-react-css-modules'` in step `Run tests (Chromium, blocking)`. Parsed workflow: the only `npm` run steps in the job are [15] (this fixture) and [17] (vite-react), both after the suite [14]. Yes, they still skip there.
- Does the module run once? -> same log, line 1761: `FixtureInstallContractTest.test_existing_install_check_fails_closed_when_required ... ok` runs in the suite step and needs no fixture, so it runs again in the new step. The four fixture cases run once; the fifth case runs twice (Minor 1).

Item 3, runtime fit
- Node line -> b10 log lines 168-187: setup-node@v7 with `node-version: 22` resolved `Found in cache @ /opt/hostedtoolcache/node/22.23.3/x64`, node v22.23.3, npm 10.9.9. Fixture lockfile `node_modules/vite` 8.3.2 has engines `^20.19.0 || >=22.12.0`; rolldown and its bindings carry the same range; no other package in the lock (43) has a stricter range (nanoid, postcss, fsevents all admit 22). 22.23.3 satisfies it. No .npmrc, .nvmrc or engine-strict setting exists to change that.
- Linux install -> read fixtures/vite-react-css-modules/package-lock.json (lockfileVersion 3): it contains `@rolldown/binding-linux-x64-gnu` 1.2.13 and `lightningcss-linux-x64-gnu` 1.33.0; all 43 packages resolve from registry.npmjs.org with integrity; the only install script is darwin-only `fsevents`; the lock root equals package.json (react 19.3.0, react-dom 19.3.0, vite 8.3.2). `git ls-tree` at BASE: all 8 fixture files, including the lock, are tracked; `node_modules` and `dist` are ignored (.gitignore:10-11). Corroboration: the `vite-react` fixture (Vite 8.3.2, same binding pattern) already installs with `npm ci` on ubuntu Node 22 in hosted job `Fixtures, Vite 7 and 8 (ubuntu-latest, Node 22)` (success, 0.95 min, run 38989714639).
- Timeout -> `gh run view 38989714639 --json jobs` (read-only): job quality-gate 18.58 min; steps: suite 922 s, Firefox canary 104 s, frontend gate 40 s, cookie step (npm ci + prepack) 3 s; limit 30 min (quality-gate.yml:28). The change adds one `npm ci` of 43 packages (a few seconds) and 5 tests (13.7 s locally per the report; the hot-update test's own waits are bounded at 10 s + 14 s). Estimate 19 to 20 min, about 10 min of headroom. Trend over the 11 saved hosted runs (b0 to b10 extracts): suite 668 s (924 tests) to 922 s (1070 tests), highest 927 s. The headroom is shrinking as PR B2 adds tests, but this change does not consume it.
- Hang exposure -> read test_r2_react.py: Vite start deadline 30 s, stop 15 s + 5 s, page waits 3 s and 10 s, restore waits 1 s x4 + 10 s. No unbounded wait; the missing step-level timeout matches the suite step, so I do not raise it.

Item 4, comment truth (quality-gate.yml:158-161), sentence by sentence
- "runs the fixture's own Vite dev server" -> test_r2_react.py:60-63 spawns `node <fixture>/node_modules/vite/bin/vite.js` -> true.
- "the suite above skips it: that fixture is not installed yet at that point" -> b10 log 1763-1769 plus the single install at step [15] after [14] -> true.
- "its module runs with installs required" -> `FKS_REQUIRE_FIXTURES: '1'` (170) -> true.
- "its cases block instead of skipping" -> fail-closed per Item 2, no `continue-on-error` -> true.
- "After the suite, so it runs only once." -> true for the four corpus cases; not for the module as a whole (Minor 1).
- Step name "(blocking, never skipped here)" -> no skip path in this module under the step's env (Item 2) -> true.

Item 5, tests that assert the step list
- Who reads the workflows? -> grep `workflow|\.github|quality-gate|cancelled|continue-on-error` over tests/, scripts/, packages/fontkitstudio/test -> only tests/test_release.py reads them; for quality-gate.yml it asserts only that `workflow_call` is in `on` (test_release.py:228-230). `test_support.CanaryListTest` checks firefox_canary names, not the workflow. Nothing asserts the job's step list, names, `if` or `continue-on-error`.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests python -m unittest test_release -v` in the root checkout -> `Ran 25 tests`, `OK`. 25 plus the 5 test_r2_react cases equals the report's "Ran 30 tests".
- `git diff --check` and `git diff --cached --check` -> exit 0. Added lines: no trailing whitespace, tabs or non-ASCII; longest 82 chars. .pre-commit-config.yaml: only the always-run whitespace hook applies to a .yml file (ruff is Python-only; js-syntax and static-checks are path-filtered), as the report says.
- Will the commit store the reviewed bytes? -> `git hash-object --path=.github/workflows/quality-gate.yml` on the working file gives 43a0f72fe7a41efd9459cada6eb2000b5cf40427, equal to the blob of BASE + DIFF (LF) and to the DIFF's own header `index f157dee..43a0f72`. BASE blob f157dee is LF-only.

Item 6, hidden skips after this change
- The suite step is unchanged and runs before any install, so hosted CI will still report `OK (skipped=16)` there, as in run 38989714639. Where each of the 16 runs with its fixture required:
  - test_r2_react.ReactCorpusTest, 4 subtests (vite-react-css-modules): now executed by the new step (this change).
  - test_one_command_vite.OneCommandViteBrowserTest, 4 (vite-react / vite7-react); test_vite_build_guarantee, 2; test_vite_types, 2; test_friction, 1; test_localhost_cookies, 1 (also in the advisory Firefox canary): the `fixtures` job step `Fixture tests (never skipped here)` (quality-gate.yml:281-286), which installs those fixtures and sets FKS_REQUIRE_FIXTURES=1.
  - test_one_command_next, 1 (next-app): the `next-fixture` job (quality-gate.yml:319-325).
  - test_one_command_messages.HostRefusalTest.test_a_server_opened_to_the_network_is_refused_in_one_line, 1 (needs vite-react): NOT run by any hosted step. It is absent from the `fixtures` job module list (286) and the `next-fixture` job, it is not in CANARY (tests/firefox_canary.py:24-34), and in `quality-gate` vite-react is installed only at step [17], after the suite. It is an existing, recorded gap, not caused by this change (docs/implementation/verification-0.3.1.md:152-157 "No CI coverage is claimed for that case"; docs/implementation/tasks/v031-task-C-review.md:282-292).
- No other skip records: Firefox canary `Ran 51 tests ... OK` without skips and the frontend gate `0 SKIP lines` (b10 extract); the new step cannot skip (Item 2). So the one test that hosted CI still never runs is the host-refusal case; the other 15 skipped suite cases each run, required, in a hosted step.

Other risks checked
- Do live docs now say something false? -> `git grep` of FKS_REQUIRE_FIXTURES, "installed fixture", "npm ci --prefix fixtures" over README.md, CONTRIBUTING.md, AGENTS.md, docs/agents, docs/specs, docs/roadmap, .github -> README.md:618 and CONTRIBUTING.md:52 say "CI sets FKS_REQUIRE_FIXTURES=1, so a missing install fails there": a general statement that is neither truer nor falser after this diff (the suite step has never set it). README.md:618 lists the fixtures that need an install without `vite-react-css-modules`; that is stale since PR A, outside this diff, for the release-point doc pass.
- Sibling comment made less true? -> read BASE quality-gate.yml:47-48 ("Only for `node --check fontkit-bridge.js` ... nothing else uses Node") -> already false at BASE (the cookie step runs `npm ci` and `prepack`), and the new steps add another Node consumer with a version floor (Vite 8: `^20.19.0 || >=22.12.0`) that the comment hides. Pre-existing and outside the new comment's scope, so not a finding; the controller may fix it in the same commit.
- Does the release gate change? -> release.yml calls quality-gate.yml (`workflow_call`), so the new steps also run in the tag gate; test_release's 25 tests still pass.
- The review target moved while I worked: HEAD advanced from BASE deb3636 to afd64be (docs only, 4 files; its quality-gate.yml blob equals BASE's), and the working copy of quality-gate.yml was rewritten with CRLF at 22:26 (`git ls-files --eol`: i/lf w/crlf). I reviewed the DIFF (SHA-256 39e7ac6c...c2bd verified with certutil) and BASE blob. The working file with CRLF folded to LF is byte-equal to BASE + DIFF, so nothing but line endings changed, and with core.autocrlf=true a commit stores LF.

### Strengths
- The two steps are independently fail-closed: the install blocks on its own and the test step refuses to skip, so no single-line edit can turn the React cases into a silent pass.
- The suite step is untouched, so its 12 other disclosed skips stay disclosed and no other fixture's absence turns into a failure.
- Every number in the report reproduces: the 16 skip names and counts, the Node line, and 25 + 5 = 30.
- The step name states the property it guarantees and follows the sibling steps' naming and `if` convention.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. quality-gate.yml:161 "After the suite, so it runs only once." Ambiguous, not false: read as the corpus (the comment's subject) it is true of the four fixture cases; read as the module it is not, because the fifth case (`FixtureInstallContractTest`, which needs no fixture) runs in the suite step too (hosted log line 1761, `ok`) and again in the new step, so the job log's `Ran` lines count it twice. The brief's "runs the module once" has the same imprecision. Wording fix: "so the four fixture cases run only once".
2. .superpowers/sdd/r2/task-7ia.patch is CRLF (27 CR in 27 lines). Against the LF blob, `git apply --check` (scratch directory, core.autocrlf=false) fails with `patch does not apply`; it passes only with `--ignore-whitespace`. An LF copy applies and reproduces the working file. The change itself is unaffected (blob 43a0f72 verified above); this matters only if anyone applies the patch to an LF blob (index, scratch worktree, a gate-runner). Re-save it with LF if it will be applied.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The diff is exactly the two specified steps, placed where the brief and Addendum 17 say, with the required `if` and env and no `continue-on-error`; the React cases fail closed under FKS_REQUIRE_FIXTURES=1 and the job gets Node 22.23.3 against Vite's `>=22.12.0`, with about 10 minutes of timeout headroom. The two Minors are a comment-wording imprecision and a CRLF patch artifact; the one test hosted CI still never runs (the host-refusal case) is an existing recorded gap outside this change.
