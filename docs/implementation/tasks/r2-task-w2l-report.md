# R2.W2L code report (MODE code, BASE 73b3ba2)

Changed: `tests/test_studio_live.py` only (+34/-28, 62 gross, all test code). Patch: `task-w2l-code.patch` (LF, `git apply --check -R` passes).

## What changed
- Import `from playwright.sync_api import TimeoutError as PlaywrightTimeout`.
- `wait_greeted(page, order, held, trigger)` (lines ~183-205): clears the recorder lists, then for a held load runs
  `with page.expect_request(f'{TARGET}/fks-hold-load.gif', timeout=20_000): trigger()`; the timeout is caught and becomes
  `self.fail('the page never requested its held image')`. Then `page.evaluate('0')` (commented: the event says the page asked, not
  that the route handler ran), `assertEqual(len(held), 1, ...)`, the readyState/hello wait, `held.pop().fulfill(204)`, the
  two-hellos and Connected waits, and the order assertion. Unheld: `trigger()` only.
- New `force_order(page, order)` (~207-216): installs `ORDER_RECORDER`, holds or not, connects with/without `?late=1`, returns `(frame, held)`.
- `hold_load` unchanged. The three tests call `force_order`; the i3 test calls `wait_greeted(page, order, held, reload)` per round,
  `reload` doing `location.reload()` plus the `performance.timeOrigin` wait. The handshake badge observer is installed by the test before
  `force_order` (simpler). All other assertions are untouched; test docstrings unchanged.
- Structural check: `grep -n wait_for_timeout tests/test_studio_live.py` shows nothing in lines 170-220 (hold_load, wait_greeted, force_order).

## Mutants (Python with PYTHONDONTWRITEBYTECODE=1, foreground, script `mutate-w2l.py` in the scratchpad, restored in finally)
All failures are at assertions, matching the oracle sets exactly.
- M1 (html 4506 `|| newSessionId()`): 4 FAIL: handshake[load first] :364 `1 != 2`; every-control[load first] :1157; i3[bridge-ready first] :1201; i3[load first] :1197.
- M2 (html 4654 unconditional): 4 FAIL: handshake[bridge-ready first] :364 `2 != 1`; every-control[bridge-ready first] :1159; i3[bridge-ready first] :1200; i3[load first] :1196.
  html SHA-256 before = after = 9a5d9c11203c75abd1fd010083c659a9fa50fe4ee7b258acbe9fe69cb29bfa25 (both).
- M3 (hold route answers at once: `route.fulfill(status=204)`): 3 FAIL, one per test, `wait_greeted:198` `0 != 1 : the page requested its held image`.
- M4 (served copy `<img src="/fks-other.gif">`): 3 FAIL, one per test, `wait_greeted:196` `AssertionError: the page never requested its held image` (a FAIL, 20 s wait each).
  test file SHA-256 before = after = 48ca160e2bedb34e33a0cfa0ef9a16ab66b8288f81983cc1575a7088438ce129 (both).

## Gates
- Focused (3 tests + test_support) five times in a row: each `Ran 37 tests`, `OK`, `GATE focused EXIT 0 IN 29s`.
- Under load (shard-2 running beside): focused `Ran 37 tests in 30.322s OK EXIT 0`; shard-2 `Ran 180 tests in 254.484s OK GATE shard-2 EXIT 0`.
- `python -m ruff check tests/test_studio_live.py`: All checks passed. `git diff --cached --check`: exit 0. Full suite not run (wave rule).

## Notes
- Sibling poll, not fixed (anti-pattern 12): `tests/test_studio_roles.py` ~1219-1222 (`for _ in range(200): if held: break ...`). Also out of scope in owned file: `wait_connected` 150 ms sleep (line 120), `LiveCase.frame` 50 ms poll (108), `wait_badge` default 5 s.
- Caveat: a PlaywrightTimeout raised by the trigger itself inside the `with` would be reported as "never requested"; acceptable, still a FAIL.
- No product file touched. Mutants M1/M2 touched only the worktree copy of fontkit-studio.html, restored.

## Handoff
- Commit subject: `test: await the held image and share the announce-order setup`
- Draft body:
  The held-image wait in wait_greeted polled every 50 ms for five
  seconds, which fails a correct run on a slow machine, and the
  announce-order setup was written out in three tests.

  Wait for the image request as an event, entered before the connect
  or reload that causes it, then make one browser round trip so the
  route handler has recorded the request before it is counted. A page
  that never asks now fails with a message instead of a timeout. One
  force_order helper replaces the three copies and wait_greeted clears
  the order recorder before each document.
- Plan item: R2.W2L (Addendum 22), tick on landing.

## Controller integration

The controller applied this patch in landing order (W2T, W2L, W2S-a, W2B2, W2B1, W2S-b, W2S-c, W2PT, W2P, W2PS, W2PI,
W2E) on BASE `73b3ba2` and ran the gates once on the integrated tree, Chromium on Windows:

- focused, adapters, detection, protocol and handshake modules: Ran 85 tests, OK.
- focused, stylesheet, preview, Studio live and React modules: Ran 232 tests, OK.
- focused, Studio roles, R2 integration and support modules: Ran 156 tests, OK.
- static (provenance PASS), `node --check fontkit-bridge.js`, product ruff and whitespace: pass.

The full suite halves, the Node package, the frontend gate and the Firefox canary run at the settled wave.
