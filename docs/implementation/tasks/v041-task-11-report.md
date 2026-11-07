# Task 11 code report (mode code, BASE 5443ff6, worktree the task's worktree)

Patch: task-11-code.patch (plain `git diff`, task 10's staged patch untouched, applies on top of it).
Files: fontkit-bridge.js (+25/-3), tests/test_bridge_runtime.py (+78, class TokenNotAppliedTests after LegacyCompositionTests),
tests/fixtures/bridge/target-terminal.html (new, 16 lines). `postWarning` untouched.

## What changed
- `handleCompositionUpdate`: `before = this.computedFontFamilies()` ahead of the token writes; a local `writeToken` wraps
  `setToken` for both the `patch.tokens` loop and the four shortcuts (same order, same replies). A name counts as written when
  `setToken` returned a value, it differs from the held `tokenOverrides` value, it is one of the four Studio names, and it was
  not already counted. After the shortcuts (before step 2), if any was written and no family differs, one
  `postWarning('token-not-applied', 'global', <New string 1>, data.requestId)`, before `acknowledge`.
- New method `computedFontFamilies()` after `removeToken`: array of computed font-family over `querySelectorAll('*')`.

## Tests
`PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_bridge_runtime.TokenNotAppliedTests ...LegacyCompositionTests ...TokenRemovalTests test_support -v`
-> Ran 45 tests, OK. Not run: test_studio_roles, test_role_routes, test_r2_integration (landing).
- RED before the source change: 4 of 5 new tests fail (no warning sent); the "page reads a synced name" test passes
  (characterization, nothing warns at BASE). The repeat-Sync test is RED at BASE only because the third Sync expects a warning.
- Breaks (each applied to the real bridge file, which the tests load from the repo root; restored afterwards):
  never posting: 4 fail. Second pass after slot loop: slot test fails. Drop changed-value filter: repeat test fails.
  Drop "at least one written" guard (`if (true)`): repeat and name/guard tests fail. Name filter widened to `startsWith('--font-')`:
  name test fails (it syncs `--font-size-base`; the first run of that mutant survived, so I added that token to the test).
- Added `--editorial-size` and `--font-size-base` in the first Sync of the name/guard test; a slots-only Sync and `{'sans': ...}` follow.

## Notes
- Deviation: the brief's test 4 text was replaced by Review fix 3 (third Sync changes one value, names only that token).
- Accepted limit (Review fix 6): a token used only in pseudo-elements, shadow roots or script, or a first write equal to the
  page's own value, may warn; New string 1 allows for it.
- The measuring runs on every composition Sync (also slots-only), one pass each side; linear, 15-25 ms on 5,000 elements.
- Pre-commit not run (not asked in the dispatch rules).

## Handoff
- Insertion point of `computedFontFamilies` (right after `removeToken`) is two unchanged lines from Task 4's 3000-3045 region.
- Commit subject: `fix(bridge): warn when a synced token changes no element`
- CHANGELOG (Unreleased, Fixed): `- Sync to Live App now tells you when it wrote font tokens and no element on the page changed, which happens when the page reads other token names.`
- Landing also runs test_studio_roles, test_role_routes, test_r2_integration.
