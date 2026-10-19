# R2.SK brief: Studio reads the role revision, reads replies tolerantly and says when it cannot

Plan: `docs/plans/2026-10-03-r2-engine.md` Addendum 25 (slice R2.SK, wave W1) and Addendum 26 items 1-5 (D075), Studio
side; the Studio-side W2 review Minors. BASE `bd20e43b912bee1431fc74d3334c8a6bd4ac55e7` (every source line number below was checked at BASE; still re-find
each by name). Worktree `C:/fks/tsk`, task id `sk`. Line budget: about 640 gross lines (about 120 in
`fontkit-studio.html`, about 520 in tests); explain any excess over 700 in the report.

## Why

- Studio cannot tell which role contract a bridge implements, and a bridge with one more reply field leaves Studio on
  "Detecting text styles…" forever. `exactRoleFields` (fontkit-studio.html 3751) refuses an object with any extra or
  missing key; `validDetectedReply` (4247) and `acceptDetectedRoles` (4285) return without a word on a bad Detect reply;
  Detect arms no timer; `validRoleReceipt` (4394) and `acceptRoleReceipt` (4419) drop a bad receipt silently, so
  Apply and Clear fall to `REQUEST_TIMEOUT_MS` (3351; the timer at 4799) and the status reads "No response to apply".
- `acceptRoleReady` (3993) accepts any bridge that says `roleDetection: true`; `data.revision` there is the bridge's
  MUTATION revision, a different thing from the new `capabilities.roleRevision` (the role CONTRACT revision). Never mix them.

## Owned files (exact; matches the Addendum 25 row)

- `fontkit-studio.html`: the role section only (3743-4470 area), the `design:ready` case's call into it (5531) and the
  `acceptResetRoleState` use of `roleState` (4453). No legacy-op code.
- `tests/test_studio_roles.py`: ONE new class `StudioRoleReplyTests(StudioRoleCase)` after `StudioContractTableTests`;
  plus the forced edits listed under Requirement 8 (named in the report as characterization changes).
- `tests/role_contract.py`: the revision row, the unknown-key builder and the tolerant-reply cases (Requirement 7);
  the docstring sentence at `violations` ("It does not compare key sets: both sides already validate exact field lists")
  is rewritten to say Studio ignores unknown keys and the bridge sends exactly the revision-1 fields.
- `capabilities` objects of fake `design:ready` messages, adding `roleRevision: 1` ONLY. The complete list at 362ffd11
  (`git grep -n roleDetection -- tests`, minus the real-bridge reads): `tests/test_studio_roles.py` 92 (`PEER`),
  93 (`PEER_DETECT_ONLY`), 112 (`hybrid_page`), 414 (the forged ready in
  `test_navigated_target_window_cannot_use_its_new_origin_as_role_authority`; it must stay refused for its own reason).
  `PEER_LEGACY` (`{}`) stays unchanged. No other test module builds a fake role capability (verified at BASE: the other
  matches read the real bridge's `ready`, which already sends `roleRevision: 1`). Re-run the grep at BASE and list any
  new site in the report.

Read-only: everything else, including `fontkit-bridge.js`, `tests/test_role_protocol.py`, `tests/test_bridge_runtime.py`
and `tests/fixtures/`.

## Read first

`constraints.md` (all); Addendum 26 and Messages (plan 798-856); `tests/role_contract.py` 76-92 and 147-160;
`tests/test_studio_roles.py` 82-130 (peers), 116-345 (`StudioRoleCase` helpers `open`, `pending`, `reply`, `receipt`,
`send`, `ready_with`, `exports`), 424-458 (ready test), 530-604 (hostile Detect), 1030-1128 (hostile receipts),
1519-1550 (timeout tests), 1707-1735 (reset state); `fontkit-studio.html` 3743-3870, 3993-4025, 4228-4320, 4360-4470,
4780-4815, 5527-5565.

## Requirements

Strings are exact (ASCII apostrophe; the ellipsis in "Detecting text styles…" is the existing U+2026).

1. **Revision check (Addendum 26 item 1).** In `acceptRoleReady`, the `valid` expression gains one more conjunct, after
   `roleDetection === true`: `Number.isSafeInteger(data.capabilities.roleRevision) && data.capabilities.roleRevision >= 1`.
   Missing, `0`, negative, fractional, a string, `true`, `null` and `2**53` all fail it. A failure takes the SAME path as
   any other invalid ready (the existing `!valid` branch): `roleView.status = ROLE_UNSUPPORTED`, Detect/Apply/Clear off,
   the shown preview unconfirmed or (foreign origin) cleared. No new status text. Any valid revision, `1`, `2` or
   `2**53 - 1`, is accepted and not stored: revision 1 defines no optional request field, so Studio sends revision-1
   requests to every bridge (Addendum 26 item 2, nothing to build). `roleStylesheet` is still read only after the
   revision check passes. Oracle: Addendum 26 item 1 and the literal `ROLE_UNSUPPORTED`. Observed: `#roleStatus`
   text, `#detectTextStyles` disabled, the peer received only `design:hello`.
2. **One tolerant reader, applied before the existing validators.** Add one helper (name free, say `readRoleWire(value,
   shape)`) and one declarative shape table (the shapes below). `readRoleWire` returns a fresh copy holding ONLY the listed
   fields at every level, or `null` when a listed field is missing, an object position holds a non-plain-object (an array,
   `null`, a scalar), a list position is not an array, or an `identity.kind` is neither `author-role` nor `style`.
   Unknown keys, of any value, are dropped, not inspected. Flow in each of the four readers:
   `safeRoleWire(raw, 1 MiB)` on the RAW message first (so hostile keys, oversize and nonfinite numbers refuse wherever
   they sit, in unknown subtrees too), then `readRoleWire`, then today's validators UNCHANGED (they stay
   `exactRoleFields`-exact: they now run on the copy, which has exactly the known keys), and the acceptor stores and
   uses only the copy (never `data`, never `data.groups`/`data.outcomes` of the raw message; echoed roles are read by the
   STRICT ROLE_INPUT shape below, so the copy's `roles` hold exactly the known keys too).
   This is how "never copied into state, exports or saved files" is guaranteed by construction. Shapes (fields in the
   order the validators already list them; `[X]` is an array of X; scalars and arrays of scalars pass through to the
   existing checks). A shape is TOLERANT (unknown keys dropped) unless marked STRICT:
   - STYLE: fontFamily, fontSize, fontWeight, textTransform, letterSpacing. VARIANT: style:STYLE, count.
   - IDENTITY: kind=`author-role`: kind, name; kind=`style`: kind, style:STYLE.
   - BINDING: value, stable, reason. CHECK: roleId, selector, matchCount, signatures:[VARIANT].
   - GROUP: id, identity:IDENTITY, suggestedName, authorRole, signatures:[VARIANT], elementCount, sampleText,
     sharedClasses (scalars), selectors:[BINDING], bindingComplete, nearDuplicateIds (scalars), adapter.
   - DETECTED: the 14 envelope keys of `validDetectedReply` 4248-4249 (type, protocolVersion, sessionId, requestId,
     revision, documentId, pageVersion, pageURL, currentPageVersion, currentPageURL, complete, reason, elapsedMs,
     scannedElements) plus groups:[GROUP], selectorChecks:[CHECK] (16 keys in all).
   - ROLE_INPUT (STRICT, ruling 1): id, name, selectors (scalars), adapter, properties. The reader returns a copy only
     when the role has EXACTLY these five keys and `properties` has only keys of the contract's property enum (read
     from the same list the validators use); any other key anywhere in an echoed role, `properties` included, returns
     `null`. The reason: an echoed role can hold only fields Studio sent (Addendum 26 item 2), and an unknown property
     key would make `canonicalCss` disagree with the roles.
   - LOSS: property, count, winningSelector, reason. OUTCOME: id, matched, checked, mismatched, complete, losses:[LOSS].
   - RECEIPT: `ROLE_RECEIPT_KEYS` (4392) with roles:[ROLE_INPUT] (strict), outcomes:[OUTCOME] (tolerant).
   - ROLE_STATE: documentId, pageVersion, pageURL, roles:[ROLE_INPUT] (strict), canonicalCss, hashAlgorithm, cssHash.
     The state object itself is tolerant. Used by `acceptRoleReady` (3994-3997) AND `acceptResetRoleState`
     (4454-4456), the same object kind. A ready whose roleState holds an unknown key inside a role refuses to
     `ROLE_UNSUPPORTED` (no pending request to name); an extra key on the state object itself is dropped.
   `safeRoleWire` also gains one line, before the object check in the loop: `if (typeof item === "number" &&
   !Number.isFinite(item)) return false;` (today it only checks size and the three hostile keys; the plan's "nonfinite
   refuses the whole message" must hold in unknown subtrees too). Callers, checked at BASE and all safe (Studio-built
   requests and replies hold finite numbers, and a nonfinite value already fails each validator): 3995, 3996, 4173,
   4242, 4248, 4309, 4396, 4455, 4784. The ready's `capabilities` object is read field by field already; it needs no
   shape.
   `design:roles-page` is R2.6S, not this slice. The seam is exactly `readRoleWire` plus a shape: R2.6S adds a
   ROLES_PAGE shape (documentId, pageVersion, pageURL and the envelope keys) and calls the helper; SK adds no shape, no
   branch and no test for it (an untested branch). `tests/role_contract.py` gets the roles-page case from R2.6S.
3. **Visible failure, Detect (item 4).** In `acceptDetectedRoles`, a reply is "matching" when `roleView.pending` is set,
   `data.requestId === pending.requestId` and `data.documentId === pending.documentId === roleView.identity.documentId`
   (the session is already checked by `acceptBridgeMessage`, 4495). A matching reply that fails `safeRoleWire`,
   `readRoleWire` or `validDetectedReply` sets `roleView.status` to
   `Studio could not read the page's reply to Detect; this page has not been checked.`, renders it in `#roleStatus`,
   leaves `roleView.rows` and the accepted preview untouched, KEEPS `roleView.pending` (the existing hostile-then-fence
   tests rely on a later valid reply for the same request still rendering) and cancels the Detect timer (Requirement 4),
   so the unreadable message is not overwritten by "did not reply". Every non-matching reply (other request id, other
   document, no pending, stale `currentPageVersion < current.pageVersion` after validation) stays a silent drop as today.
   **Detect rejection (I2).** A `design:rejected` is "matching" for Detect in `rejectRoleDetect` (4322) when its
   `requestId` equals `roleView.pending.requestId` (a rejection carries no `documentId`, so the match is requestId plus
   the session that `acceptBridgeMessage` already checked). One that fails `validRoleRejection` follows the SAME rule as
   an unreadable Detect reply: the status becomes the string above at once, `roleView.rows` and the preview stay,
   `pending` is KEPT and the Detect timer is cancelled (today it returns `true` and changes nothing, so 8,000 ms
   later the timer would otherwise overwrite the string with "did not reply"). A VALID rejection keeps today's
   behaviour (status "Role detection rejected (...)", `pending = null`); give it the same timer cancel so the handle
   is never left running (the identity guard makes it inert anyway). A rejection for another request id stays silent.
4. **Detect timeout (item 4).** The Detect click handler (4234) starts `setTimeout(..., REQUEST_TIMEOUT_MS)` and stores
   the handle on the pending object. On firing, if `roleView.pending` is still that same object, set `roleView.pending =
   null`, `roleView.status = "The page did not reply to Detect; this page has not been checked."` and render. The
   handle is cleared when a reply is accepted or shown unreadable; a stale firing (the pending was replaced, cleared by
   a reload, a ready, a rejection or a newer Detect) changes nothing, by the identity guard (no other site needs to
   clear it, so no edit to `resetRoleSession`/`acceptRoleReady`/`advanceRoleIdentity`/`rejectRoleDetect` is required).
   A reply to a cleared Detect finds `pending === null` and is ignored by the existing first line: rows and status stay.
   A later Detect works (new request id). A VALID reply that is stale (`currentPageVersion < current.pageVersion`) stays
   a silent drop, so 8 s later the status says "did not reply" although the page replied; accepted, say so in the report.
5. **Visible failure, Apply and Clear (item 4).** In `acceptRoleReceipt`, a matching reply is: `found = roleOpFor(
   data.requestId)` is the IN-FLIGHT op (`!found.late`) and `data.documentId === found.op.documentId`. A matching reply
   that fails `safeRoleWire`, `readRoleWire` or the receipt validation sets `rolePreview.message` to
   `Studio could not read the page's reply; the preview on the page may differ from what Studio shows.`, renders (it
   shows in `#rolePreviewStatus`), and does NOT settle: `live.inFlight`, the request timer and the queue are untouched,
   so the op follows the existing path to "No response to <operation>; ..." after 8,000 ms, and a valid receipt that
   arrives before or after (late) settles it as today. Do not call `markRolePreviewUnconfirmed`. A reply for a LATE
   (timed-out) op, for another id, document or session, stays silent. The same applies to a `design:rejected` whose
   `requestId` matches the in-flight role op and fails `validRoleRejection`: today `rejectRoleOp` returns `true` and
   changes nothing; it shows the same Apply/Clear string, does not settle (same as an unreadable receipt), and for a
   matching Detect rejection (`rejectRoleDetect`, 4322) the Detect string (Requirement 3); both still consume the message (no fall through to the legacy handler). For
   the Apply/Clear case the match is again requestId against the in-flight op only (no `documentId` in a rejection)
   plus the session. Rejections stay strict (no `readRoleWire`; owner ruling 2).
6. **Real-bridge and fake-peer split (AGENTS.md).** The real bridge sends exactly the revision-1 fields and always
   replies, so it can show only: ready with `roleRevision: 1` enables Detect; Detect, Apply and Clear round-trip and
   render (all through the shape reader). Extra keys, unreadable replies and silence need a fake peer; the report states this.
7. **`tests/role_contract.py`.** Add `ROLE_REVISION = 1` (comment: "Addendum 26 item 1; 0.4.0 contract") and a builder
   `with_unknown_keys(message)` returning a deep copy of a valid wire message with the key `futureField` (value
   `{"nested": [1]}`, hostile-free) added to EVERY dict in it except every dict inside an echoed role (the role itself and its `properties`
   map), i.e. everything under the `roles` list of `roles-applied` and of the `role-state` (ruling 1: echoed roles are
   strict). The message itself is a dict, so the top level gets it too; the `role-state` object and the receipt
   envelope get it, the roles in them do not. Plus `TOLERANT_KINDS = ('detected', 'roles-applied',
   'role-state')` (R2.6S appends `'roles-page'`). The oracle is Addendum 26 item 3, a literal, not Studio's shape table.
8. **Forced edits to existing Studio tests** (they assert the OLD exactness; change only these rows, name each in the
   report as a characterization change forced by Requirement 2, and move the accepted behaviour into the new class):
   `test_ready_requires_exact_snapshot_and_supported_capability`: drop the `'extra key'` row (431, an extra key on the state
   object: now tolerated) and add two rows to the same loop: `'no roleRevision'` (a ready whose `capabilities` lack
   it, built like the final `capabilities:{}` case at 452) and `'extra role key'` (an unknown key inside one echoed
   role of `roleState.roles`, refused with `ROLE_UNSUPPORTED`; strict echo, ruling 1). `test_exact_hostile_shapes_...`: drop `'extra top-level key'` and `'extra group key'` (544).
   `hostile_receipts` (1097, 1098): drop `'loss extra key'` and `'extra receipt key'`. KEEP `'extra role key'` (1076): it
   is now the strict-echo row. `test_a_reset_all_reply_without_a_valid_empty_role_state_...` (1715): drop `'extra
   key'` (a top-level `roleState` key, tolerant). Rejection tests (1495-1520, 2730s) are unchanged and must stay
   green: the Requirement 5 string contains no "rejected", and the valid receipt that ends 1495 overwrites the message
   (confirm in the first run). Edit the docstrings of those tests so their Then matches the remaining rows.
9. **W2 review Minors (Studio side and Studio tests).** Verified at BASE against the findings in
   `docs/implementation/tasks/r2-task-w2*-review.md` and `.superpowers/sdd/r2/w2-review.md`:
   - TAKEN, W2SB Minor 1: `test_studio_roles.py` 1074-1075 index `table.FAMILIES_REFUSED[0]` and `[8]` (at 1074-1075). Select by
     property instead (first entry whose lower-cased text is in `table.FAMILY_KEYWORDS`; first containing `(`), so a
     reorder cannot make a row's name lie. Within the budget (about 4 lines).
   - TAKEN, W2SB Minor 2: the help text `ROLE_FIELD_HELP.fontFamily` (3858) reads `... or url( expression( var( env( attr(,
     not a CSS-wide keyword (inherit, initial, unset, revert, revert-layer), and parentheses only inside quotes`. Change
     ONLY the punctuation of the function list: `... or url(, expression(, var(, env( or attr(, not a CSS-wide keyword
     (inherit, initial, unset, revert, revert-layer), and parentheses only inside quotes`. The words "not a CSS-wide
     keyword" and "parentheses only inside quotes" stay: `test_studio_roles.py` 774 and 775 assert exactly those two
     substrings of the gate reason (grep both at BASE; no other test or doc pins the sentence). No test edit is forced.
   - ALREADY FIXED at 362ffd11 (verified in source; no action): W2PS Minor 1 (rows for a mono page group with
     `bindingComplete: false` and a non-stable page binding exist at 2519-2523); W2PS Minor 3 (`ROLE_PAGE_MONO` now sits
     above its comment, 3866); the W2SB comment about `ROLE_FAMILY_UNSAFE` (true now the bridge rule landed); S1 (the
     serializer comment names `roleCssBlocks`); T8 (b) and (d) in `role_contract.py` (header and the bool check).
   - LEFT: W2PS Minor 2 (the `two body roles`/`two mono roles` receipt rows cannot reach the count rule; the ready
     rows kill it; a limit of the earlier brief, not a defect); W2PS Minor 4 (no `BODY` selector-check row; optional);
     W2PS closing note (two-adapter list kept in two sites by design); W2T Minors (a local helper for the three
     `role-state` constructions; the `weight as a boolean` row; the AUTHOR_ROLES comment is bridge-side
     `test_role_protocol.py`, not owned); SIMPLIFY4 (a `refuse()` helper for six "refuse, fence, one row" loops: a refactor of
     uncovered-by-this-slice tests, line budget); R7 (literals beside table names; the cited lines have moved, only
     `10001` at the receipt table remains and is not in this slice's rows); T8 (c) `CHECK_SIGNATURES` in
     `STUDIO_SIDE_ONLY` (whether the bridge class reaches it is a bridge-test question for R2.6B2). Bridge-side and
     integration-file Minors (W2SA, W2SC, W2PI, W2E, W2L) are not owned.

## Tests (new class `StudioRoleReplyTests`; per-engine via `per_engine`; each has a Given/When/Then docstring)

Fake clock (nothing in `tests/` uses `page.clock` at BASE): `page.clock.install(time=0)` after `open`, then
`page.clock.pause_at(<a later time>)` BEFORE the click under test, so fake time moves only with
`page.clock.run_for(ms)`. With `install` alone fake time flows with real time and a boundary test is flaky. Before
relying on it the implementer shows, in the report, that `wait_for_function` (the helpers at 165-200, polling 50) and the
peer-frame `evaluate` calls still work while the clock is paused. If they do not, the deterministic alternative is:
never `wait_for_function` while paused; read text with `evaluate` after each `run_for` (and use `page.wait_for_timeout`
only outside the paused span). Either way say which was used. Tests 6 and 8 need the pause only for their
8,000/9,000 ms steps; test 7 needs it throughout.

Base messages for tests 4 and 9 hold EVERY dict kind, so a mutant that skips a kind is killed: the Detect reply is the
reply to a SECOND Detect with a known role (so `selectorChecks` is non-empty and a CHECK has a signature VARIANT), with
groups of both identity kinds (`author-role` and `style`), a selector BINDING and a signature variant in a group; the
receipts hold an outcome with a loss. Test 9 counts `futureField` against those same messages.

All wire messages are built from `role_contract` and the existing helpers; real-bridge cases use `self.open(engine)`
(default `ROLE_PAGE`, the real bridge); fake-peer cases use `PEER` variants. Add `PEER_NO_REVISION` (caps
`{roleDetection:true,roleStylesheet:true}`) and a peer factory for a chosen `caps` literal.

1. `test_the_real_bridge_advertises_a_revision_and_detect_apply_clear_render` (REAL bridge): ready enables Detect with
   "Ready to detect text styles."; Detect lists a row; Apply a size and Clear both settle with their usual statuses.
   GREEN characterization (passes before the change only if the RV bridge is present; it guards the real wire against the
   new reader). Mutant: the shape table drops `adapter` from GROUP (the real reply then refuses): the test fails.
2. `test_a_ready_without_a_valid_role_revision_is_a_bridge_without_role_support` (peer): for `roleRevision` in missing,
   0, -1, 1.5, "1", true, null, 2**53: status `UNSUPPORTED`, Detect disabled, only `design:hello` sent, no rows; then a
   good ready recovers. RED now (the ready is accepted). Mutant: `>= 1` becomes `>= 0`; and `isSafeInteger` becomes
   `Number.isFinite`.
3. `test_a_higher_revision_is_accepted_and_still_receives_revision_1_requests`: caps `roleRevision` 2 and 2**53-1
   enable Detect; the detect request keys are exactly `type, protocolVersion, sessionId, requestId, documentId,
   knownRoles` and, after Apply, the apply request keys exactly `type, protocolVersion, sessionId, requestId,
   baseRevision, documentId, pageVersion, roles`. GREEN characterization. Mutant: Studio adds `roleRevision` to the
   detect request.
4. `test_unknown_keys_are_ignored_outside_echoed_roles_in_the_reply_kinds_and_never_reach_state_or_exports`
   (peer): for each kind in `TOLERANT_KINDS` the message with `with_unknown_keys` (echoed roles excluded, ruling 1) renders exactly as the plain one
   (rows, preview CSS, outcome text, status). The `futureField` value contains a marker string `LEAK-7`; assert the
   marker is in no `#detectedRoles`/`#rolePreviewOutcomes` text, in none of `self.exports(page)` (all code tabs,
   downloads and the JSON export), in none of the next detect request's bytes and none of an Apply request's, and
   that the exports are byte-identical to those taken before the reply. RED now (each is refused). Mutants (state is
   closure-private, so use source mutants): one shape lists `futureField` as a key (the exact validator then refuses the message, the test
   fails on the missing row); the reader skips `selectorChecks` items (a known-role Detect whose check carries an
   unknown key then refuses).
5. `test_hostile_content_still_refuses_even_inside_an_unknown_key` (peer, fence pattern like 530): unknown key
   holding `__proto__` / `constructor` / `prototype` (built with `json.dumps` then the `JSON.parse` path in `send`), a
   nonfinite number (`float('inf')`, via the existing `: Infinity` replacement), a value that pushes the message one byte
   over 1 MiB and a known object position holding an array: each refuses (the fence is the only change) for a Detect
   reply and a receipt. GREEN characterization at BASE (the exact validators already refuse every row); it guards the
   new tolerance and shows its value only through its mutants: the nonfinite line removed from `safeRoleWire`; the
   reader called on the raw message without `safeRoleWire` first.
6. `test_an_unreadable_reply_to_detect_says_so_and_a_later_valid_reply_still_renders` (peer): a matching reply missing
   `groups`, one with a malformed group, one with an oversize body: the status equals the Requirement 3 string exactly;
   prior rows untouched; after `run_for(9000)` the status is STILL that string (the timer was cancelled); a valid
   reply for the same request then renders "Detected ...". A reply with another request id, another document id or no
   pending changes nothing. Second run (I2): a matching `design:rejected` for the Detect with an extra key (requestId
   `fks-detect-<n>`, no documentId) gives the exact same string, the rows stay, and after `run_for(9000)` it is STILL
   that string; a rejection with another request id changes nothing. Third run (ruling 3 coherence): after the
   unreadable status, press Detect again (the button is not gated by `pending`, click handler 4234): a new request id is sent, its
   reply renders, and the old timer is inert. RED now. Mutants: the timeout is not cancelled on unreadable (the string
   flips to "did not reply"); the same for the rejection branch.
7. `test_a_detect_nobody_answers_is_cleared_after_8_seconds_and_a_late_reply_is_ignored` (peer, paused fake clock): at 7,999
   ms still "Detecting text styles…"; at 8,000+ the exact Requirement 4 string, rows unchanged; a valid late reply for
   the cleared request changes neither status nor rows; a new Detect gets a new request id and renders its reply.
   After a Detect answered at 1 s, advancing to 20 s leaves "Detected ..." (the timer does nothing). Mutants:
   the identity guard removed (the answered Detect is overwritten); `REQUEST_TIMEOUT_MS` replaced by `9000`
   (7,999/8,000 boundary fails).
8. `test_an_unreadable_apply_or_clear_receipt_says_so_and_does_not_settle` (peer, per operation): the matching receipt
   missing `outcomes` (Apply) or with `roles` non-empty (Clear): `#rolePreviewStatus` equals the Requirement 5 string
   exactly, `#rolePreviewCss` unchanged, Apply/Clear still gated as in flight (a second press queues, nothing is sent); a
   VALID receipt then settles it ("Preview applied to 1 role; ..." / "Preview cleared."); and in a second run, after
   `run_for(8000)` the status reads "No response to apply" / "No response to clear" (use the exact existing text),
   with a late valid receipt still accepted. A matching unreadable `design:rejected` (extra key, in-flight request id)
   shows the same string, does not settle, and the op still reaches "No response to ..." after `run_for(8000)`. A
   reply with a wrong request id, wrong document id, or for a late op shows nothing new. Mutant: the unreadable branch calls
   `settleRoleOp`; and one that fires for a late op.
9. `test_the_contract_table_builder_adds_the_unknown_key_at_every_dict_and_nothing_else` (no browser): over one valid
   message of each kind the builder's output equals the input once `futureField` is removed everywhere; a count of
   `futureField` equals the number of dicts except those inside echoed roles (the `roles` list of `roles-applied` and
   `role-state`: the role dicts and their `properties`); `ROLE_REVISION == 1`. Mutant: the builder skips dicts inside
   lists; and one that also adds the key inside echoed roles.
10. `test_an_unknown_key_in_an_echoed_role_refuses_and_a_matching_reply_says_so` (peer; strict echo, ruling 1): (a)
   ready whose `roleState.roles[0]` has an extra key, and one with an unknown key in its `properties`: status
   `UNSUPPORTED`, Detect disabled, then a good ready recovers; (b) a matching in-flight receipt whose `roles[0]` has an
   extra key (and one with an unknown `properties` key): `#rolePreviewStatus` equals the Requirement 5 string, not
   settled, and the valid receipt then settles it. (a) is GREEN at BASE (the exact validator refuses); (b) is RED (no
   string). Mutant: ROLE_INPUT becomes tolerant (the extra key is dropped and the reply accepted).
   Existing tests that already pass and must stay green: the whole Detect/receipt/ready hostile tables (minus the dropped
   rows), `test_a_silent_peer_times_out_the_role_op_...`, the rejection tests, the exports-byte-identical test.

TDD: run each new test at BASE before the Studio change: 2, 4, 6, 7, 8 fail (RED), 10 fails in its (b) part, and 9
fails on the missing builder (import error); 1, 3 and 5 are GREEN characterizations (say so, and that 5 earns its value
only through its mutants). Per new test, show the named mutant failing and restore
`fontkit-studio.html` byte-exact (SHA-256 before and after). Scratch scripts and logs carry `sk` in their names.

## Focused command

```
cd C:/fks/tsk && PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_studio_roles test_support -v
```
`test_support` because `test_studio_roles` is changed and `role_contract.py` is shared; also run once
`cd C:/fks/tsk && PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_studio_live test_role_protocol -v`
(they read the same ready and contract table); `node --check` on nothing (no bridge change). Real bridge cases need the RV landing in BASE. Hosted CI runs the frontend gate and Firefox canary: skip them.

## Handoff (for the landing)

Commit subject: `feat(studio): read role replies tolerantly and report unreadable ones` (68 characters). Draft a
why-body (wrap at 72): a bridge one field ahead of Studio no longer leaves Detect hanging; Studio checks the
bridge's role revision; an unreadable or missing reply is named in the role panel. Plan bookkeeping (controller): a
ledger event, D075 cost note, README role section sentence about the revision and the two statuses at the release point.
Name in the report: the forced test edits (Requirement 8), the Minors taken and left (Requirement 9), the
`safeRoleWire` nonfinite line, and any new fake-ready site found by the grep.

## Open questions

1. (Superseded by owner ruling 1 below: echoed roles, with `properties`, are strict. Kept only so the numbering
   matches the rulings.)
2. `design:rejected` is not among the four kinds Addendum 26 item 3 names, so it stays strict (an extra key in a
   rejection is still dropped, but now with the item 4 message). Option B: read rejections through the same helper (a
   second shape, ~8 lines, a rejection with a new field would then settle the op). Recommend A until the owner extends the list.
3. Requirement 3 keeps `pending` after an unreadable Detect reply (a later valid reply still renders). Alternative: clear
   it (a fence reply then does nothing and the existing hostile tables need a new Detect between rows, about 40 changed
   test lines). Recommend keeping it.

## Controller and owner rulings on the open questions (2026-10-18)

1. Owner: "Echo stays strict (Recommended)". Echoed role data (`roles` in `design:roles-applied` and in
   `design:ready.roleState`, with each role's `properties`) follows Addendum 26 item 2: it can hold only fields Studio
   sent, so an unknown key there refuses the reply, shown with the item 4 "could not read" status when it matches a
   pending request. Every other object in the four reply kinds stays tolerant. The landing records this as an
   Addendum 26 clarification.
2. Owner: "Strict, but visible (Recommended)". `design:rejected` keeps its exact legacy shape. A rejection that
   matches a pending role request (session, document, requestId) but fails validation shows the item 4 "could not
   read" status for that operation instead of being dropped.
3. Controller: as recommended. After an unreadable Detect reply the status shows at once, the Detect timer is
   cancelled and `pending` is kept, so a later valid reply to the same request still renders. The brief review
   checks that the Detect button and status stay coherent in that state.

## Revision 1 (2026-10-18)

Resolves `task-sk-brief-review.md` (Ready with fixes). Line numbers are the brief's current ones.

- I1 (strict echo): header of Requirement 2 and the STRICT ROLE_INPUT, RECEIPT and ROLE_STATE shapes (lines 59-95);
  Requirement 7 builder skips echoed roles (142-148); Requirement 8 keeps `'extra role key'` and adds the ready
  `'extra role key'` row (149-158); new test 10 (264-270); test 4 retitled (200); Open question 1 marked superseded (296-298).
- I2 (Detect rejection): Requirement 3 "Detect rejection" paragraph (100-116) and Requirement 5 tail (126-138), matched on
  requestId plus session because a rejection has no `documentId`; test 6 second run (230-245); test 8 rejection row.
- I3 (clock): the "Fake clock" paragraph before the tests (185-200): `install(time=0)` then `pause_at` before the click,
  proof that waits work while paused, with `evaluate`-after-`run_for` as the deterministic fallback; test 7 is "paused".
- I4 (TDD and fixtures): TDD paragraph (RED: 2, 4, 6, 7, 8, 10b; GREEN: 1, 3, 5, 10a; 9 fails on the missing builder);
  "Base messages ... hold EVERY dict kind" paragraph; test 5 relabelled GREEN with its mutants.
- I5 (help text): Requirement 9 second TAKEN bullet: only the function-list punctuation changes; the pinned phrases at
  `tests/test_studio_roles.py` 774-775 stay true; no test edit forced.
- M1: lines corrected to 3858, 4322, 4234, 452 (header says all were checked at BASE). M2: Requirement 2 DETECTED shape
  (14 envelope keys plus two, 16). M3: `safeRoleWire` caller list and the one-line rule in Requirement 2. M4: test 6 third
  run. M5: Requirement 4 last sentence. M6: second command in "Focused command". M7: budget now about 640 gross lines.

## Revision 2 (2026-10-18; sdd-reviewer re-review findings folded by the controller, `task-sk-brief-rereview.md`)

- I1: test 7 gains a stale-timer scenario that kills the "identity guard removed" mutant: Detect A unanswered; at
  5 s press Detect again (pending replaced, A's timer NOT cancelled); answer B at 6 s (status `Detected ...`); at
  8 s A's timer fires. With the guard the status stays `Detected ...` and the rows stay; without it the status flips
  to `The page did not reply to Detect; this page has not been checked.` Drop the accept-path and valid-rejection
  `clearTimeout` calls (the guard makes them unobservable); the only site that must clear the timer is the unreadable
  branch, where `pending` is kept. Req 3 and Req 4 text follow this.
- M1 (replaces the fake-clock fallback sentence): at Playwright 1.62.0, `wait_for_function`, locator `.click()` and
  frame `evaluate` work while the clock is paused (probed). Never call `settle` (page-side requestAnimationFrame,
  `tests/role_support.py` 184-186) or a page-timer-based wait while paused: it hangs the page. Prove "changes
  nothing" by sending the reply, then a following positive (a new Detect round trip that renders), relying on
  same-source message order.
- M2: add one reset-reply row to test 4 or 10: a reset `roleState` with an unknown top-level key is accepted; an
  unknown key inside a role shows the existing "could not be confirmed" message.
- M3: the ready `'extra role key'` rows are built with a state whose `canonicalCss` and `cssHash` match the role set
  (for example `snapshot_state([role_with_extra])`), so they refuse only for the extra key; the "no roleRevision"
  row runs as a separate step (it needs different capabilities).
- M4: test 8 asserts the exact unreadable string BEFORE any second Apply/Clear press, and expects the queued request
  to be sent after the valid receipt settles the first.
- M5: rename or re-docstring `test_malformed_rejections_are_ignored_and_leave_the_request_in_flight` (BASE 1495) so
  it no longer says "ignored" (each matching malformed rejection now shows the could-not-read string); name only,
  docstring and that one assertion's expectation, listed as a forced edit. Test 9's RED at BASE is an AttributeError.
