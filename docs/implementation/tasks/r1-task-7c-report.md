# Task 7c code report (mode: code)

Changed: packages/fontkitstudio/src/csp.js, src/vite-plugin.js, src/proxy.js, test/csp.test.js,
test/vite-plugin.test.js, test/proxy.test.js. Patch: task-7c-code.patch (apply -R check passes).

## What
- csp.js: `blocksSameOriginScript(policy, pageOrigin?)`. New host-source matching (scheme http only or
  none, exact host, port equal / `:*` / default 80, path none / `/` prefix / exact bridge path);
  malformed or non-http page origin or unparsable source = no match (warning stays). strict-dynamic
  still blocks. Without origin, behaviour unchanged.
- proxy.js: passes `proxyOrigin` (the page is served from the proxy).
- vite-plugin.js: header policies are kept (not pre-evaluated); at `transformIndexHtml`, headers plus
  the page's meta policies are checked together with the origin of `server.resolvedUrls.local[0]`
  (stored from `configureServer`). That is the address Studio's Open line uses (`started.url(local)`),
  i.e. the one the browser loads. Before listen / middleware mode there is no origin, so it behaves as before.

## Evidence
- RED (src files reset to BASE, new tests kept): `node --test` on the three test files: fail 16
  (10 csp allows, 3 other csp, 2 plugin, 1 proxy "naming the proxy's origin"); GREEN: fail 0.
  (Blocking tests pass on old code by design: old code blocked everything.)
- Mutations (each fail > 0, restored): drop port compare 5; drop scheme check 2; drop path rule 3;
  plugin passes no origin 2.
- `npm --prefix packages/fontkitstudio test`: pass 243, fail 0, skipped 2.
- `npm ci` run in worktree for fixtures/vite-react and vite7-react; `PYTHONPATH=tests python -m unittest
  test_one_command_vite test_one_command_proxy`: Ran 6, OK.
- `python -m ruff check .`: All checks passed. pre-commit (via python -m pre_commit): whitespace and
  node --check passed; ruff/static skipped (no files). test_support not run: no tests/*.py edited.
- Full Python suite not run (brief did not ask; diff touches only the package).

## Self-review
AP 1-4: trust boundary hostile cases covered (wrong port/host/scheme/path, wildcard, garbage, strict-dynamic,
multi-policy). AP 13: no processes left. Nothing written to user projects. Zero deps kept.

## Handoff
- CHANGELOG (Unreleased, `### Fixed`): "The CSP warning no longer fires for a `script-src` that names the
  dev server's own address (the proxy still warns for the target's address, since the page comes from the proxy)."
- progress.md event: "R1 7c: CSP warning skips policies naming the page's own origin (plugin: first
  resolvedUrls.local; proxy: proxyOrigin); 4 mutations shown failing; node tests 243 pass."
- Commit subject: `fix(dev): stop the CSP warning for a policy that allows the bridge`
  Body: A script-src naming the dev server's own origin allows the bridge, but the warning told users to
  change a fine policy. Match host-sources against the page origin (http only, exact host, port, bridge
  path); anything malformed still warns. The proxy passes its own origin, so a policy naming the target
  still warns.

## Fix round 1 (review Minor 1: path case)
- csp.js: only directive names and keywords (`'self'`, `*`, `http:`, `'strict-dynamic'`) are lowercased
  now; in a host-source the scheme and host compare without case and the path keeps its case.
- Tests added to the csp blocks list: `localhost:5173/@FONTKIT/` and `/@fontkit/Fontkit-Bridge.js`.
- RED (mutation: lowercase the path again): `node --test test/csp.test.js` fail 2 (those two cases).
  GREEN: `npm --prefix packages/fontkitstudio test` pass 245, fail 0. ruff clean. Patch regenerated, apply -R check ok.
