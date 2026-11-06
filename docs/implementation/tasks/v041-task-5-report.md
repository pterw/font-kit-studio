# Task 5 code report (B14, G1-5, B01)

Mode code, worktree the task's worktree, BASE 5443ff6. Nothing staged or committed in the real index. Patches in ``, in order, each on the one before:
`task-5-B14.patch` (fontkit-bridge.js, tests/test_bridge_runtime.py), `task-5-G1-5.patch` (adds target-stat-names.html), `task-5-B01.patch` (adds target-module-bundle.html, target-classic-capture.html). The second and third were cut against a throwaway index (GIT_INDEX_FILE, since deleted) holding the earlier state.

## What changed
- B14: BLOCK_ELEMENTS gains li, pre, dl, fieldset, figcaption, hr, main, dt. Nodes are built in the page with frame.evaluate before `hello`; the oracle opens a second page with `set_content` and checks the parser put each tag outside the `<p>`. The div into em/code/strong test builds its parents directly in `main`.
- G1-5: `[class*="stat"]` replaced by `.stat`. Fixture has the three divs in separate wrappers (review fix 3).
- B01: module-level `warnedUnreadOrigins` flag above resolveAllowedOrigins; warns New string 4 once when no option, no script read and `script[data-allowed-origins]` exists. Return value unchanged.

## Tests
Focused command from the brief: 51 tests, OK (66.9s), chromium.
RED before fix (shown):
- B14: 8 subtests failed, `'design:applied' != 'design:rejected'` for each tag (li ... dt).
- G1-5: `AssertionError: 3 != 1` targets.
- B01: `[] != ['[FontKitBridge] data-allowed-origins could not ...']`.
Breaks, each run against the code the test loaded (fontkit-bridge.js edited in place, restored after):
- B14: dropping `dt` fails 1 test (the dt subcase).
- G1-5: restoring `[class*="stat"]` fails the new test.
- B01: dropping the flag check fails the module test (second line); a warning decided on the final null result (after parseOriginList) fails the `*` tag case and, via the option case, the characterization test. (A first attempt placed that check before parsing and did not fail; the corrected one did.)

## Deviations and notes
- tests/test_bridge_runtime.py: three one-line page constants (MODULE_BUNDLE_PAGE, CLASSIC_CAPTURE_PAGE, STAT_NAMES_PAGE) added beside ARRANGE_PAGE at the top, and NEW_STRING_4 above UnreadOriginListTests. Outside the named class regions but needed.
- Option and `*` cases (review fix 4): no extra fixture. Module fixture reads `location.hash === '#options'` to set FONTKIT_BRIDGE_OPTIONS; classic fixture writes its tag with document.write and `#star` gives `*`. The target is passed as `...html%23options` / `%23star`. Both fixtures are therefore small extensions of the brief's description.
- The module bundle boots as a module (hello from EVIL gets design:ready; the import was not refused). Warning is already given at auto-init, so the "once" check uses a second `new FontKitBridge()` before hello (review fix 1).
- LF-to-CRLF git warnings on the new fixtures only.
- No test outside the brief broke. test_role_detection.py untouched; CHANGELOG untouched.

## Handoff
- Commit subjects as in the brief; no CHANGELOG line from this task.
- Task 18: DaisyUI `stat-title`, `stat-value`, `stat-desc` no longer match by `stat` alone; a real `.stat` still writes ids onto its siblings (sibling pass 3517-3525).
- README later carries the ways out (`window.FONTKIT_BRIDGE_OPTIONS`, `new FontKitBridge({allowedOrigins})`).

## Follow-up (page with no origin tag stays silent)
- tests/test_bridge_runtime.py: `test_a_classic_script_tag_keeps_its_list_and_warns_nothing` gains a subTest `case='no origin tag'`. It opens CLASSIC_CAPTURE_PAGE + `%23none`, first asserts `script[data-allowed-origins]` count is 0, then that hello gives design:ready and `__warns == []`.
- tests/fixtures/bridge/target-classic-capture.html: `#none` writes the bridge script tag with no data-allowed-origins attribute (comment updated). The other cases are unchanged. fontkit-bridge.js untouched in this round; no patch written.
- Break shown: removed `document.querySelector('script[data-allowed-origins]')` from the `else if` in fontkit-bridge.js (the code the test loaded), ran UnreadOriginListTests: 1 failure, `case='no origin tag'`, `['[FontKitBridge] data-allowed-origins could not be read ...'] != []`; the other test passed. fontkit-bridge.js then restored from a copy and the condition confirmed back.
- Final run, `test_bridge_runtime test_support` (chromium): 167 tests, OK. test_bridge_runtime alone is 167 minus test_support's count (not split out).
