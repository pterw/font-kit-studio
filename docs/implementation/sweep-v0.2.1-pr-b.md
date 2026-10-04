# Sweep: v0.2.1 PR B release point (2026-10-04)

Read-only consistency pass over PR #5 at `72d2a34` (20 commits, 67 files, 7,594 changed
lines against `ffcab4f`; the bridge is unchanged). Static checks, bridge syntax and the
commit-message check pass; 786 tests are collected.

## Fixed in the release-point commit

- Stale status: the ledger's "Current state" and evidence line, the product direction's
  "Where it stands", the roadmap's PR B cell and log, R1's status (`next`), and the PR B
  execution plan's status, ledger and definition of done.
- The PR B goal "suite time roughly halved" is recorded as not met: per-test time fell
  about 25 percent (740.9 s for 623 tests before, 655.7 s for 786 after).
- CHANGELOG: compare links point at commit a6d2751, because v0.2.0 is untagged (D039);
  release-state and pull-request wording removed; missing user-visible changes added
  (disabled view and colour controls, the Sync to Live App reason line and focus hand-off,
  the dropped-queued-edits status, the Adobe kit label, and PR A's 421 page, busy-port
  refusal and first-run messages); width order matches the bar; the entry is dated.
- Version labels: D009a marked as superseded by D039; the plan's Task 9 and out-of-scope
  lines point at D039 and D041; the plan's test-module ownership lines point at the PR B
  execution plan.
- README: the Firefox canary (not suite) in CI; the test-file table rows for
  `test_support.py` and the gate modules; `design:hello` carries the session id it
  proposes (also global rule 5); `[::1]` is accepted; the 390 px no-bridge badge listed
  under known gaps.
- AGENTS.md: which tests share the browser; `ci` as a commit type and `ci` and `demo` as
  scopes; "the demo app".
- Decisions and plans: D040's plain-name rule applies from R1, and R1.8 owns the copy;
  D044 says v0.2.1 is both pull requests. The extension roadmap's opening, panel row and
  open question 5 follow D047. The design spec's status line and its build-order table.

## Left for later (recorded, not fixed)

- Dead code from this pull request: `.c-field.span-4` and `.c-field.span-6` with their
  media-query entries; unused imports and names in `test_studio_dead_controls.py` and
  `test_studio_visual.py`; ids `deviceViewportBar` and `previewScroller` used by nothing.
  Removing them touches code and needs the full gates; first maintenance pass after merge.
- The bridge's pop-out badge still shows an emoji; the bridge is outside PR B.
- The legacy composition update accepts undocumented shortcut keys (`sans`, `serif`, `mono`,
  `display`, `layout.order`); Studio sends none.
- At 390 px the "No bridge answered" badge scrolls the page sideways (advisory, D029).
- Showing the Composer does not re-sync row layouts, so rows are collapsed for one frame.
- Decision rows and older plan text keep the labels of their day ("Live Target inspector",
  "Accept target state", "Target URL"); they are dated records.
