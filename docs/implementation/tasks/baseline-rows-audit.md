# Baseline row audit

Scope: original Downloads HTML, row factory/hydration, selection, rendering/collapse, row/child inspector. Read-only application audit. Graph tools unavailable per parent transport failures; generation unknown, no graph completeness claims. Direct source plus Chromium isolated context used. No application or Git edits.

## Confirmed bugs

1. **Row alignment controls do not visibly align unequal-height children.** `.row-child` has `height:100%` (HTML 518–521), forcing every wrapper to the track height while leaf contents remain at its top. `syncRowLayouts` changes `align-items` (2026), but wrappers cannot move. Reproduction: Composer → Editorial Image + Body Row → Apply preset → select row → select start, center, end, stretch. At viewport 1800×1200, actual canvas 960px, after 300ms settling each mode produced identical child top 900.359375 and wrapper height 99.03125; image placeholder height 74.1875 and text height 79.03125 both started at 910.359375. Thus center/end are effectively inert. Remove forced full height or implement alignment of inner contents deliberately.

2. **Fractional child count throws and partially mutates state.** Inspector numeric input has step=1 but JS does not round (2233–2237). Fill Children with `2.5` and dispatch change: browser pageerror `Failed to set the 'length' property on 'Array': Invalid array length`. Loop first pushes a third child, then assigning `row.children.length=2.5` throws before render/ratios synchronization. DOM remains two children while internal array is three. The same fractional imported `childCount` reaches array-length assignments in `hydrateSlot` (1775–1776), so malformed JSON also fails. Normalize to a finite integer before modifying arrays.

3. **Factory sanitization is overridden by raw values.** `makeRowSlot` initially validates type/role/gap/alignment/breakpoint (1621–1626), then `...overrides` (1629) overwrites those validated values. Only childCount/ratios/children are reasserted afterward. In hydration, arbitrary imported gap, collapseAt and alignItems survive into model/inspector/export. Runtime alignment and gap rendering have fallback handling, but breakpoint rendering accepts raw negative/nonnumeric values; invalid breakpoint can prevent expected collapse and disagrees with number-input minimum 240. This is directly established by spread order, not browser-import reproduction. Treat as confirmed source defect with runtime import behavior still to verify.

## Pre-existing requirements implemented

- Top-level row type and leaf-only child type chooser: 1547–1550, 2149–2153.
- Default row model, two-to-four child padding/truncation, ratio minimum: 1608–1634 (integer malformed-input caveat above).
- Hydration reconstructs rows and leaf children with fresh IDs, converts nested row requests into text leaves: 1768–1785. No arbitrary nesting is rendered.
- One-level ID lookup and parent-aware replacement: 2055–2085.
- Child canvas click stops propagation, selects child; row background selects row: 1966–1989.
- Child normal leaf inspector, row/child breadcrumb, row excluded from child type list: 2142–2157.
- Row inspector has child count, gap, alignment, breakpoint, per-child weights and child jump buttons: 2160–2167, 2228–2277.
- Top-level move buttons retained; row children receive no move controls: 1981–2012.
- Grid ratios, gap, breakpoint, source-order collapsed stacking: 507–516, 2004–2026.
- Collapse uses actual `getBoundingClientRect().width`, not nominal selected width, and single canvas ResizeObserver plus window resize fallback: 2016–2026, 2049–2053. Source verified; boundary resize acceptance left to parent browser suite.

No exhaustive UI/accessibility claim. Export and assets intentionally outside assigned audit scope; only factory model invalidity implicates their values.
