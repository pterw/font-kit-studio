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
