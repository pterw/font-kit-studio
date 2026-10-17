# Task codex (PR #22 Codex review fixes), code report

Mode: code, worktree C:/fks/ts4 at BASE f11055e. Staged only, nothing committed.
Patch: `.superpowers/sdd/r2/task-codex-code.patch`, sha256 `9f56bb939c778bc0b720c5d63d2e0056a1c2f9a7e45e1a67d0c4f67310ecffc7`
(`git apply --check -R` passes). Files: `fontkit-studio.html` (+25), `tests/test_studio_roles.py` (+146/-42 net), `tests/test_r2_integration.py` (+41).

## Source
1. `design:ready`: `sameDocument` (same documentId and same origin as the accepted preview) -> `live.revision = max(live.revision, readyRevision)`; a new document still sets it, even lower. The rest of the ready is still handled.
2. `serializeRoleSheet(roles)` duplicates the bridge's `serializeRoleCss` (comment: R2.S3 must extend it for the Bootstrap templates; global rule 10). `validAcceptedRoles` now also requires `css === serializeRoleSheet(roles)`; this covers receipts, ready snapshots and the reset-all reply.

## RED (before the source change)
- `test_a_stale_ready_of_the_same_document_never_lowers_the_revision_the_next_apply_carries`: `AssertionError: 4 != 5`.
- `test_a_ready_whose_css_is_not_its_roles_serialization_is_not_shown_even_with_a_matching_digest`: preview showed `p { color: red; }` as "The page reports an accepted role preview".
- `test_every_hostile_receipt_...` with two new rows (`css unrelated to the roles with its own digest`, `css with the roles plus an extra rule and its own digest`): exactly those two subtests error (fence wait timed out because the hostile receipt had settled the request). Final run of that command: `Ran 2 tests ... FAILED (errors=2)` (the other test in the run was the new-document one, which passes).
- Characterizations, GREEN before and after (no manufactured RED): `test_a_ready_for_a_new_document_adopts_its_lower_revision`, the two real-bridge serialization tests (`test_studio_shows_the_real_receipt_so_its_serialization_equals_the_bridges` with a quoted CJK family, 24.5px, 700, 1.25, 0.05em, uppercase; `test_a_receipt_for_an_escaped_class_selector_equals_studios_serialization`, selector `.sm\:big`, which the real bridge produces for a style group).

## Existing tests that had to change (they sent non-canonical CSS with a matching digest)
- Hostile table fence, wrong-session `marked`, 128 KiB and 1 MiB boundary tests, literal-markup test.
- The "fence"/"hostile" receipts are now distinguished by an outcome `matched N` marker (unique per subtest) instead of extra CSS, and each subtest issues its own request so one failure cannot cascade.
- 128 KiB test: 128 seeded roles, receipt roles carry 300 multi-byte family characters each plus selector padding (`sized_receipt`), so the CSS is a real serialization of exactly 131072 and 131073 bytes.
- 1 MiB test: padding moved from CSS into a second partial loss selector; accepted case now waits on `matched 64,` (the old wait on the status text was already true from the previous subtest).
- Literal-markup test renamed to `..._in_names_and_details_...`: markup cannot occur in canonical CSS any more (selectors and families refuse `<`), so its CSS assertion became the receipt's own CSS.
- `canonical_css` docstring updated. Every new test has a Given/When/Then docstring.

## GREEN (PYTHONPATH=tests FKS_ENGINES=chromium FKS_REQUIRE_FIXTURES=1)
- Command 1 (`test_studio_roles test_r2_integration test_studio_import_link test_studio_dead_controls test_support -v`): `Ran 199 tests ... OK` (before the escaped-selector test was added). After adding it: `test_r2_integration test_support` `Ran 59 tests ... OK`.
- Command 2 (`test_studio_live test_studio_first_run test_studio_stage.PreviewWidthTests test_studio_visual.LiveAppViewTests -v`): `Ran 184 tests ... OK`.
- `ruff check` on both test files passes; `pre-commit run --files` (via `python -m pre_commit`): whitespace, ruff, static checks Passed; node syntax Skipped (no .js file). `git diff --cached --check` clean.

## Mutants (foreground, `scratchpad/mutate-ts4.py`, source restored byte-exact in finally; sha256 of fontkit-studio.html before and after `bd3beabd142a82c00023317f217dc834d853c71b8948bfbe7c0043c27a0dd804`, "restored True")
- revision guard removed (`live.revision = readyRevision`): stale-ready test FAILS.
- equality check removed (`&& css === serializeRoleSheet(roles)`): hostile receipt test (2 new rows) and hostile ready test FAIL.
- letterSpacing `em` dropped in `serializeRoleSheet` (extra): real-bridge test ERRORS (receipt never shown).

## Concerns
- Doc/CHANGELOG/plan bookkeeping not touched (controller-owned). Suggested: note that Studio now duplicates the plain serializer and R2.S3 must extend it.
- An invalid ready over an accepted preview keeps the existing behaviour (CSS kept, marked Unconfirmed); "changes nothing" for ready means the hostile CSS is never shown.

## Fix round 1 (selector join untested)
- Added `test_a_receipt_for_a_role_with_two_selectors_equals_studios_serialization` to `tests/test_r2_integration.py` (page `TWO_SELECTOR_PAGE`: two same-styled paragraphs with classes alpha and beta; the real bridge groups them under two dom-path selectors). It asserts the request has 2 selectors, the receipt rule joins them with ", ", the preview CSS equals the receipt's `canonicalCss`, and both paragraphs render 24px. Given/When/Then docstring. GREEN on the unmutated source (characterization, no source change).
- Mutant `role.selectors.join(",")` in `serializeRoleSheet`: test ERRORS (receipt never shown). Source restored byte-exact; fontkit-studio.html sha256 `bd3beabd142a82c00023317f217dc834d853c71b8948bfbe7c0043c27a0dd804` before and after.
- `test_r2_integration test_support`: Ran 60 tests, OK. Ruff passes, `git diff --cached --check` clean.
- Patch `.superpowers/sdd/r2/task-codex-code-r1.patch` (full staged diff against f11055e), sha256 `e266eca3112422ea7b39180b16d3dcbdd6ba39272ad9dd3c2811c1b3210ebb4c`.

## Controller integration (2026-10-17)

The final patch (`task-codex-code-r1.patch`, sha256 `e266eca3...`) applies onto `207bc16` (the family-list fix) with no conflict; each staged blob equals the code-phase worktree's index.
- `test_studio_roles test_r2_integration test_studio_import_link test_studio_dead_controls test_support` (Chromium, on `207bc16`): Ran 201 tests in 272.787 s, OK.
- `test_studio_live test_studio_first_run test_studio_stage.PreviewWidthTests test_studio_visual.LiveAppViewTests test_live_integration` (Chromium): Ran 236 tests in 375.382 s, OK.
