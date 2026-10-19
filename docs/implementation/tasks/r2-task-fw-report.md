# R2.FW code report (mode code, BASE bd20e43)

Patch: `.superpowers/sdd/r2c/task-fw-code.patch` (apply --check -R passes). Files: `.pre-commit-config.yaml`
(removed only the `font_kit_studio_v0\.1\.1\.html` alternative), `fixtures/bootstrap4-static/expected-styles.json`,
`fixtures/bootstrap5-static/expected-styles.json` (the `expected` string only; byte-level script, CRLF kept, one match
each), `font_kit_studio_v0.1.1.html` (deleted), `tests/test_studio_rename.py` (rewritten, class `StudioFileName`, 3
methods with Given/When/Then docstrings). Net +33/-31 lines. Nothing deferred. The page loads in these tests go
through `file://`.

## Evidence
- RED (before delete): `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_studio_rename` ->
  `FAIL: test_old_name_is_absent_and_does_not_load ... AssertionError: True is not false`, Ran 3, failures=1. The two
  direct-open tests were GREEN (characterization).
- GREEN after delete: `python -m unittest test_studio_rename test_support -v` -> `Ran 37 tests ... OK`.
- Mutant (a): restored the stub from HEAD (sha256 of restored file ee9051194b939b55c807c5d5e8d86fc647b60a57bb09adecfff3566dc187dc95;
  file absent before, removed after): absence test FAILED `True is not false`, Ran 3, failures=1.
- Mutant (b): scratch copy (tests + fontkit-studio.html) in a temp dir, run from inside it, one-time `location.replace`
  to `fontkit-studio.html?r=1` prepended. Both direct-open tests FAILED on the redirected URL (`...?r=1#composer` !=
  expected; `...html?r=1` != bare URL). Real `fontkit-studio.html` sha256 before and after:
  56dd0108aa2322a98b20f32957bee3c1eb45fb0861ea2549e5f419e228193ba7 (never mutated; scratch deleted). An earlier
  unguarded loop variant also failed (goto timeouts) and is superseded.
- The absence test's goto-raises half is not separately mutated beyond (a), where the stub load makes the file-exists
  assert fail first.
- JSON notes: no reader parses `unknownVersionVariant`, so no test. Controller ruling quoted: the CSSOM drops CSS
  comments, so the bridge never sees the version banner, and every existing Bootstrap 5 adapter test
  (`tests/test_role_adapters.py`) already proves detection without it. `git grep -n "R2.4" -- 'fixtures/*/expected-styles.json'`
  returns nothing; both files parse (`jsonok`).
- Note: the old text said "no known version evidence"; the brief's replacement says "no version banner" and was used
  verbatim.
- `python scripts/verify.py --static-only`: PASS for all entries incl. `supplied-v0.1.1:font_kit_studio_v0.1.1.html`
  cae14e84...; browser SKIP as expected.
- `ruff check tests/test_studio_rename.py`: All checks passed. `git diff --cached --check`: clean (after `git add -N`).
- pre-commit 4.6.2 via `python -m pre_commit run --files <4 changed files>`: trailing whitespace Passed, ruff Passed,
  node check and static-checks "no files to check" Skipped. Hook proof:
  `pre-commit run static-checks --files fontkit-studio.html` -> `static checks (ids, inline JS, provenance) Passed`
  (selected and run, not skipped).

## Handoff
- Commit subject: `chore: remove the old Studio file name and fix fixture notes`. Body: the forwarder goes at 0.4.0
  (D052), bookmarks to the old name now fail; Studio opens directly with its query and hash; fixture notes now state
  what the variants detect; static-checks hook no longer lists the deleted file.
- Amend Addendum 25's R2.FW row to name `.pre-commit-config.yaml`.
- Markdown for the controller: README.md:101, CHANGELOG 0.4.0 bookmark-migration entry, D052, progress, plan
  checkbox. SOURCES.json and scripts/verify.py stay unchanged on purpose.
- Scratch `work/edit-fw.py` sits in the git-ignored `work/` of C:/fks/tfw, unstaged.

## Controller integration
