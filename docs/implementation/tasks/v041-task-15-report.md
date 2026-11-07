# Task 15 code report

Mode code, BASE 5443ff6, worktree the task's worktree. Patch: task-15-code.patch (fixture via `git add -N`). Nothing committed.

Files: `fontkit-bridge.js` (LEGACY_TOKEN_KEYS now `--font-sans, --font-serif, --font-mono, --font-display, --brand-canvas`),
`tests/test_bridge_runtime.py` (LEGACY_TOKENS_PAGE + `LegacyTokenNameTests`), `tests/fixtures/bridge/target-legacy-tokens.html` (new).
45 insertions in the diff, 2 deletions.

## Evidence
RED (old array restored in the bridge, which is what the test loaded): 4 subtests failed, one per name:
`'--accent-cyan' unexpectedly found in {... '--accent-purple': '#8844cc'}`, same for `--accent-purple`, `--editorial-size`,
`--mono-spacing`. `Ran 1 test ... FAILED (failures=4)`. This is also the re-add break; it was run with all four re-added
together, so each name is shown failing in its own subtest.
GREEN: `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_bridge_runtime test_support` -> Ran 163 tests, OK.
`--font-display` and `--accent-emerald` assertions passed at BASE (characterization).

## Deviation
Review fix 1 asks that re-adding any removed name fails the test. `--accent-emerald` cannot do that: requirement 2 puts it
in `:root` and expects it reported, so the stylesheet reader finds it whatever the list says. The fixture sets the other
four removed names (`--accent-cyan`, `--accent-purple`, `--editorial-size`, `--mono-spacing`) only under
`html[data-theme='x']`, and the test asserts them absent in subtests. Re-adding `--accent-emerald` alone would not fail any
test. Fixture additionally sets `--accent-purple`, `--editorial-size`, `--mono-spacing` (brief listed only cyan and
`--font-display`).

## Handoff
No CHANGELOG line. Commit subject: `refactor(bridge): stop reporting token names no app reads`. Body names kept items:
`--brand-canvas` (Studio CSS export, fontkit-studio.html:3216), `#main-content-flow` (fontkit-bridge.js:4120, README),
`resolveElementForSlot`; the removed names had no consumer. pre-commit not run (not asked in dispatch rules).
