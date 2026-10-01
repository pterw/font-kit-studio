# Font Kit Studio v0.1.1 Responsive Rows Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one-level responsive Row containers to Flow Composer.

**Architecture:** Extend the existing flat slot model with one bounded container type. Render rows as CSS grids and use one `ResizeObserver` on the composer canvas to switch each row between weighted columns and a vertical stack at its own breakpoint.

**Tech Stack:** Standalone HTML, CSS, vanilla JavaScript; Python/Node used only for verification.

**Spec:** `/mnt/data/docs/superpowers/specs/2026-09-17-font-kit-studio-v0.1.1-responsive-rows-design.md`

## Global Constraints
- Single self-contained HTML output.
- No runtime dependencies or npm packages.
- Row depth is exactly one level: row children cannot be rows.
- Rows contain 2–4 children.
- PNG/SVG only for image assets; no JPEG.
- Existing Library mode and v0.1.0 leaf slot behavior must remain available.

---

### Task 1: Row data model and recursive selection
**Files:** Modify `/mnt/data/font_kit_studio_v0.1.1.html`; Test `/mnt/data/tests/test_font_kit_studio_v011.py`

- [ ] Add failing structural tests for row type, row factory, recursive selection, and version.
- [ ] Run tests and confirm RED.
- [ ] Add `row` top-level type, leaf-only child type list, `makeRowSlot`, recursive selection/location helpers.
- [ ] Run tests and confirm GREEN.

### Task 2: Row rendering and responsive collapse
**Files:** Modify `/mnt/data/font_kit_studio_v0.1.1.html`; Test `/mnt/data/tests/test_font_kit_studio_v011.py`

- [ ] Add failing tests for `.row-layout`, collapse class behavior hooks, and `ResizeObserver`.
- [ ] Run tests and confirm RED.
- [ ] Render row children as weighted CSS grid columns; add `syncRowLayouts()` and canvas resize observer.
- [ ] Run tests and confirm GREEN.

### Task 3: Row and child inspector behavior
**Files:** Modify `/mnt/data/font_kit_studio_v0.1.1.html`; Test `/mnt/data/tests/test_font_kit_studio_v011.py`

- [ ] Add failing tests for row child-count, gap, align-items, collapse breakpoint, and ratio controls.
- [ ] Run tests and confirm RED.
- [ ] Add row inspector and preserve existing leaf inspector for nested children; prevent row nesting.
- [ ] Run tests and confirm GREEN.

### Task 4: Persistence/export compatibility
**Files:** Modify `/mnt/data/font_kit_studio_v0.1.1.html`; Test `/mnt/data/tests/test_font_kit_studio_v011.py`

- [ ] Add failing tests for recursive asset stripping, row import hydration, and nested CSS token traversal.
- [ ] Run tests and confirm RED.
- [ ] Update JSON version/import/export and CSS token traversal for rows.
- [ ] Run tests and confirm GREEN.

### Task 5: Final verification
**Files:** `/mnt/data/font_kit_studio_v0.1.1.html`

- [ ] Run the full structural regression suite.
- [ ] Extract inline JavaScript and run `node --check`.
- [ ] Parse HTML IDs and confirm no duplicate IDs.
- [ ] Compute SHA-256.
