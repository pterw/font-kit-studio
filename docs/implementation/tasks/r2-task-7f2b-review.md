### Spec Compliance
- PASS: Only tests/test_r2_react.py changed (patch SHA-256 f3a6b25a... equals `git diff --cached | sha256sum` in C:/fks/t7f2b; the working-tree file equals the staged one modulo CR). PATCH_DEP stays out of the patch.
- PASS: Harness per brief: owned ThreadingHTTPServer on 127.0.0.1:0 rooted at tests/fixtures/bridge, silenced log (patch lines 79-81, 100-122); origin-guarded init script + one `context.route` for `/fontkit-bridge.js` from `bridge_source()` (the only seam); HTTPS guard, scratch copy, `require_fixture`, byte restore and exit check kept; `guarded_context(**options)` with the 1500x1000 viewport; waits h1, then `design:bridge-ready` from the host log, then `hello()`, interact mode, a first Detect (role_app, lines 129-139).
- PASS: Cases 1-5 present, each with a Given/When/Then docstring, no `skipTest`, every context manager goes through `require_fixture` (session, line 143).
- PASS: Preserve: the five F2a tests are textually unchanged except the inline restore loop, now `restore_css(target, css, original)` with the same waits `(1000 x4, 10000)` and failure text (patch lines 194-232); `app()` wraps `session` with the old `(page, project)` yield.
- PASS: Case 5 recipe is the brief's: rAF stub, `style[data-vite-dev-id]` MutationObserver, same-task `message` listener, block-body `request`, `polling=10`, premise `commit < hmr < deadline` asserted (with the three numbers in the message) before any receipt field; one `roles-applied` per requestId; stale Apply and Clear carry the Detect's `pageVersion`.
- PASS: Docstring honesty: case 5 says frame callbacks are withheld and the bridge measures from its 250 ms timer; it does not claim anything about `currentPageVersion` (Addendum 18).
- PASS: No React Fast Refresh claim anywhere.

### Checks run
1. Drift (receipt, rejection and page-version fields) -> read every assertion against D063 / Addendum 16 item 4 / Addendum 18 and ran the cases on PATCH_DEP -> PASS.
   - Case 3: Clear carrying the pre-replacement receipt's `pageVersion` -> `page-changed`, revision 1, owned text and rendered styles unchanged; fresh Detect `pageVersion` `assertGreater` receipt's; then Clear accepted.
   - Case 4: after a hot update, `assertGreater(fresh.pageVersion, receipt.pageVersion)` (never +1); Clear and Apply with the receipt's version -> `page-changed`, nothing changed; the fresh Detect's version is used for the accepted Clear.
   - Case 5: `receipt.pageVersion == detected.pageVersion`, `currentPageVersion > it`, `outcomesComplete False`, `outcomeReason 'page-changed'`, `outcomes []`, committed roles/css/hash literal; stale requests carry `receipt['pageVersion']` (the Detect's), a rejection's absence of a version is respected (greater version always read from a Detect).
   - Rejections assert `type == design:rejected` and `reason`; detail `Unsupported selector` for the hostile selectors.
   - Addendum 18 (a request carrying `currentPageVersion` is accepted) is deliberately not asserted and not contradicted.
2. Mutants -> own runner `scratchpad/mutate-7f2brv-1.py` (copy outside the repo; overrides `ReactCorpusTest.bridge_source` with replaced bridge text; own implementation, written independently of the implementer's `mutate-7f2b-1.py`), run on PATCH_DEP's bridge over the five new cases, `FKS_REQUIRE_FIXTURES=1`, `PYTHONDONTWRITEBYTECODE=1`:
   - Control (no mutation): 5 tests OK, bridge unchanged.
   - M1 (bridge lines 1792 and 1795: drop `found.some(el => !members.has(el))`, `covered.size < members.size`): FAIL case 1 (body group selectors `[data-design-role="body"]` != the two author-id bindings), case 2 (body outcomes (4,4,1) vs (2,2,0)), case 3 (stable control shows Verdana). Matches the report (3 failures).
   - M2 (line 257: `checked.set(selector, true)`): FAIL case 2: `['body']`, `['h1, p']`, `['p:hover']` accepted ('design:roles-applied' != 'design:rejected') plus the apply's revision (4 != 1). 4 failures, as the report.
   - M3 (lines 1497 and 1506: both `roleJobFresh` rechecks removed): FAIL only case 5: `(True, None, [outcomes]) != (False, 'page-changed', [])`. Exactly as the report.
   - Extra mutant M9 (my own, not in the brief; line 1404: ignore `pageVersion` mismatch): FAIL cases 3, 4 and 5 ('design:roles-applied' != 'design:rejected'). The stale-version assertions are live.
   - Mutants 4 and 5 (Clear restores captured value; inline writes) were not reproduced by me; the report's results are plausible from the assertions (style-attribute count, OWNED text, computed 44px after Clear, replacement nodes styled) and the brief-rereview probed them (p6), but treat them as report claims.
   - Frozen worktree byte-identical: `git status --short` and a sha256 of bridge plus tests/*.py were `1f6c75d3...` before and after; staged diff hash `f3a6b25a...` unchanged; no `.fks-` directories left; bridge hash unchanged per the runner (`bridge unchanged True`).
3. Fake versus real -> read the harness and the five cases -> real React (Vite dev server on the scratch copy), the real `fontkit-bridge.js` (PATCH_DEP's, served via the route), the real `host-roles.html` on a real loopback `ThreadingHTTPServer`, real keyboard presses, real CSS writes and hot updates. The only stub is the in-page `requestAnimationFrame` replacement in case 5, which is the brief's intended frame-hold; no assertion is made against a stub (receipts and computed styles are read from the real page).
4. Hidden skips in hosted CI -> `.github/workflows/quality-gate.yml` lines 158-173 (npm ci of the fixture only, `FKS_ENGINES: chromium`, `FKS_REQUIRE_FIXTURES: '1'`, `python -m unittest test_r2_react -v`) -> the new cases need only: the fixture (guarded by `require_fixture` -> hard fail, not skip), `host-roles.html` and `fontkit-bridge.js` from the checkout (both tracked), Chromium, loopback sockets. No new case can skip (grep: no `skipTest` or `skipIf` in the diff). The one thing that cannot be proved here: Chromium's Local Network Access behaviour on Linux for a loopback host + loopback iframe + loopback Vite WebSocket (CANNOT VERIFY FROM DIFF; the brief-review only measured Windows; the design is the brief's and a first hosted run is the evidence). No fixed timing on the hosted runner beyond the existing 3 s / 10 s waits copied from F2a and the 250 ms premise (measured 219-237 ms margin; the premise assertion names the numbers if a slow runner breaks it, so it fails loudly, never silently green).
5. Tests quality -> read all five cases:
   - Oracle: styles from `expected-styles.json` via `self.oracle()` rows; CSS and digest from test literals and test-local `fnv1a32` (offset 2166136261, prime 16777619); hashed class read from the app with `CSS.escape` in the browser; roles built from the Detect reply but pinned by the literal CSS (`DISPLAY_CSS`, `BODY_CSS`, hash block) and by `roles[2]['selectors'] == [hash_selector]`. Case 3 uses `receipt['canonicalCss']` as the "same text" oracle (the brief's wording, and case 2 pins that text to a literal).
   - Observable outcomes: computed style (`SIGNATURE`), `style` attribute count 0, `#fontkit-role-styles` text list, `main` outerHTML equality, node `isConnected`, bytes restored.
   - No fixed sleeps in the new code: all waits are conditions (`wait_for_function`, `polling=10`, `waitFor` on the host log).
   - Case 5 premise is asserted before the first receipt field (patch lines 498-501 precede 502+).
   - Each new test fails when the behaviour is removed (M1-M3, M9 above).
6. Code -> owned servers close in `finally` (`stop_host` inside the try/finally around `stop_vite`; listener refusal asserted for both); ruff `--no-cache` on the module: All checks passed; `git diff --cached --check -- tests/test_r2_react.py`: clean. Size 433 insertions and 24 deletions, about 410 material lines, under the ~450 budget.

### Strengths
- Mutants 1-3 and a version-check mutant are all killed by the intended cases only; case 5 is the only one that kills M3, so the premise-guarded mid-Apply hot update is a real regression test.
- Premise assertion names `commit`, `hmr`, `deadline` and runs before any receipt field.
- The harness cleans up deterministically and keeps the HTTPS guard and byte-restore guarantees of F2a; the F2a tests are untouched.
- Cases never read the bridge's output as their oracle for CSS, digest or baseline rows.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- Case 5 reads `stamps` right after the receipt (patch line 499-501). `deadline` is stamped by a timer the test registered after the bridge's own, so it is normally already set, but nothing awaits it; if it were still undefined the comparison would raise TypeError instead of the named-numbers message. Awaiting `window.stamps.deadline !== undefined` (or using `.get`) would make the failure text robust.
- Case 4 `node.dispose()` is in the same `finally` as `restore_css` but not nested (patch lines 469-471): if `restore_css` fails, the handle is never disposed. The F2a test nests it (`try/finally`).
- Docstring Thens miss some asserted items: case 1 (the four `data-design-role="body"` count, `scannedElements`), case 3 (fresh `pageVersion` greater than the receipt's), case 4 (the greater `pageVersion`, the final restored 40px row). The brief asks that the Then equals what is asserted.
- `hash_selector` (line 321) duplicates the inline expression in case 1 (lines 296-297), which does not call it; `apply_previews` (line 324) is a pass-through to `send` with one argument bound; case 4 and 5 repeat the `css/original/changed` four lines three times in the module (F2a already had it). Cosmetic.
- Case 2's Detect under the live preview checks that each of the five groups has the baseline signature, but does not assert there are exactly five groups, so an extra false new role (the D067 failure mode) would pass unless it displaced an expected group. A `len(groups) == 5` check would close it.
- Two blank lines before `def hash_selector` inside the class (patch line 319-320); ruff accepts it.
- Case 3 asserts detachment and attributes for the title and first body only (the second body is covered by the rendered-style check).

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** The five cases follow the brief on a real React app, real bridge and real loopback host; on PATCH_DEP they pass, and I reproduced mutants 1-3 plus a stale-version mutant through the `bridge_source()` seam with the intended cases (and only those) failing, the frozen worktree unchanged. Only Minor polish remains; the Linux LNA behaviour is the one unverifiable-here risk and will be proved by the first hosted run.

## Scoped re-review: fix round 1

### Spec Compliance
- PASS: Minor 1. Case 5 now runs `frame.wait_for_function('window.stamps.deadline !== undefined', polling=10)` (r2 patch line 506) after the receipt and before `frame.evaluate('window.stamps')` and the premise assertion.
- PASS: Minor 2. Case 4 `node.dispose()` sits in its own `try/finally` around `restore_css` (r2 lines 478-481), as the F2a test nests it.
- PASS: Minor 3. Docstring Thens now equal the assertions, checked one by one.
  - Case 1 names 6 scanned elements and the four `data-design-role` body elements (asserted: count 4, scannedElements 6).
  - Case 3 names the greater fresh version (`assertGreater`).
  - Case 4 names the greater version and the restored literal 40px row (final assertEqual).
  - Residual: case 2's Then says "reports the baseline rows" and does not mention the new five-group count (see Minor).
- PASS: Minor 4. `apply_previews` is gone (calls use `send(..., 'design:roles-apply', ...)`). Case 1 uses `hash_selector` and case 2 holds a local `hashed`. A `scratch_css` helper replaces the repeated css/original/changed lines in cases 4 and 5. The F2a copy is untouched.
- PASS: Minor 5. Case 2 asserts `len(under_preview['groups']) == 5` at r2 line 362, before the per-group signature checks.
- PASS: Minor 6. One blank line before `hash_selector`.
- PASS: Minor 7. Case 3 now covers title, first and second body: detach (including the text child), role, id and class attributes.
- PASS: Nothing else changed. `diff` of the two patches shows only the hunks above plus the index hash and hunk-header counts (321 -> 329). Both patches change tests/test_r2_react.py only. The F2a tests keep names and assertions. No `sleep` appears anywhere in the patch (grep). The new wait is condition-based (polling=10).

### Checks run
- Frozen worktree identity -> `git diff --cached | sha256sum` in C:/fks/t7f2b -> 5c634fb3..., equal to the r2 patch SHA-256. `fontkit-bridge.js` a7e81ca1... as stated. Before and after my runs, sha256 of the bridge plus tests/*.py was 9fc16b25... both times, and `git status --short` was identical, so it stayed byte-identical.
- Control -> `scratchpad/mutate-7f2brr2.py` (own runner, overrides `bridge_source`, bridge file untouched; "bridge unchanged True") run on cases 2, 3 and 5 -> 3 tests OK in 17 s.
- Mutant A, case 2 (my own, not the implementer's code) -> bridge `design:detected` reply gets an extra ghost group (`author-role` named `ghost`) whenever the role sheet exists -> case 2 FAILS `AssertionError: 6 != 5` at test_r2_react.py:532. Every per-group lookup in that case filters by identity, so only the new count line catches this. The fix works.
- Mutant B, case 3 (my own) -> bridge copy appends a MutationObserver that, while `#fontkit-role-styles` exists, adds the class `fk-touched` to a newly inserted `modules.body.second` node (a bridge writing to replaced nodes) -> case 3 FAILS: `['body','modules.body.second','App-module__body___FoLhY fk-touched'] != [... 'App-module__body___FoLhY']`. A class does not change computed style and it touches only the second body, so the title and first-body asserts, the rendered-style comparison and the `STYLE_ATTRIBUTES == 0` count all miss it. It is caught only by the new second-body check. The r1 test had no such check and would have passed.
  - Verdict on the implementer's claim that no bridge mutant alters the app's attributes: not accepted as stated. A realistic mutant exists (a bridge that decorates or re-tags replaced nodes), it is easy to build through `bridge_source()`, and the new assertion kills it. The implementer's expected-value mutant is weaker evidence than this one, but the assertion is shown live.
- Case 5 wait -> read only. The test's deadline timer is registered inside the `message` listener the harness adds after the bridge's own, so it normally fires after the bridge's timer. Without the wait, an unset `deadline` would raise a KeyError instead of the named-numbers message (the report's mutant shows this). I did not rerun the 400 ms-timer mutant; the report's result is plausible from the code.
- Lint -> `ruff` is not installed in this shell. The report's "All checks passed" is unverified by me. The line at r2 343, `reply = self.send(...)` (about 128 columns), is long, but no line-length rule was visible to me.

### Strengths
- The count assertion and the second-body assertion each kill a realistic bridge mutant that the corresponding r1 test missed. The mutants were reproduced independently.
- Fix round touched only what the Minors named, and the patch diff is small and fully accounted for.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- Case 2's docstring Then does not say that the Detect under the preview reports exactly five groups. The assertion exists, but the Then should name it (r2 lines 332-335).

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** All seven Minors are resolved as asked, and nothing else changed. I reproduced a ghost-group mutant and a bridge-decorates-replaced-nodes mutant, and each new assertion fails on it while the control passes. The frozen worktree is byte-identical.
