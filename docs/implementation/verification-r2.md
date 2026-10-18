# R2 (0.4.0) release-point verification

Date: 2026-10-18. Branch: `feat/r2-visited-pages` (PR #24); base `fdb48d0` (PR B2 merged).
Status: release point prepared; not yet merged, tagged or published.
This evidence covers the settled PR C tree: the code at `d49158b` (the last code commit) plus the release-point docs
committed after it. Earlier R2 evidence: [PR A](verification-r2-pr-a.md); PR B and PR B2 are recorded in the ledger.

## Environment and preparation

Windows, Python 3.13.3, Node 24.16.0, npm 10.8.2. Playwright 1.62.0, Ruff 0.16.10, pre-commit 4.6.2. Chromium and
Firefox installed. Every fixture was installed in the checkout before the browser gates, so
`FKS_REQUIRE_FIXTURES=1` held (a missing fixture fails instead of skipping):

```powershell
npm ci --prefix fixtures/vite-react
npm ci --prefix fixtures/vite7-react
npm ci --prefix fixtures/vite-ts
npm ci --prefix fixtures/next-app
npm ci --prefix fixtures/vite-react-css-modules
```

## Release-freeze gates (local, one run on the frozen tree)

The source was frozen with every PR C slice applied. Each gate ran once, in the foreground, through the workspace gate
script with `PYTHONPATH=tests`, `FKS_ENGINES=chromium` (Firefox for the canary), `FKS_REQUIRE_FIXTURES=1` and
`NEXT_TELEMETRY_DISABLED=1`.

| Gate | Command | Result |
|---|---|---|
| Static and provenance | `python scripts/verify.py --static-only` | pass; provenance PASS; browser tests SKIP by design |
| Bridge syntax | `node --check fontkit-bridge.js` | pass |
| Product-tree lint | `python -m ruff check . --exclude .agents` | All checks passed |
| Whitespace | `git diff --check` and `git diff --cached --check` | pass |
| Chromium suite, six shards | `python -m unittest <modules> -v` per shard | 1,269 tests OK: 152, 180, 124, 142, 164 and 507 |
| Node package | `npm --prefix packages/fontkitstudio test` | 269 pass, 0 fail, 2 skipped |
| Frontend gate | `python scripts/dev/frontend_gate.py --engines chromium,firefox` | 30 of 30 runs; blocking 7 of 7 pass; 354 advisory REPORT lines (touch targets), 0 SKIP, 0 FAIL |
| Firefox canary (advisory, D037) | `python -m unittest firefox_canary -v` with `FKS_ENGINES=firefox` | 54 tests OK (51 before PR C plus three role smoke methods) |
| Commit messages | `python scripts/dev/check_commit_messages.py --range origin/main..HEAD` | OK on every PR C commit |

Exact Ruff (`python -m ruff check .`) still reports only the findings in the owner's untracked `.agents/` skills; the
product tree is clean.

The two Node skips are the same two no-project cases as at 0.3.1 ([verification](verification-0.3.1.md)): a
`package.json` above the temporary directory prevents that environment. Not product failures.

One intermittent failure: in the first shard-5 run,
`test_preview_server.PreviewServerLifecycleTest.test_open_flag_opens_the_studio_url_once` saw no browser launch
(`[] != [url]`) while five gate runners loaded the machine. Shard 5 then passed on the same tree (164 tests OK). The test
stops the server right after start and assumes `--open` has already launched the fake browser; under load that
assumption can fail. It is a test timing defect, not a product defect, and hosted CI passed it on every head. Fixing it
(wait for the browser log by condition) is follow-up work.

## Wave gates before the freeze

Every slice was reviewed on its own (brief review, task review and a scoped re-review of each follow-up), then landed in
waves, each gated on the integrated tree:

- W1 (version tolerance in Studio, route announcements in the bridge, entrypoint round trips, forwarder removal):
  614 focused tests in four runs, plus static, syntax, lint and whitespace.
- W2 (route observation, the visited-page inventory): 757 focused tests in four runs, plus the same fast gates.

## Hosted CI (job `quality-gate` and the fixture matrix)

| Head | Run | Result |
|---|---|---|
| `bd20e43` | 39145209339 | 12 of 12 jobs pass; 1,164 Chromium tests OK |
| `2b70e29` | 39153693305 | 12 of 12; 1,211 OK; the entrypoint classes run with no skips in the fixtures and Next.js jobs |
| `5d28252` | 39168572891 | 12 of 12; 1,269 OK; frontend gate 30 of 30; Firefox canary 51 |
| `d49158b` | 39171108206 | 12 of 12; 1,269 OK; frontend gate 30 of 30; Firefox canary 54 (the three role smoke methods included) |

In job `quality-gate` the main suite skips 26 installed-fixture cases by design (its fixtures are installed in later
steps or other jobs); each is run, with installs required, by the job that installs its fixture: the Vite 7 and 8
matrix (Vite command, plugin, build, types and the role entrypoint round trips), the Next.js job and the React
CSS-module step. The only advisory is the Node.js 20 deprecation notice for `actions/setup-python@v5` and
`actions/upload-artifact@v4`, left to a separate workflow change.

## Known limits shipped in 0.4.0

Documented in the README's Detected roles section: a Bootstrap 5 body or monospace receipt measures only its own
selectors; a component with its own size rule keeps its size under a Body role; a later author `body {}` rule of equal
specificity wins; an element that declares the font variables again shows the same blind spot; app code that cached the
native history methods before the bridge connected bypasses the route wrapper until the next Detect, Apply or Clear; a
CSSOM `insertRule` without a DOM change needs Detect again; Studio's own fullscreen and device-width buttons count as a
page change; a strict `style-src` blocks the role sheet; visited-page evidence is session-only and per origin. Real
back/forward-cache restores cannot be produced under Playwright, so those bridge tests prove the handler wiring with
dispatched events.

## Owner release steps

1. Review and merge PR #24.
2. Tag the merge commit `v0.4.0` (annotated) and push the tag; approve the `npm-release` environment.
3. After publication: `npm view fontkitstudio@0.4.0`, `npx -y fontkitstudio@0.4.0 --version` from an empty folder,
   the provenance attestation, and the release assets' SHA-256 against
   `git -c core.autocrlf=false archive v0.4.0 fontkit-studio.html fontkit-bridge.js`.
