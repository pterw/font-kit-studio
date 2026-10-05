# Task 8b code report (mode: code)

Files: `fontkit-studio.html` (+10/-2), `tests/test_studio_npx_hints.py` (new, 175 lines). Patch: `task-8b-code.patch` (applies in reverse cleanly; LF only). No fixture `npm ci` needed (the helper is the package's own, no fixture used). The worktree checkout was CRLF (autocrlf); I normalised `fontkit-studio.html` to LF so the patch matches the LF blob.

## Per message
- Signal: `SERVED_BY_PACKAGE = Boolean(new URLSearchParams(location.search).get("token"))`, read once, no probing. Empty token = not the package.
- Sync miss (`catch` in `detectDevServerSync`): CAN show under the package (its server 404s `/__fontkit/status`). Package text: "Sync to file is not available under npx fontkitstudio. Use Copy or Download in the CSS tab." Control stays disabled with that reason (title and the hint line).
- `file://` Sync text: cannot show under the package (no token there); unchanged.
- `#bridgeHint`: CAN show. Under the package its `textContent` becomes the npx wording (drops the script-tag advice and the `#bridgeHintServe` span, which also stays hidden). Extra, small: the badge `title` ("Add fontkit-bridge.js to the Live App page.") is also the same advice, so under the package it is "npx fontkitstudio adds the bridge to the page itself."
- `BLOCKED_LOOPBACK_TEXT`: CANNOT show under the package. `isBlockedLoopbackReach` returns false when Studio's host is loopback, and the package serves on 127.0.0.1. Left unchanged; a comment in the code says so.
- All text goes through `textContent`/`title`. "Font Kit Studio" used where the product is named (D040). Without a token every string is unchanged (tests check byte for byte for Sync and the hint).

## Evidence
- GREEN: `PYTHONPATH=tests python -m unittest test_studio_npx_hints -v` -> `Ran 3 tests ... OK` (3 tests: package, serve.py, no/empty token).
- RED/mutation (same edit, token ignored: `SERVED_BY_PACKAGE = false`): `FAIL: test_the_hints_say_what_an_npx_user_can_do ... AssertionError: 'Either nothing is running there, or the p[...]App.' != 'npx fontkitstudio adds the bridge ...'`; `Ran 3 tests ... FAILED (failures=1)`. Restored; GREEN re-run OK (the full green run above was before; the modules below were run on the restored file).
- Other modules, all OK: test_studio_first_run (24), test_live_integration (52), test_studio_dead_controls (26), test_support (34), test_studio_controls (34), test_studio_import_link (46), test_studio_review_findings (12), test_preview_server (34), test_studio_visual (33). test_studio_live was not run on its own (it matched the grep only for "serve.py" in setup text; the frontend gate and the others cover Studio). Not run: full suites A/B (controller's gates).
- `python scripts/verify.py --static-only`: last line `SKIP unittest/browser tests: --static-only; full acceptance not checked` (all PASS before it).
- `python scripts/dev/frontend_gate.py` last line: `[frontend_gate] SUMMARY OK: 30 of 30 planned runs finished. Blocking: 7 runs, 7 passed, 0 failed, 0 skipped. Advisory: 23 runs, 0 ADVISORY lines. 334 REPORT lines, 0 SKIP lines, 0 FAIL lines`
- `python -m ruff check .`: `All checks passed!`
- pre-commit (`python -m pre_commit run --files ...`; the `pre-commit` binary is not on PATH): whitespace Passed, ruff Passed, node --check Skipped (no JS files), static checks Passed.

## Self-review (anti-patterns)
- AP 3 / rule 5: text via `textContent`/`title`; tests assert rendered text and attributes, no `page.content()`.
- AP 13: the helper process is stopped in `addCleanup` (stdin close, wait, kill on timeout); the serve.py `Server` closed by `addCleanup`; the static handler server shut down and joined in cleanups.
- AP 14: the package test skips only when `node` is missing (same as `test_node_studio_server.py`).
- Rule 7: `https://**` blocked in every test context. D040: package wording says "Font Kit Studio".
- A guard per check: the mutation shows the package assertions fail; the no-token/empty-token and serve.py tests guard the unchanged wording. Concern: the serve.py test asserts the Sync title through Auto-sync's title because the Sync button title becomes "No changes to save yet." when nothing is saved.

## Handoff
- CHANGELOG (Unreleased, Changed): "Studio opened by `npx fontkitstudio` no longer points to `scripts/serve.py`; its Sync and bridge messages say what to do instead (use Copy or Download; the command adds the bridge itself)."
- progress.md event draft: "R1.8b: Studio's Sync-miss message, bridge hint and bridge badge title use npx wording when its URL carries a non-empty `?token=` (the package's server); `BLOCKED_LOOPBACK_TEXT` cannot show there and is unchanged; tests/test_studio_npx_hints.py (3 tests); frontend gate OK."
- Commit subject: `feat(studio): give npx users hints they can follow`
- Draft body: "The package's server has no /__fontkit/status and no sync endpoint, and it adds the bridge to the page itself, yet Studio told its users to run python scripts/serve.py or add a script tag. A non-empty ?token= in Studio's URL, read once, now selects npx wording for the Sync-unavailable reason, the bridge hint and the badge tooltip. Without a token every message is unchanged."

## Fix round 1
1. Badge tooltip: the package test now asserts it equals "npx fontkitstudio adds the bridge to the page itself." exactly.
2. The vacuous `#bridgeHintServe` visibility check is dropped; the hint's exact text is already asserted equal, and no `serve.py` or `fontkit-bridge.js` appears in the hint, Sync title or badge title.
3. The "Only the two hostnames are known..." comment is back directly above `BLOCKED_LOOPBACK_TEXT`.
4. The empty Live App inspector ("Enter the URL of a localhost app that loads fontkit-bridge.js...") CAN show to an npm user: Studio opened without `?target=`, Composer, Live App view, nothing connected. Under the token it now reads "Enter the URL of a localhost app, then press Connect Live App. npx fontkitstudio adds the bridge to the page itself." (`NPX_EMPTY_INSPECTOR`). Tests: package (exact text) and no-token (old text, byte for byte); the package URL is opened with `target` renamed away.
- Mutation (token ignored, then restored): `FAIL` in both package tests (hints, empty inspector); `Ran 5 tests ... FAILED (failures=2)`. Restored: `Ran 5 tests ... OK`.
- Re-run OK: test_studio_npx_hints (5), first_run, live_integration, dead_controls, support, controls, import_link, review_findings, preview_server, visual. ruff: All checks passed. static: all PASS, last line is the --static-only SKIP line. Frontend gate not re-run (string-only change, as the controller allowed).
- Patch regenerated at the same path (reverse-apply check passes, no CR).
