# R1 B3b brief: the command

Plan: `docs/plans/2026-10-04-r1-pr-b-sdd.md` (B3b, R1.4d; After: B3a, B5); what R1 builds:
`docs/plans/2026-10-03-r1-one-command.md` (R1.4). Constraints:
`.superpowers/sdd/r1-pr-b/constraints.md` (read all of it first). Builds on, read first:
`src/project.js` (B1), `src/vite-plugin.js` (B2), `src/run-proxy.js` and
`src/open-browser.js` (B5), `src/cli.js` and `bin/fontkitstudio.js` (PR A),
`tests/fixture_support.py` (B3a).

## Goal

`npx fontkitstudio` is the product's front door. In a Vite project it runs the project's
own Vite with the plugin added in memory (nothing is written to the project, global rule
6); given a URL it runs B5's proxy. Either way it prints two lines, opens Studio connected
to the app unless `--no-open` (D051), and stops cleanly on Ctrl-C, leaving no process
behind (anti-pattern 13). A real browser proves it on both Vite fixtures.

## Definition of done

- `node bin/fontkitstudio.js --no-open` in `fixtures/vite-react` and in
  `fixtures/vite7-react` prints the two lines; the `Open:` URL shows Studio connected; a
  live edit renders in the page; a CSS hot update keeps the connection and the edit; the
  page carries exactly one bridge tag although the fixture's config already has
  `fontkitStudio()`; stopping the command ends the process and frees both ports.
- CLI tests cover every argument case below with its text and exit code.
- Mutation evidence, one at a time, with the failing test named: the dedupe check in the
  plugin; `--no-open` ignored (always open); the Vite-project check skipped.
- The `fixtures` CI job installs Chromium and runs `test_one_command_vite` and
  `test_one_command_proxy` with `FKS_REQUIRE_FIXTURES=1`.

## Deviation from the plan (binding)

The plan says "editing `src/App.jsx` (hot update) keeps the connection and the edit". The
fixtures use no `@vitejs/plugin-react` (no React Fast Refresh, to keep lockfiles small), so
a JSX edit makes Vite reload the page, and after a reload Studio rightly asks before
re-applying edits (global rule 6). The hot-update test therefore edits `src/app.css`, which
Vite swaps without a reload. Record this in the report's deviations.

## Owns

`packages/fontkitstudio/src/cli.js`, `src/run-vite.js` (new), `test/cli.test.js`, the
dedupe hook in `src/vite-plugin.js` and its tests in `test/vite-plugin.test.js`, one export
in `src/run-proxy.js` if needed (below), `tests/test_one_command_vite.py`, and the
`fixtures` job's last two steps in `.github/workflows/quality-gate.yml`.

## Interface (binding; B6 builds on it)

```js
// src/run-vite.js
export async function runVite({
  projectDir,                   // the folder the command runs in
  open = true,
  out = process.stdout, err = process.stderr,
  studioPort = 0,
  openUrl = openBrowser,
  studioFile, bridgeFile,       // tests only
}): Promise<{ studioUrl, appUrl, close(): Promise<void> }>;

// src/cli.js
export const USAGE: string;
export async function main(argv, { out, err, cwd = process.cwd() }): Promise<number>;
```

Studio start with the port fallback: B5 wrote it inline in `runProxy` (the `EADDRINUSE`
branch in `src/run-proxy.js`). Extract it, unchanged, into an exported
`startStudio({ studioPort, studioFile, err })` in `run-proxy.js` (the only edit B3b makes
there), call it from both runners, and keep B5's tests passing; never copy it.

## Behaviour

- **Arguments** (`main`): `--help`/`-h` and `--version`/`-v` as today; `--no-open`;
  `--studio-port <n>` or `--studio-port=<n>` (an integer 1-65535); at most one positional
  URL. Order free. Exit codes: 0 started (the process then lives on its servers), 2 usage
  errors, 1 start-up failures. Texts:
  - unknown flag: unchanged (`fontkitstudio: unknown argument "<arg>"` plus usage), 2;
  - bad port: `fontkitstudio: --studio-port needs a port number from 1 to 65535`, 2;
  - two positionals: `fontkitstudio: give one dev server address, not two`, 2;
  - a positional that `new URL` cannot parse:
    `fontkitstudio: "<arg>" is not a URL. Give your dev server's address, such as http://localhost:3000`, 2;
  - a URL `startProxy` refuses (`https:`, a remote host): its message, 2;
  - no URL and `isViteProject(cwd)` false:
    `Font Kit Studio found no Vite project in <cwd>. Run it in your Vite project, or give your dev server's address: npx fontkitstudio http://localhost:3000`, 2;
  - a `ProjectError` from `loadVite` (untested major, Vite not installed): its message, 1.
  Errors go to `err`; never print a stack.
- **USAGE**:
  ```
  Usage: fontkitstudio [<url>] [--no-open] [--studio-port <n>] [--help] [--version]

  Font Kit Studio <version>: try type on your running web app, in development only.

    fontkitstudio                          in a Vite project: run its dev server with Studio
    fontkitstudio http://localhost:3000    any other local dev server: Studio through a proxy
    --no-open                              print the URL instead of opening the browser
    --studio-port <n>                      keep Studio on one port, so its settings stay
  ```
- **`runVite`**: `loadVite(projectDir)`; start Studio (with the fallback); then
  `vite.createServer({ root: projectDir, plugins: [fontkitStudio({ studio, bridgeFile })] })`
  (Vite still loads the project's own config and merges it); `await server.listen()`;
  `server.printUrls()`; `appUrl = server.resolvedUrls.local[0]`; write
  `Font Kit Studio · dev only` and `Open: <studio.url(appUrl)>`; open unless
  `open` is false. Signals and `close()` exactly as `runProxy` (SIGINT, SIGTERM, SIGBREAK on
  win32; `close()` closes Vite, then Studio, removes its handlers, idempotent). If Vite fails
  to start, close Studio before rethrowing.
- **Dedupe** (`vite-plugin.js`): a plugin created with `options.studio` (the command's)
  exposes `api: { fontkitStudio: { fromCommand: true } }`. In `configResolved(config)`, an
  instance created without `options.studio` stands down when `config.plugins` holds another
  `fontkit-studio` plugin whose `api.fontkitStudio.fromCommand` is true: its
  `configureServer` then does nothing (no Studio server, no middleware, no log line) and its
  `transformIndexHtml` returns `[]`. One Studio, one tag.

## Steps

- [ ] **1. Failing Node tests.** `test/cli.test.js`: each argument case above through the
  real bin (`spawnSync`, `cwd` set): the fake non-Vite folder is a temp dir with a
  `package.json` and no vite; the Vite-7/8 refusals use B1's `fakeProject` with Vite 9.0.0
  and with no Vite; `--studio-port 0`, `--studio-port 70000`, `--studio-port abc`; `a b`
  (two positionals); `not a url`; `https://localhost:3000`; `http://example.com`. Assert
  stderr text and status. `test/vite-plugin.test.js`: the dedupe rule with two plugin
  objects and a fake `config.plugins`; the command's plugin exposes the api flag; a
  standalone instance alone does not stand down. Run: RED.
- [ ] **2. Implement** `run-vite.js`, the CLI parsing and dispatch, the dedupe hook. Keep
  the bin as it is (it sets `process.exitCode` from `main`).
- [ ] **3. Browser test** `tests/test_one_command_vite.py` (Chromium via `ENGINES`):
  - `setUpClass`: `require_fixture` per fixture in each test; bundle once with
    `[node, 'packages/fontkitstudio/scripts/bundle.js']` (cwd the repo; no npm);
  - start `[node, str(BIN), '--no-open']` with `cwd` the fixture, `stdout=PIPE`,
    `stderr=PIPE`, `text=True`, `encoding='utf-8'`; on Windows
    `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP`. Read stdout lines on a reader
    thread into a queue; wait up to 60 s for the `Open:` line (fail with the collected
    output otherwise); assert the line before it is `Font Kit Studio · dev only` and that no
    line starts with `  Font Kit Studio: ` (the standalone plugin stood down);
  - stop in a cleanup: `CTRL_BREAK_EVENT` on Windows, `SIGINT` elsewhere; `wait(15)`;
    if it does not exit, kill only that process and fail the test ("the command did not
    stop"); then assert connecting to the Studio port and the Vite port is refused;
  - test (vite-react): open the `Open:` URL; `context.route('https://**/*', abort)`; wait
    for `#bridgeStatusBadge` `^Connected \(\d+ targets?\)$`; in `#targetAppFrame` count
    `script[src="/@fontkit/fontkit-bridge.js"]` is 1; click
    `[data-design-id="vite.hero.title"]` until `#liveTargetName` names it (one retry, as in
    `test_live_integration.click_in_target`); type `56` into `#liveFontSize` with
    keystrokes; wait for the frame title's computed `font-size` `56px`; then rewrite
    `src/app.css` adding `body { background-color: rgb(1, 2, 3); }` (restore the original
    bytes in `addCleanup`, registered before the write); wait for the frame body's computed
    `background-color` `rgb(1, 2, 3)`; assert the title is still `56px` and the badge still
    Connected; no page errors;
  - test (vite7-react): start, open, Connected, one bridge tag (connect check only).
  Then `PYTHONPATH=tests python -m unittest test_support`.
- [ ] **4. CI**: in the `fixtures` job, before the fixture tests step, add
  `python -m pip install -r requirements-dev.txt` and
  `python -m playwright install --with-deps chromium`; set `FKS_ENGINES: chromium` in the
  tests step and run `python -m unittest test_vite_build_guarantee test_one_command_vite test_one_command_proxy -v`.
- [ ] **5. GREEN**, then the three mutations, each restored by editing.
- [ ] **6. Gates for the code phase:** `npm --prefix packages/fontkitstudio test`;
  `PYTHONPATH=tests FKS_REQUIRE_FIXTURES=1 python -m unittest test_one_command_vite test_one_command_proxy test_vite_build_guarantee test_support -v`
  (run `npm ci --prefix fixtures/<name>` first in your worktree);
  `python -m ruff check .`. Gate-runners run the rest at landing.
- [ ] **7. Report** with a Handoff: the patch, a `progress.md` event draft, a CHANGELOG
  `[Unreleased]` "Added" draft (the command, the plugin, proxy mode), the commit subject
  `feat(dev): run Studio with the project's Vite or a proxy in one command` and a why-body.

## Report

Code phase: `.superpowers/sdd/r1-pr-b/task-B3b-code-report.md`, patch
`.superpowers/sdd/r1-pr-b/task-B3b-code.patch`. Landing:
`docs/implementation/tasks/r1-task-B3b-report.md`.
