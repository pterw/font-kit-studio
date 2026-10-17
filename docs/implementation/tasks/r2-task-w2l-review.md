### Spec Compliance
- PASS: no poll. `wait_greeted` (tests/test_studio_live.py:184-205) enters `page.expect_request(f'{TARGET}/fks-hold-load.gif', timeout=20_000)` before `trigger()` (193-194), catches `PlaywrightTimeout` into `self.fail('the page never requested its held image')` (195-196), makes the one-line commented `page.evaluate('0')` round trip (197), then asserts `len(held) == 1` (198), the readyState/hello wait (199-200), then `held.pop().fulfill(status=204)` (201). Order matches the brief's (a)(b)(c) exactly.
- PASS: import `from playwright.sync_api import TimeoutError as PlaywrightTimeout` added (line 17), the only addition outside the owned methods.
- PASS: one setup. `force_order` (208-215) is the only place that installs ORDER_RECORDER, holds or not, picks `?late=1` and connects; the handshake (352) and every-control (1124) tests call it, the i3 test calls it once (1183) and then `wait_greeted(page, order, held, reload)` per round (1191). No third copy.
- PASS: helper owns clearing the recorder lists (line 188 evaluate, before each trigger), so pass 2 never sees stale entries.
- PASS: badge observer is installed by the test before `force_order` (the simpler of the two choices the brief allowed).
- PASS: scope. Only tests/test_studio_live.py changed (+34/-28, 62 gross, budget about 90). `LiveCase.open` signature, ORDER_RECORDER and constants untouched; `hold_load` unchanged. The patch file is byte-identical to `git diff --cached --binary BASE` in a scratch worktree.
- PASS: same strength. Every BASE assertion is kept. The two `assertEqual(window.__order, order)` calls moved into `wait_greeted` (line 203), one place for all three tests. The i3 test now also asserts the order on its first document (BASE did not); this is stricter, matches its docstring ("Studio's page sees the two events in that order"), and the brief's review listed it as a question the helper may answer. Not a defect.

### Checklist
1. Drift: not applicable. No boundary field (protocol field, message type, schema, product file) changed; the diff is tests-only, and `fontkit-studio.html` SHA-256 in the frozen worktree is 9a5d9c11...fa25 (the same as the report's before value).
2. Mutants: I reproduced all four, on a scratch copy `scratchpad/w2l-review-tree` (tar of a scratch worktree without .git; PYTHONDONTWRITEBYTECODE=1; edit restored in the same script; SHA-256 before == after each time). Failures are AssertionError in every case, same (test, subTest) sets as the oracle:
   - M1 (html 4506 `live.sessionId = live.sessionId || newSessionId();`): 4 FAIL: handshake[load first] :364 `1 != 2`; every-control[load first] :1157; i3[bridge-ready first] :1201; i3[load first] :1197. Html SHA before=after=9a5d9c11203c75abd1fd010083c659a9fa50fe4ee7b258acbe9fe69cb29bfa25.
   - M2 (html 4654 unconditional `live.sessionId = newSessionId();`): 4 FAIL: handshake[bridge-ready first] :364 `2 != 1`; every-control[bridge-ready first] :1159; i3[bridge-ready first] :1200; i3[load first] :1196. Same html SHA before and after.
   - M3 (hold route `lambda route: route.fulfill(status=204)`): 3 FAIL, one per test, `wait_greeted:198` `0 != 1 : the page requested its held image` (handshake via 352, every-control via 1124, i3 via 1183, all through force_order:215). Test-file SHA before=after=48ca160e2bedb34e33a0cfa0ef9a16ab66b8288f81983cc1575a7088438ce129.
   - M4 (served body `<img src="/fks-other.gif">`): 3 FAIL, one per test, `wait_greeted:196` `AssertionError: the page never requested its held image` (a FAIL; Playwright's TimeoutError appears only as the chained cause; 68 s for 3 tests). Same test-file SHA before and after.
   - My first M1 attempt aborted on my own CRLF mismatch (assert count==1 failed, file untouched, tests passed unmodified); I re-ran it with a CRLF-independent anchor and got the result above.
3. Fake versus real: PASS. `force_order` still routes to the real `fontkit-studio.html` (`self.open(engine, target=None)`) and the fake target at FAKE; `hold_load` is unchanged and still serves the real fake-target.html with one added `<img>`. The fake, the route table and the Studio page were not touched. No assertion became fake-only; the M1/M2 failures in Studio's own code show the tests still exercise real Studio logic.
4. Hidden skips: none. The diff contains no skip, skipUnless, early return, or `except` that swallows (the one `except PlaywrightTimeout` ends in `self.fail`). Test counts unchanged (Ran 3 and 37 with test_support per the report; I ran the 3).
5. Tests:
   - `grep -n wait_for_timeout tests/test_studio_live.py` in lines 170-222 of the frozen worktree: 0 matches (the nearest are 108 `LiveCase.frame` and 120 `wait_connected`, both outside the owned methods and named as out of scope in the report). PASS.
   - Docstrings of the three tests are unchanged in the diff and still match: handshake ("sees the two events in that order"), every-control ("Studio's page saw the two events in that order"), i3 (as above). The `late` local is still used in all three where needed (handshake 366-ish `2 if late else 1`, every-control 1156/1164, i3 1195).
   - Implementer's concern: a Playwright TimeoutError raised inside the trigger (connect click, or the reload's `wait_for_function`) is reported as "never requested". Acceptable. It is still a FAIL, the original TimeoutError is chained in the traceback ("During handling of the above exception", visible in the M4 log) so the real cause is not lost, and the trigger's own timeouts are 30 s versus the 20 s event wait, so a hung trigger would not usually reach this branch. I rate it Minor at most (see below).
6. Code and load:
   - One helper for the three setups; 62 gross lines against about 90. PASS.
   - Load probe 1 (as the dispatch asked): `gate.sh shard-2` in a scratch worktree ran in the background (`Ran 180 tests in 244.105s OK`, `GATE shard-2 EXIT 0`) while I ran the three tests three times from the scratch tree (Ran 3 OK x3, about 14 s each).
   - Load probe 2 (to push harder, since probe 1 showed no slowdown): 28 busy-loop python burners (the brief review's figure) while the three tests ran six times: 6/6 `Ran 3 tests OK` (33 s, 24 s, 51 s, 16 s, 14 s, 14 s). The brief review measured 4 of 12 failures for the naive form under the same load; the round trip fixes it. No flake seen.
   - Cleanup: burners stopped (checked: no remaining python process with the burner script in its command line); no browser or server of mine is left; a scratch worktree is byte-identical (`git status` shows only the staged test file; both SHA-256s as above).
   - `git diff --cached --check` in the frozen worktree: exit 0. I did not re-run ruff (the report says it passed; the diff has nothing that would fail a normal lint, and `reload(frame=frame)` already guards late binding).

### Checks run
- Seam: the helper's signature change (`wait_greeted(page, order, held, trigger)`) -> `grep -rn "wait_greeted|force_order|hold_load|ORDER_RECORDER" --include=*.py` over a scratch worktree -> only tests/test_studio_live.py uses them; no external caller and no mock.patch target affected.
- Race (waiter resolves before the route handler runs) -> M3 and the 6-run burner series -> assertion fails as designed under M3, never flakes without a mutant.
- Mutant step order -> M3/M4 log shows `held` assertion and `self.fail` before any `wait_for_function`, so no timeouts of 30 s at the frame wait (M3 ran 8.7 s total).
- Patch fidelity -> `git diff --cached --binary BASE` vs task-w2l-code.patch -> identical.

### Strengths
- The (a)(b)(c) design from the brief review is implemented exactly, including the order that makes mutants fail at an assertion rather than time out; I confirmed it with M3 (8.7 s for 3 failures) and M4.
- Both orders are asserted in one place, so a drifted copy can no longer force a different order than the test's name claims.
- The order assertion now also covers the first document of the i3 test.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- tests/test_studio_live.py:193-196: `except PlaywrightTimeout` wraps `trigger()` as well as the wait, so a timeout inside the connect click or the reload wait is worded "never requested its held image". The chained traceback keeps the real cause, so I would not change it; if wanted, wrapping only the wait would need the `with` split, which costs lines for little gain.
- tests/test_studio_live.py:184: the new `order` parameter is only used for the final assertion; fine, but the docstring of `hold_load` (174) says "wait_greeted answers them", which is still true. No action.

### Plan-mandated (for the owner)
- none

### Assessment
**Task quality:** Approved
**Reasoning:** The wait is event-driven in the brief's exact order, the three setups share one helper within budget, and all four mutants fail the same (test, subTest) sets as the oracle at assertions. The three tests passed 6/6 under 28 CPU burners and beside shard-2, with the frozen worktree left untouched.
