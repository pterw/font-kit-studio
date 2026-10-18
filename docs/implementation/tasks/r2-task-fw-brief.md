# R2.FW brief: retire the old Studio file name and correct two fixture notes

Plan: `docs/plans/2026-10-03-r2-engine.md`, "R2 release point: 0.4.0" (the forwarder step), Addendum 24 item 3 and
Addendum 25 (wave W1, row R2.FW), D052. BASE `bd20e43b912bee1431fc74d3334c8a6bd4ac55e7` (the controller fills the SHA). Worktree `C:/fks/tfw`.
Task id `fw`. Line budget: about 90 gross lines (one 10-line file deleted, one 38-line test module rewritten to about
45 lines, two 1-line JSON edits). Source read at `362ffd1`.

## Why

D052 kept `font_kit_studio_v0.1.1.html` as a 10-line page that `location.replace`s to `fontkit-studio.html` and says
it "goes away at R2 (0.4.0)" (`font_kit_studio_v0.1.1.html:5-9`). The release point removes it. Its only test module,
`tests/test_studio_rename.py`, tests nothing else (`OldNameForwards`, three methods, lines 9-38), so it must change
with it. The plan wants the replacement to prove the new file opens directly and the old file is absent, not a broken
redirect.

The two `unknownVersionVariant.expected` notes end in "adapter detection deferred to R2.4"
(`fixtures/bootstrap5-static/expected-styles.json:56`, `fixtures/bootstrap4-static/expected-styles.json:30`). That is
stale: R2.4 shipped (D068-D074).

## Owned files (exact)

- `font_kit_studio_v0.1.1.html`: delete.
- `tests/test_studio_rename.py`: rewrite (keep the file name; the plan says "update tests/test_studio_rename.py").
- `fixtures/bootstrap5-static/expected-styles.json` line 56 and `fixtures/bootstrap4-static/expected-styles.json`
  line 30: the `expected` string only.

Everything else is read-only. No other non-Markdown live reference exists (see Findings), so nothing else is owned.

## Findings (checked at 362ffd1 with `git grep` over all non-Markdown tracked files)

Old-name references outside docs:

- `tests/test_studio_rename.py:6` (`OLD`): owned, rewritten below.
- `scripts/verify.py:16` `SUPPLIED_APP`, used at line 65: it reads `git show supplied-v0.1.1:font_kit_studio_v0.1.1.html`
  from the tag, not from the working tree. Deleting the file does not affect it. Do NOT edit it.
- `docs/reference/SOURCES.json:6`: provenance. Do NOT edit.
- No hit in `.github/`, `packages/`, `scripts/serve.py`, `scripts/dev/`, `pyproject`/package `files` lists (the package
  `files` is `["bin/", "src/", "dist/"]`), `.gitattributes`, the frontend gate or `tests/support.py` (`HTML` is
  `fontkit-studio.html`, line 23).
- `tests/test_font_kit_studio_v011.py` is about the app (it imports `HTML` from `support`; no mention of the old name or
  forwarding). It stays untouched. The "v0.1.1" there is the JSON export format, which also stays.

Fixture notes:

- Nothing parses `unknownVersionVariant`. `tests/test_r2_static_fixtures.py:198` loads the files via `oracle()` and reads
  `groups`; the Bootstrap 4 scratch test `test_unknown_version_scratch_variant_preserves_literal_rendering` (line 277)
  builds the banner-less copy itself from `fixtures/bootstrap4-static` and never reads the note. Other readers
  (`test_role_adapters.py:822`, `test_role_detection.py:467`, `test_r2_react.py`, `test_r2_route_fixtures.py`) read
  groups or bindings only.
- The JSON files are not byte-pinned. D060 and Addendum 4 pin only the Bootstrap vendor bytes (`vendor/**`; the
  `.gitattributes` line is `fixtures/bootstrap4-static/vendor/** -text`; `test_r2_static_fixtures.py:247` hashes the
  vendor files). No test hashes `expected-styles.json`. Do not touch any vendor byte.
- Line endings: the index is LF; a Windows worktree checks the JSON out as CRLF (`git ls-files --eol` shows `i/lf w/crlf`).
  Edit with a byte-level script that keeps each file's existing line endings and asserts exactly one match.

## What the variant detects (confirmed facts)

- Bootstrap 5.3.8 `vendor/bootstrap.min.css` starts `@charset "UTF-8";/*! * Bootstrap v5.3.8 ...`. The banner is a CSS
  comment, which the CSSOM drops (plan, Addendum 17 text at line 366; D069). The bridge's evidence is
  `--bs-body-font-family` and `--bs-font-sans-serif` both set on `:root`, read from computed style
  (`fontkit-bridge.js:1311`, `bootstrapVariables()`; D069), never the banner.
- Probe (text only, scratch script `fw_probe.py` in the session scratchpad): stripping the first `/*!...*/` comment from
  the Bootstrap 5 CSS leaves no "Bootstrap v" text and still contains `--bs-body-font-family`, `--bs-font-sans-serif`
  and `--bs-font-monospace`. So a banner-less Bootstrap 5 page keeps the same evidence and the same adapters
  (`bootstrap5-body`, `bootstrap5-mono`, `bootstrap5-heading`). This is derived from the CSS text and the CSSOM rule; no
  test runs the banner-less Bootstrap 5 copy through the bridge (see Open question 1).
- Same probe on Bootstrap 4.6.2: none of the three `--bs-` variables appears, banner or not. `test_role_adapters.py:195`
  and `:216` already prove the Bootstrap 4 fixture gives only `plain` groups and that every `bootstrap5-*` adapter is
  rejected as unsupported with nothing written. There is no Bootstrap 4 adapter.

## Requirements

1. `font_kit_studio_v0.1.1.html` is absent from the tree (`git rm`-equivalent in the patch). Oracle: the plan's release
   point step and D052 ("remove it at R2 (0.4.0)"). Observed: opening `file:///.../font_kit_studio_v0.1.1.html` fails to
   load; it does not land on any page.
2. Rewrite `tests/test_studio_rename.py` as class `StudioFileName` (module docstring: "Studio opens directly at
   fontkit-studio.html; the old name is gone (D052)."), keeping its imports from `support` (add
   `from playwright.sync_api import Error` after the stdlib imports). Three methods, each with a Given/When/Then
   docstring whose Then is exactly what it asserts:
   - `test_new_name_opens_directly_and_keeps_query_and_hash`: Given Studio's file with the query and hash the old
     test used (`?target=http%3A%2F%2Flocalhost%3A9%2F&x=1#composer`), when it is opened, then the page URL equals
     `HTML.as_uri() + suffix` at once (no `wait_for_url`, no redirect) and the title starts `Font Kit Studio v`.
     Per engine in `ENGINES`, `subTest`, contexts closed in `tearDown` as the old module did.
   - `test_new_name_opens_without_query`: Given the bare file URL, when opened, then `page.url == HTML.as_uri()` and
     the title starts `Font Kit Studio v`. (If this duplicates the first beyond reason, fold it in; the budget allows
     either.)
   - `test_old_name_is_absent_and_does_not_load`: Given `REPO / 'font_kit_studio_v0.1.1.html'`, then
     `assertFalse(OLD.exists())`, and for each engine `page.goto(OLD.as_uri())` raises `playwright.sync_api.Error`
     (a missing file is a load failure, not a broken redirect page). Independent oracle: the literal old file name.
3. The README claim, CHANGELOG entry and other Markdown are the controller's; do not touch them.
4. Replace the two `expected` strings, same sentence shape, ASCII, and nothing else in the JSON:
   - Bootstrap 5:
     `"same rendered tuples; no version banner; adapter evidence is the computed :root variables (--bs-body-font-family and --bs-font-sans-serif), which the banner does not carry, so Bootstrap 5 adapters are still suggested (D069)"`
   - Bootstrap 4:
     `"same rendered tuples; no version banner; no Bootstrap 4 adapter exists, so every group stays plain and bootstrap5 adapters are rejected as unsupported (D068, D069)"`
   Both are checked above (probe; `test_role_adapters.py:195`, `:216`). The phrase "deferred to R2.4" must not remain
   in either file (`git grep -n "R2.4" -- fixtures/*/expected-styles.json` returns nothing).

## TDD

- Requirement 2: the old-name test is GREEN only after the delete (RED before it: `OLD.exists()` is true and the goto
  loads the stub). The two direct-open tests are characterization of behaviour that already works: write them GREEN,
  not RED. Show the RED of the absence test by running it once before the delete in the worktree.
- Mutants (shown failing, then restored byte-exact with SHA-256 before and after): (a) restore the 10-line stub:
  `test_old_name_is_absent_and_does_not_load` fails; (b) make `fontkit-studio.html` begin with a
  `location.replace` to a copy of itself in a scratch copy of the repo (not the tree): the direct-open tests fail on
  the redirected URL. The JSON notes need no test (no reader); say so in the report.
- Scratch scripts and logs carry `fw` in their names.

## Focused command (from the worktree)

```
PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_studio_rename test_support -v
```

Also run `python scripts/verify.py --static-only` (provenance must still print PASS for all entries, including
`supplied-v0.1.1:font_kit_studio_v0.1.1.html`) and `python -c "import json,pathlib; [json.loads(pathlib.Path(f'fixtures/{n}-static/expected-styles.json').read_text(encoding='utf-8')) for n in ('bootstrap4','bootstrap5')]"`.
Run `python -m ruff check tests/test_studio_rename.py`. No npm fixture is needed. Run `git diff --check` after
`git add -N` on the files you create.

## Handoff

Commit subject: `chore: remove the old Studio file name and fix fixture notes` (59 chars). Body: why the forwarder
goes at 0.4.0 (D052, bookmarks to the old name now fail), that Studio opens directly with its query and hash, and that
the two fixture notes now state what the variants detect.

Markdown and controller-owned references to list for the landing (not owned here):

- `README.md:101`: says the old name "is now a small page that forwards to it ... and goes away at R2 (0.4.0)". Rewrite
  to the migration wording.
- `CHANGELOG.md:99` (0.3.0 entry) and `:196` (0.2.1 entry): both sit in dated released entries; leave them as history;
  add the 0.4.0 bookmark-migration entry under Unreleased.
- `docs/implementation/deviations.md` D052 (record the removal), `docs/implementation/progress.md`, the plan's R2
  release-point checkbox, the typography-system design line 298 (historical), and the sweep: controller.
- `docs/reference/SOURCES.json` and `scripts/verify.py:16,65`: stay unchanged on purpose; the sweep should not list them
  as stale.

## Open questions

1. No test runs a banner-less Bootstrap 5 copy through the bridge; the Bootstrap 5 note rests on the CSS text probe and
   the CSSOM rule. Options: (a) accept as written (recommended; the note states the evidence source, which
   `test_role_adapters.py` `EvidenceTests` pins); (b) add a banner-stripped Bootstrap 5 characterization to
   `tests/test_role_adapters.py` or `tests/test_r2_static_fixtures.py`, which R2.FW does not own and would need a
   dated row in Addendum 25.

## Controller ruling on the open question (2026-10-18)

Accepted as written, no new test: the CSSOM drops CSS comments, so the bridge never sees the version banner, and every
existing Bootstrap 5 adapter test (`tests/test_role_adapters.py`) already proves detection without it. Quote that
reasoning in the corrected note's evidence in the report.

## Controller fixes from the brief review (2026-10-18; `task-fw-brief-review.md`)

1. (I1) Owned files gain `.pre-commit-config.yaml`, only the `font_kit_studio_v0\.1\.1\.html` alternative in the
   `static-checks` hook's `files:` regex (line 38 at BASE): remove that alternative and nothing else. Prove the hook
   still selects `fontkit-studio.html` (for example `pre-commit run static-checks --files fontkit-studio.html` lists
   it as run, not skipped). The landing amends Addendum 25's R2.FW row to name this file.
2. (M1) The absent/direct-open checks load through `file://`; say so in the report.
3. (M2) Run mutant (b) from inside the scratch repository copy, so `support` resolves `HTML` and `REPO` to the copy.
