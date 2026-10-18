# R2.6B1 brief: the bridge announces route and content changes with design:roles-page

Plan: `docs/plans/2026-10-03-r2-engine.md` task R2.6B part 1 (first two checkboxes), "Messages" (the `design:roles-page` row),
"Route observation", Addenda 5, 11, 14, 25 (slice R2.6B1, wave W1) and 26 (the bridge sends exactly the revision-1 fields);
D061, D063, D066. BASE `bd20e43b912bee1431fc74d3334c8a6bd4ac55e7` (line numbers below are at BASE), worktree `C:/fks/t6b1`,
task id `6b1`.
Line budget: about 170 gross lines in `fontkit-bridge.js`, about 650 in the new test module (about 25 tests with Given/When/Then
docstrings plus the poll helper). Explain any excess.

## Why

Nothing in the bridge watches the URL. A single-page app that calls `history.pushState` leaves the bridge's `roleURL`
stale until the next Detect, Apply or Clear happens to call `refreshRolePage` (`fontkit-bridge.js` 1290-1296), so Studio
cannot tell that the route it checked is no longer the one on screen. `grep` shows no `pushState`, `popstate` or
`hashchange` use anywhere in the bridge. The plan's "Data-only invalidation" message `design:roles-page` does not exist
yet. Two bump sites exist and say nothing to Studio: `noteRoleMutations` (1252-1257, author DOM) and `refreshRolePage`
(URL, author stylesheet, viewport stamp). R2.6S (Studio, a later slice) consumes the message; this slice only sends it.

Studio today ignores it safely: `acceptBridgeMessage` (`fontkit-studio.html` 4489-4497) returns null for any type outside
`BRIDGE_TYPES` (3396-3397), which lacks `design:roles-page`, so the message is dropped with no status, error or state
change. The bridge may therefore send it before R2.6S lands.

## Owned files (exact)

- `fontkit-bridge.js`, only these places:
  - the module constants block (new `ROLE_PAGE_GAP_MS = 250`, beside `MAX_ROLE_CSS_BYTES` at 180);
  - inside `FontKitBridge`: `constructor` field initialisers near 660-675 (new fields only), `dispose` (812-827),
    `noteRoleMutations` (1252-1257) and `refreshRolePage` (1290-1296) (each replaces `this.pageVersion += 1` with the new
    helper call), `observeRolePage` (1259-1282: history wrappers, `popstate`, `hashchange`, `resize` listeners),
    `handleHello` (only the line after the `design:ready` post, 1207-1216, recording `announcedVersion`);
  - new methods beside `refreshRolePage`: `bumpRolePage`, `scheduleRolePage`, `sendRolePage`, `expireRolePageHold`,
    `installRoleHistory`, `removeRoleHistory`.
  Nothing else. `dropSession` and `cancelRoleJobs` stay untouched.
- New `tests/test_role_route_bridge.py`. No new fixture: the tests use existing pages (`ROLE_PAGE` =
  `tests/fixtures/bridge/target-role-protocol.html`, `fixtures/multi-page/article.html` and `spa.html`).

Read-only: `tests/role_support.py`, `tests/role_contract.py`, `tests/fixtures/**`, `fixtures/multi-page/*` (owned by F3),
`fontkit-studio.html` and every other test. If an existing test fails because a `design:roles-page` appears, report the
failing assertion; do not edit it. The ruling-5 review found none expected (see Focused commands).

## Read first

`constraints.md`; the plan texts above; at BASE `fontkit-bridge.js` 782-786 (`listen`), 1074 (`dropSession`), 1107-1117
(`post`), 1181-1230 (hello, ready; `roleState()` at 1230 carries the ready `pageVersion`), 1245-1296 (cancel, mutations,
observer, refresh), 1356 (`isOwnedRoleMutation`), 1439 (Detect calls `cancelRoleJobs`), 1523-1544 (`measureRoleReceipt`, the
rAF-plus-250 ms `fired` pattern), 1893-1990 (`detectTextStyles`; its `fresh()` calls `refreshRolePage`), 4070 (second flush
site). Tests: `tests/role_support.py` (`RoleBridgeCase.open` injects the bridge into any `TARGET + '/...'` document, blocks
HTTPS, checks the canary), `tests/test_role_detection.py` 412-460, `tests/test_role_protocol.py` 106-110 (2,000-character
URL), `tests/test_bridge_runtime.py` 203-216 (evil sibling frame), `tests/test_r2_integration.py` 120 (pushState inside the
`design:detect` listener), `fixtures/multi-page/spa.js` (classic script: `render(view)` is a global; `render('same')` swaps
`#route-content`; buttons `#push-detail`, `#replace-note`, `#back`, `#forward`, `#replace-same`, `#hash-section`),
`tests/test_r2_route_fixtures.py` for fixture oracles.

## Contract decisions (settled by the plan and the controller rulings below)

- **One rule.** After an authenticated hello, the bridge sends `design:roles-page` whenever the wire `pageVersion`
  advances, whatever the cause: URL, author DOM/text/attribute, author stylesheet node, `media`/`disabled`-attribute change,
  viewport (D063, D066). No cause-specific branch. Bridge writes, native hover/focus/press and font loading move only the
  internal epoch and send nothing (D063, D066, D067). Not announced, by design: CSSOM `insertRule` or `sheet.disabled`
  with no DOM record and no resize; Detect (explicit) sees them through `refreshRolePage` (plan "Route observation").
- **One bump helper.** `bumpRolePage()` does `this.pageVersion += 1; this.scheduleRolePage();` and replaces the increment
  at both sites (`noteRoleMutations`, `refreshRolePage`). `refreshRolePage` calls from Detect, Apply and Clear therefore also
  schedule (a send whose version differs from `announcedVersion` still posts; Studio may see a `roles-page` equal to the
  version in a Detect reply; this is harmless data and not special-cased).
- **When it starts.** The bridge is inert until a valid hello (anti-pattern 7). History wrappers and the `popstate`,
  `hashchange` and `resize` listeners are installed once, in `observeRolePage` (first hello), beside the observer. A second
  hello does not install again. `scheduleRolePage` does nothing unless `this.studioSource` is pinned and `!this.disposed`
  (listeners persist after `dropSession`). `resize` and the route listeners only call `scheduleRolePage()`; a
  `refreshRolePage()` (the send's, or the hold expiry's) is what notices the new URL or stamp and bumps.
- **Message.** Exactly `{type:'design:roles-page', protocolVersion:1, sessionId, documentId, pageVersion, pageURL}`; no
  other field (Addendum 26). Send with `this.post`. `pageURL` is `this.rolePageURL()` (`null` for an unsupported URL, such
  as over 2,000 characters; D061, Addendum 5). `pageVersion` is read after the refresh, at send time.
- **Dedupe.** Field `announcedVersion`: set to `this.pageVersion` right after the `design:ready` post (the version
  `roleState()` stated), and again at each send. A send posts only if the refreshed `pageVersion` differs. (A route that
  returns to the same URL with no DOM change inside one window still bumps and so still sends: the version moved. Do not
  claim otherwise.)
- **Invariant (the one thing the schedule must guarantee).** Every wire `pageVersion` advance after hello is announced at
  most 250 ms (the hold) plus one frame (the render wait; 250 ms more on a page that never paints) later, carrying the
  latest identity at send time. No send's own refresh may hide a pending change, and no change may wait on a bump that only
  a later send would make.
- **Schedule.** State: `rolePageRec` (null or `{epoch, raf, timers}`), `rolePageHold` (null or a timer id),
  `announcedVersion`. Timers only, never `performance.now` or `Date` (a role-preview test skews `performance.now`,
  `test_role_preview.py` 320-326).
  - `scheduleRolePage()`: return unless pinned and not disposed. If `rolePageRec` carries an older `roleEpoch` (a hello
    arrived), cancel it and clear it (no edit to `dropSession`). If a record of the current epoch exists, or `rolePageHold`
    is set, return (a held change is picked up by the expiry below). Otherwise create the record: one
    `requestAnimationFrame`, then one `setTimeout(0)`, with a 250 ms `setTimeout` fallback for pages that never paint (copy
    the `fired` guard of `measureRoleReceipt`, 1541).
  - `sendRolePage()` (the record's callback): re-check `disposed`, the pinned session and the captured `roleEpoch`. Keep
    `rolePageRec` set while it runs and clear it in a `finally`; the held record makes its own `refreshRolePage` bump a
    no-op for `scheduleRolePage` (without it a stray record could fire inside the hold and post early). Call
    `refreshRolePage()` first, then post iff `pageVersion !== announcedVersion`; on a post set `announcedVersion =
    pageVersion` and start the hold `setTimeout(expireRolePageHold, ROLE_PAGE_GAP_MS)`.
  - `expireRolePageHold()`: clear `rolePageHold`; return unless pinned and not disposed; call `refreshRolePage()` (this
    notices a URL-only or viewport change made during the hold and bumps, which schedules a record); then, if `pageVersion
    !== announcedVersion` and no record exists, call `scheduleRolePage()`. This trailing edge is what makes the invariant
    hold for changes made inside the 250 ms window.
  - So any burst yields one message carrying the latest state, and a steady stream at most one per 250 ms. `dispose`
    clears the record and the hold. Do not hook this into `cancelRoleJobs` (Detect calls it, 1439).
- **In-flight Detect.** Unchanged and not cancelled by the message. A URL change makes the job's `fresh()` fail, so the
  reply stays `complete:false`, `reason:'page-changed'`, with the captured `pageURL`/`pageVersion` and the new
  `currentPageURL`/`currentPageVersion` (Addendum 5). Studio may receive `roles-page` before or after that stale reply; the
  brief fixes neither order. The stale reply alone settles the old request.
- **Wrappers.** Own properties of the `history` object, defined with `Object.defineProperty(history, name, {value,
  configurable:true, writable:true, enumerable:true})`; not on `History.prototype`. Measured in Chromium: the native
  operations are enumerable on the prototype, so an own `enumerable:false` property would remove `pushState` and
  `replaceState` from `for (k in history)`; `enumerable:true` keeps both names (their order moves first and `Object.keys(history)`
  gains them, which cannot be avoided and is not claimed). `Object.getOwnPropertyNames(history)` gains the two names too.
  Each wrapper is `function (...args) { const out = Reflect.apply(original, this, args); <schedule inside try/catch so a
  bridge fault never alters the app's result>; return out; }`. A native throw (SecurityError, DataCloneError, TypeError for a
  bad receiver) propagates untouched and schedules nothing. `original` is whatever `history[name]` was at install (a
  router's earlier wrapper included). The whole install is inside try/catch (a non-writable property or a frozen `history`
  must not throw out of `handleHello`, which runs `observeRolePage` before `design:ready`). After `dispose` a still-installed
  wrapper forwards and schedules nothing.
- **Removal.** On `dispose`, per method: if `history[name] === ownWrapper`, restore (delete the own property when none
  existed at install, else `Object.defineProperty` with the descriptor saved at install, so its attributes return too);
  otherwise leave the app's later wrapper in place. The three
  listeners go through `this.listen`, so the existing `dispose` removes them.
- **Known limit, no polling.** Code that cached the native `history.pushState` before the first hello bypasses the wrapper.
  Its change is caught lazily by the next Detect, Apply or Clear (their `refreshRolePage`); `popstate`, `hashchange` and
  mutations cover back, forward, fragment navigation and rendered content. State this in a comment above the install and in the
  report's Handoff for the release-point README. No poll, Navigation API hook or router import (plan: "No polling loop or app
  router dependency").

## Requirements

Page choice (C1 of the review): the fixture `spa.html` renders on every history call, so its DOM observer alone would send
and hide a missing wrapper or listener. URL-only changes are therefore driven with `frame.evaluate` on `ROLE_PAGE` or
`article.html`, which write no DOM. `spa.html` is used only for the click-driven SPA case and the rendered-text cross-check.

1. URL-only routes announce. On `ROLE_PAGE`: `frame.evaluate` of `history.pushState({a:1},'','?route=x')`,
   `history.replaceState(null,'','?route=y')`, `location.hash = '#z'` (hashchange) and `history.back()` (popstate) each yield
   one `roles-page` whose `pageURL` is the literal expected URL and whose DOM (`.body-copy` text) is unchanged. Oracle: plan
   "Route observation", the "Messages" row. Measured: `location.hash=` and `history.back()` fire both `popstate` and
   `hashchange`, so these real calls cannot isolate either listener. Isolate them (1b): call the cached native
   `History.prototype.pushState.call(history, null, '', '?route=n')` (the URL changes with no wrapper call), then
   `dispatchEvent(new PopStateEvent('popstate'))`, expect one `roles-page` for `?route=n`; repeat with a native push to
   `#h` and `dispatchEvent(new HashChangeEvent('hashchange'))`.
   Hold window (1c, the invariant): push A, wait for its message, then about 50 ms later (inside the 250 ms hold) push B
   with no DOM change; B's message with B's `pageURL` and a greater `pageVersion` arrives within the next 600 ms, and no
   third message follows. Repeat with a `resize` of `#target` in place of the second push, and with a hash change. Run
   the route kinds of this requirement in order as one fast sequence (changes about 50 ms apart) and assert that the last
   message carries the final URL and the `pageVersion` of a Detect sent after quiescence.
2. Content-only change announces: no history call; `frame.evaluate` sets `.body-copy` `textContent` (or, on `spa.html`,
   calls the global `render('same')`). One `roles-page`, same `pageURL`, greater `pageVersion`.
3. Style and viewport causes announce (rulings 1 and 4): (a) append a `<style>` element to the page's head; (b) change a
   `media` attribute on an author stylesheet link or style; (c) resize the host's `#target` iframe width through
   `page.evaluate` so the `resize` event fires. Each yields one `roles-page`, unchanged `pageURL`, greater `pageVersion`.
   CSSOM `insertRule` with no other change sends nothing within 600 ms (the stated limit; a short absence check). (d) After
   that silent `insertRule`, a Detect notices it through `refreshRolePage`: a `roles-page` follows whose `pageVersion`
   equals the Detect reply's (the bump helper at the `refreshRolePage` site).
4. The message has exactly the six keys, `protocolVersion` 1, the current `sessionId`; its `pageVersion` is greater than the
   last `design:ready.roleState.pageVersion` or `roles-page` for the same document, and equals the `pageVersion` of a Detect
   sent after quiescence (the independent link). Run this on a page where the previous version is known from the ready.
5. `pageURL` null: `history.replaceState(null,'','/?'+'x'*1999)` (as `test_role_protocol.py` 106-110) sends one message with
   `pageURL: null`, a greater `pageVersion`; replacing back to a supported URL about 50 ms later (inside the hold) sends the
   URL within 600 ms. (D061, Addendum 5.)
6. Bridge-originated changes send nothing (600 ms absence check, each preceded by a proof that the page can send, one
   Requirement 1 push): a Detect with an applied preview, Apply, Clear, native focus and hover on an element, a `design:update`
   edit and the transition ban. Also, with an applied preview, a history push sends the message while the owned sheet
   text, `revision`, a following Detect's `roleState` and the computed size stay unchanged ("does not mutate roles").
7. Burst and rate. 100 `replaceState` calls plus three `pushState` calls A, B, C in one task yield exactly one message with
   C's `pageURL`; A's and B's never appear (keep 100 + 3 per page: Chromium ignores history calls over about 200 in 10 s).
   A stream of text edits every 5 ms for about 1,000 ms: measure the stream with `performance.now()` in the page, then
   assert `1 <= count <= floor(elapsed/250) + 2` and, after quiescence, that the last message's version equals a Detect's.
8. The send never runs inside the history call: a marker the page posts from a `requestAnimationFrame` callback registered
   after the history call (or the rAF-in-wrapper mutant passes) arrives before the `roles-page`; with
   `requestAnimationFrame` replaced by a no-op, the message still arrives (250 ms fallback) within 1,500 ms.
9. Wrapper semantics: receiver, arguments (the state object reaches an earlier app wrapper as the same reference with equal
   title and URL), return value `undefined`, `history.state` after a successful call equals the state passed; a cross-origin
   URL throws the page's own `SecurityError`, an uncloneable state `DataCloneError`, a non-History receiver `TypeError`; each
   leaves the URL unchanged and sends nothing. Each test first asserts one successful call produces a `roles-page` (so it
   fails when no wrapper exists).
10. Inert and removal. Before hello: `history.pushState === History.prototype.pushState`, no own `pushState`, and a push
    sends nothing. After the first hello the function identity of `history.pushState` and `replaceState` differs from the
    prototype's and is the same after a second hello (no stacking). A hello from the evil origin (sibling-frame pattern,
    `test_bridge_runtime.py` 205-215) leaves `history.pushState === History.prototype.pushState`, and a push sends the evil
    window nothing. The sorted set of names from `for (k in history)` is unchanged by install (order and `Object.keys` are
    not asserted; see "Wrappers"). An app-owned own `pushState` (configurable, writable, `enumerable:false`) defined before the
    hello has the same descriptor attributes after `dispose`. A frozen/non-writable `history.pushState` set before the
    hello does not stop `design:ready`. After `__fontkitBridge.dispose()` the native function is back; when the app wrapped
    after the hello, dispose leaves that wrapper in place, it forwards to the previous wrapper with the right return value, and
    no message is sent afterwards.
11. Session discard (anchor first: a push under s1 produces a `roles-page`, RED at BASE). Then, in one task inside the frame,
    `history.pushState(...)` followed by `window.dispatchEvent(new MessageEvent('message', {data: hello_s2, origin: STUDIO,
    source: parent}))` (a real `postMessage` cannot land in the same task). Read the raw `log` (the host's `messages()`
    filters to the current session): no `roles-page` under s1 afterwards, none for the push under s2 (the s2 ready already
    carried the version, which `handleHello` records as `announcedVersion`). Lost-update case: push, the synthetic hello, then a DOM change: exactly one message under s2 (older-epoch
    record replaced).
12. In-flight Detect (characterization; the existing `action == 'url'` subtest at `test_role_detection.py` 412-460 already
    covers the stale reply, so what is new here is the accompanying notice). Call `history.pushState` synchronously inside
    the page's `design:detect` message listener (as `test_r2_integration.py` 120 does, since on `spa.html` a Detect
    finishes inside its first slice and a `setTimeout(0)` push arrives too late). Reply: `complete:false`,
    `reason:'page-changed'`, captured `pageURL` unchanged, `currentPageURL` the new URL; a `roles-page` for the new URL
    arrives; a fresh Detect on the new route is complete with its `pageURL` equal to the old reply's `currentPageURL`.
    12b (mid-scan, kills the `cancelRoleJobs` mutant): on `fixtures/large-page/index.html` (a multi-slice scan,
    `test_role_detection.py` 523 with `design:mode` interact) start a Detect, assert no `design:detected` yet, then
    `frame.evaluate` a `history.pushState` while the scan is pending. The stale reply still arrives (`complete:false`,
    `reason:'page-changed'`) and a `roles-page` for the new URL arrives. If the scan finishes before the message, report it
    instead of loosening the check.
13. Rendered-text cross-check on `spa.html`. After hello, send `design:mode` `{mode: 'interact'}` and wait until
    `frame.wait_for_function("() => window.__fontkitBridge && window.__fontkitBridge.mode === 'interact'")`: in the default
    `select` mode `handleDocumentClick` (`fontkit-bridge.js` 3886-3894) `preventDefault`s and `stopPropagation`s a click on
    a discovered `button`/`header a`/`nav a` (`SEMANTIC_SELECTORS` 114-120; `handleMode` 3896-3910), so the fixture would never
    run. Then after each of `#push-detail`, `#replace-note`, `#hash-section` clicks the
    frame's `#route-content` `h1` text equals the fixture literal (`SPA detail evidence`, `SPA NOTE EVIDENCE`,
    `section evidence`) and one `roles-page` per click arrives with the URL literal (`spa.html?route=detail`, `?route=note`,
    `#section`).

## TDD

RED at BASE (a genuine failing behaviour assertion): requirements 1 (with 1b, 1c), 2, 3 (with 3d), 4, 5, 7, 8, 11 (anchor part), 13. Use a short
local poll helper that returns the list of `design:roles-page` messages after a timeout, then `assertEqual` on the list or
its length, so the failure reads "[] != [ ... ]" rather than the host's 6,000 ms `waitFor` rejection. Requirements 9 and 10
assert a successful `roles-page` first and are RED for that reason; their exception checks are then characterization. 6 is
a GREEN characterization at BASE (no message exists); keep waits at 600 ms, the exception the Test Quality Rules allow for
proving that nothing happened. 12 and 12b are GREEN except the new `roles-page` assertion. Report which are which.

One realistic mutant per test, shown failing, source restored byte-exact (SHA-256 before and after). Scratch scripts and
logs carry `6b1` in their names.

| Test (requirement) | Mutant (each killed by the named test) |
|---|---|
| route kinds (1) | remove the wrappers (the page has no DOM writes) |
| popstate and hashchange isolation (1b) | drop the `popstate` listener; separately drop the `hashchange` listener |
| hold window (1c) | `expireRolePageHold` compares versions without calling `refreshRolePage`; or `scheduleRolePage` during the hold creates a record anyway (then B is sent early: the rate test in 7 also fails) |
| content-only (2) | `noteRoleMutations` calls `pageVersion += 1` instead of `bumpRolePage()` |
| style and viewport (3) | drop the `resize` listener (3c); `refreshRolePage` bumps without the helper (3d, the Detect-noticed case) |
| ready link (4) | send the `pageVersion` read before the refresh |
| null URL (5) | send `location.href` instead of `rolePageURL()` |
| bridge writes quiet (6) | `isOwnedRoleMutation` returns false |
| coalescing and rate (7) | send per event; or remove the hold timer |
| after rendering (8) | send synchronously in the wrapper; or drop the 250 ms fallback |
| wrapper semantics (9) | swallow the exception, return `true`, or call with `history` instead of `this` |
| inert and removal (10) | install at construction; install a second time on every hello; dispose restores unconditionally; dispose restores by assignment (descriptor test); no try/catch around the install (frozen-property test) |
| session discard (11) | do not record `announcedVersion` after the ready post (the s2 push case then posts); or let an older-epoch record block a new one (lost-update case). Dropped as equivalent: omit the `roleEpoch` re-check (`post()` stamps the current session and the hello's refresh already equals `announcedVersion`) and "no roles-page under s1" (vacuous) |
| interrupted Detect (12b) | the send path calls `cancelRoleJobs` (the stale reply never arrives). Not killable on `spa.html`: the stale reply posts first |
| rendered text (13) | none: the text check guards the test's own premise (the click ran in `interact` mode), not a bridge break |

## Focused commands

Run from `C:/fks/t6b1`, each under about 5 minutes (the foreground cap is 10). `node --check fontkit-bridge.js` and
`python -m ruff check . --exclude .agents` run once as well. No npm fixture is needed for A, B, D (`fixtures/multi-page`
is plain HTML).

```
A: PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_role_route_bridge test_r2_route_fixtures test_role_protocol test_role_preview test_support -v
B: PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_role_detection test_role_stylesheet -v
C: npm ci --prefix fixtures/vite-react-css-modules, then FKS_REQUIRE_FIXTURES=1 PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_r2_integration test_r2_react -v
D: PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_bridge_runtime -v
```

The new module must pass `test_support`'s raw-markup scan (no `outerHTML` or `page.content()` on the host page).

Ruling-5 watch list (13 tests, none expected to break: every post-hello check filters by type): `test_role_detection.py`
19, 33, 412-460, 399-408; `test_role_protocol.py` 106, 110; `test_role_stylesheet.py` 645, 732-736, 858, 1004;
`test_role_preview.py` 305-335; `test_r2_integration.py` 120, 665; `test_r2_react.py` 649-695 (the send runs from its 250 ms
fallback inside the "commit < hmr < deadline" window; fixture-gated); the inert-before-hello guards `test_bridge_runtime.py`
196-197, 265-266 and `test_role_protocol.py` 156; the hostile guard `test_bridge_runtime.py` 213-215. **If any watch test
fails, the implementer reports the failing assertion and the message that caused it. It never edits, relaxes or skips the
test**; the controller assigns the fix.

## Handoff (for the landing)

Commit subject: `feat(bridge): announce route and content changes to Studio` (58 characters). Draft a why-body (wrap at
72): Studio could not know a single-page app had moved to another route or re-rendered, so evidence checked on one page could
be shown for another; the bridge now sends one data-only notice after the page renders, never from its own writes, and
leaves the app's history calls unchanged. Also a ledger event in product terms (no process state), the known cached-native
limit for the README, and which R2.6B boxes this closes (first two) and what stays for R2.6B2 (baseline selector checks per
known role, BFCache, delayed render, CSS HMR, the W2 review Minors).

## Open questions

1. **Watch-test breakage.** If a watch test fails, who fixes it? Recommend the controller assigns it to B2 ("extra tests in
   bridge test modules", Addendum 25) or the landing, as the ruling-5 review expects none. This stays the controller's call.

## Controller rulings on the open questions (2026-10-18)

1 and 4. One rule: after an authenticated hello, the bridge sends `design:roles-page` whenever the wire `pageVersion`
   advances, whatever the cause (URL, author DOM/text/attribute, author stylesheet, viewport; D063/D066), coalesced by
   the one timer below, and never for bridge-owned writes (they move only the internal epoch). No cause-specific
   branch. R2.6B2 adds the BFCache, delayed-render and CSS HMR tests on top of this rule.
2. Bound: one pending timer; a send waits one `requestAnimationFrame` then `setTimeout(0)` (250 ms fallback), and at
   most one send per 250 ms, trailing, carrying the current identity at send time.
3. Wrappers are own properties on the `history` instance; restore only while the property is still the bridge's own
   wrapper. Code that cached the native method before hello is a known limit (caught by the next Detect, Apply or
   Clear); state it in a comment and in the report's Handoff for the release-point README.
5. The brief review lists, now, every existing test at BASE whose exact message log or message count after hello
   could gain a `roles-page` (page mutations or navigation after hello). The controller assigns those before dispatch.

## Revision 1 (2026-10-18)

Resolves `task-6b1-brief-review.md`. Facts re-checked at BASE: no `resize` listener for roles exists (798 is `scheduleBounds`);
`roleState()` carries the ready version (1230); `ROLE_PAGE` has no router DOM writes, so no new fixture is needed.

- C1: Requirements page-choice paragraph, 1, 2, 13; mutants rows "route kinds", "content-only".
- C2: "One rule", "One bump helper", "When it starts" (resize), Requirement 3, mutant row "style and viewport"; Open
  questions 1 and 4 removed.
- I1: Requirement 11 (anchor, synthetic hello, raw `log`, lost-update); "Coalescing" (older-epoch replace, no `cancelRoleJobs`).
- I2: Requirement 12 (synchronous push in the listener, new content named); mutant row "interrupted Detect".
- I3: mutant row "bridge writes quiet" (`isOwnedRoleMutation` returns false).
- I4: Requirement 10 (identity, evil origin, enumerability, frozen property); "Wrappers" (defineProperty, try/catch).
- I5: Requirements 5 (null URL), 6 (does not mutate roles), 9 (`history.state`).
- I6: Requirement 7 (`performance.now` bound, quiescence, 100 + 3 limit).
- I7: Owned files (constants block, `bumpRolePage` and the other new methods listed).
- I8: Focused commands A-D; raw-markup scan sentence.
- M1: mutant row "ready link"; M2: Requirement 8; M3: "Coalescing" (timers only); M4: "When it starts" and "Coalescing"
  (pinned and not disposed; rAF plus two timers); M5: Dedupe (claim removed, opposite stated); M6: TDD (poll helper);
  M7: line budget 150 and 450.
- Ruling 5: Focused commands (watch list in A-D, report-never-edit sentence).

## Controller ruling on the remaining open question (2026-10-18)

A watch test that fails is reported in the code report with its output, never edited; the controller assigns the fix.

## Revision 2 (2026-10-18)

Resolves `task-6b1-brief-rereview.md`. The controller rulings above are unchanged. Probes by the reviewer (`6b1_pop.py`,
`6b1_forin.py`) were used as measured; no new probe disagreed.

- I1 (lost update in the hold window): "Invariant", "Schedule" (hold expiry refreshes, then compares with `announcedVersion`;
  the record stays set during a send); Requirement 1c, 5 (replace back inside the hold); mutant row "hold window (1c)".
- I2 (`for-in` claim): "Wrappers" (`enumerable:true`, measured), "Removal" (descriptor restore), Requirement 10 (sorted name
  set, descriptor test). `Object.keys` and ordering are not asserted; the lead's `getOwnPropertyNames` idea is unachievable
  (it gains the two names) and is stated as such.
- I3 (dead mutants): Requirement 1b and mutant rows "popstate and hashchange isolation", "session discard" (two rows
  dropped with reasons), "interrupted Detect" via Requirement 12b, "style and viewport" via Requirement 3d.
- I4 (mode switch): Requirement 13 (interact mode, wait on `__fontkitBridge.mode`, cites 3886-3894, 3896-3910, 114-120).
  The only click-driven test is Requirement 13.
- M1: `rolePageSending` dropped; the held record with `finally` replaces it, and the reason is stated ("Schedule").
- M2: Requirement 6 points at a Requirement 1 push. M3: commit subject is 58 characters. M4: mutant row "inert and
  removal" adds the missing try/catch mutant. M5: line budget 170 and 650.
- Line budget: bridge about 170 gross (schedule and hold expiry added about 20), tests about 650.

## Revision 3 (2026-10-18; sdd-reviewer re-review 2 findings folded by the controller, `task-6b1-brief-rereview2.md`)

- I1 (replaces the "Dedupe" sentence about returning to the same URL): wrappers and route listeners only schedule;
  `pageVersion` moves only in `refreshRolePage`. A -> B -> A inside one hold window with no other change advances no
  version and sends nothing, which is correct: the identity equals the last one announced. Add one test asserting
  exactly that (no `roles-page`, and a following Detect reports the unchanged version), with the mutant "a route event
  bumps the version directly".
- I2: a hold-expiry refresh reads the style stamp, so a silent CSSOM `insertRule` made within 250 ms after a post may
  be announced. The contract only requires Detect to notice it and forbids claiming it is tracked: the "One rule"
  text gains that caveat, and Requirement 3's 600 ms absence check and 3d run on a fresh page with no earlier post.
- M1: Requirement 6 is "RED at BASE on its push-proof step, then characterization".
- M2: add a mutant row "remove the wrappers" for Requirement 12, and name the first Requirement 6 subtest as the one
  that carries the `isOwnedRoleMutation` mutant; correct the 1c/7 attribution.
- M3: Requirement 10 also asserts `Object.getOwnPropertyNames(history)` is unchanged after dispose; the frozen case
  uses `Object.freeze(history)` (configurable:false), so the no-try/catch mutant fails.
- M4: Requirement 11's lost-update case runs push, synthetic hello and DOM change in one task.
- M5: one try/catch per method, saving the original descriptor before each define, so a half install is restored by
  dispose; "Coalescing" references read "Schedule".
- M6: take the cut: fold Requirement 4's exact-keys and Detect-link assertions into Requirement 2's test, and keep
  Requirement 12's fresh-Detect assertion inside 12b.
- Wrapper enumerability stays `enumerable:true` on the `history` instance (ruling 3; the reviewer's recommendation);
  dispose restores by delete or saved descriptor so `history` returns to its native state exactly.
