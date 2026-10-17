# R2.W2P brief: the bridge binds Bootstrap 5 Body to the page and checks placement

Plan: `docs/plans/2026-10-03-r2-engine.md` Addendum 23 items 1-4, task R2.W2P; D074, D069; the binding contract's
"Selector and value validation". PR B2 wave W2, phase 3, beside R2.W2PS (Studio) and R2.W2S-c. BASE
`73b3ba2b2bbc00ee4f501a338e61ff422afed8ff`, with these patches applied first in the worktree, in this order (PATCH_DEP;
the controller names their SHA-256): `task-w2t-code.patch`, `task-w2b2-code-p2.patch` (R2.W2B2 phases 1 and 2),
`task-w2b1-code.patch`, `task-w2pt-code-r1.patch` (R2.W2PT after its follow-up: the table's `page` reason, placement rules and `['body']` template cases).
Worktree `a scratch worktree`, task id `w2p`. Line budget: about 400 gross lines; explain any excess.

Lands in ONE commit with R2.W2PT, R2.W2PS and R2.W2PI. Studio at BASE refuses a `page` binding and a `body` selector, so
real-Studio tests stay red until R2.W2PS is applied: your focused set is bridge-only.

## Why

Verified at BASE (workspace `w2-review.md`, ALT1 and ALT4, "Controller verification"):

1. **ALT1.** `roleBindings` (1782-1829) tries author roles, author ids, the heading step, shared classes, then DOM paths for
   at most 32 elements. A real Bootstrap page's body-style group is many unclassed `p`/`li`/`td`, so it gets no complete
   binding, and Studio refuses the Body row. The `:root` family already reaches every inheriting element, so binding
   `body` adds no reach the variables lack.
2. **ALT4.** `canonicalizeRoles` (248-270) re-checks evidence and heading shape only: it accepts `bootstrap5-body` on any
   selectors (`.card-title` wrote the body variables page-wide) and two body roles (the second's family wins while the
   first reports no loss). D069's "at most one body and one mono suggestion" holds only for Detect.
3. **Author roles.** `suggestBootstrapAdapters` (1834-1848) gives author-role groups adapters (the `authorRole` skip at
   1845 covers only the name). Addendum 23 item 2: a `data-design-role` group gets no Bootstrap adapter.

## Owned files (exact)

- `fontkit-bridge.js`: `roleSelector` call sites for role selectors (canonicalizeRoles, Detect `knownRoles` near 1869, the
  selector check near 1946, and the Detect root-match rejection near 2005), `canonicalizeRoles`, `suggestBootstrapAdapters`
  (where the page binding is set: after the adapter is chosen, not in `choose` or `roleBindings`), and
  SIMPLIFY2 / SIMPLIFY5 (workspace `w2-review.md`; behaviour unchanged, now that R2.W2B2's phase 2 tests cover those lines).
  Not `roleSelector` itself: the general root ban stays exactly as it is.
- `tests/test_role_adapters.py` (all of it, phase 2's tests included), `tests/test_role_stylesheet.py` (every test that
  applies a `bootstrap5-body` role off `['body']`, BASE's and the PATCH_DEPs' alike: the adapter loop near 181, the
  `adapter-bootstrap-without-evidence` row near 306, the test near 208, R2.W2B1's families, validate-first, transition-ban
  and tokens tests, and R2.W2B2 phase 1's large-page Detect test: move each body role to `['body']` so it still tests what
  its name says), and `tests/test_role_detection.py`
  `test_literal_bootstrap_identities_variants_and_counts_preserve_author_dom` (465-490 at BASE): its Body expectation only
  (the Body group now binds `body`, not the four ids). Before editing, run the discovery grep in the worktree WITH the
  PATCH_DEPs applied (`git grep -n "bootstrap5-body\|bootstrap5-mono\|data-design-id" tests/`) and a baseline run of the
  focused set, and list every test this change breaks. The brief review found nine in `test_role_adapters.py` (the
  template case, the detected Body test, the inline-root test, the declared-sizes test, the 128 KiB test, ties scenario 1,
  the test at 94-95, the test at 434, which you also RENAME because it names a stylesheet-constructor fallback that
  R2.W2B1 removed, and R2.W2B2's T1/T6/T7/T14) plus the detection test above. Name each change and the rule that forced
  it.
  Also (R2.W2B1 review, Minor): its install-count test in `tests/test_role_stylesheet.py` (near 1331 on the PATCH_DEPs)
  passes with zero assertions on a non-Chromium engine through a bare `continue`; make it `self.skipTest(...)` with the
  reason (Firefox's `CSS.supports` already refuses `--x(`).

Read-only: `fontkit-studio.html`, `tests/role_contract.py`, `tests/test_studio_roles.py`, `tests/test_r2_integration.py`.
Running worktrees beside yours: `a scratch worktree` (R2.W2PS, Studio and `tests/test_studio_roles.py`) and `a scratch worktree`
(R2.W2S-c, `tests/test_r2_integration.py`). Never touch them.

## Read first

`constraints.md` (all of it); Addenda 17, 21, 22 and 23; D069, D074; `fontkit-bridge.js` with the PATCH_DEPs applied:
158-311, `roleBindings`, `suggestBootstrapAdapters`, `detectTextStyles` (knownRoles and the selector checks),
`measureRoleOutcomes`; `tests/role_contract.py` with the PATCH_DEPs; `tests/test_role_adapters.py` (all).

## Requirements

1. **Body binds the page.** With evidence, the one style group whose text style equals `body`'s own computed style gets
   `bootstrap5-body` and the single binding `{value: 'body', stable: true, reason: 'page'}`, `bindingComplete` true,
   whatever else would bind it. Addendum 21's tie rule stands (two such style groups: neither).
2. **Author roles stay plain.** A group whose identity is `author-role` gets no Bootstrap adapter and does not count toward
   the body or mono suggestion or the tie. Groups bound by `data-design-id` are style groups and follow requirement 1.
3. **Monospace fallback.** The one style group whose family equals `--bs-font-monospace` gets `bootstrap5-mono` and keeps
   its complete binding; when it has none, it binds `code`, `kbd`, `pre`, `samp` (in that order, each
   `{stable: true, reason: 'page'}`), even where some of those elements belong to other groups.
4. **Placement at Apply.** `canonicalizeRoles` first (before the selector loop) refuses with `unsupported-value` /
   `Unsupported adapter` a request with more than one `bootstrap5-body` or `bootstrap5-mono` role, or a `bootstrap5-body`
   role whose de-duplicated selectors are not exactly `["body"]` (exact lowercase: `["BODY"]` is refused; `["body",
   "body"]` de-duplicates and passes; R2.W2PT's table and R2.W2PS must agree). `body` passes only as that role's selector:
   in a plain or other role it stays `Unsupported selector` (the selector loop's detail), and the memoized `checked` map
   must not let a plain role's `body` through after the body role's. The check runs inside the validation pass, before
   the evidence read (R2.W2B1's order).
5. **Detect accepts a known Body role** (Addendum 23 item 1, clarified: known roles carry no adapter). A `knownRoles`
   entry whose sole selector is `body` is valid at every Detect site (1869, 1946, 2005), and its selector check reports what `body`
   matches as for any selector: on the fixture `matchCount` 0 with no signatures (`body` has no text of its own), 1 only
   when `body` holds its own rendered text.

## Tests (each with a Given/When/Then docstring whose Then is exactly what it asserts, and one recorded mutant)

- Body: on the Bootstrap 5 fixture with 40 added unclassed `<p>` of body style and no ids (ADD_HTML), Detect suggests one
  `bootstrap5-body` group bound exactly as requirement 1 says; applying it as received with Inter and 18px makes the 40
  paragraphs, the nav link and the label compute both, and the two `.btn` buttons compute Inter but keep `16px` (a
  literal: Bootstrap's `.btn{font-size:var(--bs-btn-font-size)}` is `1rem`; a component with its own size rule keeps it).
  Clear restores each byte-exact (computed read before Apply: the oracle). The Body role's receipt is literally
  `{id: <the role's id>, matched: 1, checked: 0, mismatched: 0, complete: true, losses: []}` (the bridge's receipt does
  not change); a second
  page whose `body` holds its own text node gives `checked: 1`. RED at BASE (no complete binding).
- Author roles: a `data-design-role` paragraph equal to body's style is `plain`, keeps its author name and binding, and the
  style group beside it is still `bootstrap5-body`. RED at BASE.
- Mono fallback: 40 unclassed `<code>` elements give one `bootstrap5-mono` group bound to the four page selectors; a mono
  group with a complete binding keeps it; and with a `span.font-monospace` member, the receipt counts only the four
  selectors' matches (the over-claim of `bindingComplete` is visible, not silent).
- Placement, in `tests/test_role_adapters.py` on the Bootstrap 5 fixture (evidence present, so missing evidence cannot
  explain a refusal), with a valid preview applied first: one case each for `bootstrap5-body` on `[".btn"]`, on
  `["body", ".btn"]`, on `["BODY"]`, on `["html"]`, `bootstrap5-mono` on `["body"]`, two body roles, two mono roles (each
  `Unsupported adapter`), `body` in
  a plain role, and a body role plus a plain role both on `["body"]` (each `Unsupported selector`, for the plain role);
  assert reason AND detail, and that the preview is unchanged (owned sheet text and a computed read).
- Known Body role: a Detect whose `knownRoles` holds an entry on `["body"]` completes, with the selector check described
  in requirement 5 (RED at BASE: refused); hostile Detect rows: a known role on `["body", ".btn"]` and on `["html"]` are
  refused as today. Mutants: each of the three Detect exceptions removed in turn (1869, 1946, 2005).
- Every existing test the change breaks is updated to the new rule and named in the report with the rule that forced it.
Mutants (each in the foreground through `RoleSheetCase.open(..., bridge_source=...)` or in the worktree, restored byte-exact,
SHA-256 before and after; PYTHONDONTWRITEBYTECODE=1): the page binding replaced by the old binding steps; author groups
taking adapters again, in both branches of `suggestBootstrapAdapters` (the heading branch too: give the author test a
heading-shaped author group); the count rule removed; the `["body"]` rule removed; the case-sensitivity removed; the
mono fallback removed; the known-role exception removed. Line numbers above are at BASE: with the PATCH_DEPs applied,
find every test and site by name. Expected values never come from the bridge's
own output. A failing green is worse than a true red.

## Focused gate

From the worktree, in Git Bash:
`sh ".superpowers/sdd/r2/tools/gate.sh" focused test_role_adapters test_role_stylesheet test_role_protocol test_role_preview test_role_detection test_support`.
Also `node --check fontkit-bridge.js`, `python -m ruff check` on changed Python files, and after staging by name
`git diff --cached --check`.

## Report and handoff

Report: each requirement with its RED and oracle; each mutant (command, failing tests and lines, SHA-256 before and after);
every existing test changed and why; the focused run (Ran line, OK, GATE line); gross and material lines. Patch
`task-w2p-code.patch` holds only your changes on top of the PATCH_DEPs (stage them first with `git apply --index` in order,
write with `git diff --binary`, `git add -N` new files, check with `git apply --check -R`), with the PATCH_DEP SHA-256s.
Commit subject (shared with R2.W2PT, R2.W2PS and R2.W2PI) `feat: bind the Bootstrap 5 Body role to the page`, a draft body
(why, wrapped at 72) and a draft CHANGELOG sentence in product terms.
