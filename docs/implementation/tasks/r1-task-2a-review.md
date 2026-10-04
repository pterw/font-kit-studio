### Spec Compliance
- PASS: rename is byte-identical. `git show :fontkit-studio.html | sha256sum` = `git show 0adb4fb:font_kit_studio_v0.1.1.html | sha256sum` = cf9463d4...2611c. `-B -M` stat shows the rename at 0 changed lines.
- PASS: stub text matches the brief's step 3 verbatim (font_kit_studio_v0.1.1.html, 11 lines).
- PASS: tests/test_studio_rename.py matches the brief's step 2 verbatim; support.HTML updated (tests/support.py:23). Ran `PYTHONPATH=tests python -m unittest test_studio_rename`: 3 tests, OK.
- PASS: every file in the brief's step 4 list is updated (support, gate helpers, gate runner, preview server incl. the refuse-list case at test_preview_server.py:593, serve.py, _frontend_gate_shared.py, capture.py, README 46 and 66). No file outside the Owns list is touched.
- PASS: verify.py has APP and SUPPLIED_APP and `provenance()` maps SUPPLIED_APP (scripts/verify.py:16, :65).
- PASS: no commit made in the code phase; commit-messages gate and pre-commit reported as not run (AP 14 honoured).
- PASS (Minor): README:66 says more than "when the old name goes": it adds "is now a small page that forwards to it (keeping any query and hash)". The brief says the old name "forwards until the release after 0.3.0", so "forwards" is allowed; the parenthetical and "small page" are extra. See Minor 1.

### Checks run
- Remaining old-name hits (risk 1) -> `git grep -n --cached "font_kit_studio_v0.1.1"` -> classified: stub itself; tests/test_studio_rename.py:6 (OLD path of the stub test); scripts/verify.py:16 (provenance constant); README.md:66 (migration note); AGENTS.md:4 (shared file, Handoff); CHANGELOG.md:109 (dated 0.2.1 entry, point-in-time per ruling 5); docs/plans/* (dated plans, R1 plan, PR A SDD doc), docs/reference/*, docs/reference/SOURCES.json (provenance manifest, source is the Downloads path), docs/implementation/**, docs/specs/**. No missed live reference. Also grepped `font_kit_studio|studio_v0` outside records: only module name `test_font_kit_studio_v011` (README:571, firefox_canary.py:28, test_support.py:127,141), which is a module name, not the file name; correctly left. No hits in .github, demo, packages, docs/agents.
- Stub as URL sink (risk 2) -> ran a real Chromium page via tests/support.py against the stub with suffixes `?x#//evil.test`, `#/evil.test`, `?//evil.test`, `#//evil.test` -> all landed on `file:///C:/fks/t2a/fontkit-studio.html` + the same suffix; scheme and host unchanged. Reasoning: the target is the fixed relative literal, query/hash are appended after it, so they cannot precede the path.
- verify.py (risk 3) -> `python scripts/verify.py --static-only` in C:/fks/t2a -> all PASS; provenance PASS for `supplied-v0.1.1:font_kit_studio_v0.1.1.html` (tag blob under the old name) and the two docs/reference files; static checks ran on `fontkit-studio.html` (SHA line names it); last line `SKIP unittest/browser tests: --static-only; full acceptance not checked`.
- Stub test strength (risk 4) -> read the test. The query-and-hash test compares full `page.url` to `HTML.as_uri() + suffix` in a real browser, so dropping `location.search` or `location.hash` fails it; deleting the stub fails at goto; the no-query case guards the empty-suffix path; the text test pins the forward expression. It also asserts the title starts "Font Kit Studio v", which proves the real Studio loaded.
- Overrides refusal case (risk 5) -> test_preview_server.py:593 diff -> the refused path is now `fontkit-studio.html`, the file the server actually serves via STUDIO_HTML, so the case still protects Studio.
- README note (risk 6) -> read README.md:66 -> says the old name goes "in the release after 0.3.0"; see Minor 1 for the extra wording.
- Handoff drafts (risk 7) -> read the report Handoff against CHANGELOG.md and AGENTS.md at HEAD -> see Minor 2.
- README claims at HEAD -> README:46 example URL matches what serve.py prints (`/fontkit-studio.html?target=...`, asserted in test_preview_server.py:487); README:66 claims true (the stub forwards query and hash, verified above).
- Gate evidence -> not re-run (report carries it): suite-a 416 tests with exactly the six known Windows baseline failures, suite-b 375 OK, frontend-gate 30/30, node-package fail 0. Plausible given the change is a rename plus a stub; I ran only the stub test and verify.

### Strengths
- Study body untouched: blob identity holds, so the pure-rename rule (ruling 4) is met.
- The report states the CRLF working-copy hash vs blob hash difference explicitly and compares the right thing.
- Provenance remains pinned to the tag's old name while static checks follow the new file.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
1. README.md:66 adds "is now a small page that forwards to it (keeping any query and hash)" beyond a note of when the old name goes. The brief's own rewrite wording ("the old name forwards until the release after 0.3.0") is shorter. Harmless and true, but more than the stated scope.
2. Handoff (report line 55-57) tells the landing to "revise" CHANGELOG.md:109 ("The Studio file is still `font_kit_studio_v0.1.1.html` until the rename"). That line sits in the dated 0.2.1 entry, which is a point-in-time record under ruling 5 and keeps the old name. The landing should not edit it; the [Unreleased] "Changed" line is the right place and its draft text is accurate and carries no process state. The AGENTS.md line 4 draft (file name only) is accurate. The progress.md event contains test-suite state, which is acceptable for progress.md but must not be copied into CHANGELOG or commit text.
3. README "Test files" table (README.md:~571-585) has no row for the new tests/test_studio_rename.py, while it lists nearly every other test file. README ownership covers only file-name references and the migration note, so the task could not add it without leaving its ownership; flag for the landing or a README pass.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The rename is byte-identical, the stub cannot change scheme or host (checked in a real browser with hostile suffixes), verify.py keeps provenance on the old name, and all live references are updated. Only Minor documentation points remain.
