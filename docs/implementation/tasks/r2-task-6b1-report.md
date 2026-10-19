# R2.6B1 code report (MODE: code, worktree C:/fks/t6b1, BASE bd20e43)

## Changed
- `fontkit-bridge.js` (+99/-2, budget 170): `ROLE_PAGE_GAP_MS`; fields `announcedVersion`, `rolePageRec`, `rolePageHold`, `roleHistory`;
  `bumpRolePage`, `scheduleRolePage`, `sendRolePage`, `expireRolePageHold`, `installRoleHistory`, `removeRoleHistory`; `dispose`,
  `noteRoleMutations`, `refreshRolePage`, `observeRolePage` (install + popstate/hashchange/resize via `listen`), `handleHello` (one line).
- New `tests/test_role_route_bridge.py` (547 lines, budget 650; 31 tests, all with Given/When/Then docstrings).
- Patch: `task-6b1-code.patch` (2 files; `git apply --check -R` passes).

## Brief steps
All done. Deferred to landing: bookkeeping (see Handoff). Deviations:
1. The pending record is `{epoch, cancel}` (one closure cancels the rAF and both timers), not `{epoch, raf, timers}`; no extra method needed.
2. Command C was run WITHOUT `npm ci` (dispatch: fixtures are junctions, never rewrite node_modules); `FKS_REQUIRE_FIXTURES=1` was set.
3. Requirement 4 folded into the content test (brief M6). Requirement 5's version link: "ready link" mutant is killed by the URL-only
   route test (a URL-only change has no earlier bump), not by the content test (the observer had already bumped).

## RED at BASE (genuine) and GREEN
RED: `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_role_route_bridge` at BASE with the bridge unchanged
(SHA-256 913a4d0b27f45ce090fbd49abf9a0ff7564fa6af0e1d4a7274f5cc16cdedef35): `Ran 31 tests ... FAILED (failures=44)` (44 subtest failures,
27 of 31 tests). Typical output: `AssertionError: Lists differ: [] != ['http://target.test/tests/fixtures/bridge/target-role-protocol.html?route=x']`;
the marker test: `['t6b1:marker'] != ['t6b1:marker', 'design:roles-page']`; the install test `[False, False] != [True, True]`.
GREEN at BASE (characterization, not red): `test_history_is_native_and_silent_before_hello`,
`test_a_hello_from_a_sibling_frame_installs_nothing_and_it_hears_nothing`, `test_a_route_that_returns_to_the_same_url_in_one_window_advances_no_version`.
(Requirement 6, 9's exceptions, 10's pre-hello/evil, 12/12b's reply parts are characterization inside tests that are RED for their first roles-page assertion.)
GREEN after the bridge change: `Ran 31 tests in 45.8s OK`.

## Mutants (in-memory copy via `RoleBridgeCase.open(bridge_source=...)`, runner `work/6b1_mutant.py`; bridge file never touched)
Bridge SHA-256 before and after all mutant runs: `e5aaec07b94fef760542ae1fa6c200fe3b2d598b6a3f61a041e439850d4061f4` (unchanged; BASE was 913a4d0b...).
| Mutant | Result | Killed by |
|---|---|---|
| no wrappers | KILLED | url_only_routes (push, replace steps); preview-unchanged; in-flight Detect |
| drop popstate / drop hashchange | KILLED each | popstate_event_alone / hashchange_event_alone |
| hold expiry without refresh | KILLED | change_inside_the_hold (push, resize, hash) |
| record created during the hold | KILLED | stream rate test (61 > 6); NOT the hold test (attribution per Rev. 3 M2) |
| mutations use `pageVersion += 1` | KILLED | content-only, spa render |
| refresh bumps without helper | KILLED | silent_cssom (3d) |
| drop resize listener | KILLED | style_node_media_and_host_resize (host resize), hold (resize) |
| version read before refresh | KILLED | url_only_routes (`0 not greater than 0`) |
| `location.href` instead of `rolePageURL()` | KILLED | unsupported_url null test |
| `isOwnedRoleMutation` false | KILLED | quiet writes: 'apply' (first) and 'detect under a preview' |
| send synchronously | KILLED | burst (many messages); marker order |
| no hold timer | KILLED | stream rate test |
| no 250 ms fallback | KILLED | without_a_paint |
| rAF inside wrapper | KILLED | marker order |
| swallow exception / return true / receiver `history` | KILLED each | native_exceptions (all three / TypeError); wrapper_keeps_receiver_... |
| install at construction | KILLED | native_before_hello; sibling-frame test |
| install on every hello | KILLED | first_hello_installs_once |
| dispose restores unconditionally | KILLED | dispose_leaves_a_later_app_wrapper |
| dispose restores by assignment | KILLED | app_owned_descriptor; dispose_restores_native (own names) |
| no try/catch around install | KILLED (as ERROR: `reply timed out`, the ready never arrives) | frozen_history |
| no `announcedVersion` after ready | KILLED | s1/s2 push test |
| older-epoch record blocks a new one | KILLED | right_after_a_new_hello (lost update) |
| route event bumps the version directly | KILLED | returns_to_the_same_url |
| send path calls `cancelRoleJobs` | **SURVIVED** | see below |

Survivor and limit, reported as instructed (no loosening): on `large-page` the stale `design:detected` posts BEFORE the roles-page
(probe order: `[(0,'design:detected'), (1,'design:roles-page')]`), because the next scan slice (setTimeout 0) sees the URL change before the
send's rAF fires. So the 12b `cancelRoleJobs` mutant is not killable here, same as on `spa.html`. The 12b test keeps its assertions
(stale reply, roles-page, fresh Detect), but it does not detect that mutant. The requirement 13 test has no mutant by design.

## Focused commands (all from C:/fks/t6b1, FKS_ENGINES=chromium)
- A `test_role_route_bridge test_r2_route_fixtures test_role_protocol test_role_preview test_support -v`: `Ran 111 tests in 86.737s OK`
- B `test_role_detection test_role_stylesheet -v`: `Ran 72 tests in 122.313s OK`
- C (FKS_REQUIRE_FIXTURES=1, no npm ci) `test_r2_integration test_r2_react -v`: `Ran 39 tests in 61.023s OK`, no skips
- D `test_bridge_runtime -v`: `Ran 128 tests in 118.845s OK`
- Watch list: no watch test failed. `node --check fontkit-bridge.js` OK; `python -m ruff check . --exclude .agents`: All checks passed.
- `python -m pre_commit run --files fontkit-bridge.js tests/test_role_route_bridge.py`: whitespace, ruff, JavaScript syntax, static checks all Passed
  (the bare `pre-commit` command is not on PATH; the module is). `git diff --check` clean (new file added with `-N` first).
- The suite was not run (settled wave).

## Notes for the landing
- [Corrected in fix round 1, see below: the staged blob is LF, the working-tree file is CRLF (core.autocrlf=true).] `fontkit-bridge.js` is CRLF in the working tree; my edit preserved CRLF (a Python replace on the LF-normalised text, written back with CRLF).
  The patch file itself contains no CR bytes (git normalises); `git apply -3` at the root should be checked with `git diff --check`.
- Measured: the stale reply on Detect beats the roles-page (see survivor); order is not fixed by the brief.
- Known limit stays in the comment above `installRoleHistory`.

## Handoff
Commit subject: `feat(bridge): announce route and content changes to Studio`
Draft body (wrap 72): Studio could not tell that a single-page app had moved to another route or
re-rendered, so evidence checked on one page could be shown for another. The bridge now sends one
data-only design:roles-page notice after the page renders, never for its own writes, and leaves the
app's history calls unchanged. A route change, content change, author stylesheet change or resize
advances the page version and is announced at most once per 250 ms.
Ledger event (product terms): the bridge announces page-version changes (route, rendered content, author styles, viewport) to Studio with
`design:roles-page` carrying document, page version and URL only; Studio ignores it until R2.6S.
README (release point): code that cached the native `history.pushState`/`replaceState` before the first hello bypasses the wrappers; its
change is caught by the next Detect, Apply or Clear, by popstate/hashchange and by rendered content; CSSOM `insertRule` with no DOM change
is seen only by Detect (a hold-expiry refresh within 250 ms after a post may announce it; it is not tracked).
Plan boxes: R2.6B part 1, first two checkboxes. Remaining for R2.6B2: baseline selector checks per known role, BFCache, delayed render,
CSS HMR, the W2 review Minors, and a way to kill the 12b `cancelRoleJobs` mutant (needs a scan whose next slice does not run before the send).


## Fix round 1

Mode code, BASE bd20e43. Patch: task-6b1-code-r1.patch (whole diff against BASE; task-6b1-code.patch untouched). Files: fontkit-bridge.js (+102/-2), tests/test_role_route_bridge.py (565 lines).

### Important 1: new test `SessionAndDetectTests.test_a_detect_started_before_the_announcement_is_sent_finishes_complete_and_is_not_cancelled`
DOM attribute change on large-page, then Detect started in the next call (before the rAF); assert reply complete True, reason None, and exactly one roles-page whose pageVersion equals the reply's.
- Mutant (in-memory, via RoleBridgeCase.open(bridge_source=...), `this.cancelRoleJobs()` added after `announcedVersion = ...` in sendRolePage): RED, ERROR `KeyError: 'complete'` at the reply assertion (the cancelled scan's reply is not a design:detected with `complete`); Ran 1 test FAILED (errors=1).
- Same runner, unmutated source: OK. Real bridge, 5 consecutive runs: OK x5 (3.43-3.44 s each).
- Mutants ran in the foreground; fontkit-bridge.js SHA-256 unchanged before/after (in-memory only). Scratch: work/m6b1r1.py (git-ignored).

### Minor 2: wrapper name and length
JS: after creating `wrapper`, `for (const key of ['name', 'length']) Object.defineProperty(wrapper, key, { value: original[key], configurable: true });` (inside the existing try).
Test: `test_the_first_hello_installs_wrappers_once_and_keeps_the_enumerable_names` (native, no app wrapper, so the names are the native ones; the other wrapper test installs an anonymous app wrapper first, so it cannot assert them) now also asserts native names are ['pushState','replaceState'] and the installed functions' [name, length] equal the native ones; docstring Then extended. I did not hardcode length (chromium reports 2, not 3).
- RED before the JS change: `[['wrapper', 0], ['wrapper', 0]] != [['pushState', 2], ['replaceState', 2]]`. GREEN after: OK.
- Mutant (line removed, in-memory): FAILED with the same diff.

### Minor 3: line endings (measured, differs from the instruction)
Python byte counts on fontkit-bridge.js before my edit: the staged blob (`git show :fontkit-bridge.js`) had 4413 LF and 0 CR. Converting that blob to CRLF gives SHA-256 e5aaec07b94f..., which is exactly the pre-edit working-tree hash, so the working-tree file WAS CRLF (core.autocrlf=true; `file` also says CRLF; now 4414 CRLF of 4414 LF, 214871 bytes). The index, HEAD and the patch are LF (0 CR). So the original note was right about the working tree and the review's 0-CR reading matches the blob, not the file. Landing on a Windows checkout with autocrlf sees LF in the patch; `git diff --cached --check` rc 0.

### Gates (focused only; suite not run)
- A (PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_role_route_bridge test_r2_route_fixtures test_role_protocol test_role_preview test_support): `Ran 112 tests in 90.374s OK` (was 111; +1 new test; test_support included).
- node --check OK; ruff on the test module: All checks passed; pre_commit run --files both: whitespace, ruff, JavaScript syntax, static checks all Passed; `git diff --cached --check` rc 0.
- `git apply --check -R task-6b1-code-r1.patch` in C:/fks/t6b1: ok. Staged: M fontkit-bridge.js, A tests/test_role_route_bridge.py.
- Handoff updates: the 12b survivor row is now KILLED by the new test; drop "a way to kill the 12b cancelRoleJobs mutant" from the R2.6B2 remainder. Command A total goes from 111 to 112 (+1 test).


## Fix round 2

Mode code, BASE bd20e43. Patch: task-6b1-code-r2.patch (whole diff against BASE; earlier patches untouched). Only hunk changed versus r1: the body and docstring of `SessionAndDetectTests.test_a_detect_started_before_the_announcement_is_sent_finishes_complete_and_is_not_cancelled`. No bridge or fixture change.

### Important 1 (rereview): the kill was ~85%
Findings while measuring: with a mutation in one call and the Detect in a later call, the rAF often fired (roles-page at 1-26 ms) before the Detect message was handled, so the Detect did not always start first. That, not the scan length, was the surviving case (3 of 20 survived the first attempt with a 9,000-element page). Both are now fixed inside the test.
- Longer scan: before hello-time Detect, the test appends 4,000 `<p>` text elements (page = 9,000 text elements, under the 10,000 limit), then waits 600 ms so that change's own announcement settles before `start` is marked. Measured Detect round trip on the real bridge (8 runs, complete True, scannedElements 9000): 482, 458, 476, 452, 468, 462, 508, 515 ms; another 6 runs 503-632 ms. All under the 2,000 ms budget. The roles-page goes out at about 18-27 ms, so it lands mid-scan with 430+ ms left.
- Detect provably after the DOM change and before the send: one frame task does `setAttribute`, `await Promise.resolve()` (the observer delivers and bumps the version, the rAF is scheduled), then dispatches the design:detect MessageEvent (source parent, same pattern as HELLO_S2) synchronously. The rAF cannot run between them. The reply is read from the host log by requestId `role-6b1`.
- Precondition asserted: the arrival order of roles-page and detected from the raw log must equal `['design:roles-page', 'design:detected']`, with the message "the scan ended before the announcement was sent, so the test cannot tell a cancelled Detect from a finished one". Docstring Given/Then updated to match (Then adds the order).
- Evidence (in-memory runner work/m6b1r2.py, same test, repeated in one process): real bridge 20 of 20 passed; mutant (`this.cancelRoleJobs()` after `announcedVersion = ...` in sendRolePage, via RoleBridgeCase.open(bridge_source=...)) 0 of 20 passed, 20 of 20 failed (the cancelled Detect never replies: `Page.wait_for_function: Timeout 6000ms exceeded` waiting for role-6b1; red as a failure, not a pass). Bridge file unchanged by the runs.
- Also tried and discarded: a capture listener that mutates on receipt of the Detect; the bridge handler ran first, so the reply was page-changed.

### Gates
- A (PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_role_route_bridge test_r2_route_fixtures test_role_protocol test_role_preview test_support): `Ran 112 tests in 94.085s OK` (includes test_support).
- pre-commit (python -m pre_commit run --files both): whitespace, ruff, JavaScript syntax, static checks all Passed; `git diff --cached --check` rc 0. `git apply --check -R task-6b1-code-r2.patch` ok. Staged: M fontkit-bridge.js, A tests/test_role_route_bridge.py.
- Scratch (git-ignored, in C:/fks/t6b1/work): m6b1r2.py, p6b1r2.py, q6b1r2.py, 6b1r2.out.

## Controller integration
