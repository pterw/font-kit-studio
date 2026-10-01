### Task 4: Persistence/export compatibility
**Files:** Modify `font_kit_studio_v0.1.1.html`; Test `tests/test_font_kit_studio_v011.py`

- [ ] Add failing tests for recursive asset stripping, row import hydration, and nested CSS token traversal.
- [ ] Run tests and confirm RED.
- [ ] Update JSON version/import/export and CSS token traversal for rows.
- [ ] Run tests and confirm GREEN.


## Reconciled execution requirements

Verify JSON round trip for rows and older v0.1.0 leaf compositions, recursive session asset stripping, malformed nested row inputs, PNG/SVG upload and JPEG rejection, text roles in row children for CSS export. Confirmed baseline bugs: failed imports partially mutate background/width before hydration fails; numeric roles accepted then crash CSS export; role slugs Body, Body, Body-2 collide. Normalize validated shape/known structural fields before committing import state; malformed import must leave prior composition unchanged and report actionable failure. Do not retain hidden descendants on leaf slots. Preserve normal metadata and leaf controls, arbitrary harmless extras only if consistent with privacy. Add failing real behavior tests before each fix, ensure recursive stripped assets including nested raw structures. Boundary needs robust rejection/normalization of invalid role and malformed slots/children without JSON/CSS crash. Reuse Task 1 normalizer. Image file async processing must not corrupt a changed selection; test a concrete race if source warrants it. No runtime dependencies; own HTML and tests.

## Report and ownership

Read AGENTS.md. Do not edit plans or ledgers: controller owns those. Write full report to docs/implementation/tasks/task-4-report.md including exact commands, relevant RED/GREEN output, files/commits, self-review and limitations. Do not spawn subagents. You are not alone in the repository: do not revert others; work only in assigned files.
