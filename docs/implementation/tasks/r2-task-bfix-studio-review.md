# PR B review fixes, Studio side: independent review

Patch `task-prb-studio-code.patch` (sha256 e616db0a...), BASE 2ba1e77. C:/fks/ts3 holds it staged (`git diff --cached 2ba1e77` is byte-equal to the patch); the bridge there is still at 2ba1e77 (`git diff 2ba1e77 -- fontkit-bridge.js` empty). The worktree was not edited (hashes of the three files and the bridge compared after all runs). Three files changed: `fontkit-studio.html`, `tests/test_studio_roles.py`, `tests/test_r2_integration.py`.

### Spec Compliance
- PASS, item 1 (F1/CR1): `validRoleRejection` (fontkit-studio.html:4262) accepts a text `detail`, or for `revision-conflict` exactly `{baseRevision, revision}` as non-negative integers; any other object detail (other reason, extra or missing key, negative, text numbers) is ignored and the op stays in flight. `rejectRoleOp` (4394) settles the op, adopts `data.revision` through `settleRoleOp`, and renders the detail via `rejectionDetailText` as `Detail: base revision N, bridge revision M` built from two integers only. The test that pinned "detail not text stays in flight" was extended, not removed: `detail not text` and four object-detail shapes still stay in flight.
- PASS, item 1 real bridge: `test_a_revision_conflict_from_the_real_bridge_settles_at_once_and_the_next_apply_succeeds` moves the bridge revision with a raw `design:roles-clear` carrying Studio's session, presses Apply on the stale revision, sees the real bridge's rejection (status names both revisions and "press the button again"), the page stays 16px, then Apply again carries `baseRevision` 1 and renders 24px. The object-detail mutant errors this test (8 s hang as in F1).
- PASS, item 2 (caps): `validRoleOutcome` (4336): `matched` any safe integer (`roleCount` default limit is `Number.MAX_SAFE_INTEGER`, 3750), `checked` and `mismatched` at most 10,000, `mismatched <= checked <= matched`, `losses.length <= 96`, `loss.count` 1-10,000. Compared with the bridge at 2ba1e77: `matched = sets[i].size` uncapped (fontkit-bridge.js:1634); `checked` only increments after `eligible >= 10000` breaks (1646-1652), so at most 10,000; `loss.count` is one per (element, property), so at most `checked`; `capped()` (1667-1672) keeps `room = 16 - (pool or overflow ? 1 : 0)` named groups plus one merged group per property, i.e. at most 16 per property, 96 over six; `fitRoleReceipt` only merges further. So Studio's limits equal the bridge's exactly: nothing stricter and nothing looser remains in these fields. (`outcomes.length <= 128` and `losses` item shapes were already equal.)
- PASS, item 2 tests: fake `test_outcome_limits_follow_what_the_bridge_can_send` (96 losses and matched 250,000 accepted, the 97th entry and checked 10,001 refused, with the valid fence last); real-bridge 30-paragraph corpus gives more than 64 loss entries and Studio lists every one (` × ` count equals the receipt's).
- PASS, item 3 (F5): `ROLE_FAMILY_UNSAFE` in Studio is character-for-character the bridge's regex (fontkit-bridge.js:175); the visible help text names control characters, `var(`, `env(`, `attr(`. The parity test is genuinely two-sided (see Checks).
- PASS, item 4 (CR5): composition coalescing now scans from the end and stops at a restore, a role op or an untargeted reset; a targeted reset is correctly not a barrier. Test queues [composition, update in flight, composition A, reset-all], then composition B; the observed order is composition, update, composition, reset, composition and the ledger keeps tokens (B survives).
- PASS, item 5 (F6): an invalid or legacy ready from a different origin than the shown preview's clears it with the visible text "This bridge does not report a role preview, so none is shown." and empty CSS/outcomes; a same-origin invalid ready still keeps the CSS marked "Unconfirmed" (controller's rule). `rolePreview.origin` is set at every install. Test switches from an applied preview to a legacy peer on another origin.
- PASS, item 6 (F7): `resetRoleSession` now sets `ROLE_DROPPED` when any role op is in flight or queued. It runs before `resetSessionState` empties the queue. Test: Apply queued behind an unanswered legacy op, then another origin connects; the status says dropped and not "Applying".
- PASS, item 7 (CR8): outcome list is rebuilt only when `rolePreview.outcomes` or `.roles` change (identity compare); text fields listen to `input` only (checkbox and select fire `input` too); the size probe is cached on `[draft version, rendered rows, identity, stylesheet flag, limit flag, live.ready, live.revision, session id]`. I read what `computeRoleApplyState` and `buildRoleRequest` depend on (identity, rows, issued ids, drafts, revision) and every change to those goes through one of the key members: rows and ids are replaced together and followed by a render, drafts change only through `onRoleDraftEdit` (version bump) or `seedRoleDrafts`, which runs only for ids with no draft and cannot affect a displayed row (an accepted role came from a sent draft; a ready resets rows and identity first). No behaviour change found; all earlier tests pass. The extra test asserts the same outcome `li` node survives a keystroke and that the draft and Apply state still follow the key.
- PASS, item 8 (CR10): one `validRoleRejection` is used by both `rejectRoleDetect` and `rejectRoleOp`, with `ROLE_REJECTIONS`; the inline reason list is gone. The detect path now also tolerates a conflict object detail, which is harmless.
- PASS: every new test has a Given/When/Then docstring and asserts the page or rendered text.

### Checks run
- Focused command 1 (Chromium, FKS_REQUIRE_FIXTURES=1) in C:/fks/ts3: `Ran 195 tests ... OK`, exit 0, 0 warnings. Command 2: `Ran 46 tests ... OK`, exit 0 (ts3rev-gate1.log, ts3rev-gate2.log).
- Nine mutants on a scratch copy (ts3rev-copy), byte-exact restore asserted by hash each time, all KILLED by their intended test:
  - object detail ignored again (`return false` for the conflict object) -> real-bridge conflict test errors.
  - `matched` capped at 10,000 -> the 10,001 test fails.
  - `losses` limit 96 to 64 -> the real 64+ losses test fails.
  - `checked` uncapped -> the fake limits test errors (the 10,001-checked receipt is accepted, so the fence never shows).
  - composition barrier removed -> the reset-all ordering test errors.
  - family regex reduced to `url|expression` -> the parity table fails on several rows.
  - outcome-list guard removed -> `test_typing_does_not_rebuild_the_outcome_list` fails.
  - queued-role-op dropped message removed -> the F7 test fails.
  - origin test for clearing the old preview disabled -> the F6 test fails.
- Parity table (judging item 3): for each of 25 rows the test types the value into Studio (or sets it plus an `input` event for control characters), posts the same value as a raw `design:roles-apply` with Studio's session to the real bridge, and asserts `reply.type == roles-applied` equals the expected verdict AND Studio's Apply enabled state equals the same flag. The accepted rows (`Georgia, serif`, a quoted stack, `variable-font`) keep both ways honest, so an always-disabled Apply could not pass; the two-sided assertion would fail if Studio were looser or stricter on any row. Includes spaced `var (`, `url (`, `! important`, tab inside a quoted name, DEL, SOH and a 301-character value.
- 10,001-matched test (judging item 2): honest, with a limit. The real bridge never binds a role to more than 10,000 elements through its own Detect, so the test page replies to the first `design:detect` itself with a `.b` class binding (reply is forged with the bridge's current revision, document and page version and registered first on `window`, so it precedes the real reply, which then arrives for an already settled request). Apply and its receipt are the real bridge's: `matched 10001, checked 1` is accepted and rendered. The comment in the test and the report state this. It proves the Studio cap against a real bridge's count, but the Detect half of that round trip is not real. I accept it as the only way to reach the case; a fake-peer test (250,000) covers the number independently.
- Trust and text: the object detail contributes only two integers to the status; string detail still capped at 200 characters; no new `innerHTML`.

### Strengths
- The conflict, loss-count and matched-count tests reproduce the three stuck-session paths from the branch review against the real bridge, and each mutant restores the failure (the 8 s hang) rather than a mere assertion.
- The family test compares Studio's gate with the live bridge's verdict row by row instead of re-stating Studio's regex.
- The composition barrier test checks both ordering and the final ledger, not only that messages were sent.

### Issues
#### Critical
None.

#### Important
None.

#### Minor
- 1. The size-probe cache relies on every row, id or seeded-draft change being followed by a render (`renderedRoleRows` is in the key; `roleView.ids` and `seedRoleDrafts` are not). I could not construct a stale case, but a future caller that changes `roleView.rows` without rendering, or seeds a displayed row's draft without bumping `roleDraftVersion`, would return a stale Apply state. One short comment at the cache or a version bump inside `seedRoleDrafts` would make it robust.
- 2. Nothing asserts the cache itself (one probe per keystroke); the dispatch asks only for the no-rebuild check, which exists. Optional.
- 3. The 10,001 page's forged Detect (discussed above) is test-only and uses `window.__fontkitBridge` fields; acceptable, but the test name says "real" for the whole flow, which is true only of Apply and the receipt.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** Each of items 1-8 is implemented as specified and pinned by a test that fails when the fix is reverted (nine mutants killed, both focused gates green: 195 and 46 tests). Studio's outcome limits now equal the bridge's exactly and the real-bridge conflict recovers at once; only three optional Minor notes remain.

**Verdict:** Approved

STATUS: COMPLETE
