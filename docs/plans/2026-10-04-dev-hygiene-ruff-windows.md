# Dev hygiene: ruff in CI, and the Windows-only test failures

Status: **active** (owner, 2026-10-04). One small pull request from `main`, branch
`chore/ruff-and-windows-tests`, before R1 PR B starts. Not part of a roadmap release.

## Why

- The v0.2.1 sweep left unused test imports, and nothing stops new ones: a lint step with
  only pyflakes rules catches unused imports and names, undefined names and syntax errors,
  in seconds, without restyling any file. `ruff format` is out (it would rewrite every
  file for no behaviour gain).
- Six tests fail on Windows only (CI runs Linux), so a Windows contributor's full suite is
  never green and real regressions hide among known failures. The dev server also cannot be
  stopped gracefully on Windows except with Ctrl-C in its own console.

## Tasks

- [ ] **H1 Ruff (controller).** `ruff==0.16.10` in `requirements-dev.txt`; `ruff.toml`
  (`select = ["F", "E9"]`, `target-version = "py311"`, `extend-exclude = [".claude",
  "work"]`); a "Lint Python (ruff)" step in the quality-gate job after the static checks;
  `ruff check .` in the AGENTS.md gate list and CONTRIBUTING; fix the eight findings
  (unused imports, three dead local variables in tests, one f-string without placeholders).
  Each dead variable was read first: none hid a missing assertion.
- [ ] **H2 Windows-only failures (implementer).** Brief:
  `docs/implementation/tasks/hygiene-task-h2-brief.md`. `serve.py` also stops gracefully on
  `SIGBREAK` (Ctrl-Break) where it exists; the test helper stops the server with
  `CTRL_BREAK_EVENT` on Windows; files are read as UTF-8; the clipboard test compares text
  with line endings normalized.
- [ ] **Review and gates.** One independent review of the whole diff; full gates; CI green.

## Definition of done

- `ruff check .` passes locally and in CI; a deliberately unused import makes it fail.
- On Windows, `python -m unittest discover -s tests` has no failures (Chromium).
- On Linux CI, nothing changes: the same tests pass.
- No product behaviour changes except `serve.py` stopping cleanly on Ctrl-Break on Windows.
