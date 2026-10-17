# R2 PR B whole-branch review (feat/r2-role-preview, HEAD 2ba1e77, origin/main..HEAD)

Read-only review through git objects. Scratch probes ran only in the session scratchpad
(`prbrev/prbrev_conflict.py`, `prbrev/prbrev_losses.py`), chromium only, targeted. Findings are
appended as confirmed.

## Findings

### F1 (Important) Studio drops every `revision-conflict` rejection for a role op, and the session never recovers
- Bridge: `fontkit-bridge.js` `checkRevision` (about line 1927 of HEAD) calls
  `reject(..., 'revision-conflict', { baseRevision, revision })`, and `reject` (line 1139) sets
  `message.detail = detail`. So the wire `detail` is an OBJECT for this reason.
- Studio: `rejectRoleOp` (fontkit-studio.html, `exactRoleFields ... typeof data.detail !== "string"`
  -> `return true`) treats a non-string `detail` as malformed: it returns without settling the op,
  without adopting `data.revision`, and without a message.
- Effect (reproduced against the real bridge, `prbrev_conflict.py`): after the bridge's revision moves
  without Studio hearing of it, Apply shows "Applying role preview..." for the whole 8 s request timeout,
  then "No response to apply". `live.revision` is never refreshed, so every later Apply or Clear
  conflicts again and is dropped the same way (retry reproduced). The only exit is a reconnect.
- Why the tests missed it: `tests/test_studio_roles.py` ~1396 drives the rejection with a fake bridge
  that sends `detail` as a STRING (`'<img src=x onerror=alert(1)>'`), and
  `test_malformed_rejections_are_ignored_and_leave_the_request_in_flight` (~1409-1420) pins "detail not
  text -> stays in flight" as intended behaviour, so the suite asserts the defect. No test sends the real
  bridge's object detail. This is a fake-only boundary case (Test Quality Rules).
- Fix: accept `detail` as a string or a plain object (show nothing or a bounded JSON-free summary for an
  object) and, in particular, always adopt `data.revision` and settle the op for a well-formed
  rejection. Add a real-bridge test: move the bridge revision with a raw `design:roles-clear` carrying
  Studio's session, press Apply, assert the revision-conflict status, then that the next Apply succeeds.

### F2 (Important) Studio silently discards a valid receipt with more than 64 loss entries; the bridge can send 96
- Bridge: `measureRoleOutcomes` `capped()` keeps up to 16 groups per role AND per property, so one
  outcome can hold 6 x 16 = 96 loss entries (`fontkit-bridge.js` diff lines ~657-667).
- Studio: `validRoleOutcome` rejects `outcome.losses.length > 64`; `acceptRoleReceipt` then returns
  without settling.
- Reproduced with the real bridge (`prbrev_losses.py`): one `.body` role over 30 paragraphs, each
  overridden by its own `main p.cN` rule on all six properties. The page commits (receipt revision 1,
  `outcomes[0].losses.length === 96`), Studio shows "No response to apply", shows no CSS, and a
  following Clear hits F1 (revision-conflict dropped), leaving a stuck session.
- Fix: one limit, stated in the plan contract and used by both sides. Either cap the bridge at 64 per
  outcome (for example merge the smallest groups into the unnamed complex-cascade entry until
  `losses.length <= 64`) or raise Studio to 96. Add a real-bridge test with this corpus.

### F3 (Important) Detection is not the app baseline once a preview is live and the page has CSS transitions
- Addendum 9 and the CHANGELOG say Detect keeps measuring the app's own styles. The bridge does it by
  setting the owned sheet `disabled` for each synchronous batch (`suspendRoleSheet`; detect `run`,
  `fontkit-bridge.js` diff lines ~721-730) and reading `getComputedStyle` in the same batch.
- Disabling the sheet is a style change. If the author CSS has a transition on the previewed property, the
  forced style recalculation starts a transition whose start value is the PREVIEW value, so the read returns
  the preview value, not the baseline.
- Reproduced with the real Studio and bridge (`prbrev/prbrev_transition.py`): page CSS
  `p { font-size: 16px; transition: font-size .2s linear }`, Detect (16px), Apply 30px, wait 1.5 s, Detect
  again: the second Detect reports `30px / 400 / none / 0em` (the preview) and Studio mints a new role
  (`role-2`) for it, so the baseline observation and the stored role inventory are polluted. `transition: all`
  is common in real apps, so this is not exotic.
- Related, same cause: the first Apply on that page reports the lost size as "overridden; source not
  provable" although the preview renders (animation check gives complex-cascade). That one is honest enough;
  the baseline read is not.
- Fix options: (a) while the sheet is suspended, also suppress transitions for the read (a second
  bridge-owned rule `*, *::before, *::after { transition: none !important }` toggled in the same batch and
  restored before yielding; say in the plan that the preview may replay its transition on restore);
  (b) when a running or finished transition or animation targets a text parent, return `complete:false`
  with a reason instead of a baseline; or (c) if neither is acceptable now, narrow the CHANGELOG sentence and
  record a deviation. Add a real-bridge test with a transitioned property.

### F4 (Minor) Matched counts and winning selectors can exceed Studio's receipt bounds
- Bridge `matched = sets[i].size` is uncapped (`measureRoleOutcomes`); the R2.5 brief pins `matched 10,001`
  on the 10,001-element page (r2-task-5-brief.md:124). Studio `validRoleOutcome` requires
  `roleCount(outcome.matched, 10000)`, so such a receipt is discarded whole (same stuck session as F2).
  It needs a page with more than 10,000 matched elements, so it is rare.
- `winningSelector`: Studio rejects U+0080-U+009F and U+2028/2029 (`roleLossSelector`); the bridge's `named()`
  only bounds length, and a CSSOM `selectorText` does not escape those code points. A rule such as
  `[title="x<U+2028>y"]` that wins a property gets the whole receipt dropped.
- Fix: raise Studio's `matched` limit (keep `checked <= 10000`) and make the bridge send `null` for a selector
  Studio would refuse (same filter), or relax Studio to the length bound only. Keep one limit table in the
  plan. Read from source; not run.

### F5 (Minor) Studio's family check is looser than the bridge's
- Studio `roleFamily` rejects `; { } < > \`, CR/LF/FF, comments, `url(`, `expression(`, `!important` and
  unbalanced quotes. The bridge's `ROLE_FAMILY_UNSAFE` also rejects every C0 control and DEL, `var(`, `env(`
  and `attr(` (and `url`/`expression` with whitespace before the paren).
- Reproduced (`prbrev/prbrev_family.py`, real bridge): `var(--f)`, `env(x)`, `attr(x)` and a quoted family
  containing a TAB all leave Apply enabled with no field warning; the bridge then answers
  `Role preview apply rejected (unsupported-value) ... Detail: Unsupported property value`.
  The reverse direction (bridge accepts, Studio rejects) did not occur for the family field.
- Fix: align Studio's regex with the bridge's (control characters, `\b(?:url|expression|var|env|attr)\s*\(`,
  `!\s*important`) and add the tokens to `ROLE_FIELD_HELP`. A rejection after a round trip is safe, so Minor.

### F6 (Minor) A ready from a bridge without role support keeps showing the previous app's preview
- `acceptRoleReady` on an invalid or legacy ready only calls `markRolePreviewUnconfirmed()` and returns
  (fontkit-studio.html diff ~3960); `rolePreview` has no origin, so after switching the target to an old
  bridge, or to another origin whose ready is invalid, the previous app's CSS, counts and loss lines stay on
  screen with only an "Unconfirmed: ..." prefix. Read from source; not run.
- Fix: when the ready is invalid, or `live.expectedOrigin` differs from the origin the preview was
  acknowledged on, call `installAcceptedRoles([], "", ROLE_EMPTY_HASH, -1, null, null, "No role preview applied.", false)`.

### F7 (Minor) A role op that never left the queue can leave "Applying role preview..." on screen
- `resetRoleSession` sets `ROLE_DROPPED` only when `live.inFlight` is a role op. `resetSessionState` then
  empties `live.queue` silently. A queued (not yet in flight) Apply or Clear keeps its "Applying..." or
  "Clearing..." message, and `acceptRoleReady` keeps the old message when the new ready has the same document
  and CSS hash (a re-hello on the same page). Read from source; not run.
- Fix: in `resetRoleSession` set `ROLE_DROPPED` when any role op is in flight or queued.

## Checked and found sound (no action)
- Trust boundary: `acceptBridgeMessage` checks source window, origin, protocol 1, type allow-list and session
  before `design:roles-applied` or `design:rejected` are read; receipts also match requestId, expected
  operation, the op-frozen documentId, current identity, base revision + 1, page version and, for apply, the
  role id order. Untrusted strings (names, CSS, winning selectors, `detail`) reach the DOM through
  `textContent` only; the added code has no `innerHTML`, `insertAdjacentHTML`, `console.*` or `debugger`.
- Bridge posts use the existing pinned-origin `post`; hello and dropSession bump `roleEpoch`, so an old
  receipt is never sent through a new session.
- Global rules 1, 2, 6: role ops are separate queue kinds and never touch `live.changes`, saved overrides or
  the sync body (test `test_role_css_never_reaches_the_code_tabs_downloads_exports_or_the_synced_file`, and
  the re-hello test); ready never replays a preview; import keeps queued role ops; Reset all page edits is the
  only untargeted reset, behind `window.confirm` whose text names the sync consequence.
- Cross-task values agree: request envelope keys, 256 KiB request, 1 MiB reply, 128 roles, 32 selectors,
  100/200 id/name limits, value ranges and rounding (`round` and `roundTo` are the same formula), the
  `revision === baseRevision + 1` rule, the six rejection reasons, the seven loss reasons, `outcomeReason`
  null/page-changed/budget-exceeded, empty hash `811c9dc5`, the ready `roleState` shape and the global-reset
  `roleState` (Studio requires zero roles and a same-document identity).
- Timers and listeners: measurement `setTimeout`/`requestAnimationFrame` chains stop on `roleJobAlive` (epoch,
  source, origin, session, disposed); `dispose` removes the owned node and the native-state listeners go
  through `this.listen`. Studio adds one persistent delegated listener on `#roleRows`.
- Docs: README, the protocol spec and the roadmap contain no claim the new messages contradict (README only
  documents `design:reset`, which still holds). The plan's PR table row for PR B still lists R2.4/R2.7F2b, but
  Addendum 13 and D064 supersede it explicitly.
- Tests: the only fixed waits in the diff are three absence waits (`quiet`, 300 and 450 ms) and a bounded 50 ms
  poll for a held route; no vacuous assertions found in the sampled receipt, reset and queue tests. The gap is
  coverage of the REAL bridge's rejection and receipt shapes at their limits (F1, F2, F4).
- CHANGELOG Unreleased is honest apart from "Detection keeps measuring the app's own styles" (F3). "Receipts
  always stay within 1 MiB" holds by `fitRoleReceipt`; the stricter 64-entry Studio limit is F2.

## Counts
Critical 0, Important 3 (F1, F2, F3), Minor 4 (F4, F5, F6, F7).

## Verdict
Changes required. F1 and F2 are reproduced stuck sessions that the real bridge can cause with ordinary input,
and an existing test pins the wrong behaviour; F3 contradicts a user-facing CHANGELOG sentence. Each fix is
small and local (one shared limit table, accept the object `detail`, a transition-safe baseline or a narrowed
claim), but the new real-bridge tests should be reviewed with them.

STATUS: COMPLETE

## Second whole-branch review: findings CR1-CR10 (2026-10-16)

A second independent review of `origin/main..HEAD` at `2ba1e77`, with dispositions.

| ID | Finding | Disposition |
|---|---|---|
| CR1 | Studio's `rejectRoleOp` drops the bridge's object `detail` on `revision-conflict`; the role op hangs and Apply cannot recover (same as F1). | Fixed, Studio item 1. |
| CR2 | Studio caps `matched` at 10,000; the bridge reports it uncapped. | Fixed, Studio item 2. |
| CR3 | Studio rejects more than 64 losses; the bridge allows 96. | Fixed, Studio item 2. |
| CR4 | `document.fonts.status` in the role style stamp makes the preview's own font load a page change. | Fixed, bridge item 6 (D066, Addendum 14). |
| CR5 | Composition coalescing can jump ahead of a queued Reset all page edits. | Fixed, Studio item 4. |
| CR6 | Studio's family check is looser than the bridge's. | Fixed, Studio item 3. |
| CR7 | `settleOwnWrites` drops author mutations made by app listeners during a handler. | Fixed, bridge item 3. |
| CR8 | Each keystroke re-renders the outcome list and re-encodes the request twice. | Fixed, Studio item 7. |
| CR9 | `postRoleReceipt` serializes every stylesheet again right after the freshness check. | Fixed, bridge item 4. |
| CR10 | The loss-reason order, comparator and rejection checks are duplicated. | Fixed, bridge item 5 and Studio item 8. |

## Follow-up review (2026-10-16, HEAD 5aa39c6)

Read-only through git objects (`git diff 2ba1e77..5aa39c6`: 5b1fe46 bridge, 5aa39c6 Studio). Probes are in the
session scratchpad (`prbrev/prbrr_slow.py`, `prbrev/prbrr_font.py`, plus my earlier probes re-run unchanged).
Chromium, targeted tests only; one Firefox run of the F3 probe.

### 1. Findings re-checked at HEAD

| ID | Result | Evidence |
|---|---|---|
| F1 / CR1 | Resolved | `validRoleRejection` accepts a string detail, or for `revision-conflict` exactly `{baseRevision, revision}` (non-negative safe integers); `rejectRoleOp` settles and adopts the revision. My `prbrev_conflict.py` probe against the real bridge: after 1.0 s the status reads "rejected (revision-conflict) ... Detail: base revision 0, bridge revision 1" (was an 8 s "No response"), and the retry Apply succeeds. The test that pinned the object detail as ignored now keeps only `detail: 5` (neither text nor the conflict object) as ignored. |
| F2 / CR3 | Resolved | `validRoleOutcome` allows 96 losses. Re-ran `prbrev_losses.py` (96 loss entries, 30 matched): "Preview applied to 1 role; 30 checked elements did not show it", CSS shown, and Clear then settles ("Preview cleared.", no rejections). Bridge bound re-derived: `capped()` keeps at most 16 per property and the named-selector cap only swaps entries, so the total never exceeds 6 x 16. |
| F3 | Resolved | `prbrev_transition.py` (Chromium and Firefox): the second Detect reports 16px and a single role, and the page renders 30px again afterwards. A 4 s transition probe (`prbrr_slow.py`), Detect 0.3 s after Apply while the page is mid-transition at 17.2px, also reports the 16px baseline and no new role. The 4 new `TransitionBaselineTests` pass. |
| F4 / CR2 | Resolved | `matched` is any safe integer; the bridge `named()` returns null for exactly the class Studio `roleLossSelector` rejects (C0, DEL, C1, U+2028/2029) and for length over 2,000; Studio requires length of at least 1 (selectorText is never empty). Tests `ten_thousand`, `sixty_four`, `outcome_limits_follow` pass. |
| F5 / CR6 | Resolved | Studio `ROLE_FAMILY_UNSAFE` is character-for-character the bridge regex. `prbrev_family.py`: `var(`, `env(`, `attr(` and a TAB family now disable Apply with the field hint. Test `family_field_agrees` passes. |
| F6 | Resolved by decision | `rolePreview.origin` is recorded at install; an invalid ready from a different origin clears the preview ("This bridge does not report a role preview, so none is shown."). A same-origin invalid ready keeps the CSS marked unconfirmed, the controller's stated rule, which I accept. Test `another_apps_preview` passes. |
| F7 | Resolved | `resetRoleSession` also checks `live.queue.some(isRoleOp)` before the queue is emptied. Test `never_left_the_queue` passes. |
| CR4 | Resolved | `document.fonts` is out of the stamp; `loading`, `loadingdone` and `loadingerror` listeners (registered once under the `roleObserver` guard, removed with the other `this.listen` entries) move only `roleNative`. Tests `font_loading_after` and `font_load_during` pass. A probe with an unloadable `@font-face` family applied twice gave equal page versions (0, 0) and complete outcomes. |
| CR5 | Resolved | The composition branch scans from the queue tail and stops at a restore, a role op or an untargeted reset. Test `not_merged_into_one_queued` passes. |
| CR7 | Resolved | `settleOwnWrites()` before the `design:order-changed` dispatch and `noteRoleMutations(takeRecords())` after it. Test `order_changed_listener` passes. It is the only `dispatchEvent` in the bridge, and `onApplied` was already settled first. |
| CR8 | Resolved | `renderRolePreview` rebuilds the outcome list only when `outcomes` or `roles` change; only `input` is listened to; `roleApplyState` is cached on draft version, rows, identity, capability flags, readiness, revision and session. Test `typing_does_not_rebuild` passes. |
| CR9 | Resolved | `postRoleReceipt(..., refreshed = true)` is passed only right after `roleJobFresh` (which refreshes), with no yield between. |
| CR10 | Resolved | One `ROLE_LOSS_REASONS` and `compareRoleLosses` in the bridge, used by `fitRoleReceipt` and `measureRoleOutcomes`; Studio `rejectRoleDetect` and `rejectRoleOp` share `validRoleRejection` and `ROLE_REJECTIONS`. |

Tests run at HEAD (Chromium, `PYTHONPATH=tests`, targeted): `test_role_detection.TransitionBaselineTests` (4),
`test_role_stylesheet -k order_changed_listener -k font_loading_after -k font_load_during` (3),
`test_r2_integration -k revision_conflict_from_the_real -k ten_thousand -k sixty_four -k family_field_agrees` (4),
`test_studio_roles` new cases (6): all OK. `node --check` on HEAD bridge passes.

### 2. New drift between Studio and the bridge
None found. Re-checked both sides: request keys and limits (256 KiB, 128 roles, 32 selectors, 100/200 ids and
names), value ranges and rounding, family grammar (identical regex), receipt envelope and revision rule,
`matched` (uncapped on both), `checked` and `mismatched` at most 10,000, losses at most 96, loss count at most
10,000 (each element counts once per property), loss reasons, the winning-selector bound (same class and length
rule), rejection reasons and detail shapes (the only object detail on the wire is the `revision-conflict` pair
that `checkRevision` builds; every other role rejection detail is a string or absent), `outcomeReason` rules and
the global-reset `roleState`.

### 3. Trust boundaries and preview isolation
No regression. `acceptBridgeMessage` is unchanged; the new object detail is validated with `safeRoleWire` and
`exactRoleFields` and rendered as a template string of two integers through `textContent`. Role ops still touch no
ledger, override, export or sync path; the composition barrier only narrows merging. The new bridge-owned
transition-ban `<style>` is in `roleOwned` (excluded from the stamp, the mutation count and the author-rule scan),
exists only during a scan with a live preview (test `installed_only_while_a_preview_is_live`), and is removed at
finish, cancel, reset and dispose (tests `throws_inside_the_scan`, `reset_during_a_scan`).

### 4. New observations (all Minor, none blocks the merge)
- N1 CHANGELOG says Detect "pauses the page's CSS transitions while it scans". The bridge does not pause them: it
  stops new transitions from starting, and only while a preview is live. Suggested wording: "stops new CSS
  transitions from starting while it scans".
- N2 The ban is `*, *::before, *::after { transition: none !important }`, which has specificity 0, so an author
  rule such as `p { transition: font-size 1s !important }` still wins and the F3 read would again return the
  preview value on that page. Read from source, not run. D067 states only that other engines are unverified;
  add this limit there.
- N3 The new `catch` around the scan batch turns any exception, including one from bridge code, into
  `page-changed` with only a `console.warn`. Intended for page-thrown errors; a bridge bug would now look like
  a changing page.
- N4 AGENTS anti-pattern 15: both fix commit bodies narrate the review ("Review of the whole role preview branch
  found ..."). Product-story wording would meet the rule. The owner decides whether to reword before the merge,
  since history is not rewritten without instruction.
- N5 `ROLE_DROPPED` still says "the page reloaded" when the op was dropped by a same-page re-hello or a
  disconnect. Wording only.

### Counts
Critical 0, Important 0, Minor 5 (N1-N5, all new and non-blocking). F1-F7 and CR1-CR10: 17 of 17 resolved
(F6 by the controller's same-origin rule).

### Verdict
Approved. The stuck-session and baseline defects are gone against the real bridge, the two sides agree on every
limit, enum and shape I could find, and trust and isolation are unchanged. N1 is a one-line CHANGELOG fix worth
making with the merge; N2-N5 can wait.

STATUS: COMPLETE (follow-up)

Dispositions: N1 CHANGELOG wording corrected; N2 recorded as a limit in D067; N3 accepted (the scan's catch logs a warning); N4 left for the owner; N5 wording corrected.
