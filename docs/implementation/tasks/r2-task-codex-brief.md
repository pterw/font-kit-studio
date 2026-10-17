# PR #22 Codex review fixes, Studio (controller, 2026-10-17)

BASE `f11055e`. Worktree `C:/fks/ts4`. You own `fontkit-studio.html`,
`tests/test_studio_roles.py` and `tests/test_r2_integration.py`. Rules:
`.superpowers/sdd/r2/constraints.md`. Both findings were checked in source
by the controller.

## 1. A stale same-document ready moves the revision backwards (Codex comment 4300459510)

- `acceptRoleReady` (`fontkit-studio.html` ~3940-3965) ignores a snapshot from
  the same document whose `revision` is older than `rolePreview.revision`.
- The `design:ready` case of the message handler (~5484) then sets
  `live.revision` from that ready anyway. The next Apply or Clear therefore
  carries a stale `baseRevision`.
- A correct bridge cannot produce this, because its revision only increases
  within one `documentId` and messages from one window arrive in order. A
  faulty or hostile bridge can.
- **Fix:** within the same `documentId`, a ready never moves `live.revision`
  backwards. A ready for a new document still sets it, even lower. Keep
  handling the rest of the ready (targets, status, mode, selection); do not
  drop it.
- **Tests (Given/When/Then):**
  - An accepted preview at revision N, then a same-document ready with N-1:
    the next Apply carries `baseRevision` N and the preview is unchanged.
  - A new-document ready adopts its lower revision.
  - Kill the mutant that removes the guard.

## 2. canonicalCss is not checked against the roles (Codex comment 4300459514)

- `validAcceptedRoles` (~3913) is used for receipts and ready snapshots. It
  checks only that `cssHash` is the digest of `canonicalCss`. The sender
  controls both, so unrelated CSS with a matching digest is accepted and
  shown as the acknowledged preview.
- **Fix:** re-serialize the validated roles in the binding format and require
  byte equality with `canonicalCss`. The bridge's format (`fontkit-bridge.js`
  `serializeRoleCss` and `roleDeclaration` ~255-264, `ROLE_CSS_NAMES` ~170)
  is:
  - roles in request order, each as `selectors.join(', ') + ' {\n'`;
  - then, for each key of the properties in the order fontFamily, fontSize,
    fontWeight, lineHeight, letterSpacing, textTransform, a line
    `'  ' + cssName + ': ' + value + ';\n'`, where fontSize is `${v}px`,
    letterSpacing is `${v}em` and the others are the raw value;
  - then `'}\n'`;
  - no roles gives the empty string.
- Global rule 10 allows this duplication across the boundary. Only the plain
  adapter exists until PR B2; leave a comment that R2.S3 must extend the
  serializer for the Bootstrap variable templates.
- **Tests (Given/When/Then):**
  - A hostile row: valid roles with `p { color: red; }\n` and its matching
    digest, in a receipt and in a ready snapshot. Each is rejected and
    changes nothing on screen.
  - A real-bridge check that a real receipt's `canonicalCss` equals Studio's
    serialization. Include non-ASCII family names and an escaped selector if
    the real bridge accepts them.
  - Kill the mutant that skips the equality check.

## Gates and output

- Run only the two focused Studio commands:
  - `python -m unittest test_studio_roles test_r2_integration test_studio_import_link test_studio_dead_controls test_support -v`
  - `python -m unittest test_studio_live test_studio_first_run test_studio_stage.PreviewWidthTests test_studio_visual.LiveAppViewTests -v`

  Both run with `PYTHONPATH=tests`, `FKS_ENGINES=chromium` and
  `FKS_REQUIRE_FIXTURES=1`.
- Show RED first for each fix, and restore each mutant byte-exact.
- Never commit.
- Output:
  - `.superpowers/sdd/r2/task-codex-code.patch`: the full staged diff against
    `f11055e`;
  - `.superpowers/sdd/r2/task-codex-code-report.md`: RED/GREEN, the mutants,
    the counts and the sha256.
