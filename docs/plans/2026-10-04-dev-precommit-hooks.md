# Dev hygiene: pre-commit and commit-msg hooks

Status: **approved in outline** (owner, 2026-10-04: "Narrow =/= vacuous so if it serves its
purpose, good"); queued behind R1 PR B's ready checks. One small pull request from `main`,
branch `chore/precommit-hooks`. Built and committed locally while PR B is in review, pushed
after PR B merges (a commit is not a push). Not part of a roadmap release.

## Why

- **Whitespace reaches review.** In R1 PR B, trailing whitespace slipped into two patches
  (`proxy.js`, `cli.js`) and only reviewers caught it. `git diff --cached --check` catches it
  before the commit exists, for free.
- **The attribution rule is enforced after the fact.** `scripts/dev/check_commit_messages.py`
  runs by hand and in CI, on commits that already exist. Agent harnesses keep proposing
  `Co-Authored-By` and "Generated with" lines that AGENTS.md forbids; a `commit-msg` hook
  refuses them before the commit is written, for every contributor.
- **Contributors** get the fast CONTRIBUTING checks without remembering them.

## Global Constraints

- Fast only: every pre-commit hook together finishes in a few seconds on a typical commit
  (`verify.py --static-only` about 0.3 s, `ruff check .` about 0.1 s on the dev machine). The
  browser suites, the frontend gate and the Firefox canary stay out: CI and the gate
  runners cover them, and a slow hook gets bypassed.
- `pre-commit` framework with `repo: local` hooks only (`language: system`): they call tools
  already pinned in `requirements-dev.txt`, so installing the hooks downloads nothing from
  GitHub. `pre-commit==4.6.2` is pinned there.
- No `--no-verify`, ever (AGENTS.md, Commit Rules). The hooks must therefore never fail on a
  clean tree and must work on Windows (Git Bash and PowerShell), macOS and Linux.
- Dev tooling stays stdlib Python plus the pinned dev requirements (global rule 8).
- No product behaviour changes; no CHANGELOG entry (it records product changes only).

## Hooks

| Stage | Hook | Entry | Runs on |
|---|---|---|---|
| pre-commit | whitespace | `git diff --cached --check` | always (`pass_filenames: false`) |
| pre-commit | ruff | `python -m ruff check` | staged `*.py` |
| pre-commit | node syntax | `node --check` | staged `fontkit-bridge.js` and `packages/fontkitstudio/**/*.js` |
| pre-commit | static checks | `python scripts/verify.py --static-only` | staged `fontkit-studio.html`, `fontkit-bridge.js`, `docs/reference/**`, `scripts/verify.py` |
| commit-msg | signatures | `python scripts/dev/check_commit_messages.py --message-file` | the message being written |

Files whose bytes are not ours to tidy are exempt from the whitespace check through
`.gitattributes` (`-whitespace`): `fixtures/*/package-lock.json`,
`fixtures/bootstrap5-static/vendor/**` (R1 PR B adds these; the attribute lines are added
when this branch is rebased on a `main` that has them), and `docs/reference/**`.

## Tasks

### P1 `--message-file` for the commit-message check (implementer)

- **Owns:** `scripts/dev/check_commit_messages.py`, `tests/test_commit_messages.py`.
- **Interface:** `--message-file PATH` checks the text in PATH as one commit message with
  the same rules the range mode applies (session trailers, AI co-authors, "Generated with"
  lines), and prints `FAIL <message>: <reason>` lines and the usual summary; exit 0 clean,
  1 on any finding or an unreadable file. Every line is checked, `#` lines included: `git commit -m`
  and `-F` keep `#` lines in the stored message, so skipping them would let a signature
  through (see the ledger, 2026-10-04). It reads no git history, so it works before the
  first commit. `--message-file` and `--range` together are a usage error (exit 2).
- **Tests (test first; RED, then GREEN):** a clean message passes; each rejected kind fails
  with its reason (a `Co-Authored-By: Claude ... <noreply@anthropic.com>` trailer, a
  `Claude-Session:` URL trailer, a "Generated with [Claude Code]" line); a human co-author
  named Claude with a personal address passes; git's editor comment block alone passes and
  a signature in a `#` line is refused; a missing file exits 1 with a message; both flags exit 2. Mutation: route `--message-file` to an empty check and the
  rejection tests fail. The range mode's existing tests still pass unchanged.
- **Gates:** static, ruff, `test_commit_messages`, `test_support`, commit messages.

### P2 The hooks, the pin and CI (controller)

- **Owns:** `.pre-commit-config.yaml` (new), `requirements-dev.txt` (the pin),
  `.gitattributes` (the `-whitespace` lines), `.github/workflows/quality-gate.yml` (one
  step), `tests/test_precommit_hooks.py` (new).
- **Config:** the five hooks in the table, `repo: local`, `language: system`;
  `default_install_hook_types: [pre-commit, commit-msg]` so one `pre-commit install` sets
  both.
- **CI:** in the quality-gate job, after ruff, `pre-commit run --all-files` (keeps the
  config working: a hook that errors on the repository fails CI) and
  `git diff --check origin/main...HEAD` for whitespace on the pull request's own lines (the
  pre-commit whitespace hook sees only staged changes, so it passes vacuously in CI).
- **Tests (behaviour, not config text):** in a scratch git repository made in a temp dir
  (`git init`, the config and `scripts/dev/check_commit_messages.py` copied in, `pre-commit
  install`), a commit of a file with trailing whitespace is refused and nothing is
  committed; the same file without it commits; a commit whose message carries an AI
  co-author trailer is refused; a clean message commits. Skip with "pip install -r
  requirements-dev.txt" when `pre-commit` is not importable locally; CI installs it, so set
  `FKS_REQUIRE_PRECOMMIT=1` there and fail instead of skipping (anti-pattern 14). Mutation:
  remove the whitespace hook from the copied config and the first test fails.
- **Gates:** all fast gates, `test_precommit_hooks`, `test_support`; suite-a and suite-b
  (a `tests/` module is added).

### P3 Docs (controller)

- **CONTRIBUTING.md:** under setup, `pre-commit install` (sets both hooks) with one line on
  what they check and that the slow checks stay in "Before you open a pull request".
- **AGENTS.md:** Environment Setup gains `pre-commit install`; the Gates section says the
  fast gates also run as hooks; Commit Rules already forbid `--no-verify`.
- **CLAUDE.md** (local sessions section): the controller's commits run the hooks; an
  implementer never commits, so its worktrees need no hooks.
- **README.md:** the contributor test section names the hooks in one line.
- Sweep for every gate list (AGENTS.md, CONTRIBUTING.md, README.md) after the edit
  (anti-pattern 11).

## Definition of done

- [ ] `pre-commit install` once, then: a commit with trailing whitespace is refused; a commit
      message with an AI co-author trailer is refused; a clean commit goes through, with
      every hook together in a few seconds (time it and record the number).
- [ ] Works on Windows (Git Bash and PowerShell) and in CI on Linux; macOS through the
      quality-gate is not available, so say so.
- [ ] `--message-file` tested test-first with mutation evidence; the range mode unchanged.
- [ ] CI runs `pre-commit run --all-files` and the whitespace check on the pull request's
      lines; `test_precommit_hooks` cannot pass by skipping in CI.
- [ ] Docs list the hooks in one place each; no stale gate list.
- [ ] Independent review; full gates; CI green.

## Sequencing

- Starts after R1 PR B's ready checks (sweep, Firefox canary, final size), while PR #10 is
  in review. P1 runs as an implementer code phase in `C:/fks/tP1`; P2 and P3 are controller
  work in this branch's worktree (`C:/fks/precommit`).
- Pushed and opened as a pull request after PR #10 merges, rebased on that `main` first
  (the `-whitespace` lines for PR B's lockfiles and vendored files need them to exist).
- Its SDD workspace (`.superpowers/sdd/precommit/`) and ledger are created when work starts,
  not before: the compaction hook resumes from the newest `progress.md`, and PR B's must
  stay the newest until PR B is ready.

## Ledger

| Date | Event |
|---|---|
| 2026-10-04 | Plan drafted after the owner agreed to a narrow pre-commit check in its own small pull request, queued behind R1 PR B's ready checks. |
| 2026-10-04 | P1 review: `git commit -m` and `-F` keep `#` lines in the stored message, so the planned skip of `#` lines in `--message-file` would let a `# Generated with ...` line reach history (caught only later by CI's range check). Changed: every line is checked; git's own comment template carries no signature and passes, and a commented-out signature is refused. |
| 2026-10-04 | P1, P2 and P3 done and reviewed on this branch (local). Measured: the hooks over the whole tree take about 1.8 s on the dev machine (Windows 11, Git Bash); macOS is not tested. Left for after R1 PR B merges: rebase, `-whitespace` for PR B's lockfiles and vendored Bootstrap, the CLAUDE.md line, a sweep, push. |
