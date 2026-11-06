### Spec Compliance
- PASS: S09 source change. `compositionPatch` takes `state.slots.find(slot => slot.type === "text")` and sends nothing when none; loop and sans/serif/mono fallbacks untouched (S09 patch, fontkit-studio.html hunk at 6849-6853).
- PASS: G2-6. `cssStack` is now `"${f.css || f.family}", ${f.fallback}`; the aliases read is gone. Byte-identical dump is claimed in the report (scratch/t7-dump-*.txt); not re-run by me. No new test, as the brief says.
- PASS: G2-19. Local renamed to `familyChoices` at its declaration and its single template use; function at the old 2536 untouched.
- PASS: owned regions only. The three patches touch only cssStack, the inspector local and use, the one fallback line, and the new test module. No CHANGELOG edit.
- PASS: Review fix 1 (first/last updates). The test reads `composition_updates(frame)` and compares `tokens[0]` (sync1, the control) with `tokens[-1]` (sync2, after the two moves). Sequence is sync1, auto, auto, sync2.
- PASS: Review fix 2 (own count). `wait_updates` polls `len(self.updates(frame))` and `assertEqual`s the count (1, 3, 4) before reading. It does not use `self.sync`.
- PASS: Review fix 3. Uses `#slotInspector [data-bind="family"]`, after `#viewSpecimenCanvas` and selecting the first flow slot.
- FAIL (Important): Review fix 1 also says "Assert both equal each other **and the chosen family's stack**". The test asserts only `tokens[-1] == tokens[0]` and `tokens[0] != FRAUNCES`. The chosen stack is never asserted. See Issues.
- Minor deviation: the brief names the Row's Up button "twice"; the test uses `button[title="Move up"]` inside `.flow-slot:has(.row-layout)`, which matches. OK.

### Checks run
- Patches apply in order at BASE -> temporary GIT_INDEX_FILE, `git read-tree 5443ff6`, then `git apply --cached --check` and apply for S09, G2-6, G2-19 -> all three ok; resulting tree equals the worktree modulo CR (checkout CRLF). Worktree untouched. The new test file is in the S09 patch only; no stray file.
- Patch subject -> the patches are plain `git diff` output with no subject line; subjects exist only in the brief/report. CANNOT VERIFY FROM DIFF that the commit subjects are as listed (the three in the report match the brief and are under 72 characters).
- Focused test -> `cd the task's worktree && PYTHONPATH=tests FKS_ENGINES=chromium timeout 300 python -m unittest test_studio_sync_reads -v` -> 1 test OK.
- S09 break reproduced -> scratch copy at scratch/t7-review (tests + html copied; REPO resolves to the copy), fontkit-studio.html line 6851 set back to `state.slots[0]` (confirmed by grep) -> the test FAILS: `- "Fraunces", serif` / `+ "JetBrains Mono", monospace`. So the test loads the page it is run against and goes RED on the named break.
- Other way to break it -> same scratch, fallback changed to the LAST text slot (`.filter(type==="text").pop()`, confirmed by grep at 6851) -> the test PASSES (MISSED). Any "wrong text slot" (last, second) that is stable across the move goes undetected, because only "equal to control" and "not Fraunces" are asserted.
- Precondition -> `wait_updates` asserts the total update count; it counts all `design:update` messages, not only composition ones. The test does not assert `len(composition_updates) == 4`. In this fake target no targetId updates occur here, so it holds; Minor.
- Regressions -> relied on the report (roles 114, role_routes 52, r2_integration 29, controls 34, live classes 44 all OK); not repeated per instructions. The cssStack change is output-identical; the rename is local. Nothing left for the wave gate beyond the full suite.
- Boundaries -> no bridge change, no new text sink (all strings are existing template literals; no innerHTML added).

### Strengths
- The test sets a non-Fraunces family first, so the keep-Fraunces break is genuinely RED; verified.
- Own-count wait removes the `self.sync` early-return trap.

### Issues
#### Critical
None.
#### Important
- tests/test_studio_sync_reads.py:41-42 -- the test never asserts the synced token equals the chosen family's stack (Review fix 1, binding). Mutation "last text slot instead of first" passes. Fix: add `self.assertEqual(tokens[0], '"JetBrains Mono", monospace')` (or the stack read from the page's font library) and keep the Fraunces inequality.
#### Minor
- tests/test_studio_sync_reads.py:19-23 -- the count wait covers all updates; also assert `len(self.composition_updates(frame)) == 4` so `tokens[0]`/`tokens[-1]` are known to be sync1/sync2 rather than any pair.
- Patches carry no commit subject; the controller must supply the three subjects when committing.
- CHANGELOG (see answer below).

### CHANGELOG question
No line is needed for G2-6 and G2-19 (no behaviour change). For S09 "no line" is not quite right: the Sync output changes for any user whose first slot is a Row or Image and whose first text family is not the library's first font. `code-dispatch.md:15` asks the Handoff to carry "the CHANGELOG line", and CHANGELOG.md [Unreleased] lists user-visible changes. The implementer correctly may not edit CHANGELOG.md and gave the substance in the Handoff, but did not draft a line. The controller should add under [Unreleased] a Fixed entry, for example: "Sync to Live App takes `--font-display` from the first text slot, not the first slot, so a Row or Image placed first no longer makes it the first library font." This is a controller decision, not a finding against the implementer (the brief said "no line").

### Plan-mandated (for the owner)
- [Minor] Brief says "CHANGELOG.md: no line" for a user-visible Sync-token fix -- brief requires: "`CHANGELOG.md`: no line (S09 changes a token only when ...; the controller writes ledger lines)". Conflicts with dispatch Handoff wording; see above.

### Source conflicts (for the controller)
- task-7-brief.md: "`CHANGELOG.md`: no line ... State this in the report." vs code-dispatch.md:15: "a Handoff with the CHANGELOG line" -- the implementer followed the brief and gave the substance only. The controller decides whether S09 gets an [Unreleased] line.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** The source changes are correct and the S09 test goes RED on the named break, but it omits the binding assertion that the token equals the chosen family's stack, so a wrong-slot fallback (last text slot) passes undetected.
