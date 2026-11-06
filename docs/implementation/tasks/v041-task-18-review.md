### Spec Compliance
- PASS: Tailwind bullet (README.md:598) matches the bridge. Fixed names list and the `token-not-applied` text are verbatim from fontkit-bridge.js:2397-2425; the extra triggers (pseudo-element, shadow root, script, equal value) follow from `computedFontFamilies` (bridge:3048), which compares light-DOM element computed font-family only.
- PASS: `design:warning` row (README.md:723) lists the four kinds; `postWarning` kinds list at bridge:2279 and the call sites at 3467 (auto-id only: `!record.stable`) and 3486 (`reapplyFrom`) agree with the clauses. Review fix 1 is honoured: only `edit-not-reapplied` says auto-id. "A Studio that does not know a kind ignores it" is true: `noteWarning` returns on `!WARNING_KINDS.includes` (fontkit-studio.html:6417). `protocolVersion` stays 1.
- PASS: error-page bullet (README.md:665) matches `isTaggable` (proxy.js:217-228, statusCode 200 is one of four conditions; "only ... status 200" states a necessary condition, true) and the Studio hint at fontkit-studio.html:4829.
- PASS: Clear row (README.md:68 of patch) says a stale `pageVersion` is not a reason to refuse it, no "only" (Review fix 4). `handleRoleMutation` bridge:1555-1556 checks `documentId` for both operations and `pageVersion` for apply only. grep `page-changed` over README: lines 233, 265, 338, 339, 718 do not say Clear is refused for it.
- PASS: Tested-on paragraph (README.md:885): link target exists; audit scope says Chromium 151 only, Next.js 16, Flask/Jinja2/Tailwind 4/DaisyUI, shadcn. No app names, no support claim.
- PASS: Next.js paragraph (README.md:523) says "seen once", no D-number; matches audit D1-10a (line 114) and its note at line 245.
- PASS: `stat` sentence (README.md:598 area, Marking up) does not list `stat-title`; bridge:120 uses `.stat`; the rule text is correct.
- PASS: Known limits bullet for a page that never stops changing (README.md:339) agrees with `handleRoleMutation` and audit D2-10.
- PASS: Known gaps: state-class move (matches 7437509 body and `planStructureReplay` -> `failReapply` before anything is sent, studio 5476-5483), B08/D2-11 (audit rows B08-b, D2-11-b, "later"), B09 (audit row 116, "later").
- PASS: CHANGELOG. I mapped every non-docs, non-refactor commit in v0.4.0..HEAD to a line in [Unreleased]: bb3c596, 60a06c6, 63c32b4, a3050d3, f620df0, 7cb1f9e, 479eda8, 2f0cff2, 58a70ed, 6233ff4, b50d601, 1548029, 961abc5, eb5cf8f, eec106b, 84df677, 7437509, 9f63282, 0c54bdd, 9323eb7, f56256a, 39e5b41 each have one line; 76912e0 sits under Changed. None missing, none duplicated. The a3050d3 line gives the code's reason ("repair the markup differently", Review fix 2) and its element list matches BLOCK_ELEMENTS (bridge:94-96). Added lines are under `### Fixed`.
- PASS: no process state in added README/CHANGELOG lines (no task, wave, D-number, "0.4.2", "later"). "Version 0.4.0" and "saved by 0.4.0" are product facts.
- PASS: scope. `git diff --stat` shows README.md and CHANGELOG.md only (21 insertions, 4 deletions); `git diff --check` clean; every line in both files ends CRLF (915/915 and 388/388); no code fence edited, so test_live_integration needs no run.

### Checks run
- Added README/CHANGELOG claims vs code -> read bridge 94-120, 1546-1580, 2262-2300, 2385-2430, 3040-3050, 3405-3495; studio 4829, 5470-5610, 6415-6445; proxy.js 217-228 -> all agree (see above).
- Audit record claims -> read scope lines 1-6, 36-62 and rows D1-10a, D2-10, B09, B08-b, D2-11-b -> agree.
- Coverage of [Unreleased] -> `git log --oneline v0.4.0..HEAD` filtered, matched one by one to CHANGELOG lines -> complete.
- Internal link -> `test -f docs/implementation/audit-2026-11-06-real-apps.md` -> exists.
- `PYTHONPATH=tests python -m unittest test_release` (once) -> Ran 26, OK.
- No browser test run.

### Strengths
- Every behavioural sentence has a code line behind it; the weaker claims are scoped ("seen once", "may read other names").
- The Tailwind advice no longer promises that token routing works.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- README.md:339 (patch line 28) and CHANGELOG "Clear preview now always removes the preview": "always" is true for a changed page but Clear is still refused for a different `documentId`, `invalid-message` or `revision-conflict`. The row at README:703 is worded correctly; the bullet is read in the context of a same-document timer, so it is not false there. Not a follow-up.
- README.md Known gaps, third bullet: "A paragraph's Reset is fixed." tells a reader of the README about a repair rather than a state; "A paragraph's Reset shows the app's current text." would read as a behaviour. Not false.
- CHANGELOG: the 84df677 line ("three more kinds of warning") comes after the three lines that already name those warnings, so it reads as a repeat. Placement was set by the brief.

### Plan-mandated (for the owner)
- None.

### Source conflicts (for the controller)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** Every added README and CHANGELOG sentence checks out against the code at BASE, the [Unreleased] list covers every user-visible landed commit once, and there is no app name, process state or support claim beyond the audited stacks and Chromium.
