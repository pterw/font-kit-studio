# R1 7b brief: Next.js behind the proxy

Plan: `docs/plans/2026-10-04-r1-pr-c-sdd.md` (7b, R1.7b); what R1 builds:
`docs/plans/2026-10-03-r1-one-command.md` (R1.7); design spec 4.1, "Next.js app: Proxy mode
in front of `next dev`, including its hot reload". Constraints:
`.superpowers/sdd/r1-pr-c/constraints.md` (read all of it first). Versions: D043 in
`docs/implementation/deviations.md`.

## Goal

Prove that `npx fontkitstudio http://localhost:<port>` works on a real Next.js 16 app:
- Studio connects.
- A live edit applies.
- A CSS hot update reaches the page through the proxy's WebSocket pass-through, without a
  reload, with Studio still connected and the edit kept.

## Owns

- `fixtures/next-app/`:
  - `package.json`: private, `"type": "module"` not needed, scripts `dev`.
    `dependencies`: `next` `16.3.8`, `react` and `react-dom` `19.3.0`, all exact.
  - `package-lock.json`, from `npm install` in your worktree.
  - `app/layout.jsx`, `app/page.jsx`, `app/globals.css`. Use plain JS/JSX with no
    `tsconfig.json`, so Next does not try to install TypeScript.
- `tests/test_one_command_next.py`.
- One line in `.gitignore`: `fixtures/*/.next/`.

## Fixture page

- **Layout:** `app/layout.jsx` imports `./globals.css` and renders `<html lang="en"><body>`.
- **Page:** `app/page.jsx` holds:
  - `<h1 data-design-id="next.hero.title">`;
  - `<p className="lead" data-design-id="next.hero.lead">`;
  - `<button className="cta" data-design-id="next.hero.cta">`.
- **Styles:** `app/globals.css` gives the title a font-size other than 56px and the lead a
  colour, `rgb(51, 51, 51)`.
- **No external content:** no fonts from Google, no images, no external URLs (`next/font`
  is not used).

## Test

Patterns: `tests/test_one_command_proxy.py` (helper process, the two lines, CSP checks) and
`tests/test_one_command_vite.py` (the real bin, stopping on Windows, the hot-update test).
Read both first. Skip the class when `node` is missing; call
`require_fixture(self, 'next-app')`.

1. **Start Next.**
   - Command: `node fixtures/next-app/node_modules/next/dist/bin/next dev --hostname
     127.0.0.1 --port <free port>`, with `cwd=fixtures/next-app` and the environment plus
     `NEXT_TELEMETRY_DISABLED=1`.
   - Wait until an HTTP GET of `/` answers 200 (poll with a short interval and a 120 s
     deadline). The first compile is slow.
   - Stop it in a cleanup, by handle (Ctrl-Break on Windows with
     `CREATE_NEW_PROCESS_GROUP`), and kill only that process on timeout.
   - Next may spawn workers. Report any process left running after the stop; check with
     PowerShell `Get-CimInstance Win32_Process` filtered on your worktree path.
2. **Start the command.** Run `node packages/fontkitstudio/bin/fontkitstudio.js
   http://localhost:<port> --no-open` and read `Open: <url>`.
3. **Open Studio.**
   - In a `support.new_context(engine)`, route `https://**/*` to abort.
   - Add an init script that records `pageerror`-like failures and console errors into
     `window.__errors` in every frame. Or use Playwright's `page.on('pageerror')` and
     `frame` console events; pick one and say which.
   - Open the URL. Wait for `#bridgeStatusBadge` to match `^Connected \(\d+ targets?\)$`.
4. **Live edit.**
   - Click the title in `#targetAppFrame` until `#liveTargetName` names
     `next.hero.title`, with one retry, as `test_one_command_vite.click_in_target` does.
   - Type `56` into `#liveFontSize` with keystrokes: click, Ctrl+A, `keyboard.type`.
   - Wait until the frame title's computed `font-size` is `56px`.
5. **Hot update.**
   - Set `window.__fksMarker = 1` in the frame.
   - Rewrite `app/globals.css` so the lead's colour becomes `rgb(200, 0, 0)`. Write the
     bytes with LF; keep the original bytes and restore them in `addCleanup`, byte for
     byte.
   - Wait until the lead's computed colour is `rgb(200, 0, 0)` (30 s deadline). Then
     assert:
     - `window.__fksMarker === 1` (no reload);
     - the badge still matches Connected;
     - the title is still `56px`.
6. **No errors.** No page error, and no console error mentioning hydration, in the frame.
   React 19 skips the injected head script during hydration; this proves it on Next. If
   Next's dev overlay logs something unrelated, quote it in the report instead of filtering
   it silently.
7. **Raw page.** Fetch `http://<proxy origin>/` with `urllib.request` (or read it through
   Studio's target URL). The body has exactly one `<script src="/@fontkit/fontkit-bridge.js"`.

## Risks (stop and report NEEDS_CONTEXT rather than working around them)

- Next 16 may refuse dev resources (`/_next/*`, the HMR socket) to an origin it does not
  expect (`allowedDevOrigins`). The proxy rewrites `Host`, `Origin` and `Referer` to the
  target's on HTTP and WebSocket upgrades (`packages/fontkitstudio/src/proxy.js`). If Next
  still refuses, do not edit the proxy or add `allowedDevOrigins` to the fixture: report it.
- Any change outside the files you own is out of scope. Report what you would change and
  why.

## Definition of done

- `npm install` in `fixtures/next-app` of your worktree produced the lockfile. Record npm's
  version and the install time.
- GREEN: `PYTHONPATH=tests python -m unittest test_one_command_next -v`, three runs in a
  row. Report the times.
- Not vacuous, each shown once and restored by editing:
  - Without the WebSocket pass-through, the hot-update assertion fails, and the report names
    the failing line. To show this, make the proxy's `upgrade` handler destroy the socket
    in your worktree, then restore it.
  - A wrong author id fails the selection.
- Also run: `PYTHONPATH=tests python -m unittest test_support -v`; `python -m ruff check .`.

## Report

- Code phase report: `.superpowers/sdd/r1-pr-c/task-7b-code-report.md`.
- Patch: `.superpowers/sdd/r1-pr-c/task-7b-code.patch` (`git diff --binary` from BASE; new
  files via `git add -N`; no `node_modules` or `.next`).
- Handoff:
  - **The CI job.** Draft the YAML for a `next-fixture` job in
    `.github/workflows/quality-gate.yml`. Model it on the `fixtures` job:
    - `ubuntu-latest`, Node 24, `cache: npm` on `fixtures/next-app/package-lock.json`;
    - `npm ci --prefix fixtures/next-app`, then prepack, then pip and Chromium;
    - env `FKS_ENGINES: chromium`, `FKS_REQUIRE_FIXTURES: '1'`, `NEXT_TELEMETRY_DISABLED:
      '1'`, `PYTHONPATH: tests`;
    - run `python -m unittest test_one_command_next -v`.
  - **Lockfile size.** The lockfile's line count, which is churn under D050.
  - **Ledger.** A `progress.md` event draft.
  - **Commit.** The subject `test: run Studio on a Next.js app behind the proxy`, with a
    why-body.
