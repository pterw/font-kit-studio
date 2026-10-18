# R2.6B2 brief: BFCache lifecycle, route-evidence guards and the revision-1 key sets on the bridge

Plan task R2.6B part 2 (`docs/plans/2026-10-03-r2-engine.md`, "R2.6B", last three checkboxes), Addendum 25 (row R2.6B2),
Addendum 24 (the W2 review Minors), Addendum 26 and the R2.6B2 items of `.superpowers/sdd/r2c/w2-carryovers.md`. Wave W2.
BASE `<RV-LANDING>` is not used here: read and build on commit `2b70e29fa7284fa4792dfa35f044ee0a37521641` (R2.6B1 landed).
Worktree `C:/fks/t6b2`, task id `6b2`. Line budget 375 gross lines (JS about 25; tests about 325; comment and test-edit
fixes about 25; the Revision 1 changes net about -5: the duplicate 3b is dropped, the registration spy, the pagehide-only
subtest and the nested-key checks are added). R2.6S runs beside you on `fontkit-studio.html` and `tests/test_role_routes.py`: never touch them.

R2.6B1 is on BASE: read `docs/implementation/tasks/r2-task-6b1-{brief,report,review}.md` and build on it
(`bumpRolePage`, `scheduleRolePage`, `sendRolePage`, `expireRolePageHold`, `installRoleHistory`/`removeRoleHistory`,
`ROLE_PAGE_GAP_MS`, the rule "every wire `pageVersion` advance is announced", `tests/test_role_route_bridge.py`). Do not
re-specify or refactor it.

## Why

Most of this task is proof, not new code. At BASE (`fontkit-bridge.js`):

- A page restored from the back/forward cache keeps its JS state but has no listener for it: `grep pageshow\|pagehide`
  finds nothing. A Detect that straddles the freeze replies as complete, and a URL the restored page now holds is not
  announced until some other event happens. The plan (Route observation) says to track `pageshow`/`pagehide`.
- Already satisfied, to be characterized GREEN and not re-implemented: the baseline selector check per known role
  (`collectRoleStyles`, lines 2160-2166 of BASE: one `SelectorCheck` per known selector, `matchCount` = sum of the
  variants' counts) read inside `run`'s batch with the owned sheet off and restored in `finally { restore(); }` (2062,
  2075; D067). Tests that already pin it: `test_role_stylesheet.BaselineDetectTests.test_detect_reports_the_app_baseline_while_the_preview_keeps_rendering`,
  `...test_detect_never_drops_the_preview_between_frames_on_the_5000_parent_corpus`, `test_role_detection` (lines 555-578,
  `matchCount` [2, 0, 1, 1]), `test_role_adapters.PlacementTests` (704, body check). Do not duplicate them.
- Several listed scenarios are already tested in `tests/test_role_route_bridge.py` (R2.6B1): URL-only push/replace/hash/back
  (47), popstate and hashchange alone (66, 76), a fast sequence of route kinds (107), same-URL content replacement on the
  SPA (147), HMR-like style node and viewport changes (157), a push inside and during a Detect (501, 518, 535),
  disposal and wrapper cleanup (399-465). Cite them; do not repeat them.
- Never proven by a test: that the stale-scan guards in `current()`/`fresh()` (2020-2026, Apply's 1569-1575), the
  baseline restoration and the wrapper-cleanup guards fail a test when removed (R2.6B's last checkbox: "No stale scan may
  present checked evidence for another route"). Section "Mutant sweep" below.

## Owned files (exact)

- `fontkit-bridge.js`: the new `pageshow`/`pagehide` listeners in `observeRolePage` (about line 1270) and two comments
  (Minors table rows "W2P 2" and "W2B1 2" in requirement 6). Nothing else.
- `tests/test_role_route_bridge.py`: new classes `LifecycleTests(RoleRouteCase)`, `DelayedRenderAndHmrTests(RoleRouteCase)`,
  `StaleScanTests(RoleRouteCase)` and `RevisionOneKeysTests(RoleRouteCase)`.
- Existing modules, only the edits named here: `tests/test_role_adapters.py` class `PlacementTests` (one new test, row
  "W2P 1"); `tests/test_role_stylesheet.py` class `InstallCountTests` (the skip, row "W2P 4 / W2B1 1");
  `tests/test_role_protocol.py` the comment above `AUTHOR_ROLES` (row "W2T"). Anything else is read-only.
  `tests/role_contract.py` belongs to R2.SK, and R2.6S owns its one `TOLERANT_KINDS` line: this slice does not edit it.

## Read first

- `fontkit-bridge.js` at BASE: 1256-1395 (cancelRoleJobs, noteRoleMutations, observeRolePage, refreshRolePage, bumpRolePage,
  send/hold, history install/removal); 2005-2080 (Detect job, `current`, `fresh`, `finish`, `run`); 2085-2175
  (`collectRoleStyles`, selector checks); 1540-1580 (Apply's own freshness helpers); 817-830 (`dispose`); 787-790 (`listen`).
- Plan: Route observation (1022-1053), R2.6B (1407-1426), Addenda 25 and 26, "Messages" (803-860) and the type block (757-796).
- `tests/test_role_route_bridge.py` 1-46 (`RoleRouteCase.start/notices/silence/urls/proof`) and 469-576 (the Detect
  patterns: dispatch in the same task as the mutation, read the reply from the host log by requestId).
- `tests/role_support.py` (`RoleBridgeCase.open(bridge_source=...)`), `fixtures/multi-page/spa.js` (the delayed render
  buttons `#load-delayed`, `#resolve-delayed`), `fixtures/large-page` (the multi-slice scan page).

## Requirements

Oracles are plan text or literals written in the test; never a value read from the bridge under test.

1. **BFCache lifecycle (RED; JS change).** After the first hello the bridge listens (through `this.listen`, so dispose
   removes them) for `pageshow` and `pagehide` on `window`. The handler moves the internal epoch (`this.roleNative += 1`
   when `this.active && this.studioSource`, the same guard as the pointer and font listeners) and calls
   `this.scheduleRolePage()`. It never calls `bumpRolePage()` itself: the wire `pageVersion` advances only through
   `refreshRolePage` when the URL, author stylesheet or viewport really changed (D063/D066, the one rule). Class
   `LifecycleTests`, events built as `new PageTransitionEvent('pageshow', {persisted: true})` and
   `new PageTransitionEvent('pagehide', {persisted: true})` and dispatched on `window` in the target frame (Playwright
   cannot freeze a page; the dispatch is the lifecycle signal, as `popstate` is dispatched alone in test 66).
   Real BFCache does not occur under Playwright Chromium (reviewer probe: going back reloads the page, JS state is lost,
   `pageshow.persisted` is false, and the target is an iframe besides). So 1a-1d prove the handler wiring, not the
   browser's restore: say so in the class docstring and in the report, and keep the README line that a page frozen
   without a `pageshow` event is seen only by the next Detect:
   a. Given a URL changed through the cached native `History.prototype.pushState.call(history, ...)` (no wrapper, no
      announcement: 300 ms of silence first), when only `pageshow` (persisted) is dispatched, then exactly one
      `design:roles-page` follows with the literal new URL and a version greater than the ready's. RED at BASE.
   b. Given nothing changed, when `pagehide` then `pageshow` are dispatched, then 600 ms later no `design:roles-page` was
      sent and a Detect reports the ready's `pageVersion`. GREEN at BASE (characterization of the one rule).
   c. Given a Detect running on the 5,000-element large page (started as in test 518, reply not yet posted), when
      `pagehide` and `pageshow` are dispatched, then the reply is incomplete with reason `page-changed`, its
      `pageVersion` equals its `currentPageVersion` (unchanged), `pageURL` equals `currentPageURL`, no
      `design:roles-page` was sent, and a fresh Detect is complete. RED at BASE (BASE replies complete). This is the
      "no stale scan presents checked evidence" proof for the lifecycle. Subtests, each with its own Detect: `pagehide`
      then `pageshow`; `pagehide` alone (a page leaving for the cache whose restore event has not arrived: the in-flight
      Detect must still end `page-changed`, which kills the "pageshow only" mutant); `pageshow` alone.
   d. Registration, observed directly. Reviewer probe: a leaked `window.addEventListener` handler is inert on the wire
      after dispose (`disposed`, `active` and a nulled `studioSource` stop it), so a "nothing is sent" assertion cannot
      tell `this.listen` from a direct `addEventListener`. Instead run the bridge from an in-memory copy of its source
      (`RoleBridgeCase.open(bridge_source=...)`) prefixed with a spy that wraps `window.addEventListener` and
      `window.removeEventListener` and records every `pageshow`/`pagehide` call as `(type, handler, capture)`. Given the
      page added its own `pageshow` listener through the spy before hello, when hello is sent, then the bridge has one
      registration for each of `pageshow` and `pagehide`; when `__fontkitBridge.dispose()` runs, then every bridge
      registration has a matching removal (same type, handler and capture), the page's own listener has none, and it
      still fires on a dispatched `pageshow`. A URL change through the cached native method plus `pageshow` after dispose
      sends nothing (a secondary check). The direct-`addEventListener` mutant leaves a registration without removal.
2. **Delayed render and HMR (expected GREEN; class `DelayedRenderAndHmrTests`).**
   Real Vite hot updates are already covered by `tests/test_r2_react.py` (349, 594, 648); these simulated tests need no
   fixture and are not a gap in that coverage.
   a. SPA page, interact mode: click `#load-delayed`. Then one `design:roles-page` names `?route=delayed` while
      `#route-content[data-render-state="pending"]`. Click `#resolve-delayed` (no fixed sleep: a click inside the 250 ms
      hold still yields the second notice at the hold's trailing edge, and `notices(..., settle=500)` outlasts it). Then a
      second `design:roles-page` with the same URL and a greater version arrives after the new nodes render (the heading
      text is `Delayed evidence`), and a Detect reports that version and the group sample `Delayed evidence`. The
      `subtree: false` mutant leaves the URL notice alone and is killed by the missing second notice.
   b. A CSS hot update, two subtests. "Text replace": the role page's `<style>` text is replaced in place
      (`style.textContent = '.body-copy { font-size: 30px }'` with another size before). "Href swap" (not Vite's own
      mechanism, which clones the link and removes the old one): a `<link rel="stylesheet">` added to the page before
      hello has its `href` swapped to another stylesheet (a `data:` URL or a Playwright-routed one; the target blocks no
      style source). Wait on a condition before Detect (the link's `load` event or the computed size), not a sleep. Then
      each update yields a `design:roles-page` with the same URL and a version greater than the ready's (compare with
      "greater than" only: reviewer probes saw +2 for the swap, a mutation bump plus a stylesheet stamp change in one
      refresh; a slow routed URL may split into two notices, so do not assert exactly one for the swap), and a Detect
      afterwards reports the new computed size (30px, literal). With a plain 24px preview applied first, the owned sheet
      is byte-identical afterwards (`self.owned(frame)` equals the earlier value) and no roles-page announced the Apply or
      the owned sheet's own mutations.
3. **Stale scans (class `StaleScanTests`).** Each test asserts the stale reply never carries `complete: True` for a page
   other than the one it names:
   a. Route A to B to C: Detect on the large page at route B (after a push and its notice), a second push to C while it
      scans. The reply names `pageURL` B and `currentPageURL` C, is incomplete `page-changed`, its `pageVersion` is below
      `currentPageVersion`, the last roles-page names C with `currentPageVersion`, only one `design:detected` carries
      that request id, and a fresh Detect is complete on C. (Test 518 covers a single push; this one pins the late B scan.)
   b. Dropped. A session change during a Detect (hello `s2`) duplicates
      `test_role_detection.test_latest_detect_hello_reset_and_dispose_suppress_old_jobs` (372-410): same page, same
      in-flight Detect, same "no `design:detected` for the old id under any session" assertion. Cite it; add nothing.
   c. A URL change that bypasses the wrapper (cached native push inside the page's `design:detect` listener, as test 501
      does with the wrapper) still ends the reply incomplete `page-changed` with `currentPageURL` the new URL. Add it
      only if the mutant sweep leaves the wrapper-dependent path unproved. It cannot kill M3a: M3a and M3c mask each
      other for every URL-only change. M3a dies only to a non-URL change that just the stamp sees (the 'style' action of
      `test_role_detection.py` near 418, or a same-task DOM mutation): find the existing killer or add that test.
4. **Revision-1 key sets (GREEN characterization; class `RevisionOneKeysTests`; carry-over from the R2.SK review).** One real-bridge test
   per message kind compares the exact key set of the posted message with a literal written from the plan's binding
   contract (the envelope keys `type`, `protocolVersion`, `sessionId` plus the body column of "Messages", and the type
   block for nested objects). `tests/role_contract.py` holds no key sets (its `violations` checks values and says it does
   not compare keys), so these literals are the oracle. Also assert `table.violations(kind, message) == []` with the kinds
   the table knows: `'detected'` for the Detect reply, `'roles-applied'` for the receipt, `'role-state'` for the ready's
   `roleState` (as `test_role_protocol.py:428` calls it). `violations` raises ValueError for any other kind and has no
   `'roles-page'` kind (R2.6S owns the one `TOLERANT_KINDS` line there): the page notice gets the key-set check only, and
   this slice does not edit `role_contract.py`. Before comparing nested keys, assert each nested list is non-empty
   (`signatures`, `selectors`, `selectorChecks` and their `signatures`, `losses`, `outcomes`, `roles`), so an empty list
   cannot let a missing or added nested key pass.
   - `design:detected` (use `knownRoles` with one matching selector, a page with a group so nested objects exist): top level
     `requestId revision documentId pageVersion pageURL currentPageVersion currentPageURL complete reason elapsedMs
     scannedElements groups selectorChecks`; each group `id identity suggestedName authorRole signatures elementCount
     sampleText sharedClasses selectors bindingComplete nearDuplicateIds adapter`; `identity` `kind name` (author role) or
     `kind style`; style `fontFamily fontSize fontWeight textTransform letterSpacing`; a signature `style count`; a
     selector binding `value stable reason`; a check `roleId selector matchCount signatures`.
   - `design:roles-applied` after an Apply with an author-rule loss (add an author `!important` rule so `losses` is not
     empty): top level `requestId operation revision documentId pageVersion currentPageVersion currentPageURL roles
     canonicalCss hashAlgorithm cssHash outcomesComplete outcomeReason outcomes`; role `id name selectors adapter
     properties`; outcome `id matched checked mismatched complete losses`; loss `property count winningSelector reason`.
   - `design:ready.roleState`: `documentId pageVersion pageURL roles canonicalCss hashAlgorithm cssHash`, with and without an
     accepted role.
   - `design:roles-page`: the existing `KEYS` (six keys including the envelope); assert it from a fresh message.
   A key the live bridge posts beyond the literal, or one the literal lists that it does not post, is reported, not
   "fixed" in either place (see Open question 2).
5. **Mutant sweep (R2.6B's last checkbox).** For each mutant below, run the named existing modules first (in-memory copy
   through `RoleBridgeCase.open(bridge_source=...)` or a scratch runner; the bridge file is never edited; SHA-256 before and
   after). A survivor gets the cheapest new test in `StaleScanTests`/`LifecycleTests` that kills it; a mutant no behaviour
   can distinguish is reported "equivalent" with the reasoning, and no test is added for it.
   - M1 `current()` without `job.session === this.sessionId`; M2 without `job.generation === this.roleGeneration`;
     M2b without `job.documentId === this.documentId` (lines 2020-2022). Expected equivalent: M1 (every `sessionId` change,
     at 1089 and 1203, follows `cancelRoleJobs()`, which moves `roleGeneration`, 1258, so the generation check still
     suppresses the reply) and M2b (`documentId` is assigned once, in the constructor, 662). Show it: run each against
     the existing modules, and report a survivor as equivalent with this reasoning; add no test. M2 is killable only where
     the generation moves with the session unchanged (a newer Detect, a rejection inside the iterator at 2093 before
     `finish` at 2030): run the existing modules first and name the killer.
   - M3a `fresh()` without its `this.refreshRolePage()` (2024); M3b without `job.native === this.roleNative` (2026); M3c
     without `job.pageURL === location.href` (2025; expected equivalent, because `refreshRolePage` has already advanced
     the version for a URL change, say so in the report with the probe that shows it).
   - M4 baseline restoration: `finally { restore(); }` at 2075 removed (the owned sheet stays disabled between slices);
     M4b `run` never calls `suspendRoleSheet()` (baseline would read the preview).
   - M5 Apply's freshness helper (1569-1575) without `job.session === this.sessionId`. Expected equivalent: the same
     helper also checks `job.epoch === this.roleEpoch` (1568), which moves with every session change (1086, 1195). Show
     it as for M1; no test.
   - M6 wrapper cleanup: `removeRoleHistory` without the `history[name] !== wrapper` guard (1389); `dispose` without
     `this.removeRoleHistory()` (828); `saved` descriptor not restored. (R2.6B1's table killed these; re-run and cite,
     add nothing unless one survives.)
   - M7 new code: handler without `roleNative += 1` (killed by 1c); handler calling `bumpRolePage()` (killed by 1b);
     listeners added with `addEventListener` instead of `this.listen` (killed by 1d's registration spy, not by any
     wire assertion); `pageshow` only, no `pagehide` (killed by 1c's `pagehide`-only subtest; not equivalent).
6. **W2 review Minors (bridge and bridge tests).** Verified at BASE; taken or left:

| Minor | Where | Verdict |
|---|---|---|
| W2P 2: comment says "Addendum 23 item 3" for the placement pass; placement is item 4 (item 3 is the mono fallback) | `fontkit-bridge.js:267` | TAKE: change to "item 4" |
| W2B1 2: the comment above `unquotedParenthesis` also describes the keyword refusal, which lives in `roleFamily` | `fontkit-bridge.js:193-194` | TAKE: move the keyword half next to the `roleFamily` regexp |
| W2P 1: no known role on `['BODY']` in Detect; a `soleBody` that lowercased would pass every test | `tests/test_role_adapters.py:704` | TAKE: new test in `PlacementTests`: Detect with `knownRoles` `[{id, selectors: ['BODY']}]` on the Bootstrap 5 fixture is `design:rejected` / `unsupported-value`; verify that at BASE first and record the observed reply. Mutant: `soleBody` compares `.toLowerCase()` |
| W2P 4 / W2B1 1: `skipTest` sits inside the engine loop, so `FKS_ENGINES=firefox,chromium` skips before Chromium runs | `tests/test_role_stylesheet.py:1335` | TAKE: `with self.subTest(engine=engine): if engine != 'chromium': self.skipTest(...)`. unittest records a skipped subtest and carries on, so Chromium still runs and Firefox is reported skipped, never passed silently |
| W2T: comment says sizes stay distinct "up to 100 roles" but the test uses 128 | `tests/test_role_protocol.py:295` | TAKE: say "199 roles" (the step of 2 exceeds `r / 100` up to 199) or drop the number |
| W2B2 1 (`range(16)`) | `tests/test_role_adapters.py` | ALREADY CLOSED (`range(table.SHARED_CLASSES)` in phase 2); verify and list as closed |
| Stale comments "before any evidence" (bridge ~1943) and "the transition ban the read set" (~1408) | bridge | ALREADY CLOSED at BASE (grep finds neither) |
| W2B2 2, 3, 4: two accepted survivors, literals `5000`/`2000`, docstring Then omissions | `test_role_stylesheet`, `test_role_adapters` | LEFT: margin choices and docstring text, no behaviour; record the survivors as accepted in the report |
| W2P 3 (`#corpus` no longer a variable-only witness); W2P 5 (mono fallback while other groups own some of the four tags, no test) | `test_role_adapters` | LEFT: each needs a new fixture design (about 30 lines each) beyond this budget; leave for the release-point sweep |
| W2B1 3 (plan wording), 4, 5; W2E, W2L, W2PI, W2PS, W2SB, W2SC, W2T Studio rows | docs, Studio tests, other modules | LEFT: controller's file, Studio-owned (R2.SK/R2.6S) or no change proposed |
| Heading grammar third copy (R4); T9 hand-written `['.h2']`; T13 `OWNED` selector in `test_r2_react` | bridge, other modules | LEFT: a bridge refactor and other owners' modules, not this slice |

## TDD

- RED (genuine, run at BASE with the bridge unchanged): 1a and 1c. Record the failing output.
- GREEN characterization, never manufactured RED: 1b, 1d (it passes at BASE because no listener exists; its value is the
  mutant), 2a, 2b, 3a, 4, and the `['BODY']` test. Say which ran green at BASE.
- One realistic mutant per new test, shown failing, with the source restored byte-exact (SHA-256 before and after):
  1a handler removed; 1b `bumpRolePage()` in the handler; 1c `roleNative` bump removed, and `pageshow` only (the
  `pagehide`-only subtest); 1d `addEventListener` instead of `this.listen`; 2a observer `subtree: false` (missing second
  notice); 2b two mutants: drop `attributes` (kills the href swap) and drop `characterData`+`childList` keeping
  `attributes` (kills the text replace; removing all three makes the constructor throw, so it is not a mutant); 3a: M3a
  or M3b as the sweep finds them (M1, M2b, M5 are expected equivalent, see requirement 5); 4: `debug: 1` added to
  `roleState()`, to the detected reply top level, to a group, to a loss (`postRoleReceipt`) and to the page notice
  (`sendRolePage`), plus one removed field; `['BODY']` the lowercase `soleBody`.
- Per Test Quality Rules: Given/When/Then docstrings whose Then is what the test asserts; real Studio-origin host and the
  real bridge; conditions instead of fixed sleeps (the 250 to 600 ms waits that prove nothing was sent are the allowed
  exception); no new skips (the `InstallCountTests` fix reports Firefox as a skipped subtest); scratch scripts and logs
  carry `6b2` in their names; mutants run in the foreground.

## Focused command (run from `C:/fks/t6b2`)

- A: `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_role_route_bridge test_role_protocol test_support -v`
- B: `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_role_adapters.PlacementTests test_role_stylesheet.InstallCountTests test_role_stylesheet.BaselineDetectTests test_role_detection test_role_preview test_r2_route_fixtures -v`
- C (watch list, once): `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_bridge_runtime.HandshakeTests -v`
- No npm fixture is needed. The full suite is not run (settled wave). Also `node --check fontkit-bridge.js`,
  `python -m ruff check . --exclude .agents`, and `git add -N` the new classes' file changes before `git diff --check`.

## Handoff

Commit subject: `feat(bridge): treat back/forward cache restores as route events`

The landing records, in product terms: a page restored from the back/forward cache is re-checked against its URL, styles
and viewport; a Detect that straddles the freeze replies incomplete; no version moves unless the page did (Route
observation); the bridge sends exactly the revision-1 fields of Detect, Apply, the ready snapshot and the page notice.
Plan boxes: the last three R2.6B checkboxes (baseline selector evidence, route test list, guard mutants). README (release
point): the 6B1 known limit stays; add that CSSOM `insertRule` without a DOM change and a page frozen without a
`pageshow` event are seen only by the next Detect. Report: the mutant table (killed by which test, survivors, equivalents
with the reasoning), the Minors table with verdicts as above, any live key-set mismatch, and the statement that real
BFCache does not occur under Playwright Chromium, so the dispatched `pageshow`/`pagehide` events stand in for it and the
tests prove the handler wiring only.

## Open questions

1. **What `pageshow`/`pagehide` should do.** The plan only says "track pageshow/pagehide" and "a route event invalidates
   evidence". Options: (A, recommended) internal epoch plus a refresh, as specified in requirement 1: an in-flight Detect
   ends `page-changed`, the version moves only if the URL, styles or viewport really did; (B) bump the wire version on
   every `pageshow` with `persisted: true`: simpler, but it breaks D063/D066 ("the wire pageVersion advances only for
   URL, author DOM/text/attribute, author stylesheet and viewport changes") and announces a version with no change.
2. **Where the key-set oracle lives.** `tests/role_contract.py` has no key sets and belongs to R2.SK, but the carry-over
   says "against tests/role_contract.py". Recommend literals in `RevisionOneKeysTests` written from the plan's type block
   (no table edit); a later task may move them into the table with the rows `with_unknown_keys` already uses.
3. **"Complete/incomplete counts for matches and variants".** The plan names no field. The existing wire already carries
   them: `SelectorCheck.matchCount` equals the sum of its signatures' counts (`table.violations` checks it), and the reply's
   `complete`/`reason` mark every check of an incomplete scan as unusable (Studio never marks a route checked from one).
   Recommend characterization only (requirements 3 and 4 assert both on incomplete replies); adding a count field would
   break "the bridge sends exactly the revision-1 fields" (Addendum 26 item 3).

## Controller rulings on the open questions (2026-10-18)

1. As recommended: `pageshow` and `pagehide` bump the internal epoch and schedule a refresh, so an in-flight Detect
   ends `page-changed` and the wire version moves only when the URL, author DOM, author styles or viewport really
   changed (D063/D066). A persisted `pageshow` never bumps the wire version by itself.
2. As recommended: the exact revision-1 key sets are literals in `RevisionOneKeysTests`, copied from the plan's type
   block and "Messages" table (the independent oracle); `tests/role_contract.py` is not edited (R2.6S owns one line
   there).
3. As recommended: characterize only; no new field (Addendum 26: the bridge sends exactly the revision-1 fields).

## Revision 1 (2026-10-18)

Each finding of `task-6b2-brief-review.md`, with the brief place that resolves it (search the quoted text; line numbers
move). The review's proposed fixes were taken as written, except Minor 1's extra detail (see note).

- Important 1: requirement 1d now observes `add`/`removeEventListener` registrations through a spy prefixed to the
  in-memory bridge source, with a page-owned control listener; requirement 1c gains the `pagehide`-only subtest; the
  requirement 5 M7 line and the TDD mutant list name those killers.
- Important 2: requirement 3b is dropped with a citation of `test_role_detection.py:372-410`; requirement 5 declares M1,
  M2b and M5 expected equivalent with the review's reasoning and makes M2's killer the implementer's to name; the TDD
  line no longer claims "3a/3b M1 and M2".
- Minor 1 (`violations` kinds): requirement 4 lists 'detected', 'roles-applied', 'role-state'; the page notice gets the
  key-set check only; `role_contract.py` is not edited (R2.6S owns its `TOLERANT_KINDS` line).
- Minor 2 (vacuous nested keys, missing mutants): requirement 4 requires non-empty nested lists; TDD adds group, loss,
  receipt and page-notice mutants.
- Minor 3 (skip wording): Minors table row "W2P 4 / W2B1 1" and the TDD "no new skips".
- Minor 4 (2b realism): requirement 2 intro and 2b ("href swap" naming, condition wait, "greater than" only, link added
  before hello, test_r2_react.py coverage cited).
- Minor 5 (mutant wording): TDD mutant list gives two 2b mutants and the 2a missing-notice kill.
- Minor 6 (3c rationale): requirement 3c reworded; M3a needs a stamp-only change.
- Minor 7 (numbering, 2a sleep): Owned files names table rows; requirement 2a drops the sleep.
- Minor 8 (BFCache): requirement 1 intro and the Handoff report line.
- Line budget: 380 reduced to 375 (header).

## Revision 2 (2026-10-18; scoped re-review findings folded by the controller, `task-6b2-brief-rereview.md`)

- Important: requirement 1d is a genuine RED at BASE (BASE registers no pageshow/pagehide listener, so "one
  registration each after hello" fails). Move it to the RED list; ignore the "GREEN ... passes at BASE" parenthetical.
- Budget: 375 gross lines (about 25 bridge, 325 tests, 25 comment and test-edit fixes); ignore "net about -5".
- 1d tells the bridge's registrations from the page's control listener by handler identity: the control handler is
  created by the test page before the bridge loads and recorded by reference; every other recorded pageshow/pagehide
  registration belongs to the bridge.
- The re-review reports the "199 roles" case as one short of the exact bound (200): check the bound at BASE (source
  and plan), use the exact boundary value, and cite where it comes from in the report.
- Line 266's "(see note)" has no note: it refers to the BFCache finding recorded in requirement 1.
