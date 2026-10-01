# v0.1.1 baseline verification — 2026-09-30

This verifies the standalone responsive-row baseline, not the newly discussed iframe/v0.2 project scope. Independent Task 5 and whole-branch reviews remain controller-owned.

## Artifact and environment

- Branch: `feat/v0.1.1-responsive-rows`; verification base: `95987aef32c32e138489f4549b137aa69a106435`.
- Shipped single-file app: `font_kit_studio_v0.1.1.html`; title and JSON version: 0.1.1.
- Final app SHA-256: `340828acf462c0742b23f6bbdd3bfd7fe20b560c60f517259afd76aaae83c50b`.
- Original received HTML SHA-256: `cae14e847640c71f4e1b528222efe2a21372e73dfcaac0ae20c26d5cf546d949`, preserved at `supplied-v0.1.1`. It is original input, not a verified release.
- Python 3.13.3; Node v24.16.0; development Playwright 1.62.0; Chromium 151.0.7922.34; Firefox 153.0.
- Design source SHA-256: `f8d48f1a23800cf9ac04517575447478b6eff9268333a980a085ac27bc0542a1`; original plan SHA-256: `e3365196c271a6b8f387cdf9382b58217e7d279b8fd7b4f5356aebdea07b8090`.

## Browser evidence

Added passing characterization tests for Library specimen edits, computed 56px display size, theme toggle, mode visibility and composition persistence. Added offline HTTP/HTTPS-blocked local-file checks for both modes at 1600×1200 and 390×844, with dynamic duplicate-ID checks after each preset top-level/child inspector selection. Existing suite verifies all leaf inspectors, PNG/SVG decode/JPEG rejection, row bounds/alignment/weighted tracks, container-only ResizeObserver boundary changes, nested persistence and export safety.

One batched visual/geometry inspection covered desktop and mobile in both engines. No acceptance defect was identified; no app changes or aesthetic redesign were made. Both engines reported:

| Viewport | Document scroll width | Actual canvas width | Row state | Computed tracks |
|---|---:|---:|---|---|
| 1600×1200 | 1600 | 960 | columns | 254px 508px |
| 390×844 | 390 | 352 | stacked | 290px |

No horizontal document overflow in tested Library or Composer states. Mobile controls and inspector are vertically accessible; long full-page screenshots record the inherited flow. Screenshots: `screenshots/desktop.png`, `mobile.png`, `desktop-firefox.png`, `mobile-firefox.png`. Fonts in these offline captures use available fallback faces.

## Mechanical detector

Ran once after UI finalized: `C:/Users/peter/.agents/skills/impeccable/scripts/impeccable.cmd detect --json font_kit_studio_v0.1.1.html` (exit 0). Summary of 16 findings: layout-transition 1; cramped-padding 1; tiny-text 2; undersized-ui-text 10 (Kit preset, Adobe kit IDs, composition preset, slots, canvas width, colour source, custom background, Tailwind family, shade, saved colour); cream-palette 1; decorative-grid advisory 1. These concern incumbent styling and legibility patterns. They are retained as quality limitations, not blanket authorization to redesign the preserved baseline. The grid is a canvas measurement/decorative surface. This check is not a full accessibility audit.

## Limits

Private prior ChatGPT discussion remained inaccessible; requirements come from supplied documents. Parent graph attempts failed with Transport closed; project/generation/coverage unknown, so evidence is direct source and browser runtime, not graph assurance. Adobe kits were not authenticated or verified, and offline tests intentionally block their requests. Desktop/mobile browser viewport checks are not physical-device verification. Visual inspection is bounded to representative presets/states, not exhaustive UI acceptance. No iframe/v0.2 implementation or acceptance is claimed.

## Full reusable verification output

Command run once after final test changes: `python scripts/verify.py` (default full mode). Exact combined output follows.


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
