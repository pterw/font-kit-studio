### Spec Compliance
- PASS: Req 1. `setText` records `state.wrote = {node, value}` (fontkit-bridge.js:3025); `restoreText` keeps the app's content when the leaf is not left as written and only clears bookkeeping (3039-3042, 3048). Inside owned region 3005-3056 (plus the allowed comment at 714).
- PASS: Req 2. Reset all (2432) and `design:restore-text` (2449) go through `restoreText`; test at test_bridge_runtime.py:~900-904 checks TITLE = page string and CTA = `Get started`.
- PASS: Req 3. Whole `test_bridge_runtime` module run in the task's worktree: 132 tests OK, existing tests unmodified (diff has only additions in the test file). Unrewritten edit still restores the original nodes through the unchanged branch (lines 3043-3045); asserted by `test_restore_text_restores_original_text_without_throwing` (150-162) and `test_reset_one_target_or_everything` (CTA = `Get started`, 808).
- PASS: Req 4. Ledger asserts `entry is None or entry['text'] is None` after Reset (test, node-value and text-content subtests).
- PASS: Review fix 1. `textState.delete(el)` in the keep branch (3041); `test_a_later_edit_after_keeping_the_app_text_resets_to_that_text` edits again, resets, and expects the app string.
- PASS: Review fix 2. `wrote.node` is null when text is '' and "unchanged" means `childNodes.length === 0` (3052). Covered by the new emoji test (no existing test did).
- PASS: Review fix 3. Accepted limit stated in the report (restore-text with an `inside` image keeps the image and skips the emoji restore).
- PASS: Review fix 4. `el.textContent = ...` rewrite subtest present; comment at 714 updated. No new user-facing string.
- PASS: Patch. `git apply --check -R` of the patch against the worktree succeeds; only fontkit-bridge.js and tests/test_bridge_runtime.py are touched. Nothing is committed, so the commit subject is unchecked here; the handoff subject `fix(bridge): reset an edited text to what the app now shows` carries no process state.

### Checks run
- Skip-every-leaf-restore break (the one the implementer did not run) -> scratch copy under scratch with `if (state.leaf) { delete state }` replacing the guard; ran `ResetAfterAppRewriteTests` -> FAILED (failures=3). The reset-all test failed with `'Edited cta' != 'Get started'` at the CTA assertion, which proves the mutated file was loaded and that the test catches the break. The emoji test also failed (`'' != emoji`).
- Round trip and capture-once (anti-pattern 6) -> read `restoreText`/`captureText` (3005-3056); the unrewritten branch is unchanged, so edit then Reset or Reset all gives back the original nodes. The `textState.delete` happens only in the keep branch, where the stale originals are meant to be dropped. A later edit recaptures what the page shows, and the test at "later edit" proves that. Re-registration without a Reset still goes through `captureText`'s existing `if (!state)` guard, so no recapture there. `textChanged`/`originalText`/`currentText` (3087-3117) still work with a deleted state (they fall back to the live text).
- Mechanical defects on `leftAsWritten`, six, each run against `ResetAfterAppRewriteTests` (script scratch/t4-review-mutate.py; scratch trees deleted afterwards):
  - drop node identity -> KILLED
  - drop `node.data === value` -> KILLED (3 failures)
  - null node returns false -> KILLED
  - drop `childNodes.length === 1` -> MISSED
  - null node returns true -> MISSED
  - the sixth (early return in keep branch) had a bad anchor string; not run, but the implementer's own mutant for the missing `textState.delete` was reproduced by logic: the later-edit test asserts that path.
- Focused runs in the task's worktree: `test_bridge_runtime` 132 OK (125 s); `python scripts/dev/check_js_syntax.py fontkit-bridge.js` rc 0. `test_support` was not rerun (not touched by this change); `test_studio_roles`, `test_role_routes`, `test_r2_integration` left to the wave gate (the change is bridge-only).
- Callers of `setText`/`restoreText` (2317, 2432, 2449, 3060, 3431, 4280, 4347) -> grep; all pass through the same two methods, none needs a change.

### Strengths
- Both rewrite styles are tested (`nodeValue` and `el.textContent =`), so a data-only check on the old node fails.
- Test 3 pairs a rewritten element with an untouched edited one, so a guard that skips all leaf restores fails (reproduced).

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- fontkit-bridge.js:3053 and :3052: the `childNodes.length === 1` clause (app appends a sibling after the edit) and the null-node branch returning false are only partly pinned. Mutants "drop the length check" and "null node returns true" survive the new tests. The null-node case is only reachable when the app writes into a cleared placeholder, and Reset via `resetElement` removes the placed image first, so the effect is small. No verdict depends on it; recorded, not a follow-up.
- The report says the skip-all-leaf break was "by construction, not executed"; it is now executed and fails as expected.

### Plan-mandated (for the owner)
None.

### Source conflicts (for the controller)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The guard keeps the app's text exactly when the bridge's written node or value changed, clears `textState` so the next edit recaptures, and leaves the unrewritten round trip unchanged (132 bridge tests pass). The skip-every-leaf break fails the reset-all test at the CTA assertion; two edge mutants survive but affect no verdict.
