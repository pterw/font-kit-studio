# Task 2a code report (MODE: code, worktree C:/fks/t2a, base 0adb4fb)

Patch: `.superpowers/sdd/r1-pr-a/task-2a-code.patch` (`git apply --check -R` passes).
Files: fontkit-studio.html (A, rename), font_kit_studio_v0.1.1.html (now stub), tests/test_studio_rename.py (A),
tests/support.py, tests/test_frontend_gate_helpers.py, tests/test_frontend_gate_runner.py,
tests/test_preview_server.py, scripts/serve.py, scripts/dev/_frontend_gate_shared.py, scripts/verify.py,
docs/assets/screenshots/capture.py, README.md.

## Steps
1. Rename: done (git mv). Blob id identical to BASE (b4248f8b...). Working-copy sha256sum differs
   (b9448116... vs cf9463d4... from `git show`) only because core.autocrlf=true gives the checkout CRLF;
   `git show :fontkit-studio.html | sha256sum` = cf9463d4..., equal to BASE's.
2. Test written. RED: with the old file gone, `PYTHONPATH=. python -m unittest test_studio_rename` -> 3 errors,
   FileNotFoundError on font_kit_studio_v0.1.1.html (expected: stub not written yet).
3. Stub written. GREEN: same command, `Ran 3 tests ... OK`. Test would fail if the stub were deleted or its
   forward target changed (RED above is the deleted case; the stub-text test pins the target string).
4. References updated (list in brief). Remaining `git grep font_kit_studio_v0.1.1` hits:
   stub itself and test_studio_rename (OLD path); scripts/verify.py SUPPLIED_APP (provenance);
   README line 66 (migration note); docs/specs, docs/implementation, dated docs/plans, docs/reference
   (point-in-time/provenance, ruling 5); AGENTS.md:4, CHANGELOG.md:109, docs/plans/2026-10-03-r1-one-command.md
   and 2026-10-04-r1-pr-a-sdd.md (shared files, see Handoff). Names `test_font_kit_studio_v011` (module) stay: not
   the file name.
5. verify.py: APP/SUPPLIED_APP done; `--static-only` all PASS, provenance verified (supplied-v0.1.1:font_kit_studio_v0.1.1.html).
   Note: README line 46 example URL also updated.
6. Gates (Chromium; Firefox inside frontend-gate):
   - static: exit 0, last line `SKIP unittest/browser tests: --static-only; full acceptance not checked`
   - bridge-syntax: exit 0
   - node-package: `ℹ tests 6`, `ℹ fail 0`
   - suite-a: 416 tests, FAILED (failures=4, errors=2): exactly the six known Windows baseline failures
     (DemoPageTest.test_demo_source_is_offline, Lifecycle: prints_studio_url (ERROR), browser_is_not_opened,
     last_line_before_the_wait, open_flag_opens (FAIL), test_copy_uses_the_real_clipboard). Nothing else.
   - suite-b: 375 tests, OK
   - frontend-gate: `SUMMARY OK: 30 of 30 planned runs finished. Blocking: 7 runs, 7 passed, 0 failed`
   - commit-messages: not run (no commit in code phase). pre-commit: not installed, not run.

## Self-review (anti-patterns)
- AP 4 (URL sinks): stub's `location.replace` target is the fixed relative literal "fontkit-studio.html"; only
  search/hash of the same page are appended, so no input changes scheme or host; a relative target stays
  same-origin/same-scheme. Test pins the literal.
- AP 11/12 (siblings): grepped all live files for the old name (and the module-name variants); every live
  copy in my ownership is updated; the shared-file copies are listed for the landing.
- AP 14: only gates listed above ran; commit-messages and pre-commit are reported not run.
- AP 15: no process state in the drafts below.
- AP 13: tests start no servers; browser contexts closed in tearDown.
- Hostile cases: the stub is a boundary only via the URL; the fixed target is the guard. No token/Host/Origin applies.

## Observations
- Diff stat shows ~6,180 lines add/delete because the stub replaces the old path in the same commit, so git does not
  detect a rename; report as churn (ruling 1). Use `-B -M` for measuring.

## Handoff
- Commit: `refactor(studio): rename Studio to fontkit-studio.html`. Body: D041, a versionless name that says what
  the file is and pairs with the bridge; the old name remains as a small page that forwards, keeping query and
  hash, for one release.
- CHANGELOG [Unreleased] "Changed": `- Studio is now fontkit-studio.html. The old name, font_kit_studio_v0.1.1.html,
  forwards to it (query and hash kept) until the release after 0.3.0.` Also CHANGELOG.md:109 says the file is
  still the old name "until the rename": revise that line (it sits in an entry below/at Unreleased; check).
- AGENTS.md line 4: `font_kit_studio_v0.1.1.html` -> `fontkit-studio.html`.
- progress.md event: R1.2a Studio renamed to fontkit-studio.html; old name forwards; suites a (six known Windows
  failures only), b, frontend-gate 30/30 pass.
- Plan checkbox: R1.2 stays open until R1.2b; tick the PR A SDD "no live reference" item after landing.
