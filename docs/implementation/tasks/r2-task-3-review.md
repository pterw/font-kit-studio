# R2.3 independent review

Reviewer appends below; the last line is the end marker.

## Review (Matthew Carter, independent reviewer, 2026-10-16)

Patch sha256 6d4fd656... matches the dispatch; reviewed against the frozen tree C:/fks/t23 (BASE 9a4f164 + patch staged).

### Spec Compliance
- PASS: Whole-request validation precedes any write; atomic rejection; reason mapping matches fact 6b (shape, prototype keys, enum, counts, ID/label lengths -> invalid-message; selector grammar/length, property values, bootstrap5-* -> unsupported-value; bytes -> size-limit; identity -> page-changed; stale base -> revision-conflict; blocked install -> stylesheet-blocked; null URL -> unsupported-value "Unsupported page URL") (fontkit-bridge.js:204-262, 1305-1345). The implementer's rulings (report 59-73) are consistent with the brief; empty `selectors`/`properties` as invalid-message is a reasonable reading of "counts"/"shape".
- PASS: Owned node found only by reference (WeakSet `roleOwned`, `this.roleSheet`), never by id/attribute (1255-1300); install verification is CSSOM-only (attached, enabled, rules equal a reference parse; 1269-1286); CSP header and late meta CSP cases reject `stylesheet-blocked` and keep prior state.
- PASS: Exactly one receipt per accepted apply; suppression only via `roleEpoch` bumped in handleHello (1105) and dropSession (994); detect does not stale a receipt (`roleJobFresh` checks revision, pageVersion, URL, native epoch only). A receipt after a real change is committed with `page-changed` / `outcomes:[]`.
- PASS: Baseline detect disables only the owned sheet around the synchronous `iterator.next()` loop, restore is in `finally` before any `finish()` or yield (1543-1549); the time-budget early exit restores first. Apply-then-Detect on the 5,000 corpus: sizes stay 40px every frame, baseline group 20px.
- PASS: Global reset removes the sheet, clears accepted state, uses a single revision, and puts `roleState` on the legacy reply; target-only reset leaves the sheet (1899-1902).
- PASS: The only change in test_bridge_runtime.py is the capability dictionary; the line-193 edit is reported (now test_role_protocol.py:208) and is exactly the allowed flip.
- PASS: Context items: I-P3 negatives present (all listed forms, with the 2,000 / 9,999 / 200 positives); M-P1 and M-P3 done; I-P2 reported infeasible with evidence; docstrings on the nine existing tests; no harness edit.
- PASS: Addendum 11 core: bridge handler writes (inline style, text, attributes) and native events no longer move the wire pageVersion; native events and render-only revalidation move `roleNative`, which detect `fresh()` and `roleJobFresh` both compare. Verified: inspector edit and reset keep the version; hover during a scan gives page-changed with equal versions.
- FAIL (partial): Addendum 11 "Bridge-originated writes ... never advance pageVersion" is not met for the bridge's own injected font `<link data-fontkit-font>` (Important 1).
- FAIL (partial): Brief and Addendum 11 test "an author DOM or URL change between Detect and Apply is rejected page-changed": the URL half cannot fail (Important 2).

### Checks run
- Focused command minus test_role_detection, in C:/fks/t23 -> Ran 84 tests, OK (53.7 s); APPLY_THEN_DETECT elapsedMs 907.7, 56 frames, heartbeat 106->162.
- test_role_detection in t23 -> 17 tests, 9 failures, every one `AssertionError: 0 not greater than 0` (the T1 currentPageVersion > pageVersion comparisons). FIRST_SCAN 354.8 ms, heartbeat 127->131, input before reply. The controller's claim is confirmed; no other failure.
- `git diff --cached --check` rc=0; `node --check fontkit-bridge.js` rc=0.
- Risk: bridge-originated font link advances wire pageVersion -> scratch test probe_rev23.py (outside the repo): open the role page, route fonts.googleapis.com to a local CSS, send `design:update {fontStylesheet: GOOGLE}` (design:applied), wait for the link sheet to load, then `design:roles-apply` with the ready pageVersion -> `design:rejected page-changed`. Confirmed.
- Risk: cost of the new pre-handler `refreshRolePage()` -> same scratch file, 6,000-rule sheet, `__fontkitBridge.refreshRolePage()` x20 -> 17.7 ms per call. It is called before every non-detect/apply/clear message (fontkit-bridge.js:1050-1051).
- Risk: are the pre-handler flush and apply's `refreshRolePage()` guarded by a test -> mutate_rev23.py (serves a mutated bridge through the open() bridge_source seam, repo untouched), whole test_role_stylesheet module: (a) remove the pre-handler flush at 1051 -> 0 failures; (b) remove `refreshRolePage()` in handleRoleMutation (1319) -> 0 failures; (c) remove the `location.href !== this.roleURL` page-version bump -> only test_exact_2000_character_route... fails, test_author_dom_or_url_change... still passes; (d) control: stamp includes the owned sheet -> 62 failures and 5 errors, so the harness does apply mutations.
- Risk: the 10,001-parent budget test could trip the 2,000 ms time budget on slow CI -> probe2_rev23.py: measuring 10,001 parents takes 0.28-0.31 s, checked 10000 each time (6x headroom).
- Risk: hover-during-scan flake -> ran test_native_hover_during_a_scan... 6 times -> 6/6 OK (3.4-4.0 s each).
- Risk: second copy of the bridge (dist) -> `git ls-files packages/fontkitstudio` has no tracked dist bridge; nothing to keep in sync.
- Docs: grep for roleStylesheet / roles-apply / roles-applied in product docs -> only plan, briefs, handoff and the test host fixture; the patch adds no doc claims (anti-pattern 11 not hit).
- Scratch files: probe_rev23.py, probe2_rev23.py, mutate_rev23.py in the session scratchpad only. Nothing in C:/fks/t23 was touched.

### Strengths
- Validation, canonicalization and install are cleanly ordered: nothing visible changes before the commit point, a failed install removes its candidate node, and the old sheet is replaced only after verification.
- Golden digests are cross-checked by an independent Python FNV in the test; the hostile table covers every limit in the contract with exact reason assertions and rendered, revision and DOM invariants after each case.
- Budget handling is honest: the 10,001st eligible parent gives `budget-exceeded` with checked 10000 and no placeholder losses.
- The undo test compares full outerHTML and every computed property byte for byte after apply, replace, repeat and clear.
- The mutations I re-ran through the bridge_source seam behave as the report describes (the harness bites).

### Issues
#### Critical
(none)

#### Important
1. **Bridge-injected font stylesheet still advances the wire pageVersion** (fontkit-bridge.js:1190-1196 `roleStyleStamp`, 1198-1204 `refreshRolePage`; legacy `ensureFontLink` 2328-2337). The stamp excludes only the owned role sheet. After an inspector `fontStylesheet` write, the `<link data-fontkit-font>` sheet appears in `document.styleSheets` when it loads (asynchronously, after the handler's records were settled), the stamp changes, and the next refresh bumps the version. Measured: an apply carrying Studio's last version is rejected `page-changed` after such an edit (probe above). This is the motivating flow of Addendum 11 ("a Clear queued behind an inspector edit") with the most common inspector edit, a font choice. Global reset has the same effect (`removeAllFontSheets()` changes the stamp after `settleOwnWrites`). The report's limitation names only `fontStatus`. The implementer could have avoided it (exclude `data-fontkit-font` link sheets from the stamp, as the owned sheet is excluded) and no test covers it. Fix: exclude bridge font links from `roleStyleStamp`; add a test: inspector `fontStylesheet` edit (locally fulfilled stylesheet, awaited via the link's `sheet`), then Apply and Clear with the pre-edit version are accepted; one restored mutation.
2. **URL half of the Detect-to-Apply test is vacuous** (tests/test_role_stylesheet.py:959-974). `detected` is taken once (line 966) and the loop runs `dom` first; after that change the page version never matches `detected['pageVersion']` again, so the `url` iteration is rejected whatever the URL logic does. Proven: removing the URL-driven version bump (mutant c) and removing apply's `refreshRolePage()` (mutant b) both leave this test green; fact 5's "call refreshRolePage() before comparing" has no guarding test at all, so a URL change between Detect and Apply could be accepted unnoticed. Fix: take a fresh `detect` before each case (or run the URL case on its own page), then re-run mutants b and c; they must fail this test.
3. **`refreshRolePage()` now runs before every non-role message** (fontkit-bridge.js:1050-1051), including `design:highlight`, `select`, `mode`, `move` and every slider `update`. It serializes the cssText of every readable stylesheet (`roleStyleStamp`): 17.7 ms per call on a 6,000-rule page, roughly 4-6 ms on a Bootstrap-sized sheet, on the target app's main thread, per Studio message. At BASE the stamp was computed only for hello and detect. The flush buys nothing that tests or real events can observe: observer records are delivered in a microtask after each task, so no author record can be pending when a separate message task starts (mutant a, removing it, leaves all 84 tests green). Fix: before the handler call only `this.noteRoleMutations(this.roleObserver.takeRecords())` (or drop the pre-flush; a later refresh sees stamp and URL changes anyway). Keep the post-handler settle.

#### Minor
1. tests/test_role_protocol.py:162-179 and tests/test_role_stylesheet.py:485,495-504: the added reads of the evil child's `log` and the target frame's `__seen` cannot observe a wrongly accepted hostile message. The bridge posts only to its pinned Studio window (`post()`, fontkit-bridge.js:1025-1030), never to `event.source`, so a bypass would reply to the host page, where the pre-existing host-log filter (line 174, and `messages(page, ...)` in the new test) already catches it; `__seen` is also installed after the same-window hostile message was queued. Keep them if wanted, but the report's "made observable" overstates it, and the context premise that replies go to the sender does not hold in this bridge.
2. fontkit-bridge.js:1686 vs 1089: `acknowledge()` settles "before author callbacks" (comment: "author callbacks below are not ours"), but `handleMessage` settles again after the whole handler and drops any record the synchronous `options.onApplied` callback made. The inner call is dead and the comment is false. Remove the inner call or move the outer one ahead of the callback path.
3. tests/test_role_stylesheet.py:990-1004: the hover-during-scan test only asserts "scan still pending" immediately after sending (always true) and then relies on Playwright's hover landing inside a 300-900 ms scan (6/6 locally). On a slow host a late hover completes the scan and the test fails; Addendum 10 asks for a premise that is asserted. Consider a scan-pending guard like R2.T1's.
4. tests/test_role_stylesheet.py:1006-1020: the receipt-staleness pointer event is page-dispatched (`PointerEvent` on `main`). That is adequate for what is under test (the capture listener does not read `isTrusted`; any pointer or focus event moves `roleNative`), and a trusted event is covered for detect. It does not prove a real hover during the frame wait; say so in the docstring.
5. Outcomes: `matched` always equals `checked` (counted only for eligible parents and stopped at the budget), so the pinned inequality is trivially satisfied and, under `budget-exceeded`, `matched` understates the real match count. The brief says to count over eligible parents, so this is a note for R2.S2 (do not read `matched` as selector reach), not a defect.
6. Process: the split-counter tests were written after the code (report 22-24); the substitute evidence is the restored mutations. Disclosed; Important 2 shows the substitute is not complete.
7. Docstring form: `test_the_owned_node_lives_in_head_with_the_documented_markers` has no "when" clause.
8. `measureRoleReceipt.run` has no try/catch; an unexpected throw inside the generator would leave a committed apply without its single receipt. Selectors are validated at apply time, so this is not reachable today.

### Plan-mandated (for the owner)
- (none)

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The stylesheet, validation, receipt and baseline-detect work is sound and the evidence is largely real, but the wire pageVersion still moves for the bridge's own font links (the Addendum 11 flow), the required URL-between-Detect-and-Apply test cannot fail (two real mutants survive), and the new pre-handler refresh adds an unguarded per-message stylesheet serialization.

STATUS: COMPLETE

## Scoped re-review (fix round 1)

Patch task-2.3-code-r1.patch sha256 19aab830... equals the staged tree in C:/fks/t23 (verified with `git diff --cached | sha256sum`). Same rules as before: t23 untouched; mutations only through the open() bridge_source seam (mutate_rev23.py, probe3_rev23.py in the session scratchpad).

### Disposition of the first-round findings
- Important 1 (font link advances wire pageVersion): RESOLVED. `bridgeFontLinks` WeakSet filled in `ensureFontLink` (fontkit-bridge.js:590, 2340) and excluded from `roleStyleStamp` (1196). New `BridgeFontLinkTests` (tests/test_role_stylesheet.py:1043-1069) waits on the real link sheet, then apply and clear with the pre-edit version are accepted, and a global reset that removes the link keeps the version. Mutant fontlink_excl (exclusion removed) fails exactly that test (`'design:rejected' != 'design:roles-applied'`).
- Important 2 (vacuous URL case): RESOLVED. A fresh detect precedes each case (tests/test_role_stylesheet.py:964). Mutant b (apply without `refreshRolePage()`) now fails test_author_dom_or_url_change_... (`roles-applied != rejected page-changed`). Mutant c (no URL-driven bump) now fails it and test_exact_2000_character_route... (2 failures).
- Important 3 (stylesheet serialization per message): RESOLVED. The pre-handler line is now `noteRoleMutations(takeRecords())` (fontkit-bridge.js:1054). Probe: with `roleStyleStamp` wrapped by a counter, design:highlight, select, update and mode produce 0 stamp calls (STAMPS_AFTER_LEGACY_MESSAGES 0). The stamp is still computed by hello, detect, apply/clear and receipt freshness, as intended.
- Minor 1 (inbox reads that cannot fail): RESOLVED. No `__seen` or evil-log read remains in either file; host-log assertions stay. Nit: the docstring at tests/test_role_protocol.py:142 still says "no hostile reply is observable anywhere"; "in the Studio host log" would be accurate.
- Minor 2 (dead inner settle, false comment): RESOLVED in behaviour, see New issue 1 for the test gap. Verified by probe3_rev23.py: an `options.onApplied` that appends a node moves the version 0 -> 1 on r1; with the end-of-handler settle made unconditional it stays 0 -> 0.
- Minor 3 (hover premise): RESOLVED. tests/test_role_stylesheet.py:993-1002 records scan start and first `pointerover` in the frame clock and asserts `hoverAt - scanStart < elapsedMs` with a premise message. A late hover now fails explicitly instead of passing or misleading; it does not remove the timing dependence, which was 6/6 stable earlier.
- Minor 4 (page-dispatched pointer event): RESOLVED. Docstring at 1007-1009 says so.
- Minor 5 (`matched` equals `checked`): unchanged, as accepted last round (a note for R2.S2, not a defect).
- Minor 6 (tests written after code): unchanged, disclosed; not fixable retroactively.
- Minor 7 (docstring "when"): RESOLVED (tests/test_role_stylesheet.py:542).
- Minor 8 (no try/catch in measurement): NOT CHANGED; the decision to leave it is ACCEPTED. The contract's closed `outcomeReason` set ('page-changed', 'budget-exceeded') has no truthful value for an internal error and adding one is out of scope; selectors are validated at apply time, so the throw is unreachable today. If it ever happens Studio sees a missing receipt, not a false one. Nothing to do now.

### Checks run
- Focused command minus test_role_detection in C:/fks/t23: Ran 85 tests, OK (47.2 s); APPLY_THEN_DETECT 756.6 ms, 47 frames, heartbeat 104->151. (test_role_detection not re-run: no detect-path change beyond the stamp exclusion; the writer reports the same 9 version-comparison failures.)
- Mutants through the seam, whole test_role_stylesheet module: a (remove pre-handler `noteRoleMutations(takeRecords())`) -> 1 failure in the first full-module run, none in 5 isolated reruns and none in 36 unmutated runs of that test (see New issue 2); b -> fails the URL test; c -> fails the URL test and the 2,000-route test; fontlink_excl -> fails BridgeFontLinkTests; ack_settle (remove the inner settle in acknowledge) -> 2 failures and 1 error (inspector/font tests: version 1 != 0); ownsettled_flag (end-of-handler settle unconditional) -> 0 failures (survives, New issue 1).
- Stamp-per-message probe and onApplied probe as above.
- `git status` in t23 unchanged (4 staged paths).

### New issues introduced by the fixes
Important
1. **The `ownSettled` ordering has no test** (fontkit-bridge.js:591, 1055, 1093, 1691). The mutant that makes the end-of-handler settle unconditional survives all 85 tests, and the author-callback behaviour it exists for is only proven by my out-of-repo probe. The writer's reason ("no author callback fixture in this task's ownership") does not hold: the callback is an instance option reachable from the test's own frame (`__fontkitBridge.options.onApplied = ...` via `frame.evaluate`, which is test-owned setup in an owned file). Constraints require one restored mutation per new guard. Fix: add a case to SplitPageVersionTests: set an `onApplied` that appends a node, send an inspector update, assert the next detect's `currentPageVersion` is greater than the version before (and that a plain inspector edit without the callback leaves it unchanged, which the existing test covers); run the `ownsettled_flag` mutant and restore. I verified the behaviour is correct as written: every `acknowledge()` call site is the last statement of its handler (1790, 1857, 1886, 1907, 1914, 2045), so no own write follows the flag, and `ownSettled` is reset at the start of every message (1055).

Minor
2. Pre-existing timing race, seen once this round: tests/test_role_stylesheet.py `test_queued_inspector_edit_and_clear_each_settle_with_their_own_authenticated_reply` asserts the apply receipt is stale (`False, 'page-changed', []`) because the inspector edit arrives before the receipt's frame. The two requests are separate messages, so under load the frame can be measured first and the receipt is complete. It failed once in a loaded full-module mutant run and passed 36/36 unmutated runs. Make it deterministic (hold the frame until the edit reply, or accept either stale or complete for the apply receipt and assert the revision sequence and renderings, which are the claim). Not new code, but unlikely to be noticed before CI flakes.

### Assessment
**Task quality:** Needs fixes (one small item)
**Reasoning:** All three first-round Important findings are genuinely fixed and now fail the right mutants, and the Minors are resolved or accepted (Minor 8 accepted). The only blocker is the untested `ownSettled` ordering introduced by the fix; the missing test is a few lines in test-owned setup. The queued-receipt timing race is worth fixing in the same pass.

STATUS: COMPLETE (re-review)

## Scoped re-review (fix round 2)

Patch task-2.3-code-r2.patch sha256 2ba85e75... equals the staged tree in C:/fks/t23 (git diff --cached | sha256sum). t23 untouched; mutations only through the open() bridge_source seam (mutate_t23rr2.py, scratchpad).

### Interdiff r1 -> r2 (index lines ignored)
- fontkit-bridge.js: no change. Everything else outside the items below is unchanged except hunk-offset line numbers in test_role_protocol.py.
- tests/test_role_protocol.py: the docstring of test_detect_authentication... now reads "no hostile reply appears in the Studio host log" (docstring only).
- tests/test_role_stylesheet.py: the queued-receipt assertion (stale OR measured) and one new test; nothing else.

### Item 1: ownSettled test
- New SplitPageVersionTests.test_author_callback_mutation_during_an_acknowledged_edit_still_advances_the_wire_page_version (tests/test_role_stylesheet.py, after the render-only test). It sets `__fontkitBridge.options.onApplied` from the frame, sends a real inspector update, asserts the author node was added, and asserts the next detect reports a newer currentPageVersion than before.
- Candidate: Ran 1 test, OK. Mutant (end-of-handler settle unconditional, `if (ownWrites) this.settleOwnWrites();`) through the seam: `AssertionError: 0 not greater than 0`, 1 failure. Reproduced both results. RESOLVED.

### Item 2: queued edit/clear test
- Now `assertIn((outcomesComplete, outcomeReason, outcomes), (stale, measured))` for the apply receipt, with exact stale and exact measured tuples; the revision sequence (apply 1, edit 2, clear 3), the clear's pageVersion equality, both renderings (24/27 then 16/27) and the two-receipt count are unchanged.
- Determinism: 30/30 OK (3 concurrent loops of 10). Not vacuous: mutant revfresh (revision no longer stales a receipt) still fails this test (the post-edit measurement reports a 27px mismatch that is neither accepted tuple). RESOLVED.
- Residual Minor: the revision-staleness guard (`job.revision === this.revision`, fontkit-bridge.js:1357) is exercised only when the edit message lands before the receipt frame, which is the usual order; in a frame-first run the same mutant would pass, so that mutant kill is order-dependent. The assertions about the sequence and renderings hold either way. Acceptable; no change required.

### Item 3: docstring
- tests/test_role_protocol.py:142-143 now says the reply is absent from the Studio host log, which is what the assertion reads. RESOLVED.

### Item 4: regressions
- Focused command minus test_role_detection in t23: Ran 86 tests, OK (47.0 s). ruff on the three test files: All checks passed. `git diff --cached --check` rc=0. The 9 test_role_detection version-comparison failures are the known R2.T1 noise and were not re-run.

### Issues
Critical: none. Important: none. Minor: the order-dependent revision-guard kill above (no action).

### Verdict
Approved

STATUS: COMPLETE (re-review 2)
