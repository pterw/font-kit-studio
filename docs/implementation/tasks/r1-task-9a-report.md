# Task 9a code report (mode: code)

Worktree `C:/fks/t9a`, BASE 7feaaf9. Patch: `task-9a-code.patch` (4 files, 350 insertions; `git apply --check -R` passes).
Files: `.github/workflows/release.yml` (new), `scripts/dev/release_notes.py` (new), `tests/test_release.py` (new), `packages/fontkitstudio/test/package.test.js` (tarball test added; 8a's tests kept).

## Per brief step
- release.yml: done, binding shape; no top-level concurrency; values via `env:` (TAG from `github.ref_name`); no `secrets.`/token words; actions at checkout@v4, setup-node@v4 (same majors as the gate).
- release_notes.py: done (stdlib; exit 1 / exit 2 as specified; accepts `0.3.0`, `v0.3.0`, pre-release suffix; LF UTF-8 out).
- tests: done. tarball test builds the expected list from the `bin/` and `src/` listings (all entries, so a stray file type fails it).
- **quality-gate.yml: DEFERRED TO LANDING** (shared file; code mode may not edit it). See Handoff for the edit. Consequence: in this worktree `test_release.QualityGateIsCallableTests` fails (that is its RED). I checked its GREEN by applying the edit to an in-memory copy and parsing it: `workflow_call` present -> True. The controller must land the quality-gate edit with this patch.
- actionlint: not installed, not downloaded; the parse test is the check.

## Evidence
- RED of the gate test: `PYTHONPATH=tests python -m unittest test_release test_support` -> 1 failure, `'workflow_call' not found in {'push':..., 'pull_request': None, 'workflow_dispatch': None}`. (The other new tests were written with the code; their RED is the mutations below, each shown failing, then restored.)
- Mutations (each restored, tree confirmed clean after):
  - top-level `id-token: write` -> `test_top_level_permissions_only_read` fails.
  - publish without `environment` -> `test_publish_waits_for_the_gates_and_the_owner` errors.
  - `release` `needs: gates` -> `test_release_waits_for_the_publish` fails.
  - release_notes accepting undated section -> first attempt (`if False:`) was NOT caught: the crash traceback happened to contain "date". Fixed the test (stderr must be exactly one line containing "no ISO date"); re-ran the real mutation (date check replaced by `pass`): 3 subtests fail (no date, "soon", month 13). Restored: 8 pass.
  - `"test/"` in package.json `files` -> `declares what npm needs...` and `the tarball holds exactly the shipped files` both fail.
- GREEN: `PYTHONPATH=tests python -m unittest test_release test_support` -> 53 tests, 1 failure (only the deferred gate test; passes once the gate edit lands).
- `npm --prefix packages/fontkitstudio test` -> `ℹ tests 250`, `ℹ pass 248`, `ℹ fail 0` (2 skipped, pre-existing).
- `python -m ruff check .` -> All checks passed. Full suite not run (brief names the focused runs only; patch touches tests, a script, a workflow and a node test).
- pre-commit (`--files` the 4 changed, staged): whitespace Passed, ruff Passed, node --check Passed, static checks Skipped (no files).
- No fixture `npm ci` needed (no fixture test used). `prepack` writes `dist/` and `LICENSE` in the worktree; both are untracked-ignored, not in the patch.
- No process started, nothing published, no network use.

## Reading the gate on a tag push
- "Check commit messages": event `push`, `before` is zeros, `git cat-file -e` fails, so it runs `check_commit_messages.py` on the last commit (the tagged one). Still checks something; no change.
- "No trailing whitespace": event `push`, `cat-file` fails, no `else`: it runs nothing and passes vacuously. It fails nothing, and the same lines were checked on the pull request, so I recommend no change. (Optional if you want: an `else git diff --check "${SHA}^" "${SHA}"`; not done, out of scope.)
- Called-run facts: `github.workflow`/`github.ref` in the gate's concurrency group are the caller's (`Release`, the tag ref); `cancel-in-progress` is false for push. The gate declares `permissions: contents: read`, within the caller's grant.

## Self-review (anti-patterns)
- AP 13: no servers/children started except subprocess runs that exit; temp changelog dirs removed via addCleanup. AP 15: no process state in files. D040: no bare "fontkit" in user-facing text (release title is the tag). Rule 8 (zero deps): nothing added to the package; PyYAML is dev-only and already installed. Ruling 7: files LF (checked via `file`). Rule 9: grepped nothing renamed.
- Concern: the test reads the repo's quality-gate.yml, so patch alone leaves one test red until the gate edit is applied.
- Concern: the `release` job runs `python` on ubuntu-latest's default Python (no setup-python); release_notes.py is stdlib and 3.8+-safe.

## Handoff
**quality-gate.yml edit (controller):** in `on:`, after `workflow_dispatch:` add
```yaml
  # The release workflow runs these same gates on a version tag (R1 9a).
  workflow_call:
```
No other change needed.

**Owner steps (PowerShell, once; needs repo admin `gh auth`).**
```powershell
$id = gh api users/pterw --jq .id
$body = @{ reviewers = @(@{ type = 'User'; id = [int]$id }); deployment_branch_policy = @{ protected_branches = $false; custom_branch_policies = $true } } | ConvertTo-Json -Depth 5
$body | gh api -X PUT repos/pterw/font-kit-studio/environments/npm-release --input -
'{"name":"v*","type":"tag"}' | gh api -X POST repos/pterw/font-kit-studio/environments/npm-release/deployment-branch-policies --input -
```
Check: `gh api repos/pterw/font-kit-studio/environments/npm-release --jq '{reviewers: [.protection_rules[].reviewers[].reviewer.login], policy: .deployment_branch_policy}'` shows `pterw` and `custom_branch_policies: true`; `gh api repos/pterw/font-kit-studio/environments/npm-release/deployment-branch-policies --jq '.branch_policies[] | [.name,.type]'` shows `v*`, `tag`. Trusted publisher on npmjs.com (R1.0): repository `pterw/font-kit-studio`, workflow `release.yml`, environment `npm-release`.

**Ledger (progress.md draft):** "R1 9a: `release.yml` added. A `v*` tag push runs the quality gate (called via `workflow_call`), then `npm publish` from `packages/fontkitstudio` under the owner-approved `npm-release` environment (OIDC trusted publishing, provenance, no token), then `gh release create` with the CHANGELOG section (`scripts/dev/release_notes.py`) and Studio plus the bridge attached. `tests/test_release.py` parses both workflows; the package test pins the tarball file list. Nothing published; owner creates the environment (steps in the 9a report)."

**Commit:** `ci: publish to npm from a v* tag after the gates`
Body draft: "A v* tag now runs the same gates a pull request runs, then waits for the owner to approve the npm-release environment, publishes by trusted publishing (OIDC, provenance, no token) and makes the GitHub Release from the tagged files and that version's CHANGELOG section. quality-gate.yml gains workflow_call so the tag run reuses it. Tests parse both workflows (permissions, needs, environment, no tokens, no expressions in scripts) and pin the tarball's file list."

## Fix round 1
1. **Tag check tested.** `test_tag_must_equal_the_package_version_before_publishing`: exactly one step reads package.json and has `exit 1`, it precedes `npm publish`, `env == {TAG: ${{ github.ref_name }}}`, and the run text contains `[ "$TAG" != "v$version" ]`. Mutation: step removed -> that test fails; restored.
2. **Notes check before publish.** New publish step "Check the CHANGELOG has this version's section" runs `python3 scripts/dev/release_notes.py "${TAG#v}" > /dev/null` (TAG via env). `test_changelog_section_is_checked_before_publishing` pins order and env. Mutation: step replaced by `echo skipped` -> fails; restored. The release job still writes notes.md.
3. **SHA pins.** Read-only `gh api repos/<r>/git/ref/tags/v4`: both are lightweight tags (type commit, no dereference needed). checkout `11d5960a326750d5838078e36cf38b85af677262 # v4`; setup-node `49933ea5288caeca8642d1e84afbd3f7d6820020 # v4`. `test_every_action_is_pinned_by_commit_sha` checks each step `uses` is `owner/name@<40 hex>`, and that `gates.uses` is the local workflow. Mutation: one pin reverted to `@v4` -> fails; restored. quality-gate.yml untouched.
4. **jq.** Handoff command now uses `reviewers[]?`: `gh api repos/pterw/font-kit-studio/environments/npm-release --jq '{reviewers: [.protection_rules[].reviewers[]?.reviewer.login], policy: .deployment_branch_policy}'`. Re-checked with jq on a protection_rules array holding a `branch_policy` entry without `reviewers`: prints `["pterw"]`, no error. (Also: `gh api repos/pterw/font-kit-studio --jq .private` -> false, so the repo is public and automatic provenance applies.)

Other Minors: 2 and 3 fixed in release_notes.py (trailing `[x]: url` definitions and whitespace-only leading lines are dropped; two new tests; `release_notes.py 0.1.1` on the real CHANGELOG now ends at the section's last line). 4 fixed: both jobs call `python3`. 5, 6 and the npm@^11.5.1 range: left as is (5 stricter test kept; 6 optimisation; range is the brief's).

Runs: `test_release test_support` 58 tests, 1 failure = QualityGateIsCallableTests (still waits for the landing edit). Node tests 248 pass, 0 fail. ruff clean. pre-commit on the staged files passes. Patch regenerated (`git apply --check -R` ok). Handoff otherwise unchanged; the release job's `python` is now `python3`.

## Fix round 2 (CI)
Worktree `C:/fks/t9a2` at 2014319. Patch: `task-9a-fix2.patch` (git diff --binary from 2014319; 3 files; `git apply --check -R` ok).

**1. Does npm 11 skip prepack on `pack --dry-run`? No; I could not read a docs page (no web fetch tool), so I read npm's own source.** I fetched `npm@11.21.0` (`npm pack npm@11`, a read-only download) and read `node_modules/libnpmpack/lib/index.js`: for a directory spec, `prepack` runs whenever `!opts.ignoreScripts`, before the tarball is built, and `dryRun` only decides whether the file is written. `lib/commands/publish.js` (11.21.0) packs through the same libnpmpack, so `npm publish` runs prepack too (it also runs prepublishOnly/publish/postpublish). Measured with `npx -y npm@<v> pack --dry-run --json` in the package with dist/ and LICENSE removed: 11.5.1, 11.6.0, 11.8.0, 11.12.0, 11.19.1 (CI's npm) and 11.21.0 all list 16 files including LICENSE and both dist files. With `--ignore-scripts` and nothing bundled: 13 files, none of the three. With the bundle run first, then `--ignore-scripts`: 16 files.

**Real cause of the CI failure: a race in the tests, not npm.** CI log (job 111594960626, npm 11.19.1) shows the tarball missing exactly LICENSE and both dist files. `node --test` runs test files in parallel; `bundle.test.js` "running the script through a directory link still bundles" does `rmSync(dist)` and `rmSync(LICENSE)` in the real package directory, and `package.test.js` packed that same directory, so prepack's output could be deleted before the tarball was read. Node 26 only changed the timing. The published 0.3.0 is not at risk from this: publish runs prepack right before reading files, with nothing racing it.

**2. release.yml.** New publish step "Bundle Studio and the bridge" (`working-directory: packages/fontkitstudio`, `npm run prepack`) before `npm publish`; it also fails on a label mismatch earlier. Test `test_studio_is_bundled_before_publishing` (step exists, in the package directory, precedes publish). Mutation: step changed to `echo skipped` -> the test fails; restored.

**3. package.test.js.** The tarball test now packs a scratch copy (root files, `bin/`, `src/`, `scripts/`, `package.json`, `README.md`) in a temp repo layout, runs `node scripts/bundle.js` explicitly, then `npm pack --dry-run --json`; exact list assertion kept. Isolated from the real dist/, so the race cannot hit it. Run with the real dist/ and LICENSE deleted: passes. Also fixed a flaw in my earlier version: the expected list came from every entry in `src/` and `bin/`, so a stray file could never fail it; it now keeps only `*.js` and `*.d.ts` as the brief said. Mutation: `src/stray.txt` -> fails; removed. (A `test/` entry in `files` is caught by "declares what npm needs", not here, since the copy has no test/.)

**Runs.** `test_release test_support`: 59 tests OK (quality-gate test passes here because 2014319 has `workflow_call`). Node tests: 248 pass, 0 fail. ruff clean. pre-commit on the changed files passes. No registry or GitHub writes; the only network use was the npm package download and `gh run`/`gh api` reads.
Note: the worktree checked out CRLF; the patch is made from the index (LF).

## Fix round 3 (the race class)
Worktree `C:/fks/t9a2`. `task-9a-fix2.patch` regenerated from 2014319 (8 files, `git apply --check -R` ok).

**Audit.** Grepped every Node test for writes, deletes or copies touching dist/ or LICENSE. Real-directory writers found: `bundle.test.js` "running the script through a directory link" (deleted dist/ and LICENSE, then bundled into them), `bundle.test.js` "npm pack ships ..." (ran prepack, so rewrote them, via `copyFileSync`, which truncates first and so can expose an empty file to a parallel reader), and `cli.test.js` `before()` (called `bundle()` when dist/ was missing). `package.test.js` was fixed in round 2. Nothing else touches them (the other hits are `node_modules/vite/dist` fixtures and temp copies).

**Changes.**
- New `test/helpers/scratch-package.js`: a scratch repository (root Studio, bridge, LICENSE; package copy under `packages/fontkitstudio` without dist/ and LICENSE). `bundle.js` resolves its repo root as `../..`, so the layout is needed rather than an output option.
- `bundle.test.js`: both real-directory tests now use the scratch package; the link test also asserts the scratch copy starts without dist/ and LICENSE, and compares with the scratch root's files. `package.test.js` uses the same helper.
- `cli.test.js`: `before()` no longer bundles; it asserts dist/ exists with a message. To keep `npm test` working from a clean checkout, the package's test script is now `node scripts/bundle.js && node --test test/*.test.js` (the script, not a test, writes the real dist/, once, before any test file starts). README and CONTRIBUTING use `npm --prefix packages/fontkitstudio test`, unchanged. Running `node --test` on cli.test.js alone with no dist/ now fails with the message instead of writing.
- Guard: `test/helpers/real-bundle-guard.js` `guardRealBundle()`, called at the top of `bundle.test.js`, `cli.test.js` and `package.test.js`. It snapshots the real LICENSE and every dist/ file (name, bytes, mtime) when the file loads and compares in an `after` hook. Not vacuous: it catches changes by any parallel file during the run, including same-byte rewrites.
- Guard mutations (each reverted): a test doing `rmSync` on the real dist -> `real-bundle-guard.js` hook fails, "a test deleted or rewrote the real dist/ or LICENSE" (fail 1); a test rewriting the real LICENSE with identical bytes -> same failure (mtime). Restored: `bundle.test.js` 4 pass, 0 fail.

**Five runs in a row**, `npm --prefix packages/fontkitstudio test`, dist/ and LICENSE deleted before the first:
run 1: tests 250, pass 248, fail 0 (2 skipped, pre-existing); run 2: same; run 3: same; run 4: same; run 5: same.

Also: `test_release test_support` 59 OK; ruff clean; pre-commit (whitespace, ruff, node --check) passes on the changed files.
