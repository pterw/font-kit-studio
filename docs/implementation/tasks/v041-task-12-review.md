### Spec Compliance
- PASS: Req 1. `stashLost` posts `edit-not-reapplied` with `record.id` and the literal message for a removed, dirty, non-stable record and returns; the stable path (`lost.set` + LOST_MAX trim) is unchanged (fontkit-bridge.js `stashLost`, D2-11 patch hunk @3406).
- PASS: Req 2. Clean or stable (author-id) removals post nothing; test 2 is the GREEN characterization with a `[]` assertion.
- PASS: Req 3. Only `stashLost` changed; `postWarning` and the removal loop are untouched; no new message type.
- PASS: Req 4. The B19 `postWarning('edit-reapply-stopped', record.id, <literal>)` sits inside the `!warnedLoops.has` block after the kept `console.warn`; REAPPLY_MAX / WINDOW untouched. requestId is omitted (arrives as null; asserted).
- PASS: New strings 2 and 3 are verbatim (checked against the brief in both source and test constants).
- PASS: Review fixes 1-4. B19 uses the quiet-page sequence (pingPong=false, second edit 44, render, 800 ms, count 1); test 2 asserts the new node's 50px; test 1 waits 300 ms before counting; the heading id comes from `ready` targets via `target_by_text(...)['id']`.
- PASS: Owned regions only: two source hunks, two new classes placed after `SpaRobustnessTests` and before `RepeatedConstructionTests`. Size 42 + 31 added lines, within the budget.
- PASS: Patch. On a temp tree built from `git archive 5443ff6` + task-10-code-r1.patch, `git apply --check` and apply succeeded for D2-11 then B19. The applied file keeps CRLF. Subjects (from the report) carry no process state.

### Checks run
- Applying in order -> scratch tree under scratch (BASE + t10-r1 + D2-11 + B19) -> all three applied clean.
- Focused: LostEditWarningTests + ReapplyStoppedWarningTests on that tree -> 3 tests OK.
- Break "early return for non-stable restored" -> test 1 fails `0 != 1 : []` (mutated JS was in the tree the tests loaded; the mutation script asserted exactly one match).
- Break "drop isDirty" -> test 2 fails on the warnings list (one warning for the clean heading). This also shows that the removal loop does run inside the 500 ms wait, so the `[]` in the green case is not an artifact of discovery never running.
- Break "drop the stable test" (the one the implementer skipped; `if (!record.stable)` -> `if (true)`) -> test 2 FAILS, but on the 50px precondition (`['', ''] != ['50px','important']`, because the stash path is skipped and the edit is not re-applied), not on the empty-warnings assertion. Caught either way.
- Break "B19 warnedLoops test dropped" (`if (true)`) -> 10 of 10 runs fail with `2 != 1` (two edit-reapply-stopped warnings). Unmutated B19 test -> 10 of 10 pass. Catch rate 10/10, no flake seen.
- B19 precondition (guard still tripped at the second render): REAPPLY_WINDOW_MS is 2000 and the second render occurs about 0.5 s after the first warning, so the margin is about 1.4 s. The no-guard run giving 2 shows the guard path is reached in every run.
- Regressions: `test_role_detection` 21 tests OK; `test_bridge_runtime` full module 134 tests OK (each once, chromium, on the patched scratch tree). Left for the wave gate: test_studio_roles, test_role_routes, test_r2_integration (Studio-side, not touched by these patches).
- Boundaries: the bridge only sends a `design:warning` through Task 10's `postWarning` with a kind it already whitelists; text is constant. No Studio change.
- Cleanup: scratch trees and logs removed; no process of mine is still running.

### Strengths
- Both new-warning tests assert kind, targetId, requestId (null) and the literal message together, so a wrong kind, id, or message fails them.
- Test 2's comment and 50px assertion tie the empty list to a real replacement of `spa.title`.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- tests/test_bridge_runtime.py B19 test: it does not assert that the guard window is still open at the second `render()` (an elapsed-time or `console.warn` precondition). On a very slow machine (more than about 1.4 s of drift) the second render would re-apply successfully and the count would be 1 vacuously. The measured margin makes this unlikely; recorded only.
- tests/test_bridge_runtime.py test 2: it does not check that the old `spa.title` node was disconnected. The 50px check plus the `isDirty` break are what show the render happened; recorded only.

### Plan-mandated (for the owner)
- None.

### Source conflicts (for the controller)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** Both rows meet the requirements and review fixes in the owned regions only. All three named breaks and the B19 break are caught (B19 10/10), the unmutated B19 test passes 10/10, and `test_bridge_runtime` and `test_role_detection` pass on the patched tree.
