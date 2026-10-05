# R1 B6 brief: dev-only refusals and failure messages

Plan: `docs/plans/2026-10-04-r1-pr-b-sdd.md` (B6, R1.6; After: B3b); what R1 builds:
`docs/plans/2026-10-03-r1-one-command.md` (R1.6). Decision D051 (no page marker; the
terminal line only). Constraints: `.superpowers/sdd/r1-pr-b/constraints.md` (read all of it
first). Read the landed `src/vite-plugin.js`, `src/proxy.js`, `src/run-vite.js`,
`src/run-proxy.js`, `src/cli.js` and `tests/test_one_command_vite.py` first.

## Goal

Every way the one command can fail or surprise a user ends with one plain message that
says what happened and what to do, and the dev-only promise holds where a user can break
it by configuration: a `vite build` with the plugin adds nothing and says so, and a Vite
server opened to the network refuses to run Font Kit Studio. Nothing reaches the user's
page but the one script tag (global rule 4). No bridge change (D051).

## Definition of done

- Each behaviour below has a test that asserts its exact text; each fails if the check
  behind it is removed (mutation evidence for the host refusal, the build line, the CSP
  check and the existing-bridge check).
- A browser test proves rule 4 on the proxied Bootstrap page: the page's body is the same
  as when served directly, and the head gained only the one script tag.
- Messages say "Font Kit Studio", never bare "fontkit" (D040), and never print a stack.

## Owns

Message and refusal code in `packages/fontkitstudio/src/vite-plugin.js`, `src/proxy.js`,
`src/run-vite.js`, `src/run-proxy.js`, `src/cli.js`; a new `src/csp.js`; their Node tests
(`test/vite-plugin.test.js`, `test/proxy.test.js`, `test/csp.test.js`, `test/cli.test.js`);
`tests/test_one_command_messages.py`; the standalone-line assertion in
`tests/test_one_command_vite.py`; one `.gitignore` line (`fixtures/*/.fks-*/`).

## Behaviour (exact texts)

1. **Build.** `apply` becomes a function: `apply(config, { command })` returns
   `command === 'serve'`; when `command === 'build'` it first writes, once per process,
   `Font Kit Studio · dev only: not added to this build` to stdout. Build output stays
   free of Font Kit Studio (B3a's test keeps passing and now also checks the build printed
   that line once).
2. **Network host.** In `configResolved(config)`, a `config.server.host` other than
   `undefined`, `'localhost'`, `'127.0.0.1'` or `'::1'` (so `true`, `'0.0.0.0'`, `'::'`,
   a LAN address) throws
   `Error('Font Kit Studio runs only on localhost; remove --host or server.host to use it')`.
   The command prints that message alone (no stack) and exits 1; Studio is closed first.
3. **Start line.** Standalone plugin mode prints the same two lines as the command,
   indented to sit under Vite's own lines: `  Font Kit Studio · dev only` and
   `  Open: <Studio URL>`. Update `tests/test_one_command_vite.py` so the command run shows
   exactly one `Font Kit Studio · dev only` line and one `Open:` line (the config's
   standalone copy stood down).
4. **A page that already loads the bridge.** When HTML about to be tagged (plugin:
   `transformIndexHtml(html)`; proxy: the buffered page) already contains a `<script`
   whose `src` contains `fontkit-bridge`, the tag is still added (it runs first) and the
   terminal shows once per run:
   `Font Kit Studio: this page also loads its own fontkit-bridge.js. If Studio does not connect, remove that script while you use npx fontkitstudio.`
5. **A CSP that blocks the bridge.** `src/csp.js` exports
   `blocksSameOriginScript(policy): boolean`: take the first of `script-src-elem`,
   `script-src`, `default-src` present (none: false); blocked when it has
   `'strict-dynamic'`, or when it has none of `'self'`, `*`, `http:`. Several policies
   (comma-separated header, several headers, or meta tags) block if any one blocks. The
   proxy checks the `content-security-policy` header and any
   `<meta http-equiv="Content-Security-Policy" content="...">` in a tagged page; the
   plugin checks `server.headers` from the resolved config and meta tags in
   `transformIndexHtml`. Once per run:
   `Font Kit Studio: this page's Content-Security-Policy blocks the bridge (it does not allow the page's own scripts). Add 'self' to script-src while you develop.`
   `Content-Security-Policy-Report-Only` never counts.
6. **Untested Vite major and a non-Vite folder**: B1's and B3b's texts stand; add a CLI test
   for each if B3b did not already assert the full text.
7. **Rule 4.** No new element, attribute or style reaches the user's page; the only
   addition is the script tag.

## Steps

- [ ] **1. Failing Node tests** for 1, 2 (each host value, plus `undefined`, `'localhost'`,
  `'127.0.0.1'`, `'::1'` accepted), 4 (plugin and proxy; printed once across two pages),
  5 (`csp.test.js`: `script-src 'self'` false; `default-src 'self'` false;
  `script-src 'nonce-x'` true; `script-src 'self' 'strict-dynamic'` true;
  `default-src 'none'` true; `script-src-elem 'self'; script-src 'none'` false; two
  policies with one blocking true; empty string false; directive names and keywords
  compared without case), and the proxy and plugin wiring of 4 and 5 (fake configs and
  `config.server.headers`; the proxy against B4's upstream helper). Run: RED.
- [ ] **1b. The host refusal through the real command** (Python, in
  `tests/test_one_command_messages.py`): `require_fixture(self, 'vite-react')`; make a temp
  project inside the fixture, `tempfile.mkdtemp(prefix='.fks-', dir=FIXTURES / 'vite-react')`, removed in
  `addCleanup`, holding a `package.json` that lists `vite` in `devDependencies` and a
  `vite.config.js` with
  `import { fontkitStudio } from '<absolute file URL of packages/fontkitstudio/src/vite-plugin.js>'; export default { plugins: [fontkitStudio()], server: { host: true } };`
  Node and the command resolve Vite from the fixture's `node_modules` one folder up. Run
  `[node, BIN, '--no-open']` there with a 60 s timeout: exit status 1, stderr has the host
  text exactly once and no `at ` stack line, and nothing listens afterwards (the process
  ended). The temp folder name starts with `.fks-` and `fixtures/*/.fks-*` is git-ignored
  (add the line to `.gitignore`).
- [ ] **2. Implement**, flat, with each message a module-level constant exported for tests.
- [ ] **3. Browser test** `tests/test_one_command_messages.py`: start B5's CSP server on
  `fixtures/bootstrap5-static` and B5's Node helper in front of it (as
  `test_one_command_proxy`); load the page directly from the CSP server and through the
  proxy in two pages (block `https://**`); in each, collect
  `[...document.body.querySelectorAll('*')].map(e => e.tagName + '#' + e.id + '.' + e.className)`
  and assert the lists are equal; in the proxied page `document.head` has exactly one
  `script[src="/@fontkit/fontkit-bridge.js"]` more than the direct one and no
  `[data-fontkit-font]`; after Studio connects and a live size edit renders, the body list
  is still unchanged. Then a CSP-blocking variant: a second CSP server instance (add a
  `csp` parameter to `start_csp_server`, default unchanged) with
  `script-src 'nonce-abc'`; the helper's stderr shows the CSP line once and Studio shows
  no connection (its badge does not reach Connected within 5 s; this short wait proves a
  negative and is allowed).
- [ ] **4. GREEN**, then the four mutations, each in the foreground, each restored by
  editing.
- [ ] **5. Gates for the code phase:** `npm --prefix packages/fontkitstudio test`;
  `PYTHONPATH=tests FKS_REQUIRE_FIXTURES=1 python -m unittest test_one_command_messages test_one_command_vite test_one_command_proxy test_vite_build_guarantee test_support -v`;
  `python -m ruff check .`.
- [ ] **6. Report** with a Handoff: the patch, a `progress.md` event draft, CHANGELOG
  wording for the refusals if the command's "Added" line needs it, the commit subject
  `feat(dev): explain every refusal and keep the command off the network` and a why-body.

## Report

Code phase: `.superpowers/sdd/r1-pr-b/task-B6-code-report.md`, patch
`.superpowers/sdd/r1-pr-b/task-B6-code.patch`. Landing:
`docs/implementation/tasks/r1-task-B6-report.md`.
