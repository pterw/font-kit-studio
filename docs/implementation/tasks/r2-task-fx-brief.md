# R2.7I2 brief: three Firefox canary smoke tests for roles

Plan: `docs/plans/2026-10-03-r2-engine.md` Addendum 25 (slice R2.7I2, wave W3) and the task R2.7I checkbox "Add at most
three focused Firefox canary methods: role-selector hostility, real Studio apply/clear round trip, and same-document
route freshness ... report Gecko differences as advisory. Keep the existing canary and full Gecko suite policy (D037)."
BASE `5d28252fb6acf52b1287d7f90054d70b49ae249e` (source read at this commit; the controller replaces it with the
landing SHA of R2.6B2 and R2.6S if they are not in it). Worktree `C:/fks/tfx` (detached at BASE; the controller creates
it and links fixtures), task id `fx`. Line budget: about 90 gross lines.

## Why

The Firefox canary (`tests/firefox_canary.py`, 34 lines) loads whole classes by name and has no role coverage, so a Gecko
difference in the role sheet, the route announcements or Studio's role UI would reach the release unseen. CI runs it as an
advisory step (`.github/workflows/quality-gate.yml` 187-201); D037 keeps it advisory and keeps the full suite on Chromium.

## Owned files (exact)

- `tests/firefox_canary.py` only: add imports, two small TestCase classes holding exactly three test methods in all, and
  their two names in `CANARY`. Keep every existing `CANARY` entry, the docstring (extend it by one sentence) and
  `load_tests` unchanged.

Read-only: every other file, including `tests/test_support.py` (`CanaryListTest` resolves each `CANARY` name to a
TestCase class with tests, so `firefox_canary.<Class>` names work with no edit there) and all modules imported below.

## Read first (line numbers at BASE; re-check them)

- `tests/firefox_canary.py` (all). `tests/test_support.py` 312-340 (`CanaryListTest`).
- `tests/role_support.py` 1-80 (`RoleBridgeCase.open`: D059 guard, regex route `^https://` with the local fallback
  registered first and the abort second, counts asserted `{'abort': 2, 'fallback': 0}` before and after navigation).
- `tests/test_role_stylesheet.py` 35-62 (`role()`, `RoleSheetCase.apply/clear/size/owned`), 259-360
  (`hostile_cases`), 359-378.
- `tests/test_role_route_bridge.py` 14-45 (`RoleRouteCase.start/notices/urls`), 48-66, 148-156.
- `tests/test_studio_roles.py` 124-170 (`StudioRoleCase.open`, the same D059 guard), 239-262 (`control`, `type_value`,
  `button`, `preview`), 1415 (`StudioLegacyCase`).
- `tests/test_r2_integration.py` 186-189 (`CAPTURE`), 246-340 (`StudioRoleBridgeTests` helpers and the apply/clear test).

## Requirements

Structure. Two classes, `BridgeRoleSmokeTests(RoleRouteCase)` (methods 1 and 3) and `StudioRoleSmokeTests(StudioLegacyCase)`
(method 2), import the bases from `test_role_route_bridge` and `test_studio_roles`. Subclass the case classes, never a class
that holds tests (`RoleRouteCase` and `StudioLegacyCase` hold none; confirm with `loadTestsFromTestCase(...).countTestCases()`
before use, else report). Loop `for engine in ENGINES` with `subTest(engine=engine)` as the sources do; the canary runs with
`FKS_ENGINES=firefox`. Use only the static fixtures `tests/fixtures/bridge/target-role-protocol.html` (`ROLE_PAGE`) and
`fixtures/multi-page/spa.html`; no npm install, no new helper in a shared file, no second `sync_playwright` driver. Both
bases open pages through the D059 guard (regex `^https://`, abort route, fallback first, counts asserted); do not bypass it
or open a context any other way.

1. `test_role_selector_hostility_is_rejected_whole_and_keeps_the_preview` (bridge class). Given an accepted 24px
   preview on the role page (`self.open(engine)`, `frame.evaluate("document.body.classList.add('on-body')")`,
   `self.hello(page)`, `self.apply(page, [role(fontSize=24)])`, revision 1), when each of these hostile selectors is sent
   as a one-role apply, then each reply is `design:rejected` with reason `unsupported-value`, `reply['revision'] == 1`,
   `self.owned(frame) == [PLAIN_24]`, the `.body-copy` computed font-size is `24px`, and `main` outerHTML is unchanged.
   Selectors (oracle: the literal reasons in `test_role_stylesheet.py` 330-343, which come from the binding contract's
   selector rules, not from the code): `.a, .b`, `:root`, `body`, `.on-body` (matches body), `p[title="x"]`, `p:hover`,
   `.a{`, `.a;`, `.a}`, `.a\n.b`. Also one non-selector hostile case: a role dict with an own `__proto__` key, built with
   `json`-style parsing in the page, if and only if `AtomicRejectionTests.test_own_proto_key_...` (395) shows a short way
   to send it; otherwise omit it. Assert `self.errors(frame) == []`.
2. `test_real_studio_apply_and_clear_round_trip` (Studio class). Given the real Studio against the real bridge on the
   role page (copy `CAPTURE` as a module constant; `page, frame, errors = self.open(engine, init=CAPTURE)`, then
   `self.detect(page)` whose status contains `Detected`), when Body is checked, given `24` through `self.type_value`
   (keystrokes) and applied with the `Apply selected roles` button, then the `[data-design-role="Body"]` paragraph renders
   `24px` while `[data-design-id="ordinary.body"]` stays `16px`, `main` outerHTML is byte-equal to before, and
   `self.preview(page)['css']` contains `font-size: 24px`; and after the `Clear preview` button, the status reads
   `Preview cleared.`, `self.preview(page)['css'] == ''` and both paragraph sizes and `main` outerHTML equal their values
   before the apply. Wait on conditions (`frame.wait_for_function` on the computed size, or a `roles-applied` entry in
   `__s2b.inbound`), not sleeps. Assert `errors == []`. Copy only the few helper lines needed (a private `look`, `size`
   and wait); do not call `StudioRoleBridgeTests` unbound (it holds tests and its helpers share state).
3. `test_a_same_document_route_change_is_announced_with_a_fresh_page_version` (bridge class). Given the role page after
   hello (`self.start(engine)`), when `history.pushState({a: 1}, '', '?route=x')` runs in the frame, then exactly one
   `design:roles-page` arrives with `pageURL == ROLE_PAGE + '?route=x'`, a `pageVersion` greater than
   `ready['roleState']['pageVersion']`, the key set `{'type','protocolVersion','sessionId','documentId','pageVersion','pageURL'}`
   and `documentId` equal to the ready's; the body text is still `Author body`; and `self.detect(page)['pageVersion']`
   equals the announced version. Then, on the SPA fixture (`self.start(engine, SPA)` with `SPA = TARGET + '/fixtures/multi-page/spa.html'`,
   defined locally), `frame.evaluate("render('same')")` yields one announcement with `pageURL == SPA` and a greater
   version. Oracles: the plan's "Messages" text for `design:roles-page` and Addendum 25 slice R2.6B1; the key set is a
   literal (also `tests/role_contract.py`), never read from the bridge.

If any assertion fails only on Firefox while the same assertion passes on Chromium, the code is correct and the engines
differ: report it and stop. Do not special-case the engine, loosen the assertion, add a sleep or skip. Quote the failing
line and both engines' values in the report as an advisory finding.

## TDD

These tests characterize behaviour that already works, so there is no RED: run each first on Chromium
(`FKS_ENGINES=chromium`, to prove the assertions on the engine that already passes the sources), then on Firefox (the
purpose). One realistic mutant per test, run under Firefox, shown failing, the source restored byte-exact with SHA-256
before and after (scratch copy of `fontkit-bridge.js` or `fontkit-studio.html` in the worktree; scratch names carry
`fx`):

- Method 1: make the bridge accept `:root` (for example remove `:root` from the selector rule's refusal in the validator) and
  the `:root` case must fail on the reply type.
- Method 2: make Clear skip the owned-sheet removal (the bridge's `design:roles-clear` handler leaves the node) and the
  after-Clear size and `css == ''` assertions must fail.
- Method 3: drop the `history.pushState` wrapper's announcement (the wrapper calls the native method but does not
  schedule the send) and the push must produce no `roles-page`, failing the notice assertion.

Locate each mutation point with Grep in `fontkit-bridge.js`/`fontkit-studio.html` at the worktree; if a mutant cannot be
made small, pick the nearest equivalent and say so. If the file named by the plan task is changed by R2.6B2/R2.6S, use the
landed text.

## Focused command

From the worktree (the only way the canary is run; CI uses the same module):

```
cd C:/fks/tfx && PYTHONPATH=tests FKS_ENGINES=firefox python -m unittest firefox_canary -v
```

Then once on Chromium for the new classes only:
`PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest firefox_canary.BridgeRoleSmokeTests firefox_canary.StudioRoleSmokeTests test_support -v`.
Also `python -m ruff check tests/firefox_canary.py`. Report Firefox availability; an engine that did not run is
reported as not run, never as verified. The existing nine canary entries must still pass (record the test count before
and after).

## Handoff (for the landing)

Commit subject: `test: add role smoke tests to the Firefox canary`. Draft a why-body (wrap at 72): Gecko previously had no
coverage of role selector hostility, Studio's apply and clear, or route announcements. Draft a ledger line in product
terms with the Firefox test count, the Gecko differences found (or none) and that the canary stays advisory (D037).

## Open questions

1. Plan wording says "methods"; the three need two classes because the bridge and Studio cases have different bases.
   Recommendation: two classes, three methods (as written). Alternative: one class on `StudioLegacyCase` driving method 1
   and 3 through Studio, which is heavier and tests less of the bridge boundary.
2. Method 3 covers both the history push and the SPA render swap in one method. Recommendation: keep them together to
   stay at three methods; split only if the owner lifts the cap.

## Controller rulings (2026-10-18)

- BASE stays `5d28252fb6acf52b1287d7f90054d70b49ae249e`: it is the R2.6S landing commit and already contains R2.6B2
  (252e0ac) and R2.6B1 (2b70e29); the drafter's note to replace it is mistaken.
- Open question 1: as recommended, two classes (`BridgeRoleSmokeTests`, `StudioRoleSmokeTests`) holding three methods
  in all, named in `CANARY`.
- Open question 2: as recommended, the route-freshness method covers the `pushState` announcement and the SPA
  `render('same')` swap.

## Revision 1 (2026-10-18; brief review findings folded by the controller, `task-fx-brief-review.md`)

- I2: method 1's mutant is a single edit: drop `|| el === document.body` at fontkit-bridge.js ~163 (the `.on-body` case
  then fails on the reply type under Firefox); the `:root` refusal needs two edits and is not the mutant. Method 2's
  mutant: a Clear that leaves the role sheet node (`roleSheet.remove()` ~1565 skipped); it is killed only by the
  after-Clear computed size, so that assertion is required and named as the killer.
- I1: the focused command runs only the two new classes under Firefox:
  `PYTHONPATH=tests FKS_ENGINES=firefox python -m unittest firefox_canary.BridgeRoleSmokeTests firefox_canary.StudioRoleSmokeTests -v`
  plus `CanaryListTest` and test_support under Chromium; the canary's total count (51 -> 54) comes from a browser-free
  collection (`python -c` loading the suite and counting), not a full local canary run (constraints: the full canary
  runs locally once at the release point).
- Minors: adopt the review's five fixes as written (the `__proto__` case expects `invalid-message`; hostile fontSize
  30; budget about 120 lines; import `SPA` and `KEYS` instead of redefining them; do not rely on the peer-only
  `received` helpers).
