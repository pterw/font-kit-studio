# R2.W2P code report (MODE code, task w2p)

Worktree `a scratch worktree`, BASE `73b3ba2`. PATCH_DEPs applied with `git apply --index`, in order, SHA-256 checked first:
1. `task-w2t-code.patch` 2f1697fb6722f9adbb23fcbfbdadd9fec9349e6ada09d995304fdb5c3d7445cd
2. `task-w2b2-code-p2.patch` 9a60fe42e178a9d21b597b57e8fdf41de7e57c30d8b32a8c53891cf1a27bb184
3. `task-w2b1-code.patch` f6bbdfb0c1e05eed5c7aae2a78105c32eb376859a1eeb48b35a1422d89f9a21c
4. `task-w2pt-code-r1.patch` ad79281c86ad8015ef5c260fbe7224ba3bbf7b1905dba4d6ce88eeab65503ec7

Patch `task-w2p-code.patch` (delta, working tree vs index; no new files): sha256 `331b376fc2c3a15ba7c978b5b0a12e92d31e7109738771ff9e1be764ce7339ae`,
`git apply --check -R` passes. Files: `fontkit-bridge.js` (+43/-20), `tests/test_role_adapters.py` (+192/-44), `tests/test_role_stylesheet.py`
(+23/-18), `tests/test_role_detection.py` (+4). Gross 344 changed lines (262 added, 82 removed); all material (no markdown).

## Bridge (done)
- `canonicalizeRoles`: placement pre-pass before the selector loop (more than one `bootstrap5-body` or `bootstrap5-mono` role, or a body role
  whose de-duplicated selectors are not exactly `["body"]`, gives `unsupported-value` / `Unsupported adapter`). The selector loop skips only the
  body role (`role === page`), so a plain or mono role on `body` stays `Unsupported selector`, and `checked` is never seeded with `body`.
- `soleBody(role)` (exact lowercase, one selector) exempts a Detect known role at the three sites: the sync check, the cooperative check in
  `collectRoleStyles`, and the post-scan root-match rejection. `roleSelector` is untouched.
- `suggestBootstrapAdapters` (set there, not in `choose`/`roleBindings`): author-role groups are filtered out of the list (no adapter, no count
  toward body/mono, name kept); the one body-style group takes `bootstrap5-body` and `[{value:'body', stable:true, reason:'page'}]`, complete;
  the one mono group takes `bootstrap5-mono` and, with no complete binding, `code, kbd, pre, samp` (stable, `page`). SIMPLIFY5 done (`sole`, `bind`,
  facts read once). SIMPLIFY2 done in `roleBindings` (`agreed(key)`; the heading step as two candidate lists, display first). Behaviour unchanged.

## Requirements, RED, oracle
RED = the same new tests against the staged (pre-change) bridge (`git show :fontkit-bridge.js` swapped in by `w2p_mutate.py pre-change`, restored byte-exact):
Ran 117, 52 failures + 5 errors, including every new test (body, body-with-own-text, author roles, mono fallback, placement rows, known Body role).
1. Body binds the page: `test_a_detected_body_group_binds_the_page_and_reaches_every_inheriting_element` (40 added `<p>`, group of 44, binding
   `[('body','page',True)]`, literal receipt `{id:'detected', matched:1, checked:0, mismatched:0, complete:True, losses:[]}`, canonical CSS literal,
   40 p + nav link + label `Inter`/`18px`, both `.btn` `Inter`/`16px` literal, clear == snapshot taken before Apply) and
   `test_a_body_that_holds_its_own_text_is_checked_by_the_receipt` (checked 1).
2. Author roles: `test_an_author_role_group_stays_plain_and_does_not_take_the_body_suggestion_from_its_neighbour` (fixture scenario and a
   heading-shaped author group on the protocol page whose role selector also matches an empty div, so the author-role binding fails and the heading step fires).
3. Mono fallback: `test_a_mono_group_binds_the_four_page_tags_unless_it_already_has_a_complete_binding` (40 `<code>`; two `.snippet` code keep `.snippet`;
   with a `span.font-monospace` the group has 41 elements and the receipt matches 40).
4. Placement: `PlacementTests.test_a_body_or_mono_role_off_its_place_...` on the Bootstrap 5 fixture with a valid Body preview, 9 refusal rows with reason and
   detail, owned text, revision and nav-link computed font unchanged; `["body","body"]` accepted as `["body"]`.
5. Known Body role: `PlacementTests.test_detect_accepts_a_known_role_on_body_alone_...` (fixture: matchCount 0, no signatures; own text: matchCount 1,
   one signature count 1, 16px, 400; `["body",".btn"]` and `["html"]` refused).

## Mutants (foreground; bridge SHA-256 before and after every run `db58389a47d86ef0fca8ba20b771f745bd2f848e74743f24066a31ecaa41bdd9`, RESTORED each time)
Runner `w2p_mutate.py`; module `test_role_adapters` (Ran 45) unless noted.
- page binding replaced by old steps: 5 fail (body test, own-text test, tooltip test, author test, fixture suggestion test).
- author groups count/take body (tie, with the name skip kept): author test fails (`Get started` loses `body` binding); heading branch (author heading-shaped group takes
  `bootstrap5-heading`): author test fails (heading-shaped subtest).
- count rule removed: placement test fails on `two body roles`, `two mono roles` (4 rows incl. detail checks).
- `["body"]` rule removed: placement test fails on 9 subtests (`.btn`, `body,.btn`, `BODY`, `html`, ...).
- case sensitivity removed: placement test fails 7 subtests incl. `BODY`.
- mono fallback removed: mono test fails 2 subtests; fallback overrides a complete binding: fails (`.snippet`); fallback binds two tags: fails 2.
- known-role exception removed at each of the three sites (sync, cooperative, root-match): `test_detect_accepts_a_known_role_on_body_alone...` errors in each (reply is a rejection).
- `checked.set('body', true)` exemption: only the `body role and a plain role both on body` row fails; exemption for mono roles on body: 5 subtests fail.
- receipt skips `body` in `measureRoleOutcomes`: own-text test fails (checked 0 not 1).
- evidence check removed (`test_role_adapters` + `test_role_stylesheet`, Ran 96): the edited evidence tests fail (181, the 306 row, BS4, body-only variables, apply-needs-both, stale adapter, live-preview evidence).

## Existing tests changed, and the rule that forced each
Placement rule (a body role must be exactly `["body"]`) or page binding (Body group binds `body`, so `.btn` buttons keep 1rem and the label inherits 18px):
- `test_role_adapters`: fixture suggestion test (binding is `body`/`page`); template-case test (body receipt `matched 1, checked 0`, nav+label 18px, buttons 16px, label no longer
  sans-serif); the detected-Body test (rewritten as the Body test above); inline-root test (nav link 18px, button 16px); declared-sizes test (now a plain role on the four ids,
  the loss logic is adapter-independent); 128 KiB test (body role on `body` + three plain roles, same exact-size arithmetic); the 434 test RENAMED to
  `test_the_installed_rule_count_equals_the_block_count_of_a_body_and_a_plain_role_without_the_stylesheet_constructor` (body template + plain `.btn` role, expects `[(1,0),(2,2)]`
  and the complex-cascade loss on the plain role); ties test (scenario 1 removed: see concern 1); BS4 rejection test, body-only-variables and apply-evidence tests (body role moved to
  `['body']` so the evidence check, not placement, refuses).
- `test_role_stylesheet`: no-evidence adapter loop and the `adapter-bootstrap-without-evidence` row (`['body']`); `UnsafeFamilyTests` (body adapter on `['body']`); `wide_roles`
  (non-plain adapter adds one body role on `body` plus three plain roles, still 134 KB); ValidateBefore tests; the tokens test (body role on `body`; its final read is
  `body` family `Inter`, because `[data-design-id="role.body"]` sets its own family); the large-page Detect test (preview on `body`; samples are `body` and `#corpus`, because `.g00`
  keeps its own `serif`); the install-count test now `self.skipTest(...)` with the reason on a non-Chromium engine.
- `test_role_detection.test_literal_bootstrap_identities_...`: the Body group (adapter `bootstrap5-body`) must equal `[{value:'body', stable:true, reason:'page'}]` and is skipped
  for the data-design-id comparison; every other group still matches the oracle ids.
- W2PT's 11 bridge tests: all green (full focused set below includes `test_role_adapters` and `test_role_protocol`).

## Gates
`sh gate.sh focused test_role_adapters test_role_stylesheet test_role_protocol test_role_preview test_role_detection test_support` on the final tree:
`Ran 187 tests in 205.699s` / `OK` / `GATE focused EXIT 0 IN 206s`. `node --check fontkit-bridge.js` ok; `python -m ruff check` on the three test files: All checks passed;
`python -m pre_commit run --files <4 files>`: whitespace, ruff, JavaScript syntax, static checks all Passed; `git diff --check` exit 0 (CRLF notice only). Chromium only (ENGINES).

## Concerns
1. Addendum 21's body tie is now unreachable: style groups are unique by style, and author-role groups no longer count, so two groups equal to `body`'s style cannot exist. The tie
   code is gone (the `sole` helper still serves the mono tie, tested). The old ties scenario 1 was replaced by the author-role test.
2. Product-visible limits for the release-point docs: the Body row's members include `.btn`, so a size set on Body never reaches them (family does); an author `body{}` rule of equal
   specificity placed after the owned sheet (HMR re-injection, a `<style>` in `<body>`) outranks the Body block and the receipt cannot show it. The receipt for a Body role is
   `matched 1, checked 0` on a page whose body has no text of its own.
3. R2.W2PI requirement 1 carries the same false oracle (every body-style element computes the size); the `.btn` buttons keep 16px.
4. New tests landed in `ApplyTests` (Body, own-text, author-role, mono) and `PlacementTests` (placement, known role); real-Studio tests stay red until R2.W2PS, per the brief.

## Handoff
- Commit (shared with W2PT, W2PS, W2PI): `feat: bind the Bootstrap 5 Body role to the page`. Draft body: "A real Bootstrap page's body-style group is many unclassed elements, so it had no
  complete binding and Studio refused the Body row. The bridge now binds that group to `body` (stable, reason page), gives the mono group Bootstrap's four tags when it has no
  binding, keeps author-role groups plain, and refuses at Apply a body role off `["body"]`, a second body or mono role, and `body` in any other role. Detect accepts a known
  role whose sole selector is `body`."
- CHANGELOG sentence: "Applying the Bootstrap 5 Body role now restyles the whole page's text through `body` and the Bootstrap font variables, and the bridge refuses Bootstrap roles placed anywhere else."
- Scratch (git-ignored `work/` in the worktree, `w2p` scripts in the session scratchpad): logs and mutant logs; no tracked file outside the four above is changed.

## Controller integration

The controller applied this patch in landing order (W2T, W2L, W2S-a, W2B2, W2B1, W2S-b, W2S-c, W2PT, W2P, W2PS, W2PI,
W2E) on BASE `73b3ba2` and ran the gates once on the integrated tree, Chromium on Windows:

- focused, adapters, detection, protocol and handshake modules: Ran 85 tests, OK.
- focused, stylesheet, preview, Studio live and React modules: Ran 232 tests, OK.
- focused, Studio roles, R2 integration and support modules: Ran 156 tests, OK.
- static (provenance PASS), `node --check fontkit-bridge.js`, product ruff and whitespace: pass.

The full suite halves, the Node package, the frontend gate and the Firefox canary run at the settled wave.
