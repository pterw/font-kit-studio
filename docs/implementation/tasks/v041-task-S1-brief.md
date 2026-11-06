# Task S1: remove Asteria from the product

BASE: `5bd655e1cf5b891b960902d7836b3e756bcbb625`. Rules: `constraints.md` in this workspace (O2, O6, O7, O9 bind).
Branch for landing: `refactor/remove-asteria`. Mode: code. One implementer, one writer per file.

## Why

Font Kit Studio was first written inside another project and used it as its test target. Studio still ships that
project's name in a composition preset and a saved-colour palette. The product must stand on its own.

## Touches

- `fontkit-studio.html`
- `tests/test_studio_dead_controls.py`, `tests/test_studio_import_link.py`, `tests/test_studio_live.py`,
  `tests/test_studio_roles.py`
- `tests/fixtures/bridge/target.html`
- `CHANGELOG.md` (one line under Unreleased)

Do not touch: `docs/`, `font-kit-studio-v0.2.0-design-bridge-protocol-v1.md`, `README.md`, the version labels, the
export format version, `fontkit-bridge.js`. Dated records and the spec keep their wording (O7).

## Required behaviour

1. **Preset gone.** `#compositionPreset` offers `rowdemo` and `blank` only, and `COMPOSITION_PRESETS` has no `asteria`
   key. `rowdemo` stays the default and is otherwise unchanged. A request for an unknown preset key resolves as it does
   today (`fontkit-studio.html:2488`, falls back to `rowdemo`).
2. **Palette renamed, hex unchanged.** `CUSTOM_COLORS` holds these names in this order:

   | Old | New | Hex |
   |---|---|---|
   | Asteria Void | Ink Black | `#030409` |
   | Asteria Abyss | Deep Navy | `#060a17` |
   | Asteria Haze | Midnight | `#0b1022` |
   | Asteria Starlight | Ice White | `#eef2ff` |
   | Asteria Mist | Slate Mist | `#98a3c5` |
   | Asteria Gold | Soft Gold | `#e6c88d` |
   | Asteria Tender | Dusty Rose | `#dca8b7` |
   | Asteria Serene | Powder Blue | `#9dbdd6` |
   | Asteria Electric | Lavender | `#b8a2da` |
   | Asteria Verdant | Sage | `#a2c6ab` |
   | Asteria Vesper | Periwinkle | `#909dd0` |

   Every default that names an old colour names the new one: lines 2197, 2212, 2272, 2284, 2304 at BASE. The saved
   name beside `#f5f1e8` already differs from its hex; keep that relationship, do not change the hex.
3. **Old saved files look the same.** A composition JSON exported by 0.4.0 can hold an old name as a slot's
   `savedColor` or the background's `saved`, with `colorSource` or `source` set to `"saved"`. Today an unknown name
   renders `#000000` (`fontkit-studio.html:2576`). After this task, importing such a file:
   - renders the old colour's hex, for slots and the background;
   - shows the new name selected in the inspector's Saved list;
   - exports the new name afterwards.

   One small lookup of old name to new name, applied to every imported slot (text, image, rule, spacer, and the
   children of a row) and to the background, whatever the colour source: a `custom` slot still holds the old name in
   `savedColor`, and 0.4.0 exports it on almost every slot. It runs inside `hydrateSlot` after the string-shape check
   (`fontkit-studio.html:2447-2450`), so image, rule and spacer slots are covered, and on the background in
   `importCompositionJson` after its string defaults (line 3288). Use `Object.hasOwn` or a `Map`, never a plain
   `lookup[name] || name`, so names such as `constructor` stay as they are. It is not shown in any UI. Its 11 old names
   are the only place `Asteria` remains in `fontkit-studio.html`, under a one-line comment saying why.
4. **Other unknown saved names** behave exactly as they do today.
5. **Fixture.** `tests/fixtures/bridge/target.html:25` shows `Sample` instead of `Asteria`. Checked at BASE: no test
   reads that text. `tests/test_bridge_runtime.py` is the only module that loads the page, so run it in full.
6. **CHANGELOG.** One bullet under `## [Unreleased]`, under a new `### Changed` heading:
   `- The Sculptural composition preset is removed and the saved colours have new neutral names (Ink Black, Deep Navy,
   Midnight, Ice White, Slate Mist, Soft Gold, Dusty Rose, Powder Blue, Lavender, Sage, Periwinkle); compositions saved
   with the old names still open with the same colours.` Touch no dated entry.

## Tests

The four test modules use `asteria` as "a preset other than the default". After the change only `rowdemo` and `blank`
exist. `blank` has the default's background (`#f5f1e8`) and the same Inter and IBM Plex Mono tokens as the `blank`
documents in `test_studio_import_link.py`, so the moves are not mechanical. Per call site, from the brief review (confirm
each by running it):

| Module:line | What to do |
|---|---|
| `test_studio_dead_controls.py:21,77-80,110-114` | The background cannot differ. Delete `ASTERIA_BACKGROUND`. Wait for `/^Blank/` in `#composerStatus`. Prove the replacement with `#slotCount` (rowdemo 4, blank 5) and/or the canvas differing from the default, plus the select value `blank`. Keep `EDITORIAL_BACKGROUND`. |
| `test_studio_dead_controls.py:93,168` | `asteria` becomes `blank`. The edit keeps the dialog appearing. |
| `test_studio_dead_controls.py:234` | Step 1 becomes `blank` (untouched, +1). The Cancel and Accept steps that select `blank` must now select `rowdemo`, or they re-select the applied preset. |
| `test_studio_roles.py:2304-2307` | The first select becomes `blank`, the second `rowdemo`. Two `blank` selections make the second a no-op and the expected flow never arrives. |
| `test_studio_live.py:2407,2411` | Drop `asteria` from the loop and name map. Add the behaviour-1 assertion here: option values equal `['rowdemo', 'blank']`. |
| `test_studio_import_link.py:50` | Rewrite the docstring for the new fixture. |
| `test_studio_import_link.py:83-86` | `blank` equals the document, so the check would be vacuous. Keep default `rowdemo` (Fraunces) and make the composition change through the UI: select the Metadata slot and set its family to `jetbrains-mono`. Both assertions stay. |
| `test_studio_import_link.py:204` | Select `rowdemo`, not `blank`: `blank` would equal the imported state. |
| `test_studio_import_link.py:294,308` | `asteria` becomes `blank`; the later `rowdemo` stays. `assert_b_is_saved` still catches a leaked A through `assertNotIn('Inter')`. Report which assertions become weaker for A. |
| `test_studio_import_link.py:407,421` | `asteria` becomes `blank`. |
| `test_studio_import_link.py:436` | `asteria` becomes `blank`; the `'"Fraunces"'` assertion becomes `'"Inter"'`, and assert `before` was Fraunces. |
| `test_studio_import_link.py:521,533` | `asteria` becomes `blank`. If the select at 521 raises a confirm, that is existing behaviour; report it. |

Do not weaken a test. A test still proves the behaviour it names and would fail if that behaviour broke. The report lists
`import_link` 83-86, `dead_controls` 77-80, 110-114 and 234, and `roles` 2304-2307 as the sites that needed rebuilt state
or different evidence.

Add one parametrized test for behaviour 3. Cases: (a) a top-level text slot, (b) a slot nested in a row, (c) the
background with `source: "saved"`, (d) an image or rule slot, (e) a text slot with `colorSource: "custom"` and an old
`savedColor`, then the colour source switched to Saved in the inspector. Use at least two different old names, with the
new name and the hex typed into the test from the table above, not read from the page. Assert the rendered computed
colour (the slot's text colour, the canvas background), the inspector's Saved select value
(`#slotInspector [data-bind="savedColor"]`, `#canvasSavedColor`), and that the exported JSON holds the new name and no
`Asteria`. Add one further case for behaviour 4: a name not in the table (`Nonesuch`, and `constructor`) is exported
unchanged and renders as it does at BASE.

Show the test red before the change. Then show it failing on each of: the lookup removed from the background path only;
the lookup removed for row children; the lookup gated on `colorSource === "saved"`. Add assertions to an existing test
for behaviour 2 if one fits. Every new test method has a Given/When/Then docstring.

Focused run, with `PYTHONPATH=tests`: `test_studio_dead_controls test_studio_import_link test_studio_live
test_studio_roles test_support test_studio_controls test_font_kit_studio_v011 test_studio_review_findings
test_studio_first_run test_bridge_runtime`. Report any you could not run.

## Sweep (verbatim, sweeper at BASE: 46 live hits)

```
fontkit-studio.html: 1145 2118-2128 2197 2212 2258 2259 2260 2272 2284 2304
tests/fixtures/bridge/target.html: 25
tests/test_studio_dead_controls.py: 21 77 78 79 80 93 110 111 113 114 168 234
tests/test_studio_import_link.py: 50 83 204 294 308 407 421 436 521 533
tests/test_studio_live.py: 2407 2411
tests/test_studio_roles.py: 2304
```

No tracked file name contains the word. Afterwards, `git grep -i asteria -- fontkit-studio.html tests` returns only the
lookup's 11 names and the test data for behaviour 3.

## Done when

The behaviours hold, the focused run passes, and the report lists every test moved, any test that needed a built state,
and the result of the sweep above. The report also notes that a file exported after this change shows `#000000` for
saved-source colours in a 0.4.0 Studio, the accepted forward limit of the rename (O6).
