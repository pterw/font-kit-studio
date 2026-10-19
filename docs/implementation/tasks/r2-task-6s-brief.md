# R2.6S brief: Studio's visited-page role inventory

Plan: `docs/plans/2026-10-03-r2-engine.md` task R2.6S (1428-1452), contract sections "Role identity and collection algorithm" and
"Route observation" (982-1035), Addenda 5 (null URL), 25 (slice R2.6S, wave W2) and 26 (D075); `w2-carryovers.md` (R2.6S, binding).
BASE `2b70e29fa7284fa4792dfa35f044ee0a37521641` (every line number is at BASE), worktree `C:/fks/t6s`, task id `6s`.
Line budget (gross): A about 260 html + 650 tests; B about 140 + 420; C about 120 + 480; total about 2,070 (html about 520, tests
about 1,550 of which about 90 are the forced edits below). The controller checks the total against the PR C cap before dispatch.
Three sequential phases, each a new implementer, green and reviewable alone; phase N+1 starts from phase N's patch (`PATCH_DEP`).
Patches: `task-6s-<a|b|c>-code.patch`. The owner's rulings (end of file) are folded into the body; the body binds.

## Why

Studio keeps only the latest Detect: `acceptDetectedRoles` (4348-4369) replaces `roleView.rows`, so evidence for earlier pages is gone,
the Detect request's `knownRoles` (4289) lists only the shown rows, and a revisit cannot be told from a new page. Nothing reads
`design:roles-page` (6B1 sends it; `BRIDGE_TYPES` 3396 lacks it, so it is dropped), so after an SPA route change the rows still look
current. `acceptRoleReady` (4062-4065) keeps `roleView.ids` across same-origin handshakes; nothing else is retained. A valid but
stale Detect reply is dropped silently (4354), leaving "Detecting text styles..." until "did not reply".

## Owned files (exact), per phase

`fontkit-studio.html`, only these ranges; everything else is read-only (`fontkit-bridge.js`, `tests/test_role_route_bridge.py`
belong to R2.6B2: build against the bridge at BASE and never wait for a change).

- **A**: `#detectedRoles` markup 1250-1275 (two new elements after `#roleRows` 1256; no `<pre>`: test_studio_roles.py:2006 counts
  one); `BRIDGE_TYPES` 3396-3397; 3741-3747 (`roleView`, role consts; add `roleCollection` and the A consts after 3747); shapes
  3971-3990 (delete `ROLE_RECEIPT_KEYS` 3972-3973, add `ROLE_WIRE.page`); `acceptRoleReady` 4044-4074 only at 4048 (key list) and
  4062-4065 (new-origin branch calls `clearRoleCollection(false)`); `renderDetectedRoles` 4076-4123 (calls the new
  `renderRoleInventory` after 4122) with the new model and render functions placed after 4123; Detect click handler 4285-4303;
  `validDetectedReply` 4304-4306 (key list only); `roleDetectUnreadable`/`acceptDetectedRoles` 4344-4370; `advanceRoleIdentity`
  4438-4443; `validRoleReceipt` 4459 (key list only); `acceptResetRoleState` 4529 (key list only); `message` switch 5600-5640
  (new `case "design:roles-page"` after 5634). `tests/role_contract.py` line 38 only (`'roles-page'` appended to `TOLERANT_KINDS`;
  the landing amends Addendum 25's R2.6S row to name it). New `tests/test_role_routes.py`. Forced test edits F1-F5 (below).
- **B**: `buildRouteSnapshot`/`renderRoleInventory` (A's functions); `acceptRoleReady` 4067 (one `compareEvidence` call in the valid
  branch); `ROLE_ROUTE_TEXT` const. `tests/test_role_routes.py` only.
- **C**: markup 1250-1275 (`#roleNotice` after `#roleStatus` 1253, `#roleClearVisited` in `.role-actions` 1257-1262); consts after
  3747; `installAcceptedRoles` 4024-4031 (notice cleared when `announce` is true); `acceptRoleReady` 4062-4074 (notice rules);
  `renderDetectedRoles` 4076-4123 (renders the notice); Detect click 4285-4303 (clears the notice); `computeRoleApplyState` 4218
  (hint text); the Clear handler (new, after 4393). `tests/test_role_routes.py` only. No existing test edit is forced in B or C
  (checked: test_studio_roles.py:1913-1926 and 846-880 hold because the notice is its own element and the origin branch stays).

## Read first

`constraints.md`; `docs/implementation/tasks/r2-task-6b1-{brief,report}.md` (roles-page is exactly `{type, protocolVersion,
sessionId, documentId, pageVersion, pageURL}`, sent after rendering at most every 250 ms, `pageURL` null for an unsupported URL, may
equal the version a Detect reply carries, may arrive before or after a stale Detect reply) and `r2-task-sk-{brief,report}.md`
(tolerant reader, strict echo, the Detect timer and its identity guard 4296-4298). Source: the ranges above; `validDetectedReply`
4304-4341; `validRoleURL` 3773-3782; `tests/test_studio_roles.py` 62-100 (`group`, `PEER`), 124-352 (`StudioRoleCase`: `open`,
`pending`, `reply`, `checks`, `detected`, `send`, `settle`), 3038-3041 (`frozen_clock`), 3101-3151, 3355-3370; `tests/role_contract.py`
(`with_unknown_keys`, `class_selector`, limits); `tests/test_r2_integration.py` 155-227; `fixtures/multi-page/expected-styles.json`
(oracle) and `spa.js`; `tests/test_r2_route_fixtures.py`; `fontkit-bridge.js` 1462-1479 (`suspendRoleSheet`, for B7).

## Model (binding, all phases; session only, never saved, never exported)

1. **State.** `const roleCollection = { routes:new Map(), refs:new Map(), labels:new Map(), evidence:null }`, beside `roleView`,
   outside `resetSessionState`/`resetRoleSession` and legacy saved state. Role IDs stay in `roleView.ids` (identity key to `role-N`)
   with `roleView.nextId`. **The origin has one source of truth: `roleView.origin` (3741)**, set in `acceptRoleReady`; the collection
   has no origin field. The inventory renders only while `roleView.origin === live.expectedOrigin`. `clearRoleCollection(keepCounter)`
   empties routes, refs, labels, evidence, `roleView.ids` and `roleDrafts`, sets `limitReached` false, and sets `nextId = 0` unless
   `keepCounter`. **A new origin resets the counter** (`clearRoleCollection(false)` in the 4062-4065 branch): the contract ties
   monotonic IDs to the origin collection's lifetime and a new origin starts a new collection. Clear visited pages (C) calls
   `clearRoleCollection(true)`: it does not end the lifetime, so an accepted role's `role-N` is never reissued (ruling 5).
2. **Route key** = the validated `pageURL` string itself (`validRoleURL` guarantees `href === value`, the authenticated origin, no
   credentials, path + search + hash <= 2,000 characters). Parameter order and hash are kept; nothing is sorted or normalised. Label
   = key without the origin. A null URL is never a key (Addendum 5).
3. **Snapshot** (one `buildRouteSnapshot(reply, ids)`, copying field by field from the tolerant copy, so no key of `data.groups` or
   `data.selectorChecks` is carried): A: `{ key, groups:[{ roleId, variants:[{ style, count }], selectors:[value] }] }` (`style` copies
   the five style fields one by one); B adds `checks:[{ roleId, selector, matchCount, found:[{ style, count }] }]`. No element counts,
   scanned counts or totals are stored (see Handoff, deviations). Storing a route is `routes.set(key, fresh)`: a revisit replaces the
   whole snapshot, keeps its first-visit list position, and nothing accumulates.
4. **References.** `refs: Map<roleId, Map<selector, style[]>>`, selectors in first-seen order. The first complete observation of a
   (role, selector) pair sets its styles from the introducing group's `signatures`; it is never rewritten or pruned until Clear
   (plan 1005-1007: retained IDs, selectors and references are bounded and stay even when a role has no matching page). Snapshots
   are replaced; retained selectors only grow. `labels: Map<roleId, string>` is set when an ID is issued: the author-role name, or
   the tuple text of a style identity.
5. **Tuple text** (`roleTupleText(style)`): `<fontFamily>: <fontSize>px / <fontWeight> / <textTransform> / <letterSpacing>em`, for
   example `serif: 32px / 700 / none / 0em`. The existing variant line (4100) keeps its count, the multiplication sign and then this
   text; every new line uses the literal ASCII `x` (`found 2 x <tuple>`). Tuples are compared by `roleIdentityKey({ kind:"style",
   style })`, never by text.
6. **Candidate validation** (`storeRouteEvidence(reply)`; only a complete, current, fully valid reply with a non-null URL; an
   incomplete, stale, unreadable or rejected one is never stored). Build the candidate (ids copy with `role-N` for new identity keys,
   routes copy with the snapshot set, refs copy plus new pairs, labels). Refuse the whole route unless: ids <= 128; routes <= 32;
   selectors per role <= 32; distinct reference styles per role, counted across all its selectors and pages, <= 8 (ruling 1); and
   the Detect request the candidate would produce fits 256 KiB UTF-8 (ruling 7): build it with the same `detectRequest(documentId,
   requestId, knownRoles)` function the click uses, with `documentId` padded to 200 characters and requestId `fks-detect-
   9007199254740991`, and test it with `safeRoleWire(request, 256 * 1024)`. On refusal: nothing stored, no ID consumed,
   `limitReached = true`, status exactly `Collection limit reached; this page was not stored`, the current detection's rows stay
   visible. On success commit everything and set status as BASE 4365. The click-time refusal `Role detection request limit
   reached.` (4293) is deleted: it is unreachable now (the padded estimate is an upper bound), and no test pins it after F4/F5.
7. **knownRoles** = every issued ID in issuance order with the full selector list from `refs` (`[]` when none); one
   `knownRolesFromCollection()` serves the click and the validation; it replaces the rows-based list at 4289-4290. Nothing is
   truncated or omitted.
8. **Evidence record** (the "pending" source): `evidence = { key, documentId, pageVersion, changed }`, set with `changed:false` only
   when a route is stored (`pageVersion` = `reply.currentPageVersion`). `compareEvidence(documentId, pageVersion, pageURL)` sets
   `changed = true` (sticky) when the document differs, the version is higher, the URL is null or its key differs. It runs inside
   `advanceRoleIdentity` (A: so a roles-page, a receipt and a reset share it) and in a valid ready (B), and after a refused Detect
   reply with that reply's identity. Cleared with the collection. A roles-page that arrives while a Detect is pending changes
   identity and `changed` but never writes `roleView.status` (the pending text stays); a null URL still cancels the pending Detect
   exactly as `advanceRoleIdentity` does at BASE 4442.
9. **Precedence (B).** Per (role, route), states are exclusive. Order: `changed` (the route equals `evidence.key` and
   `evidence.changed`: the snapshot no longer describes the page) > conflict (any check of that role found a style outside that
   selector's reference styles) > checked (a group of the role, or a check with `matchCount > 0` all inside the references) > no
   match (every check of the role has `matchCount` 0 and the role has no group there). Conflict outranks checked because hiding a
   disagreement is the worst error; a role with neither group nor check on a route is not listed for it.
10. **Rendering.** `#roleVisited` (hidden when no route is stored and after Clear, ruling 8): `Checked on N visited pages. Other pages
   have not been checked.`; for N = 1 `Checked on 1 visited page. Other pages have not been checked.`; N = stored routes. These are the
   only count claims. `#roleInventory` (`ul`, `textContent` only) lists ALL retained roles (not only the current rows) as
   `li[data-inventory-role="role-N"]` with `<label> (role-N)`, then per non-empty state a `p` with the approved label and a
   `ul[data-role-pages="checked|no-match|conflict|changed"]` of route labels in first-visit order. A: `checked` only, from groups. B:
   the four labels `Checked on:`, `No match on:`, `Different style on:` (each entry `<route>`, then lines `<selector>: expected
   <tuple>[; <tuple>], found <count> x <tuple>`), `Changed since checked:`; one `ROLE_ROUTE_TEXT` const. Pages never visited are
   never listed or counted (no denominator). Author-role variants are listed per route as `<count> x <tuple>` (Open question R3-1).

## Forced edits to existing tests (all in `tests/test_studio_roles.py` unless named; each is a characterization update)

- **A, F1** `tolerant_session` 3101-3128 plus the loop and docstring 3140-3151: the table gains `roles-page` (ruling 6), so the loop
  runs it through the role-state branch and fails. Add `elif kind == 'roles-page'` (Detect, then the wrapped roles-page for the same
  URL with `pageVersion` 1, wait for the status `The page changed since the last Detect; press Detect text styles. This page has not
  been checked.`); replace the docstring's last sentence ("belongs to R2.6S") with: raw reply objects are never stored is not
  observable by name; test_role_routes records the mutant as equivalent. Adds a case, weakens nothing.
- **A, F2** 3355-3370: the `messages` dict gains `'roles-page'` (`{type, documentId:'peer-document', pageVersion:1, pageURL:
  PEER_URL}`) and line 3364 expects `('detected', 'roles-applied', 'role-state', 'roles-page')`. Pins the contract table.
- **A, F3** `test_the_page_notice_message_changes_nothing` 1930-1941: BASE drops the message (PR C placeholder). New: an authenticated
  null-URL notice (document `peer-document`, version 5) clears the rows, disables Detect, shows `Role detection/preview
  unavailable: unsupported page URL.` and disables Apply (Addendum 5); the old "changes nothing, Apply carries pageVersion 0"
  assertions stay for the hostile variant (wrong session id), which is where they now apply. Rename and re-docstring it.
- **A, F4** 352-381 (bounded rows): 128 roles x two 1,050-character selectors is 270 KiB of `knownRoles`, which ruling 7 refuses.
  Give the 128 groups one shared 1,050-character selector (about 140 KiB, fits). Keep the `role-128`, 128-row, `Collection limit`
  (129th role after `ready()`) and reordered `role-1` assertions. Replace the "request limit" status wait and `requests.length == 1`
  (370-373) with: pressing Detect sends a second request carrying 128 `knownRoles`; the peer's final sent list gains no entry.
- **A, F5** 625-660 (UTF-8 bytes): the 128-role reply (about 275 KB of CJK selectors) is now refused as a whole. Keep the 100-role
  reply and its 100 `knownRoles`; the 128-role reply now ends with status `Collection limit reached; this page was not stored`, 128 rows,
  and Detect still sends (3 requests, `knownRoles` still 100). Keep the character-count guard (`characters < REQUEST_BYTES`).
  Mutant: validate by `string.length` instead of UTF-8 bytes (the 128-role route is stored).
- 1960-1980 (`assertIn('limit', reason)`, `startswith("Collection limit")` at 378 and 1970) pass unchanged in A and B; C's hint text
  still contains `limit`.

## Phase A: model, roles-page reader, limits, field lists, stale status

1. **Field lists (carryover 3).** Validators and acceptors read one key list per top-level message kind from the shape table:
   `ROLE_WIRE.detected.keys` (4305-4306), `.receipt.keys` (3988, 4459; drop `ROLE_RECEIPT_KEYS`), `.state.keys` (4048, 4529), new
   `.page`. Nested lists (group, style, variant, binding, check, outcome, loss, input) stay as written: deliberate (carryover 3 names
   the top-level lists). Behaviour-preserving; the existing suite passes except F1-F5. Mutant (report only): drop one key from
   `ROLE_WIRE.state`; the valid ready tests fail.
2. **Stale-but-valid Detect reply (owner, exact text).** A validated, matching reply with `currentPageVersion` below
   `identity.pageVersion` clears the timer, sets `roleView.pending = null` and the status `The page's reply to Detect was out of date;
   press Detect text styles again; this page has not been checked.`; stores nothing. Test: Apply in flight, Detect pending, a receipt
   advances the version, the stale valid reply arrives; assert the text, then again after `page.clock.run_for(9000)` (use
   `frozen_clock`). Mutant: omit `roleView.pending = null` (the timer then flips the text to "did not reply").
3. **roles-page reader.** `acceptRolesPage`: `readRoleReply` with `ROLE_WIRE.page`; requires `identity`, `documentId ===
   identity.documentId`, `pageVersion >= identity.pageVersion` (a count), `validRoleURL(pageURL, true)`, and refuses the same
   version with a different URL (as 4310 does for Detect). Valid: `advanceRoleIdentity`, then, with no Detect pending and a non-null
   URL, if `evidence?.changed` set the status `The page changed since the last Detect; press Detect text styles. This page has not been
   checked.` (rows stay visible). Null URL: rows cleared, Detect and Apply disabled, `Role detection/preview unavailable: unsupported
   page URL.`, earlier records kept. Invalid or no identity: ignored, no status. It sends nothing. Tests (peer): valid advances the next
   Apply's `pageVersion`; the same-version-different-URL, wrong-session (envelope), wrong-protocol, foreign-origin, credentials,
   other-document, older-version, `__proto__` key, array in the `pageURL` position, non-finite number, `__proto__`/constructor/
   prototype nested inside an unknown key, and 1 MiB + 1 rows each change nothing; an unknown key is ignored; null keeps the earlier
   inventory. Mutants, one per row: skip the document check; drop `>=`; accept a foreign origin; skip the same-version URL check;
   skip the session check; skip the hostile-key scan.
4. **Old request generation.** A Detect reply for an older `requestId` (a newer Detect is pending) stores nothing: `#roleVisited`
   and the inventory stay as before. GREEN characterization of 4350; mutant: drop the `requestId` equality.
5. **Collection and identity** (peer pages built with `group()` and literal URLs): equal styles on two routes with different
   selectors keep one ID, separate selectors in `knownRoles`; duplicate suggested names get distinct IDs; reordered discovery cannot
   remap an ID; author names that differ by case or by Unicode form (`Body`/`body`, a precomposed and a decomposed name) keep
   separate IDs; near-duplicate flags do not merge identities; author-role variants stay visible in the row and the inventory. Mutants:
   remap by scan order; fold the author name's case; `knownRoles` from the shown rows.
6. **Route keys and replacement.** URLs `?a=1&b=2`, `?b=2&a=1`, the same with `#keep`, and `#keep2` are five routes; a 2,000-character
   path + search + hash is accepted and its label wraps (at 1440 and 390 px `#detectedRoles.scrollWidth <= clientWidth`). A revisit of
   a key whose new groups drop a role removes that route from the role's list and keeps `N` unchanged; the route keeps its first
   position. Mutants: sort the query; drop the hash; append instead of replace.
7. **Limits** (each refuses only the new snapshot, with the exact text, earlier lists unchanged, Apply disabled with the BASE hint
   4218): the 33rd route; the 129th role; the 33rd selector of one role; the 9th reference style of one role (spread over two
   selectors); no ID is consumed (the next accepted role is `role-(n+1)`). One mutant each: allow 33 routes; 129 IDs; 33 selectors;
   count tuples per selector instead of per role; store the route anyway.
8. **256 KiB boundary (ruling 7).** Oracle in Python: the request bytes from `json.dumps(request, separators=(',', ':'),
   ensure_ascii=False)` with the peer's real `sessionId`, `documentId` of 200 characters, requestId `fks-detect-9007199254740991` and
   the candidate's `knownRoles` (selectors from `table.class_selector(n)`, n <= 2,000). Size the last selector so the total is exactly
   `table.REQUEST_BYTES` (stored) and exactly one byte more (refused with the limit text, earlier evidence kept); after the stored
   one, Detect sends (requests +1, all `knownRoles` present). Mutants: compare with `REQUEST_BYTES + 1`; count only the current
   route's roles.
9. **Unknown keys never stored (carryover 2, ruling 4; no heap probe, no test hook).** A complete reply with `table.with_unknown_keys`
   at every level renders the same `#detectedRoles` text, produces the same next Detect request bytes and exports, and no output
   holds the marker. The oracle is what a user or the wire observes. The mutant "snapshot stores `data.groups` raw" changes none
   of these, so record it in the report as an equivalent mutant with that reasoning; never weaken a test for it.
10. **Real bridge** (`RoleRouteBridgeTests`, harness below): visit index, article, conflict, then index again by Interact-mode link
    clicks and Detect; `Checked on 3 visited pages. Other pages have not been checked.`; the base-title role's list holds index
    and article, not conflict (conflict.html's title is another identity); the layout oracle is computed styles of the target (the
    literals of `expected-styles.json`), not Studio's data; `unvisited.html` is never listed. RED at BASE: no inventory, first page's
    rows vanish. Mutant: print every stored route under every role.
11. **Real bridge, SPA** on `spa.html`: Detect at `/spa.html` (view home), click `#replace-same` (same URL, view same): the status
    becomes the page-changed sentence (a real roles-page), Detect again replaces the `/spa.html` route (`N` stays 1): the home title
    role no longer lists `/spa.html`, the same-title role does. Mutant: append instead of replace.

Harness for real-bridge tests (no fixture edit; D060 bytes fixed): subclass `StudioRoleCase`; call `open(engine, TARGET +
'/fixtures/multi-page/index.html', <index.html bytes with '<script src="/fontkit-bridge.js"></script>' inserted before </body>>)`
(the exact-URL route serves it), then at once `page.context.route(TARGET + '/fixtures/multi-page/*.html', <handler that reads the
file and inserts the same tag>)` so later pages carry the bridge, click `#bridgeModeInteract` (Select mode swallows link clicks;
probed), click links in the frame, and re-read `frame` after each navigation. Probed on BASE.

Focused command A (from `C:/fks/t6s`, about 6 min): `PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_role_routes
test_studio_roles test_support -v`.

## Phase B: checked, no-match, conflict and changed states

1. Add `checks` to the snapshot (Model 3) and the four-state inventory (Model 9-10); `compareEvidence` in the valid ready (a reload
   or new document marks the old route changed). All retained roles are listed even with no row on the current page, labelled by
   identity (Model 4), so a role absent from the current Detect still shows its conflict.
2. Tests (peer, literals): **states** across four routes of one role (group seeds the reference; zero matches; a check outside the
   reference; a revisit of the conflicting route with an inside signature turns it to checked) with the exact lines `Different style
   on:` and `<selector>: expected <tuple>, found 1 x <tuple>`. Mutants: count no-match as checked; compare only the first signature;
   compare against the latest page instead of the reference; append on revisit.
3. **Precedence**: one role with three selectors on one route (zero, inside, outside) is listed only under `Different style on:`; (zero,
   inside) only under `Checked on:`; (zero, zero) only under `No match on:`. Mutant: list under every matching state.
4. **Retained role without a row**: a role observed on route 1, absent from the groups of route 3 whose check conflicts, still shows
   by its label (author name, and the tuple text for a style role) under `Different style on:`; the reused selector gives role-1 a
   conflict and the new identity a new ID (fixture: `.shared-title` on conflict.html). Mutant: build the list from `roleView.rows`.
5. **Changed**: after a stored Detect, a roles-page with a higher version (or another URL) moves that route to `Changed since
   checked:` and out of `Checked on:`, `N` unchanged, status is the page-changed sentence; while a Detect is pending the same
   roles-page leaves the pending text alone; a null URL marks it changed; a new stored Detect restores it; a reload (new document)
   marks it changed. Mutants: show changed as checked; let the roles-page overwrite the pending status.
6. **Late scans**: C's list and `N` do not change when B's complete reply (older page version) or a reply with another `documentId`
   arrives after C's roles-page. Mutants: drop the identity guard; store the stale reply.
7. **Real bridge, drift under a live preview** (replaces the old B3, which would run on a fresh document): on `spa.html` Detect at home,
   Apply a size (50) on the home-title role, click `#push-detail` (same document, the owned sheet persists, `.shared-title` becomes the
   detail style), Detect. The conflict line holds the baseline tuple `serif: 36px / 700 / none / -0.01em` (oracle:
   `expected-styles.json` detail-title) and never `50px`. Mutant: a scratch copy of `fontkit-bridge.js` with `sheet.disabled =
   true;` removed from `suspendRoleSheet` (1476), served through `context.route(TARGET + '/fontkit-bridge.js', ...)`; the repository
   copy is never edited.
8. Author-role variants and reordered discovery keep their lists per route (A5 re-asserted through the four-state inventory).

Focused commands B (two, each under 10 min): `... unittest test_role_routes test_support -v`, and `... unittest test_studio_roles
test_r2_integration test_support -v` (from `C:/fks/t6s`, `PYTHONPATH=tests FKS_ENGINES=chromium`).

## Phase C: new documents, origins, Clear visited pages

1. **`#roleNotice`** (`p`, `role="status"`, `textContent`, hidden when empty) in the panel under `#roleStatus`; field `roleView.notice`.
   It holds the latest of three sentences and is replaced by the next, cleared by a Detect click and by an accepted Apply, Clear
   preview or reset (`installAcceptedRoles` with `announce` true), never by a same-document ready.
2. **Not applied.** In a valid ready, if `rolePreview.documentId !== state.documentId`, `rolePreview.origin === live.expectedOrigin`,
   `rolePreview.roles.length > 0` (read before the ready overwrites them) and `state.roles` is empty, the notice is exactly `Role
   preview is not applied on this page.`; any other new document clears it. A re-hello of the same document (same `documentId`) leaves
   it alone, and an SPA route change in one document never shows it. Studio sends no Apply (peer: only hello; real bridge: the
   page's computed style is the author's). `#rolePreviewStatus` keeps its BASE text (so 1913-1926 holds).
3. **New origin.** The 4062-4065 branch, when `roleView.origin` was non-null, sets the notice `A new Live App origin started a new
   collection; visited pages from the previous origin were cleared.` after `clearRoleCollection(false)`; it shows at the new origin's
   first valid ready and persists through it (the status line is separate). If that origin never sends a valid ready, the old
   collection is hidden (Model 1) and returns if the user reconnects to it. Connecting the same origin changes nothing.
4. **Clear visited pages**: button `#roleClearVisited`, label exactly `Clear visited pages`, always enabled. It calls
   `clearRoleCollection(true)`, clears the rows and any pending Detect (timer cleared, `pending = null`; a late reply is ignored), keeps
   `identity`, sets status to the Ready/unavailable text, and the notice `Visited pages cleared. The applied preview and inspector
   edits stay.` It sends nothing and leaves `rolePreview` and the Apply/Clear preview controls alone. `#roleVisited` hides.
   Apply-disabled hint (ruling 2) for any overflow: `Collection limit reached, so Apply is disabled until you clear visited
   pages.` (4218; the two BASE assertions on "limit" still pass).
5. Tests. **Reload, peer**: Detect, Apply, reload the peer (new `documentId`): notice, N and inventory kept, peer received only
   hello. **Same-document re-hello** (`ready()` again): no notice. **Real bridge**: Apply on index, `frame.reload()`: computed style is
   the author's, the notice shows, a fresh explicit Apply works. **SPA**: Apply on `spa.html`, click `#push-detail`: the title stays
   previewed and the notice is empty. **Pop-out and dock** (real bridge, `#bridgePopOut`, `#bridgeDock`): the inventory and `N` survive
   both; in the pop-out window the style is the author's and the notice shows; after dock it clears. Mutants: show the notice on a
   same-document ready; on any roles-page; clear the collection on pop-out or dock.
6. **Cross-origin**: connect a second virtual origin (as test_studio_roles.py 868-880 does), Detect there: the inventory is empty, the
   notice is the new-origin sentence, the next role is `role-1` (the counter restarted); returning to the first origin starts empty
   again. Hostile Detect replies carrying a foreign-origin URL, credentials, `javascript:`, a 2,001-character path, or a null URL in a
   complete reply store nothing (no `#roleVisited`, no inventory). Mutants: keep routes across origins; keep `nextId`; accept 2,001.
7. **Clear**: after overflow Clear re-enables Apply (the hint disappears; a new Detect and tick allow Apply); a pending Detect cleared
   by Clear is not repopulated by its late reply; the accepted preview survives (css text and no `design:roles-clear` sent); the next
   Detect issues `role-(n+1)`. Mutants: Clear sends roles-clear; leaves the Detect pending; resets `nextId`; leaves `#roleVisited` shown.
8. **Legacy output unchanged**: imported legacy JSON, saved overrides, code tabs and sync PUT bodies are byte-identical before any
   Detect and after a multi-page session and Clear. Mutant (scratch Studio copy): append the route list to the Json tab.

Focused commands C (three): `... unittest test_role_routes test_support -v`; `... unittest test_studio_roles test_support -v`; and with
`FKS_REQUIRE_FIXTURES=1`: `... unittest test_r2_integration test_live_integration.SyncAndReloadTests test_support -v`.

## Requirements common to all phases

1. Every checked-page claim comes from stored complete current evidence; the two count sentences (Model 10) are the only count
   claims; lists are `textContent`, never markup. Use only the plan's fixed strings and the owner-approved strings quoted here.
2. Every new test has a Given/When/Then docstring, uses the existing base classes (`shared_runtime`/`new_context`), waits on
   conditions, types with keystrokes where a field is typed, and asserts what the page renders or the wire carries. Each phase has a
   real Studio-real bridge test. Every changed reader has hostile cases (wrong origin, document, session, older version, hostile
   key, oversize).
3. TDD per phase: tests first, quote the failing assertion at the phase base; GREEN characterization where behaviour already works
   (never manufactured RED). **Every test and every table row has one realistic mutant** (named above), run on a scratch Studio copy
   or `RoleBridgeCase.open(bridge_source=...)`; `fontkit-studio.html` SHA-256 equal before and after. The one exception: A9's
   raw-snapshot mutant is recorded as equivalent (ruling 4).
4. No test-only hook, global or protocol field. Do not touch `resetSessionState` semantics, the legacy ledger, saved overrides or
   export code. Scratch files carry `6s` and the phase letter.
5. Report: per phase the patch, RED/GREEN lines, mutant table, gate output, Handoff.

## Handoff (for the landing)

Subjects (<= 72 characters; counted 58, 67, 68): A `feat(studio): keep session-only visited-page role evidence`; B `feat(studio): show
checked, no-match and conflicting pages per role`; C `feat(studio): clear visited pages and refuse evidence across origins`. Why-bodies
in product terms (wrap 72) and ledger lines. The controller adds the plan boxes (all but `Focused`), amends Addendum 25's R2.6S row
(role_contract.py line 38; the F1-F5 edits in test_studio_roles.py), and rewords role_contract.py 89 (`REQUEST_BYTES`: Studio now
pins the exact boundary, test_role_routes). Deviations to record (D-record): no totals are rendered (plan 1028-1029 labels a total
`across visited-page observations` only if one is shown; the R2.6S boxes 1432-1452 need none), no separate `generation` counter (a
Clear sets `pending = null`, so a late reply is dropped; the effect is the same), the new-origin sentence appears at the first valid
ready, not at connect time. Not run here: Firefox, frontend gate, hosted CI.

## Open questions (round 3; the brief stands on the recommendations)

- R3-1: three formatting details the approved strings do not fix: the joiner for several expected tuples (`; `), the author-role variant
  line in the inventory (`<count> x <tuple>`, one per variant), and the order of entries (first visit). Recommend as written.

## Rulings (binding; already folded into the body)

1. Per role, all selectors: the cap of 8 counts distinct reference styles across a role's selectors and pages; a ninth refuses the
   route. 2. The OQ2 texts are approved verbatim (page-changed, `Checked on:`/`No match on:`/`Different style on:`/`Changed since
   checked:` with `<selector>: expected <tuple>, found <count> x <tuple>`, new-origin, Clear, Apply-disabled hint). 3. `1 visited
   page` for one. 4. No heap probe; observable oracles; the raw-snapshot mutant is recorded as equivalent. 5. Clear keeps the
   counter. 6. This slice owns `tests/role_contract.py` line 38. 7. The would-be Detect request must fit 256 KiB or the route is
   refused. 8. `#roleVisited` is hidden until one route is stored and after Clear.

## Revision 1 (2026-10-18)

Resolves `task-6s-brief-review.md`. Line numbers are lines of this file.

- Important 1 (rulings folded): role_contract.py line owned 24-31; heap probe replaced by observable oracles and an equivalent
  mutant 181-184, 283-284; singular sentence 104-106; new origin resets the counter, Clear keeps it 54-61; old OQs removed 300-303.
- Important 2 (forced edits): table of F1-F5 plus the role_contract line, each with file:line, old and new expectation and why
  113-135; "must pass unedited" replaced 139-142; B and C force none 35-40.
- Important 3 (256 KiB): ruling 7 as a candidate check 79-88; click guard deleted 87-88; exact-boundary test 175-180; F4/F5 125-135.
- Important 4 (phase B state model): all retained roles, labelled from identity 70-74, 104-110; precedence 99-103; evidence record
  (stored, compared, cleared, roles-page while pending) 92-98; tuple text with ASCII x 75-78; N = 0 hidden 104-105.
- Important 5 (replacement, totals): snapshots replaced and retained selectors only grow 65-74; revisit tests 167-170, 190-193;
  totals not rendered, with plan citation 289-298.
- Important 6 (missing tests): query order and hash 167-170; SPA real bridge 190-193, 223-230, 239-243; dock/pop-out 253-257;
  wrong-session, same-version different URL, nested hostile key 149-159; old requestId 160-161.
- Important 7 (B3): rewritten on the same document with the bridge-copy mutant 223-230.
- Important 8 (Apply hint): phase C, with the Clear control 248-258.
- Important 9 (notice element and lifetime): `#roleNotice`, lifetime and conditions 236-247; one origin source 54-61.
- Important 10 (owned ranges): per phase, exact at BASE, including 4459, 4529, 4024-4031, 4227-4248 not touched 24-40.
- Minor 1 mutants per test: 144-148, 159, 161, 166, 170-180, 273-287. Minor 2 stale mutant 144-148. Minor 3 subjects 289-292.
  Minor 4 split commands 200-201, 231-233, 270-272. Minor 5 harness 194-199. Minor 6 per-role discrimination 185-189. Minor 7 added
  tests 162-180, 215-216. Minor 8 long labels 167-169. Minor 9 nested lists deliberate 139-142. Minor 10 docstring 115-119.
  Minor 11 "count claims" 104-106, 275. Minor 12 cuts: A8 shrunk, `generation` dropped 289-298, 40-selector test replaced 175-180.
- Plan-mandated: 256 KiB versus knownRoles settled by ruling 7 (79-88); Addendum 25 row amendment named in the Handoff 289-295.

## Controller rulings, round 3 (2026-10-18)

- R3-1: as recommended: several expected tuples join with `; `, an author-role variant line reads
  `<count> x <tuple>`, and entries list in first-visit order. These are formats inside the owner-approved strings,
  not new wording.
- Totals: no element-count total is rendered. The plan's "Show ..." list for R2.6S names the page summary, per-role
  page lists, no-match pages, conflicts and pending/stale states, not totals; the "across visited-page observations"
  label binds only if a total is shown. This is a reading of the plan, not a deviation; the report says so.
- The new-origin sentence shows at the new origin's first valid ready in `#roleNotice`, as the brief now says.

## Revision 2 (2026-10-18; scoped re-review findings folded by the controller, `task-6s-brief-rereview.md`)

Importants:
- I1: keep both checks. The candidate-route estimate pads `documentId` and the request id to their worst-case JSON
  width (200 units, each a 6-byte `\uXXXX` escape when a control character), so it is a true upper bound; AND the
  existing click-time refusal `Role detection request limit reached.` stays (it is not deleted). The boundary test
  uses the real request bytes as its Python oracle.
- I2: add F6: `tests/test_studio_roles.py` 1141-1160 (128 groups of `'.' + '界' * 700`) is refused as a route under
  ruling 7; adapt it exactly as F5 (forced characterization edit, same reasoning), in phase A.
- I3: this slice also owns a `roles-page` branch in `violations` in `tests/role_contract.py` (the message's exact
  revision-1 fields: type, protocolVersion, sessionId, documentId, pageVersion, pageURL), beside the TOLERANT_KINDS
  line, so F2's loop covers it. The landing amends Addendum 25's R2.6S row to name both.
- I4: F4's range is 356-388; line 386's expected sent list becomes hello plus 4 detects (the click BASE refused now
  sends). State it as that forced characterization update.

Minors (adopt the review's fix for each): A2's mutant reworded so it is not equivalent (M1); one assertion each for
the three notice-clearing rules (M2); in one ready the new-origin sentence wins and C2 runs only when the origin
branch did not (M3); focused command A split into `test_role_routes test_support` and
`test_studio_roles test_r2_integration` (M4); the evidence record's narrower semantics stated exactly (M5); record in
the A and B reports that the old 128-roles hint wording stays until phase C (M6); Clear sets the Ready/unavailable
status only when `roleView.identity` is non-null (M7); A10/A11 assertions scoped to the `Checked on:` list (M8); own
CSS 778-783 only if the wrap test is RED (M9); the Handoff deviation list keeps the click-time refusal as kept, not
removed (M10, follows I1); B7 asserts its scratch replacement count is exactly 1 (M11).

Cuts (accepted; no contract obligation lost): drop A9 (the existing tolerant-reply test already compares the panel,
the next Detect request bytes and both exports); drop B8; in C6 keep only the `javascript:` URL and the 2,001-character
route (the others are in the existing hostile-shapes table, test_studio_roles.py 586-588).
