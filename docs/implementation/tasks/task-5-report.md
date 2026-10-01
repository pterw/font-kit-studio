# Task 5 report — v0.1.1 baseline final verification

## Result and ownership

Baseline acceptance checks pass at base `95987aef32c32e138489f4549b137aa69a106435`, branch `feat/v0.1.1-responsive-rows`. Only tests, this report, verification.md and four screenshot files were changed. App HTML remains unchanged by Task 5. Controller-owned README/scripts/plans/ledgers and other agents' edits were preserved. Independent Task 5 review and whole-branch review are pending controller gates. This does not complete iframe/v0.2 scope.

Read Task 5 brief first, AGENTS.md, README, active plan/progress/deviations and supplied responsive-row design. No root DESIGN.md exists; used the supplied authoritative design. Parent Verify graph attempts returned Transport closed; no graph project/generation or coverage claim is made. No subagents were spawned.

## Commands and evidence

- `python -m unittest discover -s tests -p test_font_kit_studio_v011.py -k task5 -v`: 2 tests, 17.078s, OK. Both loop Chromium and Firefox. These characterize passing inherited behavior; no RED was manufactured and no product fix was required.
- `python work/capture_task5.py`: exit 0; one batch captured desktop/mobile in both engines with HTTP/HTTPS requests blocked. Geometry table and filenames are in verification.md. All four screenshots were visually inspected once; no acceptance defect, no confirm/fix batch needed.
- `C:/Users/peter/.agents/skills/impeccable/scripts/impeccable.cmd detect --json font_kit_studio_v0.1.1.html`: exit 0, once after final UI; 16 findings summarized in verification.md. Existing small text, width animation and baseline palette/grid remain recorded quality limits, not redesign authorization.
- `python scripts/verify.py` (default full mode, once after final test changes): exit 0. Full exact combined output retained below and in verification.md; 20 tests, 111.639s, OK; 38 static unique IDs; one executable inline script syntax-valid; all three provenance hashes pass.
- `git diff --check`: exit 0, no whitespace errors (Git warns about future LF→CRLF conversion).
- `Get-FileHash font_kit_studio_v0.1.1.html -Algorithm SHA256`: final SHA `340828acf462c0742b23f6bbdd3bfd7fe20b560c60f517259afd76aaae83c50b`.

Added Library sample/size/theme behavior, mode visibility and composition-preservation checks. Added offline local-file desktop/mobile overflow and actual-canvas-collapse checks, with duplicate DOM IDs checked for every preset top-level/child inspector state. Prior tests cover the implementation's row model, inspectors, images and persistence. Python 3.13.3, Node v24.16.0, installed Playwright 1.62.0, Chromium 151.0.7922.34 and Firefox 153.0.

## Self-review and limits

Tests assert rendered/computed behavior and exported state, not only symbols. Dynamic IDs supplement static parser checks. Offline requests blocked verifies core local functionality without Adobe font availability. Mobile viewport is emulation, not a physical-device test. Representative visual inspection is bounded, not exhaustive accessibility/UI certification. Private chat unavailable; Adobe kits unauthenticated; graph unavailable. Supplied v0.1.1 tag preserves original source, not an independently verified release. Final source/design/plan hashes and full limits are also in verification.md. No app byte change means exact final app hash remains that established before Task 5.

Commit: this report and its sibling verification files are included in the Task 5 verification commit; exact commit ID is returned to the controller (self-referential Git hash is not embedded).

## Exact full verifier output

```text
PASS HTML IDs: 38 unique static IDs
PASS JavaScript syntax: 1 executable inline blocks
SHA-256 font_kit_studio_v0.1.1.html: 340828acf462c0742b23f6bbdd3bfd7fe20b560c60f517259afd76aaae83c50b
PASS provenance: supplied-v0.1.1:font_kit_studio_v0.1.1.html cae14e847640c71f4e1b528222efe2a21372e73dfcaac0ae20c26d5cf546d949
PASS provenance: supplied-v0.1.1:docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows-design.md f8d48f1a23800cf9ac04517575447478b6eff9268333a980a085ac27bc0542a1
PASS provenance: supplied-v0.1.1:docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows.md e3365196c271a6b8f387cdf9382b58217e7d279b8fd7b4f5356aebdea07b8090
RUN unittest/browser tests
test_fractional_child_counts (test_font_kit_studio_v011.BrowserCase.test_fractional_child_counts) ... ok
test_fractional_inspector_count_without_import (test_font_kit_studio_v011.BrowserCase.test_fractional_inspector_count_without_import) ... ok
test_malformed_row_values_are_normalized (test_font_kit_studio_v011.BrowserCase.test_malformed_row_values_are_normalized) ... ok
test_nested_rows_drop_hidden_descendants_and_preserve_leaf_fields (test_font_kit_studio_v011.BrowserCase.test_nested_rows_drop_hidden_descendants_and_preserve_leaf_fields) ... ok
test_row_controls_and_leaf_inspectors (test_font_kit_studio_v011.BrowserCase.test_row_controls_and_leaf_inspectors) ... ok
test_row_inspector_normalized_values_and_labels (test_font_kit_studio_v011.BrowserCase.test_row_inspector_normalized_values_and_labels) ... ok
test_task4_css_roles_are_valid_and_collision_free (test_font_kit_studio_v011.BrowserCase.test_task4_css_roles_are_valid_and_collision_free) ... ok
test_task4_css_slug_and_property_suffix_collisions (test_font_kit_studio_v011.BrowserCase.test_task4_css_slug_and_property_suffix_collisions) ... ok
test_task4_explicit_empty_kits_and_missing_field_compatibility (test_font_kit_studio_v011.BrowserCase.test_task4_explicit_empty_kits_and_missing_field_compatibility) ... ok
test_task4_failed_background_import_preserves_state (test_font_kit_studio_v011.BrowserCase.test_task4_failed_background_import_preserves_state) ... ok
test_task4_failed_import_is_transactional (test_font_kit_studio_v011.BrowserCase.test_task4_failed_import_is_transactional) ... ok
test_task4_image_upload_decode_rejection_and_selection_race (test_font_kit_studio_v011.BrowserCase.test_task4_image_upload_decode_rejection_and_selection_race) ... ok
test_task4_known_leaf_fields_have_safe_shapes (test_font_kit_studio_v011.BrowserCase.test_task4_known_leaf_fields_have_safe_shapes) ... ok
test_task4_recursive_asset_privacy_and_old_json_round_trip (test_font_kit_studio_v011.BrowserCase.test_task4_recursive_asset_privacy_and_old_json_round_trip) ... ok
test_task5_library_controls_and_mode_preservation (test_font_kit_studio_v011.BrowserCase.test_task5_library_controls_and_mode_preservation) ... ok
test_task5_offline_layouts_and_dynamic_ids (test_font_kit_studio_v011.BrowserCase.test_task5_offline_layouts_and_dynamic_ids) ... ok
test_unequal_child_alignment_geometry (test_font_kit_studio_v011.BrowserCase.test_unequal_child_alignment_geometry) ... ok
test_valid_row_factory_and_child_selection (test_font_kit_studio_v011.BrowserCase.test_valid_row_factory_and_child_selection) ... ok
test_weighted_columns_gaps_and_resize_observer_boundaries (test_font_kit_studio_v011.BrowserCase.test_weighted_columns_gaps_and_resize_observer_boundaries) ... ok
test_version_and_existing_model (test_font_kit_studio_v011.StructureTests.test_version_and_existing_model) ... ok

----------------------------------------------------------------------
Ran 20 tests in 111.639s

OK
PASS unittest/browser tests
```
