# Task 17 code report (mode code, BASE 5443ff6)

Changed: fontkit-bridge.js (handleRoleMutation: Clear checks documentId only; Apply keeps both; 2-line comment),
tests/test_role_stylesheet.py (docstring + version-77 pair removed; 2 new tests after it), tests/test_r2_react.py
(3 tests updated, one renamed per the brief). Patch: task-17-code.patch (3 files, tracked only; no new files).

## RED
New Clear test on the unfixed bridge: `AssertionError: ('design:rejected', None, 1) != ('design:roles-applied', 'clear', 2)`
(reason page-changed). The Apply characterization test passed on the unfixed bridge, as the brief says.
Mutation: restoring `|| data.pageVersion !== ...` for Clear made 3 React tests ERROR (replaced-nodes, both hot-update
tests); the mutated bridge file is what the tests loaded. Restored afterwards; AtomicRejectionTests green again.

## GREEN (FKS_ENGINES=chromium, FKS_REQUIRE_FIXTURES=1 for React; React did not skip)
- test_r2_react + test_support: Ran 44, OK
- test_role_stylesheet + test_support: Ran 87, OK

## Notes
- Review fixes applied: the docstring says a version ahead of the bridge is accepted too (D080, not a Studio flow); empty-receipt
  assertions (roles/canonicalCss/cssHash/outcomesComplete/outcomes) moved onto the accepted stale Clear in both hot-update tests.
- Nothing outside the owned regions was touched. No other test broke (only the two modules were run, per the dispatch).

## Handoff
Commit subject: fix(bridge): never refuse Clear because the page changed
Body: D080 amends D063 for Clear only; a refused Clear left the preview on a page that never stops changing; Apply and Detect
keep the rule. Changed tests: React re-render, the two hot-update loops, the stylesheet table's version 77 case.
CHANGELOG line: "Clear preview now always removes the preview, even when the page changed since the last Detect; Apply and Detect still report the change."

## Follow-up (task-17-fix1): a stale Clear through the real Studio

Added `StudioStaleClearTests.test_clear_after_the_author_text_changed_removes_the_preview_and_says_so` at the end of
`tests/test_studio_roles.py` (after the class holding the nearest test, `StudioIdleRoleControlTests`), with a small
`RECEIPTS` init script so Studio's last-heard page version is read from the Apply receipt. Only that file changed in this round.

Flow: real Studio + real bridge, detect, apply 24px, wait for "Preview applied to 1 role". The page's `design:roles-page`
notice is held back (no animation frame in the target, and Studio ignores the notice), a real element is appended, and the
test waits until the bridge's pageVersion differs from the receipt's. Precondition asserts: bridge pageVersion != the version
Studio holds, one `style[data-fontkit-role-styles]` present, Body 24px. Then Clear is pressed. Asserts: the Clear Studio
sent carries the older version, the receipt's currentPageVersion is greater, status "Preview cleared.", owned styles 0,
Body 16px, no page errors. Note: the target frame has no rAF, so waits there use `polling=50`.

Evidence (chromium, `PYTHONPATH=tests FKS_ENGINES=chromium timeout ... python -m unittest test_studio_roles.StudioStaleClearTests`):
- Fixed bridge, 10 runs: pass 10/10 (about 1.7 s each).
- Break: bridge Clear check restored to `data.pageVersion !== this.pageVersion` for both operations (the code the test loaded
  was the mutated /fontkit-bridge.js in the task's worktree), 10 runs: pass 0/10; each fails with
  `TimeoutError: Page.wait_for_function` (Studio never shows "Preview cleared." because the bridge rejects page-changed).
- Bridge restored byte-for-byte (cmp against a saved copy, scratch/t17-fix1-bridge-good.js).
- `test_studio_roles` once on the final tree: see the Ran/OK line below.
- `PYTHONPATH=tests FKS_ENGINES=chromium timeout 900 python -m unittest test_studio_roles` -> `Ran 115 tests in 183.398s` `OK`
  (114 at BASE plus the new one; the review's "148 OK" line in t17-review-run.txt is a different count, likely another module, not investigated).
- Patch rewritten: task-17-code.patch (4 files: fontkit-bridge.js, test_r2_react.py, test_role_stylesheet.py, test_studio_roles.py); `git apply --check -R` passes.
- Nothing left running. Scratch: scratch/t17-dbg.py, t17-fix1-bridge-good.js.
