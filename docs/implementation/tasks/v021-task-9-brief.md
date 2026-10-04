# v0.2.1 Task 9 brief: docs, names and screenshots

Plan: `docs/plans/2026-10-03-v0.2.1-fit-and-finish.md` (Task 9). Plan addendum 5 and D039
replace the plan's line about keeping "v0.1.1": Studio's title and eyebrow now read v0.2.1.
Implementer: Tracking-9. Runs alone, after Task 8.

## Required

1. **README matches the product at this branch head.**
   - The first-run flow:
     - the Live App URL box starts empty;
     - `serve.py` prints `Open:`, names a busy port, and opens a browser only with `--open`;
     - "Connect to the demo".
   - Controls that are disabled say why.
   - Explain what Sync to file does with nothing saved: a fresh session never writes, and
     after the user's own reset it clears the file.
   - The preset select applies on change and asks first.
   - The renamed labels, especially "Live App" (Connect Live App, Accept Live App state).
   - The current version label.
   - Grep the README for every old name and fix each one: Target App, Live Target,
     Connect Target, Accept target state, "the target" meaning the user's page, Target URL.
     Do not change protocol or code names (`?target=`, `targetId`, `data-live-target`).
2. **One name outside Studio.**
   - `scripts/serve.py` prints the demo address under `Target:`. Make that label say what
     it is: the demo app, shown next to the `Open:` line. Change only the printed label and
     its comment, plus the test assertions that pin it (`tests/test_preview_server.py`).
   - The demo's meta and footer say "demo target app" (`demo/index.html`, about lines 8
     and 334). Change only that wording.
3. **Screenshots.**
   - Regenerate every screenshot with `docs/assets/screenshots/capture.py`.
   - Rename `target-app-*.png` to `live-app-*.png`, and update every reference (README, the
     capture script, `docs/assets/README.md` if it lists them).
   - Check each image by eye: it must show Task 8's visuals and the v0.2.1 title.
4. **CONTRIBUTING.md.** Fix stale names or commands, if there are any.
5. **CHANGELOG.md.** Add a line under Unreleased for every change a user notices (the
   `serve.py` label, the demo wording). README-only edits need no line.

## Owned

- `README.md`, `CONTRIBUTING.md`
- `docs/assets/screenshots/` and `docs/assets/README.md`
- the printed label in `scripts/serve.py` and its assertions in `tests/test_preview_server.py`
- the demo's "demo target app" wording
- `CHANGELOG.md`

Must not touch: Studio, the bridge, any other test, and any agent-facing doc (`AGENTS.md`,
plans, the ledger).

## Gates

- `python scripts/verify.py --static-only`
- `node --check fontkit-bridge.js`
- `PYTHONPATH=tests FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python -m unittest test_preview_server test_bridge_runtime test_live_integration -v`
- the capture script runs clean
- a link check: every relative link and image path in README, CONTRIBUTING and
  `docs/assets/README.md` resolves to a file

## Report

Append "## Implementer report" to this brief in your worktree. Include:
- each README section changed, with what it now says;
- the grep results before and after for the old names;
- the screenshots regenerated;
- the CHANGELOG lines;
- the final `git diff --stat`;
- what you did not verify.
