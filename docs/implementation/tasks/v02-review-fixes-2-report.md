# v0.2 review fixes, part 2: report

Scope: five review findings on PR #1 in the dev server, the frontend gate,
the commit-message check and the test harness. Each was reproduced with a
failing test before the fix.

## Dev server follows links out of the repository (high)

- Problem: `clean_path()` judged only the URL. A link inside the repository
  to an outside file, a hidden file, or an `index.html` in a directory was
  served on both ports.
- Change: `scripts/serve.py` resolves the path the handler would open
  (including the index file it picks for a directory) and answers 404
  unless the result is inside the repository with no hidden component
  (`repo_servable`, `Handler.real_path_servable`). The configured
  overrides file read goes through the same check.
- Tests: `PreviewServerSymlinkTest` in `tests/test_preview_server.py`
  (outside file, outside directory, hidden-file and hidden-directory
  aliases, directory `index.html` links, a symlinked overrides file, and an
  ordinary file plus an inside link that must still be served).
- Not covered: a link swapped between the check and the open. The server is
  a loopback development tool; the owner can decide whether to open the
  resolved file directly instead.

## Gate asset scans were case-sensitive (medium)

- Change: `@import`, `url(` and absolute `http(s)://` addresses are matched
  case-insensitively in `scripts/dev/_frontend_gate_assets.py`.
- Tests: mixed-case cases in `LogoStaticTests`.

## Logo paint judge dropped the colour's own alpha (medium)

- Change: the parsed `rgba()` alpha is multiplied by the measured opacity
  before compositing.
- Tests: `LogoPaintJudgeTests` translucent-fill cases.
- Text contrast path (`_frontend_gate_theme.py`): not affected. `sample_ratio`
  already multiplies the colour alpha by the ancestor opacity. A
  characterisation test pins it.

## Human names matched as model names (medium)

- Change: `AI_MODEL_NAME` in `scripts/dev/check_commit_messages.py` needs a
  word boundary after an alphabetic model word. Version numbers still match
  on the first digit.
  The boundary is `(?![a-z])`, not `\b`, so a glued digit
  ("Claude Opus4.1", "Claude Sonnet4") is still caught.
- Tests: human-name cases (Claude Proctor, Claude Opusville, Gemini Haikuson
  and others) and model-name cases that must still fail, in
  `tests/test_commit_messages.py`.

## Empty engine list ran no browser (medium)

- Change: `tests/support.py` raises at import when `FKS_ENGINES` selects no
  engine or names an engine other than chromium, firefox or webkit. Names
  are trimmed and lower-cased.
- Tests: `tests/test_support.py` imports the harness in a subprocess.
- The gate's own engine parser (`frontend_gate.py`) is unchanged: it falls
  back to both engines on a blank value, so it never runs zero browsers.
