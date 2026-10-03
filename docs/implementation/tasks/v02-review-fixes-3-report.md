# v0.2.0 review fixes, round 3: duplicate bridges and stable-id selectors

## A. A second `new FontKitBridge(...)` returns the connected bridge

**Problem.** When an app called `new FontKitBridge(...)` again after the first
bridge had connected (for example on hot reload), the constructor only warned
and the new object also started. Its `design:bridge-ready` made Studio
re-handshake with both bridges. Both then answered every update and reset, and
the second one captured the first one's already-edited inline style as its
"original", so a later reset could bring the edit back.

**Change** (`fontkit-bridge.js`, top of the constructor). When a bridge already
exists on the page and is not replaceable, the constructor returns that
instance. Nothing is initialised, nothing is announced and no listeners are
added. The new options are not merged: they are ignored, with one console
warning ("A bridge already exists on this page; new FontKitBridge() returned it
and its options were ignored. ..."). The one replaceable case is unchanged: an
auto-created bridge that no Studio has talked to yet is still disposed and
replaced, so `new FontKitBridge({ allowedOrigins })` works whatever the script
order. `initFontKitBridge()` and loading the script twice behave as before.

**Tests.**
- `SpaRobustnessTests.test_a_second_constructed_bridge_after_connect_returns_the_connected_one`
  (real bridge): the same object comes back (also for a second call), the new
  options are not applied, there is still one `bridge-ready`, a re-handshake
  gets one `design:ready`, an edit gets one `design:applied`, and Reset restores
  the author's `style` attribute byte for byte.
- `DuplicateBridgeTests.test_a_second_new_fontkitbridge_after_connect_changes_nothing_for_the_studio`
  (real Studio, real bridge, demo): one reply per request, no overlay, no
  conflict banner, and after Reset the heading and the whole body markup equal
  the original.
- The existing replacement tests still pass (unconnected auto bridge is
  replaced; connected auto bridge is kept, now by returning it).

**RED.** Against the previous bridge the bridge test failed on "the constructor
returns the connected instance" and the integration test on `[False, 1] != [True, 1]`.

## B. Stable ids with CSS-special characters keep their rule

**Problem.** A bridge accepts any non-empty `data-design-id` up to 300
characters, but Studio's selector check refused a quoted value holding `;`, `{`,
`}`, `<` or `>` (for example `hero;alternate`). The acknowledged edit then
showed as a "skipped" comment in the CSS tab, Copy, Download and Sync.

**Change.**
- `fontkit-bridge.js` (`designIdSelector`, used for the target selector and for
  container selectors): inside the quotes `"` and `\` get a backslash, and every
  character that could end the string, the rule or a `<style>` element
  (`; { } < > ( ) / * !`) or is a control character is written as a CSS hex
  escape such as `\3b `. No raw special character reaches the CSS text.
- `font_kit_studio_v0.1.1.html`:
  - The quoted attribute value of the selector grammar now also accepts hex
    escapes (6 digits, or fewer when no hex digit follows, then the one space that
    ends it). The space is consumed or must be absent, so the pattern still
    matches each text in one way and stays linear.
  - `designIdSelector` builds the same selector for the fallback used when no
    selector was reported (an id Studio only knows from saved state).
  - The selector length limit is 2000 characters (an id of 300 characters can
    need five characters per escape); declaration values keep their limit.
  - `commentText` (comment lines for each rule and the header) now also stops a
    name or id from reopening or closing the comment, and writes `<` and `>` as
    `&lt;` and `&gt;`, so the whole file can be pasted into a `<style>`
    element. (`{`, `}` and `;` inside comments are harmless there.)
- Other places that build or check a selector from an id: the CSS export, the
  JSON export (ids are keys, not selectors), the HTML tab (comment text) and the
  inspector hint (HTML-escaped) were checked. Only the CSS export and its fallback
  needed the change.

**Tests.**
- `StableIdSelectorTests` (real bridge, demo, one fresh page per id): ids
  `hero;alternate`, ``a{b}<c>"d\e`` and the break-out attempt ``x"]{} body{color:red}/*``.
  For each, the edit appears as one rule in the CSS tab and in the synced file;
  the selector holds none of `; { } < >`; `querySelectorAll(selector)` on the
  target page finds exactly that element; stripped of comments and strings the
  file holds one rule block and nothing about `body`; the file has no `<` or `>`.
- `StableSelectorEscapeTests` (bridge): seven ids including control characters,
  `url(x)!important` and non-ASCII; the reported selector has no raw special
  character, matches exactly its element, and the ledger reports the same selector.
- `StudioReviewFixTests` (fake target): hex-escaped selectors are accepted and
  reach the CSS and the synced body. Raw `{ } ; < >` inside the quotes, a raw
  break-out, and a trailing backslash after an escape are skipped. Adversarial and
  long escape runs inside the quotes are refused or accepted in under 50 ms each.

**RED.** Against the previous code the integration test failed for all three ids
(the rule never appeared; 3 errors), the bridge test failed for six of seven ids,
and the Studio selector test failed in four sub-cases.

## Observation (not changed)

While writing the sequential version of the integration test I saw a flaky
ordering effect in Studio: after an acknowledged edit Studio re-selects the
target, and a click on another element right afterwards can be overtaken by that
reply, so a typed value lands on the previous target. It did not occur with one
edit per page, which is how the final test is written. It is not caused by this
change and was not investigated further.

## Documentation text that changes (owner: README and plan)

- README, line about loading the script twice (near "Loading the script twice
  (for example on hot reload) keeps the first instance."): add that calling
  `new FontKitBridge(...)` again while a bridge exists returns that bridge and
  ignores the new options (with a console warning), so the first bridge's options
  stay in force; configure the first one through `window.FONTKIT_BRIDGE_OPTIONS`,
  `data-allowed-origins` or `data-auto-init="false"`. Replacing an auto-created
  bridge that no Studio has talked to yet still works.
- README protocol text for selectors (where `[data-design-id="…"]` is described):
  say that `"` and `\` are backslash-escaped and that `; { } < > ( ) / * !` and
  control characters are written as CSS hex escapes (`\3b `), and that Studio's CSS
  tab, Copy, Download and Sync therefore keep ids with such characters.
- Plan: the contract text "Selectors: author id → `[data-design-id="…"]`
  (quotes/backslashes escaped)" should read "quotes and backslashes
  backslash-escaped; `; { } < > ( ) / * !` and control characters as CSS hex
  escapes".

## Limits

- An author id that contains U+0000 is written as `\0 `, which CSS reads as a
  replacement character, so its persisted selector matches nothing. HTML cannot
  produce such an id from markup (only a script can set one), so it is recorded
  here and not worked around.

## Round 2

**A repeated `allowedOrigins` is no longer dropped** (`fontkit-bridge.js`,
constructor and `narrowAllowedOrigins`). A second `new FontKitBridge({ allowedOrigins })`
after a Studio has connected used to leave an open bridge open. Now:
- A list in which every origin is already allowed (an open bridge allows
  everything) is applied. A request that is not a plain narrowing is ignored as a
  whole: `"*"`, an origin that is not already allowed, a disjoint list, and a
  value that is not a string or a list. It is never intersected or partially
  applied, and it never widens.
- When a pinned Studio's origin is no longer allowed, its session ends the way
  a disallowed origin is handled: the bridge drops the session, answers nothing
  more, applies no more patches and no longer intercepts clicks. A hello from an
  allowed origin still works.
- All other options stay ignored. The single warning names both parts, for
  example `allowedOrigins narrowed to http://studio.test (was: any origin);
  ignored: enableHighlightOverlay.` or `allowedOrigins ignored (it would not
  narrow the running policy: http://studio.test)`.

**RED** (before the change): the narrowing tests failed on
`None != ['http://other.test']` and `None != ['http://studio.test', 'http://evil.test']`
(the policy stayed open), the existing duplicate test failed on
`None != ['http://studio.test']`, the widening test failed because no warning
was issued, and the subclass test showed the policy unchanged.

**GREEN** (`RepeatedConstructionTests`, bridge, plus the updated
`test_a_second_constructed_bridge_after_connect_returns_the_connected_one`, which now
reads the real policy `allowedOrigins` instead of the option):
- Narrowing an open, connected bridge to `http://other.test`: the pinned Studio's
  session ends (`sessionId` is null), its next update and hello get no reply, no
  `design:applied` is sent, and the page keeps the value it had.
- Narrowing to two origins keeps the allowed Studio's session; widening attempts
  (`['*']`, `'*'`, a larger list, a disjoint list, 5, an object, `true`) change
  nothing and warn; narrowing again to `['http://studio.test']` leaves a Studio at
  that origin able to say hello and edit; `[]` narrows to nothing and ends the
  session; a call without the option changes nothing.
- A bridge configured by `FONTKIT_BRIDGE_OPTIONS` and connected is never widened.

**Replacement rules** (same file).
- A constructed bridge that no Studio has talked to yet is now replaced by a later
  `new FontKitBridge(...)`, like an auto-created one, so hot-reload option changes
  apply (test: both earlier instances are disposed, the new options apply, only
  the latest bridge answers, and once a Studio has talked to it the bridge is kept).
  Because that new instance starts from its own options, a later call without
  `allowedOrigins` replaces an unconnected restricted bridge with an unrestricted
  one; the page author's own code decides that, and no Studio is connected.
- A disposed bridge followed by `new` becomes the new global with the new options,
  with no "already exists" warning, and answers one hello and one edit (test).
- `new` of a subclass while a connected bridge exists returns the running instance
  (documented in the bridge header). The rest of the subclass constructor runs on that
  instance, so it can change the running bridge's fields; the test records this.

**Gates** (`FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium`, Chromium only):
- `PYTHONPATH=tests python3 -m unittest tests.test_studio_live tests.test_bridge_runtime tests.test_live_integration -v`: 203 tests, OK.
- `python3 -m unittest discover -s tests -v`: 434 tests, OK.
- `python3 scripts/dev/frontend_gate.py --engines chromium --offline`: exit 0; `SUMMARY OK: 15 of 15 planned runs finished. Blocking: 7 runs, 6 passed, 0 failed, 1 skipped. Advisory: 8 runs, 0 ADVISORY lines. 140 REPORT lines, 1 SKIP lines, 0 FAIL lines`.
- `python3 scripts/verify.py --static-only`: PASS. `node --check fontkit-bridge.js`: OK.
