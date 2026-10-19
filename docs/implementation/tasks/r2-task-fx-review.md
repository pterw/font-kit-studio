### Spec Compliance
- PASS: only tests/firefox_canary.py changed (git diff --cached --stat: 1 file, +100/-1); budget about 120 lines met.
- PASS: two classes, three methods (BridgeRoleSmokeTests: hostility + route; StudioRoleSmokeTests: round trip), both appended to CANARY (firefox_canary.py:122-123); the nine existing entries, `load_tests` and the docstring (one sentence added) intact. Docstring rewrap leaves a short line ("The frontend gate covers layout,") - cosmetic.
- PASS: bases RoleRouteCase and StudioLegacyCase hold 0 tests; KEYS and SPA imported, not redefined; `self.notices`/`self.urls` used, not the peer-only helpers; static fixtures only (both fixtures tracked in git); no new helper in a shared file, no second driver.
- PASS: D059 guard kept - both pages open through the bases' `open` (regex ^https:// abort route, fallback first, counts asserted); no other context path.
- PASS: Revision 1 minors adopted - `__proto__` case expects `invalid-message` (via JSON.parse in page, same method as test_role_stylesheet.py:395-410), hostile fontSize 30, SPA/KEYS imported.
- PASS: canary count 51 -> 54 (11 CANARY names; collection count 54 by loadTestsFromName, no browser).
- PASS: no hidden skips - Firefox run reports `OK` with no skipped line; the file has no skip/skipUnless.

### Checks run
- New classes under Firefox, frozen worktree -> `PYTHONPATH=tests FKS_ENGINES=firefox python -m unittest firefox_canary.BridgeRoleSmokeTests firefox_canary.StudioRoleSmokeTests -v` -> Ran 3, OK (7.4 s).
- Chromium + CanaryListTest -> same two classes plus test_support under FKS_ENGINES=chromium -> Ran 37, OK. `ruff check tests/firefox_canary.py` -> passed. `git diff --cached --check` clean; no non-ASCII added.
- Collection -> `loadTestsFromName` over CANARY: 54 tests, 11 names; bases RoleRouteCase 0, StudioLegacyCase 0.
- Mutants, my own, on a scratch copy of the tree under scratchpad/fxrv (frozen worktree untouched; scratch bridge restored, SHA-256 3f7f063a...5f47 equals the worktree's), all under Firefox:
  - M1 drop `|| el === document.body` (fontkit-bridge.js:163): FAIL case `.on-body`: `('design:roles-applied', None, 2) != ('design:rejected', 'unsupported-value', 1)` (later cases then fail on revision 2 from the cascade, as expected).
  - M2 skip `this.roleSheet.remove()` at the Clear commit point (:1560, kept for apply): Studio test FAIL after Clear: `(main, '24px', '16px') != (main, '16px', '16px')` - the after-Clear computed size is the killer. (`css == ''` stays true since Studio's CSS comes from the receipt.)
  - M3 drop `bridge.scheduleRolePage()` in the pushState wrapper (:1380): FAIL `[] != [ROLE_PAGE + '?route=x']`.
  - M4 (extra) replace the roleObserver callback with a no-op (:1280): FAIL on the SPA half `[] != [SPA]`, so the second half of method 3 is not decorative.
- Wait question (item 3) -> read fontkit-bridge.js 1535-1590: `installRoleSheet` and the commit point run before `postRoleReceipt`/`measureRoleReceipt`, so a `design:roles-applied` in `__s2b.inbound` can only follow an installed sheet; no `wait_for_function` on the frame was needed for this.

### Checklist answers
1. PASS (see Spec Compliance): three methods, static fixtures, guard kept, shared runtime, existing entries/load_tests/CanaryListTest intact, 51 -> 54.
2. PASS: M1, M2 (with the after-Clear size as killer), M3 and M4 reproduced by me, all red under Firefox.
3. The page-level wait on `__s2b.inbound` is a condition on an observable bridge message (the real receipt, posted after the sheet is installed), not a render proxy. It cannot let the test pass without rendering because the test then asserts the computed styles itself: after Apply `look()[1:] == ('24px','16px')`, `look()[0] == before[0]`, `css` contains `font-size: 24px` (firefox_canary.py:105-108); after Clear, `wait_status('Preview cleared.')`, `css == ''`, and `look() == before` (:109-112). The CSP explanation is plausible and the wait still sits on a real condition; no sleep. Not an issue.
4. PASS: each method asserts computed styles, DOM text/outerHTML, status/CSS panel text and roles-page fields (pageURL, pageVersion, key set, documentId) plus `errors`. The Given/When/Then docstrings match the assertions (method 1: reasons, revision 1, owned CSS, 24px, main unchanged, no errors; method 3: one notice, URL, greater version, six literal keys, document id, body text, detect version, then the SPA half; method 2 as asserted). The only waits are base-class `notices` polling (20 ms poll, 500 ms settle for stragglers - a short absence wait). Oracle independent: literal selector list/reasons, literal KEYS from the sources' own contract tuple, literal strings.
5. PASS: the advisory CI step (quality-gate.yml ~187-201) runs `python -m unittest firefox_canary -v` with FKS_ENGINES=firefox, PYTHONPATH=tests; both new classes are in CANARY so they run there, `continue-on-error` and 10-minute timeout keep it advisory (D037); they added about 7 s. FKS_REQUIRE_FIXTURES is satisfied (fixtures are tracked static files).
6. PASS: +100/-1 lines, one file.

### Strengths
- Subclasses test-free case bases, so the guarded context path and error probes are reused with no new driver.
- Mutants show each of the three methods, and both halves of method 3, can fail on Gecko.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- firefox_canary.py:10-13: the one-sentence docstring addition leaves a short orphan line ("The frontend gate covers layout,"); rewrap. Cosmetic.
- firefox_canary.py:105-107: `look()` is called three times after Apply (once per assertion), each reading the DOM at a different instant; harmless here, but one `after = look()` would assert one snapshot.
- firefox_canary.py:28-30: `CAPTURE` is a duplicate of test_r2_integration.py:186 (the brief asked for a copy; importing would drag in a test-holding module). Drift risk only.

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** The three methods run green on Firefox and Chromium, stay within the budget and the guard, raise the canary 51 -> 54, and fail under four independent mutants I reproduced, including the after-Clear size killer. The `__s2b.inbound` wait is a real message condition and the rendered styles are still asserted.
