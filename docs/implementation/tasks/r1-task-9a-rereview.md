### Scope
Re-review of fix round 1 for task 9a. Patch regenerated at task-9a-code.patch; applied tree C:/fks/t9a matches it (release.yml has both pinned SHAs and both python3 calls).

### Findings re-checked
- PASS (was Important): the tag check is now pinned by a test. `test_tag_must_equal_the_package_version_before_publishing` (tests/test_release.py) finds exactly one step with `package.json` and `exit 1`, asserts it precedes `npm publish`, asserts `env == {TAG: ${{ github.ref_name }}}` and the exact line `[ "$TAG" != "v$version" ]`. Removing the step gives zero matches, so the test fails. The other publish-step run text (`npm install -g npm`, `release_notes.py`) cannot satisfy the predicate, so the test is not vacuous.
- PASS (was plan-mandated Minor): the CHANGELOG notes are validated before the publish. release.yml:52-57 runs `python3 scripts/dev/release_notes.py "${TAG#v}" > /dev/null` with TAG via env, before `npm publish`. `test_changelog_section_is_checked_before_publishing` pins order, env and `"${TAG#v}"`. The release job still writes notes.md, so the notes it posts are the ones already checked. The step sits after the tag check and before the publish.
- PASS (was plan-mandated Minor): the actions are SHA-pinned. I verified each pin with read-only `gh api repos/<r>/git/ref/tags/v4`:
  - actions/checkout v4 -> type commit, 11d5960a326750d5838078e36cf38b85af677262. It matches release.yml (publish and release jobs).
  - actions/setup-node v4 -> type commit, 49933ea5288caeca8642d1e84afbd3f7d6820020. It matches release.yml.
  - Both are lightweight tags that point straight at a commit, so no dereference is needed.
  - `test_every_action_is_pinned_by_commit_sha` requires `owner/name@<40 hex>` on every step and keeps `gates.uses` as the local workflow. Reverting a pin to `@v4` fails it.
  - `npm install -g npm@^11.5.1` is still a range, as the brief requires. This is the only floating input in the publish job, and it is plan-mandated, so I do not count it.
- PASS (was Minor 1): the jq command now uses `reviewers[]?`. I re-ran that jq form on a protection_rules array with a `branch_policy` entry without `reviewers`, and it prints the login with no error. Changing to `[]?` only fixes this failure and cannot change a correct result.
- PASS (was Minor 2, 3): release_notes.py drops trailing blank and `[x]: url` definition lines and leading whitespace-only lines (release_notes.py, `section`). I ran it against the real CHANGELOG. Section 0.1.1 now ends at "- Nested rows and JPEG assets are out of scope." with no link definitions, and 0.2.1 starts correctly. Two new tests (`test_trailing_link_definitions_are_not_notes`, `test_blank_lines_with_spaces_are_trimmed`) assert exact output, and both would fail on the old code. Residual edge: a note body that legitimately ends with a `[x]: url` line loses it. That is acceptable for a changelog.
- PASS (was Minor 4): both jobs call `python3` (release.yml:57, 79).
- Accepted as left (Minor 5, 6): the stricter tarball test is kept next to the looser bundle.test.js one. The fast-fail tag check before the gates remains an optimisation. Neither blocks.

### Checks run
- `PYTHONPATH=tests python -m unittest test_release` in C:/fks/t9a -> 24 tests, 1 failure, which is `QualityGateIsCallableTests` ('workflow_call' not found). That failure is expected until the controller adds `workflow_call:` at landing. The new tests pass.
- Read the full regenerated patch: release.yml, release_notes.py, tests/test_release.py and package.test.js. No `${{` in a run script, no secrets or token words, permissions unchanged (top-level `contents: read`; publish `id-token: write` and `contents: read`; release `contents: write`).
- The report says `.private` is false for the repository, so automatic provenance applies. I did not re-check that.

### Issues
#### Critical
- None.
#### Important
- None.
#### Minor
- None new.

### Assessment
**Task quality:** Approved
**Reasoning:** The Important finding is fixed with a non-vacuous test. The notes check now runs before the irreversible publish. Both SHA pins match their v4 tags. The jq, trailing-definition and python3 fixes behave as claimed. The only red test is the expected `workflow_call` one.
