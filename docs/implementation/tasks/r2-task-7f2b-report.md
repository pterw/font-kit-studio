# R2.7F2b code report, phase 1 of 2 (mode code, task 7f2b)

BASE f2b438fee72f85c1d56555a4b143c90bce65b1a3, worktree C:/fks/t7f2b, no PATCH_DEP applied. Only
`tests/test_r2_react.py` changed (staged; 433 insertions, 24 deletions, about 410 material lines). Patch:
`.superpowers/sdd/r2/task-7f2b-code.patch` (SHA-256 f3a6b25a2692f4dd8c7300fbb670aed277de68860af6f2050853772180fb0fa7,
LF, `git apply --check -R` passes). `fontkit-bridge.js` SHA-256 before and after every mutant run:
f0290569aac08b3486ae96e9debe33d44e37780239e3201bd49c7c288dc34adc.

## What was built
- Harness: `session(engine, host=False)` is the old `app()` body; `app()` wraps it unchanged for the five F2a tests
  (no bridge, no host). `role_app()` starts an owned `ThreadingHTTPServer` (127.0.0.1, port 0, silenced
  `QuietHandler`, rooted at tests/fixtures/bridge), opens `host-roles.html?target=<Vite URL>`, installs the
  origin-guarded init script and one `context.route` for `/fontkit-bridge.js` served from `self.bridge_source()`,
  waits for `design:bridge-ready`, `hello()`, interact mode, then a first Detect. `guarded_context(**options)` takes the
  1500x1000 viewport. HTTPS guard, scratch copy, `require_fixture`, byte restore and the no-HTTPS exit check are kept.
  `stop_host` does shutdown, thread join, server_close and a refused-connect check beside the Vite ones.
- Preserve: the F2a hot-update test's inline loop became `restore_css(target, css, original)` (same waits and failure
  text); cases 4 and 5 also call it.
- Cases 1-5 as four-plus-one methods (names in the patch), each with a Given/When/Then docstring. Expected values are
  literals, `expected-styles.json` rows, `fnv1a32` test-local, and `CSS.escape` from the browser.
- No skipTest anywhere; every context manager goes through `require_fixture`.

## Evidence
Focused gate: `sh .../gate.sh focused test_r2_react test_support` -> `Ran 44 tests`, 5 errors, all
`KeyError: 'adapter'` in case 1 (one per group subTest). RED until PATCH_DEP, as the dispatch states; the assertion is
`self.assertEqual(group['adapter'], 'plain')`, unguarded. Everything else is green: the 5 F2a tests, cases 2-5, the
rest of case 1 (counts, identities, signatures, selectors, bindingComplete), all of test_support. I split the adapter
assertion from `bindingComplete` so that only the adapter part is red.

Mutants (run through the `bridge_source()` seam by `mutate-7f2b-1.py`; BASE line numbers):
1. choose() at 1736 and 1739: case 1 body subTest FAILS (`[data-design-role="body"]` != the two author-id bindings);
   case 2 FAILS (restyled bridge-tagged paragraphs); case 3 FAILS. Case 1's other four groups error on adapter regardless.
2. line 240: case 2 FAILS, all three hostile subTests plus the apply.
3. lines 1443 and 1452: case 5 FAILS (`(True, None, [outcomes]) != (False, 'page-changed', [])`); no other new test fails.
4. Clear writes the captured font size inline (inserted at the commit point): case 2 FAILS (`style="font-size: 40px;"` in
   main's markup), case 3 FAILS (hash size 15 vs 14), case 4 FAILS (title 40 vs 44 after Clear).
5. Inline writes plus emptied owned text: case 2 FAILS (outcomes incomplete or owned text), case 3 FAILS (family
   `serif` vs `Georgia, serif`), cases 4 and 5 FAIL (owned text `['']`).
Case 5 stamps (commit, hmr, deadline in ms, three runs): 320.2, 341.7, 576.5; 347.9, 369.8, 600.4; 333.0, 354.1, 590.8.
Gaps commit to hmr 21.5, 21.9, 21.1; hmr to deadline 234.8, 230.6, 236.7.

Production build, once, in a git-ignored scratch copy (junctioned node_modules, junction removed with rmdir): built
clean, 0 files in dist mention `fontkit`; scratch deleted. Ruff on the module: All checks passed.
`git diff --check -- tests/test_r2_react.py`: exit 0. The tests assert the host and Vite listeners refuse after close
(passed in every run); no `.fks-` directory or server left.

## Deviations
- Case 1 `adapter` red (dispatch, not a deviation). Brief's `design:detect` is sent via the host's `request` with its
  default `knownRoles: []`.
- Mutants 4 and 5 are my own implementations of the brief's descriptions (inserted at the "Commit point" comment).

## Handoff for phase 2
1. Apply R2.4's patch in C:/fks/t7f2b unstaged; record its SHA-256. Do not include it in the patch.
2. Run `sh .../gate.sh focused test_r2_react test_role_adapters test_support`; expect case 1 green (adapter `plain`).
   If any group's adapter is not `plain` on this fixture, report it.
3. Rerun `mutate-7f2b-1.py` mutants 1-5 (scratchpad; usage `python mutate-7f2b-1.py C:/fks/t7f2b <n> <test names>`)
   against PATCH_DEP's bridge. Its `once()` finds each fragment, so it fails loudly if R2.4 moved or changed a target;
   report the new line numbers (the printed `line` is the target line; mutant 3 prints it correctly as 1 less than
   BASE's, i.e. the runner's number for those two is the preceding line: BASE shows 1442/1450 for 1443/1452, so add 1).
   Rerun case 5 three times for stamps (mutant number 0 prints them as STAMPS lines). Also confirm the bridge SHA-256
   before and after.
4. Regenerate the patch only with `git diff --cached --binary f2b438f... --output=... -- tests/test_r2_react.py`.
5. Commit subject: `test: cover the role preview on a real React app`. Draft body: "The role preview must keep
   styling nodes React replaces, say honestly when a CSS hot update outdates a receipt, and clear to the app as it is
   now. Run the real bridge in a real React app behind an owned loopback host, since Chromium blocks Vite's
   WebSocket on a fulfilled document. Cover Detect, Apply, Clear, replacement and hot updates before and during a
   measurement." (wrap at 72 when committing; attribution line per the dispatch).
6. Plan items: R2.7F2b done after phase 2 is green.

## Phase 2 (mode code, task 7f2b)

Staged `tests/test_r2_react.py` re-hashed to f3a6b25a... (matches). PATCH_DEP `task-4-code.patch` SHA-256
767311d34ed0ed1ea09729bd41780f8d238cbfd3ba37724f00b70394bc6c866e (matches), applied unstaged in C:/fks/t7f2b; it never
enters the patch. `fontkit-bridge.js` SHA-256: BASE f0290569...adc; with PATCH_DEP 66813402832462281659232a6c84e658ff2dc32e570e1c866a905bdff7b4a0b0,
unchanged before and after every mutant and stamp run (the runner prints "sha256 equal True"). No test change.

Focused: `gate.sh focused test_r2_react test_role_adapters test_support` -> `Ran 67 tests in 64.565s`, OK, `GATE focused EXIT 0 IN 65s`.
Case 1 (`test_detect_groups_five_real_react_roles...`): green; every group's `adapter` is `'plain'`. All five new cases green.

Mutants on PATCH_DEP's bridge (bridge_source seam; the runner's printed line for mutant 3 is the preceding line, true lines given):
1. lines 1792, 1795: case 1 body subTest, case 2, case 3 FAIL (3 failures).
2. line 257: case 2 FAILS (3 hostile subTests + the apply, 4 failures).
3. lines 1497 and 1506 (runner printed 1496/1504; grep confirms): case 5 FAILS `(True, None, [...]) != (False, 'page-changed', [])`; only that test.
4. insertion at the commit point, line 1426: cases 2, 3, 4 FAIL (inline `font-size: 40px`; hash size 15 vs 14; title 40 vs 44).
5. insertion at line 1426: cases 2, 3, 4, 5 FAIL (receipt incomplete; family `serif` vs `Georgia, serif`; owned text `['']`).
Case 5 stamps (commit, hmr, deadline ms, three runs): 423.2, 453.2, 674.8; 414.3, 441.4, 678.5; 471.8, 504.7, 723.9.
Gaps commit to hmr 30.0, 27.1, 32.9; hmr to deadline 221.6, 237.1, 219.2. Hot update lands between commit and deadline each time.
No Vite or host server left (the tests assert refusal after close).

Patch: `.superpowers/sdd/r2/task-7f2b-code-r1.patch` (tests/test_r2_react.py only, identical content to phase 1's;
`git apply --check -R` passes). Phase 2 changed nothing.

Handoff (updated): land the r1 patch after R2.4 (task-4-code.patch) lands; re-run the focused gate then. Commit subject
`test: cover the role preview on a real React app`, body as in the phase 1 draft. Plan item R2.7F2b done; case 1 and all cases green.

## Fix round 1

Mode code. Staged test hash before: f3a6b25a... (verified). PATCH_DEP switched: `git apply -R task-4-code.patch` (767311d3...) then `git apply task-4-code-r1.patch` (4c39e12c...), unstaged, not in my patch; fontkit-bridge.js = a7e81ca1fd057f391b41d019ab63d015d2491b7c9c87f56cd632196a7e189a5f.
Only tests/test_r2_react.py changed. Patch: `task-7f2b-code-r2.patch`, SHA-256 5c634fb32ef84746ce4e286ca70ff3d5daf28f6d3da56e6abdbedc6d56cc01e5, no CR, `git apply --check -R` ok, numstat 441 insertions / 24 deletions (412 added material lines). ruff --no-cache: All checks passed; `git diff --cached --check` clean.

Per Minor (mutants: scratchpad/mutate-7f2br1.py; every file SHA-256 identical before/after: bridge a7e81ca1..., test file 1290b4a3...):
1. Case 5 now awaits `window.stamps.deadline !== undefined` (polling=10) before reading stamps. Mutant: test timer moved to 400 ms. With the wait: OK. Wait removed: ERROR `KeyError: 'deadline'`.
2. Case 4 `node.dispose()` nested in its own try/finally inside the finally. Mutant: restore_css raises RuntimeError; nested shape prints DISPOSED, old shape does not.
3. Docstring Thens now match: case 1 (6 scanned elements, four data-design-role body), case 3 (fresh Detect reports greater version), case 4 (greater version, restored literal 40px row).
4. Case 1 uses `hash_selector` (also case 2, now a local `hashed`); `apply_previews` removed (calls use `send(..., 'design:roles-apply', detected, roles=...)`); new `scratch_css(project)` helper for the repeated css/original/changed lines in cases 4 and 5 (the F2a copy is untouched). Cases still pass (below).
5. Case 2 Detect under the live preview asserts `len(groups) == 5`. Mutant (bridge copy via bridge_source(): appends a ghost author-role group when roleSheet exists): control OK, mutant FAIL `6 != 5` at that line. The D067 transition-ban mutant was not run.
6. One blank line before `hash_selector`.
7. Case 3 now covers title, first and second body (detach incl. text child, attributes, class). Mutant: expected second-body id changed to `modules.body.first`: FAIL `['body','modules.body.second',...] != ['body','modules.body.first',...]`. This is an expected-value mutant, not a bridge mutant: no bridge change plausibly alters the app's attributes.

Focused (`FKS_REQUIRE_FIXTURES=1`, tests dir, PATCH_DEP r1): `python -m unittest test_r2_react test_role_adapters test_support` -> `Ran 73 tests in 70.045s OK`.
Case 5 three times, all OK, premise stamps (ms): commit 385.2 / hmr 410.1 / deadline 646.2; 459.4 / 483 / 716.2; 415.2 / 439.6 / 668.3.
Nothing left running; no full suite run.

## Controller integration

- Landed from `task-7f2b-code-r2.patch` (SHA-256 `5c634fb3...01e5`) after R2.4 and R2.S3, with one controller
  edit: case 2's docstring Then names the five-group count (re-review Minor).
- It ran in two phases: against the W0 bridge first (case 1's adapter assertion red by design), then with R2.4's
  patch. The five mutants' line numbers refer to R2.4's first patch; its later fix changed only the heading step,
  which these cases do not reach, and the landing run below uses the final bridge.
- Review: Approved with seven Minors, all fixed on R2.4's final bridge; the scoped re-review is Approved, and a
  realistic bridge mutant proves the second-body check.
- Landing gates, Windows, Chromium, `FKS_REQUIRE_FIXTURES=1`, with R2.4's, R2.S3's and R2.7F2b's patches on the
  integrated tree at `f2b438f`: the Studio modules, 194 tests in 257.343 s; the bridge role modules, 103 tests in
  160.264 s; the preview, protocol, React and integration modules, 74 tests in 118.011 s; all OK. Static and
  provenance, `node --check`, product-tree Ruff and whitespace pass; exact Ruff reports only the four preserved
  findings under `.agents/`. `test_r2_react` ran in the 74-test run.
- Material lines: 441 added, 24 removed, in `tests/test_r2_react.py` (D065), plus the one-line docstring edit.
