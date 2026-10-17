# R2.W2PI code report (mode: code, worktree a scratch worktree)

Staged state verified: `git diff --cached --stat` = 10 files, 1154 insertions, 252 deletions (w2t, w2sa, w2b2-p2, w2b1, w2sb, w2sc,
w2pt-r1, w2p, w2ps-r1). Patch `task-w2pi-code.patch` (sha256 7285916eac82b446d703c7f4b4b64eb894e87ca3833cee8f05bc378c4740b9b6) is the
delta on that index: `tests/test_r2_integration.py` only, +55/-2 gross; `git apply --check -R` passes; `git diff --cached --check` clean.
Incident: I briefly ran `git reset` on that path and so dropped its staged W2SA hunk from the index; I restored it (reverse-apply my
patch, `git add`, re-apply) and re-verified the index stat (10 files, 1154/252) and that `git diff --binary` is byte-identical to the patch.

## Changes
1. Existing test `test_a_bootstrap_5_body_row_applies_with_its_variables_and_clear_restores_the_page`: font-size assertion now
   `['16px', f'{size}px', f'{size}px', '16px']` (both `.btn` keep 16px under a body binding; Addendum 23 item 1), docstring says so.
   Buttons stay in the tuple; nothing else changed.
2. New `test_the_bootstrap_5_body_row_applies_to_body_text_that_has_no_ids_or_shared_class_and_clear_restores_it`, with `MEMBERS` and
   `STYLES` class constants. 20 `<p>` and 20 `<li>` added before `</main>`. Oracles: members = `main *` elements with own text whose
   computed family/size/weight/line height/letter spacing/transform equal body's, read before Apply (count asserted 44, 2 `.btn`);
   expected values are the typed family, `22px`, and literal `16px` for `.btn`. Asserts: row has role id, Apply enabled, request roles
   == `[('bootstrap5-body', ['body'])]`, status "Preview applied to 1 role; 0 checked elements did not show it.", the whole Body line
   ending with the page-wide literal, member styles, Clear restores styles and `main` markup, preview CSS empty. Detect and receipt
   waits are bounded (15 s) polls that return the text, so a hang is an assertion, not a timeout.

## RED (scratch trees outside the repository; "base" = W2P and W2PS reverse-applied, other patches kept)
- base: `AssertionError: False is not true` at `self.assertTrue(self.button(page, APPLY).is_enabled())` (role id was not None; no draft controls enabled).
- W2PS alone (W2P reversed): `AssertionError: 'Detected' not found in 'Detecting text styles...'` (differs from the brief's guess: Studio
  W2PS drops a reply whose Body adapter group has no `page` binding, so Detect hangs; reported as observed).
- W2P alone (W2PS reversed): same `'Detected' not found in 'Detecting text styles...'`, as the brief predicted.

## GREEN
`gate.sh focused test_r2_integration test_studio_roles test_role_adapters test_support`: `Ran 201 tests in 214.425s`, `OK`,
`GATE focused EXIT 0 IN 215s`. `python -m ruff check tests/test_r2_integration.py`: All checks passed.

## Mutants (scratch full copy, sha256 before = after for each; foreground; test run alone)
1. Bridge page binding removed (`bind(group, ['body'])`; sha db58389a...): `'Detected' not found in 'Detecting text styles...'`.
2. Studio `page` acceptance removed (sha 56dd0108...): same assertion.
3. Bridge body plain block dropped (sha db58389a...): fails at the status assertion, `'Preview applied...' not found in 'No response to apply;
   the shown preview is the last one the page acknowledged.'` The bridge's install check (rule count = block count, D-rule in Addendum 22)
   refuses the lone `:root` block, so the family assertion is not reached. A real red at an assertion, but not the family one the brief expected.
4. Studio receipt wording reverted (`pageWide` branch off; sha 56dd0108...): assertEqual of the outcome line fails (no-eligible-text suffix vs page-wide).

## Notes
Gross lines 55 inserted (brief budget ~90). Handoff: one commit-body sentence for W2P's commit: "The real Studio now applies the Bootstrap 5 Body
row on a 44-element page whose body text has no ids or shared class, and the existing Bootstrap 5 test expects .btn to keep 16px."
Scratch copies deleted.

## Controller integration

The controller applied this patch in landing order (W2T, W2L, W2S-a, W2B2, W2B1, W2S-b, W2S-c, W2PT, W2P, W2PS, W2PI,
W2E) on BASE `73b3ba2` and ran the gates once on the integrated tree, Chromium on Windows:

- focused, adapters, detection, protocol and handshake modules: Ran 85 tests, OK.
- focused, stylesheet, preview, Studio live and React modules: Ran 232 tests, OK.
- focused, Studio roles, R2 integration and support modules: Ran 156 tests, OK.
- static (provenance PASS), `node --check fontkit-bridge.js`, product ruff and whitespace: pass.

The full suite halves, the Node package, the frontend gate and the Firefox canary run at the settled wave.
