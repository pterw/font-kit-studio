# PR B review fixes, bridge side: independent review (2026-10-16)

Patch task-prb-bridge-code.patch sha256 3040b2cc... equals the staged tree in C:/fks/t26 (git diff --cached | sha256sum = 3040b2cc6639d06e; HEAD 2ba1e77). t26 was not edited. Mutants and variants ran only through RoleBridgeCase.open(bridge_source=...) (mutate_t26rev.py, probe_t26rev.py in the session scratchpad). ASCII only.

### Spec Compliance
- PASS (with a deviation to decide, item 1): F3 transition baseline. Test and probes show the exact 16px baseline with a live 30px preview on a page with `transition: font-size .2s linear`, no new group, 30px restored with no running animation.
- PASS: Item 2 (F4) control-character selectors are unnamed (`{null, complex-cascade}`); table row `p.a\85`; both the full filter and the C1 range are pinned by mutants.
- PASS: Item 3 (CR7) listener writes from `design:order-changed` advance pageVersion, the bridge's own reordering does not (details below).
- PASS: Item 4 (CR9) `postRoleReceipt(..., refreshed)` skips the second stylesheet serialization at the two call sites that directly follow `roleJobFresh`; behaviour unchanged (all receipt tests pass). The change is pure performance; mutant `refreshed_skip` survives, which is expected for a no-behaviour change.
- PASS: Item 5 (CR10) one module-level `ROLE_LOSS_REASONS` and `compareRoleLosses` serve `measureRoleOutcomes` and `fitRoleReceipt`; reordering the reasons fails the grouping/order test.
- PASS (with one hole, Minor 2): Item 6 (D066, Addendum 14) fonts status is out of the stamp and moves only `roleNative`.

### Checks run
- Focused set (Chromium): test_role_stylesheet test_role_preview test_role_protocol test_role_detection test_bridge_runtime.HandshakeTests test_support -> Ran 123 tests, OK (157.6 s). APPLY_THEN_DETECT elapsedMs 802.7, complete, 5,000 scanned, 49 frames, heartbeat 89->138.
- D058 timing (probe, large 5,000-parent page, Chromium): first scan 278 ms (5,000 scanned); Detect with a live preview 667 ms, complete (limit 2,000; unchanged). The R2.T1 rewrite removed the FIRST_SCAN print; the first-scan assertion test passes.
- Item 1 variants through the seam, same page and fixtures:
  - current patch (ban for the whole scan): baseline [16], live Detect 667 ms complete, 5,000 scanned.
  - no ban (`noban`): baseline [30] (the F3 bug reproduces), live Detect 612 ms.
  - per-batch alternative (ban installed with the sheet toggle, then re-enable, flush with `getBoundingClientRect`, remove the ban inside the same batch; `perbatch`): baseline correct ([16], no replay), but the live Detect on the 5,000-parent page returned `time-budget` after 2,038 ms with only 64 elements scanned (incomplete). It also reproduces the writer's 58-element figure. Infeasible at this cost.
  - running transition at scan start (color 3 s transition, 400 ms in; Detect during it): with the ban there is no `transitioncancel` event and the transition keeps progressing (rgb 33 -> 34 -> 76 -> 255 in step with the no-ban run). Same on the large page with a 344 ms scan: 250 `transitionrun`, 0 cancel, colour progress normal. So in Chromium the ban suppresses only transitions that would START during the scan; running transitions are not cancelled.
  - a page that throws inside the scan (`document.createTreeWalker` patched after a preview exists): the ban `<style>` stays installed afterwards (ban_left true) while the owned sheet is enabled again.
  - global reset sent in the middle of a scan with a live preview: ban removed with the current code; with the `releaseRoleQuiet()` call removed from `cancelRoleJobs()` (mutant `release_in_cancel`/`nocancel`) the ban stays (ban_left true) and no test notices.
- Mutants against SplitPageVersionTests + test_role_preview + TransitionBaselineTests (each restored by construction, bridge served from memory):
  - killed: fonts.status back in the stamp (commit test), font events not moving the epoch (scan test), ban not installed, no flush on release, control-character filter removed, C1 range removed, own writes not settled before the order-changed dispatch, listener writes not counted after it, `releaseRoleQuiet` not called in `finish`, reasons reordered.
  - survived: `loading` removed from the font event list (equivalent: `loadingdone`/`loadingerror` still stale the scan), `releaseRoleQuiet` removed from `cancelRoleJobs` (untested, see Minor 1), `refreshed` skip (no behaviour).
- Flake check: the font scan test 10/10 and the font commit test 10/10 (two concurrent loops of 5 each).

### Item 1: the transition ban stays for the whole scan (decision)
**Verdict: ACCEPT the deviation, record it, and tighten two points.**

What it changes, measured above: Addendum 9's rule is about the owned role sheet, and that rule still holds exactly: `sheet.disabled = true` is undone in the batch `finally` before every yield, so a paint never sees the preview sheet disabled. What is new is a second bridge-owned `<style>` carrying `transition: none !important` that persists between batches until `finish`, `cancelRoleJobs` or `dispose`. While it is on, transitions that would START (hover, class toggles by the app) are instant instead of animated. Running transitions are not cancelled in Chromium (probe), contrary to the writer's stated limitation. The window is the scan (about 0.3 s on the 5,000-parent page, tens of ms on ordinary pages, never over 2 s), Detect is an explicit user action, and any native pointer or focus event during a scan ends the scan as page-changed on its next slice, which releases the ban. The ban is bridge-owned (in `roleOwned`, so it is not an author mutation and is excluded from the stamp and from author-rule collection).

Why not per batch: a transition-free restore needs the preview flushed back under the ban before the ban is removed, and that flush forces a full style and layout pass per 8 ms slice. Measured: 64 elements in 2.0 s (time-budget, incomplete) on the 5,000-parent page, versus 667 ms with the whole-scan ban. Reading the baseline "without toggling" is not available: any cascade-excluded read needs the sheet disabled or a second document; reading the transition's end value from `getAnimations()` would instead start a visible preview-to-baseline-and-back transition, which is worse for the user than the ban.

Trade-off for the owner, stated plainly: (1) the app's new transitions are suppressed for the duration of an explicit Detect, an effect visible only if something transitions during that window; (2) the bridge inserts and removes a `<style>` in head on every Detect that has a live preview, which page MutationObservers or style-scanning libraries can see (the owned role sheet already does that on Apply); (3) a CSP that forbids inline style would silently drop the ban and the baseline would be preview-contaminated, but such a page cannot hold a live preview in the first place. Accepted because correctness of the baseline evidence is the point of Detect and the cheaper per-batch design is not feasible.

Required with the acceptance: record the deviation (Addendum 9 and the CHANGELOG sentence "Detection keeps measuring the app's own styles" should say that transitions are suppressed while a scan with a live preview runs), and correct the report's limitation (running transitions are not cancelled in Chromium; other engines were not run, and the CSS spec says cancellation may occur). Recommended, not required: install the ban only when the page can transition at all (for example when the style stamp already contains `transition`, or `document.getAnimations()` shows transitions), so pages without transitions see no head mutation and no change.

### Item 2: font loading and the wire version
- `document.fonts.status` is out of `roleStyleStamp`; `loading`, `loadingdone` and `loadingerror` listeners on `document.fonts` (registered through `listen`, so `dispose` removes them) move only `roleNative` when active with a session. No other code reads `document.fonts` (grep).
- Slip-through channels checked: a held author `@font-face` released after the apply commit (the test: second apply and clear with the receipt's version accepted, revisions 2 and 3); the viewport and stylesheet parts of the stamp are unchanged, so a real `@font-face` rule insertion or a bridge font link still behaves as before (author sheet counts, bridge link excluded); a `FontFace` added from script moves only the epoch. I found no route by which a font load advances the wire version.
- Staleness tests: the commit test fails when `fonts.status` returns to the stamp, the scan test fails when the epoch listener is removed, and the scan test carries a premise (font `loading` time within the first half of a calibrated scan, ladder 0.3/0.2/0.1, failure message), 10/10 stable.
- Note (accepted by D066): a role that names a not-yet-loaded font will normally get a stale receipt, because the load starts during the post-commit measurement and moves the epoch; the next Apply or Clear is accepted, which is the intent.

### Item 3: order-changed listener writes
`applyWireframeMovement` now settles the bridge's own writes immediately before `window.dispatchEvent(new CustomEvent('design:order-changed'))` and counts whatever the listeners wrote right after (`noteRoleMutations(takeRecords())`), so the end-of-handler settle cannot drop them. This is the only author-facing event in the bridge besides `options.onApplied`, which was already handled (grep: one `dispatchEvent`, one `options.on*`). The test covers both halves: the bridge's own reorder leaves the version unchanged; with a listener that appends a node, an apply carrying the earlier version is rejected `page-changed` and the page stays 16px. Both ordering mutants fail it. CORRECT.

### Strengths
- The F3 fix is exact on the tested page and leaves no running animation or stray `<style>` behind in the normal exits.
- Item 6 is minimal: one epoch listener set, one stamp field removed, nothing else touched, and both behaviours (commit not stale on the wire, scan stale with equal versions) have real-bridge tests with premises.
- Duplicate loss ordering is now genuinely one comparator.

### Issues
#### Critical / Important
(none)

#### Minor
1. **The ban's lifetime is not exception safe and the cancel path is untested.** `releaseRoleQuiet()` is called from `finish`, `cancelRoleJobs` and `dispose`, but the detect `run` loop has no try/catch: if `iterator.next()` throws (probe: a page patching `document.createTreeWalker`), `finally` restores the owned sheet but the ban stays on, and no reply is sent, until the next Detect or reset. The report's claim "no exit leaves it behind" is therefore not true for an exception. Also the `cancelRoleJobs()` release (reset or re-hello during a scan) is correct (probe) but unpinned: removing it survives all tests. Fix: release in a `catch` (rethrow) around the batch, and add one test: live preview, start a scan on the large page, send a global reset, expect no `transition: none` style afterwards (the probe is a ready template).
2. The report's limitation "a page transition already running when Detect starts is cancelled while the ban is on" does not hold in Chromium (no `transitioncancel`, progress continues, probes above). Correct the sentence; Firefox and WebKit were not run.
3. Test docstring and premise notes only: `test_detect_with_a_live_preview_...` asserts `getAnimations().length == 0` after the 30px wait, which also proves no replayed transition; fine. No other findings.

### Plan-mandated (for the owner)
- [Minor] Addendum 9 ("restoring it before yielding"; "never leave the owned sheet disabled across a task, a timer or a paint") and the CHANGELOG sentence do not mention the bridge-owned transition ban that now spans the scan. The implementer did not follow the fix brief exactly (it asked for the ban inside the same batch), so this is a recorded deviation rather than plan-mandated; the owner should amend the plan text as stated under Item 1.

### Assessment
**Task quality:** Approved with fixes
**Reasoning:** All six items are implemented and the focused set passes (123 tests, Apply-then-Detect 803 ms, live-preview Detect 667 ms); the whole-scan transition ban is an acceptable, measured deviation (the per-batch design takes the 5,000-parent scan from 667 ms to a 2 s time-budget failure, and running transitions are not cancelled in Chromium), and font loading cannot reach the wire version. Before landing, make the ban exception safe and pin its cancel-path release with a test, and amend the plan and CHANGELOG wording and the report's limitation sentence.

**Verdict: Approved with fixes**

STATUS: COMPLETE


## Scoped re-review (fix round 1)

Patch task-prb-bridge-code-r1.patch sha256 aa4e7270... equals the staged tree in C:/fks/t26 (git diff --cached | sha256sum = aa4e7270a65558fa). t26 not edited; mutants through the open() bridge_source seam (mutate_t26rr1.py, scratchpad). ASCII only.

### Interdiff (task-prb-bridge-code.patch -> task-prb-bridge-code-r1.patch)
Item 4, nothing else changed: CONFIRMED. The bridge change is one `thrown` flag, `} catch (e) { thrown = true; } finally { restore(); }` and `if (thrown) { finish('page-changed'); return; }` in the detect batch. The tests change only in test_role_detection.py (three new tests and a `ban_nodes` helper in `TransitionBaselineTests`); test_role_stylesheet.py and test_role_preview.py differ only in hunk offsets.

### Item 1: a throw mid-scan
- Behaviour: the page that patches `document.createTreeWalker` now gets `design:detected` with `complete: false`, `reason: 'page-changed'` (previously no reply at all), the owned sheet is restored by `finally`, and `finish` releases the ban first, so no ban style is left and the preview still renders 30px. The test asserts all of that. Without the catch the test errors (mutant `no_catch`).
- Is page-changed the honest reason? Acceptable. The reply's closed set is time-budget, element-limit, group-limit, variant-limit, identity-limit, reply-limit and page-changed. The limit reasons would be false (nothing was exceeded); identity-limit says an author identity was invalid, which is also false. `page-changed` is the only reason that means "the evidence from this scan cannot be trusted; run a fresh Detect", and it makes Studio show the stale status and offer a new Detect without storing anything (Only complete current results enter the checked inventory). A new reason would break the contract. Cost: a page that throws every time gets "page changed" on every Detect.
- Request (Minor 1): the catch swallows the error silently. Other bridge catches log with `console.warn('[FontKitBridge] ...')`; do the same here so the cause of a repeated page-changed is diagnosable.

### Item 2: cancel-path release test
`test_a_reset_during_a_scan_removes_the_transition_ban_at_once` (live preview on the large page, wait for the ban node mid-scan, global reset, assert no ban node). Mutant with `this.releaseRoleQuiet()` removed from `cancelRoleJobs()` (`no_cancel_release`) fails it: 6 of 6 runs, so the kill is reliable. The test itself passed 6 of 6. Residual risk (Minor 2): if the page round trip is slower than the whole scan (about 0.7 s) the ban would already be gone and the assertion would pass without proving the cancel path; `wait_for_function` makes that unlikely and the mutant kill was stable, so no change is needed.

### Item 3: no preview, no ban
`test_the_transition_ban_is_installed_only_while_a_preview_is_live` counts inserted ban nodes with a MutationObserver: 0 for a Detect with no preview, 1 and none left over after a Detect with a preview. The code path is `suspendRoleSheet`, which returns before touching the ban when there is no enabled owned sheet. A mutant that installs a ban node when there is no sheet (`ban_without_preview`) fails this test (and, incidentally, the baseline test). CORRECT.

### Checks run
- Focused set (Chromium): test_role_stylesheet test_role_preview test_role_protocol test_role_detection test_bridge_runtime.HandshakeTests test_support -> Ran 126 tests, OK (153.4 s). APPLY_THEN_DETECT elapsedMs 701.7, complete, 5,000 scanned, 44 frames, heartbeat 85->129 (limit 2,000; report: 765.5).
- Mutants (TransitionBaselineTests): no_catch -> 1 error; no_cancel_release -> 1 failure; ban_without_preview -> 2 failures.

### Issues
#### Critical / Important
(none)

#### Minor
1. The new `catch (e) { thrown = true; }` swallows the exception without a log line (see Item 1). Add a `console.warn` with the message.
2. The reset-during-scan test depends on landing the reset inside the scan; stable here (6/6 pass, 6/6 kill), see Item 2.

### Assessment
**Task quality:** Approved
**Reasoning:** The throw path now releases the ban, ends the job with the existing page-changed reply (the most honest reason in the closed set), the cancel-path release and the no-preview condition each have a test that kills its mutant, the interdiff contains nothing else, and all 126 focused tests pass. Only a log line in the new catch is left to add.

**Verdict: Approved**

STATUS: COMPLETE (re-review)
