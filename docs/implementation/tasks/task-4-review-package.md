# Review package

Base: 979fa782d388d232e993b9eb2f5932446d7b84f0
Head: ae452d69fcf0d1471adee463e0383f06741c1a6f

## Commits

```text
ae452d6 Validate composition imports and harden nested exports
```

## Stat

```text
docs/implementation/tasks/task-4-report.md |  39 +++++++
 font_kit_studio_v0.1.1.html                |  97 +++++++++++++----
 tests/test_font_kit_studio_v011.py         | 168 ++++++++++++++++++++++++++++-
 3 files changed, 280 insertions(+), 24 deletions(-)
```

## Diff

```diff
diff --git a/docs/implementation/tasks/task-4-report.md b/docs/implementation/tasks/task-4-report.md
new file mode 100644
index 0000000..28d549e
--- /dev/null
+++ b/docs/implementation/tasks/task-4-report.md
@@ -0,0 +1,39 @@
+# Task 4 implementation report
+
+## Ownership and evidence
+
+Read task-4-brief.md first, AGENTS.md, README, implementation plan/progress/deviations, original design and baseline-exports-audit.md. Checked branch `feat/v0.1.1-responsive-rows` and starting HEAD `979fa782d388d232e993b9eb2f5932446d7b84f0`. Controller progress was already modified; concurrent tooling writer subsequently changed README/requirements/scripts and owns its own report. All nonassigned changes are preserved and excluded. This writer owns only HTML, tests and this report. No subagents, remote publication or runtime dependencies.
+
+Graph Verify parent list/search/coverage attempts returned Transport closed; project/generation/coverage unknown. Exact direct source and fresh Chromium/Firefox contexts establish this task's evidence. No graph verification is claimed.
+
+## Changes and reconciliation
+
+- Validate slot objects and row-children arrays during hydration. Reject malformed slot/children/background structural shapes with actionable messages. Build complete candidate background, normalized canvas width, hydrated slots, selection and kit IDs before publishing live state. Failed validation leaves composition JSON, IDs, selection, controls and canvas DOM unchanged. The original audit's fractional-count hydration exception is already fixed by Task 1, so that exact historical failure is not claimed reproduced here; newly accepted malformed shapes provide genuine RED rejection evidence.
+- Normalize known leaf scalar/enum fields and finite numbers to ordinary editable shapes/control bounds, including typography, image/rule/spacer settings. Invalid role types become Custom; harmless custom string roles survive. Use own-property role-default lookup so `__proto__` cannot inherit missing defaults. Valid metadata, text and variable-axis values survive; unsupported leaf descendants remain dropped. Unknown harmless metadata survives except reserved session asset payloads.
+- Strip every `assetDataUrl` key recursively through objects/arrays, both on import and across the entire exported state. This covers hidden metadata and nonimage extras rather than only recognized row/image nodes. Names/dimensions remain available for reselection; data URLs never survive JSON round trips.
+- CSS token export handles role types defensively and reserves every generated property name. Numeric suffixes now avoid both duplicate role slugs and suffix collisions (for example Body's `--font-body-size` versus a role named Body-size). Existing row-child traversal and row grid tokens remain.
+- Capture the original image slot object/ID when starting a file read. On completion, update it only if the same image still exists. A selection change no longer writes asset fields into the newly selected text slot; deleted/replaced images are ignored.
+- Extend existing BrowserCase helpers and add seven behavior tests. Characterize older v0.1.0 leaf import and v0.1.1 row round trip, real PNG/SVG decode and JPEG rejection; regressions cover malformed structures/transactionality, numeric roles, prototype role defaults, property collisions, recursive privacy and controlled delayed FileReader selection race. No production testing globals.
+
+## Exact commands and results
+
+All commands run at repository root `C:/Users/peter/Documents/Codex/2026-09-30/ref/outputs/font-kit-studio`.
+
+1. `git status --short; git rev-parse HEAD` plus required direct reads — expected baseline above; controller progress edit preserved. Targeted renderer, hydration, importer/exporter and file-reader reads identified exact boundaries.
+2. **Initial RED**, unchanged HTML: `python -m unittest discover -s tests -p test_font_kit_studio_v011.py -k task4 -v` — `Ran 4 tests in 23.218s`, `FAILED (failures=7, errors=1)`, exit 1. Both browsers: `slot.role.toLowerCase is not a function`; null slot accepted instead of rejected; `HIDDEN` asset retained in nested metadata. Chromium race fails original image name (`logo.svg` instead of `delayed.png`); callback wrote into newly selected text. Firefox's PNG decode reported `Invalid encoded image data` because the initial canned fixture had an invalid CRC. This fixture error is not claimed as an application defect.
+3. **Independent collision RED**, unchanged HTML: `python -m unittest discover -s tests -p test_font_kit_studio_v011.py -k task4_css_slug -v` — `Ran 1 test in 5.205s`, `FAILED (failures=2)`, exit 1. Both browsers: 32 declarations versus 24 unique names for Body/Body/Body-2/Body-size.
+4. **Independent background-shape RED**, unchanged HTML: `python -m unittest discover -s tests -p test_font_kit_studio_v011.py -k task4_failed_background -v` — `Ran 1 test in 5.153s`, `FAILED (failures=2)`, exit 1. Both browsers wrongly report successful import for numeric background 42. This demonstrates missing validation, not a reproduced historical fractional exception.
+5. Replaced test PNG with a CRC-valid 1x1 RGBA PNG assembled from standard-library chunks. **Race RED**, unchanged HTML: `python -m unittest discover -s tests -p test_font_kit_studio_v011.py -k task4_image -v` — `Ran 1 test in 4.888s`, `FAILED (failures=2)`, exit 1. Both engines decode PNG 1x1 and SVG 3x2, reject JPEG and then fail the delayed selection race (`logo.svg` remains on original image). Standard FileReader is delayed by a test-only DOM event; actual file reading resumes after child selection changes.
+6. **Focused GREEN**, after candidate validation/export/race fixes: `python -m unittest discover -s tests -p test_font_kit_studio_v011.py -k task4 -v` — `Ran 6 tests in 27.991s`, `OK`, exit 0. Both engines pass known regressions, recursive stripping and round trips. Malformed inputs now fail with prior export and DOM unchanged.
+7. **Additional defaults RED**, before own-property role fix: `python -m unittest discover -s tests -p test_font_kit_studio_v011.py -k task4_known_leaf -v` — `Ran 1 test in 4.651s`, `FAILED (errors=2)`, exit 1. Both engines report `KeyError: 'text'` for accepted role `__proto__`, because inherited defaults omit text and size. Same command after fix — `Ran 1 test in 5.158s`, `OK`, exit 0. Malformed object role/text, bad size, array variables and invalid element/style normalize to safe defaults and export without crash.
+8. Final full scoped suite: `python -m unittest discover -s tests -v` — `Ran 17 tests in 92.384s`, `OK`, exit 0. Sixteen behavior tests run both Chromium and Firefox; the structural test passes. Browser pageerror lists empty.
+9. Syntax extraction: `python -c "import re; from pathlib import Path; s=Path('font_kit_studio_v0.1.1.html').read_text(encoding='utf-8'); Path('work/inline.js').write_text('\n'.join(re.findall(r'<script[^>]*>(.*?)</script>',s,re.S)),encoding='utf-8')"`; `node --check work/inline.js` — exit 0, no syntax errors. Scratch is ignored.
+10. `git diff --check` — exit 0, no whitespace errors; informational LF-to-CRLF warnings only. Direct assigned diff review completed.
+
+## Self-review and limitations
+
+Reviewed hydration publication order, authoritative IDs/types, leaf metadata preservation, recursive reserved-key stripping, property-name reservation and original-object upload binding. Candidate validation does not modify live state before success; all malformed-case tests compare full exports (including IDs/selection) and DOM. New file-reader tests use a controlled real read rather than production hooks. Real image decode and dimensions establish usable PNG/SVG behavior in both engines; JPEG rejection keeps prior image. All behavior tests capture page errors.
+
+Known field normalization deliberately uses incumbent inspector bounds; imported values outside those controls clamp. Canvas width normalizes to 240–2400px or fluid, with 960px fallback. Extra metadata is retained, but all reserved `assetDataUrl` values are cleared regardless of nesting/type. No new deep-row support or binary persistence is introduced. Invalid image bytes with allowed MIME/extension are outside this task's decoder acceptance; PNG/SVG decoder failure handling is not redesigned. File-reader binding prevents changed/deleted-target corruption; multiple concurrent uploads to the same unchanged image are not separately ordered. External Adobe fonts and global Library acceptance remain for final verification. Independent review is pending controller dispatch.
+
+Files: `font_kit_studio_v0.1.1.html`, `tests/test_font_kit_studio_v011.py`, this report. Commit message: `Validate composition imports and harden nested exports`; final handoff supplies identifier (report included in commit). Nonassigned controller/tooling changes are not staged.
diff --git a/font_kit_studio_v0.1.1.html b/font_kit_studio_v0.1.1.html
index 7c46939..be12ac9 100644
--- a/font_kit_studio_v0.1.1.html
+++ b/font_kit_studio_v0.1.1.html
@@ -1546,21 +1546,21 @@ if (remembered) kitId.value = remembered;
   const SLOT_TYPES = ["text", "image", "rule", "spacer", "row"];
   const LEAF_SLOT_TYPES = ["text", "image", "rule", "spacer"];
   const ROW_ALIGNMENTS = ["start", "center", "end", "stretch"];
   const ALIGNMENTS = ["left", "center", "right", "justify"];
   const TRANSFORMS = ["none", "uppercase", "lowercase", "capitalize"];
 
   const byName = name => fonts.find(f => f.name === name) || fonts[0];
   const byFamily = family => fonts.find(f => f.family === family) || fonts[0];
 
   const makeTextSlot = (role="Body", family="gotham", overrides={}) => {
-    const def = ROLE_DEFAULTS[role] || ROLE_DEFAULTS.Custom;
+    const def = Object.hasOwn(ROLE_DEFAULTS, role) ? ROLE_DEFAULTS[role] : ROLE_DEFAULTS.Custom;
     const font = byFamily(family);
     const first = font.styles[0];
     const vars = {};
     if (font.variable) {
       Object.entries(font.variable).forEach(([axis, range]) => { vars[axis] = range[2]; });
     }
     return {
       id: crypto.randomUUID ? crypto.randomUUID() : `slot-${Date.now()}-${Math.random()}`,
       type: "text",
       role,
@@ -1765,37 +1765,76 @@ if (remembered) kitId.value = remembered;
     if (ids.length) composerKitIds.value = ids.join(", ");
   });
   loadComposerKits.addEventListener("click", loadComposerKitStyles);
   composerKitIds.addEventListener("keydown", e => { if (e.key === "Enter") loadComposerKitStyles(); });
 
   function clone(value) { return JSON.parse(JSON.stringify(value)); }
 
   function freshId() { return crypto.randomUUID ? crypto.randomUUID() : `slot-${Date.now()}-${Math.random()}`; }
 
   function hydrateSlot(raw, depth=0) {
+    if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
+      throw new Error("Each slot must be an object; check composition.slots and row children.");
+    }
+    raw = stripSessionAssets(raw);
     const requested = String(raw?.type || "text");
     if (requested === "row" && depth === 0) {
+      if (raw.children !== undefined && !Array.isArray(raw.children)) {
+        throw new Error("Row slot children must be an array.");
+      }
       const rawChildren = Array.isArray(raw.children) ? raw.children.slice(0, 4) : [];
       const children = rawChildren.map(child => hydrateSlot(child, 1)).filter(child => child.type !== "row");
       while (children.length < 2) children.push(makeTextSlot("Custom", "gotham"));
       const count = rowNumber(raw.childCount, children.length, 2, 4, true);
       while (children.length < count) children.push(makeTextSlot("Custom", "gotham"));
       children.length = count;
       const row = makeRowSlot({ ...raw, children, childCount:count });
       row.id = freshId();
       row.children = row.children.map(child => ({ ...child, id:freshId(), assetDataUrl:child.type === "image" ? "" : child.assetDataUrl }));
       return row;
     }
     const type = LEAF_SLOT_TYPES.includes(requested) ? requested : "text";
-    const base = type === "text" ? makeTextSlot(raw?.role || "Custom", raw?.family || "gotham") : makeGenericSlot(type);
+    const role = typeof raw.role === "string" && raw.role.trim() ? raw.role : "Custom";
+    const base = type === "text" ? makeTextSlot(role, typeof raw.family === "string" ? raw.family : "gotham") : makeGenericSlot(type);
     const { children:discardedChildren, ...leaf } = raw || {};
-    return { ...base, ...leaf, type, id:freshId(), assetDataUrl:type === "image" ? "" : (raw?.assetDataUrl || "") };
+    const slot = { ...base, ...leaf, type, id:freshId(), assetDataUrl:"" };
+    // Imported known fields must keep the same scalar shapes as editable leaves.
+    Object.keys(base).forEach(key => {
+      if (typeof base[key] === "string" && typeof slot[key] !== "string") slot[key] = base[key];
+      if (typeof base[key] === "number") slot[key] = rowNumber(slot[key], base[key], -Number.MAX_VALUE, Number.MAX_VALUE);
+    });
+    if (type === "text") {
+      slot.role = role;
+      slot.family = byFamily(slot.family).family;
+      slot.element = ELEMENTS.includes(slot.element) ? slot.element : base.element;
+      slot.transform = TRANSFORMS.includes(slot.transform) ? slot.transform : base.transform;
+      slot.fontStyle = ["normal", "italic", "oblique"].includes(slot.fontStyle) ? slot.fontStyle : base.fontStyle;
+      slot.size = rowNumber(slot.size, base.size, 8, 86);
+      slot.lineHeight = rowNumber(slot.lineHeight, base.lineHeight, .7, 3);
+      slot.tracking = rowNumber(slot.tracking, base.tracking, -.2, 1);
+      slot.weight = rowNumber(slot.weight, base.weight, 1, 1000);
+      slot.styleIndex = rowNumber(slot.styleIndex, base.styleIndex, 0, byFamily(slot.family).styles.length - 1, true);
+      const variables = raw.variables && typeof raw.variables === "object" && !Array.isArray(raw.variables) ? raw.variables : base.variables;
+      slot.variables = Object.fromEntries(Object.entries(variables).filter(([axis, value]) =>
+        /^[a-zA-Z0-9]{4}$/.test(axis) && typeof value === "number" && Number.isFinite(value)));
+    }
+    slot.align = ALIGNMENTS.includes(slot.align) ? slot.align : base.align;
+    slot.colorSource = ["custom", "tailwind", "saved"].includes(slot.colorSource) ? slot.colorSource : base.colorSource;
+    slot.colorHex = CSS.supports("color", slot.colorHex) ? slot.colorHex : base.colorHex;
+    if (type !== "text") {
+      slot.imageWidth = rowNumber(slot.imageWidth, base.imageWidth, 16, 800);
+      slot.opacity = rowNumber(slot.opacity, base.opacity, .05, 1);
+      slot.ruleWidth = rowNumber(slot.ruleWidth, base.ruleWidth, 1, 100);
+      slot.ruleThickness = rowNumber(slot.ruleThickness, base.ruleThickness, 1, 20);
+      slot.spacerHeight = rowNumber(slot.spacerHeight, base.spacerHeight, 4, 240);
+    }
+    return slot;
   }
 
   function applyCompositionPreset(key) {
     const preset = COMPOSITION_PRESETS[key] || COMPOSITION_PRESETS.asteria;
     state.canvasWidth = preset.width;
     state.background = clone(preset.background);
     state.slots = preset.slots.map(slot => hydrateSlot(slot, 0));
     state.selectedId = state.slots[0]?.id || null;
     syncCompositionControls();
     renderComposer();
@@ -2344,23 +2383,25 @@ if (remembered) kitId.value = remembered;
       assetFile?.addEventListener("change", () => {
         const file = assetFile.files?.[0];
         if (!file) return;
         const allowed = ["image/png", "image/svg+xml"];
         const extOkay = /\.(png|svg)$/i.test(file.name);
         if (!allowed.includes(file.type) || !extOkay) {
           composerStatus.textContent = "Asset rejected: v0.1.1 accepts PNG and SVG only.";
           assetFile.value = "";
           return;
         }
+        const target = selectedSlot();
         const reader = new FileReader();
         reader.onload = () => {
-          const current = selectedSlot();
+          const current = findSlotById(target.id)?.slot;
+          if (current !== target || current.type !== "image") return;
           current.imageName = file.name;
           current.assetDataUrl = String(reader.result || "");
           renderComposer();
           composerStatus.textContent = `${file.name} loaded for this session.`;
         };
         reader.readAsDataURL(file);
       });
     } else if (slot.type === "rule") {
       bindSimpleInput('[data-bind="ruleWidth"]', "input", Number);
       bindSimpleInput('[data-bind="ruleThickness"]', "input", Number);
@@ -2394,69 +2435,71 @@ if (remembered) kitId.value = remembered;
   canvasBgFamily.addEventListener("change", () => {
     state.background.family = canvasBgFamily.value;
     updateShadeOptions(canvasBgFamily, canvasBgShade, Object.keys(TAILWIND_COLORS[state.background.family] || {})[5]);
     state.background.shade = canvasBgShade.value;
     updateCanvasBackground();
   });
   canvasBgShade.addEventListener("change", () => { state.background.shade = canvasBgShade.value; updateCanvasBackground(); });
   canvasSavedColor.addEventListener("change", () => { state.background.saved = canvasSavedColor.value; updateCanvasBackground(); });
 
   function stripSessionAssets(slot) {
-    const clean = clone(slot);
-    if (clean.type === "image") clean.assetDataUrl = "";
-    if (clean.type === "row") clean.children = slot.children.map(stripSessionAssets);
-    return clean;
+    if (Array.isArray(slot)) return slot.map(stripSessionAssets);
+    if (!slot || typeof slot !== "object") return slot;
+    return Object.fromEntries(Object.entries(slot).map(([key, value]) =>
+      [key, key === "assetDataUrl" ? "" : stripSessionAssets(value)]));
   }
 
   function serializableState() {
-    const clean = clone(state);
-    clean.slots = state.slots.map(stripSessionAssets);
+    const clean = stripSessionAssets(state);
     return { version:"0.1.1", app:"Font Kit Studio", kitIds:normalizeKitIds(composerKitIds.value), composition:clean };
   }
 
   function showExport(title, text, filename, mime) {
     exportDialogTitle.textContent = title;
     exportDialogText.value = text;
     exportFilename = filename;
     exportMime = mime;
     if (typeof exportDialog.showModal === "function") exportDialog.showModal();
     else exportDialog.setAttribute("open", "");
   }
 
   function exportCompositionJson() {
     showExport("Composition JSON", JSON.stringify(serializableState(), null, 2), "font-kit-studio-composition.json", "application/json");
   }
 
   function cssTokenName(slot, index) {
-    const base = slot.role ? slot.role.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") : `slot-${index+1}`;
+    const base = typeof slot.role === "string" ? slot.role.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") : `slot-${index+1}`;
     return base || `slot-${index+1}`;
   }
 
   function walkLeafSlots(slots) {
     const leaves = [];
     slots.forEach(slot => {
       if (slot.type === "row") slot.children.forEach(child => leaves.push(child));
       else leaves.push(slot);
     });
     return leaves;
   }
 
   function exportCompositionCss() {
     const lines = [":root {"];
-    const usedNames = new Map();
+    const usedNames = new Set();
     walkLeafSlots(state.slots).forEach((slot, index) => {
       if (slot.type !== "text") return;
       const font = byFamily(slot.family);
       const baseName = cssTokenName(slot, index);
-      const seen = (usedNames.get(baseName) || 0) + 1;
-      usedNames.set(baseName, seen);
-      const name = seen === 1 ? baseName : `${baseName}-${seen}`;
+      const properties = name => ["", "-size", "-weight", "-style", "-tracking", "-line-height"]
+        .map(suffix => `--font-${name}${suffix}`).concat(`--color-${name}`);
+      let name = baseName;
+      let suffix = 2;
+      while (properties(name).some(property => usedNames.has(property))) name = `${baseName}-${suffix++}`;
+      properties(name).forEach(property => usedNames.add(property));
       lines.push(`  --font-${name}: ${cssStack(font)};`);
       lines.push(`  --font-${name}-size: ${slot.size}px; /* ${formatSize(slot.size).replace(/^.*\(/, "").replace(/\)$/, "")} */`);
       lines.push(`  --font-${name}-weight: ${slot.weight};`);
       lines.push(`  --font-${name}-style: ${slot.fontStyle};`);
       lines.push(`  --font-${name}-tracking: ${slot.tracking}em;`);
       lines.push(`  --font-${name}-line-height: ${slot.lineHeight};`);
       lines.push(`  --color-${name}: ${resolvedColor(slot)};`);
     });
     state.slots.forEach((slot, index) => {
       if (slot.type !== "row") return;
@@ -2467,28 +2510,38 @@ if (remembered) kitId.value = remembered;
     lines.push(`  --brand-canvas: ${resolvedColor({source:state.background.source,hex:state.background.hex,family:state.background.family,shade:state.background.shade,saved:state.background.saved})};`);
     lines.push("}");
     showExport("CSS tokens", lines.join("\n"), "font-kit-studio-tokens.css", "text/css");
   }
 
   function importCompositionJson(file) {
     const reader = new FileReader();
     reader.onload = () => {
       try {
         const data = JSON.parse(String(reader.result || "{}"));
-        if (!data.composition || !Array.isArray(data.composition.slots)) throw new Error("Missing composition.slots");
+        if (!data || !data.composition || !Array.isArray(data.composition.slots)) throw new Error("Missing composition.slots array.");
         const incoming = data.composition;
-        state.canvasWidth = incoming.canvasWidth || "960";
-        state.background = incoming.background || clone(COMPOSITION_PRESETS.blank.background);
-        state.slots = incoming.slots.slice(0,8).map(raw => hydrateSlot(raw, 0));
-        if (!state.slots.length) state.slots = [makeTextSlot("Custom", "gotham")];
-        state.selectedId = state.slots[0].id;
-        if (Array.isArray(data.kitIds) && data.kitIds.length) composerKitIds.value = data.kitIds.join(", ");
+        if (incoming.background !== undefined && (!incoming.background || typeof incoming.background !== "object" || Array.isArray(incoming.background))) {
+          throw new Error("Composition background must be an object.");
+        }
+        const background = { ...COMPOSITION_PRESETS.blank.background, ...stripSessionAssets(incoming.background || {}) };
+        const defaults = COMPOSITION_PRESETS.blank.background;
+        Object.keys(defaults).forEach(key => { if (typeof background[key] !== "string") background[key] = defaults[key]; });
+        if (!["custom", "tailwind", "saved"].includes(background.source)) background.source = defaults.source;
+        if (!CSS.supports("color", background.hex)) background.hex = defaults.hex;
+        const slots = incoming.slots.slice(0,8).map(raw => hydrateSlot(raw, 0));
+        if (!slots.length) slots.push(makeTextSlot("Custom", "gotham"));
+        const width = String(incoming.canvasWidth || "960");
+        const kitIds = Array.isArray(data.kitIds) ? normalizeKitIds(data.kitIds.filter(id => typeof id === "string").join(", ")) : [];
+        // Only publish a fully hydrated candidate; failed validation leaves live state intact.
+        Object.assign(state, { canvasWidth:width === "100%" ? width : String(rowNumber(width, 960, 240, 2400)),
+          background, slots, selectedId:slots[0].id });
+        if (kitIds.length) composerKitIds.value = kitIds.join(", ");
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
index bfbae05..9a3a948 100644
--- a/tests/test_font_kit_studio_v011.py
+++ b/tests/test_font_kit_studio_v011.py
@@ -1,12 +1,15 @@
 import json
+import re
+import struct
 import unittest
+import zlib
 from pathlib import Path
 
 from playwright.sync_api import sync_playwright
 
 HTML = Path(__file__).resolve().parents[1] / 'font_kit_studio_v0.1.1.html'
 
 
 class BrowserCase(unittest.TestCase):
     def setUp(self):
         self.runtime = sync_playwright().start()
@@ -21,27 +24,31 @@ class BrowserCase(unittest.TestCase):
         browser = getattr(self.runtime, engine).launch()
         self.browsers.append(browser)
         page = browser.new_page(viewport={'width': 1600, 'height': 1200})
         errors = []
         page.on('pageerror', lambda error: errors.append(str(error)))
         page.goto(HTML.as_uri())
         page.locator('#modeComposer').click()
         return page, errors
 
     def import_slots(self, page, slots):
+        status = self.import_document(page, {'version': '0.1.1', 'composition': {'slots': slots}})
+        self.assertIn('Composition imported.', status)
+
+    def import_document(self, page, data):
         page.locator('#composerStatus').evaluate('(status) => status.textContent = ""')
         page.locator('#importJsonFile').set_input_files({
             'name': 'composition.json', 'mimeType': 'application/json',
-            'buffer': json.dumps({'version': '0.1.1', 'composition': {'slots': slots}}).encode(),
+            'buffer': json.dumps(data).encode(),
         })
         page.wait_for_function("/import/i.test(document.querySelector('#composerStatus').textContent)")
-        self.assertIn('Composition imported.', page.locator('#composerStatus').inner_text())
+        return page.locator('#composerStatus').inner_text()
 
     def export(self, page):
         page.locator('#exportJson').click()
         result = json.loads(page.locator('#exportDialogText').input_value())
         page.locator('#exportDialog').evaluate('(dialog) => dialog.close()')
         return result
 
     def row_geometry(self, page):
         # Wait for the inherited grid transition to finish before measuring tracks.
         page.wait_for_timeout(220)
@@ -49,20 +56,177 @@ class BrowserCase(unittest.TestCase):
             const rect = element => {
                 const r = element.getBoundingClientRect();
                 return {x:r.x, y:r.y, width:r.width, height:r.height, bottom:r.bottom};
             };
             return {layout:rect(layout), collapsed:layout.classList.contains('is-collapsed'),
                 children:[...layout.children].map(rect),
                 order:[...layout.children].map(child => child.dataset.rowChild),
                 gap:parseFloat(getComputedStyle(layout).gap)};
         }''')
 
+    def test_task4_failed_import_is_transactional(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                before = self.export(page)
+                before_canvas = page.locator('#composerCanvas').inner_html()
+                for malformed in ([None], [42], [[]], [{'type':'row', 'children':{}}],
+                                  [{'type':'row', 'children':[{'type':'text'}, None]}]):
+                    status = self.import_document(page, {'composition': {'canvasWidth':'640',
+                        'background':{'source':'custom', 'hex':'#ffffff'}, 'slots':malformed}})
+                    self.assertTrue(status.startswith('Import failed:'), status)
+                    self.assertIn('slot', status.lower())
+                    self.assertEqual(self.export(page), before)
+                    self.assertEqual(page.locator('#composerCanvas').inner_html(), before_canvas)
+                # A malformed background previously throws after live state assignments.
+                status = self.import_document(page, {'composition': {'canvasWidth':'640',
+                    'background':42, 'slots':[{'type':'text', 'text':'replacement'}]}})
+                self.assertTrue(status.startswith('Import failed:'), status)
+                self.assertEqual(self.export(page), before)
+                self.assertEqual(errors, [])
+
+    def test_task4_css_roles_are_valid_and_collision_free(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                self.import_slots(page, [{'type':'row', 'childCount':4, 'children':[
+                    {'type':'text', 'role':12}, {'type':'text', 'role':'Body'},
+                    {'type':'text', 'role':'Body'}, {'type':'text', 'role':'Body-2'}]},
+                    {'type':'text', 'role':'Body-size'}])
+                page.locator('#exportCss').click()
+                self.assertEqual(errors, [], 'CSS export must not throw for accepted roles')
+                self.assertTrue(page.locator('#exportDialog').evaluate('dialog => dialog.open'))
+                css = page.locator('#exportDialogText').input_value()
+                declarations = re.findall(r'^\s*(--[a-z0-9-]+):', css, re.M)
+                self.assertEqual(len(declarations), len(set(declarations)), css)
+                families = re.findall(r'^\s*--font-[a-z0-9-]+: [^;]*,', css, re.M)
+                self.assertEqual(len(families), 5, css)
+                self.assertIn('--row-1-columns:', css)
+
+    def test_task4_failed_background_import_preserves_state(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                before = self.export(page)
+                status = self.import_document(page, {'composition': {'canvasWidth':'640',
+                    'background':42, 'slots':[{'type':'text', 'text':'replacement'}]}})
+                self.assertTrue(status.startswith('Import failed:'), status)
+                self.assertEqual(self.export(page), before)
+                self.assertEqual(errors, [])
+
+    def test_task4_css_slug_and_property_suffix_collisions(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                self.import_slots(page, [{'type':'row', 'childCount':4, 'children':[
+                    {'type':'text', 'role':role} for role in ('Body','Body','Body-2','Body-size')]}])
+                page.locator('#exportCss').click()
+                css = page.locator('#exportDialogText').input_value()
+                declarations = re.findall(r'^\s*(--[a-z0-9-]+):', css, re.M)
+                self.assertEqual(len(declarations),len(set(declarations)),css)
+                self.assertEqual(errors, [])
+
+    def test_task4_known_leaf_fields_have_safe_shapes(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                self.import_slots(page, [{'type':'row', 'children':[
+                    {'type':'text', 'role':'__proto__'},
+                    {'type':'text', 'role':{}, 'size':'bad', 'variables':[{'wght':500}],
+                     'text':{}, 'fontStyle':'italic; --bad: red', 'element':'script'}]}])
+                for child in self.export(page)['composition']['slots'][0]['children']:
+                    self.assertIsInstance(child['role'], str)
+                    self.assertIsInstance(child['text'], str)
+                    self.assertIsInstance(child['size'], (int,float))
+                    self.assertIsInstance(child['variables'],dict)
+                    self.assertIn(child['fontStyle'], ('normal','italic','oblique'))
+                    self.assertNotEqual(child['element'],'script')
+                page.locator('#exportCss').click()
+                self.assertNotIn('--bad:',page.locator('#exportDialogText').input_value())
+                self.assertEqual(errors, [])
+
+    def test_task4_recursive_asset_privacy_and_old_json_round_trip(self):
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                old = {'version':'0.1.0', 'composition': {'slots':[
+                    {'type':'text', 'role':'Body', 'text':'legacy', 'size':31},
+                    {'type':'image', 'imageName':'logo.svg', 'imageWidth':123, 'assetDataUrl':'SECRET',
+                     'metadata':{'owner':'retained', 'nested':[{'assetDataUrl':'HIDDEN'}]}}]}}
+                self.assertIn('Composition imported.', self.import_document(page, old))
+                exported = self.export(page)
+                self.assertEqual(exported['version'], '0.1.1')
+                self.assertEqual(exported['composition']['slots'][0]['text'], 'legacy')
+                self.assertEqual(exported['composition']['slots'][0]['size'], 31)
+                image = exported['composition']['slots'][1]
+                self.assertEqual((image['imageName'], image['imageWidth']), ('logo.svg',123))
+                self.assertEqual(image['metadata']['owner'], 'retained')
+                self.assertNotIn('SECRET', json.dumps(exported))
+                self.assertNotIn('HIDDEN', json.dumps(exported))
+                self.import_slots(page, [{'type':'row', 'gap':33, 'ratios':[2,3], 'children':[
+                    {'type':'image', 'imageName':'nested.png', 'assetDataUrl':'NESTED',
+                     'extra':{'assetDataUrl':'DEEP'}}, {'type':'text', 'role':'Accent', 'text':'inside'}]}])
+                first = self.export(page)
+                self.assertNotIn('NESTED', json.dumps(first))
+                self.assertNotIn('DEEP', json.dumps(first))
+                self.assertIn('Composition imported.', self.import_document(page, first))
+                second = self.export(page)
+                def without_ids(value):
+                    if isinstance(value, dict):
+                        return {k:without_ids(v) for k,v in value.items() if k not in ('id','selectedId')}
+                    if isinstance(value, list):
+                        return [without_ids(v) for v in value]
+                    return value
+                self.assertEqual(without_ids(first), without_ids(second))
+                self.assertEqual(errors, [])
+
+    def test_task4_image_upload_decode_rejection_and_selection_race(self):
+        def chunk(kind, data):
+            return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data))
+        png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR',struct.pack('!2I5B',1,1,8,6,0,0,0))
+               + chunk(b'IDAT',zlib.compress(b'\x00\xff\x00\x00\xff')) + chunk(b'IEND',b''))
+        svg = b'<svg xmlns="http://www.w3.org/2000/svg" width="3" height="2"><rect width="3" height="2" fill="red"/></svg>'
+        for engine in ('chromium', 'firefox'):
+            with self.subTest(engine=engine):
+                page, errors = self.page(engine)
+                self.import_slots(page, [{'type':'row', 'children':[{'type':'image'}, {'type':'text', 'text':'safe'}]}])
+                page.locator('.row-child').first.click()
+                for name, mime, buffer, dimensions in (
+                    ('pixel.png','image/png',png,(1,1)), ('logo.svg','image/svg+xml',svg,(3,2))):
+                    page.locator('#assetFile').set_input_files({'name':name,'mimeType':mime,'buffer':buffer})
+                    page.wait_for_function('''name => document.querySelector('#composerStatus').textContent.includes(`${name} loaded`)''', arg=name)
+                    image = page.locator('.row-child img')
+                    image.evaluate('image => image.decode()')
+                    self.assertEqual(image.evaluate('image => [image.naturalWidth,image.naturalHeight]'), list(dimensions))
+                    data = self.export(page)['composition']['slots'][0]['children'][0]
+                    self.assertEqual(data['imageName'], name)
+                    self.assertEqual(data['assetDataUrl'], '')
+                page.locator('#assetFile').set_input_files({'name':'photo.jpg','mimeType':'image/jpeg','buffer':png})
+                self.assertIn('Asset rejected:', page.locator('#composerStatus').inner_text())
+                self.assertEqual(page.locator('.row-child img').get_attribute('alt'), 'logo.svg')
+                # Hold an actual FileReader until selection changes, then release it.
+                page.evaluate('''() => { const NativeReader = FileReader;
+                    window.FileReader = class extends NativeReader {
+                        readAsDataURL(file) { document.addEventListener('test-release-asset-read',
+                            () => super.readAsDataURL(file), {once:true}); }
+                    }; }''')
+                page.locator('#assetFile').set_input_files({'name':'delayed.png','mimeType':'image/png','buffer':png})
+                page.locator('.row-child').nth(1).click()
+                page.evaluate("document.dispatchEvent(new Event('test-release-asset-read'))")
+                page.wait_for_function("document.querySelector('#composerStatus').textContent.includes('delayed.png loaded')")
+                children = self.export(page)['composition']['slots'][0]['children']
+                self.assertEqual(children[0]['imageName'], 'delayed.png')
+                self.assertNotIn('imageName', children[1])
+                self.assertEqual(children[1]['text'], 'safe')
+                page.locator('.row-child img').evaluate('image => image.decode()')
+                self.assertEqual(errors, [])
+
     def test_row_inspector_normalized_values_and_labels(self):
         for engine in ('chromium', 'firefox'):
             with self.subTest(engine=engine):
                 page, errors = self.page(engine)
                 self.import_slots(page, [{'type':'row', 'gap':99999, 'collapseAt':99999,
                     'ratios':[99999, -99999]}])
                 row = self.export(page)['composition']['slots'][0]
                 self.assertEqual((row['gap'], row['collapseAt'], row['ratios']), (96, 1600, [12, .25]))
                 for selector, event, cases, key in (
                     ('[data-bind="rowChildCount"]', 'change', [('1',2), ('5',4), ('2.5',3), ('',2)], 'childCount'),
```
