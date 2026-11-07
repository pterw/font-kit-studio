### Spec Compliance
- PASS: Clear no longer compares pageVersion; documentId is still compared, Apply keeps both halves (fontkit-bridge.js:1545-1547). The check sits after the whole-request validation (invalid-message, size-limit) and after checkRevision, so revision-conflict stays. `a || b && c` precedence is right.
- PASS (a): a stale Clear is accepted and removes the owned style. New test `test_clear_removes_the_preview_after_the_author_text_changed` asserts type/operation/revision 2, currentPageVersion > pageVersion, owned == [] and 16px (test_role_stylesheet.py:165-180). A real page change still makes the next Apply refuse: `test_apply_after_the_author_text_changed_is_still_refused` (182-194) asserts page-changed, no owned node, revision 0, 16px.
- PASS (b): the four pins are updated as the brief says. The version-77 pair is removed and the docstring points to the new test (test_role_stylesheet.py:148-158). Each React pin now asserts acceptance and a removed node, and the Apply half stays rejected page-changed with revision 1, OWNED [DISPLAY_CSS] and the shown signature (test_r2_react.py:583-587, 619-634, 681-691). The empty-receipt assertions (roles, canonicalCss, cssHash, outcomesComplete, outcomes) moved onto the accepted Clear in both hot-update tests, as review fix 2 asks. D080 allows only this loosening.
- PASS (c): Studio's `validRoleReceipt` for a clear (fontkit-studio.html:4641-4648) requires roles == [], outcomesComplete and outcomes == []. It does not require currentPageVersion == pageVersion; that rule applies only to Apply (4657). `acceptRoleReceipt` then shows "Preview cleared." and advances identity. I confirmed it end to end with the real Studio and real bridge in a scratch probe (see Checks). The patch itself adds no real-Studio test for this; the brief did not ask for one.
- PASS (d): a Clear for `documentId: 'elsewhere'` is still refused page-changed. The retained table row (test_role_stylesheet.py:158) fails when the documentId check is removed for Clear (mutation m2).
- PASS: no files outside the owned regions are touched. `git apply --check --reverse` of the patch on the worktree succeeds. The patch has 3 tracked files and no stray file. The brief's subject is 55 characters and review fix 3 says 56, and the report uses the 55-character form from the brief, so I did not count it against the implementer. The patch file carries no commit message to check.

### Checks run
- Gate modules, one at a time, chromium, `PYTHONPATH=tests FKS_ENGINES=chromium timeout 900` in the task's worktree -> test_role_routes: 86 OK; test_r2_integration: 63 OK; test_studio_roles: 148 OK; test_role_detection: 55 OK. Output is in scratch/t17-review-run.txt. I did not rerun test_role_stylesheet or test_r2_react; the report says 87 and 44 OK.
- RED on the unfixed bridge -> scratch copy with BASE `fontkit-bridge.js` (scratch/t17-mut), run `test_role_stylesheet.AtomicRejectionTests` -> only the new Clear test FAILs, with `('design:rejected', None, 1) != ('design:roles-applied', 'clear', 2)`, reason page-changed. The Apply characterization test passes there, as the brief says.
- Mutation m1, drop the version check for Apply too -> `test_apply_after_the_author_text_changed_is_still_refused` and the wrong-page-version case FAIL. (The huge fan-out of other cases in the first run was because that mutation also stripped the documentId check.)
- Mutation m2, the documentId check applies to Apply only -> the `elsewhere` row FAILs.
- End to end with the real Studio, which no patch test covers -> scratch probe in scratch/t17-probe/probe_t17_review.py. It applies 24px, withholds rAF in the target so the bridge's roles-page announcement is delayed, appends an element, then clicks Studio's "Clear preview" at once. -> Studio sent Clear with pageVersion 0, the receipt came back pageVersion 0 / currentPageVersion 1 / clear / revision 2, the status read "Preview cleared.", Body rendered 16px, the preview CSS was empty and there were no page errors. On the BASE bridge the same probe times out, because the Clear is rejected and no receipt arrives.
- Cleanup -> no process of mine is left running. The scratch copies are in scratch.

### Strengths
- The change is one condition in one place. Apply, Detect and the invalid-message / size-limit / revision-conflict checks are untouched.
- The new Clear test builds its precondition from the bridge's own state (a Detect's currentPageVersion above `roleState.pageVersion`), so it asserts its own timing assumption.
- The Apply characterization test fails under the "drop the version check for Apply" break, so the asymmetry is pinned from both sides.

### Issues
#### Critical
- none
#### Important
- none
#### Minor
- test_r2_react.py:93-97 (first hot-update test): the fresh Detect and its baseline check now run after the Clear, so they read a page with no preview. They no longer show that Detect reads the author baseline while the preview is applied. The brief required this ordering ("Keep the fresh Detect afterwards"). `test_detect_after_apply_reads_the_baseline_and_leaves_the_preview_alone` (test_r2_integration.py:590) still covers that behaviour, so it is only recorded.
- No test in the patch drives a stale Clear through the real Studio (no automated test, only the scratch probe above). The brief did not ask for one; the wave gate might add one.

### Plan-mandated (for the owner)
- [Minor] The hot-update baseline check moves after Clear and loses its "preview applied" precondition (test_r2_react.py:93-97) -- brief requires: "Keep the fresh Detect afterwards and its baseline check; drop the second Clear and adjust the revision."

### Source conflicts (for the controller)
- none

### Assessment
**Task quality:** Approved
**Reasoning:** Clear alone skips the page-version check, still rejects a foreign document, and Studio accepts and shows the resulting receipt. I verified this in a real Studio and bridge probe and with mutations. The updated pins still prove acceptance, a removed preview, and a refused stale Apply, and the four gate modules pass.

---

### Spec Compliance
- PASS: one new class StudioStaleClearTests (tests/test_studio_roles.py, end of file, after StudioIdleRoleControlTests) using StudioRoleCase, Given/When/Then docstring, only that file changed in the round.
- PASS: precondition asserted before the press: bridge pageVersion differs from the receipt's (frame.wait_for_function), owned stylesheet count is 1, Body 24px.
- PASS: Studio really sends the stale version: the test captures the design:roles-clear message in the target (`__sent[0].pageVersion == seen`) and asserts currentPageVersion in the receipt is greater. Outcomes asserted: "Preview cleared.", owned styles 0, Body 16px, no page errors.
- PASS: patch applies on top of the head of fix/v0.4.1-repairs (f56256a): `git read-tree` into a temporary index, then `git apply --cached --check task-17-code.patch` -> APPLIES. (The merge-base with the branch is still 5443ff6, so the branch moved only by other commits.)

### Checks run
- Is the held-back state reachable by a real user? -> read fontkit-bridge.js scheduleRolePage/sendRolePage/expireRolePageHold (1319-1370) and fontkit-studio.html acceptRolesPage (4616) -> yes. The bridge bumps pageVersion at once on any author mutation (noteRoleMutations 1265), but tells Studio only after a rendered frame plus 0 ms (250 ms fallback), at most one notice per 250 ms (ROLE_PAGE_GAP_MS hold), and a hidden tab may not paint. Studio updates its held version only in acceptRolesPage. A Clear pressed in that gap, or in a throttled/hidden tab, sends the older version. The test makes the gap permanent by dropping the notice (capture listener with stopImmediatePropagation on the Studio window, rAF stubbed in the target), so it is a stretched real window, not a state only the test can make. Studio's own handler is not patched.
- Does the Clear carry the stale version? -> test reads the message at the target (`__sent[0].pageVersion`) and compares to `seen` from the last Apply receipt -> yes, and the bridge's version is shown different by the precondition wait.
- Run 5 times: `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_studio_roles.StudioStaleClearTests` in the task's worktree -> 5/5 OK (1.5-1.7 s each).
- Break once: copy of bridge, studio html, tests, fixtures in the scratchpad (worktree untouched); Clear check changed to `data.pageVersion !== this.pageVersion` for both operations -> test errors with `Page.wait_for_function: Timeout 30000ms exceeded` (Studio never shows "Preview cleared."). A pass would have shown the copy was not loaded; the failure shows it was.

### Strengths
- The precondition is asserted from both sides (bridge version vs. Studio's held version, and owned stylesheet present), so a fast run cannot pass without the version going stale.
- Reads Studio's held version from the Apply receipt and the sent version at the target, not from a mock.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- tests/test_studio_roles.py, docstring: says "the page's text changes" but the test appends an `hr` element (a childList mutation). Any non-bridge mutation bumps the version, so the proof is the same; wording only.
- The notice is dropped for good, whereas a real one arrives within about 250 ms. The test proves the stale Clear is accepted; it does not exercise the later notice. Fine for the claim.

### Plan-mandated (for the owner)
None.

### Source conflicts (for the controller)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The new test drives the real Studio against the real bridge through a reachable stale-version window, asserts its precondition and the version actually sent, passes 5/5 and fails when the Clear check is restored. The patch applies on the current branch head.
