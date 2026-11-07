# CI docs-only skip, fixture bumps and dependency audit Plan

Status: proposed (2026-11-06).
Implementation branch: `ci/docs-skip-and-fixture-bumps`, stacked on the branch of pull request 30 (`fix/v0.4.1-repairs`). Every `file:line` and
version below is read at `1b86000`.

**Goal:** stop paying for the browser steps on a pull request that changes only Markdown, and stop shipping known advisories in the test
fixtures and the development tools.

**Architecture:** no change to the package, Studio, the bridge or the dev server. Three CI-only changes: updated fixture dependencies, a
condition on the browser work in `quality-gate.yml`, and one new workflow, `dependency-audit.yml`.

**Tech stack:** GitHub Actions, npm lockfiles, `requirements-dev.txt`, stdlib Python for any helper script.

This branch merges after the 0.4.1 tag and takes later commits of the 0.4.1 branch by merge. It changes no user-facing behaviour, so it adds
no CHANGELOG line. The fixture bumps stay inside the versions the README documents (`README.md:38`, `:460`, `:664` say Vite 7 or 8;
`:514` and `:885` say Next.js 16; `packages/fontkitstudio/README.md:7` and `:39` say Vite 7 or 8). If Task 1 cannot stay inside those lines, it
stops and a README and CHANGELOG line become part of that task.

## Global constraints

- No change to what any gate proves on a code pull request. The 12 jobs and their names stay. Each of the three browser places gains one
  decision step, and browser steps gain a condition; nothing else changes in what any step runs, or in their order.
- The package keeps zero runtime dependencies (global rule 8). The fixtures and the development tools are dev and CI only.
- The strings `8.3.2` and `7.3.6` in `packages/fontkitstudio/test` are test data for fake projects, not pins. Do not change them.
- Every workflow value that comes from an event goes through `env`, never into script text (the rule `quality-gate.yml` already follows).
- Procedure: `AGENTS.md`. Global rules: `docs/agents/global-rules.md`.

## Tasks and progress

### Task 1: fixture bumps

**Touches:** `fixtures/*/package.json` and `fixtures/*/package-lock.json` for the five fixtures below. **After:** none. It lands first so
the audit in Task 3 does not open on known advisories.

| Fixture | Package | Now | To | Advisories now |
|---|---|---|---|---|
| `next-app` | next | 16.3.8 | 16.4.5 | 3, critical |
| `vite-react`, `vite-ts`, `vite-react-css-modules` | vite | 8.3.2 | 8.3.6 | 6, high |
| `vite7-react` | vite | 7.3.6 | 7.3.7 | 5, high |

The advisories are measured with `npm audit --package-lock-only` and all are in direct dependencies. Each `package.json` keeps its exact pin
style; the lockfile changes only what the bump needs.

- [x] Each fixture's `package.json` and lockfile carry the version in the table; `npm audit --package-lock-only` reports no vulnerability in
  any of the five.
- [x] `test_vite_types` passes locally. Fixture dev servers do not run locally for this branch: the Fixtures and Next.js jobs run
  `test_r2_react` and the Next fixture test (`test_one_command_next` and `test_r2_entrypoints.NextEntrypointTests`) on the pull request,
  with `FKS_REQUIRE_FIXTURES=1`, so none is skipped. Local acceptance is the audit line above plus `test_vite_types`.
- [x] The linked-package entry in `fixtures/vite-ts/package-lock.json` is kept: `test_vite_types.LinkedPackageLockTests` requires its
  version to equal `packages/fontkitstudio/package.json`'s. When merging later 0.4.1 commits that touch it, take the 0.4.1 version of that
  entry.
- [x] Commit: `chore: bump fixture Next and Vite past their advisories`.

### Task 2a: the decision helper

**Touches:** one stdlib Python helper under `scripts/dev/` and its test in a new module under `tests/`. No workflow change. **After:** none.
It does not depend on Task 1.

**Interface (frozen for 2b).** The helper reads the event name from `env` and the whole-PR diff from git: the merge commit's first parent
against `HEAD`, with `--no-renames`, so a rename lists both its old and its new path. It prints `docs_only=true` to the file named by
`GITHUB_OUTPUT` only when the event is `pull_request` and every changed path qualifies as Markdown under the rules in Task 2b. In every other
case it prints nothing: a `HEAD` with no second parent (not a merge commit), a git failure, an empty diff, any other event. It runs on
Linux, macOS and Windows with the standard library only.

- [x] A table test in a new test module covers: Markdown only (prints); one `.md` plus one `.py` (nothing); root `README.md` alone (nothing);
  `packages/fontkitstudio/README.md` alone (nothing); a rename from a code file to a `.md`, listing both paths (nothing); a deleted file
  (judged by its path like any other); an unknown extension, `.markdown` and `.mdx` (nothing); `docs/guide.md`, `docs/reference/x.md` and
  `AGENTS.md` alone (print); `HEAD` that is not a merge commit (nothing); an event other than `pull_request` with Markdown-only paths
  (nothing); a git failure (nothing); an empty diff (nothing).
- [x] The new module is picked up by `test_support`'s guards like any new module, and passes.
- [x] Commit: `ci: add the helper that decides a Markdown-only pull request`.

### Task 2b: wire the decision into the browser steps

**Touches:** `.github/workflows/quality-gate.yml`. **After:** Task 2a. It does not depend on Task 1. Its throwaway pull requests target the
task branch, not `main`, so other tasks' files stay out of their diffs; the controller runs them after a push.

**Required behaviour.**

- Where the decision runs. It runs as a step inside each of the three places: the `quality-gate` job, each `fixtures` leg and the
  `next-fixture` job. No new job is added, so the 12 jobs stay. In each place the step comes after that job's Set up Python step and calls
  the Task 2a helper. The step reads the merge commit that a `pull_request` run checks out, so it needs no API call and no new permission.
- The checkout. `fixtures` and `next-fixture` set `fetch-depth: 2` on their checkout, so the first parent of the merge commit is present;
  a depth-1 checkout would have no base and would silently run everything in those six jobs. `quality-gate` already checks out full history
  (`fetch-depth: 0`, `fetch-tags: true`, for the provenance check) and keeps it. `node-package` is unchanged.
- Polarity. A browser step is skipped only when the decision step's output equals exactly `true`. Unset, empty or any other value runs it.
  On a step that already carries `if: ${{ !cancelled() }}` (`quality-gate.yml:153, 165, 169, 179, 192, 206`) the new condition is combined
  with it and never replaces it, so a cancelled or failed run behaves as before.
- Failing towards running everything. The decision step sets step-level `continue-on-error: true`, so a helper that errors leaves its output
  unset, the job carries on and the browser steps run. This is the one place `continue-on-error` belongs in this change, besides the
  existing advisory Firefox step: a failure of the decision must not fail the job, because the safe answer to a decision that could not
  be made is to run the work. It is never set on a whole job.

- Only browser work is skipped. The fast checks (static checks, bridge syntax, ruff, commit messages, pre-commit, whitespace) still run on
  every pull request, and every one of the 12 jobs is still present and reports a result. A skipped step leaves its job passing, so the job
  list and its names do not change.
- Browser work lives in three places, and the skip covers all three: in `quality-gate`, every step from "Bound browser dependency
  acquisition" to "Upload gate screenshots"; in `fixtures` (five legs), the steps that install fixtures and browsers and run the tests; in
  `next-fixture`, the same. `node-package` (five legs) is fast and runs in full.
- The skip applies only when the event is `pull_request`. Push to `main`, a `v*` tag run through `release.yml` (`workflow_call`) and a manual
  `workflow_dispatch` run everything.
- A pull request is judged on its whole diff against its base, from the merge base to the head. It skips only when every changed path ends in
  `.md` and none is the root `README.md` or a `packages/*/README.md`. A rename counts both its old and its new path. One code file anywhere in
  the diff means everything runs, whichever push is newest. This gives up skipping a docs-only push to a code pull request; the reason is in
  Decision 2.
- Every doubt runs everything: the diff cannot be read, the base is unavailable, the diff is empty, a path is not plain text, the event is
  unknown, the decision step itself errors. `.markdown`, `.mdx` and any other extension count as code.
- Markdown that tests or the gate read. `tests/test_live_integration.py:38` reads the root `README.md` and runs its snippets;
  `packages/fontkitstudio/test/bundle.test.js:48` and
  `package.test.js:128` expect `README.md` in the package bundle. `scripts/verify.py:62` hashes the Markdown under `docs/reference/` in the
  static check, which still runs on every pull request; that is why `docs/reference/*.md` counts as Markdown. `release.yml` and `scripts/dev/release_notes.py` read `CHANGELOG.md`, only on a tag, which never skips.
  The implementer repeats `git grep` over `tests/`, `scripts/` and `packages/fontkitstudio/test` for `.md` and `README` at the BASE of the
  task and adds any further read to the plan's list before changing a workflow.

**Acceptance.** The reviewer shows each way the skip must not fire, and shows the one way it must.

- [x] The offline table of Task 2a passes at the commit that lands 2b, and its helper is the one the three places call.
- [ ] On a throwaway pull request with a Markdown-only change, the three places skip their browser steps, all 12 jobs end green, and the
  fast checks ran.
- [ ] On a throwaway pull request that edits the root `README.md`, and on one that edits a `.py` file, the full run happens.
- [ ] On a throwaway pull request that changes code and then pushes a Markdown-only commit, the newest run still runs the browser work.
- [ ] On a throwaway pull request, a deliberately failing decision (for example a helper made to exit non-zero in the real workflow) leaves
  the output unset, the browser steps run in all three places and the jobs pass. The deliberate failure is not committed to the branch.
- [ ] On a throwaway pull request with a Markdown-only change, the `fixtures` and `next-fixture` checkouts at `fetch-depth: 2` yield a
  skip, which shows the first parent was present.
- [x] Reading `quality-gate.yml` shows every skipped step's condition is "decision output equals `true`", combined with any existing
  `!cancelled()`; the decision step has step-level `continue-on-error` and no job has it. The tag path is proven by that reading and the
  offline table (the helper prints nothing for any event but `pull_request`), since a tag run cannot be staged before a release.
- [x] Commit: `ci: skip browser jobs on a pull request that changes only Markdown`.

### Task 3: a non-blocking dependency audit

**Touches:** `.github/workflows/dependency-audit.yml` (new). `release.yml` and `quality-gate.yml` are not edited. **After:** Task 1.

**Required behaviour.**

- A separate workflow. It runs weekly on a schedule, on `workflow_dispatch`, and on pull requests that touch `requirements-dev.txt`, any
  `fixtures/*/package.json` or `fixtures/*/package-lock.json`, `packages/fontkitstudio/package.json`, or the workflow file itself.
- Python: `pip-audit -r requirements-dev.txt`, which resolves the transitive packages that the three pins pull in. The shipped code is stdlib
  only, so nothing else is audited. The `pip-audit` version is pinned in the workflow.
- npm: `npm audit` for each of the five fixtures, each from its lockfile. `packages/fontkitstudio` has no lockfile and no dependencies, so
  there is nothing to audit there; the workflow's trigger watches its `package.json` so a first dependency would be noticed.
- Every action is pinned by commit SHA with the version in a comment, as `release.yml` does (`quality-gate.yml` pins by tag and is not the
  model). Permissions are `contents: read`. The legs run independently, so one finding does not hide another.
- Non-blocking means no required check and no change to the merge rules. It does not mean the finding is hidden. A finding must show as a
  failed check on the pull request, which a reader sees without opening a log. A job-level `continue-on-error` is not used, because it turns
  the check green and a finding then shows nowhere on the pull request. A scheduled run has no pull request: its finding shows in the Actions
  list only.
- `npm audit` keeps its default threshold, so every severity fails a leg.
- The Python leg has never been measured. If `pip-audit` reports a transitive advisory, the task records it and decides; it does not pin a
  package to get around it. A leg that stays red with no fix available is recorded, not silenced.

**Acceptance.**

- [ ] On the branch after Task 1, the first run of every npm leg passes. The Python leg's first result is recorded, whichever it is.
- [ ] On a throwaway pull request that pins a package version with a known advisory in one fixture's lockfile, that leg shows as failed in
  the pull request's checks list, the other legs show their own result, and the pull request's merge box does not block (the check is not
  required). The reviewer records what the checks list showed.
- [x] Reading the file shows no job-level `continue-on-error`, every `uses:` is a 40-character SHA, and the `pip-audit` version is exact.
- [x] `release.yml` and `quality-gate.yml` have no diff from this task's commit.
- [x] Commit: `ci: audit dependencies weekly, without blocking`.

## Non-goals

No change to what any gate proves on a code pull request. No blocking audit. No change to the package's zero runtime dependencies. No
Dependabot configuration file: turning Dependabot alerts on is a repository setting outside this plan. No change to the fixture tests
beyond running them. No skip for any file type but Markdown.

## Decisions

Recorded 2026-11-06.

1. **Root and package READMEs count as code.** Tests read them (the list in Task 2b), so skipping the browser work on a README-only change
   would let a broken README snippet merge unrun.
2. **The skip judges the whole pull request.** A skipped run does not stop the concurrency group from cancelling a full run in progress, so
   judging only the newest push could leave a code pull request with a head that has only a skipped run. Judging the whole diff costs the skip
   on a docs-only push to a code pull request, and removes that hole.
3. **The audit is a separate, non-blocking workflow, after the fixture bumps.** A new job in `quality-gate.yml` would change the 12-job
   count and run on every tag through `release.yml`. A blocking audit would fail a pull request for an advisory it did not introduce. Landing
   the bumps first means the audit's npm legs report no advisory the repository already knows. Only the npm baseline was measured.
4. **`docs/reference/*.md` counts as Markdown.** Only `scripts/verify.py` reads it, in the static check that runs on every pull request.
5. **The audit has a manual trigger.** The schedule runs only from the default branch, so a first look at a red leg, and a re-run after an
   upstream fix, need `workflow_dispatch`.
6. **`npm audit` keeps its default threshold, every severity.** The npm baseline is clean after Task 1 and the job gates no merge.
7. **An audit finding shows as a failed check that is not required.** There is no job-level `continue-on-error`, so a finding is visible on
   the pull request. Non-blocking means it gates no merge.

## Open questions

None.
