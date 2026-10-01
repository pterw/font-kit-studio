# Review package

Base: ab087c073d0b9c9738fdd4fb23027c2f2fee7789
Head: 0e86c9ff0a8a953224ac59eba129bd99e329bc6d

## Commits

```text
0e86c9f Fix row alignment and verify responsive grid geometry
```

## Stat

```text
docs/implementation/tasks/task-2-report.md | 36 ++++++++++++++
 font_kit_studio_v0.1.1.html                |  1 -
 tests/test_font_kit_studio_v011.py         | 79 ++++++++++++++++++++++++++++++
 3 files changed, 115 insertions(+), 1 deletion(-)
```

## Diff

```diff
diff --git a/docs/implementation/tasks/task-2-report.md b/docs/implementation/tasks/task-2-report.md
new file mode 100644
index 0000000..1f8ef3f
--- /dev/null
+++ b/docs/implementation/tasks/task-2-report.md
@@ -0,0 +1,36 @@
+# Task 2 implementation report
+
+## Scope and evidence
+
+Read task-2-brief.md first, AGENTS.md, README.md, implementation plan/progress/deviations, original design, baseline row audit and Task 1 report. Branch is `feat/v0.1.1-responsive-rows`; starting HEAD is `ab087c073d0b9c9738fdd4fb23027c2f2fee7789`. Initial status was clean. Controller ledger edits subsequently appeared and are preserved/excluded. Writer owns only HTML, tests and this report; no subagents or remote operations.
+
+Graph Verify parent attempts (list_projects/search_graph/check_index_coverage) failed with Transport closed. Project/generation/coverage unknown. This task uses exact direct source plus fresh isolated Chromium/Firefox browser contexts, without claiming graph verification.
+
+## Changes and requirement reconciliation
+
+The inherited renderer already supplies `.row-layout`, weighted CSS grid columns, `.is-collapsed`, `syncRowLayouts()` and one canvas ResizeObserver. Those capabilities are characterized as passing; none were deleted to manufacture RED.
+
+Remove only `.row-child`'s forced `height:100%`. Natural grid item heights now allow start, center and end alignment to move unequal-height children. Grid's existing stretch behavior still makes their wrappers equal height. The incumbent visual design and collapsed single-column layout are preserved; no runtime dependencies or production test globals were added.
+
+Extend BrowserCase with geometry measurements and two behavior tests. Alignment checks real wrapper bounds for 40px/140px spacers in all four modes. Row layout characterization covers 2/3/4 children, weights 1..N, 17px actual horizontal/vertical gaps, 679/680/681px canvas widths and return to expanded mode. Parent-container width changes do not fire a window resize or app render event: the canvas observer must update the class. Nominal selection remains 960px, establishing actual-width collapse. Collapsed children retain source order and equal single-column widths. Existing preset/selection/model checks remain in the full suite.
+
+## Exact commands and relevant output
+
+Working directory: `C:/Users/peter/Documents/Codex/2026-09-30/ref/outputs/font-kit-studio`.
+
+- Preflight: `git status --short; git branch --show-current; git rev-parse HEAD` — clean, intended branch/HEAD above. Direct reads of required documents and exact renderer/CSS source established inherited behavior.
+- **RED**, unchanged HTML: `python -m unittest discover -s tests -p test_font_kit_studio_v011.py -k unequal_child_alignment -v` — `Ran 1 test in 8.311s`, `FAILED (failures=6)`, exit 1. start/center/end fail in both Chromium and Firefox with `AssertionError: 0 != 100 within 1 delta (100 difference)` for wrapper-height difference. Stretch passes. This is genuine rendered behavior failure before fix.
+- Initial characterization harness: `python -m unittest discover -s tests -p test_font_kit_studio_v011.py -k weighted_columns -v` — `Ran 1 test in 64.974s`, `FAILED (errors=2)`, exit 1. Both browser waits timed out because harness set parent border-box width equal to intended canvas width, omitting stage padding/border. Corrected test-only parent-width calculation using computed edges. No production defect inferred from this harness failure.
+- Corrected inherited characterization, unchanged HTML: same weighted-columns command — `Ran 1 test in 11.596s`, `OK`, exit 0. Both browsers pass boundary/observer/tracks/gaps/source-order checks before the production fix.
+- **GREEN**, after one-line CSS fix: `python -m unittest discover -s tests -p test_font_kit_studio_v011.py -k unequal_child_alignment -v` — `Ran 1 test in 6.692s`, `OK`, exit 0. All four alignment modes pass in both browsers; pageerror lists empty.
+- Final full scoped suite: `python -m unittest discover -s tests -v` — `Ran 8 tests in 56.837s`, `OK`, exit 0. Seven behavior tests each run Chromium and Firefox; one structural test passes. Both new tests assert empty browser pageerror lists.
+- Inline syntax extraction: `python -c "import re; from pathlib import Path; s=Path('font_kit_studio_v0.1.1.html').read_text(encoding='utf-8'); Path('work/inline.js').write_text('\n'.join(re.findall(r'<script[^>]*>(.*?)</script>',s,re.S)),encoding='utf-8')"`; then `node --check work/inline.js` — exit 0, no syntax errors. Scratch file is ignored.
+- `git diff --check` — exit 0, no whitespace errors; only Git's informational LF-to-CRLF warnings.
+
+## Self-review and limitations
+
+Reviewed assigned diff: production change is exactly removal of the height declaration. Existing row alignment values still pass through syncRowLayouts, and stretch remains native CSS grid behavior. Test measurements wait beyond existing grid transition duration; container boundary waits also require actual canvas width and matching collapse class. No app event or global testing hook drives observer acceptance. Browser pages are isolated by existing BrowserCase conventions. No broader redesign or unrelated model/export change.
+
+This verifies bounded row rendering behavior, not every leaf-type geometry, external Adobe fonts, screenshot polish, persistence/export or whole-branch acceptance. Task 3 inspector refinements and later final checks remain controller-assigned. Independent review is pending controller dispatch.
+
+Assigned files: `font_kit_studio_v0.1.1.html`, `tests/test_font_kit_studio_v011.py`, `docs/implementation/tasks/task-2-report.md`. Commit message: `Fix row alignment and verify responsive grid geometry`; commit identifier is provided in the final handoff (report included in commit).
diff --git a/font_kit_studio_v0.1.1.html b/font_kit_studio_v0.1.1.html
index 25c197d..641b360 100644
--- a/font_kit_studio_v0.1.1.html
+++ b/font_kit_studio_v0.1.1.html
@@ -510,21 +510,20 @@ footer {
   min-width: 0;
   grid-template-columns: 1fr 1fr;
   gap: 24px;
   align-items: center;
   transition: grid-template-columns .16s ease, gap .16s ease;
 }
 .row-layout.is-collapsed { grid-template-columns: 1fr !important; }
 .row-child {
   min-width: 0;
   margin: 0;
-  height: 100%;
 }
 .row-child .slot-badge { left: 6px; }
 .row-child-list {
   display: grid;
   gap: 6px;
 }
 .row-child-jump {
   display: grid;
   grid-template-columns: 1fr auto;
   gap: 8px;
diff --git a/tests/test_font_kit_studio_v011.py b/tests/test_font_kit_studio_v011.py
index e09de62..5db8277 100644
--- a/tests/test_font_kit_studio_v011.py
+++ b/tests/test_font_kit_studio_v011.py
@@ -35,20 +35,99 @@ class BrowserCase(unittest.TestCase):
         })
         page.wait_for_function("/import/i.test(document.querySelector('#composerStatus').textContent)")
         self.assertIn('Composition imported.', page.locator('#composerStatus').inner_text())
 
     def export(self, page):
         page.locator('#exportJson').click()
         result = json.loads(page.locator('#exportDialogText').input_value())
         page.locator('#exportDialog').evaluate('(dialog) => dialog.close()')
         return result
 
+    def row_geometry(self, page):
+        # Wait for the inherited grid transition to finish before measuring tracks.
+        page.wait_for_timeout(220)
+        return page.locator('.row-layout').evaluate('''layout => {
+            const rect = element => {
+                const r = element.getBoundingClientRect();
+                return {x:r.x, y:r.y, width:r.width, height:r.height, bottom:r.bottom};
+            };
+            return {layout:rect(layout), collapsed:layout.classList.contains('is-collapsed'),
+                children:[...layout.children].map(rect),
+                order:[...layout.children].map(child => child.dataset.rowChild),
+                gap:parseFloat(getComputedStyle(layout).gap)};
+        }''')
+
+    def test_unequal_child_alignment_geometry(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                for alignment in ('start', 'center', 'end', 'stretch'):
+                    with self.subTest(alignment=alignment):
+                        self.import_slots(page, [{'type':'row', 'alignItems':alignment,
+                            'children':[{'type':'spacer', 'spacerHeight':40},
+                                        {'type':'spacer', 'spacerHeight':140}]}])
+                        geometry = self.row_geometry(page)
+                        short, tall = geometry['children']
+                        self.assertFalse(geometry['collapsed'])
+                        if alignment == 'stretch':
+                            self.assertAlmostEqual(short['height'], tall['height'], delta=1)
+                        else:
+                            self.assertAlmostEqual(tall['height'] - short['height'], 100, delta=1)
+                            offset = {'start':0, 'center':50, 'end':100}[alignment]
+                            self.assertAlmostEqual(short['y'] - tall['y'], offset, delta=1)
+                self.assertEqual(errors, [])
+
+    def test_weighted_columns_gaps_and_resize_observer_boundaries(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                self.assertEqual(page.locator('#canvasWidth').input_value(), '960')
+                for count in (2, 3, 4):
+                    self.import_slots(page, [{'type':'row', 'childCount':count,
+                        'ratios':list(range(1, count + 1)), 'gap':17, 'collapseAt':680,
+                        'children':[{'type':'spacer', 'spacerHeight':20 + i * 10}
+                                    for i in range(count)]}])
+                    # Change only container width: no window resize or app render event.
+                    # Responsive updates must therefore come from ResizeObserver.
+                    for width in (681, 680, 679, 681):
+                        page.locator('#composerCanvas').evaluate(
+                            '''(canvas, width) => {
+                                const parent = canvas.parentElement;
+                                const style = getComputedStyle(parent);
+                                const edges = ['paddingLeft', 'paddingRight', 'borderLeftWidth', 'borderRightWidth']
+                                    .reduce((sum, key) => sum + parseFloat(style[key]), 0);
+                                parent.style.width = `${width + edges}px`;
+                            }''', width)
+                        page.wait_for_function('''expected => {
+                            const canvas = document.querySelector('#composerCanvas');
+                            return Math.abs(canvas.getBoundingClientRect().width - expected.width) < .1
+                                && canvas.querySelector('.row-layout').classList.contains('is-collapsed') === expected.collapsed;
+                        }''', arg={'width':width, 'collapsed':width <= 680})
+                        geometry = self.row_geometry(page)
+                        children = geometry['children']
+                        self.assertEqual(geometry['order'], [str(i) for i in range(count)])
+                        self.assertAlmostEqual(geometry['gap'], 17, delta=.1)
+                        if width <= 680:
+                            for child in children:
+                                self.assertAlmostEqual(child['width'], geometry['layout']['width'], delta=1)
+                                self.assertAlmostEqual(child['x'], children[0]['x'], delta=1)
+                            for previous, child in zip(children, children[1:]):
+                                self.assertAlmostEqual(child['y'] - previous['bottom'], 17, delta=1)
+                        else:
+                            usable = geometry['layout']['width'] - 17 * (count - 1)
+                            total = sum(range(1, count + 1))
+                            for index, child in enumerate(children):
+                                self.assertAlmostEqual(child['width'], usable * (index + 1) / total, delta=1)
+                            for previous, child in zip(children, children[1:]):
+                                self.assertAlmostEqual(child['x'] - previous['x'] - previous['width'], 17, delta=1)
+                self.assertEqual(errors, [])
+
     def test_valid_row_factory_and_child_selection(self):
         for engine in ('chromium', 'firefox'):
             with self.subTest(engine=engine):
                 page, errors = self.page(engine)
                 page.locator('#compositionPreset').select_option('rowdemo')
                 page.locator('#applyPreset').click()
                 row = next(s for s in self.export(page)['composition']['slots'] if s['type'] == 'row')
                 self.assertEqual(row['childCount'], 2)
                 self.assertEqual(row['ratios'], [1, 2])
                 self.assertEqual([s['type'] for s in row['children']], ['image', 'text'])
```
