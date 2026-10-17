# R2 PR B review fixes: brief (2026-10-16)

Sources: the two whole-branch reviews in [r2-pr-b-review.md](r2-pr-b-review.md)
(F1-F7 and CR1-CR10). Each claim was checked in source
by the controller. BASE `2ba1e77` for both writers. They own disjoint files and
run in parallel.

## Studio writer (worktree C:/fks/ts3): fontkit-studio.html, tests/test_studio_roles.py, tests/test_r2_integration.py

1. F1/CR1. `rejectRoleOp` (`fontkit-studio.html` ~4366) drops any non-string
   `detail`. The real bridge's `revision-conflict` sends `detail:
   {baseRevision, revision}` (`fontkit-bridge.js` checkRevision ~1929), so the
   op hangs for 8 s and every later Apply or Clear conflicts. Accept a string
   detail, or for `revision-conflict` exactly
   `{baseRevision, revision}` with non-negative integers. Settle the op and
   adopt the revision. Render the detail as text. Add a real-bridge test that
   produces a role revision-conflict (for example a legacy edit from a second
   authenticated client, or a bumped Studio revision) and then succeeds on the
   next Apply. Delete or flip the test that asserts the object detail is
   ignored.
2. F2/F4/CR2/CR3. `validRoleOutcome` (~4304) must accept exactly what the
   bridge can send:
   - `matched` is any non-negative safe integer, uncapped (the bridge sends
     `sets[i].size`);
   - `checked` is at most 10,000, and `mismatched <= checked <= matched`;
   - `losses.length` is at most 96 (16 groups x 6 properties).
   Real-bridge tests: 10,001 matched elements, and one outcome with more than
   64 loss groups.
3. F5/CR6. `roleFamily` (~3876) matches the bridge's `ROLE_FAMILY_UNSAFE`
   (`fontkit-bridge.js` ~175): reject `var(`, `env(`, `attr(`, `url(` and
   `expression(` with optional spaces before the parenthesis, every control
   character, `!important` with spaces and comments. Show the field's visible
   hint, and update ROLE_FIELD_HELP.fontFamily. Use table-driven parity rows.
4. CR5. Composition coalescing (~4673) must not merge into a composition op
   queued before an untargeted reset, a restore or a role op. Mirror the
   update branch's barrier. Test: queue [composition A, reset-all], change the
   composition to B; B is sent after the reset and survives.
5. F6. A ready from a legacy or invalid bridge must not leave the previous
   app's preview CSS shown as current. Show it cleared or explicitly not
   applied, with visible wording. Test it.
6. F7. A role op that was queued but never sent, then dropped by reset or
   re-hello, must not leave "Applying role preview..." on screen. Test it.
7. CR8 performance. Re-render the outcome list only when `rolePreview`
   changes. Text fields listen to `input` only. Compute the size probe only
   when the selection or values change, not twice per keystroke. Behaviour is
   unchanged; prove it with the existing tests, plus one check that typing a
   key does not rebuild the outcome nodes.
8. CR10. Use `ROLE_REJECTIONS` and one shared rejection shape check in both
   `rejectRoleDetect` and `rejectRoleOp`.

## Bridge writer (worktree C:/fks/t26): fontkit-bridge.js, tests/test_role_stylesheet.py, tests/test_role_preview.py, tests/test_role_detection.py (only new cases)

1. F3. Detect with a live preview on a page with CSS transitions reports the
   preview value. Disabling the owned sheet starts a transition from the
   preview value. Keep the baseline exact: inside the same synchronous read
   batch, also install a bridge-owned style that sets transition and animation
   to none, so no transition starts. Restore in a finally block without
   leaving a transition running. Settle the bridge's own mutations as usual.
   Test: `p { font-size: 16px; transition: font-size .2s linear }`, apply
   30px, Detect: the baseline is 16px, no new role appears, and the page
   renders 30px again afterwards. D058 timings hold.
2. F4. A winning `selectorText` containing C0, DEL, C1 (U+0080-U+009F),
   U+2028 or U+2029 is reported as `{winningSelector: null, reason:
   'complex-cascade'}`. This matches Studio's bounded-text rule. Test with an
   escaped selector such as `.a\85`.
3. CR7. `settleOwnWrites` drops author mutations made synchronously by app
   listeners that the bridge's handlers call, for example
   `design:order-changed` (~3890). Settle the bridge's own writes before
   dispatching any author-facing event or callback, as `acknowledge()` already
   does before `onApplied`, so the listener's mutations advance pageVersion.
   Prefer filtering by ownership if that is simpler and provable. Test: an
   `order-changed` listener appends a node, and the next roles-apply with the
   old version is rejected `page-changed`.
4. CR9. `postRoleReceipt` must not serialize every stylesheet again right
   after `roleJobFresh` did. Pass the page version and URL already computed.
   The behaviour and the tests are unchanged.
5. CR10. Keep one copy of the loss-reason order and the loss comparator,
   shared by `fitRoleReceipt` and `measureRoleOutcomes`.
6. Font status (CR4), released: D066 / Addendum 14. document.fonts status moves
   the internal epoch, never the wire pageVersion. See the controller message.

## Both

Every new or changed test has a Given/When/Then docstring and asserts
rendered or intended behaviour. Show RED first, or a killed mutant restored
byte-exact. Run focused gates only: your modules plus `test_support`, and
for the Studio writer the second Studio command from `task-s2a-code-report.md`.
Scratch files carry your task id (`ts3` or `t26`). A denied tool call is
reported, never retried through a different tool. Never commit. Keep each
round near 400 material lines.
