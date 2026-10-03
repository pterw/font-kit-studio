# v0.2.1 Task 3 review: First run, Studio

Reviewer: Leading. Brief and implementer report: `v021-task-3-brief.md`. Plan:
`docs/plans/2026-10-03-v0.2.1-fit-and-finish.md`, Task 3 and decision 4.
Scope: the uncommitted Task 3 changes to `font_kit_studio_v0.1.1.html` (the connect, status and
hint code, the Target URL field and Connect button, the head link, `switchToTargetView`'s connect
option), `demo/index.html`, the new `tests/test_studio_first_run.py`, and the four changed
assertions in `tests/test_studio_live.py` and `tests/test_live_integration.py`, in the main tree
at `0e8befa`. The same tree also holds Task 4's uncommitted changes (`.preview-scroller`,
`setDeviceWidth`, the serif fallback), which another reviewer covers.

## Verdict

### Result: Approved with fixes

Reviewer: Leading. Tree at `0e8befa` plus uncommitted work (the Studio file has since gained Task 5's
changes; line numbers below are the current ones). Chromium only (`FKS_ENGINES=chromium`); Firefox not
run. `node --check`, the full suite and `frontend_gate.py` were not run (not asked).

Gates run:
- `python scripts/verify.py --static-only`: PASS (IDs, inline JS, provenance).
- `python -m unittest tests.test_studio_first_run`: Ran 18, OK (a `TargetClosedError` "Future exception was
  never retrieved" line prints at teardown; playwright shutdown noise, not a failure).
- `python -m unittest tests.test_live_integration`: Ran 43, OK.

No code defect blocks the commit. Two fixes close real gaps in proof and in the demo-offer gate (F1, F2).
One design judgement (F3) is recommended, not required.

### (1) Brief conformance

| Item | Verdict | Evidence |
|---|---|---|
| Empty field disables Connect with visible reason; typed URL enables it | Met | Markup `disabled title="Enter your app's URL"` plus `#targetUrlHint`; `refreshConnectControl` (font_kit_studio:3585 region). `test_an_empty_field_disables_connect_with_the_reason_and_typing_enables_it` types by keystroke, checks title, hint text and visibility, and Backspace back to empty. |
| No connect to a hard-coded default | Met | `DEFAULT_TARGET_URL` removed; `connectTargetApp` returns false on empty (3623-3626). `test_nothing_connects_to_a_hard_coded_default` (Enter, then the Target tab; `src` stays null, badge Idle). The 300 ms wait proves a negative. |
| Schemeless URL refused with exact text, nothing loads | Met | `hasUrlScheme` plus the first line of `resolveTarget` (3606). I probed `[::1]:8001/x`-style and `host:port` forms by reading the regex: `host:port/...` counts as schemeless, `localhost:abc` has a scheme and gets "Invalid target URL" from `safeTargetUrl`. Test covers four probes by Connect and by Enter, and a refused URL leaves a connected target alone. Not covered: a `file:` target from a `file:` Studio (still allowed; `OpenedFromFileTests` passes). |
| No-bridge status names the origin; hint has two causes; dev-server line only for `file:` | Met | `armNoBridgeTimer` (3539-3540, `textContent`); `bridgeHintServe.hidden = location.protocol !== "file:"`. Tests: target.test, evil.test, loopback target on the dev server, and the `file:` Studio (hint contains the serve line; served Studio does not). |
| Non-loopback Studio origin with loopback target | Met | `isBlockedLoopbackReach` decides from `location` and the target origin only; shown at the no-bridge timeout, so a browser that does allow the reach still connects. Test uses studio.test and a closed localhost port (simulated; the implementer says so). |
| Demo offer prefills only on loopback http, no `?target=`, never connects | Met, with F2 | `detectDevServerSync` (5313-5316). `test_the_dev_server_offers_the_demo_and_connects_only_when_asked` asserts no request to the target port and no `src` for 500 ms, then a click connects. `NoDemoOfferTests` covers studio.test and `file:`. `test_a_target_in_the_address_wins_over_the_offer` covers `?target=`. |
| Favicon in Studio and demo, nothing fetchable | Met | Both heads carry a `data:image/svg+xml` link; `FaviconTests` parse the SVG, assert no `href=`, `src=` or `url(`, and that no `favicon` request goes out. The implementer is right that headless Chromium may never request one, so the markup assertions carry the proof. |
| Fullscreen no longer connects | Met | `switchToTargetView({ connect: false })`; mutation 1 below. |

### (2) Security (Rule 5, anti-patterns 3 and 4)

- Every new string reaches the DOM through `textContent` or a static attribute: status (`setBridgeStatus`
  sets `textContent`), the origin label (inside a template string passed to that function), the button label
  (`btnConnectTarget.textContent`), the hint (static markup; only `hidden` toggles). The `title` is set as an
  attribute value. No new `innerHTML`.
- Schemes: `javascript:` and `data:` from a hostile `/__fontkit/status` never reach the field. I probed this
  against the real Studio on a loopback dev server with the status route faked (scratch script, not in the
  repo): `javascript:...`, `data:text/html,x` and `null` leave the field empty and Connect disabled.
- Probe results for the other hostile values (Studio on loopback, status faked):
  - `http://evil.example/` and `http://localhost:1/` are placed in the field and the button reads "Connect to
    the demo". Nothing loads until the click; the click then loads it (a typed URL may be any http(s) URL, so
    this matches the typed-URL gate, but the label lies). See F2.
  - `demo/` and `//evil.example/x` are placed in the field (they pass `safeTargetUrl` because it resolves
    against `location`). The click is refused with the "Use a full URL" text. Harmless but wrong: the offer
    should not accept a value Studio would refuse.
- Recursion guard: the status of the demo URL is unaffected; `resolveTarget` still blocks Studio's own URL
  and now clears the field (the old code reset it to the default, which the Connect handler then loaded; the
  RED test shows that). `test_a_recursion_block_leaves_the_field_empty_and_connect_disabled` passes.
  `RecursionGuardTests` in the integration run passes.
- The offered URL is never posted to or loaded by anything but the user's click. `file:` returns before the
  fetch. Studio does not contact a third party.

### (3) The instance `value` accessor on `#targetAppUrl`

Behaviour (probed in Chromium against the real tree): it breaks nothing I tried. `page.fill('')` and
`page.fill(url)` update Connect (they fire `input`, which the listener also handles); keystroke typing and
Backspace work; `input_value()` reads the native getter; programmatic `.value = ""` disables Connect;
`defaultValue` does not go through the setter, but the input has no `<form>` owner (checked: `form` is null),
so form reset does not apply; `pageshow` covers history restore. The accessor is an own property that
shadows `HTMLInputElement.prototype.value`, and it delegates to the native descriptor, so reads are exact.

Judgement: a plainer design exists and I would take it. There are four assignment sites for the field:
`resolveTarget` (3613), `adoptImportedLive`'s `live.target` import (4049), the demo offer (5316) and the
initial `?target=` (5683); the first and third are in Task 3's own code and the fourth is covered by the
`connectTargetApp` call that follows. An `input` listener plus one `refreshConnectControl()` call after
each assignment (or a three-line `setTargetUrl(value)` helper) says what it does where it does it. The
accessor is hidden control flow that a maintainer will not find by grepping for `refreshConnectControl`, and
Global Rule 8 asks for flat, predictable runtime code. The implementer's reason is sound, though: line 4049
sits in a function another task owns. Since Task 5's work is now in the same tree, the controller can add
the one line at that site. If it is kept, it is correct, but add a test for the one path no test covers
today: importing a composition JSON with `live.target` into an empty field enables Connect (the other three
sites are covered). Recommendation: replace, not blocking.

### (4) `switchToTargetView({ connect: false })`

Callers (current lines): 5068, 5576 (fullscreen, the only one passing the option), 5604, 5608 (Enter),
5637 (click listener), 5685 (initial `?target=`). The click listener at 5637 passes the `MouseEvent` as
`options`; `event.connect` is `undefined`, so `options?.connect !== false` holds and it connects as before.
No other caller's behaviour changed. One visible consequence of the empty-field rule: Enter in an empty field
now shows the Target view with no frame (the connect returns false silently); this is acceptable and the
status stays Idle.

### (5) The four changed assertions (D033 precedent)

- `test_studio_live.py:315` and `:1101`: wait for `^No bridge detected$` became
  `^No bridge answered at http://target\.test within 4 s\.$`. The follow-on hint, panel and error
  assertions are unchanged. Minimum edit and stronger (it pins the origin).
- `test_live_integration.py:1672` and `:1680`: `^No bridge detected$` became `^No bridge answered at `.
  A prefix match is the minimum for a wording change; it still tells "no bridge" apart from every other badge.
- `test_studio_live.py:945` (the `status_target='javascript:...'` probe) is NOT minimal and it weakens the
  old test. It ran Studio on studio.test. The old assertion (field still equals the default) failed if
  `safeTargetUrl` let `javascript:` through. The new one asserts the field is empty, but studio.test is not
  loopback, so the new loopback gate in `detectDevServerSync` blocks the prefill before the scheme check is
  reached. Mutation 2 below confirms: removing the `safeTargetUrl(status.target)` check passes this test and
  every new test. See F1.

### (6) Test quality and mutation checks (scratch copies in the scratchpad, since deleted)

1. Fullscreen reconnect restored (`switchToTargetView({ connect: false })` replaced by `switchToTargetView()`):
   `FullscreenTests.test_fullscreen_does_not_connect_to_the_typed_url` FAILS with
   `'http://target.test/fake-target.html' is not None`. Killed.
2. Status response unvalidated (`safeTargetUrl(status.target) &&` removed): `test_c1_target_url_scheme_allow_list`,
   `NoDemoOfferTests` and `DemoOfferTests` all PASS. Survived. The mutant puts `javascript:parent.__pwned=1`
   into the field and labels Connect "Connect to the demo" (probe, loopback origin); only `resolveTarget`
   then refuses the click ("Invalid target URL"), so nothing executes. The same probe on the unmutated tree
   shows the field empty, so a test from a loopback origin would kill this mutant.

Other test-quality notes: no new fixed sleeps except short waits that prove a negative (each commented);
the typing test is keystroke-level; hostile cases exist for schemes (javascript:) and origins (evil.test), but
not yet for a hostile status from the loopback origin (F1). Real Studio against the real bridge and the real
demo is exercised by `DemoOfferTests` and `FaviconTests`. No test sends pop-out with an empty field (the new
"Enter your app's URL" branch in `popOutTarget`); nit, below.

### (7) README

Already updated in the working tree (lines 108 and 428 now carry
`No bridge answered at <origin> within 4 s.`). The README still does not say, and should, in the Studio
section: an empty Target URL keeps Connect disabled with "Enter your app's URL"; a URL needs `http://` or
`https://`; from the dev server Studio offers the demo with a "Connect to the demo" button and never
connects by itself; the hint has two causes and adds "Start the dev server" from a `file:` Studio; a Studio on
a non-loopback origin gets the "Browsers block a web page from reaching localhost" message; fullscreen no
longer connects. Quickstart line 46 (`Open:` URL carries `?target=`) is still true.

### Fixes

- **F1 (required, test).** Restore the lost proof and kill mutation 2. Add to `DemoOfferTests` in
  `tests/test_studio_first_run.py` a case that serves the real Studio from the dev server, routes
  `**/__fontkit/status` to a hostile body (`javascript:parent.__pwned=1`, `data:text/html,x`, `demo/`,
  `//evil.example/x`, `http://evil.example/`), and asserts the field stays empty, Connect stays disabled
  with the label "Connect Target", `src` stays null and `window.__pwned` is undefined. Then correct or
  annotate `tests/test_studio_live.py:945` so it no longer claims the scheme check (it now proves only the
  origin gate). Covering test: the new one; mutation 2 must fail it.
- **F2 (required, code).** Tighten the demo-offer gate at `font_kit_studio_v0.1.1.html:5313`: accept
  `status.target` only when `hasUrlScheme(status.target)`, `safeTargetUrl(...)` passes, its hostname is in
  `LOOPBACK_HOSTS`, and it is not Studio itself (`isStudioDocument`). Today any http(s) host is offered under
  the label "Connect to the demo" and a schemeless value is offered and then refused. This is the
  allow-list rule (Rule 5: URLs by scheme and host) applied to the one value that Studio did not type.
  Covering test: the F1 case with `http://evil.example/` and `demo/` (both must leave the field empty).
- **F3 (recommended, code).** Replace the `value` accessor (3593 ff.) with `refreshConnectControl()` calls at
  3613, 4049, 5316 and 5683 (or a `setTargetUrl` helper), and add the import-enables-Connect test described
  in section 3. Not blocking; if kept, add that test.
- **Nit.** Add one test that pop-out with an empty field says "Enter your app's URL" and opens nothing.
  Add the README lines listed in section 7.

Cleanup: the scratch copies and the probe script's runs left no edits in the tree; the probe script was deleted after use;
`git status` shows no files from this review other than this one. I started no long-running
processes; every dev server was started and stopped by the test harness.


## Re-review

Reviewer: Leading. Scoped to fixes F1, F2, F3 and the nit. Tree at `af7ec76` plus uncommitted Tasks 3, 4, 5.
Chromium only. Run: `tests.test_studio_first_run` Ran 22, OK; `tests.test_studio_live -k no_bridge -k c1_
-k fullscreen -k pop_out -k recursion -k theater -k import` Ran 20, OK.

### Result: Approved

Two small follow-ups for the commit (neither changes a verdict): one README sentence is inaccurate, and one
probe string should join the hostile list. Both are below.

### (1) F2: `isOfferableDemo` (font_kit_studio:3592-3596, used at 5315)

- The function requires a string, `hasUrlScheme`, `safeTargetUrl`, a hostname in `LOOPBACK_HOSTS`, and not
  `isStudioDocument`. `detectDevServerSync` calls it and nowhere else decides the offer. The old probes now give:
  `http://evil.example/` and `demo/` are not offered (field empty, "Connect Target", Connect disabled), covered
  by `test_a_hostile_status_target_is_never_offered` (nine probes, including `//evil.example/x`, an `https` host
  on the studio port, Studio's own URL and its `127.0.0.1` and `?x=1` aliases). The control test offers the real
  demo and its `127.0.0.1` alias and loads nothing.
- Mutation "both checks gone" (keep `hasUrlScheme` and `isStudioDocument`; drop `safeTargetUrl` and the host
  check): the hostile test FAILS (`failures=4` subtests, including the `javascript:` and `data:` probes). The
  scheme probes still bite. Killed.
- Mutation "remove `safeTargetUrl`" (replaced by a plain `new URL(raw, location.href)`): the hostile test
  passes, as Kerning reports. Kerning's reason is half right. `javascript:` and `data:` have an empty hostname,
  so the host check rejects them. It is NOT an equivalent mutant: I probed the mutant on a loopback Studio with
  a hostile status of `ftp://localhost:<port>/x` and `ws://localhost:<port>/`; both are placed in the field
  under "Connect to the demo". The real tree rejects both (field empty). `safeTargetUrl` therefore does real
  work, and the test does not prove it. Harmless today (a click is refused by `resolveTarget` with "Invalid
  target URL"), but add one probe, `f'ftp://localhost:{port}/x'`, to the hostile list so the scheme allow-list
  is actually pinned. Not blocking.
- `http://localhost:1/` left out of the hostile list: accepted. A loopback host on any port is a legitimate
  target (a typed URL may use any port), the value stays on this machine, and the user must still click.

### (2) F1: the hostile-status test

Met. It runs from a real loopback Studio served by `serve.py`, routes `/__fontkit/status`, and asserts the
field is empty, the button disabled with label "Connect Target", `src` null, `window.__pwned` undefined and
no page errors, per probe and per engine. The control test proves the route works and a loopback demo is
accepted, so the hostile cases are not passing for lack of a working route.

### (3) F3: the accessor

- `grep defineProperty` returns one line, 3196: `Object.defineProperty(obj, key, { value, enumerable:true,
  writable:true, configurable:true })`, a data-property helper for plain objects, unrelated to the input field.
  The accessor block and `nativeValue` are gone (3598-3603 keeps only the `input` and `pageshow` listeners and
  one initial refresh).
- Refresh calls follow each assignment of the field: 3615 (`resolveTarget`, recursion clear), 4051
  (`adoptImportedLive`), 5319 (the demo offer) and 5687 (the `?target=` init block); 3635 in `connectTargetApp`
  was already there.
- `adoptImportedLive`: Kerning's change is the one line at 4051 (the same statement wrapped in braces plus
  `refreshConnectControl();`). The other differences in that function (`wasLinked` parameter, the
  `reconcileImportedLinked` branch) are Task 5's own edits, not Kerning's; nothing else there is Kerning's.
- `test_importing_a_composition_with_a_live_target_enables_connect` exists and asserts field, enabled button,
  hidden hint and no load. As Kerning says, it passes with either design; with the accessor gone it now
  genuinely depends on the explicit call at 4051.

### (4) The comment at `tests/test_studio_live.py:941-943`

Accurate. Studio runs on studio.test, so that case proves the origin gate; the comment says so and points to
`test_studio_first_run.DemoOfferTests` for the scheme and host checks. The assertion line is unchanged.

### (5) The nit

`test_pop_out_with_an_empty_field_asks_for_a_url_and_opens_nothing` exists: status "Enter your app's URL",
`window.open` is never called (wrapped counter), no new page, placeholder hidden. The 300 ms wait proves a
negative.

### README lines (checked against the code)

Accurate: the empty box and disabled Connect; the `http://` or `https://` requirement; the demo prefill and
"Connect to the demo" without connecting; the 4 s no-bridge badge with both causes and the disk-only
dev-server line; fullscreen no longer connecting.

One sentence is wrong: "A Studio hosted on the web cannot reach `localhost` in Chromium; Studio says so
instead of waiting." Studio does not decide in advance. It waits the full 4 s and shows the "Browsers block a
web page from reaching localhost" message only when no bridge answered from a non-loopback Studio origin to a
loopback target; a browser that does allow the reach connects normally. Suggested wording: "If Studio is
hosted on the web and your app is on `localhost`, Chromium may block the reach; after 4 seconds with no
answer, Studio says so. Open Studio from the dev server or from the file on disk instead."

### Follow-ups for the commit (non-blocking)

1. README: reword the sentence above (anti-pattern 11).
2. `tests/test_studio_first_run.py` hostile list: add `f'ftp://localhost:{port}/x'` (kills the "remove
   `safeTargetUrl`" mutant).

Cleanup: the scratch copies and the probe were in the scratchpad and are deleted; the main tree was not edited.
