### Spec Compliance
- PASS: patch is one file, `tests/test_studio_live.py` (+101/-40); `fontkit-studio.html` and the fixture untouched. SHA-256 of the patch (d5a99657...94d) equals `git diff --cached` in `C:/fks/tt2`; the frozen worktree's `fontkit-studio.html` (bd3beabd...d804) and test file (09d8b9ec...fbe86) were identical before and after my work, `git status` shows only `M  tests/test_studio_live.py`.
- PASS: hold mechanism as briefed (tests/test_studio_live.py:171-198): routes registered on `page.context` after `self.open(engine, target=None)` and before `connect`; fixture copy with exactly one `</body>` asserted, `<img>` added, served at the exact `FAKE` string (so `?late=1` stays on the module routes); image routed to `lambda route: held.append(route)`; poll up to 5 s (100 x 50 ms) by condition; `assertEqual(len(held), 1, 'the page requested its held image')`; frame wait on `readyState !== "complete"` plus a received hello; then fulfil (204); then wait for >= 2 hellos on the current document; `wait_connected`'s fixed sleep is not used for these paths.
- PASS: order recorder installed before `connect`, lists cleared before each reload, `window.__order` asserted against the literal pair before any session assertion (:339, :1162/1175).
- PASS: `wait_for_timeout(100)` after the reload replaced by `performance.timeOrigin` wait (:1157-1158 of the new file region, `frame.wait_for_function(..., arg=started)`).
- PASS: `?target=` half moved to its own `self.context(engine)` page, assertions unchanged (:357-368).
- PASS: both tests keep their names and have Given/When/Then docstrings; each Then matches the assertions (handshake: order, badges Connecting/Bridge detected/Connected, exactly two hellos, origin/protocol/session shape, 1 or 2 sessions, last == design:ready session, `?target=` prefill/Live App/connect/no page error; reload: order, exactly two hellos, session relations, no-bridge badge, hint visible, no live controls, no page error). The "Connected" in the Then is asserted by `wait_badge` inside `wait_greeted`.
- PASS: `LiveCase.open` signature unchanged.
- PASS (disclosed departure, see Minor 1): module constants `ANNOUNCE_ORDERS`, `ORDER_RECORDER` and `from itertools import product` beyond "at most two small LiveCase methods".
- PASS: sibling pre-scan listed in the report (see checklist 7).

### Checks run
- Patch identity -> `sha256sum` of the patch file and of `git diff --cached` in `C:/fks/tt2` -> both d5a996574cfe415266c1b807da67dffe25c6c26bfb12ceefff79316ed4c9a94d.
- Mutants 1-3 and the report's 4 reproduced on a copy of the worktree outside the repository (`scratchpad/t2rv-copy`; `PYTHONPATH=tests FKS_ENGINES=chromium FKS_REQUIRE_FIXTURES=1 python -m unittest <the two ids>`); copy run unmutated first: `Ran 2 tests ... OK`. Results in checklist 2.
- Sibling `test_every_control_message_carries_protocol_version_and_session` forced load-first -> scratch module `scratchpad/t2rv-mods/t2rv_late.py` (patches `LiveCase.open` in memory to append `?late=1`), 2 runs on the copy -> 2 of 2 `AssertionError: 'fks-...' != 'fks-...'` at test_studio_live.py:1133 (the `data.get('sessionId'), sid` assertion); control run without the patch -> `OK`. Confirmed.
- Other order-sensitive tests -> `t2rv_late2.py`, the 8 tests the report calls order-agnostic (Defect spoof, 5 Protocol tests, Arrange move, Popout) forced load-first on the copy -> `Ran 8 tests ... OK`. Confirmed.
- `python -m ruff check tests/test_studio_live.py` in the worktree -> All checks passed. `git diff --cached --check` -> rc 0.
- Skips -> grep `skip` in tests/test_studio_live.py, tests/support.py; grep the two test names in `tests/firefox_canary.py`, `scripts/dev/*.py`, `.github/workflows/*.yml` -> no skip decorator or condition on the changed tests; no other runner selects them.
- Possible race on `window.__ready[-1]` in the load-first handshake (the fake's second design:ready might not have reached Studio's page when the assertion runs) -> read Studio's `design:ready` case (fontkit-studio.html:5495-5512) and `acceptBridgeMessage` (4457-4464) -> after bridge-ready the badge reads "Bridge detected" until the S2 ready is accepted, Studio's listener sets `Connected` and the recorder's listener pushes in the same dispatch, and `wait_greeted` waits for `Connected` after the 2nd hello; so `__ready` holds S2 when the assertion runs. No race found.
- I did not run the full five-run gate or the loaded run; I rely on the report for those (my copy runs: the two tests passed at the start of each mutant sequence and in the unmutated control).

### Review checklist
1. Drift: not applicable. The patch touches no contract field (test file only; no `tests/role_contract.py`, no bridge or Studio code).
2. Mutants (all on a copy outside the repository; the copy's `fontkit-studio.html` and test file were restored byte-exact: bd3beabd...d804 and 09d8b9ec...fbe86 before and after each):
   - Mutant 1 (`:4496` `live.sessionId || newSessionId()`): 3 failures. Handshake load-first `:351` `1 != 2`; reload bridge-ready-first `:1172` (`assertNotEqual(hellos[0], sid)`); reload load-first `:1168` (`assertNotEqual(hellos[1], sid)`). Matches the brief.
   - Mutant 2 (`:4644` unconditional `newSessionId()`): 3 failures. Handshake bridge-ready-first `:351` `2 != 1`; reload bridge-ready-first `:1171` `2 != 1`; reload load-first `:1167` `hellos[0] != sid`. Matches the brief.
   - Mutant 3 (image fulfilled at once): both tests fail at `wait_greeted:191` `0 != 1 : the page requested its held image` (call sites :338 and :1154), never at a session assertion. Matches the brief.
   - Mutant 4 (report's extra, late variant forced to normal announce): both tests fail at the order premise (:339, :1162) `Lists differ: ['bridge-ready', 'load'] != ['load', 'bridge-ready']`. Matches the report.
3. Fake versus real: everything runs against the fake target (`fake-target.html`) and Studio's real `fontkit-studio.html`; the real `fontkit-bridge.js` is not exercised. The brief allows it (module docstring, brief "Owned files": fixture read-only, `?late` switch named as the load-first mechanism). Load-first depends on the fake's 60 ms timer after its own load event (`fake-target.html:524`); a lost race fails at the order premise (mutant 4), not at a session count. The held variant needs `fake-target.html` to contain exactly one `</body>`; a changed fixture fails loudly (:39).
4. Hidden skips: none. The two changed tests have no skip decorator or in-test skip; hosted CI runs them with `FKS_ENGINES=chromium`, so the `firefox` and `webkit` subtests of the `ENGINES` loops do not run there, as for every test in the module (the Firefox canary does not select them). No change in skip behaviour versus BASE.
5. Tests: expected values are literals (order pairs, 2 hellos, protocol 1, regex, 1 or 2 sessions), the order log, and `window.__ready[-1]` (the fake's design:ready reply). `session_id(frame)` is used only for `sid`, the session of the document before a reload, compared across documents (the brief's own form); never as the bridge's session. Outcomes are observable (messages on the wire, badge text, hint visibility). The only fixed waits left are 50 ms ticks of condition polls (:107, :190) and the unchanged `wait_connected` (150 ms, used only by the unchanged `?target=` half and the other tests). Each test fails when the behaviour is removed (mutants 1-4). No near-duplicates.
6. Code: `hold_load` (one hold-variant caller per test, two tests) and `wait_greeted` (both branches exercised: `held` path in the bridge-ready variants, `None` path in the late variants) have no untested branch; the constants have two callers each. Gross 141 against about 120; the report's explanation (41 shared infrastructure lines, 11 docstring lines, no churn) holds on the diff. Minor 2.
7. Sibling confirmed: `StudioFixRound1Tests.test_every_control_message_carries_protocol_version_and_session` fails 2 of 2 in my runs when the target loads first (`'fks-A' != 'fks-B'` at the now-:1133 `data.get('sessionId'), sid` loop, which includes both hellos) and passes in the control. It is not fixed here, per the brief; it needs a controller decision. The other eight tests the report lists (Defect spoof :194 area, Protocol :338, :384, :521, :673/:682, :699, Arrange move, Popout) all passed forced load-first. No other test in the module that I ran or read assumes one announce order (`ArrangeCase.wait_ready` waits for 2 hellos, order-neutral). I did not forced-run the rest of the module's 100+ tests; the `git grep` hit list (design:hello, session_id, `__received`) was read, and every remaining hit takes the last hello or waits on other message types.
8. Constants and import: the shared recorder and pair are needed by both tests in both variants; the alternative is a second inline copy of a 7-line JS recorder plus the pair, with the `product` loops spelled out. Judged the minimal shared form. The brief's text said "at most two small LiveCase methods"; module-level names are a literal departure, disclosed in the report's "Lines, deviations, concerns" section but not marked as a recorded deviation. Minor 1: the controller should record it with the plan "Owns" update the report already drafts.

### Strengths
- The order log makes a lost race or a missing hold fail at the premise with a readable list diff, not as a misleading session count; verified by mutants 3 and 4.
- Independent oracle for the bridge's session (`window.__ready` from the fake's replies), and `hellos[0] == sid` in the load-first reload pins the "session in use" behaviour that mutant 2 breaks.
- Reload now waits for the new document by `performance.timeOrigin` instead of a fixed sleep; hellos are read only after a condition wait.
- The report's sibling finding is correct and reproducible.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
1. tests/test_studio_live.py:13, :30-40: `ANNOUNCE_ORDERS`, `ORDER_RECORDER` and `from itertools import product` go beyond "at most two small LiveCase methods". They are the smallest shared form (two callers each) and are disclosed, but the controller should list them as an accepted deviation and update the plan's R2.T2 "Owns" line accordingly (the report drafts it).
2. Whole patch: 141 gross lines against about 120. Explained and material; no action beyond acknowledging.
3. Open item for the controller, not a defect of this patch: the sibling above remains order-sensitive until a plan change fixes it (only non-hello messages and the last hello need to carry `sid`).

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** Both tests now force and assert each announce order with an independent oracle, and all four mutants fail exactly where the brief and report say (reproduced on a copy outside the repository, sources restored byte-exact). The only findings are disclosed polish items and a confirmed sibling flake that the brief tells the controller to decide.

## Scoped re-review: the third test

### Spec Compliance
- PASS: Patch delta. `diff task-t2-code.patch task-t2-code-r1.patch` shows one changed hunk (the third test, tests/test_studio_live.py:1097-1170 in the frozen file) plus the index line and a line-offset change on the following hunk header. Nothing else differs. The frozen worktree's staged diff hashes to 31a44a44...81dd (matches the r1 patch).
- PASS: Both orders forced, premise first. Body runs `product(ENGINES, ANNOUNCE_ORDERS)`, opens `target=None`, installs ORDER_RECORDER, uses `hold_load` for bridge-ready first and `?late=1` for load first, then `wait_greeted`, and asserts `window.__order == order` (line 1114) before the first click.
- PASS: Oracle is the fake's stamp. `final = page.evaluate('window.__ready')[-1]` (line 1142); `session_id(frame)` is not used in the test. ORDER_RECORDER pushes `e.data.sessionId` of each `design:ready` the fake sends.
- PASS: Bridge-ready first: exactly two hellos, `first == second == final`, and every Studio message is checked against `final` (the `not late` branch covers all indexes).
- PASS: Load first: exactly two hellos, `first != second`, `second == final`, and every message at index > second hello carries `final`. The first hello is the only message excluded, and the messages strictly between the two hellos are also unchecked (none exist in practice; see Minor).
- PASS: Every other BASE assertion is kept: kinds present, no highlight, per-message origin STUDIO and protocolVersion 1, restore-text baseRevision 2 and requestId, exactly one composition update, `errors == []`.
- PASS: Given/When/Then docstring matches the assertions (order recorded, origin/protocol/session per order, kinds, never highlight, one composition update, restore-text fields).
- PASS: The two earlier tests' code is unchanged by the fix round (item 4): the patch-to-patch diff contains no hunk in them.

### Checks run
- Replaced 300 ms wait, does `assertNotIn('design:highlight')` still prove what it claims -> `git show e2098ac:fontkit-studio.html | grep -ci highlight` -> 0. Studio at BASE has no string "highlight" at all. Every sender goes through `sendDesignMessage` (4450) with the literal types hello (4497, 4646), select (4690), update/reset/move/restore-text/roles (4750-4781), mode (6534), detect (4215). No path can send design:highlight, before or after the back click. The assertion is true independent of timing, so the wait was never what proved it; the new wait (back click's design:select, count taken before the click) is only a sync point so the back select is in the record. Ordering: one sender window posting to one target window is delivered in send order (HTML postMessage queues tasks on one task source), and the back handler (5837) sends only that one select (`requestSelection(null)` -> `sendTrackedSelection`) and nothing after it. So no AGENTS.md exception is needed and the replacement is not a finding.
- Mutant 1 (copy outside repo, fontkit-studio.html:4496 `live.sessionId = live.sessionId || newSessionId();`) -> focused test on the copy -> FAIL at test_studio_live.py:1148 `assertNotEqual(first, second)`: 'fks-3966...' == 'fks-3966...' (load first). Baseline on the copy was OK first.
- Mutant 2 (:4644 `live.sessionId = newSessionId();`) -> FAIL, session mismatch (bridge-ready first: fks-64a1... vs fks-86d3...).
- Mutant 3 (hold_load `held.append(route)` -> `route.fulfill(status=204)`) -> FAIL `0 != 1 : the page requested its held image` (premise).
- Extra mutant (mine): sendDesignMessage stamps design:mode with a stale session -> FAIL in both orders (failures=2), so the per-message session check bites after the second hello too.
- Frozen worktree untouched -> sha256 of fontkit-studio.html and tests/test_studio_live.py before and after equal; `git status --short` shows only `M  tests/test_studio_live.py`; staged diff hash still 31a44a44...81dd. Scratch copy removed.

### Strengths
- The session oracle comes from the fake's own design:ready stamp, so the test cannot agree with a wrong Studio by reading Studio's own hello.
- Order premise is asserted before any behaviour, so a harness regression fails as a premise failure rather than a misleading green.
- The three reproduced mutants fail on the intended assertions, one per branch (load first, bridge-ready first, premise).

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- tests/test_studio_live.py:1157 `if not late or index > hello_at[1]` leaves messages between the two hellos unchecked in the load-first branch. Nothing is sent in that window at BASE, so nothing is hidden today; asserting that `hello_at[1] == hello_at[0] + 1` or that those messages carry the first session would pin it. Optional.
- `assertNotIn('design:highlight', kinds)` cannot fail at BASE (Studio has no such sender). It is a BASE assertion the brief says to keep; a note only.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The only delta from the approved patch is the third test, which now forces both announce orders with the premise asserted first, takes its session oracle from the fake's design:ready stamp, and fails under the three reproduced mutants plus one of mine. The fixed wait removal is sound: Studio has no design:highlight sender at all, so the assertion never depended on the wait.
