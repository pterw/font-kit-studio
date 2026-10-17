# R2.S3 brief: Studio adapter pass-through

Plan: `docs/plans/2026-10-03-r2-engine.md`, task R2.S3; Addenda 16 and 17 (items 1-3); D068-D069; the
binding contract (`DetectedGroup.adapter`, `RoleInput.adapter`, canonical CSS). PR B2, wave W1. BASE: the
W0 head, filled in at dispatch. Worktree `C:/fks/ts3`, task id `s3`. Codes in parallel with R2.4 (bridge,
disjoint files) and lands with it in one commit. Line budget: about 500 material lines (Studio about 40,
tests about 450); explain any excess.

## Why

The bridge now suggests an adapter per detected group (R2.4). Studio must accept that field exactly, send
it back unchanged when the user applies the role, show it, and accept the bridge's template bytes in
receipts and ready snapshots, which it compares byte for byte since PR B.

## Owned files (exact)

- `fontkit-studio.html`.
- `tests/test_studio_roles.py`: new tests; `group()` gains a last parameter `adapter='plain'` and puts it in
  the dict; `canonical_css` learns the templates (step 4 rules), because the existing
  `test_ready_with_accepted_roles_shows_them_seeds_drafts_and_is_never_sent_back` seeds a `bootstrap5-body`
  role with a family; R2.C0's template self-check in `StudioContractTableTests` grows from two cases to all
  five (`canonical_css(case['roles']) == case['css']`).
- `tests/test_r2_integration.py`: new real-bridge cases, and one existing literal: the `MANY_MATCHES`
  page's inline group (lines 214-217 at `afd64be`) gains `adapter: 'plain'`.

Read-only: `fontkit-bridge.js`, `tests/role_contract.py`, `tests/support.py`, fixtures, every other module.

## Read first

`constraints.md`; the binding contract; Addenda 16-17; D068-D069; `tests/role_contract.py` (`ADAPTERS`,
`TEMPLATE_CASES`); in `fontkit-studio.html`: `validDetectedGroup` (key list), `validDetectedReply`,
`ROLE_ADAPTERS`, `validRoleInput`, `serializeRoleSheet` (its comment says R2.S3 must extend it),
`validAcceptedRoles`, `acceptRoleReady`, `buildRoleRequest`, the role-rows render block (title, bindings,
`Safe complete bindings unavailable.`, shared classes, near duplicates), `validRoleRejection`,
`rejectRoleOp` and `rejectionDetailText`.

## Behaviour to build

1. **Detected groups.** `validDetectedGroup` requires `adapter`, exactly one of `ROLE_ADAPTERS`. A group
   without it or with any other value makes the whole reply malformed, as for any other field (no
   released Studio or bridge has role detection, so no older shape is accepted).
2. **Requests.** `buildRoleRequest` sends `adapter: group.adapter`, unchanged, for each selected role.
3. **Rows.** A row whose adapter is not `plain` shows one more line, its own `<p>` directly after the last
   binding line and before `Safe complete bindings unavailable.`: `Adapter: Bootstrap 5 body variables`
   (`bootstrap5-body`), `Adapter: Bootstrap 5 monospace variable` (`bootstrap5-mono`), `Adapter: Bootstrap 5
   heading rule` (`bootstrap5-heading`). The label comes from a Studio-owned map keyed by the validated
   value, never from reply text, and goes through `textContent`. Plain rows are unchanged (the controller's
   reading of D068's "shows it as text": no line on every non-Bootstrap row).
4. **Bytes.** `serializeRoleSheet` follows Addendum 17 item 1 exactly: for a `bootstrap5-body` or
   `bootstrap5-mono` role with `fontFamily`, first `:root {\n  --bs-body-font-family: F;\n  --bs-font-sans-serif: F;\n}\n`
   (mono: `:root {\n  --bs-font-monospace: F;\n}\n`), then the unchanged plain block; heading and plain roles
   only the plain block; request order, never merged. Receipts and ready snapshots are then accepted only
   with these bytes; update the comment above it.
5. **Rejections (no Studio change).** `rejectRoleOp` already shows any valid role rejection with its detail
   and keeps the accepted preview. Do not add a case for `Unsupported adapter`.
6. **Selector-check signatures (D070, Addendum 18).** Studio accepts up to `CHECK_SIGNATURES` (1,024 =
   `ROLES * VARIANTS`) signatures per `SelectorCheck`, the bridge's real bound in a complete reply; today it
   drops a whole valid reply above 128 (`validRoleVariants(check.signatures, check.matchCount, 128)` in
   `validDetectedReply`). Change that one argument. RED: R2.C0's report hands you the test (a check of
   `CHECK_SIGNATURES` signatures renders, one more is refused); add it to `StudioContractTableTests`.
7. **Losses per property (D071, Addendum 20; owner ruling 2026-10-17).** A receipt outcome carries at most
   `LOSSES_PER_PROPERTY` (16) losses for each property, so at most `LOSSES` (96). Today `validRoleOutcome`
   checks only the total (`outcome.losses.length > 96`), so an outcome with 17 losses for one property is
   shown as acknowledged. Add the per-property count to that function's validation, nothing else. RED:
   R2.C0's report hands you the test (16 losses for each property render; 17 for one property are refused
   and change nothing); add it to `StudioContractTableTests`, and record one mutant that removes your check.

## Tests

Literal expectations come from `TEMPLATE_CASES`, `ADAPTERS`, this brief and the fixtures'
`expected-styles.json`, never from Studio's code. Where a `TEMPLATE_CASES` literal exists, no test takes
expected bytes from `canonical_css`.

RED at BASE (BASE refuses any group with the new key): a group with `adapter` renders; the four adapters
render; request pass-through; the `body`, `mono` and `mixed` bytes; the Bootstrap 5 real-bridge case; a
selector check of `CHECK_SIGNATURES` signatures renders.
GREEN at BASE, kept as characterization with a mutant each: the `'bootstrap9'`, `null` and non-string
rows (refused today only because of the extra key; their evidence is the mutant that weakens the enum
check), `body-without-family`, `heading`, the rejection, and the Bootstrap 4 and plain requests.

Fake peer (`tests/test_studio_roles.py`):

- Each of the four adapters in a detected group renders, with the line above for the three Bootstrap ones
  and none for plain; a missing `adapter`, `'bootstrap9'`, `null` or a non-string refuses the whole reply
  (the fence renders, nothing of the refused reply does).
- Apply sends each selected group's adapter unchanged, row by row (a plain and a body role carry both
  values in order), and the receipt built from the `body` case's and a plain case's literals is what
  `#rolePreviewCss` and the status then show. Change one group's adapter between two Detects: the next
  request carries the new value.
- For each `TEMPLATE_CASES` entry, a ready snapshot whose roles are the case's roles and whose CSS and
  digest are the case's literals is accepted, and `#rolePreviewCss` shows the literal. The `body` case is
  also driven as a receipt (Apply a body row, answer with the case's literals; `validRoleReceipt`
  compares role ids, so use the request's ids). Refusals: `body`, `mono` and `mixed` are refused when sent
  with the plain serialization of their roles (no `:root` block) and that text's own digest;
  `body-without-family` and `heading`, whose literal bytes are the plain serialization, are refused when
  the `body` case's four-line `:root` block is put before their literal bytes (own digest). A refused
  snapshot clears the rows, sets `#roleStatus` to `This bridge does not support role detection/preview.`,
  disables Detect and Apply, and leaves `#rolePreviewCss` as it was (over an accepted preview,
  `#rolePreviewStatus` gains the `Unconfirmed` prefix), as `acceptRoleReady` does and
  `test_a_ready_whose_css_is_not_its_roles_serialization_is_not_shown_even_with_a_matching_digest` asserts.
  A refused receipt leaves the request in flight (the fence pattern of
  `test_every_hostile_receipt_is_ignored_until_the_valid_fence_settles_the_request`).
- Rejection, characterized GREEN: a body row is applied and acknowledged with template bytes; a second
  Apply is answered `design:rejected` (`unsupported-value`, detail `Unsupported adapter`). Then
  `#rolePreviewStatus` reads exactly `Role preview apply rejected (unsupported-value); the previous preview
  is kept. Detail: Unsupported adapter`, `#rolePreviewCss` still equals the acknowledged bytes (`:root`
  block first), the typed drafts keep their values, and after `self.quiet(page)` the peer holds no further
  `design:roles-apply`.
- Before changing `validDetectedGroup`, run `git grep -n -E "nearDuplicateIds|bindingComplete" -- tests` at
  your BASE: every detected group a test sends to Studio must carry the field. At `afd64be` those are
  `group()` and the `MANY_MATCHES` page; the W0 head may add some in `StudioContractTableTests`. List them
  in the report. Every other existing test keeps passing unchanged.

Real bridge (`tests/test_r2_integration.py`, real Studio against the real bridge across origins):

- Serve the Bootstrap 5 fixture at its own URL so `vendor/` and `app.css` resolve:
  `html = (REPO/'fixtures'/'bootstrap5-static'/'index.html').read_text(encoding='utf-8').replace('</body>',
  '<script src="/fontkit-bridge.js"></script></body>')`, then `self.open(engine, TARGET +
  '/fixtures/bootstrap5-static/index.html', html, init=CAPTURE)`; `TARGET` maps to the worktree, so the
  bridge is the worktree's. Never write a page under `fixtures/`. Locate the row by its adapter line and read
  its `data-role-id` and title from the row (do not depend on R2.4's names or ids). Assert that exactly one
  row has an adapter line, that its request role carries `adapter: 'bootstrap5-body'`, and that after Apply
  with a family F and a size, the four elements of the oracle's body-tuple group (`bs5.button`,
  `bs5.navigation`, `bs5.label`, `bs.hero.cta`) render F and the size, the target's computed
  `--bs-body-font-family` and `--bs-font-sans-serif` (`.strip()`) equal F, and Studio's preview CSS starts
  with `:root {\n  --bs-body-font-family: F;\n  --bs-font-sans-serif: F;\n}\n`. Clear removes both: the
  variables, the four elements' computed family and size, and `main`'s outerHTML equal their pre-apply
  values, and Studio shows no preview.
- Bootstrap 4 static fixture and the plain role target: every request Studio sends carries `plain`.

The `Unsupported adapter` rejection is tested with the fake peer only. Studio sends its latest detection's
adapter and the newest page version it has heard of, and every change the bridge observes to the
Bootstrap evidence (a DOM, text or attribute mutation; an edit, disable or media change of a
`document.styleSheets` entry; a viewport change) advances the page version (D063; `roleStyleStamp`,
`noteRoleMutations`), so the real bridge answers `page-changed` first. Only an unobserved change reaches
the adapter check (an adopted stylesheet replaced, a non-viewport media-feature flip such as
`prefers-color-scheme`), which no flow on the fixtures produces. Record this in the report.

Each new test method has a Given/When/Then docstring whose Then is exactly what it asserts.

## Working beside R2.4

R2.4 writes the bridge in parallel. The fake-peer tests need nothing from it. The real-bridge cases need
its patch: when the controller sends `PATCH_DEP` (R2.4's code patch and its SHA-256), apply it in your
worktree with `git apply` for those runs only, and keep it out of your patch (`git diff --cached --binary
<BASE> -- fontkit-studio.html tests/test_studio_roles.py tests/test_r2_integration.py`). Until then, write
those cases and record them as not yet run; never mark them passing.

## Mutants (one per new test; foreground; source restored byte-exact with SHA-256 before and after)

Map each to the test it fails: accept a group without `adapter`; weaken the enum check to `typeof
group.adapter === "string"` (the `'bootstrap9'` row); accept `null` (the null row); send `'plain'` instead of
the group's adapter; send `bootstrap5-body` for every role (the Bootstrap 4 and plain requests); drop the
`:root` block (`body`, `mono`, `mixed`); emit it for a heading role or a body role without a family
(`heading`, `body-without-family`); swap the two body variables; merge two `:root` blocks (`mixed`); put the
mono variable under the body name; show the adapter line for plain rows; `rejectRoleOp` clears the preview
or enqueues the op again (the rejection test); the check-signature limit back to 128, or to 1,025 (the
`CHECK_SIGNATURES` test). Report each with its command and failing line.

## Focused gates

From the worktree, in Git Bash. Without `PATCH_DEP`:
`sh "C:/Users/peter/Python Projects/font-kit-studio/.superpowers/sdd/r2/tools/gate.sh" focused test_studio_roles test_studio_import_link test_studio_dead_controls test_support`
With `PATCH_DEP` applied:
`sh "C:/Users/peter/Python Projects/font-kit-studio/.superpowers/sdd/r2/tools/gate.sh" focused test_studio_roles test_r2_integration test_studio_import_link test_studio_dead_controls test_support`
Also `python scripts/verify.py --static-only` (inline JS syntax, unique ids), Ruff on the changed test
files and `git diff --check`. No npm fixture is needed.

## Report and handoff

Report: what changed by function; RED and GREEN as split above; each new test's oracle and mutant; which
real-bridge cases ran with `PATCH_DEP` (its SHA-256) and which did not; the grep list of Studio-bound
groups; the unreachable rejection path and why; focused output; material lines; deviations with the rule
that forced them. Handoff: the patch; a draft commit body for the Studio part of the combined R2.4 + R2.S3
commit; a draft replacement for the CHANGELOG Unreleased line "Only the plain adapter is accepted so far."
and one line for the new visible adapter text (the controller writes CHANGELOG); the R2.S3 plan items done.
