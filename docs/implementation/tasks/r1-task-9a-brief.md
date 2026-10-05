# R1 9a brief: the release workflow

Plan: `docs/plans/2026-10-04-r1-pr-c-sdd.md` (9a, R1.9; owner Q1: the workflow also makes
the GitHub Release). Decisions: D039 (release tags, assets from the tag), D042 (trusted
publishing, owner-gated, no token), D043 (Node lines), D044 (one version) in
`docs/implementation/deviations.md`. R1.0's ledger entry in
`docs/implementation/progress.md` fixes the trusted publisher's fields: repository
`pterw/font-kit-studio`, workflow `release.yml`, environment `npm-release`. Constraints:
`.superpowers/sdd/r1-pr-c/constraints.md` (read all of it first).

## Goal

When the owner pushes a `vX.Y.Z` tag:
- the same gates a pull request runs, run on the tag;
- then, once the owner approves the `npm-release` environment, `npm publish` runs from
  `packages/fontkitstudio` by trusted publishing (OIDC, with provenance, no token);
- then a GitHub Release `vX.Y.Z` is made, with that version's CHANGELOG section as notes
  and `fontkit-studio.html` and `fontkit-bridge.js` from the tag attached.

Nothing here publishes during this task. Agents never run `npm publish` (constraints,
ruling 8).

## Owns

- `.github/workflows/release.yml` (new).
- `.github/workflows/quality-gate.yml`: add `workflow_call:` to `on:`, and only the edits a
  called run needs. This task lands after 7a, 7b and 8a changed that file, so start from
  BASE as given.
- `scripts/dev/release_notes.py` (new; stdlib only).
- `tests/test_release.py` (new).
- `packages/fontkitstudio/test/package.test.js`: the tarball file-list test (8a already
  added its own tests there; keep them).

## release.yml (binding shape)

```yaml
name: Release
on:
  push:
    tags: ['v*']
permissions:
  contents: read
jobs:
  gates:
    uses: ./.github/workflows/quality-gate.yml
  publish:
    needs: gates
    runs-on: ubuntu-latest
    environment: npm-release
    permissions:
      id-token: write
      contents: read
    steps: checkout the tag; setup-node 24 with registry-url https://registry.npmjs.org;
           npm install -g npm@^11.5.1 (trusted publishing needs 11.5.1+);
           check the tag equals "v" + package.json version (fail with a message naming both);
           npm publish (working-directory: packages/fontkitstudio; prepack bundles Studio
           and the bridge and fails if their labels differ from the package version)
  release:
    needs: publish
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps: checkout the tag; python scripts/dev/release_notes.py <version> > notes.md;
           gh release create <tag> --verify-tag --notes-file notes.md --title <tag>
             fontkit-studio.html fontkit-bridge.js   (GH_TOKEN: github.token)
```

- **Concurrency.** No top-level `concurrency` in `release.yml`. The called gate's group is
  `${{ github.workflow }}-${{ github.ref }}`, which evaluates to the caller's values, so the
  same group in the caller would deadlock.
- **Values.** Every value from the event (the tag, the version) goes through `env:`, never
  interpolated into a `run:` script (same rule as `quality-gate.yml`).
- **Tokens.** No `secrets.*`, no `NODE_AUTH_TOKEN`, no `NPM_TOKEN` anywhere.
- **Pinned actions.** Use the same action major versions `quality-gate.yml` uses.
- **Reading the gate under a tag push.** Read `quality-gate.yml`'s "Check commit messages"
  and "No trailing whitespace" steps and work out what each does on a called run from a tag
  push (`github.event_name` is `push`, `github.event.before` is all zeros for a new tag).
  Say in the report whether each still checks something, and change them only if they would
  fail or check nothing useful.

## release_notes.py

- **Usage:** `python scripts/dev/release_notes.py <version> [--changelog PATH]` (default
  `CHANGELOG.md` at the repository root).
- **Output:** the body under `## [<version>] - YYYY-MM-DD`, up to the next `## [` heading,
  stripped of leading and trailing blank lines, on stdout, UTF-8, LF.
- **Exit 1** with a one-line message on stderr when the section is missing, its date is not
  ISO, the version is `Unreleased`, or the body is empty.
- **Version text.** Accept `0.3.0` or `v0.3.0`. Anything else that is not `X.Y.Z` (with an
  optional pre-release) is exit 2, a usage error.

## Tests

- **`tests/test_release.py` (stdlib `unittest`; PyYAML is available from the dev
  requirements through pre-commit; use it to parse the workflows):**
  - **`release_notes.py`** on temporary changelogs written with LF:
    - found;
    - found with a `v` prefix;
    - missing;
    - undated;
    - `Unreleased`;
    - empty body;
    - the last section in the file;
    - a bad version string (exit 2).
  - **`release.yml` parsed:**
    - the only trigger is `push.tags == ['v*']`;
    - top-level permissions `{contents: read}`;
    - `gates.uses` names `quality-gate.yml`;
    - `publish.needs == 'gates'`, `publish.environment == 'npm-release'`, and
      `publish.permissions == {'id-token': 'write', 'contents': 'read'}` exactly;
    - publish's `npm publish` step has `working-directory: packages/fontkitstudio`;
    - `release.needs == 'publish'` and `release.permissions == {'contents': 'write'}`;
    - no top-level `concurrency`;
    - the file text contains no `secrets.`, `NODE_AUTH_TOKEN` or `NPM_TOKEN`.
  - **`quality-gate.yml` parsed:** `on` has `workflow_call`.
  - **The release job's run steps:** no `${{` inside any `run:` text. Values come through
    `env`.
- **`package.test.js`: the tarball's file list.**
  - Run `npm pack --dry-run --json` in the package directory. On Windows spawn it as one
    command string with `shell: true`; prepack prints a line before the JSON, so parse from
    the first `[`. Prepack needs the repository's Studio and bridge; that is fine.
  - Assert the file paths equal exactly:
    - `LICENSE`, `README.md`, `package.json`;
    - `bin/fontkitstudio.js`;
    - every `src/*.js` and `src/vite-plugin.d.ts`;
    - `dist/fontkit-studio.html`, `dist/fontkit-bridge.js`.

    No `test/`, `scripts/` or fixture path.
  - Build the expected list from the directory listing of `src/` and `bin/`, so a new
    source file needs no test edit, but a stray file type does.

## Definition of done

- **RED, then GREEN** for each test. Mutations, each shown failing and restored:
  - `id-token: write` on the top-level permissions;
  - publish without `environment`;
  - `release` with `needs: gates`;
  - `release_notes.py` accepting an undated section;
  - a `test/` path in `files`.
- **Validate the workflow syntax** if `actionlint` is not installed: say so. Do not
  download it. The parse test is the check.
- **Run:**
  - `npm --prefix packages/fontkitstudio test`;
  - `PYTHONPATH=tests python -m unittest test_release test_support -v`;
  - `python -m ruff check .`;
  - `python -m pre_commit run --files` on your changed files.

## Report

- Code phase report: `.superpowers/sdd/r1-pr-c/task-9a-code-report.md`.
- Patch: `.superpowers/sdd/r1-pr-c/task-9a-code.patch`.
- Handoff:
  - **Owner steps.** The exact PowerShell commands the owner runs once (`gh api` to create
    the `npm-release` environment with the owner `pterw` as required reviewer, and a
    deployment policy limited to `v*` tags), and how to check them.
  - **Ledger.** A `progress.md` event draft.
  - **Commit.** The subject `ci: publish to npm from a v* tag after the gates`, with a
    why-body.
