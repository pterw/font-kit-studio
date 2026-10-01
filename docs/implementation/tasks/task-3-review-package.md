# Review package

Base: d0496ad610381f627b4dfe55d836abe722088c15
Head: a03d8aea9c25362a606fe72d819024243d87a586

## Commits

```text
a03d8ae Normalize row inspector displays and verify child editing
```

## Stat

```text
docs/implementation/tasks/task-3-report.md | 31 ++++++++++++
 font_kit_studio_v0.1.1.html                | 17 +++++--
 tests/test_font_kit_studio_v011.py         | 75 ++++++++++++++++++++++++++++++
 3 files changed, 118 insertions(+), 5 deletions(-)
```

## Diff

```diff
diff --git a/docs/implementation/tasks/task-3-report.md b/docs/implementation/tasks/task-3-report.md
new file mode 100644
index 0000000..71b5d7b
--- /dev/null
+++ b/docs/implementation/tasks/task-3-report.md
@@ -0,0 +1,31 @@
+# Task 3 implementation report
+
+## Scope and reconciliation
+
+Read task-3-brief.md first, then AGENTS.md, README, plan, progress/deviations, original design and exact inspector/model/render source. Starting branch feat/v0.1.1-responsive-rows, HEAD d0496ad610381f627b4dfe55d836abe722088c15. Controller progress edits were already present and preserved. One writer owns HTML/tests/this report; no subagents, ledger edits or publication.
+
+Parent Graph Verify discovery/coverage failed Transport closed; project/generation/coverage unknown. Direct source and fresh Chromium/Firefox behavior are the evidence, with no graph verification claim.
+
+Inherited inspector already supports child count, gap, alignment, breakpoint, numeric weights, summary selection, breadcrumb, leaf-only type choices and leaf inspectors. Characterized passing behavior honestly rather than manufacturing RED. Confirmed defect: model normalizes breakpoint 99999 to 1600 but inspector continues displaying 99999. Numeric weights have the same missing reflection in source. Fix reflects normalized breakpoint and weights on change, retaining live bounded layout/model updates on input. Committing reflection on change preserves multi-digit/decimal keyboard editing; tests type 680 and 2.5 character-by-character then Tab. Gap range reflects its bounded value immediately. Associated labels/IDs added for all row controls and each weight without visual redesign. Shared rowNumber normalization retained.
+
+## Tests and outcomes
+
+Commands run in C:/Users/peter/Documents/Codex/2026-09-30/ref/outputs/font-kit-studio.
+
+- Preflight: `git status --short`, `git branch --show-current`, `git rev-parse HEAD`: intended branch/HEAD, only controller progress file dirty.
+- RED on unchanged HTML: `python -m unittest discover -s tests -k row_inspector_normalized -v`: Ran 1 test in 9.624s, FAILED (failures=2), exit 1. Both engines: AssertionError '99999' != '1600'. Model upper bounds pass before display assertion.
+- Initial harness import failed because Windows default text encoding wrote cp1252; corrected UTF-8. First leaf characterization run failed because Playwright first is a property, not a method; corrected harness and actual top-level selector. These were test errors, not production RED.
+- Initial GREEN: `python -m unittest discover -s tests -k row_ -v`: Ran 4 tests in 27.858s, OK, exit 0. Then changed numeric reflection to commit events and added keyboard acceptance.
+- Full suite: `python -m unittest discover -s tests -v`: Ran 10 tests in 60.662s, OK, exit 0. Nine browser tests run both Chromium and Firefox; structural test passes. Final identical suite after test-only newline cleanup: Ran 10 tests in 58.378s, OK, exit 0. Newline cleanup did not alter test semantics.
+- Syntax: `python -c "import re; from pathlib import Path; s=Path('font_kit_studio_v0.1.1.html').read_text(encoding='utf-8'); Path('work/inline.js').write_text('\n'.join(re.findall(r'<script[^>]*>(.*?)</script>',s,re.S)),encoding='utf-8')"`, then `node --check work/inline.js`: exit 0, no errors.
+- `git diff --check`: exit 0 after newline cleanup.
+
+New UI tests cover child-count low/high/fractional/empty values, breakpoint high/low/empty, weight high/low/empty, normalized committed displays, accessible labels, keyboard editing, all four alignments (export and computed style), gap interaction (export and actual geometry), summary jumps, child breadcrumb, row exclusion, no child movers, text/image-width/rule/spacer editing and top-level move with retained child text. Deferred Task1 M1 covered oversized finite imported gap/breakpoint/weights, asserting 96/1600/[12,.25]. Each test asserts no page errors in both engines.
+
+## Self-review and limits
+
+Reviewed production diff: local inspector markup and normalization reflection only; no globals, runtime dependencies, model/import/export redesign or leaf control removals. Dynamically rendered inspector is unique; weight IDs are unique within its selected row. Events reference current selection and existing render lifecycle. Live input can temporarily show uncommitted out-of-range text while layout/model remain bounded; change/blur commits normalized display, preserving typing.
+
+Tests characterize representative existing leaf edits, not every typography/axis/image-asset control or Library action. Asset acceptance/export/import atomicity and complete final browser acceptance belong to later tasks. No screenshot/design redesign or external Adobe access is claimed. The spec supplies no new breadcrumb-navigation action, so existing textual row/child breadcrumb is retained. Independent task review remains controller-owned.
+
+Assigned files: font_kit_studio_v0.1.1.html, tests/test_font_kit_studio_v011.py, docs/implementation/tasks/task-3-report.md. Commit ID is returned in handoff; report is included in commit.
diff --git a/font_kit_studio_v0.1.1.html b/font_kit_studio_v0.1.1.html
index 641b360..7c46939 100644
--- a/font_kit_studio_v0.1.1.html
+++ b/font_kit_studio_v0.1.1.html
@@ -2159,25 +2159,25 @@ if (remembered) kitId.value = remembered;
     const indexLabel = isChild
       ? `ROW ${loc.index + 1} · CHILD ${loc.childIndex + 1}/${loc.parent.children.length}`
       : `SLOT ${loc.index + 1}/${state.slots.length}`;
     let body = `
       <div class="inspector-title-row"><h2>${escapeAttr(slot.type === "text" ? slot.role : slot.type[0].toUpperCase()+slot.type.slice(1))}</h2><span class="inspector-index">${indexLabel}</span></div>
       <div class="inspector-grid">
         <div class="inspector-field full"><label>Slot type</label><select data-bind="type">${optionsHtml(typeChoices, slot.type, v => v[0].toUpperCase()+v.slice(1))}</select></div>`;
 
     if (slot.type === "row") {
       body += `
-        <div class="inspector-field"><label>Children</label><input data-bind="rowChildCount" type="number" min="2" max="4" step="1" value="${slot.children.length}"></div>
-        <div class="inspector-field"><div class="value-line"><label>Gap</label><output>${slot.gap}px</output></div><input data-bind="rowGap" type="range" min="0" max="96" step="1" value="${slot.gap}"></div>
-        <div class="inspector-field"><label>Align items</label><select data-bind="rowAlignItems">${optionsHtml(ROW_ALIGNMENTS, slot.alignItems)}</select></div>
-        <div class="inspector-field"><div class="value-line"><label>Collapse at</label><output>${slot.collapseAt}px</output></div><input data-bind="rowCollapseAt" type="number" min="240" max="1600" step="10" value="${slot.collapseAt}"></div>
-        <div class="inspector-field full"><span class="inspector-label">Column weights</span><div class="inspector-grid">${slot.children.map((child, childIndex) => `<div class="inspector-field"><label>Child ${childIndex + 1}</label><input data-row-ratio="${childIndex}" type="number" min="0.25" max="12" step="0.25" value="${slot.ratios[childIndex] ?? 1}"></div>`).join("")}</div></div>
+        <div class="inspector-field"><label for="rowChildCount">Children</label><input id="rowChildCount" data-bind="rowChildCount" type="number" min="2" max="4" step="1" value="${slot.children.length}"></div>
+        <div class="inspector-field"><div class="value-line"><label for="rowGap">Gap</label><output>${slot.gap}px</output></div><input id="rowGap" data-bind="rowGap" type="range" min="0" max="96" step="1" value="${slot.gap}"></div>
+        <div class="inspector-field"><label for="rowAlignItems">Align items</label><select id="rowAlignItems" data-bind="rowAlignItems">${optionsHtml(ROW_ALIGNMENTS, slot.alignItems)}</select></div>
+        <div class="inspector-field"><div class="value-line"><label for="rowCollapseAt">Collapse at</label><output>${slot.collapseAt}px</output></div><input id="rowCollapseAt" data-bind="rowCollapseAt" type="number" min="240" max="1600" step="10" value="${slot.collapseAt}"></div>
+        <div class="inspector-field full"><span class="inspector-label">Column weights</span><div class="inspector-grid">${slot.children.map((child, childIndex) => `<div class="inspector-field"><label for="rowRatio${childIndex}">Child ${childIndex + 1}</label><input id="rowRatio${childIndex}" data-row-ratio="${childIndex}" type="number" min="0.25" max="12" step="0.25" value="${slot.ratios[childIndex] ?? 1}"></div>`).join("")}</div></div>
         <div class="inspector-field full"><span class="inspector-label">Children</span><div class="row-child-list">${slot.children.map((child, childIndex) => `<button type="button" class="row-child-jump" data-select-child="${escapeAttr(child.id)}"><span>${childIndex + 1}. ${escapeAttr(child.type === "text" ? child.role : child.type[0].toUpperCase()+child.type.slice(1))}</span><small>${escapeAttr(child.type)}</small></button>`).join("")}</div><p class="inspector-note">Children are ordinary leaf slots. Select one to edit it. Rows cannot contain rows in v0.1.1.</p></div>`;
     } else if (slot.type === "text") {
       const font = byFamily(slot.family);
       const styleLabels = font.styles.map((s, i) => `${i}|${s.label}`);
       body += `
         <div class="inspector-field"><label>Role</label><select data-bind="role">${optionsHtml(ROLES, slot.role)}</select></div>
         <div class="inspector-field"><label>Element</label><select data-bind="element">${optionsHtml(ELEMENTS, slot.element)}</select></div>
         <div class="inspector-field full"><label>Family</label><select data-bind="family">${fonts.map(f => `<option value="${escapeAttr(f.family)}"${f.family === slot.family ? " selected" : ""}>${escapeAttr(f.name)}</option>`).join("")}</select></div>
         <div class="inspector-field full"><label>Style / cut</label><select data-bind="styleIndex">${styleLabels.map(v => { const [i,label] = v.split("|"); return `<option value="${i}"${Number(i) === Number(slot.styleIndex) ? " selected" : ""}>${escapeAttr(label)}</option>`; }).join("")}</select></div>
         <div class="inspector-field full"><div class="value-line"><label>Size</label><output>${formatSize(slot.size)}</output></div><input type="range" data-bind="size" min="8" max="86" step="1" value="${slot.size}"></div>
@@ -2242,43 +2242,50 @@ if (remembered) kitId.value = remembered;
         row.children.length = next;
         while (row.ratios.length < next) row.ratios.push(1);
         row.ratios.length = next;
         row.childCount = next;
         renderComposer();
       });
       const rowGap = slotInspector.querySelector('[data-bind="rowGap"]');
       rowGap?.addEventListener("input", () => {
         const row = selectedSlot();
         row.gap = rowNumber(rowGap.value, 24, 0, 96);
+        rowGap.value = row.gap;
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
         row.collapseAt = rowNumber(collapse.value, 680, 240, 1600);
         updateInspectorOutput(collapse, "rowCollapseAt", row.collapseAt);
         syncRowLayouts();
       });
+      collapse?.addEventListener("change", () => {
+        collapse.value = selectedSlot().collapseAt;
+      });
       slotInspector.querySelectorAll('[data-row-ratio]').forEach(input => {
         input.addEventListener("input", () => {
           const row = selectedSlot();
           const ratioIndex = Number(input.dataset.rowRatio);
           row.ratios[ratioIndex] = rowNumber(input.value, 1, .25, 12);
           syncRowLayouts();
         });
+        input.addEventListener("change", () => {
+          input.value = selectedSlot().ratios[Number(input.dataset.rowRatio)];
+        });
       });
       slotInspector.querySelectorAll('[data-select-child]').forEach(button => {
         button.addEventListener("click", () => {
           state.selectedId = button.dataset.selectChild;
           renderComposer();
         });
       });
       return;
     }
 
diff --git a/tests/test_font_kit_studio_v011.py b/tests/test_font_kit_studio_v011.py
index 5db8277..bfbae05 100644
--- a/tests/test_font_kit_studio_v011.py
+++ b/tests/test_font_kit_studio_v011.py
@@ -49,20 +49,95 @@ class BrowserCase(unittest.TestCase):
             const rect = element => {
                 const r = element.getBoundingClientRect();
                 return {x:r.x, y:r.y, width:r.width, height:r.height, bottom:r.bottom};
             };
             return {layout:rect(layout), collapsed:layout.classList.contains('is-collapsed'),
                 children:[...layout.children].map(rect),
                 order:[...layout.children].map(child => child.dataset.rowChild),
                 gap:parseFloat(getComputedStyle(layout).gap)};
         }''')
 
+    def test_row_inspector_normalized_values_and_labels(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                self.import_slots(page, [{'type':'row', 'gap':99999, 'collapseAt':99999,
+                    'ratios':[99999, -99999]}])
+                row = self.export(page)['composition']['slots'][0]
+                self.assertEqual((row['gap'], row['collapseAt'], row['ratios']), (96, 1600, [12, .25]))
+                for selector, event, cases, key in (
+                    ('[data-bind="rowChildCount"]', 'change', [('1',2), ('5',4), ('2.5',3), ('',2)], 'childCount'),
+                    ('[data-bind="rowCollapseAt"]', 'input', [('99999',1600), ('1',240), ('',680)], 'collapseAt'),
+                    ('[data-row-ratio="0"]', 'input', [('99999',12), ('0',.25), ('',1)], 'ratios'),
+                ):
+                    for value, expected in cases:
+                        control = page.locator(selector)
+                        control.fill(value)
+                        control.dispatch_event(event)
+                        control.dispatch_event("change")
+                        row = self.export(page)['composition']['slots'][0]
+                        actual = row[key][0] if key == 'ratios' else row[key]
+                        self.assertEqual(actual, expected)
+                        self.assertEqual(page.locator(selector).input_value(), str(expected))
+                breakpoint = page.locator('[data-bind="rowCollapseAt"]')
+                breakpoint.fill('')
+                breakpoint.press_sequentially('680')
+                self.assertEqual(breakpoint.input_value(), '680')
+                breakpoint.press('Tab')
+                self.assertEqual(breakpoint.input_value(), '680')
+                weight = page.locator('[data-row-ratio="0"]')
+                weight.fill('')
+                weight.press_sequentially('2.5')
+                weight.press('Tab')
+                self.assertEqual(weight.input_value(), '2.5')
+                for selector in ('[data-bind="rowChildCount"]', '[data-bind="rowGap"]',
+                                 '[data-bind="rowAlignItems"]', '[data-bind="rowCollapseAt"]', '[data-row-ratio="0"]'):
+                    self.assertTrue(page.locator(selector).evaluate('el => el.labels.length > 0'))
+                self.assertEqual(errors, [])
+
+    def test_row_controls_and_leaf_inspectors(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                self.import_slots(page, [{'type':'row', 'childCount':4, 'children':[
+                    {'type':'text', 'text':'before'}, {'type':'image'}, {'type':'rule'}, {'type':'spacer'}]},
+                    {'type':'text', 'text':'outside'}])
+                for alignment in ('start','center','end','stretch'):
+                    page.locator('[data-bind="rowAlignItems"]').select_option(alignment)
+                    self.assertEqual(self.export(page)['composition']['slots'][0]['alignItems'], alignment)
+                    self.assertEqual(page.locator('.row-layout').evaluate('el => getComputedStyle(el).alignItems'), alignment)
+                gap = page.locator('[data-bind="rowGap"]')
+                gap.fill('37')
+                gap.dispatch_event('input')
+                self.assertEqual(self.export(page)['composition']['slots'][0]['gap'], 37)
+                self.assertAlmostEqual(self.row_geometry(page)['gap'],37,delta=.1)
+                for index, selector, value, key, expected in (
+                    (0,'[data-bind="text"]','edited','text','edited'),
+                    (1,'[data-bind="imageWidth"]','123','imageWidth',123),
+                    (2,'[data-bind="ruleThickness"]','7','ruleThickness',7),
+                    (3,'[data-bind="spacerHeight"]','88','spacerHeight',88),
+                ):
+                    page.locator('.row-child-jump').nth(index).click()
+                    self.assertIn(f'ROW 1 · CHILD {index+1}/4',page.locator('.inspector-index').inner_text())
+                    self.assertEqual(page.locator('[data-bind="type"] option[value="row"]').count(),0)
+                    self.assertEqual(page.locator('.row-child .slot-movers').count(),0)
+                    control=page.locator(selector)
+                    control.fill(value)
+                    control.dispatch_event('input')
+                    self.assertEqual(self.export(page)['composition']['slots'][0]['children'][index][key], expected)
+                    page.locator('#composerCanvas > .flow-slot').first.click(position={'x':3,'y':3})
+                page.locator('#composerCanvas > .flow-slot').first.locator('.slot-movers button').nth(1).click()
+                slots=self.export(page)['composition']['slots']
+                self.assertEqual([s['type'] for s in slots], ['text','row'])
+                self.assertEqual(slots[1]['children'][0]['text'],'edited')
+                self.assertEqual(errors, [])
+
     def test_unequal_child_alignment_geometry(self):
         for engine in ('chromium', 'firefox'):
             with self.subTest(engine=engine):
                 page, errors = self.page(engine)
                 for alignment in ('start', 'center', 'end', 'stretch'):
                     with self.subTest(alignment=alignment):
                         self.import_slots(page, [{'type':'row', 'alignItems':alignment,
                             'children':[{'type':'spacer', 'spacerHeight':40},
                                         {'type':'spacer', 'spacerHeight':140}]}])
                         geometry = self.row_geometry(page)
```
