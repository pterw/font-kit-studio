# R2.S2 independent review

## Phase 1 review (2026-10-16)

### Spec Compliance
- PASS: Controls live only inside `#detectedRoles`; per-row checkbox, family, size, weight, line height, tracking and case select all start empty/unchecked with observed values as placeholders; accessible names "<field> for <name> (role-N)" (fontkit-studio.html:4015-4044, test `test_each_detected_row_has_empty_unchecked_draft_controls...`).
- PASS: Apply gating (bridge `roleStylesheet`, authenticated identity with non-null URL, no selected row with `bindingComplete:false`, one valid property, 128-ID flag with the lifetime of `roleView.ids`, 256 KiB UTF-8 request limit), each reason visible in a `data-hint-for` hint (roleApplyState, fontkit-studio.html:4089-4102). Clear is enabled with a null URL. `adapter:'plain'` only (buildRoleRequest, 4070-4087; the request test asserts it).
- PASS: Queue kinds `roles-apply`/`roles-clear`; documentId frozen at the click and re-checked at dispatch (4658-4668; document check at 4663); pageVersion/baseRevision read at dispatch; update-coalescing barrier (4642); import keeps role ops and does not count them (3243-3247); role ops settle only from their own receipt/rejection (`handleReply` guard 4969, `design:applied` never settles a role op); no retry on rejection; validated rejection raises `live.revision`; `scheduleAutoSync` re-armed by `roleQueueIdle()`; late receipt for a timed-out op accepted.
- PASS: Receipt validation matches the brief and the R2.3 pins (Additions 3-4): `revision == baseRevision + 1`, ids equal sent ids in order, FNV-1a32 over UTF-8 and 128 KiB, `0 <= mismatched <= checked <= matched`, `losses[].property` one of the six RoleInput keys, complete outcomes need equal version and non-null equal URL (captured URL from the dispatch-time identity), `page-changed` needs `outcomesComplete:false` and `outcomes:[]`, budget-exceeded invalid on null/changed URL, clear empty with null reason (validRoleReceipt, 4285-4309). The fake peer in `tests/test_studio_roles.py` bumps revision once per accepted op (also the hybrid peer via `fake.bumpRevision`, which exists at tests/fixtures/studio/fake-target.html:270).
- PASS: Only acknowledged state is shown. Click only sets a "Applying..." message; CSS/outcomes/roles change only in `installAcceptedRoles`, called from a valid receipt, a valid ready, or a valid empty `roleState` on the reset-all reply. An invalid ready or a reload marks the preview unconfirmed (`markRolePreviewUnconfirmed`); an op in flight at reload sets `ROLE_DROPPED`, which survives the next ready; the old document's late receipt fails the `documentId` check. Role settlement writes none of `live.changes`/overrides/tokens/structure (only `live.revision` upward).
- PASS: Reset all page edits: inside `#detectedRoles` after the preview block, enabled whenever `live.ready`, `window.confirm` wording follows auto-sync/sync-off, dismiss sends nothing, accept enqueues exactly one untargeted `design:reset`; the half-built untargeted branch is finished (overrides, `live.structure`, saved tokens, `reconcileSavedOverrides`). The ack with an invalid or absent `roleState` keeps the preview and marks it unconfirmed.
- PASS: Preview block: exact heading, focusable `pre` (overflow auto), own `role=status` named "Role preview status", separate from `#roleStatus`; `design:roles-applied` added to `BRIDGE_TYPES`, `design:roles-page` left out and tested to change nothing; `restore-text` fallback untouched (explicit role branch placed before the chain).
- PASS: Ownership: only `fontkit-studio.html`, `tests/test_studio_roles.py`, `tests/test_r2_integration.py` changed; existing fullscreen tests unchanged except the brief-allowed `print`/absolute-path screenshot removals (r2_integration diff) and Given/When/Then docstrings.
- PASS: Audit items I-S1..I-S3, I-I1, M-I1, M-S1..M-S3 are done (recorded-message assertions, multi-byte limits, 1 MiB and 1 MiB + 1 built from valid fields, selector negatives and positives, the always-true `assertIn('Body', ...)` removed, one subtest per hostile shape).
- FAIL (Important, see I1 and I2): two guards the brief names have no killing test: a receipt must not lower the page generation (advanceRoleIdentity, 4268-4273) and a late legacy reply must not settle a timed-out role op (handleLateReply, 4956).
- FAIL (Minor, see m1): the rounding of typed fractions (roleNumber, 3878-3883) has no test.
- CANNOT VERIFY FROM DIFF: phase 2 real-bridge cases are out of scope per the dispatch.

### Interpretations judged (report "Interpretations to confirm")
1. Removed-roles sentence as its own element (`#rolePreviewRemoved`, aria-live, inside the preview group): ACCEPT. The brief says both "status names accepted roles the new set removes" and "a valid stale receipt ... shows exactly `Preview applied; page changed before checks finished`"; a separate adjacent live region satisfies both. Owner may confirm (see Plan-mandated).
2. Json tab and its Download show `live.revision`, +1 after a role op: ACCEPT, owner to confirm. `liveJson()` reads `live.revision` (fontkit-studio.html:6291-6292); a role op must raise it (the next `baseRevision`). The only way to keep the tab byte-identical is to change legacy `liveJson` to `canonicalRevision`, which the brief's "exports and legacy behavior are unchanged" argues against. The test asserts exactly +1 and every other byte equal, and the composition JSON export (`canonicalRevision`), CSS/HTML tabs and Sync body fully identical. Verified at `test_code_download_export_and_the_synced_file_are_byte_identical_before_and_after_apply`.
3. Invalid typed fields block Apply only for selected rows: ACCEPT, owner to confirm. The brief's "A typed but invalid field, or an enabled invalid row beside valid ones, disables Apply" can be read either way; an unselected row is not in the request, so nothing is dropped silently. Gap: the flagged field of an unselected row gets `aria-invalid` and a red border but no visible reason text (Minor m4).
4. Rounding to the contract decimals: ACCEPT. It matches `canonicalLiveValue` and the bridge (`fontkit-bridge.js:226` rounds fontSize to 2 dp itself; receipts must echo rounded values, which Studio validates). No functional risk. Untested (mutant survives, Minor m1).
5. Accepted roles whose issued id is not in the current rows are dropped by Apply and named afterwards: ACCEPT; it is what the brief says (replace the whole set, name the removed). Owner may want a pre-click warning; none is in the brief.

### Checks run
- Focused gate 1 (frozen C:/fks/ts2, Chromium, FKS_REQUIRE_FIXTURES=1): `python -m unittest test_studio_roles test_r2_integration test_studio_import_link test_studio_dead_controls test_support` -> `Ran 167 tests ... OK`, exit 0 (log s2arev-gate1.log). Output carries 2 `ResourceWarning: unclosed file` lines from tests/test_studio_roles.py:1776.
- Focused gate 2 (the second command in the report) -> `Ran 46 tests ... OK`, exit 0 (s2arev-gate2.log).
- Landing risk: patch applied to a `git archive HEAD` copy (5041b84, R2.3 bridge) in scratch `s2arev-head` -> applies cleanly; `test_r2_integration` -> 1 failure: `test_current_bridge_keeps_detect_and_says_why_apply_and_clear_are_off` (real bridge now advertises `roleStylesheet`, fontkit-bridge.js:1130). The other six pass.
- Mutants run on a scratch copy (s2arev-copy; the repo and C:/fks/ts2 were never edited; each run restored byte-exact, sha256 6af535062... verified after every run):
  - receipt `revision == base+1` removed -> killed (many shapes of the hostile-receipt test fail).
  - dispatch-time documentId check removed -> killed (`test_a_reload_while_a_role_op_is_queued...` errors).
  - preview CSS written with `innerHTML` -> killed (`test_literal_markup_in_names_css_and_details...`).
  - receipt CSS limit 128 KiB -> 128 KiB + 1 -> killed (`test_a_receipt_css_at_128_kib...`).
  - ready newer-revision guard removed -> killed (`test_an_older_ready_cannot_replace...`).
  - reset-all `live.structure = savedStructureFrom(...)` removed -> killed (`test_reset_all_empties_overrides_tokens_and_saved_order...`).
  - SURVIVED: `roleNumber` without `roundTo` (5 tests OK); `handleLateReply` role guard `|| isRoleOp(op)` removed (whole `test_studio_roles`, 54 tests OK); `advanceRoleIdentity` monotonic guard `pageVersion < current.pageVersion` removed (54 tests OK).
  So 6 of 9 sampled mutants are killed (at least 3 were required).
  Reproduced from the report's own list (same line, scratch copy): receipt revision, dispatch-document check, text-only CSS, ready revision guard (killed as claimed). The implementer's scratch `mut.py` shows its "legacy-reply-settles-role-op" mutant removes the in-flight guard at `handleReply` (line 4969), not the late branch at `handleLateReply` (line 4956); so the report's category is true for the in-flight case only and the late branch is uncovered (I2). Its list has no mutant for `advanceRoleIdentity` (I1) or for rounding (m1).
- Absence waits: `quiet()` 300 ms (no resend, nothing sent yet) and 450 ms x2 in the auto-sync test; `AUTO_SYNC_MS` is 400 (fontkit-studio.html:3352), so 450 ms (900 ms in total) outlasts a wrongly armed timer. Allowed by AGENTS.md Test Quality ("short waits that prove something did not happen"). Justified, thin margin on the 450/400 coupling.
- polling=50: removed in a scratch copy of the test file and ran the Queue, LegacyInterplay and ResetAll classes (19 tests) -> 1 `Frame.wait_for_function: Timeout 30000ms exceeded`. The deviation is justified. The copy's test file was restored from C:/fks/ts2 (sha256 verified equal).
- Hostile coverage read in the diff: receipts and rejections with wrong requestId/operation/revision/document/version/route/credentials/script URL/digest/algorithm/CSS size/role ids/outcomes/losses; wrong session, protocol, Studio-window source and nested frame; ready snapshots (digest, algorithm, extra keys, non-RoleInputs, 201-char document, URLs); reset-all reply roleState (absent, extra key, non-empty, other document, digest, foreign URL, older revision). Markup in role name, CSS (`</pre>`), rejection detail renders as text only; detail capped at 200 characters.

### Strengths
- Acknowledged-state discipline is enforced in one function (`installAcceptedRoles`) and its three callers are each validated before they reach it; hostile tests use a valid fence to prove the hostile message changed nothing (observable, not a mock check).
- Test digest helper is written independently and pinned against the published FNV-1a vectors, so receipts are not checked against Studio's own function.
- Size boundaries are built from valid fields at exactly 1 MiB, 1 MiB + 1, 128 KiB, 128 KiB + 1 and 256 KiB in UTF-8 bytes.
- Reset-all mutation set (structure, saved order, banner) is tested against a real arrange fixture, not only the role state.

### Issues
#### Critical
None.

#### Important
- I1. Untested guard: a receipt must never lower a newer page generation. `advanceRoleIdentity` (fontkit-studio.html:4268-4273, `pageVersion < current.pageVersion`) implements the brief's "Nothing downgrades a newer accepted revision or page generation", yet removing the guard leaves all 54 tests in `test_studio_roles` passing. Two reachable routes: (a) Detect assigns `roleView.identity` from its reply (acceptDetectedRoles, line 4198) and may run beside a queued Apply, so a Detect reply at version N+1 followed by the Apply receipt at `currentPageVersion` N must leave the next request at N+1; (b) a timed-out op's late receipt runs `advanceRoleIdentity` before the `revision > rolePreview.revision` check, so Apply1 times out, Apply3's receipt reports version 3, then Apply1's late receipt reports version 1 and must not lower it. Add one of them.
- I2. Untested guard: a late legacy reply must not settle a timed-out role op. `handleLateReply` (`if (!op || isRoleOp(op)) return;`, fontkit-studio.html:4956) has no killing test; removing `|| isRoleOp(op)` leaves the module green. The brief says "operation matching both ways" and "a `design:applied` never settles a role op". Existing tests cover only the in-flight case (`handleReply`, 4969; the report's "legacy reply settling a role op" mutant is that one). Add: Apply times out, a `design:applied` carrying its requestId arrives, the later valid receipt must still be accepted.

#### Minor
- m1. Rounding of typed fractions (`roleNumber`, 12.345 -> 12.35, 0.12345 -> 0.1235) is not asserted anywhere: the bounds test only checks enabled/disabled and the request test uses values that need no rounding. Mutant survives. Harmless functionally (bridge rounds and echoes rounded), but add one assertion on the sent request.
- m2. tests/test_studio_roles.py:1776 (inside `exports`, 1768) `open(download.value.path(), 'rb').read()` never closes the file: two `ResourceWarning` lines in the focused output (not pristine) and a leaked handle on Windows. Use `Path(...).read_bytes()`.
- m3. `exports()` clicks the CSS, HTML, Json tabs in that order and then Download, so only the Json download is compared. The report's "Download of CSS ... fully identical" and the test docstring ("the downloaded bytes") overstate it. CSS output is still covered by the tab text and the Sync body.
- m4. A typed-invalid field in an unselected row is only marked `aria-invalid` with a red border; no visible or described reason says why (renderRoleControls, fontkit-studio.html:4103-4110, aria-invalid at 4107). The reason appears only once the row is ticked.
- m5. A late receipt ignored as older sets `rolePreview.message = "A late acknowledgement for an older preview was ignored."` (fontkit-studio.html:4324), replacing the status that describes the still-shown preview. The CSS is correctly unchanged; only the status text loses the counts.
- m6. Read from code (installAcceptedRoles 3921-3927, acceptRoleReady 3940-3963): after a reload the new ready installs the empty state while `rolePreview.roles` still holds the old document's roles, so the note `Removed from the preview: Body.` appears. It is true in effect but reads as a Studio action. The reload test asserts status and CSS but not this element.
- m7. No receipt-specific wrong-origin case (the origin check is the shared `acceptBridgeMessage`, covered for detect by the S1 navigated-window test); wrong source, session and protocol are covered for receipts.

### Plan-mandated (for the owner)
- [Important] The phase 1 patch cannot land green on 5041b84. `test_current_bridge_keeps_detect_and_says_why_apply_and_clear_are_off` (tests/test_r2_integration.py:176) asserts the real bridge does not advertise `roleStylesheet`; R2.3 now does (fontkit-bridge.js:1130), verified by applying the patch to a HEAD archive (1 failure, assertion at tests/test_r2_integration.py:188). The implementer followed the brief and flagged the conversion in its Handoff; phase 2 (or the integration commit) must convert or drop it. Brief requires: "real Studio with the R2.2 bridge showing Apply/Clear disabled with the reason while Detect still works."
- [Minor] Json tab and Download `revision` rises by one after a role op (`liveJson`, fontkit-studio.html:6291-6292, reads `live.revision`). Brief requires both: "assert those outputs are byte-identical before and after Apply" and "it raises `live.revision` only upward". Owner decision: accept the exception (current), or change `liveJson` to the acknowledged-legacy `canonicalRevision` (legacy change).
- [Minor] Brief wording is self-conflicting for removed roles ("its status names accepted roles the new set removes" vs "shows exactly `Preview applied; page changed before checks finished`"); the separate `#rolePreviewRemoved` element is the implementer's resolution. Confirm.
- [Minor] "A typed but invalid field ... disables Apply" does not say whether it applies to unselected rows; implementation blocks only selected rows. Confirm. Also confirm that no pre-Apply warning is wanted for accepted roles not in the current rows (named only after Apply).

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The implementation matches the brief and contract, shows only acknowledged state, keeps previews out of exports and sync, and both focused gates reproduce green (167 and 46 tests). Two brief-named guards (page generation never downgraded; late legacy reply never settles a timed-out role op) are survivable mutants, so the "every guard has a killing test" claim fails for them; add those two tests and close the small ResourceWarning before the patch is integrated, and convert the R2.2-bridge gating test when it lands on R2.3.

**Verdict:** Approved with fixes (no Critical; two Important test gaps, I1 and I2, to add before integration; the Plan-mandated landing failure is the controller's to convert).

STATUS: COMPLETE

## Scoped re-review (fix round 1)

Scope: my findings I1, I2, m1-m7 and regressions, against `task-s2a-code-r1.patch`. C:/fks/ts2 was verified identical to that patch (`git diff 90e8a87` of the three files is byte-equal to it) and was not edited. The interdiff was read from a scratch copy of the previous tree against the frozen tree: 8 source hunks in `fontkit-studio.html`, test additions only in `tests/test_studio_roles.py`, `tests/test_r2_integration.py` unchanged.

### Checks run
- Focused gate 1 (Chromium, FKS_REQUIRE_FIXTURES=1): `Ran 172 tests ... OK`, exit 0, 0 ResourceWarning lines (s2arr1-gate1.log). Focused gate 2: `Ran 46 tests ... OK`, exit 0 (s2arr1-gate2.log).
- Mutants on a fresh scratch copy (s2arr1-copy), foreground, restored byte-exact with the sha256 checked after each (b99b94eb1244...). All eight KILLED, each by the intended test:
  - I1: `advanceRoleIdentity` guard `pageVersion < current.pageVersion` removed -> `test_a_receipt_never_lowers_a_newer_page_generation_learned_from_a_detect` fails.
  - I2: `|| isRoleOp(op)` removed from `handleLateReply` -> `test_a_late_design_applied_with_a_timed_out_role_ops_id_does_not_settle_it` fails.
  - m1: `roundTo` dropped in `roleNumber` -> `test_typed_fractions_are_rounded_to_the_contract_decimals_in_the_sent_request` fails.
  - m7: origin check in `acceptBridgeMessage` (line 4402) removed -> `test_a_receipt_from_a_foreign_origin_while_the_op_is_in_flight_changes_nothing` fails. Run unmutated 4 more times: 4 of 4 OK, so no flake seen.
  - m5: `${rolePreview.shown} ...` reverted to the bare sentence -> the ignored-late-receipt status/counts test fails.
  - m6: `announce &&` removed -> the reload test fails on `#rolePreviewRemoved`.
  - m4: the `if (!note) return;` guard removed -> `test_bounded_rows_collection_and_utf8_request_limit_are_visible` fails (the crash on rows without an issued id is covered); note forced hidden -> the row-blocking test fails.
- Regression reading of the source hunks: `shown` is set only in `installAcceptedRoles`, so repeated ignored late receipts do not stack the sentence; the reset-all path still announces removals (`announce` defaults true; its test still passes); the per-row note reads `draft` only when `bad.length` is non-empty, so a row with no draft cannot throw; `aria-describedby` is removed when the field is fixed (asserted).

### Findings
- I1: resolved (route a, reachable via the Detect reply that assigns `roleView.identity`; mutant killed).
- I2: resolved (late `design:applied` with the timed-out op's id changes nothing, and the op's own receipt still renders; mutant killed).
- m1: resolved. m2: resolved (0 ResourceWarning lines; `Path.read_bytes`). m3: resolved (every tab's Download is compared; only the Json one is aligned on the single revision number; docstrings corrected).
- m4: resolved. Per-row note `#roleNote-<id>` names row and field, says the row is not selected, and is linked by `aria-describedby`; the 128-row crash is guarded and tested.
- m5: resolved (status keeps counts; CSS and outcomes unchanged). m6: resolved (a ready names nothing as removed; reset-all still does). m7: resolved (foreign-origin receipt with the right session and request id is ignored).
- Test cost/shape: the two new 8 s tests (I2, m5) wait for the real request timeout through condition waits (`wait_for_function`, 20 s cap), no fixed sleeps. Acceptable. The m7 test polls for the held image route in a Python loop of `wait_for_timeout(50)` (cap 10 s); that is a condition poll, not a fixed sleep, and it is the only way to detect a route being held. Acceptable.
- No new Critical, Important or Minor findings. The owner's decisions on the three plan-mandated interpretation items and on keeping the R2.2 gating test for phase 2 are taken as given; the earlier Plan-mandated landing note (that test fails on a R2.3 base) stands until phase 2 converts it.

**Verdict:** Approved (fix round 1 closes I1, I2, m1-m7 with no regression).

STATUS: COMPLETE (re-review)

## Phase 2 review (2026-10-16)

### Spec Compliance
Scope: phase 2 only. The delta was taken as the staged tree in C:/fks/ts2b against a 4d3b0bb archive with `task-s2a-code-r1.patch` applied (ignoring CR); `git diff --cached 4d3b0bb` is byte-equal to `task-s2b-code.patch`. Delta: Studio +35 lines (`fontkit-studio.html`), `tests/test_studio_roles.py` +123 lines of diff, `tests/test_r2_integration.py` the real-bridge class. ts2b was never edited (hashes of the three files compared before and after).

- PASS: `winningSelector` is null or bounded text: `roleLossSelector` (fontkit-studio.html, validRoleOutcome) accepts a string of 1-2,000 characters with no U+0000-U+001F or U+007F; the role selector grammar is no longer applied. It is rendered through `textContent` only (`line()` builds a `<p>` with `node.textContent`). Matches Addendum 13 / brief Additions 1.2 and the R2.5 Handoff.
- PASS: Outcome lines show `matched N, checked M eligible text elements, mismatched K`; "no eligible text found for this role" only when `checked` is 0; `matched > checked` on a complete outcome adds "N matched elements have no rendered text and were not measured" (not a failure); `complete:false` shows "(incomplete)". Every reason reads in plain words, using exactly the wording in the R2.5 Handoff (`ROLE_LOSS_TEXT`).
- PASS: R2.2 gating test dropped, as the brief's Additions 3 and the controller's context allow (R2.3 advertises `roleStylesheet`, fontkit-bridge.js:1130; no hook serves the real bridge without it). Gating is still proven: phase 1's fake-peer `test_a_bridge_with_detection_only_keeps_detect_and_explains_why_apply_and_clear_are_off` (unchanged, passes) asserts Apply and Clear disabled with the visible `This bridge does not support role preview.` hint while Detect works and only hello/detect are sent.
- PASS: The 12 real-bridge tests cover every phase 2 item in the brief: Apply by keystrokes (Body 24px, `ordinary.body` 16px, markup unchanged) and Clear restoring markup and all computed styles; replace/repeat/idempotent clear and raw `roles: []` (revisions 1-6, each +1); post-commit rerender (stale status, then an inspector edit and Clear settle); target-only reset keeps the preview; reset-all dismissed (no untargeted reset) and accepted (exactly one, preview and edit cleared, no banner, Apply works again); inspector edit surviving with a counted mismatch whose reason is read from the receipt; CSP `stylesheet-blocked` keeps the previous preview; initial 2,001-character URL (Apply disabled with the reason, Clear works with a null-URL receipt) and valid-to-unsupported; Detect after Apply reads the 16px baseline; ready after re-hello; fullscreen with a populated preview (fluid and fixed 1440, height above 500, panel inert, observations equal after Escape); the author `.card p` winner shown as text.
- PASS: Each new test has a Given/When/Then docstring. Changed existing assertions (counts wording, reason text, rows `loss selector body` removed and four rows added: over 2,000 characters, line break, NUL, non-text) are the ones the new wording and rule force.
- Owner decisions in Additions after dispatch 1 are respected (Json tab revision +1, removed-roles element, selected-row blocking): untouched by this delta.

### Checks run
- Focused command 1 in C:/fks/ts2b (Chromium, FKS_REQUIRE_FIXTURES=1): `Ran 184 tests ... OK`, exit 0, 0 warning lines (s2brev-gate1.log). Command 2: `Ran 46 tests ... OK`, exit 0 (s2brev-gate2.log).
- Mutants on a scratch copy (s2brev-copy; byte-exact restore asserted by hash after each; ts2b untouched). All five killed:
  - role selector grammar reinstated for `winningSelector` -> killed by the fake-peer plain-words test (error) and the real `.card p` test (fail).
  - 2,000-character limit removed -> killed by the hostile-receipt table (`loss selector over 2000...` shape and cascade).
  - control-character test removed -> killed by the hostile-receipt table (line break / NUL shapes).
  - `matched` rendered as `checked` -> NOT killed by the apply test or the `.card p` test (matched equals checked there; first attempt survived), killed by `test_complete_zero_match_stale_budget_and_clear_receipts_render_their_own_state` (matched 5 vs checked 3). Fine, because the dedicated test carries it.
  - author-rule text without the selector -> killed by the fake-peer test and the real `.card p` test.
  The report's fifth mutant (panel placement for fullscreen) was not rerun.
- Export check with the real bridge (probe s2brev_probe.py, outside the repo): inspector edit, Apply 24px, then CSS, HTML, JSON tabs and the JSON export before and after: no `font-size: 24px`, no receipt `cssHash` in any output, CSS/HTML/export byte-equal -> OK. So exports are clean with the real bridge, but see Minor 2: no repo test pins it.
- Overflow probe: a 2,000-character `winningSelector` at 390 px -> `#detectedRoles` and the page do not overflow (li has overflow-wrap:anywhere) -> OK.
- Hostile probe: a winning selector with U+0085 (C1 control) is accepted (see Minor 1).
- Hostile coverage in repo: selector with markup (`<img ... onerror>`) and exactly 2,000 characters render as literal text (no `img`, `body[data-bad]` unset); empty, over-length, line break, NUL, non-text are rejected with the receipt left in flight.
- Not vacuous: real tests assert computed styles in the target frame (24px/16px/20px/27px), markup `outerHTML` equality, and Studio-rendered text derived from the receipt (reason text mapped from `loss.reason`, not hard-coded). Receipt arrival is awaited through an init-script listener that runs before Studio's handler, and the rendering check happens after that dispatch completes. The 300 ms `quiet()` in the reset-all test is an absence proof (allowed).

### Strengths
- Real-bridge tests assert the page, not only messages: Clear returns every computed style and the author markup, the winning `.card p` rule really keeps 20px, reset-all really restores both paragraphs.
- Revision +1 per accepted op is confirmed against the real bridge, including repeated Clear and a raw empty `roles: []`.
- `matched` versus `checked` is pinned with three cases (0/0, 4/0, 5/3) so the "not a failure" wording cannot silently regress.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
- 1. `roleLossSelector` rejects only U+0000-U+001F and U+007F (fontkit-studio.html, just above `validRoleOutcome`). The brief says "no control characters"; C1 controls (U+0080-U+009F) pass (probed with U+0085, receipt accepted). Rendering is textContent, so no injection, and the bridge never emits them; widen to `[\u0000-\u001f\u007f-\u009f]` and add a table row if the owner wants the literal rule.
- 2. No repo test pins "exports, saved overrides and Sync never contain the preview CSS" with the real bridge (phase 1 pins it with the legacy fake only). My probe passes, so this is a coverage gap, not a defect; one extra test (probe shape above) closes it.
- 3. `test_replace_repeat_and_clear_each_raise_the_revision_by_one...` asserts receipts (revision, operation, empty fields) but not the rendered result of the replace (25px) or that the repeated Apply leaves the page unchanged; the brief lists "replace, repeat and idempotent clear". Add a computed-size assertion after each step.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** Phase 2 meets the brief, the Addendum 13 rules and the R2.5 Handoff; the real-bridge tests assert rendered page and receipt-derived text, the five mutants I ran are killed by intended tests, both focused gates pass (184 and 46), and exports are clean with the real bridge. Only three optional Minor items remain.

**Verdict:** Approved

STATUS: COMPLETE

## Scoped re-review (phase 2 fix round 1)

Interdiff read: `task-s2b-code.patch` (my reviewed tree) to `task-s2b-code-r1.patch`; C:/fks/ts2b equals the r1 patch (`git diff --cached 4d3b0bb` byte-equal) and was not edited (hashes of the three files compared after all runs). The patch touches only `fontkit-studio.html`, `tests/test_r2_integration.py`, `tests/test_studio_roles.py`.

### Checks run
- Focused command 1 (Chromium, FKS_REQUIRE_FIXTURES=1): `Ran 185 tests ... OK`, exit 0, 0 warning lines (s2brr1-gate1.log). Command 2: `Ran 46 tests ... OK`, exit 0 (s2brr1-gate2.log).
- 1. `roleLossSelector` now rejects `[ --  ]`; three hostile-table rows added (C1 U+0085, U+2028, U+2029). Mutant (class narrowed back to ` -`) on a scratch copy -> killed: the hostile test's failing subtests include exactly `loss selector with a C1 control`, `... a line separator`, `... a paragraph separator`. Byte-exact restore asserted by hash.
- 2. `test_role_css_never_reaches_the_code_tabs_downloads_exports_or_the_synced_file` (real bridge, Sync route): compares CSS/HTML/Json tabs, each tab's Download, the JSON export (`aligned(after) == aligned(before)`, only the Json tab and its download aligned on the revision number) and the Sync body, asserts the Json revision is exactly +1, and asserts no output contains `font-size: 24px`, the receipt's digest or `data-design-role`. Reproduced once: mutant appending `rolePreview.css` to `liveCss()` (Css tab, download and Sync body) -> the test fails on the byte comparison (`{'Css': '[data-design-role="Body"] {...'} != {'Css': '/* Font Kit Studio live overrides ...'}`). Restored, hash verified.
- 3. The replace/repeat test now asserts the target's computed size after each Apply (24, 25, 25px, with the ordinary paragraph at 16px) and 16px after each Clear. Mutant in a scratch copy of the bridge (`installRoleSheet` rewrites `25px` to `24px` on the install path) -> the test errors. Restored, hash verified.
- 4. `exports()` and `sync_body()` moved byte-for-byte into `StudioRoleCase`; the old inner `sync_body` closure and the class-local `exports()` are removed, and the phase 1 byte-identical test calls the shared methods with the same logic. Grep: these are the only definitions in tests/ and the only callers are that test and the new one. The 185-test run (up from 184 by the one new test) shows no other test changed behaviour.
- 5. `fontkit-bridge.js` in C:/fks/ts2b: `git diff 4d3b0bb -- fontkit-bridge.js` is empty and `git hash-object` equals `git rev-parse 4d3b0bb:fontkit-bridge.js` (293d476d...). Not in the patch.

### Findings
- Minor 1 (C1/separator characters), Minor 2 (real-bridge export isolation) and Minor 3 (rendered sizes after replace/repeat) from the first phase 2 review are all resolved. No new findings.

**Verdict:** Approved

STATUS: COMPLETE (re-review)
