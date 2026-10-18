### Spec Compliance
- PASS: Req 1 revision check. `Number.isSafeInteger(data.capabilities.roleRevision) && >= 1` sits after `roleDetection === true` in the same `valid` expression, so it takes the existing `!valid` branch (ROLE_UNSUPPORTED, Detect off); `roleStylesheet` is read only after `valid` (fontkit-studio.html 4047, 4066 at HEAD). Revision is not stored; Studio sends revision-1 requests (test 3).
- PASS: Req 2 tolerant reader. One `readRoleWire` + one shape table; `readRoleReply` runs `safeRoleWire(raw, 1 MiB)` on the RAW message first, then the shape, then the unchanged validators on the copy; the four acceptors store only the copy (4045, 4352, 4490, 4527). Unknown keys are dropped at every level (STYLE, VARIANT, IDENTITY both kinds, BINDING, GROUP, CHECK, LOSS, OUTCOME, envelope, state). Echoed roles are strict (`ROLE_WIRE_INPUT`, `strict` + `only:ROLE_PROPS`). The `safeRoleWire` nonfinite line is added (3763).
- PASS: Req 3 and 4 (Detect). Matching = pending set, same requestId, same document as pending and identity. Unreadable (raw, shape or validator failure) sets `ROLE_DETECT_UNREADABLE`, keeps `pending`, cancels the timer (4344-4347, 4353). Non-matching and stale-after-validation stay silent. Timer 8,000 ms (`REQUEST_TIMEOUT_MS`) with identity guard (4296-4299). Matching Detect rejection that fails `validRoleRejection` gives the same string and keeps pending (4390); a valid one is unchanged and does not clear the timer (Revision 2).
- PASS: Req 5 (Apply/Clear). Matching = in-flight op (`!found.late`) and equal documentId; unreadable sets `rolePreview.message`, renders, does not settle, does not call `markRolePreviewUnconfirmed` (4484-4494). Unreadable in-flight rejection shows the same string and returns true (4516). Late, other id and other document stay silent.
- PASS: Req 7 `role_contract.py` (`ROLE_REVISION = 1`, `with_unknown_keys`, `TOLERANT_KINDS`, docstring rewritten). `UNKNOWN_KEY` and a `value` parameter are small additions the marker test needs.
- PASS: Req 8 forced edits are exactly the brief's list and are removals of the tolerated rows plus the M5 rename (see item 8 below). Req 9: W2SB 1 and 2 done, help text changes only the function-list punctuation.
- PASS: the four fake-ready sites got `roleRevision: 1` only (PEER, PEER_DETECT_ONLY, hybrid_page, the forged ready); PEER_LEGACY unchanged.
- PASS: budget. Patch is +548/-39 in the cached stat (about 590 gross), under 640. No markdown, no bridge, no unowned file.
- Note (Minor): brief says "Add PEER_NO_REVISION"; it was not added and the report does not say so. `peer_with_caps` is there and test 2 mutates `caps` in the page. An unused constant would be dead code, so this is harmless.
- CANNOT VERIFY FROM DIFF: Firefox and WebKit. The new frozen-clock tests (6, 7, 8) were only run on chromium; the hosted Firefox canary is advisory and will be their first run there.

### Checks run
- Tracked files stay byte-identical -> `sha256sum` of fontkit-studio.html, tests/role_contract.py, tests/test_studio_roles.py in C:/fks/tsk before and after all my runs -> ac75c7fb..., 66be3850..., 7afa9b44... unchanged; `git status --short` shows only the three staged M files. (Working tree is CRLF, index LF, `i/lf w/crlf`; the SHAs in the report are of the working copy.) All runs used PYTHONDONTWRITEBYTECODE and mutants ran on a copy under the scratchpad.
- Real bridge through Studio with known roles (selectorChecks non-empty), which the new real-bridge test 1 does not cover -> `test_role_adapters` (all) and `test_r2_integration` in C:/fks/tsk, chromium -> Ran 74 tests, OK. So the CHECK/VARIANT/BINDING shapes read the real bridge's second Detect.
- Item 3 (stale valid reply) reproduced -> scratch test `sk_rev_stale.py` (scratchpad, subclasses StudioRoleReplyTests, frozen clock): Apply in flight, Detect pending, Apply receipt with currentPageVersion 1 and page-changed, then a valid Detect reply (pageVersion 0, currentPageVersion 0) -> status stays "Detecting text styles..." after the reply, and after `run_for(8000)` reads "The page did not reply to Detect; this page has not been checked." Confirmed.
- Where Studio stores or exports reply objects -> grep of `roleView`, `rolePreview`, `roleState`, `data.groups/outcomes/roles` and every `JSON.stringify`/`setItem` site (15) -> role state is read only inside the role section; `serializableState` (3145-3147), the code tabs and the overrides file use `live.overrides/tokens/structure` only. Nothing role-related is exported or saved at HEAD. The one raw read left is `data.roleState?.documentId` at 5603 (a comparison, not stored; pre-existing).
- `design:roles-page` -> grep of the html for the type -> no handler at HEAD; nothing to make tolerant here. R2.6S owns it, as the brief says.
- Exact status strings -> grep of the three constants (3745-3747) and `git diff --cached` non-ASCII scan -> strings match Addendum 26 item 4 character for character with ASCII apostrophes; the only non-ASCII added is the existing ellipsis and middle dot in test literals.
- `git diff --cached --check` -> exit 0.
- Hidden skips -> grep `skip` in tests/test_studio_roles.py and `support.ENGINES` -> no new skip; tests loop `ENGINES`, hosted CI runs chromium (and Firefox advisory). Test 9 needs no browser. None would be skipped by hosted CI.
- Paused-clock tests never call `settle` -> grep in the new class -> `settle` and `ready_with` appear only in test 10 (unfrozen); frozen tests use `evaluate`, `wait_for_function`, `run_for`, `quiet` (Playwright-side `wait_for_timeout`).

Mutants I reproduced (copy of the worktree under the scratchpad, one-line source edits, original restored; script `sk_rev_mut.py` and `sk_rev_mut2.py`):

| Mutant | Test | Result |
|---|---|---|
| identity guard `if (roleView.pending !== pending) return;` removed | 7 | FAIL (`Detected` flips) |
| `clearTimeout(roleView.pending.timer)` removed from the unreadable branch | 6 | FAIL (string flips to "did not reply") |
| unreadable Detect rejection no longer cancels the timer | 6 | FAIL |
| `REQUEST_TIMEOUT_MS` -> 9000 | 7 | FAIL at the 8,000 ms step |
| `!found.late &&` removed in `acceptRoleReceipt` | 8 | FAIL (2 failures, time-out phases) |
| `isSafeInteger` -> `isFinite` on roleRevision | 2 | ERROR (1.5 and 2**53 rows) |
| `ROLE_WIRE_INPUT` strict -> false | 10 | ERROR (ready and receipt rows) |
| nonfinite line removed from `safeRoleWire` | 5 | ERROR (nonfinite rows) |
| `readRoleReply` skips `safeRoleWire` | 5 | ERROR (10 subtests) |
| `selectorChecks` shape replaced by `[]` | 4 | ERROR (both plain and unknown-key sessions) |
| **`roleView.rows = data.groups` (raw groups stored) in both acceptor branches** | 4 | **PASS (mutant survives)** |

### Strengths
- The "by construction" design is real: validators run on the copy, acceptors use only `reply`, so unknown keys cannot reach `roleView`/`rolePreview` unless an acceptor is changed by hand.
- Strict echo and the Apply/Clear/Detect "unreadable" paths all leave the request pending or in flight, so the existing timeout and late-receipt paths are reused with no new settlement code.
- The tests use literal expected strings, not the html constants, and real timers or the paused clock are chosen per phase; the frozen-clock boundary (7,999 / 8,000) and the stale-timer scenario (Revision 2 I1) are exact and killed by the guard and 9000 mutants.
- Forced edits to existing tests are removals of rows the new behaviour tolerates, with docstrings updated; no assertion was weakened.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
- tests/test_studio_roles.py (test 4, `test_unknown_keys_are_ignored_outside_echoed_roles_in_the_reply_kinds_and_never_reach_state_or_exports`, and `tolerant_session`): the name and the marker/export assertions promise "never reach state or exports", but nothing in Studio renders or exports raw reply objects, so those assertions cannot fail. My mutant that stores `data.groups` instead of `reply.groups` passes the test. What the test does prove (tolerance: plain and unknown-key messages render identically; two mutants kill it) is real. The brief asked for this test shape and said state is closure-private, so see Plan-mandated; the report should say the "never stored" half rests on construction, not on a test.
- tests/test_studio_roles.py test 6, third run: the "old timer is inert" step is vacuous (the unreadable branch already cancelled that timer). The inertness of a stale timer is proved properly in test 7. Wording only.
- Report omits that PEER_NO_REVISION was not added (see Spec Compliance).

### Plan-mandated (for the owner)
- [Minor, escalate before R2.6S] A valid, matching Detect reply that is stale (`currentPageVersion` below Studio's current page version) is dropped silently, `pending` stays and the timer keeps running, so the status stays "Detecting text styles..." and 8 s later reads "The page did not reply to Detect; this page has not been checked." The page did reply, so "did not reply" is untrue (reproduced above); "this page has not been checked" is true and pressing Detect again is the right action. Addendum 26 item 4 says nothing about a valid-but-stale reply, and today's code (before this task) also dropped it silently. Narrow today (needs a receipt to advance the identity while a Detect is outstanding) but R2.6S's `design:roles-page` will advance the identity more often. Brief requires: "A VALID reply that is stale (`currentPageVersion < current.pageVersion`) stays a silent drop, so 8 s later the status says "did not reply" although the page replied; accepted, say so in the report." The report does say so. Proposed fix (owner decision, new status text): when a validated matching reply is stale, set `pending = null`, `clearTimeout(pending.timer)` and status "The page's reply to Detect was out of date; press Detect text styles again; this page has not been checked." Test: the scratch scenario above (Apply in flight, Detect pending, receipt with currentPageVersion 1, valid reply with currentPageVersion 0) asserting the new text after the reply and the same text after `run_for(9000)`; mutant: leave the timer running (string flips to "did not reply").
- [Minor] No test pins that the real bridge sends exactly the revision-1 key set any more. Before, Studio's exact validators noticed an added bridge key in every real-bridge round trip; now the readers drop it and `violations` "does not compare key sets" (tests/role_contract.py 160-161). `test_role_protocol.py` is read-only for this task. Brief requires: "the docstring sentence at `violations` ... is rewritten to say Studio ignores unknown keys and the bridge sends exactly the revision-1 fields." The sentence is true at HEAD but unenforced; suggest a bridge-side key-set assertion in R2.6B2 or a key-set row in `violations` as its own decision.
- [Minor] Test 4's "never reach state" claim has no oracle (see Minor above and the surviving `data.groups` mutant). Brief requires: "assert the marker is in no `#detectedRoles`/`#rolePreviewOutcomes` text, in none of `self.exports(page)` ... and that the exports are byte-identical to those taken before the reply."
- [Minor] Field lists now exist three times on the Studio side (shape table, `validDetectedReply`/`validRoleReceipt`, and the two copies of the seven `roleState` keys in `acceptRoleReady` and `acceptResetRoleState`). Brief requires: "today's validators UNCHANGED (they stay `exactRoleFields`-exact: they now run on the copy)" and shapes "in the order the validators already list them". A drift fails closed (the message refuses), so it is a maintenance cost, not a defect.

### Assessment
**Task quality:** Approved
**Reasoning:** Every requirement is implemented as written, the exact strings, the 8,000 ms timer with its identity guard, the unreadable-never-settles behaviour and the strict echo all hold, and 10 of 11 mutants I reproduced are killed. The only survivor (raw groups stored) and the stale-reply "did not reply" wording both come from the brief's own text and are listed for the owner, so none counts against the implementer.

---

Checklist 1-8 in one place:
1. Drift: PASS. roleRevision rule, tolerant levels (all of detected, roles-applied, ready.roleState and the reset roleState), strict echo with properties, safeRoleWire-first order and the hostile/oversize/nonfinite/array refusals match Addendum 26 items 1-4, D075, the brief rulings and role_contract.py. roles-page is absent by design. Unknown keys cannot reach state, the JSON export or the overrides file: acceptors store only the copy, and no role data is exported at all at HEAD (grep above).
2. Statuses: PASS. Exact strings; `#roleStatus` for Detect, `#rolePreviewStatus` for Apply/Clear; 8,000 ms (7,999 stays, 8,000 flips); identity guard killed by mutant; late reply ignored (test 7); unreadable receipts and in-flight rejections follow the time-out path and do not settle (test 8, `late` mutant); unreadable matching Detect rejection visible (test 6, `rejnocancel` mutant).
3. Stale reply: see Plan-mandated, first bullet. Brief covered it and accepted it; status is untrue to the user; classified plan-mandated Minor with wording and test.
4. Mutants: 11 reproduced on a scratchpad copy; the frozen worktree is unchanged.
5. Fake versus real: test 1 uses the real Studio and real bridge (ready revision, Detect, Apply, Clear); real-bridge second Detect with selectorChecks is covered by existing `test_role_adapters` and `test_r2_integration`, which I ran (74 OK). Test 4 runs real Studio and its real export code against the legacy fake target with a fake role peer; that is justified because the real bridge never sends extra keys. The export half cannot fail (nothing role-related is exported), so the claim "never exported" is true by absence, not proved by the test.
6. Hidden skips: none.
7. Tests: one killed mutant for each of tests 2, 3 (report), 4 (tolerance only), 5, 6, 7, 8, 10 reproduced or in the report; 1 and 9 per the report (not rerun). Oracles are literals or the contract table. Thens match assertions. The `quiet` waits are used only for absence; frozen tests never call `settle`.
8. Code: only owned places changed; forced test edits are exactly the brief's list and are row removals plus the M5 rename and one added wait; no third copy of a logic beyond the plan-mandated field lists; about 590 lines against 640.

## Scoped re-review (wording follow-up)

### Spec Compliance
- PASS: Test 4 renamed to `test_a_reply_with_unknown_keys_outside_echoed_roles_renders_exactly_like_the_plain_reply`; the docstring claims only tolerance (plain vs unknown-key messages render identically) and labels the export, marker and later-request assertions as regression guards that hold by construction (task-sk-code-r1.patch:545-548). The words "never stored" / "never reach" no longer appear in the test; the one remaining "never reaches state, exports" (patch line 38) is a product comment in fontkit-studio.html, which is byte-identical (sha ac75c7fb...) and out of scope.
- PASS: Test 6 docstring (patch:600) no longer says the old timer does nothing; it says the new Detect renders and keeps "Detected" after 9,000 ms and points to the 8-second test. That test (patch:647-) does prove replaced-timer inertness ("pressed again at 5 s ... answered at 6 s ... first one's timer fires at 8 s").
- PASS: Report's PEER_NO_REVISION note is true. Test 2 builds the no-revision peer inline from `PEER` with a caps dict (`**({} if value is MISSING else {...})`, patch:480-481), covering missing/0/-1/1.5/string/true/null/2**53. `peer_with_caps` (patch:290) serves the higher-revision test. A separate constant would be unused. The brief line ("Add `PEER_NO_REVISION` ... and a peer factory") was not followed literally, but the deviation is recorded and harmless.
- PASS: Fix changed only names, docstrings, comments. `diff task-sk-code.patch task-sk-code-r1.patch` shows exactly 5 hunks:
  1. line 266: index hash line (file blob hash changed, expected);
  2. line 413: hunk header count 404 -> 405 (one more docstring line);
  3. line 542: test 4 `def` line (name);
  4. lines 545-547: test 4 docstring;
  5. line 599: test 6 docstring last line.
  No `+`/`-` line outside those; no assertion added, removed or weakened (all test 4 assertions visible unchanged at patch:549-554).

### Checks run
- Test 4 tolerance mutant still fails -> copied /c/fks/tsk to a skrr scratch dir outside the repo, sed'd fontkit-studio.html:3987 to drop "signatures" from the selectorChecks shape, ran `python -m unittest test_studio_roles.StudioRoleReplyTests -k renders_exactly_like` -> FAILED (errors=2), Playwright timeout waiting for the rendered state.
- Control for that red -> restored the unmutated html in the copy, same command -> Ran 1 test, OK. The failure comes from the mutant, not the copy.
- Frozen worktree untouched -> `git status --short` in /c/fks/tsk shows only the 3 staged files, as before.
- Second mutant (binding shape lists `futureField`) not re-run by me; it exercises the same shape-validation path and the report states it errors. CANNOT VERIFY independently, not needed for the verdict.

### Strengths
- Test 4 now claims only what it proves; the accepted gap (`roleView.rows = data.groups` survives) is named in the docstring and routed to R2.6S rather than overclaimed.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
None.

### Plan-mandated (for the owner)
- Unchanged from the first review: three items routed to R2.6S in w2-carryovers.md.

### Assessment
**Task quality:** Approved
**Reasoning:** The fix touched only test name and docstrings, every assertion is intact, the wording is now accurate, and a tolerance mutant I reproduced on an outside copy still turns test 4 red while the unmutated copy is green.
