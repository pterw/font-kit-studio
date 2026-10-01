### Task 2: Row rendering and responsive collapse
**Files:** Modify `font_kit_studio_v0.1.1.html`; Test `tests/test_font_kit_studio_v011.py`

- [ ] Add failing tests for `.row-layout`, collapse class behavior hooks, and `ResizeObserver`.
- [ ] Run tests and confirm RED.
- [ ] Render row children as weighted CSS grid columns; add `syncRowLayouts()` and canvas resize observer.
- [ ] Run tests and confirm GREEN.


## Reconciled execution requirements

Characterize inherited row grid behavior with rendered browser geometry at breakpoint -1, exact breakpoint, +1 and at actual canvas widths smaller than nominal selection. Test observer updates after canvas/container resize, source order, 2-4 children, weighted columns and gaps. Fix confirmed defect: .row-child height:100% causes alignment start/center/end/stretch to be visually inert with unequal-height children. Add a real failing geometry regression before fix. Preserve current design and collapsed single-column behavior; no unrelated CSS redesign. Browser acceptance must include Chromium and Firefox (both installed), use isolated contexts. Extend existing regression suite/helper conventions. Own only HTML and tests. Full scoped suite once before commit. No runtime dependencies.

## Report and ownership

Read AGENTS.md. Do not edit plans or ledgers: controller owns those. Write full report to docs/implementation/tasks/task-2-report.md including exact commands, relevant RED/GREEN output, files/commits, self-review and limitations. Do not spawn subagents. You are not alone in the repository: do not revert others; work only in assigned files.
