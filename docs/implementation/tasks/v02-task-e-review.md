# v0.2.0 Task E review: bridge arrangement, pop-out overlay, font stylesheets, framework robustness

Reviewer: independent, read-only. Task E uncommitted, on top of the Task C change. Scope: `fontkit-bridge.js`, `tests/test_bridge_runtime.py`, `tests/fixtures/bridge/**`, `docs/implementation/tasks/v02-task-e-report.md`. Task F files were not reviewed. I changed no repository file except this report. Every claim below is from direct source and runtime probes.

Commands run:

- `cd tests && FKS_ENGINES=chromium FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium python3 -m unittest test_bridge_runtime test_preview_server -v`: `Ran 88 tests in 71.062s, OK`.
- `node --check fontkit-bridge.js`: OK.
- Probes (throwaway, outside the repo) as scratch files: `demo*.py`, `move*.py`, `overlay*.py`, `fonts.py`, `spa*.py`, `r1.py`, `r2.py`, `m7.py`, `m8.py`, `scale*.py`. The HEAD bridge (`git show HEAD:fontkit-bridge.js`) was served as a baseline.

## Spec Compliance

- ✅ Move `to` forms: `{index}`, `{before}`, `{after}`, `{container, index?}` all apply and report `canonicalPatch.move` as final `{container, index}` (`fontkit-bridge.js:1118-1215`). The 20 invalid shapes behave as specified:
  - Malformed `to`: `invalid-message` with `detail.field` (`to`, `to.index`, `to.container`, ...).
  - Out-of-range index, unknown container, self, descendant, void or replaced container (`img`, `svg`), `relative-to-self`: `unsupported-value` with `detail.reason`.
  - Unknown target or unknown `before` id: `unknown-target`.
  - Revision conflict: `revision-conflict`.
  - `strategy` or `force` of the wrong type: `invalid-message`.
- ✅ Guards (`:1267-1358`):
  - Form owner: `input` and `button` out of a form are rejected. Moving within the same form and moving a non-control out of a form are allowed.
  - Radio group: a radio, or its wrapping label, leaving the fieldset is rejected. Reordering inside the group is allowed.
  - Implicit label: an input leaving its `<label>` gives `label-reference`.
  - Framework: `framework-managed` (`overridable: true`, `framework: "react"`). `force: true` passes it, and does not override `form-owner`.
  - `label[for]` and aria moves are allowed in the same root.
- ⚠️ The root-scoped `getRootNode` label/aria branch (`:1327-1357`) is unreachable and untested, as the report discloses. Same-document id references cannot break by a move, and I confirmed they are not wrongly rejected.
- ✅ css-order (`:1160-1177`, `applyCssOrder`):
  - It requires a flex or grid parent and the same container; otherwise it is rejected with `guard: "css-order"`.
  - The DOM is untouched. I checked the visual order `2 3 1` while the DOM order stayed `s1 s2 s3`.
  - Every sibling gets an `order` declaration in the ledger and `structure` stays empty.
  - Resetting one member clears the group, and reset-all clears it too.
- ✅ Byte-exact reset. I compared `documentElement.outerHTML` before and after:
  - `move.html`: mixed moves, a nested move, css-order, then reset-all. Identical.
  - Round trip back to the original position without a reset: identical, and `structure` empty.
  - A no-op move: `structure` empty.
  - Reset-all after the app removed the destination container: the original order is restored.
  - Real demo: a move plus text, style and weight overrides, then single-target resets of three targets. Identical.
  - Real demo: a cross-container move, then single reset. Identical.
  - Real demo: moves, then reset-all. Identical.
  - The report's caveat that a single reset may leave whitespace nodes was not reproducible in any of these.
- ✅ `structure` html is cleaned. In the demo, the auto-registered sibling `a.btn-ghost` carries no `data-design-*`, no `style` override and no `order`. Author `style="color: red"` is preserved. Author `data-design-*` attributes are correctly kept. The page-level overlay nodes are never present: a popup session with the overlay on and a `body` structure entry has no `id="fontkit-bridge…"`.
- ✅ Overlay (`:552-575`):
  - It appears on `overlay:true` with `pointer-events:none` for both nodes.
  - It is removed on `overlay:false`.
  - It is removed on a new `design:hello`.
  - It is removed about 0.5 s after the opener page closes. The popup also stops intercepting clicks (`#pricing` link worked).
  - It never appears in ledger or structure html.
- ✅ Font stylesheets: 40 hostile inputs probed. These were rejected:
  - `https://fonts.googleapis.com.evil.test/…`, `…com@evil.test/…`, `//fonts.googleapis.com/…`.
  - `…&callback=`, raw newline, trailing newline, `javascript:`, `HTTPS://`, `FONTS.googleapis.com`.
  - `/css?`, `#frag`, `:443`, `&&`, empty `family=`, duplicate `display`, `display=evil`, `"onload="`, spaces, `/../`.
  - Typekit with query, trailing newline, extra path, `.evil` host, `http`, 3 or 11 characters.
  - `data:`, non-strings, 2100-character values, 9 families, `text=` over 600 characters.
  - Also verified:
    - Dedupe: two targets with the same URL give one `<link>`.
    - Release: `null` on one target keeps the link, and `null` on the last target removes it.
    - Replacing the URL on a target drops the old link.
    - Reset-all clears links and `imports`.
    - An invalid sibling key in the same patch leaves the links untouched (atomic).
    - A link the app removed is re-added on the next set.
    - Only the percent-escape cases in M2 were accepted.
- ✅ SPA re-apply. The style-triggered re-render case (an app that re-renders whenever a style changes) is bounded: 7 renders in total over 12 s, then quiet, with one `console.warn`. With no Studio-side change, a second update re-applies normally. Wholesale `innerHTML` re-render without a loop restyles. `childList`-observing apps are unaffected. See M3 for the one pattern that is not bounded.
- ✅ R1: a constructed instance replaces an unconnected auto instance. With `allowedOrigins:[nobody]` the studio hello is ignored; with `allowedOrigins:[studio]` exactly one `design:ready` arrives. A connected auto instance is not replaced and gives the documented warning.
- ⚠️ R2: base64 and long `data:image/…;base64` URLs in `src`, `srcset` and `url()` are abbreviated. A long un-base64 SVG data URL containing raw spaces is not (M1).
- ✅ M7/R3: a legacy `layout.order` update is recorded in `structure`. `transition` and `order` do not leak into the html. A second layout call updates the entry. Reset-all restores the original bytes. Single reset puts the element back.
- ✅ M8: a 1846-node random deep DOM (identical branches, duplicate ids, `id="a:b"`, Tailwind-style classes `md:flex`, `w-[100px]`, `a\b`, `x.y`, SVG children, 718 targets) gave 0 non-unique or invalid auto selectors. After a DOM mutation and after a class toggle the selectors stayed unique (cache invalidation works).
- ✅ Real-app run (`demo/index.html` at `http://target.test`, repo root):
  - Standalone before hello: nav link works.
  - Interact mode: nav link, FAQ `<summary>` toggle and button clicks work; no bridge messages are sent while interacting.
  - After a DOM move the nav link still works.
  - Select mode: a nav-link click selects it and does not navigate.
  - Only console error: a 404 (the gitignored `fontkit-overrides.css`), unrelated to Task E.
- ⚠️ Contract: `siblings: []` in bulk manifests above 100 siblings, and per-target repeated `containers`. See Interpretation opinions and Important 1.
- ✅ Inert before hello, double-load keeps one instance, and `design:warning` windows are covered by tests that pass. I did not re-derive `design:warning` independently beyond reading `watchRuntimeErrors` and `noteRuntimeError` (`:896-915`).

## Strengths

- Tests came first with real RED evidence. They are honest about the four that were already green, and the report lists the two temporary-revert RED checks. 37 new tests across 11 classes pass; the full 88-test run is green.
- The guards are layered correctly: hard guards run before the framework guard, and `force` can override only the framework guard (`:1267-1307`).
- The original-order machinery is correct under messy conditions: round trips, no-op moves, app-added children, an app-removed destination, and reset of single or all targets. Whitespace nodes come back exactly (`pruneOrderState`, `restoreNodeOrder`).
- Loop-guarded re-apply (5 per 2 s) and the old-element ledger copy are simple and bounded.
- `dispose()` is complete (listeners, observers, timers, overlay), and the R1 replacement is clean.
- Font URL validation uses strict string prefix matching rather than `new URL()`, so there is no normalization surprise.
- The selector uniqueness check (`querySelectorAll === [el]`, extended up to `body`) plus a version-keyed cache is a good M8 fix.

## Issues

### Critical

None.

### Important

**I1. `arrangement.containers` is repeated in every target of every bulk manifest, so message size and cost grow quadratically.**

- Where: `fontkit-bridge.js:2319` (`containers: context.containers.filter(...)`), reached via `getTargetManifest` (`:2162`), `design:ready`, and the `design:targets` post at `:2078`. `BULK_SIBLINGS_MAX` (`:82`, `:2305`) only caps `siblings`.
- Verified failure scenario:
  - Probe page of 1846 DOM nodes (718 targets, 249 candidate containers each). `design:ready` took 790 ms in-page and 8.36 MB (HEAD: 58 ms and 288 KB). `containers` was 8.36 MB of the 8.7 MB of arrangement data; `siblings` was only 126 KB.
  - A ticker adding one `button` to a section every 500 ms for 3.2 s produced 5 `design:targets` posts of about 8.4 MB each, because every rediscovery that changes targets re-posts the whole manifest.
  - On the demo (46 targets, 15 containers each) it is fine: 88.7 KB (arrangement 57.9 KB, 65%), 20 ms in-page. The risk is ordinary content pages (blogs, docs, dashboards of 2000 nodes), which the zero-hook goal targets.
- Fix: treat `containers` like `siblings` in bulk manifests: omit it when `context.bulk` (keep it on `design:selected`, `design:applied`, `design:inspect-result`, which is all the Arrange UI reads). Alternatively send one top-level `containers` list in `design:ready` and `design:targets`. Either is a contract change, so the plan's Addendum 1 text must change first (rule 3 in `docs/agents/global-rules.md`). Also add a test that `design:ready` size stays near-linear (for example, a 700-target fixture stays under a few hundred KB), the same way the existing `test_bulk_manifests_leave_out_the_sibling_list_of_very_large_groups` pins the sibling cap.

### Minor

**M1. R2 abbreviation misses data URLs that contain spaces or quotes.**

- `DATA_URL_IN_ATTRIBUTE` (`:117`) stops at whitespace, `"`, `'` and `)`.
- Scenario: `<img src="data:image/svg+xml,%3Csvg xmlns='…' …">` with a 1.5 KB payload is returned in full in the ledger html (the first token `data:image/svg+xml,%3Csvg` is under 256, so it is kept). Verified in the r2 probe.
- Fix: for an attribute whose value starts with `data:` (and `src`/`href`/`poster`), abbreviate the whole value when it is longer than 256. For `srcset`, split on commas before a descriptor.

**M2. `fontStylesheet` accepts percent-escaped control and markup bytes.**

- `GOOGLE_FONTS_VALUE` (`:120`) allows any `%XX`. `…family=x%0a&display=swap`, `…text=%3Cscript%3E`, `…text=%0a` and `…family=x%2F..%2F` were accepted and requested (they all stay inside `https://fonts.googleapis.com/css2?`, so this is not an injection).
- The contract says "safe characters". Tighten to a short allow-list (`%20`, `%2B`, `%3A`, `%3B`, `%2C`, `%40`) or reject `%00-%1F`, `%22`, `%27`, `%3C`, `%3E`, `%2F`, `%5C`.

**M3. An app that re-renders on any attribute mutation keeps the bridge in an unbounded loop. It is pre-existing, but sibling registration widens it.**

- The loop guard (`reapplyFrom`, `:1954`) only covers stable (author-id) targets that carry overrides. Auto targets get `data-design-id/role/name` written by the bridge itself (`:1871-1874`); an app whose `MutationObserver` observes all attributes of its subtree re-renders, the bridge re-registers, writes attributes, and the app re-renders again.
- Verified (`spa.html?mode=anyattr`): 34 renders in 3 s and still running; HEAD showed 29. The `style`-only variant is correctly bounded (7 renders, then idle).
- Fix, if worth it: do not write bridge attributes onto auto targets (keep the id map in a `WeakMap`), or back off discovery after N consecutive attribute-only mutations that the bridge's own writes caused.

**M4. Arbitrary HTML content-model breaks are not guarded.**

- Disclosed by the report. Verified: `{"container":"a"}` where `a` is a `<p>` moved a `<p>` into a `<p>`; the bridge applied it and serialized `<p>A<p>B</p></p>`.
- Rule 6 asks for guards only on form, radio, label/aria and framework, so this is not a spec miss. A cheap hint would still help: block `p` children that are block elements, `li` outside `ul`/`ol`, `tr` outside `table`/`tbody`, and `option` outside `select`/`datalist`.

**M5. Container names in `arrangement.containers` are often uninformative.**

- Examples from the demo: `div.wrap`, `div`, `div.section-head`. The Move into list in the Arrange UI will show several identical-looking entries.
- Fix: include the selector tail or a text hint when two names collide (for example, `div.wrap (Halyard, Features, Pricing)`).

**M6. The report names a stale base** (an older commit than the current branch tip). The report also lists several contract interpretations (siblings omission, `containers`, imports reference counting) that need entries in `docs/implementation/deviations.md`.

## Interpretation opinions

**"Every sibling of a target is registered, so containers become hover/click-selectable."**

- This is the literal reading of Addendum 1 ("each is registered (auto if needed) so it has an id"). Registration is needed anyway so the Studio can list and move siblings by id. The compliance reading is correct.
- Measured effect on the demo:
  - 34 targets before, 46 after: 12 new selectables.
  - Of 1424 sampled viewport points that resolve to any target, 349 (24%) resolve to a sibling-only target: 155 `ul` via a `li` hit, 130 `summary`, and the rest `.actions` (CTA row), `.icon` and `nav`.
  - Real mouse-click table over 24 typical spots (title, lead, CTA, card h3/p, plan button, nav, brand, footer): 7 changed, 17 identical, and none got worse.
  - Padding of the hero card, feature card and plan card still selects nothing (those wrappers are not siblings of a target).
  - Wrappers never beat a text target: `closestTarget` (`:2115`) walks innermost-first. They only claim gaps and non-target descendants that previously fell through to the app.
  - The two surprises:
    - A click on a `li` selects the whole `ul` rather than that line.
    - FAQ `<summary>` is now selected rather than toggled in Select mode, so a user must switch to Interact to open an answer.
- Verdict: not noisy on the demo and acceptable as is. The risk is pages where targets are direct children of a large container (a blog `main > h1, p, section, aside`), because every big block becomes hoverable and a gap or padding click selects the whole block. A concrete low-risk rule:
  1. Keep eager registration, but add `arrangementOnly: true` to records that were created only as siblings (not author, not `[data-design-role]`, not semantic) in the manifest, so the Studio can draw them differently and label them as groups.
  2. In `closestTarget`, let an arrangement-only record win only when the hit is the element itself (its own padding or gap) or the element has its own non-whitespace text (`summary`, a text-bearing `div.icon`). Otherwise continue to the next ancestor record, and fall back to null as in HEAD. Siblings stay selectable from the Studio sibling list through `design:select`.
  3. Suppress the hover outline (not click selection) of an arrangement-only record that covers more than about 60% of the viewport.
- I would not make this a blocker; it is a Task F/D follow-up once Studio draws the group outline.

**`siblings: []` above 100.**

- Reasonable and clearly disclosed. `count` and `index` stay correct, so Studio can tell the list was omitted. The plan states the contract must change first, so record it as a deviation and amend the plan text.
- The cap targets the wrong dominant cost, though: siblings were 126 KB in the stress page and `containers` was 8.36 MB (Important 1).

**88 KB `design:ready`.**

- Acceptable for the demo (4x HEAD, 20 ms), but 65% is repeated `containers`. Because Studio needs `containers` only for the selected target, drop it from bulk manifests (Important 1). That also brings `design:targets` back near HEAD size.

**Other calls I agree with.**

- Container keys exclude bridge-added ids.
- `canonicalPatch.move.index` is the final index.
- `before`/`after` may name a target in another container.
- `force` overrides only the framework guard.
- `imports` is reference-counted (only in-use stylesheets).
- The opener poll is 500 ms.

## Assessment

Task E meets the contract and Addenda 1 and 2 for moves, guards, css-order, overlay, font stylesheets, SPA re-apply, R1, R2, M7/R3 and M8, with strong, mostly honest tests (88/88 green, `node --check` clean). Reset is byte-exact in every case I tried, and the real demo remains fully usable in Select and Interact modes. I found no Critical issue. One verified Important issue remains: the quadratic bulk manifest (`containers` repeated per target), which makes `design:ready` and every `design:targets` post multi-megabyte on an ordinary 2000-node page. It has a small, local fix (omit `containers` from bulk manifests, plus a size test) and a plan-text change. The remaining findings are Minor.

**Task quality:** Approved with fixes

---

## Re-review after first changes

Scope: Task E changes after first review against plan Addendum 3 (D019). Task E still uncommitted. Read-only; scratch probes.

Commands: `python3 -m unittest test_bridge_runtime test_preview_server -v` (Chromium): `Ran 98 tests in 97.748s, OK`. `node --check fontkit-bridge.js`: OK. The test suite passes while I2 below exists, so there is a test gap, not just a code gap.

### Verified fixed

- **I1 (bulk size).** Same generated 1846-node, 718-target page:

  | | before fix | after fix | HEAD baseline |
  |---|---|---|---|
  | `design:ready` bytes | 8.36 MB | 711 KB | 288 KB |
  | `design:ready` in-page time | 790 ms | 169 ms (tests running concurrently) | 36-58 ms |
  | `design:targets` per rediscovery (2 Hz ticker adding a button) | 8.4 MB x 5 | about 711 KB x 6 | about 288 KB |

  Demo `design:ready`: 88.7 KB down to 50-54 KB, 20 ms. Bulk `arrangement` keys are now `containerKey, containerName, containerSelector, count, cssOrderAvailable, frameworkManaged, index, siblings` (no `containers`). A selected manifest carries 15 containers and the full siblings.
- **Content-model guard.**
  - Block into `p`, `h2`, `span`, `a`, `button`, `label`, `summary` is rejected (10 variants, including `before` a child of a `p`). `detail.guard` is `content-model`, `overridable: false`, and `force: true` does not override it.
  - A `p` into a `p` is rejected.
  - Allowed: span into div or p, em into span, same-parent reorder inside an `<a>` that holds block children, reordering in flex, div into div, css-order.
  - The rejected moves left the DOM untouched.
  - Gap (Minor): only the moved element's own tag is checked, so an inline wrapper that contains a block child can still be moved into a `p`.
- **Font percent allow-list.** All 40 hostile URLs are rejected, including the earlier `%0a`, `%3C…%3E` and `%2F..%2F`. Dedupe, release, replace, atomicity, reset-all and re-add-after-app-removal are unchanged.
- **M1.** The 1.5 KB SVG data URL with raw spaces and quotes is now `data:image/svg+xml,…(995 bytes)`. Base64 `src`, `url()` and `href` data URLs are abbreviated.
  - Minor: any attribute whose value merely starts with `data:` is collapsed. An author `title="data: hello this is a long title…"` became `title="data:…(338 bytes)"`. A `srcset` with two data URLs collapses to one. Fix: limit whole-value collapse to `src`, `href`, `poster`, `action`, `data`, `xlink:href`, or require `^data:[mime]?(;param)*,`.
- **M3 backoff.** On my any-attribute re-render app: 13 renders in the first 3 s (previously 34 and still going), then +2, +0, +1, +0, +1 per 3 s window. One `console.warn`, and a normal update is still answered. The loop slows to roughly one rediscovery plus render per 3-8 s but never stops. That is acceptable for a pathological page, because it costs one small discovery per backoff step and the app is already looping with itself. A page-level breaker (stop rediscovery after N backoff steps until a `design:hello`) would still be better. Not required.
- **M5.** Container names are now informative: `Halyard home`, `Client work, without the status meeting…`, `div.actions`, `Example project`, `Live client portal`. Residual Minor: three identical `details` entries on the demo FAQ (no heading text inside the `<details>` parent).
- **Regressions: none found in reset or overlay.**
  - Byte-exact reset: fixture reset-all, round trip, no-op move, app-removed destination, legacy layout (M7), demo single reset, demo cross-container single reset, and demo reset-all are all identical to the baseline `outerHTML`.
  - Overlay: removed on `overlay:false`, on a new session and on opener close; never in ledger or `body` structure html.
  - R1 behaves as before; the M8 selectors are still unique (0 non-unique among 718 targets); the font probe is unchanged.
- **Real Studio probe** (current uncommitted `font_kit_studio_v0.1.1.html` at `http://studio.test`, real bridge in `demo/index.html` at `http://target.test`):
  - `?target=` connected with the badge `Connected (46 targets)`. I observed it only at the first connect, before any rediscovery, so it never showed the I2 effect described below.
  - Clicking `.actions .btn-primary` in the iframe selected it.
  - The Arrange list showed `landing.hero.cta` and `auto:a:button:6`.
  - `#liveMoveNext` moved the DOM (`See how it works`, `Start your free trial`).
  - The HTML tab then showed the structure comment `<!-- Structure: div.actions … child order: A: "See how it works", Hero call to action -->` plus the cleaned `<div class="actions">` snippet.
  - No contract mismatch: Studio reads Arrange data from selected/applied manifests (`font_kit_studio_v0.1.1.html:3976-4003`), filters `arrangementOnly` from its list (`:3689`, `:3874`), and treats only framework guards as overridable (`:3973`, `:4126-4129`), which matches the bridge (`fontkit-bridge.js` `moveGuard`, `overridable: false` for content-model).

### New Important issue

**I2. `arrangementOnly` is cleared on the first rediscovery, which silently brings back the original hit-test noise.**

- Where: `fontkit-bridge.js:2066-2072` (`discoverTargets` step 2) with `registerAuto` at `:2010-2021`. A sibling-only record gets bridge-owned `data-design-role` written onto its element (`setBridgeAttr(el, 'data-design-role', role)`). The next discovery's candidate selector `[data-design-role]` matches that bridge-written attribute, finds a known record, and runs `known.arrangementOnly = false` ("it is a semantic/role target after all").
- Verified failure scenario (demo, real bridge):

  | Moment | records flagged `arrangementOnly` |
  |---|---|
  | after first hello | 12 |
  | after a second hello (Studio reconnect or new session) | 0 |
  | after any DOM mutation, such as appending a div, or after a `design:move` (about 500 ms later) | 0 |

  - Afterwards `closestTarget(summary)` returns the `summary` record again. A Select-mode click on the FAQ `<summary>` is intercepted and does not toggle the `<details>`, and a hover or click on a `li` selects the whole `ul`. This is exactly the behaviour Addendum 3 was meant to remove. My 24-spot table was identical to HEAD only on a pristine page; any move, any re-render or any reconnect restores the old noise.
  - Studio is affected too: it excludes `arrangementOnly` targets from its default list, so the same session's target count jumps from 34 to 46 after the first rediscovery.
  - The new tests do not catch this because they hit-test straight after the first hello without any rediscovery.
- Fix: in step 2, clear the flag only when the role is author-supplied or the element is semantic, for example `if (this.authorAttr(el, 'data-design-role') || this.isSemanticElement(el)) known.arrangementOnly = false;`. Or exclude bridge-owned attributes from the `[data-design-role]` candidate set (`this.isBridgeAttr(el, 'data-design-role')`). Add a test that performs a second hello, then an appended node and a `design:move`, and then re-checks `arrangementOnly`, the `li` hit-test and the `summary` toggle.

### Minor

- **N1. Bulk siblings still grow quadratically up to the 100 cap.** 20 `section`s each with 100 target children (2000 targets): `design:ready` was 15.8 MB (7.9 KB per target), measured with tests running concurrently so the 1.8 s is inflated. This follows Addendum 3 as written. Because Studio reads Arrange data only from selected/applied manifests, the bulk `siblings` list is unused. Consider lowering the bulk threshold (for example to 12) or omitting bulk `siblings` entirely and keeping `count` and `index`. A plan amendment would be needed.
- **N2.** The M1 and content-model gaps listed above.
- **N3.** The bridge still posts all targets on each target-changing rediscovery (about 711 KB on the 718-target page at 2 Hz in my ticker). It is a fraction of the earlier 8.4 MB but still unbounded for chatty apps; a diff or a cap on `design:targets` frequency would help later.

### Verdict

Changes after first review resolves I1 and the four requested Minor items (M1, M2, M3, M5) and adds a sound content-model guard, and the real Studio flow works end to end. The new `arrangementOnly` hit-testing, however, stops working after the first rediscovery (second hello, any DOM mutation, or any move), so the headline UX fix from the review is lost in real sessions. That needs one small bridge fix and one regression test before this is approved.

**Task quality:** Approved with fixes (I2 must be fixed and covered by a test before commit)

---

## Re-review after second changes

Scope: Task E changes after second review (I2, bulk siblings and containers omitted per the Addendum 3 amendment, M1 scope). Task E still uncommitted. Read-only; scratch probes.

Commands: `python3 -m unittest test_bridge_runtime test_preview_server -v` (Chromium): `Ran 101 tests in 95.063s, OK`. `node --check fontkit-bridge.js`: OK.

### I2: fixed

Demo, real bridge, sequence run in one session. After each step: flagged `arrangementOnly` count, hit-test of a `.plan li` (via `closestTarget` at the element's centre), and whether a real click on the FAQ `<summary>` toggles the `<details>` in Select mode.

| Step | flagged | `li` hit | summary toggles |
|---|---|---|---|
| after first hello | 12 | none | yes |
| after second hello | 12 | none | yes |
| after appended DOM node (+500 ms) | 12 | none | yes |
| 600 ms after `design:move` of a sibling-only `ul` | 12 | none | yes |
| after a third hello (reconnect) | 12 | none | yes |
| after reset-all | 12 | none | yes |
| after iframe reload and a fresh hello | 12 | none | yes |

The earlier failure (flags dropping to 0 after the second hello or first mutation) no longer reproduces.

### Bulk manifests: fixed

- `design:ready` arrangement keys: `containerKey, containerName, containerSelector, count, cssOrderAvailable, frameworkManaged, index`. There are no `siblings` and no `containers`.
- `design:selected` and `design:applied` carry the full arrangement (`siblings` of 2, `containers` of 15 for the CTA).
- Sizes (tests were running concurrently, so times are noisy and likely inflated):

  | Page | before changes after first review | after round 1 | now | HEAD baseline |
  |---|---|---|---|---|
  | 718-target, 1846-node page: bytes | 8.36 MB | 711 KB | 586 KB | 288 KB |
  | same page: in-page time | 790 ms | 169 ms | 145 ms | 36-58 ms |
  | 20 sections x 100 target children (2000 targets): bytes | not measured | 15.8 MB | 1.40 MB | not measured |
  | same page: in-page time | | 1.8 s | 609 ms | |
  | ticker (a button added every 500 ms for 3.2 s): `design:targets` per post | 8.4 MB | 711 KB | about 587 KB (5 posts) | about 288 KB |
  | demo `design:ready` | 88.7 KB | 50-54 KB | 40 KB | 20 KB |

  The remaining gap to HEAD is per-target manifest bytes (`containerSelector` about 110 chars plus `containerName`, and the arrangement fields); it is linear, about 800 bytes per target. Keeping `containerSelector` is fine.
- Residual, unchanged Minor: a target-changing rediscovery still reposts the whole manifest (about 587 KB at 2 Hz on the 718-target page).

### M1 scope: fixed

- Abbreviated: `src`, `href`, `url(data:…)` in `style`, and each `srcset` candidate separately, for example `srcset="data:image/png;base64,…(422 bytes) 1x, data:image/png;base64,…(522 bytes) 2x"`. The 1.5 KB SVG data URL with raw spaces is now `data:image/svg+xml,…(995 bytes)`.
- Untouched: the 346-character `title="data: hello this is a long title …"` is intact, and `data-x="data:,short"` is intact.

### Regressions: none found

- Byte-exact reset, compared via `documentElement.outerHTML`: all identical to baseline.
  - Fixture reset-all (1817 = 1817).
  - Round trip back to the original position, and a no-op move.
  - Reset after the app removed the destination container.
  - Legacy layout (M7).
  - Demo single resets, a demo cross-container single reset, and demo reset-all.
  - Probe edit: `move2.py` read bulk siblings, so I changed it to take siblings from a selected manifest.
- Overlay: appears with `pointer-events:none`, removed on `overlay:false` and on a new session, removed about 0.5 s after the opener closes (the popup's nav link still works), and absent from the ledger html and the `body` structure html.
- Font URLs: 0 of the 40 hostile URLs accepted.
- Content-model guard: block-in-`p` and the other variants still rejected with `overridable: false`; allowed moves unchanged.
- M8: 0 non-unique auto selectors among 718 targets, including after a mutation.
- M3 backoff: unchanged (the any-attribute re-render app logs 17 renders after the first update, then slows; one `console.warn`; updates still answered). The style-ping-pong loop remains bounded (7 renders).

### Real-Studio probe (note only)

The uncommitted Studio and the real bridge on the demo connected with `Connected (34 targets)`. That is now consistent with `arrangementOnly` targets being excluded and staying excluded (earlier it jumped to 46 after rediscovery). Clicking the CTA in the iframe selected it, the Arrange list showed both siblings (taken from the selected manifest), `#liveMoveNext` moved the DOM, and the HTML tab showed the structure comment plus the cleaned `div.actions` snippet. Task F is concurrently adjusting Studio to tolerate omitted bulk siblings; this probe ran against its in-flux file and passed, which I note without blocking Task E on it.

### Verdict

All three requested items are fixed and verified on the real bridge, and no regressions were found. No Critical or Important issues remain. Remaining items are Minor only: whole-manifest reposts per rediscovery, and content-model checking only the moved element's own tag.

**Task quality:** Approved
