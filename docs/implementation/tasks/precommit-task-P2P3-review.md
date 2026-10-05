### Spec Compliance
- PASS: five `repo: local`, `language: system` hooks, `default_install_hook_types: [pre-commit, commit-msg]`, `pass_filenames: false` on whitespace and static-checks (the tools take no files), commit-msg gets the message path (pre-commit appends it; the signatures test proves it) (.pre-commit-config.yaml:6-45).
- PASS (justified deviation): the node hook is `scripts/dev/check_js_syntax.py`, not bare `node --check`. The plan table says `node --check`; the controller's reason (node checks only the first file) is true and the script is per-file.
- PASS: `files:` regexes. Bridge, `packages/fontkitstudio/**/*.{js,mjs,cjs}` (12 tracked .js, no .mjs/.cjs yet), Studio, the root old stub, `docs/reference/.+`, `scripts/verify.py` for static-checks. Nothing wider. The old stub is an addition to the plan's table and is checked by verify.py (SUPPLIED_APP, verify.py:16), so it is correct.
- PASS: `-whitespace` on `docs/reference/**` works (scratch repo: exempt file rc 0, other file rc 2). R1 PR B lockfile/vendor lines and the CLAUDE.md line wait for the rebase, as agreed.
- PASS: CI. `Pre-commit hooks` runs after ruff; setup-node (line 44) and `pip install -r requirements-dev.txt` (line 52) are earlier in the same job. The whitespace step mirrors the commit-message step: same four env values, nothing interpolated. `FKS_REQUIRE_PRECOMMIT: '1'` is on the suite step; the test calls `self.fail` when `pre_commit` is missing and the variable is 1.
- FAIL: P3 README line. The plan says "README.md: the contributor test section names the hooks in one line". The README "Development and testing" block (README.md:542-553) is unchanged: no `pre-commit install`, no hooks line. The hooks appear only inside the "Commit messages" and "CI" paragraphs (README.md:630, 632).
- CANNOT VERIFY FROM DIFF: the DoD's recorded timing number and the "macOS is not covered" statement. Neither is in the diff; they may live in progress.md or the PR body. Measured below.

### Checks run
- Behaviour tests -> `PYTHONPATH=tests python -m unittest test_precommit_hooks test_commit_messages -v` -> 38 tests OK, 11.9 s (5 hook tests plus 33).
- Speed -> `python -m pre_commit run --all-files` -> 4 hooks passed in 1.8 s wall (commit-msg hook is separate and trivially fast). Meets "a few seconds".
- Broken-bridge test is meaningful? -> drove the scratch repo through the test's own helpers: (a) broken bridge, as-is: refused by js-syntax AND by static-checks; (b) broken bridge with the js-syntax hook removed: still refused (static-checks fails with "can't open file ...scripts/verify.py"); (c) a VALID bridge (`var a = 1;`): refused too. So the test passes whatever js-syntax does. Vacuous (Issue 1).
- Isolation, global `core.hooksPath` -> reran the module with `GIT_CONFIG_GLOBAL` pointing at a file that sets it -> all 5 tests fail in setUp ("Cowardly refusing to install hooks with core.hooksPath set"). Global `core.whitespace = -trailing-space` -> the whitespace test fails (commit goes through). `GIT_CONFIG_NOSYSTEM=1` is set but the global file still leaks (Issue 2). `commit.template` did not break anything.
- check_js_syntax.py by hand -> (bad, ok) rc 1; (ok, bad) rc 1 with `FAIL <path>` on stderr; missing file rc 1; no args rc 0; node absent from PATH rc 1 with "node is not on PATH; install Node 22 or later". Behaviour is right. No unit test covers any of it.
- Whitespace/hook semantics -> `git diff --cached --check` honours `-whitespace`; flags `y \n` in a non-exempt file. The patch's own added lines have no trailing whitespace (grep over the patch).
- Doc sweep -> grepped README, CONTRIBUTING, AGENTS for gate lists: the three existing lists (README.md:548-550, CONTRIBUTING.md:25-27, AGENTS.md:120-122) are unchanged and correct; each of CONTRIBUTING and AGENTS says what the hooks check in one place. README does not (Issue 3).
- Ruff vs. extend-exclude -> `ruff.toml` excludes `.claude` and `work`; no tracked files there now (`git ls-files work .claude` empty).
- Process note: I ran `git add -N .` once by mistake while probing; I reverted it with `git rm --cached` on the three new files. `git status` is back to the original (P1 staged, P2/P3 unstaged, three new files untracked). No content changed.

### Strengths
- Behaviour tests make real commits and assert on whether HEAD exists, not on config text. The whitespace control (hook removed, same commit goes through) is meaningful, and I confirmed the refusal text comes from git's whitespace check.
- Own `PRE_COMMIT_HOME` outside the scratch repo, LF-written copies of the scripts, cleanup via `addCleanup`, local `core.autocrlf=false` and `commit.gpgsign=false`.
- CI whitespace step mirrors the commit-message step's env handling. A missing BEFORE does not crash (cat-file guard).
- `check_js_syntax.py` is small, stdlib, and has a clear missing-node message and exit codes.

### Issues
#### Critical
(none)

#### Important
1. **The broken-bridge test proves nothing about the js-syntax hook** (tests/test_precommit_hooks.py, `test_a_bridge_with_a_syntax_error_is_refused`). The scratch repo does not contain `scripts/verify.py`, and `fontkit-bridge.js` triggers the static-checks hook, which then fails with "can't open file". The commit is refused for that reason alone: it is also refused for a valid bridge, and it still passes with the js-syntax hook deleted from the config. Fix: add `scripts/verify.py` stand-ins is not needed; instead stage a file that only js-syntax matches (e.g. `packages/fontkitstudio/src/x.js`), or drop the static-checks hook from the copied config in this test. Add a control (a valid JS file commits) and assert on the js-syntax output (`check_js_syntax: FAIL`).
2. **Hook tests leak the contributor's global git config** (tests/test_precommit_hooks.py:42-44, env). Only the system config is disabled. A contributor with a global `core.hooksPath` (common with husky or global hooks) sees all 5 tests error in setUp; a global `core.whitespace` flips the whitespace test. Fix: also set `GIT_CONFIG_GLOBAL=os.devnull` (and `HOME`/`USERPROFILE` to the scratch dir so nothing else is read). One line; the tests then run the same on every machine.
3. **README misses the P3 line and the install step** (README.md:542-553). The plan asks the contributor test section to name the hooks in one line, and the DoD says "Docs list the hooks in one place each". CONTRIBUTING and AGENTS do; README does not (it only mentions the commit-msg hook and the CI run).

#### Minor
1. No test exercises `check_js_syntax.py` with two files, which is the only reason the script exists. A regression to a single `node --check` call over all files would pass every test. Add a unit test: two temp files, bad second one, exit 1 and the path named; no files rc 0; node missing (patch `shutil.which`) rc 1.
2. Whitespace CI step is silent when it does nothing (push with a missing/zero BEFORE, and workflow_dispatch): no output, step green. The commit-message step falls back to the last commit there. Suggest `git diff --check HEAD~1 HEAD` as the fallback for push, or an `echo "skipped: ..."` line, so a skip is visible (AP 14 spirit).
3. Entries use bare `python`. Fine on Windows and in CI (setup-python); on macOS or Debian/Ubuntu with only `python3` the hooks fail to run, and a contributor would be tempted to `--no-verify`. Docs everywhere already say `python`, so low priority; a one-line note in CONTRIBUTING would do.
4. `python -m ruff check` receives explicit paths, which bypass `extend-exclude` (`work`, `.claude`) unless `--force-exclude` is given. No tracked file is affected today; adding `--force-exclude` keeps hook and `ruff check .` in step.
5. A contributor with `core.autocrlf=false` on Windows who stages CRLF text gets "trailing whitespace" from the whitespace hook. That is arguably right for an LF repo, but the hook name/message does not say CR. A CONTRIBUTING sentence would save a support question.
6. `@unittest.skipIf(node missing)` on the JS test is not covered by `FKS_REQUIRE_PRECOMMIT`; in CI node is set up, so fine, but the skip could hide a missing setup-node step later.

### Plan-mandated (for the owner)
(none)

### Assessment
**Task quality:** Needs fixes (Approved with fixes: no Critical, 3 Important, all small)
**Reasoning:** The config, CI wiring, regexes, speed (1.8 s) and the whitespace/commit-msg tests are sound and verified by real commits. The JS-hook test passes without the hook it names, the tests are not isolated from a contributor's global git config, and the README line the plan asked for is missing.


## Fixes (controller, 2026-10-04)

All three Important findings fixed. The JavaScript hook test now stages package files only that hook matches (a broken and a valid file, so the per-file run is shown) and asserts on `check_js_syntax: FAIL` naming only the broken one, with a valid-files control; with the hook removed from the copied config it fails. The hook tests set `GIT_CONFIG_GLOBAL` to the null device and `HOME`/`USERPROFILE` to the scratch folder, so a contributor's own git config cannot change them. README's development section gains the `pre-commit install` line. `pre-commit run --all-files` over the tree takes about 1.8 s.
