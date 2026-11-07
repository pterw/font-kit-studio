# Task 17 brief: Clear is never refused for a changed page

Plan Task 17, wave 3 (code phase; the landing is last among the fixes). BASE `5443ff6`, worktree `the task's worktree`, audit rows `D2-10, S06`
(one row, one patch). Mode: code. Line budget: about 110 gross lines (bridge about 6, tests about 100).
Rulings: O27 (Clear never refused), D080 and plan Addendum 1 (both recorded at BASE; they amend D063 for Clear only).

## Why

PokeCipher's cursor text changes about every 600 ms. Each author text mutation advances the wire `pageVersion` (D063), so a Clear that
carries the version Studio last saw is refused `page-changed` and the preview stays on the page (audit D2-10: 3 of 8 Clears refused). S06
(a class change on `<html>` mid-press) is the same mechanism. The cause still holds at BASE: `fontkit-bridge.js:1545`, in
`handleRoleMutation` (1530), is shared by Apply and Clear:
`if (data.documentId !== this.documentId || data.pageVersion !== this.pageVersion) { this.reject(data.requestId, 'page-changed'); return; }`.
A Clear never reaches `roleJobFresh` (1579; used at 1632 and 1641 for non-empty roles only): with no roles it posts its receipt directly
at 1570. Removing the bridge-owned preview is safe whatever the page did since (D080).

## Owned files (exact)

- `fontkit-bridge.js`: line 1545, and the comment above it (1525-1529) if one sentence is needed. Nothing else (Tasks 1, 4, 5, 10-13, 15
  edit other regions at the same time).
- `tests/test_role_stylesheet.py`: `AtomicRejectionTests.test_unknown_field_on_clear_and_stale_clear_are_rejected_without_removing_the_preview`
  (418-432), and two new tests inserted directly after it (before line 434).
- `tests/test_r2_react.py`: `test_replaced_react_nodes_keep_the_preview_and_clear_needs_a_fresh_detect` (541-592, stale Clear at 584-585),
  `test_hot_update_after_apply_keeps_the_role_and_shows_the_new_author_size` (594-646, Clear half of the loop at 623-625) and
  `test_hot_update_between_apply_and_measurement_makes_a_committed_receipt_without_outcomes` (648-690, Clear half of the loop at 686-688).
- Read-only: everything else, `CHANGELOG.md`, `docs/`, `README.md` (Task 18 states the limit). `fontkit-studio.html` is not touched.

## Read first

`fontkit-bridge.js` 1521-1590 (handlers, `handleRoleMutation`, `roleJobFresh`, `postRoleReceipt`); `tests/test_role_stylesheet.py` 36-60
(`apply`, `clear`, `current` helpers) and 259-274, 359-376, 418-432; `tests/test_r2_react.py` 405-408 (`send`), 438-448, 541-692.

## Existing tests that pin a stale Clear as `page-changed` (re-found by search at BASE)

Search: every `clear(` / `roles-clear` call in `tests/*.py` read against the assertions around it. Exactly four pins, all change in this patch:

1. `test_r2_react.py:584-585` (Clear after the React re-render, receipt's version). Becomes accepted.
2. `test_r2_react.py:624-625` (loop `('design:roles-clear', 'design:roles-apply')`, Clear half). Clear becomes accepted; the Apply half stays
   rejected `page-changed`.
3. `test_r2_react.py:687-688` (loop `('design:roles-apply', 'design:roles-clear')`, Clear half). Same split.
4. `test_role_stylesheet.py:427` (`{'pageVersion': 77}` -> `page-changed` in the Clear table). Remove that pair; the `documentId: 'elsewhere'`
   pair (426) and the other three stay, since the bridge still checks `documentId`.

Not pins, left alone: `test_role_stylesheet.py:273-274` (the plan listed them; `hostile_cases` feeds only `self.apply`, line 369, and Apply keeps the
rule); the Apply cases at `test_r2_react.py:625, 688`; `test_r2_integration.py` 534-543 (stale Apply receipt); `test_role_route_bridge.py:254`,
`test_role_stylesheet.py:867, 1136, 1231` (Clear with a current or equal version); Studio-side peer-mock tests in `test_studio_roles.py`.
The plan names `test_role_detection.py`, `test_role_routes.py`, `test_r2_integration.py` and the page-version tests; none asserts a stale Clear
refusal, so none is edited (they run as gates).

## Requirements

1. In `handleRoleMutation`, a Clear no longer compares `pageVersion`; it still rejects a different `documentId` as `page-changed`. Apply keeps
   both halves. The request is still validated whole first (`invalid-message`, `size-limit`) and `checkRevision` still runs (`revision-conflict`
   stays). Oracle: D080 text. Observed: a Clear carrying an old version removes the owned `<style>`; an Apply carrying the same old version is refused.
2. The Clear receipt still reports the truth: `pageVersion` echoes the request, `currentPageVersion` is the bridge's current one (greater
   after a change), `outcomesComplete` true, `revision` +1. No other receipt field changes. Oracle: the existing receipt table in
   `tests/role_contract.py` (the tests already validate receipts through it).
3. Update the four pins above to the new behaviour (assert acceptance and a removed preview, not a weaker "does not crash"):
   - React re-render test: the stale Clear returns `design:roles-applied`, `operation` `clear`, revision 2; `OWNED` is `[]` and `rendered` equals
     `literal()`; `currentPageVersion` is greater than the receipt's `pageVersion`. Drop the later fresh Detect and second Clear. Rename the test to
     `test_replaced_react_nodes_keep_the_preview_and_a_stale_clear_still_removes_it` and fix its docstring.
   - Hot-update test: send the Apply first (still `page-changed`, revision 1, `OWNED` `[DISPLAY_CSS]`, title shows `shown`), then the Clear
     (accepted, revision 2, `OWNED` `[]`). Keep the fresh Detect afterwards and its baseline check; drop the second Clear and adjust the revision.
   - Measurement-race test: Apply rejected as before; the Clear is accepted and removes the node; drop the fresh Detect and the second Clear.
   - Stylesheet table: delete the `pageVersion: 77` pair and say in the docstring that the stale-version case moved to the new test.
4. Two new tests in `test_role_stylesheet.py`, after the edited one (see Tests).

## Tests (each with a Given/When/Then docstring)

- `test_clear_removes_the_preview_after_the_author_text_changed` (RED before the fix). Given an applied 24px preview and an author text change
  in the page afterwards (`frame.evaluate` setting a paragraph's `textContent`), proven to have advanced the bridge's version by a Detect whose
  `currentPageVersion` is greater than `page.evaluate('roleState.pageVersion')`; when Clear carries the version Studio last observed (`self.clear(page)`
  as it is), then the reply is `design:roles-applied` with `operation` `clear`, `revision` 2 and `currentPageVersion` above `pageVersion`, the owned
  node list is `[]` and the page renders `16px` again. RED: the bridge answers `design:rejected` / `page-changed`, so the type assertion fails.
  Realistic break: restoring the `pageVersion` half for Clear. Oracle: the literal 16px of the unstyled fixture and the receipt table.
- `test_apply_after_the_author_text_changed_is_still_refused` (GREEN characterization; Apply behaviour does not change). Given a hello and the same
  real text change proven by a Detect, when Apply carries the old version, then the reply is `design:rejected` / `page-changed`, no owned node exists,
  the revision is 0 and the page renders `16px`. Realistic break: dropping the version check for Apply as well. No RED is manufactured.
- Reuse the existing helpers; no new helper (rule of three). The React edits are behaviour updates, not new tests.

## Focused command

From `the task's worktree`, one module per run, each with a timeout (the React module needs the installed fixtures and `node`; if the run skips or the
install check fails, say so in the report, never mark it green):

```
PYTHONPATH=tests FKS_ENGINES=chromium timeout 900 python -m unittest test_role_stylesheet test_support -v
PYTHONPATH=tests FKS_ENGINES=chromium timeout 900 python -m unittest test_r2_react test_support -v
```

Landing gates (not run in the code phase): `test_role_stylesheet`, `test_r2_react`, `test_studio_roles`, `test_role_routes`, `test_r2_integration`.
RED: run the new Clear test first on the unfixed bridge and quote the failure.

## Patch and commit

One row, one patch: `task-17-code.patch`. Subject (55 characters): `fix(bridge): never refuse Clear because the page changed`.
Body (why, 72 columns): D080 amends D063 for Clear only; a refused Clear left the preview on a page that never stops changing; Apply and Detect
keep the rule. It names the changed tests: the four pins above (React re-render, the two hot-update loops, the stylesheet table's version 77 case).
No process state, no attribution line.

CHANGELOG line (for the report's Handoff; the implementer does not edit `CHANGELOG.md`): "Clear preview now always removes the preview, even
when the page changed since the last Detect; Apply and Detect still report the change."

## Open questions

1. The plan's Touches line lists `test_role_stylesheet.py:273-274` and `427` as stale-Clear pins. At BASE 273-274 sit in `hostile_cases`, used only
   by Apply, so they stay; only 427 changes. The React pins at 624-625 and 687-688 were not in the plan and change. Recommendation: as written
   here; the plan text is superseded by this search.
2. The plan says the Studio-side Clear button is disabled when no preview is applied (`fontkit-studio.html:4352`), so the Studio flow needs
   no change. Recommendation: confirm at BASE during the read; if Studio itself blocks a stale Clear anywhere, stop and report, as that would
   widen the task beyond the bridge.

## Controller rulings

1. Open question 1: follow the brief's search over the plan text.
2. Open question 2: keep the check; the brief review settles it at BASE.

## Review fixes (binding: these govern over the text above)

1. Studio's Clear gate is `roleClearReason` at `fontkit-studio.html:4357`, not 4352, and it has no staleness test, so the check you were asked to make is settled: `fontkit-bridge.js:1545` is the only refusal.
2. Where the brief says to drop the second Clear in the two hot-update tests, keep their empty-receipt assertions.
3. Apply the remaining Minor items in `task-17-brief-review.md`. The commit subject is 56 characters.

---

# Task 17 follow-up: prove a stale Clear through the real Studio

The worktree `the task's worktree` holds Task 17's finished work, unstaged. Keep it. See `task-17-code-review.md`.

**Finding.** The patch tests a stale Clear only at the bridge. The reviewer proved the whole path with a scratch probe (`scratch/t17-probe`), but no committed test drives it. `AGENTS.md` asks for at least one test per boundary that runs the real Studio against the real bridge, and this is the plan's own check: "pressing Clear is accepted and the stylesheet is gone".

**Do this.** Add one test to `tests/test_studio_roles.py`, in a new class directly after the nearest related test, using `StudioRoleCase`, with a Given/When/Then docstring. Start from the scratch probe. Given a preview applied and acknowledged in the real Studio, when the page's version moves past the one Studio holds (a real text change on the page) and the user presses Clear, then Studio shows "Preview cleared.", the bridge-owned stylesheet is gone, and the element's computed style is back to its original value.

The test must assert its precondition: before pressing Clear, the bridge's page version differs from the one Studio last saw, and the owned stylesheet is present. Without that, a fast run could pass without the version ever going stale.

Show the break failing: restore the `pageVersion` half of the check for Clear, run the test, show it fails on the code the test loaded, then restore. Run it and its break 10 times each and report the rate. Touch only `tests/test_studio_roles.py`. Run `test_studio_roles` once. Rewrite `task-17-code.patch` from the worktree. Append to the REPORT.
