# Task 18 brief: README and CHANGELOG state what 0.4.1 shipped

Plan Task 18, wave 4, docs only. Drafted against `f56256a`; the worktree is `the task's worktree`, cut from the head that contains Task 17's
commit (see Order). Audit rows: none of its own (it documents the rows the other tasks fixed). Line budget: about 45 gross lines in
`README.md`, about 14 in `CHANGELOG.md` (Markdown is reported apart, D065). Single commit, single patch.

## Order and the one fact to check first

Task 17 is treated as landed (D080). At `f56256a` it is not: `git log --oneline` there has no `fix(bridge): never refuse Clear because
the page changed`. Before editing, run `git log --oneline -40` in `the task's worktree`. If that subject is absent, stop and return NEEDS_CONTEXT:
two Requirements below (4 and 8) state behaviour only that commit ships.

## Why

The README still says things the 0.4.1 commits made untrue or incomplete, and it lacks the limits those commits leave:

- `README.md:595` tells users to route fonts through `--font-display`; Sync writes only the fixed names `--font-display`, `--font-sans`,
  `--font-serif`, `--font-mono` (`fontkit-bridge.js:2397`, `writeToken`), and a page that reads other names changes nothing. The bridge now
  posts a `token-not-applied` warning in that case (`fontkit-bridge.js:2421-2425`).
- `README.md:719` says `design:warning` carries only `runtime-error`. `postWarning` (`fontkit-bridge.js:2276`) now sends three more kinds
  (D079; `deviations.md`).
- `README.md:653-661` ("If Studio does not connect") never mentions error pages. Studio's hint now does (`fontkit-studio.html:4829`); the
  proxy tags a page only when the app answers `200` with `text/html` and identity encoding (`packages/fontkitstudio/src/proxy.js:217-228`).
- `README.md:701` says nothing of what Clear checks; after Task 17 it checks `documentId` and not `pageVersion` (D080).
- `CHANGELOG.md` (Unreleased) is missing lines (see Requirement 9).

## Owned files (exact)

- `README.md`: `### Next.js` (511-543, one new paragraph after line 521), `#### Known limits` of Detected roles (329-339, one new bullet),
  `### Tailwind` (590-595), `### If Studio does not connect` (653-661, one bullet), the `design:roles-clear` row (701), the `design:warning`
  row (719), and `**Firefox status.**` plus `Known gaps:` (881-889: one new paragraph before 881, and the Reapply bullet at 885).
  Everything else is read-only. Line numbers are at `f56256a`; re-find each by its text.
- `CHANGELOG.md`: the `[Unreleased]` block only (lines 13-60 at `f56256a`). Do not date it or touch any other heading; Task 19 does.
- Read-only, no edit: `packages/fontkitstudio/README.md` (checked: it repeats none of these claims; `git grep -n -i "font-display\|404\|warning\|page-changed"`
  on it returns nothing), `docs/`, all code and tests.

## Read first

`README.md` 201-209, 252-266, 317-339, 590-600, 653-661, 699-702, 717-719, 876-889; `CHANGELOG.md` 1-60; `docs/implementation/audit-2026-11-06-real-apps.md`
rows `D1-10a` (line 114), `B09` (116), `B08` and `B08-b` (102-103), `D2-11-b` (106); the format of the existing Known limits bullets.

## Requirements

Each states shipped behaviour only, names stacks never apps, and carries no process state (no task, wave or version-to-come wording; do not
write "0.4.2" or "later" in the README). Oracle for a claim is the code line cited, read at the worktree head.

1. **Tailwind (595).** Replace the advice. It says: Sync writes the fixed names `--font-display`, `--font-sans`, `--font-serif` and
   `--font-mono`, and the page may read other names; if Sync wrote those tokens and no element on the page changed, the bridge warns and
   Studio shows the note (`Sync wrote {names}, but no element on the page changed. This page may read other token names.`). So route
   through semantic tokens only where the app reads those four names; otherwise use the Copy or Sync CSS rule. It may also warn when the
   token is read only in a pseudo-element, a shadow root or script, or when the written value equals the page's own (Task 11 accepted
   limit). Check: `fontkit-bridge.js:2421-2425` for the text and trigger.
2. **Warning kinds (719).** The row lists `runtime-error` and `token-not-applied`, `edit-not-reapplied`, `edit-reapply-stopped`, each with
   one clause: Sync wrote font tokens and no element changed; the page replaced an element whose edit could not be re-applied; the page
   keeps re-creating an element so its edits stop being re-applied (the last two apply to auto-id targets: `fontkit-bridge.js:3463-3485`).
   Add: the kinds are additive, `protocolVersion` stays 1, and a Studio that does not know a kind ignores it. Check: `postWarning` and
   Studio `noteWarning` (`fontkit-studio.html:6415`) at the worktree head.
3. **Error pages (653-661).** One bullet: **A 404 or 400 page.** In proxy mode the bridge is added only to an HTML page the app answers
   with status 200, so an error page has none; go back to a normal page. Oracle: `proxy.js` `isTaggable` (statusCode 200).
4. **Clear (701).** Append to the `design:roles-clear` row: it is not refused for a changed `pageVersion`, only for a different
   `documentId`. Do not change the `design:roles-apply` row. Check: `handleRoleMutation` in the bridge at the worktree head, and
   `grep -n "page-changed"` over the README to confirm no other sentence says Clear can be refused for it (fix any that does).
5. **Tested on.** One short paragraph before `**Firefox status.**`: "Version 0.4.0 was exercised against a Flask app with Jinja, Tailwind 4
   and DaisyUI and a Next.js 16 app with shadcn, in Chromium only. See [the audit record](docs/implementation/audit-2026-11-06-real-apps.md)."
   No app names, no support claim. Check: the link target exists (`test -f`), and the audit record's scope lines 40-60 agree.
6. **Next.js dev note (after line 521).** Under `next dev`, React may log a hydration mismatch for an element the bridge marked: the
   `data-design-id`, `data-design-role` and `data-design-name` attributes reach the page before hydration. It was seen once under `next dev`
   and not in three production loads; the attributes are how Studio identifies the element, so the bridge keeps them. Write no D-number. State it as
   "seen once", not as general. Check: audit row `D1-10a`; `fontkit-bridge.js` writes the attributes (grep `setAttribute('data-design-`).
7. **Auto-discovery of `stat` (Marking up, before the attribute table, or as one sentence under 598-599).** Auto-discovery matches the class
   `stat` by whole name; a class that only contains the letters, such as DaisyUI `stat-value` or `stat-desc`, is not found by that rule
   (it may still be found by the heading, paragraph, link and button rules); mark such elements with `data-design-id`. **Correction to the
   plan text:** `stat-title` is still found, through the `[class*="title"]` rule (`fontkit-bridge.js:120`); do not list it. Check: `git grep -n
   "'\.stat'" fontkit-bridge.js` and `tests/test_bridge_runtime.py` `AutoSelectorWholeNameTests`.
8. **Page that never stops changing (Detected roles, Known limits).** One bullet: a page that rewrites its text on a timer (a blinking
   cursor) counts as changing each time; Detect and Apply can end `page-changed` and need pressing again, while Clear always removes the
   preview. Fuller fix is not described. Check: `handleRoleMutation` as in 4; audit row `D2-10`.
9. **Known gaps (885).** Extend the Reapply bullet: a DOM move saved by 0.4.0 under a container whose selector held a state class (such as
   `is-active`) cannot be placed again; Reapply stops as a whole, nothing is sent, and the fix is to redo the move. Wording from Task 13's
   review; no test pins it (`failReapply`, `fontkit-studio.html` 5482-5571). Add one bullet for B08 and D2-11 as unfinished: Sync does not
   learn the token names the page reads, and an edit on a replaced auto-id element is only warned about, not re-applied. Add one for B09:
   when the app overwrites a heading's single string child, the Studio text edit is overwritten (a paragraph's Reset is fixed). Check:
   audit rows `B08-b`, `D2-11-b`, `B09`.
10. **CHANGELOG (Unreleased).** Placement: all user-visible commits under `### Fixed`; nothing new goes under `### Changed`. Grep the file for
    each phrase before adding, because most landed commits already have a line. Add these four lines, one per commit, after the last Fixed line,
    in commit order:
    - `a3050d3`: "Moving a list item, preformatted block, definition list, fieldset, caption, rule, main or definition term into a paragraph,
      heading, link, button, label or summary is now refused, since the browser would re-nest it on the next load."
    - `f620df0`: "Auto-discovery now matches the class `stat` by whole name, so `static` and `status` no longer get design attributes."
    - `84df677`: "Studio now shows three more kinds of warning from the bridge as notes; the protocol stays at version 1."
    - Task 17 (`fix(bridge): never refuse Clear because the page changed`): "Clear preview now always removes the preview, even when the page
      changed since the last Detect; Apply and Detect still report the change."
    No line for `310ad2b` (a refactor), `468b7bb`, `b28ee2b`, or any `docs:` commit. Wrap at about 80 columns like the neighbours.

## Tests (how each claim is checked; none new)

No test is added or changed: the claims are checked, not asserted by a new test. For each Requirement run the named `git grep -n` or `sed -n`
against the worktree and keep the line in the report. Then:

- `grep -n "0.4.2\|Task 1[0-9]\|D07[0-9]\|D080" README.md` returns nothing new in the lines you added (D-numbers and task names are process state).
- `git diff --stat` shows only `README.md` and `CHANGELOG.md`; `git diff --check` is clean; CRLF/LF unchanged (`file README.md CHANGELOG.md` before and after).
- `grep -c "" CHANGELOG.md` shows only added lines under `## [Unreleased]`; `python scripts/dev/release_notes.py` (as `tests/test_release.py` does) still
  parses the file: `PYTHONPATH=tests timeout 300 python -m unittest test_release test_support -v`.
- `tests/test_live_integration.py:38-44` reads README code lines by regex; the code fences are not edited, so no run is needed. Say so.
- `pre-commit run --files README.md CHANGELOG.md`.
- Every internal link added resolves (`test -f` on the path).

## Patch and commit

One patch: `task-18-code.patch`. Subject (54 characters): `docs: describe the 0.4.1 repairs and their limits`
Body (why, 72 columns): the README still advised routing fonts through tokens Sync may not reach, listed one warning kind and no error-page
note; it now states the fixed names, the added kinds, the limits the fixes leave, and what was tested. CHANGELOG gains the four missing lines.
No process state, no attribution line beyond what the dispatch gives.

## Open questions

1. **Plan text for `stat`.** The plan says DaisyUI `stat-title`, `stat-value` and `stat-desc` are no longer found. `stat-title` still is (through
   `title`). Recommendation: Requirement 7 as written; the plan sentence is superseded by the code.
2. **Leave prompt (Task 9).** Studio now asks before a reload or close drops unsynced edits, but the README does not describe it, and Task 9's known
   limit (one key covers every carrier, so Download of the HTML tab after a style edit closes silently) belongs to it. Recommendation: do not add
   either (not in the Task 18 list, and a limit of an undocumented feature). Say so in the report.
3. **Task 4 limit.** `design:restore-text` keeps an appended `inside` image and skips the emoji restore (Task 4 accepted limit). Recommendation:
   leave it out of the README; Reset via the inspector is not affected.
4. **`310ad2b`** (removed unused token names from the bridge's reported list). Recommendation: no CHANGELOG line (internal; no consumer read them).

## Controller rulings

1. Open question 1: use the brief's corrected wording; stat-title is still found through the title rule.
2. Open question 2: add neither to the README; the CHANGELOG line covers the leave prompt.
3. Open question 3: leave the restore-text image limit out of the README.
4. Open question 4: no CHANGELOG line for the refactor 310ad2b.

## Review fixes (binding: these govern over the text above)

1. Requirement 2: `edit-not-reapplied` applies to auto-id targets; `edit-reapply-stopped` comes from `reapplyFrom`, which runs for author-id targets (bridge 3416). Do not write that both apply to auto-id targets.
2. Requirement 10, the `a3050d3` line: the guard covers p, h1-h6, span, a, button, label and summary, and the browser re-nests only for a paragraph. Use the code's own reason: the browser would repair the markup differently.
3. Owned files gain the "Marking up elements" section of `README.md`, which requirement 7 edits.
4. Requirement 4: say a stale version is not a reason to refuse Clear. Do not write "only" for a different `documentId`: Clear is still refused for `invalid-message` and `revision-conflict`.
5. The Why section's "Requirement 9" means requirement 10. The audit's scope lines are 4-5 and 59.
