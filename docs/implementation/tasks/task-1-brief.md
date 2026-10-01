### Task 1: Row data model and recursive selection
**Files:** Modify `font_kit_studio_v0.1.1.html`; Test `tests/test_font_kit_studio_v011.py`

- [ ] Add failing structural tests for row type, row factory, recursive selection, and version.
- [ ] Run tests and confirm RED.
- [ ] Add `row` top-level type, leaf-only child type list, `makeRowSlot`, recursive selection/location helpers.
- [ ] Run tests and confirm GREEN.


## Reconciled execution requirements

The HTML already implements rows. Characterize the row factory, one-level ID selection and valid preset/import behavior. Correct title/version inconsistencies. Fix row numeric invariants demonstrated by malformed childCount (fractional values throw invalid array length), nonfinite values and raw spread overriding normalized gap/alignment/breakpoint. Keep normalization small and shared across factory/hydration/inspector as needed; Task 3 may add more inspector interaction checks. Enforce leaf-only children even for malformed nested row imports without retaining hidden descendants; this prevents session data leaks, with detailed export tests in Task 4. Preserve all ordinary text/image/rule/spacer fields. Add meaningful Python unittest regression tests using installed Playwright against real browser UI and JSON import/export; dev-only browser dependency is allowed, no app dependencies. Version/ID/syntax structural checks are also useful. Genuine failing cases require RED then GREEN; inherited correct behavior may pass initially. Never remove implemented features to force RED. Exports are the observable state, no production testing globals required. Ensure browser page errors are captured. HTML/test writer exclusively owns implementation during this task.

## Report and ownership

Read AGENTS.md. Do not edit plans or ledgers: controller owns those. Write full report to docs/implementation/tasks/task-1-report.md including exact commands, relevant RED/GREEN output, files/commits, self-review and limitations. Do not spawn subagents. You are not alone in the repository: do not revert others; work only in assigned files.
