# R2.7I2 (fx) code report

Mode: code. Changed: `tests/firefox_canary.py` only (+100/-1; CRLF working tree kept). Patch: `task-fx-code.patch`
(`git apply --check -R` passes).

## Done
- `BridgeRoleSmokeTests(RoleRouteCase)`: methods 1 and 3. `StudioRoleSmokeTests(StudioLegacyCase)`: method 2. Both
  names appended to `CANARY`; docstring extended by one sentence. Both bases hold 0 tests (checked).
- Method 1 includes the own-`__proto__` role case (via `JSON.parse` in the page, expects `invalid-message`), hostile
  fontSize 30. `KEYS` and `SPA` imported. Method 3 uses `self.notices`, not the peer-only `received` helpers.
- Studio waits use `page.wait_for_function` on `__s2b.inbound` (a `roles-applied` entry), because frame-level
  `wait_for_function` times out on the target (page CSP; first draft failed on Chromium for that reason).

## Evidence (all GREEN characterization, no RED)
- Chromium, the two classes: Ran 3 tests, OK. Firefox, the two classes: Ran 3 tests in 7.7 s, OK. No Gecko difference found.
- Canary count, browser-free collection: 51 before, 54 after.
- Chromium `test_support` (includes `CanaryListTest`): Ran 34 tests, OK. `ruff check`: passed.
- Mutants under Firefox, `fontkit-bridge.js` mutated on disk, SHA-256 before and after both
  `3f7f063a5256f9be365930b4d8d38f3072eeb093fdff137d097818acc5bf5f47`:
  - Method 1: drop `|| el === document.body` (line 163): FAIL case `.on-body`: `('design:roles-applied', None, 2) != ('design:rejected', 'unsupported-value', 1)`.
  - Method 2: skip `this.roleSheet.remove()` at line 1560 (commit point; the one Clear uses; line 1493
    `removeRoleSheet` is not on Clear's path, a first try there survived): FAIL after Clear:
    `(..., '24px', '16px') != (..., '16px', '16px')`. Killer: the after-Clear computed size / `look() == before`.
  - Method 3: drop `bridge.scheduleRolePage()` in the pushState wrapper: FAIL `[] != ['...?route=x']`.
- pre-commit on the file: trailing whitespace Passed, ruff Passed, node/static Skipped (no files).

## Handoff
Subject: `test: add role smoke tests to the Firefox canary`. Body: Gecko previously had no coverage of role selector
hostility, Studio's apply and clear, or route announcements; add three smoke tests in two classes to the advisory
canary. Ledger: canary 51 -> 54 tests (3 role smoke tests); Firefox ran them green, no Gecko differences found;
canary stays advisory (D037).

## Controller integration
