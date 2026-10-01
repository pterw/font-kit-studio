# Review package

Base: 0db4ca993f00f40c092a66df5643344b106ae7dd
Head: 40ad06dc8d0a52f9e870ee823278731c36713360

## Commits

```text
40ad06d Restore explicitly empty imported kit IDs
```

## Stat

```text
docs/implementation/tasks/task-4-report.md | 11 +++++++++++
 font_kit_studio_v0.1.1.html                |  3 ++-
 tests/test_font_kit_studio_v011.py         | 15 +++++++++++++++
 3 files changed, 28 insertions(+), 1 deletion(-)
```

## Diff

```diff
diff --git a/docs/implementation/tasks/task-4-report.md b/docs/implementation/tasks/task-4-report.md
index 28d549e..75b775b 100644
--- a/docs/implementation/tasks/task-4-report.md
+++ b/docs/implementation/tasks/task-4-report.md
@@ -30,10 +30,21 @@ All commands run at repository root `C:/Users/peter/Documents/Codex/2026-09-30/r
 9. Syntax extraction: `python -c "import re; from pathlib import Path; s=Path('font_kit_studio_v0.1.1.html').read_text(encoding='utf-8'); Path('work/inline.js').write_text('\n'.join(re.findall(r'<script[^>]*>(.*?)</script>',s,re.S)),encoding='utf-8')"`; `node --check work/inline.js` — exit 0, no syntax errors. Scratch is ignored.
 10. `git diff --check` — exit 0, no whitespace errors; informational LF-to-CRLF warnings only. Direct assigned diff review completed.
 
 ## Self-review and limitations
 
 Reviewed hydration publication order, authoritative IDs/types, leaf metadata preservation, recursive reserved-key stripping, property-name reservation and original-object upload binding. Candidate validation does not modify live state before success; all malformed-case tests compare full exports (including IDs/selection) and DOM. New file-reader tests use a controlled real read rather than production hooks. Real image decode and dimensions establish usable PNG/SVG behavior in both engines; JPEG rejection keeps prior image. All behavior tests capture page errors.
 
 Known field normalization deliberately uses incumbent inspector bounds; imported values outside those controls clamp. Canvas width normalizes to 240–2400px or fluid, with 960px fallback. Extra metadata is retained, but all reserved `assetDataUrl` values are cleared regardless of nesting/type. No new deep-row support or binary persistence is introduced. Invalid image bytes with allowed MIME/extension are outside this task's decoder acceptance; PNG/SVG decoder failure handling is not redesigned. File-reader binding prevents changed/deleted-target corruption; multiple concurrent uploads to the same unchanged image are not separately ordered. External Adobe fonts and global Library acceptance remain for final verification. Independent review is pending controller dispatch.
 
 Files: `font_kit_studio_v0.1.1.html`, `tests/test_font_kit_studio_v011.py`, this report. Commit message: `Validate composition imports and harden nested exports`; final handoff supplies identifier (report included in commit). Nonassigned controller/tooling changes are not staged.
+
+## Review fix round 1 of 5 — explicit empty kit IDs
+
+Read task-4-review.md; verified fix baseline `0db4ca993f00f40c092a66df5643344b106ae7dd`. Preserved controller ledgers and untracked review files. Important finding confirmed: the importer normalized empty IDs but only published nonempty candidates, contaminating kit-free round trips with receiving IDs.
+
+Added a both-browser regression that starts with populated receiving input `abc123, def456`, imports an old document with no kitIds and verifies input/export retain those IDs, then imports explicit `kitIds:[]` and requires empty input/export. This defines missing-field compatibility separately: absence retains receiving selection; an explicitly supplied field publishes the normalized candidate, including an empty array. Changed only the publication condition plus an explanatory comment; malformed explicitly supplied kitIds likewise normalize to empty under existing candidate normalization.
+
+- **RED** before fix: `python -m unittest discover -s tests -p test_font_kit_studio_v011.py -k task4_explicit_empty_kits -v` — `Ran 1 test in 4.543s`, `FAILED (failures=2)`, exit 1. Chromium and Firefox both fail with `AssertionError: 'abc123, def456' != ''`. Missing-field preservation assertions pass before the failing empty-field assertion.
+- **GREEN** after fix: same command — `Ran 1 test in 5.492s`, `OK`, exit 0. Both browsers verify missing-field preservation and explicit-empty input/export; pageerror lists empty.
+- Repeated exact inline-JavaScript extraction command from step 9; `node --check work/inline.js`; `git diff --check` — exit 0, syntax/whitespace clean, informational line-ending warnings only.
+- Self-review: publication remains after candidate validation; no import state changes on rejection. Object.hasOwn distinguishes an absent legacy field from a deliberately supplied empty field. Only the scoped regression rerun as instructed; no repeat full suite for this small review fix. Commit message: `Restore explicitly empty imported kit IDs`; identifier supplied in fix handoff. Parent will run scoped independent re-review.
diff --git a/font_kit_studio_v0.1.1.html b/font_kit_studio_v0.1.1.html
index be12ac9..0055847 100644
--- a/font_kit_studio_v0.1.1.html
+++ b/font_kit_studio_v0.1.1.html
@@ -2527,21 +2527,22 @@ if (remembered) kitId.value = remembered;
         Object.keys(defaults).forEach(key => { if (typeof background[key] !== "string") background[key] = defaults[key]; });
         if (!["custom", "tailwind", "saved"].includes(background.source)) background.source = defaults.source;
         if (!CSS.supports("color", background.hex)) background.hex = defaults.hex;
         const slots = incoming.slots.slice(0,8).map(raw => hydrateSlot(raw, 0));
         if (!slots.length) slots.push(makeTextSlot("Custom", "gotham"));
         const width = String(incoming.canvasWidth || "960");
         const kitIds = Array.isArray(data.kitIds) ? normalizeKitIds(data.kitIds.filter(id => typeof id === "string").join(", ")) : [];
         // Only publish a fully hydrated candidate; failed validation leaves live state intact.
         Object.assign(state, { canvasWidth:width === "100%" ? width : String(rowNumber(width, 960, 240, 2400)),
           background, slots, selectedId:slots[0].id });
-        if (kitIds.length) composerKitIds.value = kitIds.join(", ");
+        // Legacy documents without kitIds retain the receiving selection; explicit IDs replace it, even when empty.
+        if (Object.hasOwn(data, "kitIds")) composerKitIds.value = kitIds.join(", ");
         familyOptions(canvasBgFamily, state.background.family);
         populateSavedColors(canvasSavedColor, state.background.saved);
         syncCompositionControls();
         renderComposer();
         composerStatus.textContent = "Composition imported. Image assets must be reselected in v0.1.1.";
       } catch (err) {
         composerStatus.textContent = `Import failed: ${err.message}`;
       }
     };
     reader.readAsText(file);
diff --git a/tests/test_font_kit_studio_v011.py b/tests/test_font_kit_studio_v011.py
index 9a3a948..3dfbeba 100644
--- a/tests/test_font_kit_studio_v011.py
+++ b/tests/test_font_kit_studio_v011.py
@@ -106,20 +106,35 @@ class BrowserCase(unittest.TestCase):
         for engine in ('chromium', 'firefox'):
             with self.subTest(engine=engine):
                 page, errors = self.page(engine)
                 before = self.export(page)
                 status = self.import_document(page, {'composition': {'canvasWidth':'640',
                     'background':42, 'slots':[{'type':'text', 'text':'replacement'}]}})
                 self.assertTrue(status.startswith('Import failed:'), status)
                 self.assertEqual(self.export(page), before)
                 self.assertEqual(errors, [])
 
+    def test_task4_explicit_empty_kits_and_missing_field_compatibility(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                kits = page.locator('#composerKitIds')
+                kits.fill('abc123, def456')
+                legacy = {'version':'0.1.0', 'composition':{'slots':[{'type':'text','text':'legacy'}]}}
+                self.assertIn('Composition imported.', self.import_document(page, legacy))
+                self.assertEqual(kits.input_value(), 'abc123, def456')
+                self.assertEqual(self.export(page)['kitIds'], ['abc123','def456'])
+                self.assertIn('Composition imported.', self.import_document(page, {**legacy,'kitIds':[]}))
+                self.assertEqual(kits.input_value(), '')
+                self.assertEqual(self.export(page)['kitIds'], [])
+                self.assertEqual(errors, [])
+
     def test_task4_css_slug_and_property_suffix_collisions(self):
         for engine in ('chromium', 'firefox'):
             with self.subTest(engine=engine):
                 page, errors = self.page(engine)
                 self.import_slots(page, [{'type':'row', 'childCount':4, 'children':[
                     {'type':'text', 'role':role} for role in ('Body','Body','Body-2','Body-size')]}])
                 page.locator('#exportCss').click()
                 css = page.locator('#exportDialogText').input_value()
                 declarations = re.findall(r'^\s*(--[a-z0-9-]+):', css, re.M)
                 self.assertEqual(len(declarations),len(set(declarations)),css)
```
