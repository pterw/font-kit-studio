### Spec Compliance
- PASS: Requirement 1. `FAMILIES` gains `[(v, False) for v in table.FAMILIES_REFUSED] + [(v, True) for v in table.FAMILIES_ACCEPTED]`, read by name from `tests/role_contract.py` (tests/test_r2_integration.py:239); `import role_contract as table` added before `from support import` (line 5). 19 refused + 10 accepted rows. Oracle is the table, not either side's output.
- PASS: Requirement 2. Docstring Then ("Apply is enabled exactly when the bridge accepts the value") equals the Apply-state assertion. The parity test also asserts the raw bridge reply type; the Then does not name it (brief review Minor 5: not to be widened). Not an issue.
- PASS: Owned files. Only `tests/test_r2_integration.py`; delta is 2 insertions, 1 deletion (3 gross lines, budget about 10).
- PASS: No existing test changed; no new test; no skip added.

### Checks run
- Drift (1): table rows vs existing rows -> read FAMILIES (lines 234-239) against role_contract.py:57-68 -> no table value duplicates an existing row (existing rows are var/env/attr/url/expression/!important/control chars/unbalanced quote/length; table rows are keywords, dashed functions, parentheses). Table self-consistency -> `family_refused()` from the table over both tuples -> every REFUSED value True, every ACCEPTED value False, so the labels match the independent oracle.
- Mutants (2), Chromium only, single test id, PYTHONDONTWRITEBYTECODE=1, on a scratch copy of the frozen tree (sha256 of the scratch files restored byte-exact, printed before = after every time; frozen worktree sha256 re-checked identical afterwards: studio b8aff99f..., bridge 3a0f96a9..., test 84e974ce...). Control (unmutated): Ran 1, OK.
  - Studio keyword check removed -> 8 failures: inherit, initial, unset, revert, revert-layer, INHERIT, Revert-Layer, '  inherit  '.
  - Bridge keyword check removed -> the same 8.
  - Studio parenthesis check removed -> 7 failures: --x(, --x(a), --x(), 'Inter, --x(', 'if(media(all): Inter', '"Inter", --x(a)', '--x("a")'.
  - Bridge `unquotedParenthesis` call removed -> the same 7.
  - Bridge keyword regex without `$` -> 4 failures: 'Initialism, serif', 'Inherit Sans', 'inherited', 'revert-layers' (only the accepted rows kill it).
  - Bridge paren scan ignoring quotes -> 5 failures: "'Inter (Display)'", '"Inter (Display)"', '"A)"', `"Inter's (x)"`, `'say "hi" (x)'`.
  - Studio paren scan ignoring quotes (my variant: `continue` on a quote char) -> 6 failures: the same 5 plus the pre-existing `'Unbalanced` row, because my variant also disables Studio's unbalanced-quote check. The implementer's 5 is the narrower variant; both are consistent.
- RED on BASE Studio (2) -> scratch copy with `git show HEAD:fontkit-studio.html` (HEAD = BASE 73b3ba2; its sha256 equals the BASE blob) and the W2B1 bridge -> FAILED (failures=15): the 8 keyword rows and the 7 dashed rows above, matching the brief review. The 4 table-only refused rows (generic(kai), Inter), a), serif, Inter (Display)) and the 10 accepted rows stay green on BASE, as the report and brief review state.
- Fake versus real (3) -> read the parity test (lines 500-521) and `self.start`/`self.raw` use -> the page is the real `fontkit-studio.html` driven by keystrokes (`type_value`) and the real `fontkit-bridge.js` answers the raw `design:roles-apply`; each mutant above was applied to the real source and killed, which would be impossible with a stand-in.
- Hidden skips (4) -> diff shows no skip/skipIf/expectedFailure; the test body is unchanged; the control run was OK with 0 skips.
- Lint -> `python -m ruff check tests/test_r2_integration.py` -> All checks passed.
- Scratch tree, script and temp files deleted; no browser or server left running by me (the test owns and closes its own).

### Strengths
- Rows are read from the contract table by name, so a table change reaches the parity test without a second edit.
- The accepted half is exercised: both over-refusal mutants (no `$` anchor, quote-blind scan) fail only the accepted rows, on both sides.
- Reported mutant results reproduced exactly (8 / 8 / 7 / 7 / 4 / 5) and the BASE RED count (15) matches the brief review.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. tests/test_r2_integration.py:239: the appended comprehensions make the closing line of `FAMILIES` about 140 columns and put table rows after the hand-written ones with no comment saying where they come from. Ruff passes (long lines are allowed in this repo). Cosmetic.
2. The report says the delta is "unstaged" in the worktree (status `MM`), and the brief wants `git diff --cached --check` after staging by name. The controller runs it at landing; `git diff --check` was not re-run by me (ruff only), and the delta is a single clean line.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** A minimal, table-driven change; every mutant the brief names (and the BASE-Studio RED) reproduces on the real Studio against the real bridge with the stated failing rows, and sources restore byte-exact. No hidden skips, no scope creep, within the line budget.
