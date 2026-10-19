# R2.RL brief: set the live version labels to 0.4.0 (code half)

Plan task: "R2 release point: 0.4.0", checkbox "Set matching labels 0.4.0; keep protocol 1 and legacy JSON 0.1.1"
(`docs/plans/2026-10-03-r2-engine.md:1573`). The forwarder part of that checkbox landed in R2.FW (cc4940a):
`font_kit_studio_v0.1.1.html` is already absent at BASE. Wave W3. BASE `5d28252fb6acf52b1287d7f90054d70b49ae249e`
(read source with `git show 5d28252:<path>`), worktree `C:/fks/trl`, task id `rl`. Line budget: 25 gross lines.
Scratch files and logs carry `rl` in their names.

## Why

AGENTS.md "Versions and releases" (D039): every version label states the release it ships in. D044: Studio, bridge and
package share one version. 0.3.1 set its labels in `6ada9b3` (title, eyebrow, bridge header, package.json, the vite-ts
linked lock record, existing title assertions). At BASE every live label still says 0.3.1:

- `fontkit-studio.html:6` `<title>Font Kit Studio v0.3.1</title>`
- `fontkit-studio.html:1014` `<p class="eyebrow">Font Kit Studio · v0.3.1</p>`
- `fontkit-bridge.js:3` ` * fontkit-bridge.js version 0.3.1`
- `packages/fontkitstudio/package.json:3` `"version": "0.3.1",`
- `fixtures/vite-ts/package-lock.json:16` `"version": "0.3.1",` (key `"../../packages/fontkitstudio"`)

## Owned files (exact)

1. `tests/test_font_kit_studio_v011.py` line 534 (`StructureTests.test_version_and_existing_model`) plus new assertions in
   the same test method (see Requirements 2-4).
2. `tests/test_studio_visual.py` lines 470-471 (`VersionLabelTests.test_the_title_and_the_eyebrow_name_this_release`).
3. `fontkit-studio.html` lines 6 and 1014 (label text only).
4. `fontkit-bridge.js` line 3 (comment only).
5. `packages/fontkitstudio/package.json` line 3.
6. `fixtures/vite-ts/package-lock.json` line 16 (one value; no other lock line changes).

Everything else is read-only. No Markdown. Not owned and need no change (verified at BASE): the other four fixture
lockfiles (`next-app`, `vite-react`, `vite-react-css-modules`, `vite7-react`: no `file:`-linked record, no 0.3.1),
`scripts/verify.py` (no version check), `scripts/dev/release_notes.py` (help text example only), `tests/test_release.py`
(0.3.0 values are synthetic CHANGELOG fixtures, historical, stay), `packages/fontkitstudio/src/cli.js` and `project.js`
(read the version from package.json at run time), `packages/fontkitstudio/test/cli.test.js:161` (derives from
package.json), `.github/workflows/release.yml` (compares tag to package.json at run time).

## Read first

- AGENTS.md "Versions and releases"; D039, D042, D044 in `docs/implementation/deviations.md`.
- `git show 6ada9b3 -- fontkit-studio.html fontkit-bridge.js packages/fontkitstudio/package.json fixtures/vite-ts/package-lock.json tests`
  (how 0.3.1 did it); `docs/implementation/sweep-0.3.1.md:15` (its list of live labels).
- `tests/test_vite_types.py:46-53` (`LinkedPackageLockTests`, reads package.json and the vite-ts lock; do not edit).
- `fontkit-bridge.js:76` (`const PROTOCOL_VERSION = 1;`), `fontkit-studio.html:3146` (legacy JSON export
  `version:"0.1.1"`), `tests/test_font_kit_studio_v011.py:240` and `tests/test_studio_live.py:917` (existing
  `exported['version'] == '0.1.1'` assertions).

## Requirements

1. Studio: title text is exactly `Font Kit Studio v0.4.0`; eyebrow text is `Font Kit Studio · v0.4.0`. Oracle: the
   literals, plus D039. Observed: `page.title()` and `.eyebrow` text content in a real page.
2. Bridge header: line 3 reads ` * fontkit-bridge.js version 0.4.0`. No test checks it at BASE. Add one assertion to
   `StructureTests.test_version_and_existing_model`: the first 10 lines of `REPO / 'fontkit-bridge.js'` (read as UTF-8)
   contain `fontkit-bridge.js version 0.4.0`. Import `REPO` from `support` (it exists, `tests/support.py:22`); extend the
   existing import line, add no helper.
3. Package: `packages/fontkitstudio/package.json` `"version"` is `0.4.0`. Add one assertion in the same test method that
   `json.loads` of `REPO/'packages'/'fontkitstudio'/'package.json'` has `version == '0.4.0'`. `json` is already imported.
4. Linked lock: `fixtures/vite-ts/package-lock.json` entry `packages["../../packages/fontkitstudio"].version` is
   `0.4.0`. The existing `test_vite_types.LinkedPackageLockTests` already proves it equals package.json (characterization,
   no new test). Edit the single value by hand (a byte-level edit preserving the file's line endings), or run
   `npm install --package-lock-only` in `fixtures/vite-ts` only if the diff is exactly that one line; otherwise hand edit.
5. Unchanged and asserted: protocol stays 1 and the legacy JSON format stays 0.1.1. In the same test method add:
   `fontkit-bridge.js` source contains `const PROTOCOL_VERSION = 1;`, and Studio source contains
   `version:"0.1.1", app:"Font Kit Studio"`. (The runtime assertions at `test_font_kit_studio_v011.py:240` and
   `test_studio_live.py:917` already cover the export; do not duplicate them.)
6. No behaviour change: `git diff` outside the owned lines is empty; the lock diff is one line.

## TDD

- RED: first update `tests/test_studio_visual.py:470-471` and `tests/test_font_kit_studio_v011.py:534` to `0.4.0` and add
  the new assertions (Requirements 2, 3, 5). Run the focused command at BASE and show: the title/eyebrow test fails
  (`'Font Kit Studio v0.3.1' != 'Font Kit Studio v0.4.0'`), `test_version_and_existing_model` fails on the title (and,
  when the title line is temporarily satisfied, on the bridge header and package version). Record the failing output.
  Genuine RED: the labels really are 0.3.1 at BASE.
- GREEN: apply the five source edits; the same command passes. The protocol and JSON-format assertions pass at BASE
  already (characterization, never RED).
- Mutants (one realistic mutant per label, each shown failing, source restored byte-exact with SHA-256 before and after):
  (a) title left at 0.3.1 -> `test_version_and_existing_model` and `VersionLabelTests` fail; (b) eyebrow left at 0.3.1 ->
  `VersionLabelTests` fails; (c) bridge header left at 0.3.1 -> `test_version_and_existing_model` fails; (d) package.json
  left at 0.3.1 -> `test_version_and_existing_model` fails AND `LinkedPackageLockTests` fails (lock now ahead); (e) lock
  left at 0.3.1 -> `test_vite_types.LinkedPackageLockTests` fails; (f) `PROTOCOL_VERSION = 2` -> the new protocol
  assertion fails.
- Also run Node: `cd packages/fontkitstudio && node --test test/cli.test.js test/package.test.js` (they derive the
  version from package.json; expect green, report the result). Report as not run if Node is unavailable.

## Focused command

From `C:/fks/trl`:
`PYTHONPATH=tests FKS_ENGINES=chromium FKS_REQUIRE_FIXTURES=1 python -m unittest test_font_kit_studio_v011.StructureTests test_studio_visual.VersionLabelTests test_vite_types.LinkedPackageLockTests test_support -v`
`test_vite_types` needs the vite-ts fixture installed in the main checkout (`npm ci --prefix fixtures/vite-ts`); if the
worktree has no `node_modules`, the lock test is a file-level read and does not need it, but report any skip. Also
`node --check fontkit-bridge.js` and `python scripts/verify.py --static-only`.

## Handoff

Commit subject: `chore: set the release labels to 0.4.0` (max 72). Body: Studio, bridge and package share one version
(D044); the export format stays 0.1.1 and the protocol stays 1; the vite-ts lock records the linked package version.
The landing adds a ledger event; no process wording in the commit.

Markdown mentions of versions found at BASE, for the controller and the docs slice (none edited here):

- `CHANGELOG.md:53` `## [0.3.1] - 2026-10-07` stays (historical); `:299-300` compare links: `[Unreleased]` compares
  `v0.3.1...HEAD` and must become `[0.4.0]: .../compare/v0.3.1...v0.4.0` plus `[Unreleased]: .../compare/v0.4.0...HEAD`
  at the release point (checkbox at plan line 1576). The Unreleased heading becomes `## [0.4.0] - <date>`.
- `README.md:101` and `:518` mention `font_kit_studio_v0.1.1.html` / 0.3.x behaviour; re-read for forwarder claims.
- `packages/fontkitstudio/README.md` (changed by the 0.3.1 release commit): re-read for version text.
- `docs/agents` and `CONTRIBUTING.md`: no 0.3.1 hit at BASE.
- Historical, stay: `docs/implementation/{audit-2026-10-08-library-composer,sweep-0.3.1,verification-0.3.1}.md`, deviations
  D044/D052 text, plan lines 40-41, 92, 1113, 1255 (past tense), roadmap lines 82 and 142-146,
  `docs/plans/2026-10-07-v0.3.1-localhost-cookies.md`, `docs/reference/`, the `supplied-v0.1.1` provenance.
- Plan line 92 "The existing 0.3.1 labels stay until the R2 release point" becomes stale after this lands: controller
  addendum or edit.

## Open questions

1. Lockfile edit method: hand edit (recommended, one value) versus `npm install --package-lock-only` (may reorder or
   rewrite other lines). Brief recommends hand edit; the implementer checks `git diff --stat` shows exactly one line.

## Controller ruling (2026-10-18)

Open question 1: as recommended, hand-edit the one version value in `fixtures/vite-ts/package-lock.json` (a `file:`
link carries no integrity hash); `npm install --package-lock-only` is not run. `test_vite_types.LinkedPackageLockTests`
must pass afterwards with the fixture installed; if it fails, report it and stop.

## Controller notes from the brief review (2026-10-18)

- Waiver: constraints.md lists release labels as controller-only shared files; the controller delegates exactly the
  five non-Markdown labels and the lock value named in this brief to this slice. Every Markdown version mention stays
  with the controller and the docs slice.
- Budget: about 25 lines counted as added plus removed lines in the patch.
- The Studio-source `version:"0.1.1"` assertion may be dropped if the runtime export tests already pin it (name them).
