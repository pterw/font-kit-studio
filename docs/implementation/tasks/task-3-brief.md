### Task 3: Row and child inspector behavior
**Files:** Modify `font_kit_studio_v0.1.1.html`; Test `tests/test_font_kit_studio_v011.py`

- [ ] Add failing tests for row child-count, gap, align-items, collapse breakpoint, and ratio controls.
- [ ] Run tests and confirm RED.
- [ ] Add row inspector and preserve existing leaf inspector for nested children; prevent row nesting.
- [ ] Run tests and confirm GREEN.


## Reconciled execution requirements

Verify inherited row controls and normal leaf inspector via browser interaction: integer 2-4 child count, bounds, gap, start/center/end/stretch, breakpoint, numeric weights; child summary jumps, breadcrumb, child type chooser excluding row; text/image/rule/spacer edits and top-level move controls, no child movers. Model normalization may already exist after Task 1; test UI normalization including empty/fractional inputs, preserve usable inspector after changes. Reproduce any concrete defect before fixing. Accessibility of newly modified row controls should include associated labels where practical without redesigning entire app. Stay within row interaction scope. Own only HTML and tests; no external files or production globals.

## Report and ownership

Read AGENTS.md. Do not edit plans or ledgers: controller owns those. Write full report to docs/implementation/tasks/task-3-report.md including exact commands, relevant RED/GREEN output, files/commits, self-review and limitations. Do not spawn subagents. You are not alone in the repository: do not revert others; work only in assigned files.
