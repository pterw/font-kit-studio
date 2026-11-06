### Spec Compliance
- PASS: S01. `elementHasChanges` also checks `live.structure` ids (S01 patch, fontkit-studio.html ~7205). Inside the owned region. Test asserts the saved move and banner survive the reload first, then enabled state, `title` and the `[data-hint-for]` hint (Review fix 3). Guard test with nothing saved keeps Reset disabled with the reason.
- PASS: S02. Swatch handler appends the alpha byte of `cssColorToHex(liveValues(target.id).color)` when it is `#rrggbbaa` (~6101-6107). `liveValues` includes pending patches, so a second swatch move keeps the last sent alpha. Text box mirrors the sent value (Review fix 2). Typed text box path untouched. Limit (hsla -> "" -> no alpha) is stated in the report.
- PASS: S03. `liveSeed` returns "" for non-finite line height (5927); markup has `placeholder="normal"` (6050, verbatim New string 13). `setLiveControl` unchanged. Nothing queued on select (export overrides asserted empty). Set values (24px/16px -> 1.5) still shown. Only the line-5927 and line-6050 edits touch the file; Task 7's 6046 line is not touched.
- PASS: Seeding follows Review fix 1 (inline style on hero.lead + `fake.select`), each test asserts the seed arrived first. `test_studio_live.py` unchanged. Source is 12 changed lines, tests about 135 lines, inside budget.
- PASS: Patches. Applied S01, S02, S03 in order with `git apply --check` + `git apply` onto a `git archive 5443ff6` export in a scratch directory (no stray files; patches carry only fontkit-studio.html and tests/test_studio_readouts.py). Commit subjects match the brief and carry no process state. Patch 1 creates the module; 2 and 3 append.
- CANNOT VERIFY FROM DIFF: the commit body/trailer (patches are bare diffs).

### Checks run
- Byte difference of the test module -> compared the worktree file with the export after the three patches. The HTML is identical (`cmp`). The test module differs only in line endings: `tr -d '\r'` of both gives identical content; the applied copy is CRLF (core.autocrlf=true, and `tests/test_studio_live.py` is CRLF too), the worktree copy is LF. The patches themselves contain no CR. Confirmed benign.
- Focused module -> `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_studio_readouts -v` in the task's worktree -> 7 tests OK.
- One break per row, on a scratch export (patched HTML edited there; tests ran from that directory, so the mutated HTML is what loaded) -> S01 revert of the `live.structure` clause: KILLED (saved-move test fails). S02 `sent = event.target.value` (no alpha): KILLED (translucent swatch test). S03 `? 1.2` restored: KILLED (empty-field assertion).
- Further mutants -> S01 always-true: KILLED by the disabled guard. S02 typed-box gets alpha: KILLED. S03 default 0, placeholder removed, px division broken: all KILLED.
- MISSED: S01 `live.structure.length > 0` (any saved move enables Reset for any element). No test selects an element outside every saved entry after a reload. See Minor.
- MISSED (equivalent): S02 text box not mirrored in the handler. The acknowledgement redraw writes the value back, so the mirror line is redundant at runtime and the assertion after `wait_live` cannot distinguish it. Not a defect.
- Regressions -> not rerun (implementer ran test_studio_live, roles, role_routes, r2_integration, all OK per report; the edits are three narrow lines). Left for the wave gate.
- Boundaries -> no bridge change, no new postMessage, no innerHTML added (markup edit is one static attribute). No rule 5 crossing.

### Strengths
- Each RED test asserts its seed precondition first, so a lost move or an unseeded colour cannot pass for a fix.
- Alpha is read from `liveValues` (seed, acknowledged or pending), not from the picker, as the brief requires.

### Issues
#### Critical
- None.
#### Important
- None.
#### Minor
- tests/test_studio_readouts.py (S01 guard): after a reload with a saved move, no check that an element outside every saved entry (e.g. a different, unmoved container's element) still shows Reset disabled. A mutant that enables Reset whenever any `live.structure` entry exists passes all tests. Cheap to add, no verdict depends on it.

### Plan-mandated (for the owner)
- None.

### Source conflicts (for the controller)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** All three requirements and the review fixes are met inside the owned regions, the patches apply in order at BASE and reproduce the worktree (HTML byte-identical, test module equal modulo CRLF), and each row's named break fails its test. One minor guard gap only.
