### Spec Compliance
- PASS: `font_kit_studio_v0.1.1.html` deleted (patch lines 40-56); absent in the frozen worktree (`ls` fails).
- PASS: `tests/test_studio_rename.py` rewritten as `StudioFileName`, docstring text exact, `Error` import added after stdlib, three methods with Given/When/Then docstrings (test_studio_rename.py diff lines 62-133). Direct-open test uses the query/hash suffix, no `wait_for_url`; bare-URL test kept (brief allowed either); absence test asserts `OLD.exists()` false and `goto` raises per engine.
- PASS: both `expected` strings are the brief's text verbatim; one line changed per file (`--numstat` 1/1); `git grep "R2.4"` on the two files is empty per report and the diff shows the only changed lines.
- PASS: `.pre-commit-config.yaml` change (controller fix I1) removes only the `font_kit_studio_v0\.1\.1\.html` alternative (patch line 9-10).
- PASS: no Markdown, verify.py, SOURCES.json, vendor, or tests/support.py touched (`git diff --cached --numstat`: 5 files only).
- PASS: report states loads go through `file://` (controller fix M1) and mutant (b) was run from a scratch copy (M2).
- PASS: net size +33/-31, within the ~90-line budget.

### Checks run
1. Completeness -> `git grep -n -e font_kit_studio_v0 ... bd20e43 -- . ':!*.md'` and `-i -e OldNameForwards -e forwarder -e location.replace -e studio_v0 -e "has moved"` -> live non-Markdown hits at BASE: `.pre-commit-config.yaml:38` (handled by the diff), `tests/test_studio_rename.py` (rewritten), the stub itself (deleted), `scripts/verify.py:16` and `docs/reference/SOURCES.json:6` (provenance, untouched; verify.py reads the file via `git show supplied-v0.1.1:`). `test_font_kit_studio_v011` hits in `firefox_canary.py` and `test_support.py` are a module name, not the file. Nothing left unhandled. Provenance untouched: `git diff --cached -- scripts docs vendor` is 0 lines.
2. Mutants (own, on copies under the session scratchpad `fw_a`/`fw_b`/`fw_c`; the frozen worktree was never written to; `PYTHONDONTWRITEBYTECODE=1`):
   - fw_a (clean copy): `Ran 3 ... OK`.
   - (a) restore the stub from `bd20e43` into fw_b: `test_old_name_is_absent_and_does_not_load` FAILS at `assertFalse(OLD.exists())` (`True is not false`), failures=1.
   - (a2) same, with the `OLD.exists()` assertion replaced by `pass`: FAILS with `Error not raised` on `page.goto(OLD.as_uri())`. So the goto half independently detects the old file coming back (the report did not show this; I did).
   - (b) prepend a one-time `location.replace(pathname + "?fwr=1")` to a copy of `fontkit-studio.html` in fw_c, run from inside fw_c (support resolves HTML/REPO to the copy): both direct-open tests FAIL on the redirected URL (`...html?fwr=1` != expected), failures=2.
   - Worktree after: `git status --short` shows only the five expected staged entries; `fontkit-studio.html` sha256 56dd0108... equals the report's value.
3. Real behaviour -> read tests + support.py `new_context`/`goto`: the tests open a Chromium context and `goto` a `file://` URL, then read `page.url` and `page.title()`; the absence test relies on `goto` raising for a missing file. Not filesystem-only; mutants a/a2/b above prove it.
4. Hidden skips -> `grep skip` in the module: none. `quality-gate.yml:157` runs `unittest discover` with `FKS_ENGINES=chromium`, so all three tests run on hosted CI. Firefox: `firefox_canary.py` does not list this module, so the Firefox branch of `ENGINES` is not exercised in CI (not a skip; the loop simply covers whatever engine is set).
5. Tests per item: recorded mutant per new test: tests 1 and 2 -> mutant (b); test 3 -> (a)/(a2). Oracles: `HTML.as_uri()+suffix` and the literal old file name, independent of the code under test. Docstring Thens match the assertions (test 1 asserts URL equality and the title prefix; test 3 asserts nonexistence and a raised `Error`). The "at once" wording in test 1 is satisfied by the absence of `wait_for_url`, not a timing assertion (see Minor).
6. Fixture notes -> `fontkit-bridge.js:1311` (`evidence` = both `--bs-body-font-family` and `--bs-font-sans-serif`), D069 text in `docs/implementation/deviations.md:63` (banner is a CSS comment the CSSOM drops), `test_role_adapters.py:195,216` (Bootstrap 4 all plain; bootstrap5 adapters rejected as unsupported). Both note texts are true at BASE. `git grep unknownVersionVariant`: only the two JSON files, one task brief and the plan; no reader, no hash of `expected-styles.json` (scripts, docs/reference, .gitattributes show none). Line endings: working tree files are 100% CRLF (75/75, 108/108), index LF, diff has no stray CR.
7. Pre-commit -> evaluated the new `files:` regex in Python: matches `fontkit-studio.html` (True), no longer matches `font_kit_studio_v0.1.1.html` (False); other alternatives intact in the diff. Report also shows `pre-commit run static-checks --files fontkit-studio.html` Passed (not re-run by me). `git diff --cached --check` clean (rc=0). I did not grep `tests/test_precommit_hooks.py` for a pin: it contains no `static-checks`, `files:` or `fontkit-studio` text.

### Strengths
- Both halves of the absence test are independently effective (a and a2), and the direct-open tests fail on a real redirect (b), with oracles independent of the implementation.
- The edit is minimal and byte-faithful (CRLF kept, one-line changes), and provenance is untouched.

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- `tests/test_studio_rename.py:50-53` (absence test): `assertRaises(Error)` accepts any Playwright `Error` (a crashed target or closed browser also raises). It would be tighter to assert the message names a file-not-found/failed-load code (Chromium `ERR_FILE_NOT_FOUND`). The exists-assertion makes this low risk.
- `tests/test_studio_rename.py:32-35` (direct-open): "at once" is checked only right after `goto` returns; a delayed (timer) redirect would not be caught. The Then text says "at once" and the mutant shows immediate redirects are caught; acceptable.
- `test_new_name_opens_without_query` is largely subsumed by the first test (it adds only the bare-URL case); the brief allowed both.

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** The forwarder, its tests, the two fixture notes and the hook alternative are handled exactly as briefed; I reproduced the absence mutant (both halves) and the redirect mutant on copies, and the new tests fail for the right reason. No live non-Markdown reference is left unhandled and provenance is untouched.
