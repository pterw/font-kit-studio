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