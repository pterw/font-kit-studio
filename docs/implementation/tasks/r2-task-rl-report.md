# R2.RL code report (mode: code, BASE 5d28252, worktree C:/fks/trl)

Changed (staged in WORKTREE): fontkit-studio.html (title, eyebrow), fontkit-bridge.js (header), packages/fontkitstudio/package.json, fixtures/vite-ts/package-lock.json (one value, hand-edited per ruling), tests/test_font_kit_studio_v011.py, tests/test_studio_visual.py. 14 added, 9 removed lines. CRLF preserved in CRLF files.

RED at BASE (tests updated first): 39 tests, 2 failures.
- StructureTests.test_version_and_existing_model: title assertion false.
- VersionLabelTests: `'Font Kit Studio v0.3.1' != 'Font Kit Studio v0.4.0'`.
The bridge-header and package assertions were not shown separately failing as a pre-edit RED, since the title assertion fails first in that method. Mutants (c) and (d) cover them.

GREEN after the five source edits: the same command ran 39 tests, OK. LinkedPackageLockTests passed with no skip (FKS_REQUIRE_FIXTURES=1).

Mutants (one label left old, restored byte-exact, SHA-256 prefix unchanged before and after each):
- (a) title 0.3.1: test_version_and_existing_model and VersionLabelTests fail.
- (b) eyebrow 0.3.1: VersionLabelTests fails.
- (c) bridge header 0.3.1: test_version_and_existing_model fails.
- (d) package.json 0.3.1: test_version_and_existing_model and LinkedPackageLockTests fail.
- (e) lock 0.3.1: LinkedPackageLockTests fails.
- (f) PROTOCOL_VERSION = 2: test_version_and_existing_model fails.
Scripts: work/rl_edit.py, work/rl_mut.py in WORKTREE (git-ignored).

Deviation: the Studio-source `version:"0.1.1"` assertion is dropped, per the controller note. It is pinned by the runtime export assertions at test_font_kit_studio_v011.py:240 and test_studio_live.py:917. The protocol assertion (`const PROTOCOL_VERSION = 1;`) is kept.

Other gates:
- `node --check fontkit-bridge.js`: ok.
- `python scripts/verify.py --static-only`: PASS, browser SKIP.
- Node: package.test.js 7/7 pass. cli.test.js fails with "dist/ is missing: run npm test or npm run prepack". That is an unbuilt artifact in the worktree, unrelated to the labels, and was not built here, so cli.test.js is NOT verified.
- pre-commit on the 6 files: whitespace, ruff, JavaScript syntax and static checks all Passed.
- `git diff --cached --check` clean. Patch `git apply --check -R` ok.

Patch: C:/Users/peter/Python Projects/font-kit-studio/.superpowers/sdd/r2c/task-rl-code.patch

## Handoff
Commit subject: `chore: set the release labels to 0.4.0`. Body: Studio, bridge and package share one version (D044); the export format stays 0.1.1 and the protocol stays 1; the vite-ts lock records the linked package version. The landing should run cli.test.js after `npm run prepack` if it wants that Node proof. The Markdown version mentions are as listed in the brief and are untouched.

## Controller integration
