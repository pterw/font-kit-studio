# R1 (0.3.0) release-point verification — 2026-10-04

Gate evidence for the 0.3.0 release point: R1 PR C (PR #12, plan
`docs/plans/2026-10-04-r1-pr-c-sdd.md`) on top of PR A (#8) and PR B (#10). The
gates checked what they found and changed nothing.

## Artifact and environment

- **Tree under test:** commit `320c601` (`320c601d766230ea84aefaf1317a1023a863d239`, "chore: version 0.3.0"), with
  the full gates run on that exact tree before it was committed. The commit after it,
  which removes a race between two Node test files (`tasks/r1-task-9a-rereview3.md`), is
  test and workflow only. It was gated with the Node tests, `test_release`, `test_support`
  and ruff.
- **Local machine:** Windows 11, 8 cores, Python 3.13.3, Node v24.16.0 (npm 10.8.2),
  Playwright (Python) 1.62.0 with its Chromium and Firefox.
- **CI:** GitHub Actions, the Quality Gate workflow on PR #12. Linux runs the Python suite
  and the frontend gate. The Node package runs on Node 22, 24 and 26 on Linux and Node 24
  on macOS and Windows (D043). The Vite fixtures job runs on the same five cells, and the
  Next.js fixture job on Linux with Node 24.
- **SHA-256 of the release files** at `320c601`, from the git blobs, so with LF line
  endings, as `git -c core.autocrlf=false archive v0.3.0` gives them:

| File | SHA-256 |
|---|---|
| `fontkit-studio.html` | `6b2b903298258edae59545a70b1c0031949c8f54142696fdb4c68a3d6ab85bb9` |
| `fontkit-bridge.js` | `1463b6c13b321ed23ae54744b42ffeb3a86d3f81afbfbc4f2e6c310e937c4f80` |
| `font_kit_studio_v0.1.1.html` (forwarding stub, D041) | `2952ce1f002336cf1a91bef997f919d1c8c1ab55d755553834cb2fab6f062755` |
| `packages/fontkitstudio/package.json` | `3b0359ca93ffef3ebe907fce9580e57dcb2346abcc8e814a52606a163cf40454` |

## Exact commands

```bash
python scripts/verify.py --static-only
node --check fontkit-bridge.js
npm --prefix packages/fontkitstudio test
python -m ruff check .
FKS_REQUIRE_FIXTURES=1 python -m unittest discover -s tests -p "test_[a-r]*.py"
FKS_REQUIRE_FIXTURES=1 python -m unittest discover -s tests -p "test_[s-z]*.py"
python scripts/dev/frontend_gate.py
PYTHONPATH=tests FKS_ENGINES=firefox python -m unittest firefox_canary -v
python scripts/dev/check_commit_messages.py --range origin/main..HEAD
cd packages/fontkitstudio && npm pack --dry-run --json
```

Every fixture was installed with `npm ci` (`vite-react`, `vite7-react`, `vite-ts`,
`next-app`), so `FKS_REQUIRE_FIXTURES=1` made each fixture test run, never skip. The suite
ran in two halves, in parallel with the other gates on the same machine.

## Gate results (local, Windows 11)

| Gate | Result |
|---|---|
| Static checks (ids, inline JS, provenance) | PASS |
| Bridge syntax | PASS |
| Node package tests | PASS: 250 tests, 248 pass, 0 fail, 2 skipped (two `project.test.js` cases skip when a `package.json` sits above the temp folder, as on this machine; CI runs them) |
| Ruff | PASS |
| Python suite, first half (`test_[a-r]*`) | PASS: 471 tests in 355 s |
| Python suite, second half (`test_[s-z]*`) | PASS: 384 tests in 522 s |
| Frontend gate | PASS: 30 of 30 planned runs; blocking 7 of 7; 0 FAIL, 0 ADVISORY lines |
| Firefox canary (advisory, D037) | PASS: 49 tests |
| Commit messages | PASS (run on the final range before the PR leaves draft) |

So 855 Python tests and 250 Node tests pass in Chromium, against 788 Python tests on
`main` before R1 PR B.

## The one command, by fixture

| Fixture | What is proven | Where |
|---|---|---|
| `fixtures/vite-react` (Vite 8.3.2, React 19.3.0) | The command and the permanent plugin connect Studio; one bridge tag; a live edit renders; a CSS hot update keeps the edit and the connection; `vite build` holds no bridge | `test_one_command_vite`, `test_vite_build_guarantee` |
| `fixtures/vite7-react` (Vite 7.3.6) | The same on the previous Vite major | `test_one_command_vite`, `test_vite_build_guarantee` |
| `fixtures/bootstrap5-static` behind a `script-src 'self'; style-src 'self'` CSP | Proxy mode: Studio connects and edits with no CSP violation; the page's CSP header passes unchanged; the body gains only the one tag | `test_one_command_proxy`, `test_one_command_messages` |
| `fixtures/next-app` (Next 16.3.8, React 19.3.0) | Proxy mode in front of `next dev`: a live edit applies; a CSS edit arrives by hot update over the WebSocket pass-through without a reload; Studio keeps editing after it; no hydration warning | `test_one_command_next` |
| `fixtures/vite-ts` (create-vite 9.2.1's react-ts config, TypeScript 6.0.3) | A strict `vite.config.ts` that uses `fontkitStudio()` type-checks; a wrong use fails with TS2322 | `test_vite_types` |

## Friction test

The time from starting `npx fontkitstudio` on the Vite fixture, with stdin closed, to a
connected Studio showing the page's title.

- **CI**, first green fixtures run (run 37255139023, head 60accb0):

| Cell | Time |
|---|---|
| Linux, Node 22 | 0.6 s |
| Linux, Node 24 | 0.4 s |
| Linux, Node 26 | 0.6 s |
| macOS, Node 24 | 0.5 s |
| Windows, Node 24 | 0.8 s |

- **Local:** 1.2 to 4.6 s, depending on other load on the machine.
- **Budget** (R1 plan, question 4): 2 s in CI, which is the slowest cell plus 50 percent,
  rounded up; 10 s locally.

## The npm tarball

`npm pack --dry-run --json` in `packages/fontkitstudio` at `320c601`, from the Windows
checkout. The published tarball comes from CI and is measured again there, with its
integrity and provenance recorded after the publish.

- 16 files, 133,146 bytes packed, 492,918 unpacked.
- Files:
  - `LICENSE`, `README.md`, `package.json`;
  - `bin/fontkitstudio.js`;
  - `src/cli.js`, `src/csp.js`, `src/open-browser.js`, `src/project.js`, `src/proxy.js`,
    `src/run-proxy.js`, `src/run-vite.js`, `src/studio-server.js`, `src/vite-plugin.js`,
    `src/vite-plugin.d.ts`;
  - `dist/fontkit-studio.html`, `dist/fontkit-bridge.js`.
- No dependencies, no `test/`, `scripts/` or fixture files. A Node test pins this list
  exactly.

## What was not run, and what waits on the owner

- **Not run locally:** the Firefox frontend-gate profiles beyond what the gate runs by
  default; physical phones; Linux and macOS (CI covers them).
- **The publish itself has not run.** The owner, in order:
  1. Creates the `npm-release` environment, with the owner as required reviewer and
     deployments limited to `v*` tags (commands in `tasks/r1-task-9a-report.md`).
  2. Merges PR #12.
  3. Tags the merge commit `v0.3.0` (annotated) and pushes the tag.
  4. Approves the publish job.

  The provenance attestation (`npm view fontkitstudio@0.3.0 dist.attestations`) is recorded
  in the ledger after that.
