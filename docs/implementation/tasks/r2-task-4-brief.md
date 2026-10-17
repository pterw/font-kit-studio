# R2.4 brief: framework adapters and selector quality (bridge)

Plan: `docs/plans/2026-10-03-r2-engine.md`, task R2.4; Addenda 16-18; D063, D066-D070; the binding contract
("Selector and value validation": adapters; "Detection and performance": bindings). PR B2, wave W1.
BASE: the W0 head, filled in at dispatch. `tests/role_contract.py` (`ADAPTERS`, `TEMPLATE_CASES`,
`violations`, which deliberately skips the adapter) and `RoleContractTableTests(RoleSheetCase)` in
`tests/test_role_protocol.py` exist only from the W0 head. Worktree `C:/fks/t4`, task id `4`. Codes in
parallel with R2.S3 (Studio, disjoint files) and lands with it in one commit. Line budget: about 1,200
material lines (bridge about 200, tests about 1,000); explain any excess.

## Why

PR B shipped the role preview for plain pages. On a Bootstrap 5 page the bridge should suggest Bootstrap's
own roles, set Bootstrap's font variables for the body and code roles, and still check every role's
effect on its own selectors. Studio echoes the suggested adapter (R2.S3), so the bridge also re-checks it
at Apply.

## Owned files (exact)

- `fontkit-bridge.js` (also update its comment "Plain adapter only until R2.4").
- New `tests/test_role_adapters.py` (subclass `RoleSheetCase` from `tests/test_role_stylesheet.py`).
- `tests/test_role_stylesheet.py`: only `ApplyAndClearTests.test_only_the_plain_adapter_is_accepted_until_framework_adapters_land`
  (rename it, for example `test_a_bootstrap5_adapter_is_rejected_where_the_page_has_no_bootstrap5_evidence`,
  and update its docstring) and the `adapter-bootstrap` row of `AtomicRejectionTests` (rename it
  `adapter-bootstrap-without-evidence`; its expectation is unchanged).
- `tests/test_role_protocol.py`: only `RoleContractTableTests`, extended as in the tests below.

Read-only: `fontkit-studio.html`, `tests/role_contract.py`, `tests/support.py`, `tests/role_support.py`,
fixtures, every other test module. Variants are built in the test module: either mutate the loaded
fixture with `frame.evaluate` before `hello` (the `PreviewCase.author` pattern, `test_role_preview.py:87-93`),
or open the fixture URL, register a later `page.context.route(url, ...)` that fulfils the changed bytes plus
`<script src="/fontkit-bridge.js"></script>`, call `page.reload()` and re-find the frame. `role_support.py`
stays unchanged and nothing is written under `fixtures/` or `tests/fixtures/`. Any page state a test needs
is set before `hello`: a later attribute, DOM or stylesheet change advances the page version (D063) and
makes Apply `page-changed`.

## Read first

`constraints.md`; the plan's binding contract, Addenda 16-18; D068-D070; `tests/role_contract.py`; the
review of this brief, `task-4-brief-review.md` (its probe log describes the BASE behaviour of every page
below); in `fontkit-bridge.js`: `ROLE_ADAPTERS`, `canonicalizeRoles` (its output hard-codes
`adapter: 'plain'`), `serializeRoleCss`, `roleShapeError`, `handleRoleMutation`, `installRoleSheet`,
`verifyRoleSheet` (and its second caller in `attributeLoss`), `suspendRoleSheet`, `releaseRoleQuiet`,
`detectTextStyles`, `collectRoleStyles`, `roleBindings` (its `choose()`), `styleSignature`, `familyNames`,
`measureRoleOutcomes`; the F1 records `docs/implementation/tasks/r2-task-f1-{brief,report}.md` (the
fixtures' `unknownVersionVariant` metadata predates D069: a banner-less Bootstrap 5 copy still has both
variables, so never use it as the no-evidence page; use Bootstrap 4 or a one-variable page). The plan's
`detectRoleAdapter()` name is illustrative; name the new function as you see fit.

## Behaviour to build

1. **Every detected group carries `adapter`**, one of `ADAPTERS`. Set `adapter: 'plain'` in the group
   literal when the group is created in `collectRoleStyles`, and overwrite it after the binding pass, so
   groups in incomplete replies (`element-limit`, `identity-limit`, `group-limit`, `variant-limit`) carry it
   too: Studio validates every group of every reply.
2. **Bootstrap 5 evidence** (Addendum 17 item 2): computed `--bs-body-font-family` and
   `--bs-font-sans-serif` on `document.documentElement` are both non-empty after trimming. Both come from
   the app's own CSS, never from a live preview.
   - Scan: once, at the top of `collectRoleStyles` before its first `yield` (inside the first batch, where
     `detectTextStyles`' `run` already suspended the owned sheet), together with the computed
     `--bs-font-monospace` and `styleSignature(document.body)`; keep the four values on the job.
   - Apply: only when the request holds a non-plain role, in `handleRoleMutation` after the page-changed and
     unavailable-URL checks and before `canonicalizeRoles`:
     `const restore = this.suspendRoleSheet(); try { read } finally { restore(); this.releaseRoleQuiet(); }`.
     `suspendRoleSheet` attaches the page-wide `transition: none !important` node; only `releaseRoleQuiet`
     removes it.
3. **Bindings on Bootstrap 5 pages.** The order becomes: author role, author id, then (evidence only) the
   heading level, then shared classes, then DOM paths. A group is a heading-level candidate when every
   element is the same level N (1-6) by tag `hN` or class `.hN`, or every element carries the same
   `.display-N` class and no `.hN`; an element whose tag level and class level differ is not a candidate.
   Its candidate selectors are those of `hN` and `.hN` that match at least one of its elements (or
   `.display-N`), checked by the existing `choose()` rule: valid, every match is a member, and the members
   are covered. Reason `'class'`, stable. Author roles and ids keep winning (global rule 3). A group whose
   heading step fails `choose()` falls through to the class step. Every other binding rule is unchanged.
4. **Suggestions** (evidence only; at most one body and one mono group per scan):
   - `bootstrap5-heading`: the heading step of rule 3 chose the group's bindings (`hN`, `.hN` or both, or
     `.display-N`). A group whose heading step failed, and a group of mixed levels, stay `plain`.
   - `bootstrap5-mono`: the group has one signature, and its family compares equal (`familyNames`) to the
     computed `--bs-font-monospace`. If more than one group qualifies, none gets it.
   - `bootstrap5-body`: the group has one signature, equal to `styleSignature(document.body)`. If more than
     one group qualifies, none gets it.
   - A group that qualifies twice takes heading, then mono, then body.
   - Names, evidence pages only (pages without evidence keep `Text`; a group with an author role keeps its
     role name), the first that applies: `Heading N` (all elements are one heading level N, rule 3's
     predicate), `Display N` (all carry one `.display-N`), `Monospace` or `Body` (the group that takes that
     adapter), then the first entry of this list, in the list's order, whose class is among the group's
     shared classes: `lead` `Lead`, `small` `Small`, `btn` `Button`, `nav-link` `Navigation link`,
     `navbar-brand` `Brand`, `card-title` `Card title`, `form-label` `Form label`; else `Text`. The name does
     not depend on which binding step won; only the adapter does.
5. **Serialization** (Addendum 17 item 1): a `bootstrap5-body` or `bootstrap5-mono` role with `fontFamily`
   emits its `:root` block, then its unchanged plain block; without a family, only the plain block; heading
   and plain roles emit only the plain block; request order, never merged. `canonicalizeRoles` keeps each
   role's adapter in its output. The digest and `MAX_ROLE_CSS_BYTES` cover the whole sheet. Both callers of
   `verifyRoleSheet` (`installRoleSheet` and `attributeLoss`) pass the count of CSS blocks, not of roles, for
   its rule-count fallback. `TEMPLATE_CASES` are the byte oracle.
6. **Apply verification** (D068): `plain` as today. Any `bootstrap5-*` role needs the evidence now (rule 2).
   A heading role's selectors must be exactly what rule 3's heading step can emit (`hN`, `.hN` or both for
   one level, or one `.display-N`). Any failure rejects the whole request as `unsupported-value` with detail
   `Unsupported adapter`, before anything is written (revision, accepted state and DOM unchanged).
7. **Unchanged:** measurement and outcomes use each role's selectors exactly as for plain roles; a loss
   whose author winner's value uses `var()` reports `complex-cascade` (R2.5's closed-world proof); Clear
   removes only the owned node; the D067 transition ban also covers Bootstrap's own transitions.

## Tests (`tests/test_role_adapters.py`), each against the real bridge

Literal expectations come from the fixtures' `expected-styles.json`, `tests/role_contract.py`, the
vendored CSS and this brief, never from the bridge. Each new test method has a Given/When/Then docstring
whose Then is exactly what it asserts.

- RED, the Bootstrap 5 fixture's suggestions and names (the fixture's author ids win, so no heading
  bindings there): adapter `plain` unless stated: 40/500 `Heading 1`; 32/500 `Heading 2`; 28/500
  `Heading 3`; 24/500 `Heading 4`; 20/500 `Heading 5`; 16/500 `Heading 6`; 80/300 to 40/300 `Display 1` to
  `Display 6`; 20/300 `Lead`; 14/400 `Small`; 16/400 `Body` (`bootstrap5-body`: `bs.hero.cta`,
  `bs5.button`, `bs5.navigation`, `bs5.label`); 20/400 `Brand`; the `Editorial` and `editorial` author-role
  groups unchanged. A variant with one text element per remaining class (`btn`, `nav-link`, `card-title` on
  a `div`, `form-label`), each with its own inline font size so it forms its own group, gives `Button`,
  `Navigation link`, `Card title`, `Form label`.
- RED, template bytes: every `TEMPLATE_CASES` entry (a subTest per name) on the Bootstrap 5 fixture: apply
  `case['roles']`; `reply['roles'] == case['roles']`, `canonicalCss == case['css']`, `cssHash ==
  case['hash']`, the owned node's text equals the css, and the computed variables change exactly where the
  case says (body: both; mono: `--bs-font-monospace`; the others: neither). For the `body` case: outcomes
  `matched 3, checked 3, mismatched 0, losses []`; `bs.hero.cta`, `bs5.button` and `bs5.navigation` compute
  `Inter` and 18px; `bs5.label` still computes sans-serif and 16px; computed `--bs-body-font-family` and
  `--bs-font-sans-serif` (`.strip()`) equal `Inter`.
- RED, the detected group as received: apply the suggested body group (its adapter and its four
  selectors) with `fontFamily: 'Inter'`, `fontSize: 18`. All four elements compute them; the receipt's roles
  equal the request and its outcomes are `matched 4, checked 4, mismatched 0`; `canonicalCss` equals this
  literal, written in the test from Addendum 17 item 1 (never taken from the reply):
  `':root {\n  --bs-body-font-family: Inter;\n  --bs-font-sans-serif: Inter;\n}\n[data-design-id="bs.hero.cta"], [data-design-id="bs5.button"], [data-design-id="bs5.navigation"], [data-design-id="bs5.label"] {\n  font-family: Inter;\n  font-size: 18px;\n}\n'`.
- Clear (after each apply): both variables return to the values the test read from the page before Apply
  (the vendored stack), the elements to their pre-apply computed styles, and `main`'s outerHTML (read on the
  frame) is byte-identical.
- Id-less variant of the Bootstrap 5 page: heading groups bind `hN, .hN` pairs (or one of them) and display
  groups `.display-N`, are `bootstrap5-heading`; applying a Heading 2 or 3 role (not Heading 1: `.hero h1`
  in `app.css` wins there) renders its size on its own level only (the next level's computed size is
  unchanged).
- Heading fallbacks (id-less variant plus `<h2 class="fs-6">Small h2</h2>`): the Heading 2 group's `h2`
  also matches a non-member, so `choose()` fails and the class step binds `['.h2']` (reason `class`,
  stable); its adapter is `plain`, its name `Heading 2`. The `h6.h6` + `h2.fs-6` group has mixed levels,
  binds by DOM path and is `plain`. Applying the Heading 2 selectors leaves the `fs-6` heading at 16px.
- Mono variant with two `<code>` elements: one group named `Monospace`, count 2, `bootstrap5-mono`; send
  `TEMPLATE_CASES['mono']` unchanged (selectors `code`); computed `--bs-font-monospace` equals
  `"JetBrains Mono"` including quotes, and both elements render it. (The group's own selectors are DOM
  paths, stable false.)
- The Bootstrap 4 fixture: every group is `plain`; a plain role with a family and a size on its body-tuple
  group (`btn`, `nav-link`, `form-label`) renders on the three elements, `canonicalCss` has no `:root`
  block, computed `--bs-body-font-family` stays empty, the receipt's adapter is `plain`, Clear restores;
  each `bootstrap5-*` adapter there is rejected (`unsupported-value`, `Unsupported adapter`), nothing
  written. The protocol target page is covered by the converted R2.3 test.
- Evidence needs both variables: the protocol page plus an injected `:root` rule defining only
  `--bs-body-font-family`, then only `--bs-font-sans-serif`, gives `plain` everywhere (with a text parent
  that inherits body's style, so a body suggestion would otherwise appear).
- Ties and precedence, on the protocol page plus an injected `:root` rule defining both variables: an
  author-role paragraph and an automatic paragraph that both equal body's style get no body suggestion; two
  groups whose family equals `--bs-font-monospace` (say `code` at 14px and `samp` at 16px) get no mono
  suggestion; `<h2>` elements styled `font-size: 1em; font-weight: 400` equal body's style and nothing else
  does: that group takes `bootstrap5-heading` and no group takes body; with `--bs-font-monospace:
  monospace` and `body { font-family: monospace }` the one inheriting group takes `bootstrap5-mono`, not
  body.
- A non-Bootstrap page that defines both variables (with a text parent that inherits body's style) gets
  the body suggestion: the cost D069 records, pinned (RED at BASE, which has no `adapter` field).
- Apply-time re-check: detect on the Bootstrap 5 page, remove its Bootstrap `<link>`, detect again (the
  groups are now plain and the page version is new), then apply the earlier body suggestion with the new
  version: rejected `unsupported-value` / `Unsupported adapter`, nothing written. (A stylesheet, DOM or
  viewport change advances the page version, D063, so an honest Studio reaches this check only through an
  unobserved change, such as an adopted stylesheet or a media-feature flip, or a client that sends a stale
  adapter.) A heading role whose selectors name two levels is rejected the same way.
- Evidence comes from the app, not the preview: apply the `body` case (the preview now defines both
  variables), remove the Bootstrap `<link>`, Detect (every group is `plain`), then Apply `bootstrap5-body`
  with the Detect's `currentPageVersion`: `unsupported-value` / `Unsupported adapter`; preview, owned node and
  revision unchanged.
- No transition ban survives an Apply: with a preview already live, apply the `body` case; afterwards no
  `style` element whose text contains `transition: none` is in the document, and `.btn` still computes the
  vendored `transition-duration` (`0.15s, 0.15s, 0.15s, 0.15s`).
- Detect with a live Bootstrap 5 preview returns the groups of a Detect without it, and their styles equal
  expected-styles.json (the preview values never appear).
- An `html` element with an inline `style` (`--bs-body-font-family: Serif-Inline`), put in the served bytes
  or set before `hello`: Apply cannot override it (the role's plain rule still applies to its selectors),
  and Clear leaves the inline `style` attribute byte-identical.
- A variant whose author CSS adds a higher-specificity rule with a `var()` font size on the body group's
  elements: the receipt reports their `fontSize` losses as one `complex-cascade` entry (count 4, null
  winning selector; `matched 4, checked 4, mismatched 4`); the same apply without that rule has
  `mismatched 0` and no losses. (On Bootstrap pages any such loss is `complex-cascade`: Bootstrap's own rules
  declare these sizes with `var()` or rem.)
- Whole-sheet limit: a body role whose sheet, `:root` block included, is exactly 128 KiB installs; one byte
  more is `size-limit`.
- Rule-count fallback: serve the bridge through `bridge_source=` with a first line
  `Object.defineProperty(window,'CSSStyleSheet',{value:undefined,configurable:true,writable:true});`, apply
  the `body` case: `design:roles-applied`, and one forced loss still reports its normal reason, not
  `stylesheet-blocked`.
- `RoleContractTableTests`: for the `group-limit` and `variant-limit` replies and for a Detect on the
  Bootstrap 5 fixture, every group's `adapter` is in `ADAPTERS`, and the fixture reply holds at least one
  non-plain value.

## Mutants (one per new test; foreground, restored byte-exact with SHA-256; or served through `open(bridge_source=...)`)

Each new test names one realistic mutant of the behaviour it pins and shows it failing. Examples: remove
the evidence check (Bootstrap 4 and protocol-page tests); evidence needs one variable only (one-variable
pages); read the variables without suspending the sheet (evidence-from-the-app test); drop
`releaseRoleQuiet()` (no-leak test); heading step before author ids (fixture RED); drop the heading member
check (`fs-6` variant); echo `adapter: 'plain'`, emit `:root` for a plain or heading role, merge or reorder
blocks, swap the body variables (template cases); write the mono variable under the body name or compare
families as raw strings (mono variant); write the variables inline (inline-style test); skip the Apply
re-check; swap two entries of the names list (names variant); count roles instead of blocks (fallback test);
omit `adapter` from a group created before the binding pass (`RoleContractTableTests`). Report each with its
command and failing line.

## Focused gate

From the worktree, in Git Bash, after `tools/link-fixtures.ps1 -Worktree C:/fks/t4` (the controller does
this before dispatch):
`sh "C:/Users/peter/Python Projects/font-kit-studio/.superpowers/sdd/r2/tools/gate.sh" focused test_role_adapters test_role_detection test_role_stylesheet test_role_preview test_role_protocol test_r2_react test_r2_static_fixtures test_support`
Studio integration modules are expected to fail on this patch alone (Studio rejects the new field until
R2.S3); do not run them. Also `node --check fontkit-bridge.js`, Ruff on the changed test files and, after
staging by name, `git diff --cached --check`.

## Report and handoff

Report: what changed by file and function; RED (command, failing assertion) and GREEN; each new test's
oracle and mutant; focused output; material lines; deviations with the rule that forced them. Handoff: the
patch, the commit subject `feat(bridge): suggest and apply Bootstrap 5 font roles` (landing together with
R2.S3 may change it), a draft body (why, wrapped at 72, no process narration), and the R2.4 plan items done.
CHANGELOG wording is drafted by R2.S3; say only that the bridge comment was updated.
