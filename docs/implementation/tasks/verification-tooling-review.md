# Verification tooling review

## Spec Compliance

- ✅ Spec compliant for `verification-tooling-brief.md`; reviewed the immutable working-file package based on `979fa782d388d232e993b9eb2f5932446d7b84f0`. All four assigned working-file SHA-256 values match the package, so this verdict applies to those exact bytes.
- `README.md:13` documents Python/Node, development dependency installation, Chromium/Firefox installation and the default verifier command; `:21` explicitly distinguishes static-only and missing-Git skips from full acceptance. Existing reference links, direct-file run instructions and optional Adobe description remain present.
- `requirements-dev.txt:1` pins Playwright to 1.62.0; a read-only installed-package query independently returned 1.62.0.
- `scripts/verify.py:14` anchors paths to the script; `:21` parses HTML IDs and executable inline JavaScript; `:84` checks duplicates; `:88` uses temporary files and Node syntax checking, including `.mjs` for modules; `:100` computes the app SHA-256; `:52` verifies tagged original-input blobs against manifest hashes; `:106` runs unittest discovery with the current interpreter and repository cwd.
- `scripts/verify.py:103` truthfully labels static-only browser-test skipping. `:108` rejects nonzero suite results, and `:112` converts ordinary file/process/parser/manifest failures to nonzero exit with a failure message.
- ⚠️ This is tooling approval, not app acceptance. Default full-suite execution remains for Task 5 after implementation stops; the report's point-in-time app hash is not the final artifact hash. No browser suite was rerun in this review.

## Strengths

- `scripts/verify.py:49` uses subprocess argument lists and a single repository cwd; Git output is hashed as bytes within `provenance()` at `:52`. No shell interpolation or persistent generated files are introduced.
- `scripts/verify.py:88` scopes syntax files to `TemporaryDirectory`, including the failure path; `:97` preserves Node's actionable diagnostic for invalid JavaScript.
- `scripts/verify.py:52` explicitly reports missing Git and fails on unreadable tagged input or a hash mismatch in an available repository.
- `verification-tooling-report.md:11` records a successful static-only run, `:25` records invoking-directory independence, and `:33` records separate duplicate-ID and invalid-JavaScript fixture failures. Its limitations at `:62` distinguish static checking from UI acceptance and dynamically created IDs.

## Issues

### Critical (Must Fix)

None found in this bounded diff.

### Important (Should Fix)

None found in this bounded diff.

### Minor (Nice to Have)

None requiring action for this task.

## Assessment

**Task quality:** Approved.

**Reasoning:** The verifier meets the requested reproducibility, failure handling, temporary-cleanup and provenance boundaries with a small standard-library implementation. The README accurately separates development packages, static checks and final browser acceptance.

**Checks and limitations:** Read the brief, full report and immutable package. Verified all four assigned file hashes and the installed dependency version without executing tests. Named focused unchanged-source risk: the provenance implementation derives repository paths from source basenames; checked `docs/reference/SOURCES.json` and confirmed its three entries map to the intended app/reference paths and reported original hashes. No broader source exploration or app/test changes. Confirmed branch/head/status before writing only this review and preserved concurrent edits. Parent-supplied graph attempts failed with Transport closed; project/generation/coverage remain unknown and no graph evidence is claimed. Original tagged-blob comparison and the reported fixture runs were assessed from code and retained evidence, not independently rerun.
