# Review package

Base: 95987aef32c32e138489f4549b137aa69a106435
Head: 068b7c1075d84aa92322f42fa5d1bbf943a7bb38

## Commits

```text
068b7c1 test: verify standalone responsive row baseline
```

## Stat

```text
.../implementation/screenshots/desktop-firefox.png | Bin 0 -> 165312 bytes
 docs/implementation/screenshots/desktop.png        | Bin 0 -> 165311 bytes
 docs/implementation/screenshots/mobile-firefox.png | Bin 0 -> 124037 bytes
 docs/implementation/screenshots/mobile.png         | Bin 0 -> 135327 bytes
 docs/implementation/tasks/task-5-report.md         |  62 +++++++++++++++++
 docs/implementation/verification.md                |  74 +++++++++++++++++++++
 tests/test_font_kit_studio_v011.py                 |  61 +++++++++++++++++
 7 files changed, 197 insertions(+)
```

## Diff

```diff
diff --git a/docs/implementation/screenshots/desktop-firefox.png b/docs/implementation/screenshots/desktop-firefox.png
new file mode 100644
index 0000000..850f79b
Binary files /dev/null and b/docs/implementation/screenshots/desktop-firefox.png differ
diff --git a/docs/implementation/screenshots/desktop.png b/docs/implementation/screenshots/desktop.png
new file mode 100644
index 0000000..5074d43
Binary files /dev/null and b/docs/implementation/screenshots/desktop.png differ
diff --git a/docs/implementation/screenshots/mobile-firefox.png b/docs/implementation/screenshots/mobile-firefox.png
new file mode 100644
index 0000000..4e3717b
Binary files /dev/null and b/docs/implementation/screenshots/mobile-firefox.png differ
diff --git a/docs/implementation/screenshots/mobile.png b/docs/implementation/screenshots/mobile.png
new file mode 100644
index 0000000..83af72f
Binary files /dev/null and b/docs/implementation/screenshots/mobile.png differ
diff --git a/docs/implementation/tasks/task-5-report.md b/docs/implementation/tasks/task-5-report.md
new file mode 100644
index 0000000..f48c3d7
--- /dev/null
+++ b/docs/implementation/tasks/task-5-report.md
@@ -0,0 +1,62 @@
+# Task 5 report — v0.1.1 baseline final verification
+
+## Result and ownership
+
+Baseline acceptance checks pass at base `95987aef32c32e138489f4549b137aa69a106435`, branch `feat/v0.1.1-responsive-rows`. Only tests, this report, verification.md and four screenshot files were changed. App HTML remains unchanged by Task 5. Controller-owned README/scripts/plans/ledgers and other agents' edits were preserved. Independent Task 5 review and whole-branch review are pending controller gates. This does not complete iframe/v0.2 scope.
+
+Read Task 5 brief first, AGENTS.md, README, active plan/progress/deviations and supplied responsive-row design. No root DESIGN.md exists; used the supplied authoritative design. Parent Verify graph attempts returned Transport closed; no graph project/generation or coverage claim is made. No subagents were spawned.
+
+## Commands and evidence
+
+- `python -m unittest discover -s tests -p test_font_kit_studio_v011.py -k task5 -v`: 2 tests, 17.078s, OK. Both loop Chromium and Firefox. These characterize passing inherited behavior; no RED was manufactured and no product fix was required.
+- `python work/capture_task5.py`: exit 0; one batch captured desktop/mobile in both engines with HTTP/HTTPS requests blocked. Geometry table and filenames are in verification.md. All four screenshots were visually inspected once; no acceptance defect, no confirm/fix batch needed.
+- `C:/Users/peter/.agents/skills/impeccable/scripts/impeccable.cmd detect --json font_kit_studio_v0.1.1.html`: exit 0, once after final UI; 16 findings summarized in verification.md. Existing small text, width animation and baseline palette/grid remain recorded quality limits, not redesign authorization.
+- `python scripts/verify.py` (default full mode, once after final test changes): exit 0. Full exact combined output retained below and in verification.md; 20 tests, 111.639s, OK; 38 static unique IDs; one executable inline script syntax-valid; all three provenance hashes pass.
+- `git diff --check`: exit 0, no whitespace errors (Git warns about future LF→CRLF conversion).
+- `Get-FileHash font_kit_studio_v0.1.1.html -Algorithm SHA256`: final SHA `340828acf462c0742b23f6bbdd3bfd7fe20b560c60f517259afd76aaae83c50b`.
+
+Added Library sample/size/theme behavior, mode visibility and composition-preservation checks. Added offline local-file desktop/mobile overflow and actual-canvas-collapse checks, with duplicate DOM IDs checked for every preset top-level/child inspector state. Prior tests cover the implementation's row model, inspectors, images and persistence. Python 3.13.3, Node v24.16.0, installed Playwright 1.62.0, Chromium 151.0.7922.34 and Firefox 153.0.
+
+## Self-review and limits
+
+Tests assert rendered/computed behavior and exported state, not only symbols. Dynamic IDs supplement static parser checks. Offline requests blocked verifies core local functionality without Adobe font availability. Mobile viewport is emulation, not a physical-device test. Representative visual inspection is bounded, not exhaustive accessibility/UI certification. Private chat unavailable; Adobe kits unauthenticated; graph unavailable. Supplied v0.1.1 tag preserves original source, not an independently verified release. Final source/design/plan hashes and full limits are also in verification.md. No app byte change means exact final app hash remains that established before Task 5.
+
+Commit: this report and its sibling verification files are included in the Task 5 verification commit; exact commit ID is returned to the controller (self-referential Git hash is not embedded).
+
+## Exact full verifier output
+
+```text
+PASS HTML IDs: 38 unique static IDs
+PASS JavaScript syntax: 1 executable inline blocks
+SHA-256 font_kit_studio_v0.1.1.html: 340828acf462c0742b23f6bbdd3bfd7fe20b560c60f517259afd76aaae83c50b
+PASS provenance: supplied-v0.1.1:font_kit_studio_v0.1.1.html cae14e847640c71f4e1b528222efe2a21372e73dfcaac0ae20c26d5cf546d949
+PASS provenance: supplied-v0.1.1:docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows-design.md f8d48f1a23800cf9ac04517575447478b6eff9268333a980a085ac27bc0542a1
+PASS provenance: supplied-v0.1.1:docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows.md e3365196c271a6b8f387cdf9382b58217e7d279b8fd7b4f5356aebdea07b8090
+RUN unittest/browser tests
+test_fractional_child_counts (test_font_kit_studio_v011.BrowserCase.test_fractional_child_counts) ... ok
+test_fractional_inspector_count_without_import (test_font_kit_studio_v011.BrowserCase.test_fractional_inspector_count_without_import) ... ok
+test_malformed_row_values_are_normalized (test_font_kit_studio_v011.BrowserCase.test_malformed_row_values_are_normalized) ... ok
+test_nested_rows_drop_hidden_descendants_and_preserve_leaf_fields (test_font_kit_studio_v011.BrowserCase.test_nested_rows_drop_hidden_descendants_and_preserve_leaf_fields) ... ok
+test_row_controls_and_leaf_inspectors (test_font_kit_studio_v011.BrowserCase.test_row_controls_and_leaf_inspectors) ... ok
+test_row_inspector_normalized_values_and_labels (test_font_kit_studio_v011.BrowserCase.test_row_inspector_normalized_values_and_labels) ... ok
+test_task4_css_roles_are_valid_and_collision_free (test_font_kit_studio_v011.BrowserCase.test_task4_css_roles_are_valid_and_collision_free) ... ok
+test_task4_css_slug_and_property_suffix_collisions (test_font_kit_studio_v011.BrowserCase.test_task4_css_slug_and_property_suffix_collisions) ... ok
+test_task4_explicit_empty_kits_and_missing_field_compatibility (test_font_kit_studio_v011.BrowserCase.test_task4_explicit_empty_kits_and_missing_field_compatibility) ... ok
+test_task4_failed_background_import_preserves_state (test_font_kit_studio_v011.BrowserCase.test_task4_failed_background_import_preserves_state) ... ok
+test_task4_failed_import_is_transactional (test_font_kit_studio_v011.BrowserCase.test_task4_failed_import_is_transactional) ... ok
+test_task4_image_upload_decode_rejection_and_selection_race (test_font_kit_studio_v011.BrowserCase.test_task4_image_upload_decode_rejection_and_selection_race) ... ok
+test_task4_known_leaf_fields_have_safe_shapes (test_font_kit_studio_v011.BrowserCase.test_task4_known_leaf_fields_have_safe_shapes) ... ok
+test_task4_recursive_asset_privacy_and_old_json_round_trip (test_font_kit_studio_v011.BrowserCase.test_task4_recursive_asset_privacy_and_old_json_round_trip) ... ok
+test_task5_library_controls_and_mode_preservation (test_font_kit_studio_v011.BrowserCase.test_task5_library_controls_and_mode_preservation) ... ok
+test_task5_offline_layouts_and_dynamic_ids (test_font_kit_studio_v011.BrowserCase.test_task5_offline_layouts_and_dynamic_ids) ... ok
+test_unequal_child_alignment_geometry (test_font_kit_studio_v011.BrowserCase.test_unequal_child_alignment_geometry) ... ok
+test_valid_row_factory_and_child_selection (test_font_kit_studio_v011.BrowserCase.test_valid_row_factory_and_child_selection) ... ok
+test_weighted_columns_gaps_and_resize_observer_boundaries (test_font_kit_studio_v011.BrowserCase.test_weighted_columns_gaps_and_resize_observer_boundaries) ... ok
+test_version_and_existing_model (test_font_kit_studio_v011.StructureTests.test_version_and_existing_model) ... ok
+
+----------------------------------------------------------------------
+Ran 20 tests in 111.639s
+
+OK
+PASS unittest/browser tests
+```
diff --git a/docs/implementation/verification.md b/docs/implementation/verification.md
new file mode 100644
index 0000000..31b9b5d
--- /dev/null
+++ b/docs/implementation/verification.md
@@ -0,0 +1,74 @@
+# v0.1.1 baseline verification — 2026-09-30
+
+This verifies the standalone responsive-row baseline, not the newly discussed iframe/v0.2 project scope. Independent Task 5 and whole-branch reviews remain controller-owned.
+
+## Artifact and environment
+
+- Branch: `feat/v0.1.1-responsive-rows`; verification base: `95987aef32c32e138489f4549b137aa69a106435`.
+- Shipped single-file app: `font_kit_studio_v0.1.1.html`; title and JSON version: 0.1.1.
+- Final app SHA-256: `340828acf462c0742b23f6bbdd3bfd7fe20b560c60f517259afd76aaae83c50b`.
+- Original received HTML SHA-256: `cae14e847640c71f4e1b528222efe2a21372e73dfcaac0ae20c26d5cf546d949`, preserved at `supplied-v0.1.1`. It is original input, not a verified release.
+- Python 3.13.3; Node v24.16.0; development Playwright 1.62.0; Chromium 151.0.7922.34; Firefox 153.0.
+- Design source SHA-256: `f8d48f1a23800cf9ac04517575447478b6eff9268333a980a085ac27bc0542a1`; original plan SHA-256: `e3365196c271a6b8f387cdf9382b58217e7d279b8fd7b4f5356aebdea07b8090`.
+
+## Browser evidence
+
+Added passing characterization tests for Library specimen edits, computed 56px display size, theme toggle, mode visibility and composition persistence. Added offline HTTP/HTTPS-blocked local-file checks for both modes at 1600×1200 and 390×844, with dynamic duplicate-ID checks after each preset top-level/child inspector selection. Existing suite verifies all leaf inspectors, PNG/SVG decode/JPEG rejection, row bounds/alignment/weighted tracks, container-only ResizeObserver boundary changes, nested persistence and export safety.
+
+One batched visual/geometry inspection covered desktop and mobile in both engines. No acceptance defect was identified; no app changes or aesthetic redesign were made. Both engines reported:
+
+| Viewport | Document scroll width | Actual canvas width | Row state | Computed tracks |
+|---|---:|---:|---|---|
+| 1600×1200 | 1600 | 960 | columns | 254px 508px |
+| 390×844 | 390 | 352 | stacked | 290px |
+
+No horizontal document overflow in tested Library or Composer states. Mobile controls and inspector are vertically accessible; long full-page screenshots record the inherited flow. Screenshots: `screenshots/desktop.png`, `mobile.png`, `desktop-firefox.png`, `mobile-firefox.png`. Fonts in these offline captures use available fallback faces.
+
+## Mechanical detector
+
+Ran once after UI finalized: `C:/Users/peter/.agents/skills/impeccable/scripts/impeccable.cmd detect --json font_kit_studio_v0.1.1.html` (exit 0). Summary of 16 findings: layout-transition 1; cramped-padding 1; tiny-text 2; undersized-ui-text 10 (Kit preset, Adobe kit IDs, composition preset, slots, canvas width, colour source, custom background, Tailwind family, shade, saved colour); cream-palette 1; decorative-grid advisory 1. These concern incumbent styling and legibility patterns. They are retained as quality limitations, not blanket authorization to redesign the preserved baseline. The grid is a canvas measurement/decorative surface. This check is not a full accessibility audit.
+
+## Limits
+
+Private prior ChatGPT discussion remained inaccessible; requirements come from supplied documents. Parent graph attempts failed with Transport closed; project/generation/coverage unknown, so evidence is direct source and browser runtime, not graph assurance. Adobe kits were not authenticated or verified, and offline tests intentionally block their requests. Desktop/mobile browser viewport checks are not physical-device verification. Visual inspection is bounded to representative presets/states, not exhaustive UI acceptance. No iframe/v0.2 implementation or acceptance is claimed.
+
+## Full reusable verification output
+
+Command run once after final test changes: `python scripts/verify.py` (default full mode). Exact combined output follows.
+
+
+```text
+PASS HTML IDs: 38 unique static IDs
+PASS JavaScript syntax: 1 executable inline blocks
+SHA-256 font_kit_studio_v0.1.1.html: 340828acf462c0742b23f6bbdd3bfd7fe20b560c60f517259afd76aaae83c50b
+PASS provenance: supplied-v0.1.1:font_kit_studio_v0.1.1.html cae14e847640c71f4e1b528222efe2a21372e73dfcaac0ae20c26d5cf546d949
+PASS provenance: supplied-v0.1.1:docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows-design.md f8d48f1a23800cf9ac04517575447478b6eff9268333a980a085ac27bc0542a1
+PASS provenance: supplied-v0.1.1:docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows.md e3365196c271a6b8f387cdf9382b58217e7d279b8fd7b4f5356aebdea07b8090
+RUN unittest/browser tests
+test_fractional_child_counts (test_font_kit_studio_v011.BrowserCase.test_fractional_child_counts) ... ok
+test_fractional_inspector_count_without_import (test_font_kit_studio_v011.BrowserCase.test_fractional_inspector_count_without_import) ... ok
+test_malformed_row_values_are_normalized (test_font_kit_studio_v011.BrowserCase.test_malformed_row_values_are_normalized) ... ok
+test_nested_rows_drop_hidden_descendants_and_preserve_leaf_fields (test_font_kit_studio_v011.BrowserCase.test_nested_rows_drop_hidden_descendants_and_preserve_leaf_fields) ... ok
+test_row_controls_and_leaf_inspectors (test_font_kit_studio_v011.BrowserCase.test_row_controls_and_leaf_inspectors) ... ok
+test_row_inspector_normalized_values_and_labels (test_font_kit_studio_v011.BrowserCase.test_row_inspector_normalized_values_and_labels) ... ok
+test_task4_css_roles_are_valid_and_collision_free (test_font_kit_studio_v011.BrowserCase.test_task4_css_roles_are_valid_and_collision_free) ... ok
+test_task4_css_slug_and_property_suffix_collisions (test_font_kit_studio_v011.BrowserCase.test_task4_css_slug_and_property_suffix_collisions) ... ok
+test_task4_explicit_empty_kits_and_missing_field_compatibility (test_font_kit_studio_v011.BrowserCase.test_task4_explicit_empty_kits_and_missing_field_compatibility) ... ok
+test_task4_failed_background_import_preserves_state (test_font_kit_studio_v011.BrowserCase.test_task4_failed_background_import_preserves_state) ... ok
+test_task4_failed_import_is_transactional (test_font_kit_studio_v011.BrowserCase.test_task4_failed_import_is_transactional) ... ok
+test_task4_image_upload_decode_rejection_and_selection_race (test_font_kit_studio_v011.BrowserCase.test_task4_image_upload_decode_rejection_and_selection_race) ... ok
+test_task4_known_leaf_fields_have_safe_shapes (test_font_kit_studio_v011.BrowserCase.test_task4_known_leaf_fields_have_safe_shapes) ... ok
+test_task4_recursive_asset_privacy_and_old_json_round_trip (test_font_kit_studio_v011.BrowserCase.test_task4_recursive_asset_privacy_and_old_json_round_trip) ... ok
+test_task5_library_controls_and_mode_preservation (test_font_kit_studio_v011.BrowserCase.test_task5_library_controls_and_mode_preservation) ... ok
+test_task5_offline_layouts_and_dynamic_ids (test_font_kit_studio_v011.BrowserCase.test_task5_offline_layouts_and_dynamic_ids) ... ok
+test_unequal_child_alignment_geometry (test_font_kit_studio_v011.BrowserCase.test_unequal_child_alignment_geometry) ... ok
+test_valid_row_factory_and_child_selection (test_font_kit_studio_v011.BrowserCase.test_valid_row_factory_and_child_selection) ... ok
+test_weighted_columns_gaps_and_resize_observer_boundaries (test_font_kit_studio_v011.BrowserCase.test_weighted_columns_gaps_and_resize_observer_boundaries) ... ok
+test_version_and_existing_model (test_font_kit_studio_v011.StructureTests.test_version_and_existing_model) ... ok
+
+----------------------------------------------------------------------
+Ran 20 tests in 111.639s
+
+OK
+PASS unittest/browser tests
+```
diff --git a/tests/test_font_kit_studio_v011.py b/tests/test_font_kit_studio_v011.py
index 3dfbeba..c48ce54 100644
--- a/tests/test_font_kit_studio_v011.py
+++ b/tests/test_font_kit_studio_v011.py
@@ -56,20 +56,81 @@ class BrowserCase(unittest.TestCase):
             const rect = element => {
                 const r = element.getBoundingClientRect();
                 return {x:r.x, y:r.y, width:r.width, height:r.height, bottom:r.bottom};
             };
             return {layout:rect(layout), collapsed:layout.classList.contains('is-collapsed'),
                 children:[...layout.children].map(rect),
                 order:[...layout.children].map(child => child.dataset.rowChild),
                 gap:parseFloat(getComputedStyle(layout).gap)};
         }''')
 
+    def test_task5_library_controls_and_mode_preservation(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                page.locator('#modeLibrary').click()
+                self.assertTrue(page.locator('#libraryView').is_visible())
+                self.assertFalse(page.locator('#composerView').is_visible())
+                samples = page.locator('.big-sample')
+                self.assertGreater(samples.count(), 0)
+                page.locator('#sampleText').fill('Offline Library acceptance')
+                self.assertTrue(all(text == 'Offline Library acceptance' for text in samples.all_text_contents()))
+                page.locator('#sizeRange').fill('56')
+                page.locator('#sizeRange').dispatch_event('input')
+                self.assertEqual(samples.first.evaluate('el => getComputedStyle(el).fontSize'), '56px')
+                page.locator('#themeToggle').click()
+                self.assertEqual(page.locator('#themeToggle').get_attribute('aria-pressed'), 'true')
+                page.locator('#modeComposer').click()
+                self.assertTrue(page.locator('#composerView').is_visible())
+                page.locator('#compositionPreset').select_option('rowdemo')
+                page.locator('#applyPreset').click()
+                before = self.export(page)
+                page.locator('#modeLibrary').click()
+                self.assertEqual(page.locator('#sampleText').input_value(), 'Offline Library acceptance')
+                page.locator('#modeComposer').click()
+                self.assertEqual(self.export(page), before)
+                self.assertEqual(errors, [])
+
+    def test_task5_offline_layouts_and_dynamic_ids(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                browser = getattr(self.runtime, engine).launch()
+                self.browsers.append(browser)
+                page = browser.new_page()
+                page.route('https://**/*', lambda route: route.abort())
+                page.route('http://**/*', lambda route: route.abort())
+                errors = []
+                page.on('pageerror', lambda error: errors.append(str(error)))
+                page.goto(HTML.as_uri())
+                for width, height in ((1600,1200),(390,844)):
+                    page.set_viewport_size({'width':width,'height':height})
+                    page.locator('#modeLibrary').click()
+                    self.assertGreater(page.locator('.big-sample').count(), 0)
+                    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width)
+                    page.locator('#modeComposer').click()
+                    page.locator('#compositionPreset').select_option('rowdemo')
+                    page.locator('#applyPreset').click()
+                    page.wait_for_timeout(250)
+                    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'), width)
+                    canvas_width = page.locator('#composerCanvas').evaluate('el => el.getBoundingClientRect().width')
+                    collapsed = page.locator('.row-layout').evaluate('el => el.classList.contains("is-collapsed")')
+                    self.assertEqual(collapsed, canvas_width <= 680)
+                    for target in ('#composerCanvas > .flow-slot', '.row-child'):
+                        for index in range(page.locator(target).count()):
+                            page.locator(target).nth(index).click(position={'x':3,'y':3})
+                            duplicates = page.evaluate('''() => {
+                                const ids = [...document.querySelectorAll('[id]')].map(el => el.id);
+                                return ids.filter((id,index) => ids.indexOf(id) !== index);
+                            }''')
+                            self.assertEqual(duplicates, [])
+                self.assertEqual(errors, [])
+
     def test_task4_failed_import_is_transactional(self):
         for engine in ('chromium', 'firefox'):
             with self.subTest(engine=engine):
                 page, errors = self.page(engine)
                 before = self.export(page)
                 before_canvas = page.locator('#composerCanvas').inner_html()
                 for malformed in ([None], [42], [[]], [{'type':'row', 'children':{}}],
                                   [{'type':'row', 'children':[{'type':'text'}, None]}]):
                     status = self.import_document(page, {'composition': {'canvasWidth':'640',
                         'background':{'source':'custom', 'hex':'#ffffff'}, 'slots':malformed}})
```
