# Task 1 code report: NEEDS_CONTEXT (diagnosis done, no patch)

Mode code, BASE 5443ff6, worktree the task's worktree. `fontkit-bridge.js` restored to BASE (git diff clean). Only
`tests/test_role_detection.py` carries uncommitted work (draft `ClosedDetailsDetectionTests`, hard-codes the
"exclude" counts 3/4; must change with the answer). No patch written.

## Requirement 1 diagnosis (demo, clean BASE, probe is non-perturbing: one existing `range.getClientRects()` captured)
Cause: layout-state, not a page change. In Chromium the closed `<details>` bodies (`<p>`) report 0 text-range rects on the
first read of the first Detect and 1 on every later read, so the start loop and the end check disagree.
- Press 1 (reply: complete false, page-changed, scannedElements 60, pageVersion 0 == currentPageVersion 0):
  - start loop (2107-2116) read rects for the 3 closed `<p>`: "No. Each cli"=0, "Yes. Drag in"=0, "Your portals"=0
    -> skipped, not in `styles` (styles = 60 parents, no closed `<p>`).
  - end check (2175-2181) re-read "No. Each cli" = 1 -> rendered but `!styles.has(el)` -> line 2181 returns
    `page-changed`. `rendered` so far 49 of the 60 when it aborted.
- Press 2 (complete, scannedElements 63): start loop reads all three = 1 (in `styles`), end reads all three = 1;
  `styles` 63 == `rendered` 63. Difference vs press 1: exactly the 3 closed `<p>`.
- Fixture (main + closed details): press 1 page-changed, scanned 3; press 2 complete, scanned 4.
- Not 2185 (size guard); not S06; no page-version bump.

## Precondition masks the bug (Review fix 3 as written)
Reading `#closed-body.getClientRects()` before press 1 primes layout: press 1 then completes with 4 (no RED). Without
the read, press 1 is page-changed with 3. Any layout read on the closed body (el rects, a second range read) flips
the first range read to 1; instrumented runs that did extra reads in the start loop also completed. So the
precondition must be non-perturbing (candidates to verify: `details.open === false`, `el.checkVisibility()`,
`getComputedStyle(details, '::details-content').contentVisibility`); a rects-based assertion cannot be used.
Also: after layout the closed `<p>` does have rects (getBoundingClientRect height 18 on a fresh page).

## The question (blocks the patch)
Press 2 TODAY counts the closed paragraphs (demo 63 not 60; fixture 4 not 3). Review fix 2 says press 2 must stay what
it is today, so the predicate must count closed-details text at both ends (e.g. prime layout / treat closed body as
rendered). Review fixes 3 and 4 and the meaning of "rendered" read as excluding the hidden body (then press 2 changes to
60/3). Which governs: (A) count closed-details text at both ends (press 2 unchanged), or (B) exclude closed-details
body text (not `<summary>`, nested/open kept) at both ends via a shared predicate in `renderedRoleText`? Test numbers
and the predicate direction flip together. A is Chromium-specific and counts text that is not visible; B is a stable
predicate but changes the scanned counts.

## Handoff
CHANGELOG line (unchanged from brief): "The first Detect on a page with a closed disclosure (`<details>`) now completes
instead of reporting an incomplete detection." Scratch: scratch/t1_probe*.py (mine).

---
# Continuation (ruling option A): patch written

Files: `fontkit-bridge.js` (+6, in `renderedRoleText`), `tests/test_role_detection.py` (+~80, class `ClosedDetailsDetectionTests`).
Patch: `task-1-code.patch` (from `git diff`, no staging, no commit).

## Fix
In `renderedRoleText`, after the display/opacity/visibility/colour checks and before the rect test: walk `el.closest('details')`
upward; if a details is not `open` and `el` is not inside its first `:scope > summary`, return true (rendered, no rect read).
Used by both the start loop and the end check. The end check (2175-2185) and size guard are untouched.

## Tests (4, chromium)
1. fixture, fresh connection, precondition `details.open === false` via a plain `frame.evaluate`: first Detect complete, 4 scanned, equals second.
2. demo: same, 63 scanned.
3. `test_details_text_is_counted_by_where_it_sits_not_by_a_rect_read`, subTests: hidden text in closed body excluded (+1 summary only);
   summary of closed details counted; clipped text outside any details excluded (added so "rule applied to every element" fails);
   open details body counted (+2). Deltas are over a baseline detect of the plain fixture.
4. `test_an_animation_during_a_scan_still_ends_page_changed_beside_a_closed_details`: large-page fixture plus a closed details,
   `.g00.animate(fontSize)` after `design:detect` is sent, reply `complete False, page-changed`; fresh detect completes.
   I replaced my draft's text-insert (and a stylesheet-rule variant): on the small fixture the scan ended before the timer, and
   a rule insert is caught by page-version freshness, not the end check. A Web Animation changes computed style with no DOM or
   rule mutation, so only the end check can catch it.

## Breaks (each run on the whole class; mutated file is what the tests loaded, restored after from scratch/t1_fixed.js)
- Rule removed (BASE bridge): FAIL demo test (first reply page-changed) and FAIL animation test. Fixture test: RED when run alone
  (twice, reply complete:false), but it PASSED at BASE when run inside the class after the earlier tests, so layout warm-up leaks
  between tests in one process. Per-module run is order dependent for that one test; the demo test is the stable RED.
- Rule applied to every element (`return true;` after the loop): FAIL test 3, case "clipped text outside any details".
- Rule before the hidden checks: FAIL test 3, case "hidden text in a closed body".
- Both end-check returns neutered (`/*x*/` and `{}`): FAIL the animation test (the other three passed). This is the "ignore all
  mismatches" break; the guard removal oracle of brief req 5.

## Runs (chromium, one module at a time)
- test_role_detection: Ran 25, OK. test_bridge_runtime: Ran 128, OK. test_support: Ran 34, OK. No pre-existing test broke.

## Outside regions / concerns
- None outside `renderedRoleText` and the new class. The fixture test is RED alone but order dependent in-class (above); the
  controller may want it run alone for RED evidence.
- Detect now counts closed-body text (63 demo, 4 fixture), as ruled; summary text unchanged.

## Handoff
CHANGELOG (Fixed): "The first Detect on a page with a closed disclosure (`<details>`) now completes instead of reporting an
incomplete detection." Commit subject: `fix(bridge): count closed details text the same at both ends of a Detect scan`.

## Follow-up
Changed (worktree the task's worktree, unstaged; patch rewritten at task-1-code.patch, `git apply --check -R` passes):
1. Dropped the fixture test and the unused `CLOSED` constant. The demo test is the RED proof; the class now has 3 tests.
2. End-check test: the animation is kept in `window.probeAnimation` and `.cancel()`led before the second Detect; the first
   reply also asserts `pageVersion == currentPageVersion`, so freshness did not catch it. Kept the font-size trigger.
3. Test 3 gained two subTests: "clipped summary of a closed details" (+0) and "open details inside a closed one" (+3 over base,
   its body `<p>` is clipped `height:0;overflow:hidden` so only the climbing rule counts it; with an unclipped body the case
   passed under the no-climb break because layout state counted it).
4. Bridge: `if (d.open) continue;` first, then `el.closest('summary')` compared by parent to `d`; no `querySelector(':scope > summary')`.

Breaks (the worktree bridge is what the tests load; restored byte-for-byte from scratch/t1fix1_good.js, `cmp` clean):
- Summary exemption removed (`return true;`): test 3 FAILS, case "clipped summary of a closed details", `3 != 2`.
- Climb replaced by closest-only (`d = null`): test 3 FAILS 3 of 3 runs, case "open details inside a closed one".
- Both end-check returns neutered: animation test passes 0/10. At the fixed code it passes 10/10.

Runs, one module at a time, chromium: test_role_detection Ran 24 OK; test_bridge_runtime Ran 128 OK; test_support OK (Ran line cut
by my tail, exit 0). The earlier "RED when run alone" claim for the fixture test is withdrawn (test removed). Demo-test RED
at BASE (10/10 per the review) was not re-run; the rule's behaviour for closed-body text is unchanged. Nothing left running.

Handoff: CHANGELOG line and commit subject unchanged.
