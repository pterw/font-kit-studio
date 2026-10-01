# Review package

Base: ba881ea688f2ea5beb7f7131aad14b82ef2f4b8a
Head: cc9ebd5204596744ce41142f91ee50e9db6e0fe0

## Commits

```text
cc9ebd5 Fix row model normalization and leaf-only hydration
```

## Stat

```text
docs/implementation/tasks/task-1-report.md |  35 ++++++++
 font_kit_studio_v0.1.1.html                |  44 +++++----
 tests/test_font_kit_studio_v011.py         | 137 +++++++++++++++++++++++++++++
 3 files changed, 198 insertions(+), 18 deletions(-)
```

## Diff

```diff
diff --git a/docs/implementation/tasks/task-1-report.md b/docs/implementation/tasks/task-1-report.md
new file mode 100644
index 0000000..7277395
--- /dev/null
+++ b/docs/implementation/tasks/task-1-report.md
@@ -0,0 +1,35 @@
+# Task 1 implementation report
+
+## Scope and evidence
+
+Writer owns only HTML, reusable tests, and this report. Read the task brief, AGENTS.md, README, supplied design, implementation plan, progress/deviations, and both baseline audits before editing. Verified branch `feat/v0.1.1-responsive-rows`, HEAD `ba881ea688f2ea5beb7f7131aad14b82ef2f4b8a`, and initially clean status. Controller's subsequent ledger edits are preserved and excluded from this commit.
+
+Graph Verify attempts supplied by controller: list_projects, search_graph, check_index_coverage returned Transport closed. Project/generation/coverage unknown; no graph claims. Exact direct HTML reads and isolated Chromium/Firefox browser behavior supply evidence.
+
+## Changes
+
+- Correct document title and section version comments to 0.1.1.
+- Add small shared finite-number normalization for factory, hydration and row inspector. Round child counts before any array mutation. Bounds match incumbent controls: children 2–4; gap 0–96; breakpoint 240–1600; ratios .25–12. Defaults remain gap 24, center alignment, collapse 680; nonfinite ratios default to 1. Finite negative/oversized values clamp to control bounds. Fractional counts round with Math.round.
+- Apply raw row overrides before authoritative model fields, preventing invalid raw fields from overriding normalization.
+- Remove unsupported children properties when hydrating leaves and constructing row children; nested row requests retain the existing conversion to text, without retaining hidden descendants. Preserve normal leaf fields, including variables, typography, rule/spacer values and image metadata.
+- Keep existing UI, preset, one-level ID selection and ordinary child inspector. No production testing globals or runtime dependencies.
+
+## Commands and results
+
+Working directory for all commands: repository root.
+
+1. `Get-Content -Raw docs/implementation/tasks/task-1-brief.md; Get-Content -Raw AGENTS.md` and targeted reads of listed references; `git status --short; git branch --show-current; git rev-parse HEAD` — clean intended baseline.
+2. `python -m unittest discover -s tests -v` — first test harness attempt had an incorrectly case-sensitive status wait: 5 tests, 5 failures and 2 timeout errors. Fixed only test wait to recognize both Import failed and imported.
+3. Same command against unchanged app — **RED: 5 tests, 7 failures**, 29.667s. Chromium/Firefox both report fractional import Invalid array length; nonfinite child count exports 4 rather than fallback 2; nested converted text retains children/SECRET; title remains v0.1.0. Preset factory and child selection characterization passed initially.
+4. Same command after implementation — **GREEN: 5 tests OK**, 18.582s, both Chromium and Firefox; pageerror lists empty.
+5. Added independent inspector fractional regression. `New-Item -ItemType Directory -Force work | Out-Null; git show ba881ea688f2ea5beb7f7131aad14b82ef2f4b8a:font_kit_studio_v0.1.1.html | Set-Content -Encoding utf8 work/baseline.html; python -c "import sys,unittest; from pathlib import Path; sys.path.insert(0,'tests'); import test_font_kit_studio_v011 as t; t.HTML=Path('work/baseline.html').resolve(); unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([t.BrowserCase('test_fractional_inspector_count_without_import')]))"` — **RED: 1 test, 2 browser subtest failures**, 5.204s, childCount remains 2 after 2.5; baseline copy is scratch, shipped app unchanged. This custom runner returned process 0 despite failed unittest result, so verdict is based on explicit FAILED output.
+6. Final `python -m unittest discover -s tests -v` — **GREEN: 6 tests OK**, 25.762s; browser tests each run Chromium/Firefox in separate fresh browser contexts, empty pageerror lists.
+7. `python -c "import re; from pathlib import Path; s=Path('font_kit_studio_v0.1.1.html').read_text(encoding='utf-8'); Path('work/inline.js').write_text('\n'.join(re.findall(r'<script[^>]*>(.*?)</script>',s,re.S)),encoding='utf-8')"`; `node --check work/inline.js`; `git diff --check` — inline syntax and whitespace checks pass; combined final command exit 0. Only Git LF-to-CRLF informational warning.
+
+## Self-review and limitations
+
+Reviewed full HTML diff. Shared helper protects array lengths and finite model values before export/render; row fields cannot be overwritten by raw spread. Descendant stripping occurs at hydration/factory boundary while ordinary leaf fields survive. Tests exercise public file import, export dialog, preset and inspector controls; errors captured per page. Existing implemented features were characterized, never removed to force failure.
+
+This task does not close alignment/rendering, actual-width responsive acceptance, malformed text-role/CSS collision, atomic failed-import state, detailed uploaded asset handling or whole-branch review: those remain for subsequent assigned tasks. External Adobe font loading is not tested. Upper bounds are taken from existing inspector controls, as confirmed by controller. Scratch files and controller ledgers are not part of the commit.
+
+Files: `font_kit_studio_v0.1.1.html`, `tests/test_font_kit_studio_v011.py`, this report. Commit message: `Fix row model normalization and leaf-only hydration` (commit identifier supplied in final handoff; this report is included in that commit).
diff --git a/font_kit_studio_v0.1.1.html b/font_kit_studio_v0.1.1.html
index 1362ad0..25c197d 100644
--- a/font_kit_studio_v0.1.1.html
+++ b/font_kit_studio_v0.1.1.html
@@ -1,16 +1,16 @@
 <!doctype html>
 <html lang="en">
 <head>
 <meta charset="utf-8" />
 <meta name="viewport" content="width=device-width, initial-scale=1" />
-<title>Font Kit Studio v0.1.0</title>
+<title>Font Kit Studio v0.1.1</title>
 
 <!--
   TYPEKIT / ADOBE FONTS
   ---------------------
   Option A: paste your kit ID into the field at the top of the page.
   Option B: replace YOUR_KIT_ID below and uncomment the line.
 
   <link rel="stylesheet" href="https://use.typekit.net/YOUR_KIT_ID.css">
 -->
 
@@ -307,21 +307,21 @@ footer {
   header { padding-top: 25px; }
   .controls-inner { grid-template-columns: 1fr; }
   .card-head { grid-template-columns: 1fr; }
   .styles { justify-content: flex-start; max-width: none; }
   .card-foot { grid-template-columns: 1fr; }
   .css { max-width: 100%; text-align: left; }
 }
 
 
 /* ================================================================
-   Font Kit Studio v0.1.0 — Composer
+   Font Kit Studio v0.1.1 — Composer
    ================================================================ */
 .mode-nav {
   position: sticky;
   top: 0;
   z-index: 31;
   background: color-mix(in srgb, var(--bg) 95%, transparent);
   backdrop-filter: blur(16px);
   border-bottom: 1px solid var(--line);
 }
 .mode-nav-inner {
@@ -1207,21 +1207,21 @@ function loadAdobeKit() {
 
 loadKit.addEventListener("click", loadAdobeKit);
 kitId.addEventListener("keydown", e => {
   if (e.key === "Enter") loadAdobeKit();
 });
 
 const remembered = localStorage.getItem("typekit-specimen-kit");
 if (remembered) kitId.value = remembered;
 
 /* ================================================================
-   Font Kit Studio v0.1.0 — Flow Composer
+   Font Kit Studio v0.1.1 — Flow Composer
    ================================================================ */
 (function initComposer() {
   const TAILWIND_COLORS = {
   "black": "#000",
   "white": "#fff",
   "slate": {
     "50": "oklch(98.4% 0.003 247.858)",
     "100": "oklch(96.8% 0.007 247.896)",
     "200": "oklch(92.9% 0.013 255.508)",
     "300": "oklch(86.9% 0.022 252.894)",
@@ -1598,44 +1598,51 @@ if (remembered) kitId.value = remembered;
     savedColor: "Asteria Gold",
     imageName: "",
     assetDataUrl: "",
     imageWidth: 180,
     opacity: 1,
     ruleWidth: 42,
     ruleThickness: 1,
     spacerHeight: 38
   });
 
+  function rowNumber(value, fallback, min, max, integer=false) {
+    const number = value == null || value === "" ? fallback : Number(value);
+    const finite = Number.isFinite(number) ? number : fallback;
+    return Math.max(min, Math.min(max, integer ? Math.round(finite) : finite));
+  }
+
   const makeRowSlot = (overrides={}) => {
-    const children = overrides.children ? overrides.children.slice(0, 4) : [
+    const children = Array.isArray(overrides.children) ? overrides.children.slice(0, 4).map(child => {
+      if (!LEAF_SLOT_TYPES.includes(child?.type)) return hydrateSlot(child, 1);
+      const { children:discardedChildren, ...leaf } = child;
+      return leaf;
+    }) : [
       makeGenericSlot("image"),
       makeTextSlot("Body", "gotham")
     ];
     while (children.length < 2) children.push(makeTextSlot("Custom", "gotham"));
-    const count = Math.max(2, Math.min(4, Number(overrides.childCount) || children.length || 2));
+    const count = rowNumber(overrides.childCount, children.length || 2, 2, 4, true);
     while (children.length < count) children.push(makeTextSlot("Custom", "gotham"));
     children.length = count;
     const ratios = Array.isArray(overrides.ratios) ? overrides.ratios.slice(0, count) : [];
     while (ratios.length < count) ratios.push(ratios.length === 1 ? 2 : 1);
     return {
+      ...overrides,
       id: crypto.randomUUID ? crypto.randomUUID() : `slot-${Date.now()}-${Math.random()}`,
       type: "row",
       role: "Row",
       childCount: count,
-      gap: Math.max(0, Number(overrides.gap ?? 24)),
+      gap: rowNumber(overrides.gap, 24, 0, 96),
       alignItems: ROW_ALIGNMENTS.includes(overrides.alignItems) ? overrides.alignItems : "center",
-      collapseAt: Math.max(240, Number(overrides.collapseAt ?? 680)),
-      ratios: ratios.map(v => Math.max(.25, Number(v) || 1)),
-      children,
-      ...overrides,
-      childCount: count,
-      ratios: ratios.map(v => Math.max(.25, Number(v) || 1)),
+      collapseAt: rowNumber(overrides.collapseAt, 680, 240, 1600),
+      ratios: ratios.map(v => rowNumber(v, 1, .25, 12)),
       children
     };
   };
 
   const COMPOSITION_PRESETS = {
     asteria: {
       name: "Asteria — Sculptural",
       background: { source:"custom", hex:"#030409", family:"slate", shade:"950", saved:"Asteria Void" },
       width: "960",
       slots: [
@@ -1764,31 +1771,32 @@ if (remembered) kitId.value = remembered;
   function clone(value) { return JSON.parse(JSON.stringify(value)); }
 
   function freshId() { return crypto.randomUUID ? crypto.randomUUID() : `slot-${Date.now()}-${Math.random()}`; }
 
   function hydrateSlot(raw, depth=0) {
     const requested = String(raw?.type || "text");
     if (requested === "row" && depth === 0) {
       const rawChildren = Array.isArray(raw.children) ? raw.children.slice(0, 4) : [];
       const children = rawChildren.map(child => hydrateSlot(child, 1)).filter(child => child.type !== "row");
       while (children.length < 2) children.push(makeTextSlot("Custom", "gotham"));
-      const count = Math.max(2, Math.min(4, Number(raw.childCount) || children.length));
+      const count = rowNumber(raw.childCount, children.length, 2, 4, true);
       while (children.length < count) children.push(makeTextSlot("Custom", "gotham"));
       children.length = count;
       const row = makeRowSlot({ ...raw, children, childCount:count });
       row.id = freshId();
       row.children = row.children.map(child => ({ ...child, id:freshId(), assetDataUrl:child.type === "image" ? "" : child.assetDataUrl }));
       return row;
     }
     const type = LEAF_SLOT_TYPES.includes(requested) ? requested : "text";
     const base = type === "text" ? makeTextSlot(raw?.role || "Custom", raw?.family || "gotham") : makeGenericSlot(type);
-    return { ...base, ...(raw || {}), type, id:freshId(), assetDataUrl:type === "image" ? "" : (raw?.assetDataUrl || "") };
+    const { children:discardedChildren, ...leaf } = raw || {};
+    return { ...base, ...leaf, type, id:freshId(), assetDataUrl:type === "image" ? "" : (raw?.assetDataUrl || "") };
   }
 
   function applyCompositionPreset(key) {
     const preset = COMPOSITION_PRESETS[key] || COMPOSITION_PRESETS.asteria;
     state.canvasWidth = preset.width;
     state.background = clone(preset.background);
     state.slots = preset.slots.map(slot => hydrateSlot(slot, 0));
     state.selectedId = state.slots[0]?.id || null;
     syncCompositionControls();
     renderComposer();
@@ -2223,53 +2231,53 @@ if (remembered) kitId.value = remembered;
       }
       replaceSelectedSlot(replacement);
       renderComposer();
     });
 
     if (slot.type === "row") {
       const childCount = slotInspector.querySelector('[data-bind="rowChildCount"]');
       childCount?.addEventListener("change", () => {
         const row = selectedSlot();
         if (!row || row.type !== "row") return;
-        const next = Math.max(2, Math.min(4, Number(childCount.value) || 2));
+        const next = rowNumber(childCount.value, 2, 2, 4, true);
         while (row.children.length < next) row.children.push(makeTextSlot("Custom", "gotham"));
         row.children.length = next;
         while (row.ratios.length < next) row.ratios.push(1);
         row.ratios.length = next;
         row.childCount = next;
         renderComposer();
       });
       const rowGap = slotInspector.querySelector('[data-bind="rowGap"]');
       rowGap?.addEventListener("input", () => {
         const row = selectedSlot();
-        row.gap = Math.max(0, Number(rowGap.value) || 0);
+        row.gap = rowNumber(rowGap.value, 24, 0, 96);
         updateInspectorOutput(rowGap, "rowGap", row.gap);
         syncRowLayouts();
       });
       const rowAlign = slotInspector.querySelector('[data-bind="rowAlignItems"]');
       rowAlign?.addEventListener("change", () => {
         const row = selectedSlot();
         row.alignItems = ROW_ALIGNMENTS.includes(rowAlign.value) ? rowAlign.value : "center";
         syncRowLayouts();
       });
       const collapse = slotInspector.querySelector('[data-bind="rowCollapseAt"]');
       collapse?.addEventListener("input", () => {
         const row = selectedSlot();
-        row.collapseAt = Math.max(240, Number(collapse.value) || 680);
+        row.collapseAt = rowNumber(collapse.value, 680, 240, 1600);
         updateInspectorOutput(collapse, "rowCollapseAt", row.collapseAt);
         syncRowLayouts();
       });
       slotInspector.querySelectorAll('[data-row-ratio]').forEach(input => {
         input.addEventListener("input", () => {
           const row = selectedSlot();
           const ratioIndex = Number(input.dataset.rowRatio);
-          row.ratios[ratioIndex] = Math.max(.25, Number(input.value) || 1);
+          row.ratios[ratioIndex] = rowNumber(input.value, 1, .25, 12);
           syncRowLayouts();
         });
       });
       slotInspector.querySelectorAll('[data-select-child]').forEach(button => {
         button.addEventListener("click", () => {
           state.selectedId = button.dataset.selectChild;
           renderComposer();
         });
       });
       return;
diff --git a/tests/test_font_kit_studio_v011.py b/tests/test_font_kit_studio_v011.py
new file mode 100644
index 0000000..e09de62
--- /dev/null
+++ b/tests/test_font_kit_studio_v011.py
@@ -0,0 +1,137 @@
+import json
+import unittest
+from pathlib import Path
+
+from playwright.sync_api import sync_playwright
+
+HTML = Path(__file__).resolve().parents[1] / 'font_kit_studio_v0.1.1.html'
+
+
+class BrowserCase(unittest.TestCase):
+    def setUp(self):
+        self.runtime = sync_playwright().start()
+        self.browsers = []
+
+    def tearDown(self):
+        for browser in self.browsers:
+            browser.close()
+        self.runtime.stop()
+
+    def page(self, engine):
+        browser = getattr(self.runtime, engine).launch()
+        self.browsers.append(browser)
+        page = browser.new_page(viewport={'width': 1600, 'height': 1200})
+        errors = []
+        page.on('pageerror', lambda error: errors.append(str(error)))
+        page.goto(HTML.as_uri())
+        page.locator('#modeComposer').click()
+        return page, errors
+
+    def import_slots(self, page, slots):
+        page.locator('#composerStatus').evaluate('(status) => status.textContent = ""')
+        page.locator('#importJsonFile').set_input_files({
+            'name': 'composition.json', 'mimeType': 'application/json',
+            'buffer': json.dumps({'version': '0.1.1', 'composition': {'slots': slots}}).encode(),
+        })
+        page.wait_for_function("/import/i.test(document.querySelector('#composerStatus').textContent)")
+        self.assertIn('Composition imported.', page.locator('#composerStatus').inner_text())
+
+    def export(self, page):
+        page.locator('#exportJson').click()
+        result = json.loads(page.locator('#exportDialogText').input_value())
+        page.locator('#exportDialog').evaluate('(dialog) => dialog.close()')
+        return result
+
+    def test_valid_row_factory_and_child_selection(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                page.locator('#compositionPreset').select_option('rowdemo')
+                page.locator('#applyPreset').click()
+                row = next(s for s in self.export(page)['composition']['slots'] if s['type'] == 'row')
+                self.assertEqual(row['childCount'], 2)
+                self.assertEqual(row['ratios'], [1, 2])
+                self.assertEqual([s['type'] for s in row['children']], ['image', 'text'])
+                page.locator('.row-child').nth(1).click()
+                self.assertIn('CHILD 2/2', page.locator('#slotInspector').inner_text())
+                self.assertEqual(page.locator('#slotInspector select[data-bind="type"] option[value="row"]').count(), 0)
+                self.assertEqual(errors, [])
+
+    def test_fractional_inspector_count_without_import(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                self.import_slots(page, [{'type': 'row', 'childCount': 2}])
+                control = page.locator('[data-bind="rowChildCount"]')
+                control.fill('2.5')
+                control.dispatch_event('change')
+                row = self.export(page)['composition']['slots'][0]
+                self.assertEqual(row['childCount'], 3)
+                self.assertEqual(len(row['children']), 3)
+                self.assertEqual(len(row['ratios']), 3)
+                self.assertEqual(errors, [])
+
+    def test_fractional_child_counts(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                self.import_slots(page, [{'type': 'row', 'childCount': 2.5}])
+                row = self.export(page)['composition']['slots'][0]
+                self.assertEqual(row['childCount'], 3)
+                self.assertEqual(len(row['children']), 3)
+                control = page.locator('[data-bind="rowChildCount"]')
+                control.fill('3.5')
+                control.dispatch_event('change')
+                row = self.export(page)['composition']['slots'][0]
+                self.assertEqual(row['childCount'], 4)
+                self.assertEqual(len(row['children']), len(row['ratios']))
+                self.assertEqual(errors, [])
+
+    def test_malformed_row_values_are_normalized(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                self.import_slots(page, [{'type': 'row', 'childCount': 'Infinity', 'gap': -99,
+                    'alignItems': 'invalid', 'collapseAt': 'bad', 'ratios': ['Infinity', -2]}])
+                row = self.export(page)['composition']['slots'][0]
+                self.assertEqual(row['childCount'], 2)
+                self.assertEqual(row['gap'], 0)
+                self.assertEqual(row['alignItems'], 'center')
+                self.assertEqual(row['collapseAt'], 680)
+                self.assertEqual(row['ratios'], [1, .25])
+                self.assertEqual(errors, [])
+
+    def test_nested_rows_drop_hidden_descendants_and_preserve_leaf_fields(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                leaves = [
+                    {'type': 'row', 'text': 'converted', 'children': [{'type': 'image', 'assetDataUrl': 'SECRET'}]},
+                    {'type': 'text', 'text': 'retained', 'size': 31, 'variables': {'wght': 600}},
+                    {'type': 'rule', 'ruleWidth': 65, 'ruleThickness': 3},
+                    {'type': 'spacer', 'spacerHeight': 77},
+                ]
+                self.import_slots(page, [{'type': 'row', 'childCount': 4, 'children': leaves}])
+                data = self.export(page)
+                children = data['composition']['slots'][0]['children']
+                self.assertEqual([s['type'] for s in children], ['text', 'text', 'rule', 'spacer'])
+                self.assertNotIn('children', children[0])
+                self.assertNotIn('SECRET', json.dumps(data))
+                self.assertEqual(children[1]['variables'], {'wght': 600})
+                self.assertEqual(children[1]['size'], 31)
+                self.assertEqual(children[2]['ruleWidth'], 65)
+                self.assertEqual(children[3]['spacerHeight'], 77)
+                self.assertEqual(len({s['id'] for s in children}), 4)
+                self.assertEqual(errors, [])
+
+
+class StructureTests(unittest.TestCase):
+    def test_version_and_existing_model(self):
+        source = HTML.read_text(encoding='utf-8')
+        self.assertTrue('<title>Font Kit Studio v0.1.1</title>' in source, 'Document title must match version 0.1.1')
+        for symbol in ('makeRowSlot', 'findSlotById', 'selectedLocation', 'LEAF_SLOT_TYPES'):
+            self.assertIn(symbol, source)
+
+
+if __name__ == '__main__':
+    unittest.main()
```
