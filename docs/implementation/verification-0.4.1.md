# 0.4.1 release verification

Date: 2026-11-07. Branch: `fix/v0.4.1-repairs`, pull request #30.
Status: released (2026-11-07). Publication evidence is in [Publication checks](#publication-checks-2026-11-07).

This record covers the final source tree, gated before its commits landed. The commits apply that tree, and each code file's blob was compared with it. The release commit adds this record and bookkeeping only.

## Environment

Windows 11, Python 3.13.3, Node 24.16.0. Playwright 1.62.0, Ruff 0.16.10, pre-commit 4.6.2. Chromium only for the local runs below.

## Local gates on the final tree

The suite ran as six shards on a clean worktree, with `FKS_REQUIRE_FIXTURES=1`.

| Shard | Tests | Result |
|---|---|---|
| 1 | 155 | pass |
| 2 | 204 | pass |
| 3 | 140 | pass |
| 4 | 147 | pass |
| 5 | 171 | 5 failed, see below |
| rest | 616 | 23 failed, see below |
| **Total** | **1,433** | **1,405 passed, 28 failed** |

Of the 28 failures:

- **27 did not run.** Each is a fixture test that stopped on `fixtures/<name>/node_modules is missing`, because that worktree has no installs and the setting turns a skip into a failure. They are not reported as passing here. Hosted CI installs the fixtures and runs them.
- **1 is an intermittent failure under load.** `test_detect_never_drops_the_preview_between_frames_on_the_5000_parent_corpus` ended as `time-budget` at 2,014 ms against the 2 s scan budget, with five other shards running. Alone on the same tree it passed 3 of 3. The bridge differs from the previous green run only in its version comment. This is the older large-page weakness carried to 0.4.2 in [plan Addendum 4](../plans/2026-11-06-v0.4.1-repairs.md#carried-to-042).

One test changed after these gates: `test_an_edit_made_while_the_write_is_in_flight_still_asks` now awaits the held request instead of polling for it. No product code changed. `test_studio_guards` (35 tests) and `test_support` (34) pass with it, and the test passes 5 of 5 at CPU rate 40.

Other local checks on the same tree:

| Check | Command | Result |
|---|---|---|
| Static, provenance | `python scripts/verify.py --static-only` | pass; browser tests skipped by the flag |
| Bridge syntax | `node --check fontkit-bridge.js` | pass |
| Ruff, product tree | `python -m ruff check . --exclude .agents` | pass |
| Whitespace | `git diff --check` and `git diff --cached --check` | pass |
| Node package | `npm --prefix packages/fontkitstudio test` | 272 tests: 270 pass, 0 fail, 2 skipped |

The two Node skips are the no-project cases, which a `package.json` above the temporary folder prevents here, as at 0.3.1.

Not run locally: Firefox, the frontend gate on the final tree (it ran for the theme control, 15 of 15 Chromium runs), and fixture dev servers. Hosted CI runs all three.

## Hosted CI

Last full run before the final commits: `1b86000`, run 42331337578: 12 of 12 jobs, 1,422 tests with 27 skipped in the main job, frontend gate 30 of 30 runs, Firefox canary passing as an advisory. The 27 fixture tests run in the Fixtures and Next.js jobs. The final head's run is under Publication checks.

## Slow-runner checks

A failure seen only on a Linux runner led to CPU-throttled runs of the tests this branch added. The leave-prompt, stale Clear and animation tests pass at rates up to 20 to 40. Whole-module runs of `test_studio_live` and `test_studio_roles` at rate 20 were stopped for time, so only their new classes were throttled.

## Real-app rerun

Run read-only at `c0c4af6`.

- A Flask, Jinja, Tailwind and DaisyUI app: the first Detect reached 19 roles from 53 parents in 5 of 5 fresh connections.
- A Next.js 16 and shadcn production build: 15 of 15 acknowledged Clears were accepted, against 3 of 8 refused at 0.4.0.
- Not reached on a real app: `edit-reapply-stopped`. The page never re-created an element in a loop, so only its tests cover it.

This rerun predates the Sync warning change, the leave prompt rework, the unacknowledged-edit prompt, the composition carry, the theme control and the row change. None of them was rerun on either app. Each has its own tests in a real browser.

## Unchanged versions

The export format stays at `0.1.1` and the bridge protocol at version 1. Asserted at the release point.

## Known limits

The limits this release accepts, and the items carried to 0.4.2, are in [plan Addendum 4](../plans/2026-11-06-v0.4.1-repairs.md#carried-to-042).

## Publication checks (2026-11-07)

Pull request #30 merged at `eb1fe6a`, whose tree is identical to the checked head `f872881`. Annotated tag `v0.4.1` targets that merge.

**Final hosted runs.** Pull request head `f872881`, run 42338655241: 12 of 12 jobs, 1,433 tests with 27 skipped in the main job, frontend gate 30 of 30 runs, Firefox canary passing as an advisory. The fixture tests the local run could not reach ran in the Fixtures and Next.js jobs. Merge on `main`, run 42340346772: success. Release run 42340358812: all gates, then `publish`, success.

**npm.**

- `npm view fontkitstudio@0.4.1` serves the version, and `latest` is `0.4.1`. The registry lagged the publish by under a minute.
- Integrity `sha512-5iWFaQ/e4LTcRm+ovJrpCB/f+48/19B1gxie6qnjFEoLp/Z4DyBBYA/uYcOBoaDtSoBRuXF5oGdONpvFfAxY3g==`.
- Provenance: an SLSA v1 attestation on the registry entry, and the publish log records the statement in the transparency log.
- `npx -y fontkitstudio@0.4.1 --version` from an empty folder prints `0.4.1`, exits 0 and leaves the folder empty.
- Runtime dependencies: none.

**Release assets.** The GitHub release `v0.4.1` is published and not a prerelease. Each asset was compared with `git -c core.autocrlf=false archive v0.4.1`, and the Studio and bridge inside the npm package with the same files.

| File | SHA-256 | Release asset | npm package |
|---|---|---|---|
| `fontkit-studio.html` | `32012029c7a4f66e085e67b2ef3f63898c323329be4adc172f112e146ced2e1a` | match | match |
| `fontkit-bridge.js` | `79be2fee3911defb3b85257150bab447869433bc8e05e83b46c9d32395f05acb` | match | match |
| `serve.py` | `b62ca6a5c1b5bba26a031eb3942c19245e5f0634ec55d4694b76aa155489797a` | match | not in the package |
