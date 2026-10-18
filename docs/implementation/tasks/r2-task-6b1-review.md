### Spec Compliance
- PASS: message shape. sendRolePage posts {type, documentId, pageVersion, pageURL}; `post` (fontkit-bridge.js:1112-1117) adds protocolVersion and sessionId, so the wire has exactly the six keys. The content test asserts `set(message) == KEYS` with the session `s1`, protocolVersion 1 and the ready's documentId (test_role_route_bridge.py ~L302-305).
- PASS: pinned session and origin only. It goes through `post` (studioSource, studioOrigin). scheduleRolePage and sendRolePage return unless studioSource is pinned and not disposed. The sibling-frame test shows an evil-origin hello installs nothing and the evil window hears nothing.
- PASS: null URL (D061). `pageURL: this.rolePageURL()` is null for a URL over 2,000 characters. The test asserts null, then the supported URL inside the hold.
- PASS: does not mutate roles or the revision. sendRolePage only reads, refreshes and posts. The test with an applied preview checks the owned sheet, the size, the revision and a re-greeted roleState. I mutated the send path to bump `revision` and to call `removeRoleSheet()`; both were killed by that test.
- PASS: owned places only. The cached diff has 8 hunks (constant, fields, dispose, handleHello, noteRoleMutations, observeRolePage, refreshRolePage plus the new methods). `dropSession` and `cancelRoleJobs` are untouched.
- PASS: budget. Bridge +99/-2 (budget about 170). Test module 547 lines (budget about 650).
- PASS: deviation 1 (the record is `{epoch, cancel}`, not `{epoch, raf, timers}`) is recorded. It is behaviourally equivalent. Deviation 2 (no `npm ci`) follows the dispatch.
- FAIL (see Important 1): "In-flight Detect unchanged and not cancelled by the message" has no killing test. The report's claim that the `cancelRoleJobs` mutant is unobservable is wrong.
- CANNOT VERIFY FROM DIFF: firefox and webkit. I ran chromium only (`FKS_ENGINES` default). The module loops over `ENGINES` and contains no skips, so a hosted engine run would execute it.

### Checks run
- Checklist 1 (drift). Read the contract table (plan 807) against `sendRolePage`. The six keys match and nothing else is sent. `post` stamps the pinned `studioSource`/`studioOrigin`. Null URL passes through `rolePageURL()`. Mutants `send_revision` and `send_removes_sheet`, run via `RoleBridgeCase.open(bridge_source=...)` with an in-memory copy, were each KILLED by `test_a_history_push_under_an_applied_preview_leaves_the_roles_unchanged` (`2 != 1`; `([], '16px') != ([PLAIN_24], '24px')`).
- Checklist 2 (schedule invariant). I walked every path.
  - `bumpRolePage` calls `scheduleRolePage`. It returns while a record exists or a hold is set, and the hold expiry picks the change up.
  - The send refreshes first, so a pending URL or viewport change is folded in. Its own bump is a no-op for scheduling because the record stays set until the `finally`.
  - It posts only if the version differs, then sets `announcedVersion` and starts the hold. With no post, no hold starts.
  - The hold expiry refreshes (a URL or viewport change made during the hold bumps and schedules a record). It then explicitly schedules if a DOM bump during the hold left the version ahead with no record. That second branch is not redundant, and a mutant removing it is killed (below).
  - Re-hello: an older-epoch record is cancelled in `scheduleRolePage` or ignored in `sendRolePage`. `handleHello` sets `announcedVersion` after the ready. The hello's own refresh may leave a record that no-ops.
  - dropSession: `studioSource` is null, so schedule and send return. dispose: cancels the record and hold, and every path also checks `disposed`.
  - No lost or duplicate announcement found. The worst latency is hold + rAF + setTimeout(0), or +250 ms with no paint, as the brief allows.
- Checklist 3 (history wrappers). Read `installRoleHistory` and `removeRoleHistory`. Own `enumerable:true` properties. The wrapper uses `Reflect.apply(original, this, args)` and returns `out`. Scheduling sits in its own try/catch. A native throw propagates before scheduling. There is one try/catch per method with the descriptor saved before each define. `observeRolePage` returns early on a second hello, so there is one install. Removal checks `history[name] === wrapper`, then restores the saved descriptor or deletes. The tests cover each case: receiver and state, the three native exceptions, install once, a frozen `history`, an app-owned descriptor, a later app wrapper after dispose, and own names back to native. Execution passed for these (report A/D; test_support rerun by me OK, 34 tests).
- Checklist 4 (mutants, reproduced myself with the in-memory loader, bridge SHA-256 unchanged e5aaec07... before and after every run).
  - `expiry_no_refresh` (hold expiry compares versions without `refreshRolePage`): KILLED by the hold test (push, resize and hash: `[] != [...]`).
  - `expiry_no_schedule` (drop the explicit trailing schedule): KILLED by the stream-rate test (`200 != 161`).
  - `no_send_refresh` (send does not refresh first): KILLED, 5 failures in the URL-only test.
  - `send_revision` and `send_removes_sheet`: KILLED (above).
  - `send_cancels_jobs` (the report's survivor): the existing 12b test SURVIVES, as the report says. My own scratch test KILLS it (see Issue 1). My probe, `scratchpad/test_6b1_probe.py`, passes on the real bridge (roles-page, then `design:detected` complete, 260 ms scan) and ERRORs on the mutant (`reply timed out`).
- Checklist 5 (fake versus real). Every test uses the real bridge in a real page through `RoleBridgeCase.open`. The evil-origin hello test exists (`test_a_hello_from_a_sibling_frame_installs_nothing_and_it_hears_nothing`) and asserts both that history stays native and that `received == []`.
- Checklist 6 (hidden skips). `grep -i "skip|expectedFailure|continue"` on the test module: none. The report's command C ran with `FKS_REQUIRE_FIXTURES=1` and no skips. No new test would be skipped by hosted CI. The only gap is that the new tests never ran under firefox or webkit.
- Checklist 7 (tests).
  - Every test has a G/W/T docstring. Expected values are literals (URLs, `Author body`, `SPA detail evidence`, ...) or come from the ready or a Detect, never from the code under test.
  - The only fixed sleeps are short waits that prove absence (300 to 600 ms), the 50 ms in-hold offsets the brief prescribes, and 400 ms before-hello absence checks.
  - Most tests have a recorded mutant (report table). Without a distinct mutant of their own: `spa_clicks` (brief says none by design), `clear`, `inspector edit` and `native focus and hover` inside the quiet-writes test (carried by the `apply` and `detect under a preview` subtests, as Revision 3 M2 allows), and 12b (Issue 1).
- Checklist 8 (code).
  - The known cached-native-method limit is stated in the comment above `installRoleHistory` (fontkit-bridge.js ~L1352 in the diff).
  - The `fired` guard now exists twice (`measureRoleReceipt`, `scheduleRolePage`), which is not a third copy. The brief asked for the copy.
  - Comments explain why. `node --check`, ruff (`tests/test_role_route_bridge.py`: All checks passed), `git diff --cached --check` (rc 0) and `test_support` (OK) were clean at HEAD of the frozen worktree.
  - Line endings: the report says the working-tree bridge is CRLF, but at the worktree it has 0 CR bytes and BASE has 0. It is LF, as the constraints require. The report note is wrong but harmless.

### Strengths
- The schedule is small and correct: one record, one hold, a trailing edge that refreshes before comparing, and an explicit schedule for DOM-only bumps in the hold.
- The test oracle uses the Detect reply's `pageVersion` as an independent link, and literal URLs.
- The two-sided mutants for the install and removal (assignment versus defineProperty, unconditional versus conditional restore) are all killed.
- The hold-expiry and stream-rate tests really pin the trailing edge; I confirmed both mutants.

### Issues
#### Critical
(none)

#### Important
1. The `cancelRoleJobs`-in-send mutant is killable, so it is a test gap, not a protocol limit. The report says the stale reply always posts first, so the mutant "is not killable here". That holds only for a change made after the scan starts. Make the change first and start the Detect before the rAF fires. The Detect's own refresh captures the new `pageVersion`, so the scan is not stale. The pending send then fires mid-scan with the version differing from `announcedVersion`, posts a `roles-page`, and the mutant's `cancelRoleJobs` kills the in-flight scan.
   - The brief requires this ("In-flight Detect. Unchanged and not cancelled by the message"), and the 12b test (`test_a_push_during_a_multi_slice_scan_keeps_the_stale_reply_and_sends_the_notice`) does not guard it.
   - Probe (passes on the real bridge, errors on the mutant): on `LARGE` after hello and `design:mode` interact, `frame.evaluate("document.body.firstElementChild.setAttribute('data-t6b1','1')")`, then immediately `page.evaluate('() => { window.pending6b1 = request({type:"design:detect"}); }')`, then `reply = page.evaluate('() => window.pending6b1')`. Assert `(reply['complete'], reply['reason']) == (True, None)` and `[m['pageVersion'] for m in self.messages(page,'design:roles-page',start)] == [reply['pageVersion']]`. Observed on the real bridge: order `[roles-page, detected]`, scan 260 ms, versions equal.
   - Fix: add this test, with the mutant recorded as killed. Until then, 12b's docstring "keeps the stale reply" is true but does not catch the regression it is named for.

#### Minor
1. The quiet-writes test hosts five subtests, but only `apply` and `detect under a preview` were shown to fail under a mutant. `clear`, `inspector edit` and `native focus and hover` depend on the same `isOwnedRoleMutation` mutant only through shared code. A different mutant (for example, a bridge that bumps on focus) would not be caught for the last one. Acceptable under Revision 3 M2; noting it.
2. The wrapper is an anonymous-looking `function (...args)` assigned to `const wrapper`, so `history.pushState.name` becomes `wrapper` and `.length` becomes 0 (native: `pushState`, 2). The brief only requires receiver, arguments, return value and exceptions. A one-line `Object.defineProperty(wrapper, 'name', ...)` would be tidier but is not required.
3. The report's Notes say the working tree is CRLF; it is LF. Correct the note before it is copied into the landing bookkeeping.

### Plan-mandated (for the owner)
(none)

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The implementation and most tests are sound: the schedule invariant holds on my walk and every mutant I reproduced was killed, except that one realistic regression (the send path cancelling an in-flight Detect) passes the suite. The report calls that mutant unobservable, but a change made before the Detect starts kills it with a short test (Important 1).

## Scoped re-review 1

### Spec Compliance
- PASS (Minor 2): the wrapper line is `for (const key of ['name','length']) Object.defineProperty(wrapper, key, { value: original[key], configurable: true })` (fontkit-bridge.js:1378, inside the existing try, before the wrapper is installed).
- PASS (Minor 2): the assertion sits after the first hello, where `window.kept` and the native `[name, length]` (read from `History.prototype` before hello) are both in scope (tests/test_role_route_bridge.py:371-377). Docstring Then matches the assertions.
- PASS (Minor 3): the report's note now states what was measured; confirmed by byte count (below).
- PASS (fix scope): the two patches differ in exactly the hunks named below; nothing else changed.
- FAIL (Important 1): the new test kills the `cancelRoleJobs`-in-send mutant only about 85% of the time on this machine, and the kill depends on scan speed (see Issues).

### Checks run
- Patch diff (`diff task-6b1-code.patch task-6b1-code-r1.patch`): changed hunks are (1) the bridge hunk header +93 to +94 lines and the one added `for (const key of ['name','length'])` line; (2) the wrapper-test docstring Then clause; (3) wrapper test: 3 added lines (native name/length read plus names assert, and the installed-functions assert); (4) the new test `test_a_detect_started_before_the_announcement_is_sent_...` (+15 lines, 547 to 565 lines). The rest is index-hash and line-count header changes. No other behaviour changed.
- Minor 3 -> Python byte count in C:/fks/t6b1 -> working-tree bridge 214871 bytes, 4414 CRLF, 4414 LF; index blob 210457 bytes, 0 CR, 4414 LF; BASE blob 0 CR; r1 patch 48397 bytes, 0 CR. SHA-256 of the index blob converted to CRLF equals the working-tree hash (44b6f54c...). `git ls-files --eol`: i/lf w/crlf for the bridge, i/lf w/lf for the test; `core.autocrlf=true`. Note now true. (A bash `grep -c` printed 0 on the CRLF file, which is how the first review misread it.)
- Important 1, real bridge -> in-memory runner `scratchpad/m6b1rr.py none <test>` x4 -> OK x4 (3.4-3.6 s). Bridge SHA-256 unchanged before and after.
- Important 1, mutant -> `m6b1rr.py send <test>` (cancelRoleJobs added after `announcedVersion = ...` in sendRolePage) x6 -> ERROR `KeyError: 'complete'` x6. Red, though as an ERROR at `reply['complete']` rather than a clean assertion failure.
- Important 1, kill rate -> same mutant, 15 tests in one process (`loop6b1rr.py`) -> 13 killed, 2 survived. A second, independent 20-run loop with the same body (`loop6b1rr2.py`) -> 18 killed, 2 survived. Combined 4 survivors in 35.
- Important 1, cause -> frame probe (`test_6b1rr_probe2.py`, rAF wrapper plus a timeOrigin-based clock, 15 runs). The Detect always starts before the announcement (rAF fires 253-389 ms after the Detect message is received; never before). But the roles-page is not sent until about 250 ms into the Detect (the 250 ms fallback or a late rAF), and the Detect reply arrives at 253-394 ms. The kill only happens when the scan outlasts the send; when the scan ends at about 250 ms or earlier the cancel finds nothing to cancel.
- Important 1, G/W/T -> read the test (L696-710). Then = reply complete, no reason, exactly one roles-page carrying the reply's pageVersion; assertions = `(type, complete, reason) == ('design:detected', True, None)` and `[pageVersion] == [reply['pageVersion']]`. They match (the extra `type` check is harmless).
- Minor 2, mutants -> `names` (line removed): `[['wrapper',0],['wrapper',0]] != [['pushState',2],['replaceState',2]]` FAILED. `lenonly` (name only kept): length 0 != 2, FAILED. `nameonly` (length only kept): name 'wrapper' != 'pushState', FAILED. Real bridge x3: OK.
- Untouched: fontkit-bridge.js unchanged by me (SHA-256 44b6f54c... before and after); `git status` unchanged (M bridge, A test).

### Strengths
- The wrapper-name fix is correct and two-sided: both name and length are asserted, and removing either half is killed.
- The new test is deterministic on the real bridge (4 of 4 here, and the report's 5 of 5), and the Detect demonstrably starts before the announcement's frame in every probed run.
- The report's Minor 3 correction is accurate, with a hash proof.

### Issues
#### Critical
(none)

#### Important
1. `tests/test_role_route_bridge.py:696-710`: the new test does not reliably kill the mutant it was added for. 4 of 35 mutant runs survived (green with the regression present). The roles-page goes out about 250 ms after the DOM change (rAF is starved during the scan, so the 250 ms fallback fires), while the Large-page scan lasts 253-394 ms here. The scan has to outlast the send for `cancelRoleJobs` to have anything to cancel. On a faster machine or a faster hosted runner the scan can end before 250 ms, and the test would then pass with the regression present. The Detect-before-frame ordering is deterministic; the scan-outlasts-the-send condition is not asserted or forced. The report's "Mutant: RED" holds on a single run, but the guard is probabilistic.
   - Fix: lengthen the scan inside the test so that it clearly outlasts 250 ms, for example by appending a few thousand more elements to the frame before the Detect (the added DOM change folds into the same announcement). Or assert a precondition, such as the roles-page arriving before the reply, so a too-fast scan fails loudly rather than silently passing. Then re-run the mutant 20 or more times; the target is 0 survivors.

#### Minor
(none new)

### Plan-mandated (for the owner)
(none)

### Assessment
**Task quality:** Needs fixes
**Reasoning:** Minor 2 and Minor 3 are fixed and verified, and the diff between the patches shows no other change. The Important 1 test passes reliably on the real bridge but kills the cancelRoleJobs mutant only about 85% of the time, because the scan barely outlasts the 250 ms fallback send. A guard that silently goes green under the regression on a faster machine is not yet a true red.

## Scoped re-review 2

### Spec Compliance
- PASS (kill rate): the test is red on every mutant run and green on every real-bridge run (12 of 12 each, below).
- PASS (precondition): the arrival order of roles-page and detected is asserted from the raw host log, `assertEqual(order, ['design:roles-page', 'design:detected'], 'the scan ended before the announcement was sent, so the test cannot tell a cancelled Detect from a finished one')` (tests/test_role_route_bridge.py, new test, `order` assertion). A scan that ends before the send makes the order `[detected, roles-page]` and fails with that message, so the test cannot pass vacuously.
- PASS (budget): 9,000 elements (5,000 + 4,000), under the 10,000 `eligible` limit (fontkit-bridge.js:1856); Detect complete:true in 498-571 ms against the 2,000 ms budget (fontkit-bridge.js:1853). Margin 3.5x at the slowest run.
- PASS (stand-in): see Checks.
- PASS (G/W/T and scope): Then = assertions; fix changed only this test (hunks named below).

### Checks run
- Real bridge, repeated -> `loop6b1rr2.py none 12` (cwd C:/fks/t6b1, FKS_ENGINES=chromium, one process, one fresh test run per iteration) -> 12 OK, 0 FAIL, 0 ERR.
- Mutant, repeated -> `loop6b1rr2.py send 12` (in-memory `this.cancelRoleJobs()` after `this.announcedVersion = this.pageVersion;` in sendRolePage, injected via `RoleBridgeCase.open(bridge_source=...)`) -> 0 OK, 12 ERR. All 12 logs hold `Page.wait_for_function: Timeout 6000ms exceeded` (the cancelled Detect never replies), and none lacks `wait_for_function`, so each is the intended kill and not a setup error. Red is an ERROR (timeout after 6 s), not a clean assertion failure.
- Timing -> `probe6b1rr2.py 12` (same body; a host `message` listener records Date.now() deltas from the synchronous dispatch) -> roles-page at 34-46 ms; Detect reply at 498, 553, 515, 571, 503, 557, 552, 560, 547, 566, 554, 555 ms (min 498, max 571); complete True and scannedElements 9000 in all 12. The roles-page lands 450-535 ms before the reply, so it is mid-scan with wide margin, and the announcement is not a fallback-timer send.
- Margin on a slower machine -> 2000/571 = 3.5x, above the 3x threshold. On a machine more than about 3.5x slower the real bridge returns an incomplete Detect and the test goes red loudly on the `complete` assertion, not green. Not flagged.
- Stand-in -> read fontkit-bridge.js:794 and 1112-1196. The listener is `this.listen(window, 'message', e => this.handleMessage(e))`; the synthetic event goes through `handleMessage`, then `isFromSession` (`event.source === this.studioSource`, `event.origin === this.studioOrigin`, `data.sessionId === this.sessionId`). The test uses `source: parent` (the host that sent hello), origin `http://studio.test` and the host's real `window.sessionId`. The reply (`complete:true`, posted to the host through `studioSource.postMessage`) proves the checks passed. This is the normal handler, not a bypass. It is the same pattern as HELLO_S2 (test file L470). The only difference from a real Studio message is task timing, which the test needs.
- Ordering inside the frame task -> read the evaluate body: `setAttribute`, `await Promise.resolve()` (MutationObserver microtask bumps the version and schedules the rAF), then the dispatch. The rAF cannot run between them, so the Detect starts after the change and before the send, deterministically.
- The 600 ms wait after the 4,000-element append lets that change's own announcement settle before `start` is marked; the post-mark roles-page count (`[pageVersion] == [reply.pageVersion]`) therefore counts only the data-t6b1 announcement.
- Patch diff -> `diff task-6b1-code-r1.patch task-6b1-code-r2.patch` -> hunks: (1) index/line-count headers (565 to 576 lines); (2) the docstring of `test_a_detect_started_before_the_announcement_is_sent_finishes_complete_and_is_not_cancelled`; (3) its body (+4 lines appending 4,000 `<p>` and the 600 ms wait; the 3-line setAttribute/request/read replaced by message build, the frame task, `wait_for_function` and the `find` read; +2 lines for `order` and its assertion). No bridge hunk, no other test touched.
- Integrity -> bridge SHA-256 44b6f54c5b52 and `git status` (M bridge, A test) unchanged after all runs. Scratch: `loop6b1rr2.py`, `probe6b1rr2.py` in the session scratchpad; logs `work/6b1rr2.*.log` in C:/fks/t6b1/work (git-ignored).

### Strengths
- The kill no longer depends on scan speed: the Detect-before-send order is forced in one frame task, and the scan is about 10x longer than the send delay (about 40 ms), so the mutant is killed 12 of 12 here, and a too-fast scan fails with a named message.
- Docstring Given/Then now matches the assertions, including the order.

### Issues
#### Critical
(none)
#### Important
(none)
#### Minor
1. The mutant is detected as a 6 s `wait_for_function` timeout error rather than an assertion failure, so a kill costs 6 s and the message names no cause. The order assertion is also unreachable on a cancelled Detect. Acceptable; a clearer message would need a bounded wait that returns a value. Not required.

### Plan-mandated (for the owner)
(none)

### Assessment
**Task quality:** Approved
**Reasoning:** The re-review finding is closed: the mutant is killed 12 of 12 (the 85% figure is now 100% on this sample), the real bridge passes 12 of 12, the scan takes 498-571 ms against the 2,000 ms budget, and a loud precondition prevents a vacuous pass. Only the test hunk changed.
