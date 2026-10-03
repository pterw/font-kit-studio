# v0.2.1 Task 3 brief: First run, Studio

Plan: `docs/plans/2026-10-03-v0.2.1-fit-and-finish.md`, Task 3 and decision 4. Base: `3083e4d`
on `ccr-9eab25c9-mgatzt`. Implementer role: Kerning (Studio).

## Problems (audit, `docs/implementation/audit-2026-10-03-first-run-and-controls.md`)

1. The no-bridge hint (`#bridgeHint`, html:1003; set at 3491 after `NO_BRIDGE_MS`) blames the
   bridge even when nothing is listening at the URL.
2. An empty Target URL (`#targetAppUrl`, 981) connects to `DEFAULT_TARGET_URL` (3064) and logs a
   postMessage origin error; a URL without a scheme is resolved relative to Studio (`resolveTarget`,
   3509).
3. Studio served by the dev server with no `?target=` does not offer the demo.
4. Fullscreen (`toggleFullscreenTheater`, 5437) connects to the target as a side effect. Verify
   this first; if it does, remove only that call from the function (Task 1 owns the rest of it and
   is committed).
5. Studio and the demo have no favicon, so a headed browser logs a 404.
6. A Studio whose own origin is neither loopback nor `file:` cannot reach a loopback target in
   Chromium and says nothing.

## Required behaviour

- Empty URL: `#btnConnectTarget` is disabled with the visible reason "Enter your app's URL" (title
  and an adjacent hint); typing a URL enables it. No connect to a hard-coded default ever.
- A URL without `http://` or `https://` is refused with the status "Use a full URL starting with
  http:// or https://" and nothing is loaded. (`file:` stays allowed only when Studio itself is
  `file:`, as today.)
- No bridge after `NO_BRIDGE_MS`: the status reads "No bridge answered at <origin> within 4 s." and
  the hint reads "Either nothing is running there, or the page does not load fontkit-bridge.js.
  Add <script src=\"fontkit-bridge.js\"> after the page's own scripts, reload it, then press
  Connect Target." When Studio is a `file:` page the hint adds "Start the dev server: python
  scripts/serve.py". The origin is the target's origin, text-only (`textContent`).
- Studio served over http(s) from a non-loopback origin with a loopback target: the status says
  browsers block a web page from reaching localhost and to open Studio from the dev server or from
  disk instead. Decide this from `location` and the target origin only.
- Demo offer (decision 4): when Studio is served over http from a loopback origin and has no
  `?target=`, read `/__fontkit/status` (same origin; already fetched for Sync near 5165) and, when
  it answers, prefill `#targetAppUrl` with the demo URL it names and set the Connect button's
  label to "Connect to the demo". Never connect by itself. From `file:` or any other origin,
  prefill nothing; the field starts empty.
- Favicon: an inline SVG `data:` favicon `<link>` in Studio's head and in `demo/index.html`. No
  external request.
- Fullscreen no longer connects (if it did).

## Tests: new module `tests/test_studio_first_run.py`

Fake-target tests (subclass `LiveCase`): empty URL disables Connect with the reason, typing
enables it (keystroke-level); a schemeless URL is refused with the status text and the iframe
`src` is unchanged; a URL whose page has no bridge shows the new status and hint text with the
right origin; from a `file:` Studio the dev-server line appears; the non-loopback-origin case via
`route_virtual_origins` (Studio on `studio.test`, target `http://localhost:<port>`); fullscreen
sends no `design:hello`. Dev-server tests (subclass `LiveIntegrationCase`): Studio opened from the
server without `?target=` shows the demo URL prefilled and "Connect to the demo", no hello is sent
until the button is pressed, and pressing it connects; Studio and demo responses include the
favicon link and no request for `favicon.ico` is made (or, if the browser still requests it,
assert the response is not a 404 by serving it: say which).

## Owned files

`font_kit_studio_v0.1.1.html`: `resolveTarget`, `connectTargetApp`, `setBridgeStatus`, the
no-bridge timer, the `#targetAppUrl`/`#btnConnectTarget` markup and listeners (981-982,
5470-5475), `#bridgeHint`, `DEFAULT_TARGET_URL`, the status fetch near 5165, the head `<link>`,
and the one connect call in `toggleFullscreenTheater` if present. `demo/index.html` (favicon
link only). `tests/test_studio_first_run.py` (new). Nothing else.

## Environment and gates

```
export PYTHONPATH=tests FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium
python scripts/verify.py --static-only
python -m unittest tests.test_studio_first_run          # only your module; two other agents share the CPUs
```

Never run `playwright install`. Stop only processes you started, by PID. No `sleep` polling.
Do not commit or push. First command: `git rev-parse HEAD`; if it is not the base above or
newer, run `git fetch origin ccr-9eab25c9-mgatzt && git merge --ff-only origin/ccr-9eab25c9-mgatzt`
before editing. Two other implementers edit other functions of the Studio file in their own
worktrees at the same time: stay inside your named functions and CSS blocks, add new code next
to them rather than at the end of the script, and never reformat or move code you do not own.
Tests go in your own new module (subclass `LiveCase` from `test_studio_live` or
`LiveIntegrationCase` from `test_live_integration` for fixtures; with `PYTHONPATH=tests` they
import as top-level modules). Test-first: write the tests, capture the failure text (RED), make
the smallest fix, run your module (GREEN). Behaviour that already works is characterized, never
made RED.

## Report

Append under this heading in this file: RED evidence (test names and failure text), the fix
(functions and lines), GREEN evidence (your module count), what you did not verify.

## Report

Implementer: Kerning. Base fast-forwarded from a6d2751 to 0e8befa before any edit. Chromium only
(`FKS_ENGINES=chromium`); Firefox not run.

### RED (new module against the unmodified Studio, 18 tests: 9 FAIL, 6 ERROR, 3 passing)

- Empty field / typing: `test_an_empty_field_disables_connect_with_the_reason_and_typing_enables_it`:
  `'http://localhost:8001/demo/' != ''`. `test_nothing_connects_to_a_hard_coded_default`: iframe
  `src` was `'http://localhost:8001/demo/'`.
- Schemeless: `test_a_url_without_a_scheme_is_refused_and_nothing_loads`:
  `'Invalid target URL' != 'Use a full URL starting with http:// or https://'`.
- Recursion block: `test_a_recursion_block_leaves_the_field_empty_and_connect_disabled`:
  `'Connecting…' != 'Recursion blocked'`. Cause: the guard reset the field to the default, then the
  Connect handler's `switchToTargetView()` connected to it.
- No bridge: four tests time out waiting for `No bridge answered at <origin> within 4 s.` (target.test,
  evil.test, `file:` Studio, loopback target on the dev server); the localhost-block test times out on
  the new status.
- Fullscreen: `test_fullscreen_does_not_connect_to_the_typed_url`: `'http://target.test/fake-target.html' is not None`.
  Verified: the fullscreen toggle does connect, through `switchToTargetView()` (it loads the URL in the
  field when the iframe has no `src`).
- Demo offer: `'Connect Target' != 'Connect to the demo'` (two tests); `test_nothing_is_prefilled_from_a_file_or_another_origin`:
  `'http://localhost:8001/demo/' != ''`.
- Favicon: `no inline SVG <link rel="icon">`; `document.querySelector("link[rel~=icon]")` is null.
- Characterized, passing at once: `test_other_schemes_keep_their_own_refusal`, `test_the_target_tab_still_connects_when_pressed`,
  `test_a_target_in_the_address_wins_over_the_offer`.

### Fix

`font_kit_studio_v0.1.1.html`:
- Head: inline SVG `data:` favicon `<link>` (no external request). `demo/index.html`: same, orange "H".
- Markup: `#targetAppUrl` starts empty; `#btnConnectTarget` starts `disabled` with title "Enter your app's URL";
  new `#targetUrlHint` (adjacent visible reason); `#bridgeHint` carries the new two-cause text plus a hidden
  `#bridgeHintServe` span ("Start the dev server: python scripts/serve.py", shown only when Studio is `file:`).
- `DEFAULT_TARGET_URL` removed. New block "first run: the Target URL field" right before `resolveTarget`:
  `hasUrlScheme`, `isBlockedLoopbackReach`, `targetOriginLabel`, `refreshConnectControl`, `offeredDemoUrl`,
  `BLOCKED_LOOPBACK_TEXT`, and an instance `value` accessor on `#targetAppUrl` so code that sets the field
  (import `adoptImportedLive`, the recursion guard, the demo offer) keeps Connect in step without touching
  the other tasks' functions.
- `resolveTarget`: schemeless input (incl. `host:port/...`, `//host`, relative) gets "Use a full URL starting with
  http:// or https://"; other schemes keep "Invalid target URL" and the `safeTargetUrl` gate. Recursion block
  now clears the field instead of resetting to a default.
- `connectTargetApp`: empty input returns false (no connect); calls `refreshConnectControl()` after connecting.
  `popOutTarget`: empty input says "Enter your app's URL"; no default fallback.
- `armNoBridgeTimer`: status "No bridge answered at <origin> within 4 s." (`textContent`; `file:` targets show
  the URL), hint on. When Studio is http(s) from a non-loopback origin and the target is loopback, the status is
  the "Browsers block a web page from reaching localhost..." text instead (no hint; decided from `location` and
  the target origin only). It is shown when the bridge does not answer, so a browser that does allow the reach
  still connects.
- `detectDevServerSync`: prefills the status `target` only when Studio is on a loopback host, no `?target=`, no
  `live.url`, and the field is empty; the button label becomes "Connect to the demo" while the field holds that
  address. Never connects. `file:` returns earlier, so nothing is offered there.
- `toggleFullscreenTheater` calls `switchToTargetView({ connect: false })`; `switchToTargetView(options)` skips the
  connect only for that flag (a one-line signature change in a function outside the named list, because the connect
  call lives there, not in the fullscreen function).

Existing tests updated because their asserted text or default changed (outside my new module, minimal edits):
`tests/test_studio_live.py` (two `^No bridge detected$` waits now expect the new status; the `status_target`
javascript: probe expects an empty field instead of the old default) and `tests/test_live_integration.py`
(two `No bridge detected` waits now `^No bridge answered at `).

### GREEN

- `python -m unittest tests.test_studio_first_run`: Ran 18, OK (chromium). A `TargetClosedError` "Task was destroyed"
  line prints at interpreter teardown; it is playwright shutdown noise, not a failure.
- `python scripts/verify.py --static-only`: PASS (unique IDs, inline JS, provenance).
- Existing tests touched by the change, run by name: test_studio_live `-k no_bridge/c1_/fullscreen/pop_out/recursion/theater`
  (9 tests, OK); test_live_integration `BookmarkletTests`, `RecursionGuardTests`, `PopOutTests`, `OpenedFromFileTests` (5, OK).

### Not verified / for the controller

- Full suite, `frontend_gate.py`, Firefox, phone profiles and `node --check` were not run (told to run only my module).
  The gate's network-isolation and contrast checks should be re-run: Studio and the demo gained a `data:` icon link.
- Headless Chromium may never request a favicon, so "no `favicon.ico` request" cannot prove much; the tests assert
  the inline `<link rel="icon">` in the served Studio and demo HTML (well-formed SVG, nothing fetchable) and in the
  loaded DOM. No `favicon.ico` route was added.
- The real-browser block of loopback from a non-loopback origin is simulated: studio.test with a closed localhost port.
  Chromium's actual behaviour (blocked or permission-prompted) was not observed.
- Stale docs outside my files: `README.md` lines 108 and 428 still say the badge shows `No bridge detected` (now
  "No bridge answered at <origin> within 4 s."). Fix in the commit (AGENTS.md anti-pattern 11). Lines mentioning the
  Target field prefill, if any, were not found.
- The plan lists `tests/test_studio_live.py` and `tests/test_live_integration.py` as Task 3 files; the brief says
  my own module only. I edited four assertions in them (above); a merge with Tasks 4 and 5 should be trivial.

## Fix round 1

Review: `v021-task-3-review.md` (Approved with fixes). The worktree first received Task 4 and Task 5 (`git apply
--3way`, no conflicts, markers grepped: none). Chromium only.

### F1 (test) and F2 (code)

RED, new `DemoOfferTests.test_a_hostile_status_target_is_never_offered` (Studio served by the real dev server,
`/__fontkit/status` routed to a hostile body, loopback origin) against the code before F2: 7 of 9 probes FAIL with
`'<probe>' != ''` for `demo/`, `//evil.example/x`, `http://evil.example/`, `https://evil.example:8001/demo/`,
`http://127.0.0.1:<studio port>/font_kit_studio_v0.1.1.html`, the same on `localhost` with `?x=1`, and Studio's own
URL. `javascript:` and `data:` already passed (the `safeTargetUrl` check was there), which the old tests could not show
because they ran on studio.test.

Fix: new `isOfferableDemo(raw)` next to `refreshConnectControl`: a string with `hasUrlScheme`, passing `safeTargetUrl`,
with a hostname in `LOOPBACK_HOSTS`, and not `isStudioDocument`. `detectDevServerSync` offers the demo only through it.
The probe asserts: field empty, Connect disabled with label "Connect Target", iframe `src` null, `window.__pwned`
undefined, no page errors. Control `test_a_status_target_on_the_loopback_is_offered`: the real demo URL and its
`127.0.0.1` alias are offered with "Connect to the demo" and nothing loads. Rule: any loopback port is accepted (the
dev server names the demo's own port; a typed loopback URL on any port is equally allowed), so `http://localhost:1/` is not
in the hostile list.

Mutation results (scratch edits to the Studio file, restored from a saved copy; `git diff` clean of them):
- `isOfferableDemo` reduced to `typeof raw === "string"`: the hostile test FAILS 9 of 9 probes. Killed.
- The review's mutation (the `safeTargetUrl` check replaced by a plain `new URL`): the test still passes. This is now an
  equivalent mutant: `javascript:` and `data:` resolve to a non-loopback (empty) hostname, which the host check rejects.
  The scheme probes stay in the test, so removing the host check as well fails them.

`tests/test_studio_live.py` test_c1: annotated that the studio.test case proves the origin gate, and points to the loopback
cases here (assertion line unchanged).

### F3 (code)

Removed the instance `value` accessor on `#targetAppUrl` (the `Object.defineProperty` block and `nativeValue`). Kept the
`input` and `pageshow` listeners. Explicit `refreshConnectControl()` calls now follow each assignment of the field:
`resolveTarget` (recursion clear), `adoptImportedLive` (the import adoption; the one line inside Task 5's function,
the braces plus this one call), `detectDevServerSync` (the demo offer), and the `?target=` init block. Test added:
`test_importing_a_composition_with_a_live_target_enables_connect` (field gets the target, Connect enabled, hint hidden,
nothing loads). It passed before and after the change (it characterizes the accessor and now the explicit call).

### Nit

`test_pop_out_with_an_empty_field_asks_for_a_url_and_opens_nothing`: status "Enter your app's URL", `window.open`
never called, no new page. README lines from review section 7 were not added (README is not an owned file).

### GREEN

- `python -m unittest tests.test_studio_first_run`: Ran 22, OK (chromium).
- `python scripts/verify.py --static-only`: PASS.
- `tests.test_studio_live -k no_bridge -k c1_ -k fullscreen -k pop_out -k recursion -k theater -k import`: Ran 20, OK.
