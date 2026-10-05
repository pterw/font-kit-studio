# Task 7b code report (mode: code)

Files (patch `task-7b-code.patch`, 7 files, 1191 insertions): `.gitignore` (+`fixtures/*/.next/`),
`fixtures/next-app/{package.json,package-lock.json,app/layout.jsx,app/page.jsx,app/globals.css}`,
`tests/test_one_command_next.py`. `git apply --check -R` passes. No node_modules or .next in it.

## Steps
- Fixture: done as briefed (next 16.3.8, react/react-dom 19.3.0 exact, plain JSX, no tsconfig).
  Title font-size 40px, lead colour rgb(51, 51, 51). `npm install --no-audit --no-fund`: npm 10.8.2,
  23 packages in 29 s, lockfile 950 lines (churn under D050).
- Test: done. Next started by handle (Ctrl-Break, kill on timeout), 120 s poll for 200; command run
  against `http://localhost:<port>`; errors via Playwright `pageerror` plus page `console` events
  (frame console messages arrive on the page); css bytes restored in addCleanup (and between engines);
  raw page fetched through the proxy target: exactly one bridge tag.
- Deviation (small): after the edit the badge text reads "Live · rev N", not "Connected (N targets)", so the
  post-hot-update check uses `data-state in (connected, live)` exactly as test_one_command_vite does.
  Connected text is matched before the edit.
- No Next refusal of the proxied origin: no allowedDevOrigins needed; proxy untouched.

## Evidence
GREEN x3 (`PYTHONPATH=tests python -m unittest test_one_command_next`): 16.8 s (cold compile), 4.5 s, 4.3 s, all OK.
Mutation 1: proxy.js line 300 replaced by `socket.destroy(); return;` (start of the upgrade handler):
FAILED, test line 179, the `frame.wait_for_function` for lead colour rgb(200, 0, 0) timed out at 30 s. Restored (cmp via
copy; git shows proxy.js unmodified).
Mutation 2: TITLE_ID = 'next.hero.wrong': FAILED in select_title (line 134), wait_for_function 3000 ms timeout. Restored.
Also: `test_support` 34 tests OK; `ruff check .` All checks passed; pre-commit (via `python -m pre_commit`, the
bare command is not on PATH) passed on the changed files.
Not run: full suite (task scope names only these); Firefox (ENGINES default Chromium).

## Processes
After the runs, a Get-CimInstance filter on the worktree path showed only my own bash/powershell shells; no next,
node or worker process left.

## Self-review
AP 13: every Next and command process stopped by handle in addCleanup. AP 14: require_fixture used, no skip in CI.
AP 11-12: grepped nothing renamed. Rule 6: css restored byte for byte. Rule 7/10: https routed to abort,
NEXT_TELEMETRY_DISABLED=1. D040: no user-facing text. Finding to know: Next 16 writes `AGENTS.md` and `CLAUDE.md`
into `fixtures/next-app/` on install/dev (agent-rules boilerplate). I did NOT include them in the patch; they appear
untracked in the worktree. The controller should decide: ignore them (add `fixtures/next-app/AGENTS.md` and CLAUDE.md
to .gitignore) or delete after runs; they will reappear on each `next dev`/install. Outside my owned files, so not changed.

## Handoff
Commit subject: `test: run Studio on a Next.js app behind the proxy`
Body draft: Prove the R1 proxy mode on a real Next.js 16 dev server: Studio connects, a live edit applies, and a CSS
hot update crosses the proxy's WebSocket pass-through with no reload, the edit kept and no hydration errors.
The fixture is pinned by lockfile.

CI job (`.github/workflows/quality-gate.yml`), model on `fixtures` job (check its step names/versions):
```yaml
  next-fixture:
    runs-on: ubuntu-latest
    env:
      FKS_ENGINES: chromium
      FKS_REQUIRE_FIXTURES: '1'
      NEXT_TELEMETRY_DISABLED: '1'
      PYTHONPATH: tests
    steps:
      - uses: actions/checkout@<same pin as fixtures job>
      - uses: actions/setup-node@<same pin>
        with:
          node-version: 24
          cache: npm
          cache-dependency-path: fixtures/next-app/package-lock.json
      - run: npm ci --prefix fixtures/next-app
      - run: npm --prefix packages/fontkitstudio run prepack
      - uses: actions/setup-python@<same pin>
        with: { python-version: '3.13' }
      - run: python -m pip install -r requirements-dev.txt   # as the fixtures job does
      - run: python -m playwright install --with-deps chromium
      - run: python -m unittest test_one_command_next -v
```
Lockfile: 950 lines (churn). Ledger draft: "7b: Next 16.3.8 fixture and test_one_command_next; proxy WS pass-through
proven (mutation: destroying upgrade sockets fails the hot-update wait); GREEN x3."

## Fix round 1
1. Second live edit: after the hot update, `#liveFontSize` gets Ctrl+A and `48`; the frame title must read 48px (8 s).
2. Next's stdout and stderr are drained by two daemon threads into a buffer; the last 40 lines are in the failure
   message when `next dev` exits early or does not answer 200 within 120 s.
3. After stopping, Next's port and the proxy's port (from the Open: line) must refuse connections (`refused()`, as in the
   vite test); only own processes are stopped by handle.
4. Console errors that are not about hydration, collected per run and printed at the end of the test: exactly one,
   `Failed to load resource: the server responded with a status of 404 (Not Found)` (same in all 3 runs; no URL in the
   text, so I did not confirm it is /favicon.ico; it is not a hydration or page error). No other console errors.

Evidence: `PYTHONPATH=tests python -m unittest test_one_command_next` x3: OK in 7.6 s, 8.1 s, 7.6 s. `test_support` OK
(34 tests), `ruff check .` All checks passed. (Two intermediate runs failed on my own bugs, a string-escape mishap and
`urlsplit` on the "Open: " prefix; fixed.) No mutation re-run: the earlier two mutations still target unchanged lines.
Patch regenerated at the same path; `git apply --check -R` passes. AGENTS.md and CLAUDE.md left alone.

## Fix round 2
The proxy-port refusal check in the command cleanup is skipped when proxy_port is None (no Open: line read), with a comment. Run: test_one_command_next OK once, test_support OK, ruff clean. Patch regenerated, apply -R check passes.
