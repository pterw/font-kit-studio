# R2.S3 code report (phase 1 of 2, MODE code)

Status: BLOCKED on one existing test (below); everything else is done, staged in `C:/fks/ts3` and in the patch.
BASE `f2b438f`. Patch: `.superpowers/sdd/r2/task-s3-code.patch` (SHA-256 `a839ade06a90bdd43c99f7fd85289b981be1ad7f6570f35d85297524bb59c1e8`, LF only, `git apply --check -R` passes). Files: `fontkit-studio.html` (+18 -8), `tests/test_studio_roles.py` (+262 -6), `tests/test_r2_integration.py` (+66 -1). 346 added, 15 removed (brief: about 500).
Proposed fix for the blocker, NOT in the patch: `.superpowers/sdd/r2/task-s3-proposed-fix.diff`.

## The blocker (existing test outside the brief's scope)
Item 7 (16 losses per property) makes `StudioRoleApplyTests.test_a_receipt_at_one_mib_is_accepted_and_one_byte_more_is_not` fail: its `build()` pads each outcome with 64 `fontSize` losses, which D071 now refuses. The brief says every other existing test keeps passing unchanged, so I stopped instead of editing it. The one-line fix (give the padding losses `PROPERTY_ORDER[n % 6]` as their property; chunks stay 64, at most 11 per property) was tried: that test goes `Ran 1 test in 5.190s OK`; file then restored to its staged bytes (SHA-256 `495d0bca...fe05` before and after). Focused gate without PATCH_DEP: `Ran 194 tests in 276.026s`, `FAILED (errors=1)`, that test only, `GATE focused EXIT 1`. With the fix, the other 193 pass. The controller decides; phase 2 can apply `task-s3-proposed-fix.diff` (applies to `tests/test_studio_roles.py` after the patch, 1 line).

## What changed, by function (`fontkit-studio.html`)
- `validDetectedGroup`: key list gains `adapter`; `ROLE_ADAPTERS.includes(group.adapter)` required (item 1).
- `buildRoleRequest`: `adapter: group.adapter` (item 2).
- Role rows: `Adapter: <label>` paragraph after the last binding line, before `Safe complete bindings unavailable.`, only for non-plain; labels from the new `ROLE_ADAPTER_LABELS` (item 3).
- `serializeRoleSheet` + new `ROLE_ADAPTER_VARIABLES`: `:root` block before the plain block for body/mono roles with a family; comment updated (item 4).
- `validDetectedReply`: check signature limit 128 -> 1024 (item 6). `validRoleOutcome`: at most 16 losses per property (item 7). Item 5: no change.

## Tests (`tests/test_studio_roles.py`)
`group(..., adapter='plain')`; `canonical_css` learns the templates (`ADAPTER_VARIABLES`); template self-check now asserts `canonical_css(case['roles']) == case['css']` for all five cases and keeps the plain check. New `StudioAdapterTests` (8 tests, Given/When/Then docstrings) before `StudioContractTableTests`; two tests from R2.C0's record added to `StudioContractTableTests`. Expected bytes come from `TEMPLATE_CASES` literals, `BODY_ROOT`/`LEAD_BLOCK` literals and the brief's labels; digests of refused bytes use the test module's own `fnv1a32`.

RED at BASE (`red-s3.log`, Chromium, Studio unchanged): `Ran 11 tests in 422.061s`, `FAILED (errors=19)`. Every adapter test and both contract tests error (mostly `TimeoutError: Page.wait_for_function`). Caveat on the brief's GREEN-at-BASE split: the shared `group()` now carries `adapter`, which BASE refuses, so those characterization tests (bootstrap9/null/number refusals, body-without-family and heading rows, the rejection, the wrong-bytes refusals) are RED at BASE as well, not green; their evidence is the mutants. The template self-check test is GREEN at BASE (test helper only), as expected.
GREEN after the change (`green1-s3.log`): `Ran 11 tests in 8.113s`, `OK`.

## Mutants (`work/mutate-s3.py`, foreground, one test each, `fontkit-studio.html` SHA-256 `9a5d9c11...` before and after every run, see logs `mutants1-3-s3.log`)
| Mutant | Fails | Line / reason |
|---|---|---|
| missing adapter defaults to plain | refuse (missing, null) | 2335 Timeout (fence never renders) |
| enum weakened to `typeof string` | refuse (bootstrap9) | 2335 |
| null accepted | refuse (null) | 2335 |
| send `plain` | send, change | 2354, 2376 `Lists differ` |
| send `bootstrap5-body` always | send, change | 2354, 2376 |
| adapter line on plain rows | render | 2318 `Adapter: undefined` |
| no `:root` block | accept (body, mono, mixed), wrong-bytes, body receipt | 2388, 2417, 2438 |
| `:root` for heading roles | accept (heading, mixed), wrong-bytes | 2388, 2413 |
| `:root` for a body role without family | accept (body-without-family) | 2388 |
| swap the two body variables | accept (body, mixed), body receipt | 2388, 2438 |
| second `:root` block dropped | accept (mixed) | 2388 |
| mono variable under the body name | accept (mono, mixed) | 2388 |
| `rejectRoleOp` clears preview | rejection | 2464 `'' != ':root {...'` |
| `rejectRoleOp` enqueues the op again | rejection | 2466 `3 != 2` |
| check limit 128 | signatures (1024 row) | 2775 `False is not true : Detecting text styles` |
| check limit 1025 | signatures (1025 row) | 2769 Timeout |
| per-property check removed / `<= 17` | losses (17 for one property) | 2797 Timeout |
Line numbers are `tests/test_studio_roles.py`; the "Bootstrap 4 and plain requests" mutant (send `bootstrap5-body`) is also covered by the real-bridge case, not run (below).

## Real-bridge cases (`tests/test_r2_integration.py`): written, NOT RUN (no PATCH_DEP)
Probe without the patch: Studio now refuses every real-bridge Detect (the bridge sends no `adapter`), so the Detect wait times out (`bridge-nodep-s3.log`). That is the expected cause; it says nothing about the cases. Every existing test in this module is red the same way until R2.4's bridge is applied.
1. `test_a_bootstrap_5_body_row_applies_with_its_variables_and_clear_restores_the_page`: serves `fixtures/bootstrap5-static/index.html` with the bridge added at its URL; finds the one row with an `Adapter:` line (asserts exactly one), reads id and name from the row; types `Georgia, serif` and 22; expects the request role `adapter == 'bootstrap5-body'`; after the receipt the four elements (`bs5.button`, `bs5.navigation`, `bs5.label`, `bs.hero.cta`) compute that family and `22px`, `--bs-body-font-family` and `--bs-font-sans-serif` on `:root` (trimmed) equal the family, and `#rolePreviewCss` starts with the `:root` block; after Clear, variables, the four elements' family and size and `main`'s outerHTML equal their pre-apply values and the preview CSS is empty.
2. `test_every_request_from_the_bootstrap_4_fixture_and_the_plain_role_target_carries_the_plain_adapter`: selects every row of each target with a size, presses Apply, expects at least 2 roles all `plain`, and no `Adapter:` line.
Phase 2 must check: which Bootstrap 5 group R2.4 labels body (the test needs exactly one `Adapter:` row and that its bindings cover the four elements); that `Georgia, serif` computes unchanged on a `.btn` (Bootstrap's own `font-family` rules) and that the variables read back through `getPropertyValue(...).trim()`; whether Clear empties `#rolePreviewCss` before the wait times out; `MANY_MATCHES` page (literal edited: `adapter: 'plain'`) with the real bridge.

## Greps and notes
- `git grep -n -E "nearDuplicateIds|bindingComplete" -- tests` at BASE: Studio-bound groups come from `group()` (`test_studio_roles.py:67`, also the `hostile(...)` and `{**group(), ...}` rows built on it) and the `MANY_MATCHES` page (`test_r2_integration.py:217`); the rest are bridge-side reads (`test_role_detection`, `test_role_protocol`) or `role_contract.py` (read-only). W0 added no other Studio-bound literal.
- Unreachable rejection path: Studio sends its latest detection's adapter and newest page version; every bridge-observed change to the Bootstrap evidence advances the page version first (D063, `roleStyleStamp`, `noteRoleMutations`), so the real bridge answers `page-changed` before the adapter check. Only unobserved changes (adapted stylesheet replaced, non-viewport media flip) reach it, and no fixture flow produces them. The `Unsupported adapter` rejection is therefore tested with the fake peer only.
- Gates: `python scripts/verify.py --static-only` passes (JS syntax, provenance); Ruff passes on both test files; `git diff --cached --check` exit 0. No full suite run (override).

## Handoff
- Commit subject: per the combined R2.4 + R2.S3 commit (controller's); draft Studio body: "Studio accepts the adapter the bridge suggests for each detected group, sends it back unchanged, shows a line for the three Bootstrap 5 adapters, and accepts the Bootstrap 5 template bytes (a :root variable block before the plain block of body and mono roles with a family) in receipts and ready snapshots. A selector check may carry 1,024 signatures (D070) and a receipt outcome at most 16 losses for each property (D071)."
- CHANGELOG: replace "Only the plain adapter is accepted so far." with "Detected groups carry the adapter the page suggests (plain, or one of three Bootstrap 5 adapters); Studio sends it back unchanged and accepts the Bootstrap 5 variable template in receipts and snapshots." New visible text: "A role row for a Bootstrap 5 body, monospace or heading role shows `Adapter: Bootstrap 5 body variables`, `Adapter: Bootstrap 5 monospace variable` or `Adapter: Bootstrap 5 heading rule`."
- Plan items: R2.S3 items 1-4, 6, 7 done in code; the real-bridge items and the existing-test fix await phase 2.

# Phase 2 (MODE code, task s3)
Status: DONE. Patch: `.superpowers/sdd/r2/task-s3-code-r1.patch` (SHA-256 `85645bd75d48784ec24070fece4b8e97becc705350ed94fb97ed99b2556af08f`, LF only, three files, `git apply --check -R` passes). Phase 1 staged diff hash verified (`a839ade0...1e8`). PATCH_DEP hash verified (`4c39e12c...ac1`) and applied unstaged in `C:/fks/ts3` (never in my patch).

## Fix of the blocker (deviation: edit of an existing test outside the brief)
Rule forcing it: D071, owner ruling (16 losses per property, item 7). `test_a_receipt_at_one_mib_is_accepted_and_one_byte_more_is_not` padded one property with 64 losses. Applied the controller's one-line change in `tests/test_studio_roles.py` (`build()` spreads padding over `PROPERTY_ORDER`; name, 1 MiB limit and assertions unchanged).
- RED (before): `cd tests; python -m unittest test_studio_roles.StudioRoleApplyTests.test_a_receipt_at_one_mib_is_accepted_and_one_byte_more_is_not` -> `TimeoutError: Page.wait_for_function: Timeout 15000ms exceeded.`, `Ran 1 test in 20.639s`, `FAILED (errors=1)`.
- GREEN (after): same command -> `Ran 1 test in 5.453s`, `OK`.

## Real-bridge cases (Chromium, PATCH_DEP applied)
First run of `test_r2_integration`: 28 tests, 27 ok, 1 error = the Bootstrap 5 case, `Locator.get_attribute: Timeout 30000ms` waiting for `#roleRows > li` filtered `has=#roleRows > li p...`. Root cause: a test bug, not the bridge or Studio. Playwright evaluates `has=` relative to each `li`, so my phase-1 locator (which repeated `#roleRows > li`) never matched (the count assertion before it had passed: exactly one Adapter line). Fix, test only: `row = page.locator('#roleRows > li').filter(has=page.locator('p', has_text=re.compile(r'^Adapter: ')))`. After: that case `Ran 1 test in 1.888s OK`; the whole module passes in the gate. The bridge labelled exactly the body-style group `bootstrap5-body`; Georgia computes unchanged, variables read back trimmed, Clear empties the preview CSS, `MANY_MATCHES` (`adapter: 'plain'`) and the other 26 existing cases pass with the real bridge.
Mutants (`work/mutate-s3p2.py`, `work/mutants-s3p2.log`, foreground, `fontkit-studio.html` SHA-256 `9a5d9c11203c...` before and after each):
| Case | Mutant | Fails |
|---|---|---|
| Bootstrap 5 body row | send `plain` | line 761 `['plain'] != ['bootstrap5-body']` |
| Bootstrap 5 body row | no `:root` block in the preview CSS | line 766 `False is not true` |
| Bootstrap 4 + plain target | send `bootstrap5-body` always | line 789, both targets (`Items in the first set but not the second`) |

## Focused gate and checks
`sh .../tools/gate.sh focused test_studio_roles test_r2_integration test_studio_import_link test_studio_dead_controls test_support` -> `Ran 222 tests in 315.542s`, `OK`, `GATE focused EXIT 0 IN 316s` (`work/gate-s3p2.log`). `python scripts/verify.py --static-only` passes (browser SKIP). Ruff passes on both test files. `git diff --cached --check` exit 0. No full suite (override).

## Material lines of the whole patch
`fontkit-studio.html` +18 -8, `tests/test_r2_integration.py` +66 -1, `tests/test_studio_roles.py` +263 -7: 347 added, 16 removed (brief: about 500).

## Updated Handoff
- Studio body for the R2.4 + R2.S3 commit: "Studio accepts the adapter the bridge suggests for each detected group, sends it back unchanged, shows an Adapter line for the three Bootstrap 5 adapters, and accepts the Bootstrap 5 template bytes (a :root variable block before the plain block of body and mono roles with a family) in receipts and ready snapshots. A selector check may carry 1,024 signatures (D070) and a receipt outcome at most 16 losses for each property (D071). One existing receipt-size test now spreads its padding losses over the six properties to stay within D071." Real-bridge tests cover a Bootstrap 5 body Apply and Clear and the plain adapter on Bootstrap 4 and the role target.
- CHANGELOG: replace "Only the plain adapter is accepted so far." with "Detected groups carry the adapter the page suggests (plain, or one of three Bootstrap 5 adapters); Studio sends it back unchanged and accepts the Bootstrap 5 variable template in receipts and snapshots." New visible text: `Adapter: Bootstrap 5 body variables`, `Adapter: Bootstrap 5 monospace variable`, `Adapter: Bootstrap 5 heading rule` on role rows.
- Plan items done: R2.S3 items 1-4, 6, 7, the existing-test fix, and both real-bridge cases (item 5 needed no change). Note the worktree's `tests/test_role_adapters.py` is untracked PATCH_DEP output; the patch excludes it and the PATCH_DEP files.

## Fix round 1 (tests only, tests/test_studio_roles.py)
Precondition: staged diff of the three files at BASE hashed 85645bd7...f08f; bridge a7e81ca1... Only tests/test_studio_roles.py
changed; fontkit-studio.html and tests/test_r2_integration.py are byte-identical to the approved patch.
- M1: the refused row is now one 17-loss outcome per property in table.PROPERTY_ORDER (subTest `17 for <prop>`); each request
  gets a distinct size (24 + rows so far). Docstring Then updated. Mutants (fontkit-studio.html SHA 9a5d9c11... before and after,
  restored in finally, work/mut_s3r1.py): `ROLE_PROPS.filter(p => p !== "textTransform").every(...)` now ERROR at row
  '17 for textTransform'; `lineHeight` skip ERROR at '17 for lineHeight'; `fontFamily` skip ERROR at '17 for fontFamily'.
- M2: StudioAdapterTests subclasses StudioLegacyCase (its quiet reused, the copy removed); wait_css and wrong_bytes inlined at
  their single callers.
- M3: the render test builds its groups from table.ADAPTERS (name/author = the adapter, body incomplete) and its expected paragraphs
  and row count from the same loop. Scratch copy with a fifth value 'bootstrap5-extra' added to ADAPTERS: the test ERRORs
  (Studio refuses the unknown adapter, wait_for_function times out; 1 test, FAILED errors=1). Copy deleted.
  The other adapter tests need specific adapters (body/heading) by design and are not enumerations.
- M4: the self-check test uses the module's ADAPTER_VARIABLES and ROOT_BLOCK; the local copies are gone.
Focused: `gate.sh focused test_studio_roles test_support` -> Ran 122 tests, OK (GATE focused EXIT 0). ruff check: All checks
passed. `git diff --cached --check`: clean. Patch: task-s3-code-r2.patch (SHA-256 4ccc9fa5...a74), `git apply --check -R` ok.
Patch lines: 3 files, 337 insertions, 21 deletions (fontkit-studio.html 26, tests/test_r2_integration.py 67,
tests/test_studio_roles.py 265 lines changed).

## Controller integration

- Landed from `task-s3-code-r2.patch` (SHA-256 `4ccc9fa5...a94a74`) in the same commit as R2.4.
- It ran in two phases so it could code beside R2.4: without R2.4's bridge first, then with it for the
  real-bridge cases.
- Deviation, forced by D071: `test_a_receipt_at_one_mib_is_accepted_and_one_byte_more_is_not` spreads its padding
  losses over the six properties; its name, its 1 MiB limit and its assertions are unchanged.
- Review: Approved with six Minors. Fix round 1 made the per-property refusal cover every property, reused the
  shared helper, drove the adapter tests from the contract table and kept one copy of the template oracle; the
  scoped re-review is Approved (one optional Minor: a readable assertion for an unknown adapter). The controller
  wrote the CHANGELOG line in product terms (Minor 5) and corrected `tests/role_contract.py`'s stale comment about
  Studio's former 128-signature cap in this commit (Minor 6).
- Landing gates, Windows, Chromium, `FKS_REQUIRE_FIXTURES=1`, with R2.4's, R2.S3's and R2.7F2b's patches on the
  integrated tree at `f2b438f`: the Studio modules, 194 tests in 257.343 s; the bridge role modules, 103 tests in
  160.264 s; the preview, protocol, React and integration modules, 74 tests in 118.011 s; all OK. Static and
  provenance, `node --check`, product-tree Ruff and whitespace pass; exact Ruff reports only the four preserved
  findings under `.agents/`.
- Material lines: 337 added, 21 removed, in three files (D065).
