# Task 1 brief: the first Detect on a page with a closed `<details>` completes (C1-1)

Plan task 1, wave 1, lands first, mode code. BASE `5443ff6`, worktree `the task's worktree`. Audit row C1-1 (one row, so one patch,
`task-1-code.patch`). Budget: about 60 gross lines (bridge 5-15, tests 40-50); Markdown not counted.

## Why

On ScrobbleScope `/` and on the bundled demo, the first Detect after Connected ends "Incomplete detection (page-changed)" though
nothing changed; the second press completes (audit row C1-1: 5 of 5 fresh runs fail once, then 19 roles from 53 parents; opening the
disclosure first makes the first press complete; `/results`, which has no `<details>`, completed). The demo has three closed
`<details>` (`demo/index.html:293-304`) and loads the bridge (`demo/index.html:352`). S06 is not the cause (no mutation recorded).
This is not a page-version change; D063 and D066 do not move.

Where it ends: `collectRoleStyles` (`fontkit-bridge.js:2092`) records each rendered text parent in `styles` (loop 2107-2116, using
`renderedRoleText` at 1427). Its closing check (2174-2185) walks the text again, and if a parent is rendered but not in `styles`, or
`rendered.size !== styles.size`, it bumps `roleNative` and returns `'page-changed'` (2181, 2185).

## Open questions

1. The plan's cause does not follow from the code as read at BASE. `renderedRoleText` returns false when the text has no client
   rects, and that test is the same call at the start (2112) and the end (2179), so closed-details text should be skipped at both ends.
   Something must differ between the two reads (candidates: a closed `<details>` body with `content-visibility: hidden` that gets
   laid out after the first scan's own work; the `visibility` WeakMap cache passed at the start but not at the end, 1427 and 2179;
   `styleSignature` changing for the summary or its parent). The implementer finds out, per requirement 1. Recommendation: if the
   evidence points somewhere other than 2175-2185 and `renderedRoleText`, stop and report with the evidence instead of widening the
   region. Do not paper over it by ignoring mismatches.

## Owned files (exact)

- `fontkit-bridge.js`: lines 2174-2185 (the end-of-scan check) and, only if the evidence needs it, `renderedRoleText` (1427-1456).
  Other tasks edit other regions of this file at the same time (Addendum 1); stay inside these.
- `tests/test_role_detection.py`: one new class, `ClosedDetailsDetectionTests(RoleBridgeCase)`, inserted directly after the last test of
  `RoleDetectionTests` (the end of that class, immediately before `class TransitionBaselineTests`, line 639 at BASE). No existing test
  is edited.
- Everything else is read-only, including `demo/index.html` and all other fixtures. Put the test page in the test itself (inject a
  `<details>` with `frame.evaluate` before `self.hello`) rather than adding a fixture file.

## Read first

- `fontkit-bridge.js` 2092-2186 and 1427-1456; the job wrapper 2018-2090 (`fresh()` and the `roleNative` comparison at 2033-2045).
- `tests/role_support.py` 12-70 (`open(engine, target=...)`, `detect`; the document route serves a file, so a demo target is
  `TARGET + '/demo/index.html'`, not `/demo/`).
- `tests/test_role_detection.py` 412-460 (mid-scan change pattern: `design:detect` listener plus `setTimeout`) and 38-60 (inject a node
  before `hello`).

## Requirements

1. Diagnose before fixing. Run the first press and the second press on a page with a closed `<details>` and record, for each, the set
   of parent elements in `styles` and in `rendered` (a temporary local probe, removed before the patch) and which line returns
   `page-changed`. Put the two sets and the line in the report. Oracle: the report shows the difference between press 1 and press 2.
2. A first Detect on a fresh connection to a page with text in a closed `<details>` replies `complete: true`. Oracle: the second
   press on the same page, whose `groups` (ids aside, compare identity and `elementCount`) and `scannedElements` equal the first's
   literally. The page observes no page-version bump: `pageVersion == currentPageVersion` on the first reply.
3. Same on the bundled demo (`TARGET + '/demo/index.html'`): first press complete, and equal to the second press. Oracle: the second
   press.
4. A real change still ends `page-changed`: a visible text node inserted into `main` after `design:detect` is sent and before the scan
   finishes (the existing `content` pattern, 412-445) replies `complete: false, reason: 'page-changed'`. Oracle: the literal
   reason string, and a fresh Detect afterwards completes and counts the inserted text.
5. The fix counts closed-details text the same way at both ends of the scan. It does not remove the `rendered.size !== styles.size`
   guard and does not skip comparisons for text inside `<details>` (that would hide a real change in an open one). Oracle: the
   requirement 4 test with the guard removed fails (show it).
6. No new user-facing string, no message or field change, protocol stays 1, version labels stay 0.4.0.

## Tests

Three tests, all in `ClosedDetailsDetectionTests`, each with a Given/When/Then docstring and `for engine in ENGINES` with
`subTest`, as the neighbours do.

- `test_first_detect_on_a_page_with_a_closed_details_completes_like_the_second` (req 2). RED at BASE: the first reply is
  `complete: false, reason: 'page-changed'`. That is the audit symptom; if it does not reproduce, stop (open question 1). Realistic
  break: reverting the fix.
- `test_first_detect_on_the_demo_page_completes_like_the_second` (req 3). RED at BASE for the same reason. Realistic break: a fix
  that special-cases a test fixture's markup but not the demo's.
- `test_text_inserted_during_a_scan_still_ends_page_changed_beside_a_closed_details` (req 4 and 5). GREEN characterization at BASE
  (it passes before and after); never manufactured RED. Its break to show: ignore all end-of-scan mismatches (delete the 2181 and
  2185 returns), and the test fails.

Keep the suite lean: one behaviour per test, no copy of the existing role tests' other assertions.

## Focused command

From `the task's worktree`, bounded to 600 seconds:

`PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_role_detection test_support -v`

Studio landings also run `test_studio_roles`, `test_role_routes` and `test_r2_integration`, but this task touches no Studio file, so
the controller runs them at the wave landing. Also run `test_bridge_runtime` (imports the bridge and holds the demo tests at
3370-3430) as a second command, one module at a time. No shards, no dev server.

## Patches

One patch, `task-1-code.patch`, one commit:

`fix(bridge): count closed details text the same at both ends of a Detect scan`

CHANGELOG line (a user notices it; the controller adds it at landing, under `### Fixed` in `## [Unreleased]`): "The first Detect on a
page with a closed disclosure (`<details>`) now completes instead of reporting an incomplete detection."

Report: the requirement 1 evidence, RED and GREEN output per test, the guard-removed failure, the focused outputs, and the patch's
file list (expected: `fontkit-bridge.js`, `tests/test_role_detection.py`).

## Controller rulings

1. Open question: keep diagnosis as the first requirement. If the evidence points outside the owned lines, stop and report with the press-1 and press-2 sets.

## Review fixes (binding: these govern over the text above)

1. If the probe shows the two reads differ in rects, the expected place for the fix is a rendering predicate in `renderedRoleText` (1427-1456), used at both ends. That is inside your owned lines, so do not stop and report for it. Requirement 5 forbids skipping comparisons only in the end check, not a shared predicate.
2. `<summary>` text stays counted. Nested `<details>` and `details[open]` keep working. The second press's result must stay what it is today (19 roles, 53 parents on the audited shape, or the fixture's equivalent).
3. RED at BASE is Chromium-only. The first test asserts its own precondition before the first press: the closed `<p>` has no client rects. A browser that stops hiding the body then fails the test rather than passing it for the wrong reason.
4. Add one assertion that a visible text or summary text is a group member, so a fix that drops everything under `<details>` cannot pass.

---

# Task 1 continuation: the controller's ruling on closed details

Continue from the state of `the task's worktree`: `fontkit-bridge.js` is at BASE, and `tests/test_role_detection.py` holds a draft `ClosedDetailsDetectionTests`. Read `task-1-brief.md` and the diagnosis in `task-1-code-report.md`; do not repeat the diagnosis. Where this file differs from the brief or its Review fixes, this file governs.

## Ruling (option A)

Text in the body of a closed `<details>` counts as rendered at both ends of a Detect scan, so press 1 equals what press 2 finds today: 63 on the demo, 4 on the fixture. Reasons: the plan requires the same roles and parent count the second press finds; that text is real content a user restyles and later opens; and a rule stated in the code gives the same result in every engine, where Chromium's lazy layout does not.

## Fix

In `renderedRoleText` (1427-1456), one shared rule used by both the start loop and the end check: when the text is inside the body of a closed `<details>`, skip the client-rect test and treat it as rendered. Every check before the rect test still applies, so `display:none`, `visibility:hidden`, zero opacity and a transparent colour inside the body still exclude it. Do not read rects to decide this: reading them is what changes the result. `<summary>` text and text in an open `<details>` keep today's path. A closed `<details>` nested in a closed one counts as closed; text in a closed `<details>` inside an open one counts as closed.

Do not change the end check at 2175-2185, and do not skip any comparison there.

## Tests

Replace the draft's numbers: they hard-code the excluded counts 3 and 4.

1. Fixture, fresh connection: Detect once ends complete with 4 scanned, and a second Detect gives the same role list and count. The precondition must not disturb layout: assert `details.open === false` before the press. Never read the closed body's rects first, because that makes the press pass at BASE (your report measured this). This test is RED at BASE.
2. The bundled demo page, the same, with 63 scanned.
3. One case each, in the same test by subTest: hidden text inside a closed body stays excluded; summary text is a group member; text in an open `<details>` is counted.
4. A real change during the scan still ends `page-changed` (the plan's check). Show it failing if the fix ignores all mismatches.

Show a break for each: the rule removed; the rule applied to every element; the rule placed before the hidden checks.

Review fix 3 in the brief is replaced by test 1's precondition. Review fixes 1, 2 and 4 stand; "the second press's result stays what it is today" is now exact.

Run `test_role_detection`, `test_bridge_runtime` and `test_support`, one at a time. Write `task-1-code.patch`. Append to the report.

---

# Task 1 follow-up

The worktree `the task's worktree` holds Task 1's work, unstaged. Keep it. Read `task-1-code-review.md`: Issues and "answer 1". Ruling C1 stands. Where this file differs from `task-1-continue-brief.md`, this file governs.

1. **Drop the fixture test** (`test_role_detection.py:34-48`). It passes at BASE in 5 of 10 fresh processes, so it proves nothing. The bundled demo test, which fails at BASE 10 of 10 and passes at the fix, is the proof. This replaces the continuation brief's test 1. Keep a fixture only where another case needs it.
2. **Make the end-check test reliable.** It fails 7 of 10 runs at the fixed code, because the animation is still running at the second Detect. Call `.cancel()` on the animation before the second Detect. Assert `pageVersion == currentPageVersion` on the first reply, so the test shows the end check caught the change, not page-version freshness. If the reviewer's closer check is as simple (a text node that turns visible mid-scan, with its visibility animation cancelled during the scan), use it instead; it caught 10 of 10 at the fix and under the break.
3. **Pin the two untested parts of the rule**, as subTest cases in test 3: clipped summary text (`<details><summary style="height:0;overflow:hidden">S</summary></details>`) adds 0, which fails if the summary exemption is removed; an open `<details>` inside a closed one is counted, which fails if the climb becomes `closest('details')` alone.
4. **Remove the quadratic case.** Test `d.open` first, so an open `<details>` costs nothing, and find the summary from the text's side: `el.closest('summary')`, compared by parent to `d`, not `d.querySelector(':scope > summary')`. Behaviour stays the same; the case in item 3 guards it.

Show each break failing on the code the test loaded, then restore. **Run the end-check test and its break 10 times each and report the rate.** Run `test_role_detection`, `test_bridge_runtime` and `test_support`, one at a time, once each. Rewrite `task-1-code.patch` from the worktree. Append to the report.
