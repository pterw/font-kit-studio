# R2.7F2b brief: React role preview integration

Plan: `docs/plans/2026-10-03-r2-engine.md`, task R2.7F2b; Addendum 16 item 4 (as clarified by Addendum 18);
D063, D066, D067; the binding contract (apply/clear, receipts, page version, undo). Reconciles the
2026-10-08 draft (`react-role-brief-draft.md`), which predates D063-D067. PR B2, wave W1. BASE: the W0 head,
filled in at dispatch, with R2.4's code patch applied in the worktree as `PATCH_DEP` (unstaged, never part of
your patch). Worktree `C:/fks/t7f2b` with fixtures linked. Task id `7f2b`. Line budget: about 450 material
lines; explain any excess. Brief gate: passed (first review Not ready, folded; scoped re-review Ready with
fixes, folded).

## Why

React apps replace DOM nodes on state changes, and Vite rewrites the text of the app's CSS-module `<style>`
on hot updates. The role preview must keep styling replaced nodes (from its one owned stylesheet, never inline
writes), must say honestly when a hot update or re-render outdates a receipt, and Clear must reveal the app as
it is now. Hosted CI runs this module with its fixture installed (R2.7Ia), so every new case blocks there.

## Owned files (exact)

Only `tests/test_r2_react.py`. Fixture source, lockfile and config, `fontkit-bridge.js`, Studio, shared
helpers, host fixtures, workflows and records are read-only. Local helpers in the module are fine; no new
shared helper file.

## Read first

`constraints.md`; the draft and its 2026-10-08 review (`react-role-brief-review.md`); this brief's review
(`task-7f2b-brief-review.md`: its probes are the evidence for every mechanism below) and its scoped re-review
(`task-7f2b-brief-rereview.md`: probes of the revised harness, cases and mutants); the F2a records
(`docs/implementation/tasks/r2-task-f2a-{brief,report,review}.md`) and the hot-update fix records
(`r2-task-hmr-{report,review}.md`); the current module (`app()`, `start_vite`/`stop_vite`, `guarded_context`,
the bounded hot-update restore); `tests/fixtures/bridge/host-roles.html` (`hello`, `request`, `control`,
`waitFor`, `messages`); R2.4's code report (the controller sends its path with `PATCH_DEP`).

## Harness

The Vite hot-update channel only works when the host page and the app document are both real loopback
documents: Chromium's Local Network Access checks block the Vite WebSocket of a document that Playwright
fulfilled (`ERR_BLOCKED_BY_LOCAL_NETWORK_ACCESS_CHECKS`) and block a real loopback iframe under a fulfilled
host. So neither `route_virtual_origins` nor `route.fulfill` may serve either document; the pattern in
`tests/role_support.py` fits static targets only. Build it this way:

- Host: an owned `http.server.ThreadingHTTPServer` on `127.0.0.1`, port 0, with a `SimpleHTTPRequestHandler`
  rooted at `tests/fixtures/bridge` and `log_message` silenced. Open
  `http://127.0.0.1:<host port>/host-roles.html?target=` + `quote(<Vite URL>, safe='')`. In `finally`,
  `shutdown()`, `server_close()` and a refused connect, beside the Vite checks.
- Bridge: leave the app's document alone. A context init script (`add_init_script`), guarded by
  `location.origin === <Vite origin>`, appends `<script src="/fontkit-bridge.js">` to `body` on
  `DOMContentLoaded`. `context.route(<Vite origin> + '/fontkit-bridge.js', ...)` fulfils that one file from
  `self.bridge_source()`, a method that reads the worktree's `fontkit-bridge.js` bytes; a mutant runner
  overrides it, and it is the only seam. Fixture files and the production build stay untouched.
- Keep the module's HTTPS guard (canaries first, the earlier local fallback route kept), the scratch fixture
  copy, `require_fixture`, owned Vite shutdown, byte restoration and the exit check that the app made no HTTPS
  request. `guarded_context` gains `**options` so the context can take a 1500x1000 viewport.
- Wait for `frame.locator('h1')`, then for the bridge itself: the init script appends it at DOMContentLoaded, it
  announces itself only when it runs, and the host's `hello()` sends once, so a hello sent earlier is lost (the
  helper then rejects "reply timed out" after 6 s). Read the host's log:
  `page.evaluate("(o) => waitFor((d, e) => e.fromTarget && e.origin === o && d.type === 'design:bridge-ready')",
  <Vite origin>)`. Then `hello()`, then `control({'type': 'design:mode', 'mode': 'interact'})` (in the default
  select mode the bridge swallows the click that Enter or Space produces on a target).
- `design:mode` has no reply, and a key press is not ordered against a posted message: send a request (a first
  Detect) and await its reply between `control` and the first key press.
- One Vite per test method. Each hot-update test makes exactly one forward write (cases 4 and 5).
- Bind the target frame to a local named `frame` and read markup only through it (`test_support`'s raw-markup
  guard flags `evaluate` text containing `innerHTML`/`outerHTML` unless the call's first name is `frame`, and flags
  `.inner_html()`, `.outer_html()` and `.content()` on every receiver: read markup with
  `frame.locator('main').evaluate('el => el.outerHTML')`).
- Fallback only if the loopback host cannot be built: launch an own Chromium with
  `--disable-features=LocalNetworkAccessChecks` (it disables a browser protection; Chromium only) and close it
  in `finally`.

## Cases (all real React, real bridge, authenticated host; none may skip with the fixture installed)

Literal expectations come from `fixtures/vite-react-css-modules/expected-styles.json` (`styles`, and the
`authorIds` under `bindings`), the fixture source, the contract and this brief, never from the bridge. After
`hello` the bridge tags the unannotated paragraphs `data-design-role="body"`, so the oracle's own probe
`p[data-design-role="body"]` counts 4; `assert_styles` stays valid only before `hello`. After it, read the
elements through these selectors: title `[data-design-id="modules.title"]`, bodies
`[data-design-id="modules.body.first"]` and `[data-design-id="modules.body.second"]`, hash-only `aside > p`,
stable-class `p.stable-copy`, action `[data-design-id="modules.replace"]`.

1. **Detect.** After the h1 wait and `hello`: `complete` true, `scannedElements` 6, five groups. The test
   reads the observed class of `aside > p` itself and never predicts a hash:
   - display: identity author-role `display`, elementCount 1, the display row, selector
     `[data-design-role="display"]` (author-role, stable true);
   - body: identity author-role `body`, elementCount 2, the body row, selectors
     `[data-design-id="modules.body.first"]`, `[data-design-id="modules.body.second"]` (author-id, stable
     true). It binds by id because the bridge tags the two unannotated paragraphs `data-design-role="body"`
     after hello (assert the frame counts `[data-design-role="body"]` as 4, the observation that explains it);
   - hash-only: identity style (the hash-only row), suggestedName `Text`, selector `.` + `CSS.escape(class)`
     of `aside > p` (css-module, stable false);
   - stable-class: identity style (the stable-class row), `Text`, `.stable-copy` (class, stable true);
   - action: identity style (the action row), `Text`, `[data-design-id="modules.replace"]` (author-id, true).
   Every group has `bindingComplete` true and `adapter` `'plain'` (no Bootstrap evidence; needs `PATCH_DEP`).
2. **Apply.** First, hostile requests, each rejected `unsupported-value` with detail `Unsupported selector`,
   revision still 0, no owned node, computed fonts unchanged: selectors `['body']`, `['h1, p']`, `['p:hover']`.
   Then one request with three roles built from the Detect reply's own selectors: display
   `{fontFamily: 'Georgia, serif', fontWeight: 700}`, body `{fontFamily: 'Verdana, sans-serif',
   letterSpacing: 0.05}`, hash-only `{fontFamily: '"Courier New", monospace', fontSize: 15}`; no role sets the
   title's size, so case 4 can see the hot update. Receipt: operation `apply`, revision 1, `outcomesComplete`
   true, outcomes (matched, checked, mismatched) (1,1,0), (2,2,0), (1,1,0) with no losses, `canonicalCss` equal
   to a literal in the test (three blocks in request order, two-space indent, final LF, the third selector built
   from the observed class), `cssHash` equal to FNV-1a32 of those bytes from a test-local reference (offset
   2166136261, prime 16777619; never read from the bridge). Rendered through those selectors: the
   display, body and hash-only elements show the role values with their other properties from the literal rows;
   the stable-class control and the action button keep their literal rows; no element has a `style` attribute;
   one `#fontkit-role-styles` node whose text equals `canonicalCss`. Then a Detect with the preview live returns
   the literal baseline rows, not the role values (D067), and Clear carrying its version succeeds: `roles`
   empty, `canonicalCss` empty, `cssHash` `811c9dc5`, the owned node gone, and `main`'s outerHTML (read
   through `frame`) equals the one taken after hello.
3. **Replacement.** In interact mode, with the case 2 preview live: focus `Replace text`, press Enter, then
   Space; after each press wait for `h1` to read `Module title <n>` (the F2a condition) before reading or
   sending anything. The old title and body elements and their text nodes detach (handles taken before each
   press), the new nodes show the role values from case 2 and the literal rows for every other property, their
   `data-design-role`, `data-design-id` and `class` equal the fixture's, no element has a `style` attribute, and
   the owned node is the same single node with the same text. The replacement advanced the page version: a
   Clear carrying the receipt's `pageVersion` is rejected `page-changed` and changes nothing; after a fresh
   Detect (greater version), Clear is accepted, the owned node is gone and the new nodes show the literal rows,
   read through those selectors.
4. **Hot update after Apply (D063).** Replace the section once (Enter, interact mode; wait for `Module title 1`),
   then Detect and Apply the case 2 display role alone (no size set), so the receipt's version already includes
   the replacement. Write the title declaration 40px to 44px once. The document marker, the React text
   `Module title 1` and the title node survive; the computed title is the role's family and weight at 44px (the
   role survives, the author size shows); the page version is greater than the receipt's (a hot update advances
   it by 2 here: assert greater, never +1). A Clear carrying the receipt's `pageVersion` is rejected
   `page-changed` and changes nothing (revision, one owned node with unchanged text, computed role font). An
   Apply carrying the receipt's `pageVersion` is rejected `page-changed` the same way. Read the greater version
   from the fresh Detect's `pageVersion`; a rejection carries none. After a fresh Detect the display group's
   baseline is serif/44/600/uppercase/0.02 (the app as it is now, not the preview). Clear then succeeds:
   operation `clear`, revision + 1, `roles` empty, `canonicalCss` empty, `cssHash` `811c9dc5`,
   `outcomesComplete` true, `outcomes` empty; the owned node is gone; the title is serif/44/600/uppercase/0.02,
   not the 40px seen before the update. Restoring the source bytes (the shared bounded restore) returns the
   literal 40px row.
5. **Hot update during Apply.** A real hot update lands after Apply's commit and before the bridge's
   measurement. The one `roles-applied` receipt carries the committed roles, `canonicalCss` and `cssHash`
   (literals), `pageVersion` equal to the Detect's, a greater `currentPageVersion`, `outcomesComplete: false`,
   `outcomeReason: 'page-changed'` and `outcomes: []`. A hot update takes 19 to 36 ms to land while the bridge
   measures on the next frame (8 to 20 ms), so a write timed from the receipt delay misses. Hold the frames
   instead. Before sending Apply, `frame.evaluate` (a) replaces `window.requestAnimationFrame` with a stub that
   stores callbacks, so the bridge measures from its 250 ms fallback timer; (b) observes the app's
   `style[data-vite-dev-id]` node (childList, characterData, subtree) to stamp `hmr`; (c) adds a `message`
   listener (it runs after the bridge's own, in the same task) that, on `design:roles-apply`, stamps `commit`,
   restores the real `requestAnimationFrame` and starts its own 250 ms timer that stamps `deadline`. Send Apply
   from a block body, without awaiting it: `page.evaluate("(m) => { window.pending = request(m); }", msg)` (an
   expression body returns the promise, and Playwright awaits it). Wait for `commit` with `polling=10` (the
   default raf polling can use the page's own stubbed `requestAnimationFrame`), write the 44px CSS once, wait
   for the computed 44px, then await the receipt. Premise, asserted before any receipt field: `commit < hmr <
   deadline`; otherwise fail naming the three numbers. Exactly one `roles-applied` arrives for the request id.
   The docstring says the frame callbacks are withheld, so the bridge measures from its 250 ms fallback timer,
   not that a frame was missed. Then, carrying the Detect's version (the receipt's `pageVersion`), an Apply and
   a Clear are each rejected `page-changed` and change nothing (revision, owned node text, computed fonts);
   after a fresh Detect the same Clear is accepted. (A client carrying the receipt's `currentPageVersion`, as
   Studio does, is accepted and re-measured: Addendum 18; do not claim otherwise in a docstring.) Restore with
   the shared bounded restore.

Each new test method has a Given/When/Then docstring whose Then is exactly what it asserts. No React Fast
Refresh claim: the fixture adds no React plugin, so CSS updates are Vite CSS hot updates.

## Preserve

The five F2a tests keep their names and assertions. The only edit allowed in them is replacing the inline
restore loop of the hot-update test (waits 1 s four times, then 10 s; same failure text) by one local helper,
`restore_css(frame_or_page, css, original)`, that cases 4 and 5 also call. They stay on the app without the
bridge, so the literal six-parent, four-signature baseline is still asserted before any bridge exists. Every
new context manager calls `require_fixture` first (a missing install fails under `FKS_REQUIRE_FIXTURES=1`); no
new case calls `skipTest`.

## Mutants (foreground; served through the bridge route by a scratch runner `mutate-7f2b-<n>.py` outside the repository that overrides `bridge_source()`; the module and `fontkit-bridge.js` are never edited; report the SHA-256 of `fontkit-bridge.js` before and after)

1. Detect-side selector verification, `roleBindings`' `choose()`: drop the member check and accept a covering
   superset (remove `found.some(el => !members.has(el))`, change `covered.size !== members.size` to
   `covered.size < members.size`). The body group then binds `[data-design-role="body"]` (4 matches) and Apply
   restyles the two bridge-tagged paragraphs. Fails case 1 (body binding) and case 2 (outcomes (2,2,0), the
   stable-class control and the hash-only row).
2. Apply-side selector validation, `canonicalizeRoles`: `checked.set(selector, true)`. Fails case 2's hostile
   requests.
3. Freshness: remove both `roleJobFresh` rechecks in `measureRoleReceipt`. Fails case 5 (a complete receipt
   with outcomes).
4. Clear restores a captured value instead of removing the owned node: capture each matched element's computed
   font size at Apply, write it inline at Clear. Fails case 4 (computed 44px after Clear, the style attribute).
5. Inline writes instead of the owned sheet: Apply writes each role's properties to `el.style` and empties the
   owned node's text after its verification. Fails case 2 (style attribute, owned text) and case 3 (replacement
   nodes unstyled).

Targets, each found once in the bridge (mutant 3: both lines): 1 the two quoted expressions; 2 the
`roleSelector(selector, true)` call inside `checked.set(...)`, replaced by `true`; 3 the two
`if (!this.roleJobFresh(job)) { ... }` lines of `measureRoleReceipt`. Report the line numbers you changed in
`PATCH_DEP`'s bridge (R2.4 moves BASE's: 1736 and 1739, 240, 1443 and 1452 at BASE). The working-tree bridge is
CRLF on the Windows checkout: replace single-line fragments, or normalise `\r\n` first.

## Focused gate

From the worktree, in Git Bash, with `PATCH_DEP` applied and fixtures linked:
`sh "C:/Users/peter/Python Projects/font-kit-studio/.superpowers/sdd/r2/tools/gate.sh" focused test_r2_react test_role_adapters test_support`
Also, once (not per fix round), the fixture's production build stays clean (`npm.cmd --prefix
fixtures/vite-react-css-modules run build` in a scratch copy, then no `fontkit` or role CSS in `dist`), Ruff on
the module, and `git diff --check -- tests/test_r2_react.py` (plain `git diff --check` would also sweep
`PATCH_DEP`).

## Report and handoff

Report: per case, its oracle, its mutant and result; the `commit`, `hmr` and `deadline` stamps and gaps of three
runs of case 5; cleanup evidence for the owned host server and Vite (listener refused, reader finished); the
`PATCH_DEP` SHA-256; focused output; material lines; deviations with the rule that forced them. Handoff: your
patch, made with `git diff -- tests/test_r2_react.py` so `PATCH_DEP` stays out of it; the commit subject
`test: cover the role preview on a real React app`; a draft body (why, wrapped at 72, no process narration); and
the R2.7F2b plan items done.
