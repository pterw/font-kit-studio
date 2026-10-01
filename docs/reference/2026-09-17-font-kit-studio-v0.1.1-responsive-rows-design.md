# Font Kit Studio v0.1.1 Responsive Rows — Design

## Goal
Add responsive one-level Row containers to Flow Composer so assets and typography can sit side-by-side without introducing free-positioned artboard behavior.

## Scope
- Keep the app a single self-contained HTML/CSS/JS file with no runtime dependencies.
- Add `row` as a top-level slot type.
- A row contains 2–4 child slots; children may be Text, Image, Rule, or Spacer only.
- Rows may not contain rows.
- Row controls: child count, per-child numeric column weight, gap in px, align-items (`start`, `center`, `end`, `stretch`), and collapse breakpoint in px.
- Collapse is based on the actual rendered composer canvas width, not only the selected nominal width. A `ResizeObserver` updates row layout when the canvas changes size.
- When collapsed, children stack vertically in source order and each child uses one column.
- Child slots remain individually selectable and editable with the existing inspector controls.
- Existing top-level slot move controls remain. Row children do not gain drag/free-position behavior in this version.
- Existing PNG/SVG image support remains unchanged. JPEG remains unsupported.
- JSON import/export supports nested row children and strips session-local asset data recursively.
- CSS token export traverses row children so nested text roles are not lost.

## Data model
A row slot has:

```js
{
  id,
  type: "row",
  role: "Row",
  childCount: 2,
  gap: 24,
  alignItems: "center",
  collapseAt: 680,
  ratios: [1, 2],
  children: [leafSlot, leafSlot]
}
```

Children are the same leaf slot objects already used at top level. Selection remains ID-based and resolves recursively through one row level.

## Rendering
Rows render as `.row-layout` CSS grids. Normal mode sets `grid-template-columns` from the ratio weights. Collapsed mode applies `.is-collapsed` and uses `1fr`. A single canvas `ResizeObserver` calls `syncRowLayouts()` after render and whenever the canvas width changes.

## Inspector
Selecting a row exposes row controls plus a compact child summary. Selecting a child exposes the normal leaf inspector, with a breadcrumb indicating its row/child position. The slot-type dropdown for children excludes `Row`.

## Non-goals
- Arbitrary/deep nesting.
- Drag/drop or free positioning.
- Artboard mode.
- Editable inline SVG.
- Font binary parsing/fontkit.
