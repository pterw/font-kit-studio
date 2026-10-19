# R2.7I1 brief: role round trips through the real command, plugins and proxies

Plan: `docs/plans/2026-10-03-r2-engine.md` task R2.7I (entrypoint bullets) and Addendum 25 (slice R2.7I1, wave W1);
Addendum 26 only for the tolerant status wording. BASE `bd20e43b912bee1431fc74d3334c8a6bd4ac55e7` (the controller fills the SHA; source read at
`362ffd11e726011f3ca3c932e93a6e4c3d8c967d`). Worktree `C:/fks/t7i1` (detached at BASE; run `tools/link-fixtures.ps1
-Worktree C:/fks/t7i1` after creating it), task id `7i1`. Line budget: about 380 gross lines (up from 330 after the review's fixes), all in one new test
module. Tests only: no product code, workflow or package change.

## Why

Detect -> Apply -> rerender -> Clear is proven only against fake origins (`tests/test_studio_roles.py`,
`test_r2_integration.py`) and bridge-level messages on one Vite app (`test_r2_react.py` drives `design:*` messages
itself). No test runs the real Studio over the real `fontkitstudio` command, the Vite 7 and 8 plugins, the proxy in
front of Bootstrap 5, or the proxy in front of Next.js, and then reads what the page renders. The existing one-command
modules (`test_one_command_vite.py` 43-229, `test_one_command_proxy.py` 35-116, `test_one_command_next.py` 14-190)
stop at a font-size edit. `test_vite_build_guarantee.py` 12-56 scans builds for the bridge but not for role CSS.

## Owned files (exact)

- New `tests/test_r2_entrypoints.py`. Nothing else. Read-only: every other file, including the existing one-command,
  fixture-support and React modules, the fixtures, `.github/workflows/quality-gate.yml` and the package.

## Read first

`constraints.md`; at BASE: `tests/fixture_support.py` (all), `test_one_command_vite.py` 43-145,
`test_one_command_proxy.py` 35-84, `test_one_command_next.py` 14-135 and 136-190, `test_r2_react.py` 157-190
(`guarded_context`) and 449-540 (what a Detect reply and an Apply receipt hold), `test_studio_roles.py` 189-260
(Studio's role controls: `detect`, `control`, `button`, `type_value`, `preview`), the plan's "Messages" and Addenda 16-18
(stale receipt: the next Apply or Clear needs a fresh Detect), and `fontkit-studio.html` 4438 (`NEXT_STEPS`
`page-changed`: "The page changed: press Detect text styles, then try again.").

## Fixed design (do not re-decide)

- **Reuse without a new shared path.** Borrow the existing public harness methods by assignment, never by importing a
  TestCase class name into the module (discovery would run it twice): `import test_one_command_vite as vite`, then in
  the class body `start = vite.OneCommandViteBrowserTest.start`, `pump`, `stop`, `wait_badge`, `select_title`. The
  Vite class needs its own `setUpClass` (the bundle step, as `test_one_command_vite.py` 43-45) and `setUp`
  (`self.contexts = []` plus the `close_contexts` cleanup); `start` itself calls `require_fixture`
  (`test_one_command_vite.py:54`). Next: borrow `start_next`, `drain`, `tail`, `stop_next`, `start_command`, `wait_badge`,
  `select_title` from `test_one_command_next.OneCommandNextBrowserTest`; its `require_fixture` lives in that class's
  `setUp` (`test_one_command_next.py:76`), which is NOT borrowed, so the new class's own `setUp` sets `self.contexts`,
  registers the `close_contexts` cleanup and calls `require_fixture(self, 'next-app')` (a missing install must fail
  under `FKS_REQUIRE_FIXTURES=1`, not die in Popen); it also needs the bundle `setUpClass`. Proxy: borrow `stop_helper`,
  `wait_badge`, `select_title` from `test_one_command_proxy.OneCommandProxyBrowserTest`; its own `setUp` repeats only the
  `start_csp_server(FIXTURE, csp=...)` and helper-start lines (`test_one_command_proxy.py:36-52`, the one difference
  is the `csp=` argument). Build: borrow `build` from `test_vite_build_guarantee.ViteBuildGuaranteeTests`
  (`test_vite_build_guarantee.py:17-33`; it needs only `self` and already asserts `BUILD_LINE`). Guard: `guarded_context`
  from `test_r2_react.ReactCorpusTest` (public, uses only `self.assertEqual`). Free functions (`free_port`, `refused`,
  `interrupt`, `require_fixture`, `vite_bin`) are imported by name. `open_studio` is NOT borrowed (below). Per ruling 3,
  list each borrowed member by module and name in the report.
- **HTTPS guard and one own `open_studio`.** The borrowed `open_studio` methods (`test_one_command_vite.py:131-144`,
  `test_one_command_next.py:174-187`) use `new_context` plus a bare `route('https://**/*', abort)`: no verified
  prefix, no counts, no canary, against D059 and constraints ruling 9. Write one `open_studio(self, engine, url)` in
  this module on `guarded_context(engine)`: append the context to `self.contexts` (the guard does not), wire
  `pageerror` and console errors, `goto`, wait for the connected badge (60 s first, as Next does), take the frame, wait
  for `readyState === 'complete'`, return `page, frame, errors, console_errors, counts`. Each test ends by asserting
  `counts == {'aborted': 2, 'fallback': 0}` and no `pageerror`. All three classes use it.
- **Real Studio UI, keystrokes.** Open the Studio URL the command prints (`?target=...`). Detect with the "Detect text
  styles" button; pick the role row with `page.locator('#roleRows > li', has_text=<selector text>)`; inside it use the
  labelled controls "Preview this role for ..." and "Size (px) for ..." (`get_by_label(re.compile(...))` scoped to the
  row, so names are not hard-coded), typing with `focus`, `ControlOrMeta+A`, `press_sequentially('48')`; then the
  buttons "Apply selected roles" and "Clear preview". Wait on conditions (`#roleStatus`, computed style, the owned
  `style[data-fontkit-role-styles]` count), never fixed sleeps.
- **Oracles.** Vite and Next apply Size 48. Title sizes are literals from the fixture CSS: Vite fixtures' `h1` has no
  rule (`fixtures/vite-react/src/app.css`, `vite7-react/src/app.css`), so the UA default `32px`; Next `h1` `40px`
  (`globals.css`; type selector 0,0,1 loses to the role sheet's 0,1,0). **Bootstrap cannot take Size**: `app.css`
  `.hero h1 { font-size: 40px }` (0,1,1) beats the plain role selector `[data-design-id="bs.hero.title"]` (0,1,0; the
  bridge bans `!important`, `fontkit-bridge.js:159,181`) and the bridge would report an `author-rule` loss
  (`fontkit-bridge.js:1739`). The Bootstrap case therefore applies **Weight 700** to the title role: nothing in
  `.hero h1` sets weight, Bootstrap's `h1 { font-weight: 500 }` (`vendor/bootstrap.min.css`) is a type selector
  (0,0,1) and loses, so the literals are `500` -> `700`. Use the labelled control "Weight for ..." in the row.
  Measure the group's selector once at BASE and pin it as a literal if it is a `data-design-id` (the hero title ids are
  `vite.hero.title`, `next.hero.title`, `bs.hero.title`); a `[data-design-id=...]` binding is expected, but a group
  that also binds other elements (Bootstrap `bs5.heading.1` shares the 40px signature) is fine: assert only that the
  title changes and that every other `[data-design-id]` text element outside the chosen selectors keeps the value
  measured before Apply.
- **Snapshot.** `snap(frame)` = `[main.outerHTML, per-`[data-design-id]` computed font-family, font-size, font-weight,
  line-height, letter-spacing, text-transform, `document.querySelectorAll('[style]').length]`. Taken before Apply
  (A) and after the rerender with the preview on (B). `main.outerHTML` differs between A and B (the rerender changes
  author text), so the comparisons are separate and never one equality on the whole snapshot: after Clear, (i) the
  markup part equals B's markup, (ii) the computed text properties per id equal A's, (iii) the `[style]` count equals
  both A's and B's.

## Requirements (one browser round trip per entrypoint, per engine in `ENGINES`)

Each case's docstring is Given/When/Then and its Then is exactly what it asserts.

1. **Vite 8 command** (`fixtures/vite-react`, class `ViteEntrypointTests`, `test_vite8_command_detect_apply_rerender_clear`).
   `self.start('vite-react')`; Detect (status starts with "Detected"); Apply 48 to the title role: frame title
   computed `48px`, snapshot A's `main.outerHTML` unchanged (the preview is a stylesheet only), exactly one owned
   `style[data-fontkit-role-styles]`, the receipt shown in `#rolePreviewCss` contains `font-size: 48px`. Rerender by
   first clicking Studio's `#bridgeModeInteract` button and waiting for `aria-pressed="true"` (Studio starts in select
   mode, `fontkit-studio.html:2312`; the bridge's capture-phase `handleDocumentClick`, `fontkit-bridge.js:3851-3893`,
   `preventDefault`s and `stopPropagation`s any `data-design-id` click, and `vite.hero.cta` has one, so without this
   the click selects instead of rendering), then clicking the page's button twice ("Clicked 2 times", a real React
   state render): title still `48px`, the owned node
   is the same element handle and still connected, no `[style]` attribute added. The render changed author text, so
   Clear is refused until a fresh Detect: assert Studio shows the `page-changed` next step text (`NEXT_STEPS`) after one
   Clear click and the title is still `48px`; then Detect again, then Clear: owned node count 0, and the three comparisons of the Snapshot bullet hold (markup equals B's, computed
   text properties equal A's, `[style]` count equals both). Oracle: plan Addendum 16
   item 4 and the Messages table (`page-changed`), literals above.
2. **Vite 7 command** (`fixtures/vite7-react`): same test body through a shared private method on the class, a second
   test method (`test_vite7_command_...`). The method is the one caller of two tests, not an abstraction for later.
3. **Build output stays free** (same class, `test_vite_builds_ship_neither_bridge_nor_role_css`): for `vite-react` and
   `vite7-react` call the borrowed `build(name)` (it runs `vite build`, asserts exit 0 and `BUILD_LINE` once), then scan
   every output file for the existing `FORBIDDEN` needles (import them from `test_vite_build_guarantee`) plus
   `data-fontkit-role-styles`, `fontkit-role-styles`, `design:roles-apply` and `design:roles-clear` (these add value only
   for an inlined bridge that lacks the tag name); keep the positive control (the build holds `vite.hero.title`). Plain
   bytes, `assertFalse(needle in data, name)`. This is the plan's "existing production build" observation and it is
   Vite only; Bootstrap and Next have no build in this slice.
4. **Bootstrap proxy** (`fixtures/bootstrap5-static`, no npm install; class `ProxyEntrypointTests`,
   `test_bootstrap_proxy_detect_apply_rerender_clear`). Own `setUp` (borrow list above): `start_csp_server(FIXTURE,
   csp="script-src 'self'; style-src 'self' 'unsafe-inline'")` (the page keeps a real CSP that still blocks foreign
   scripts; ruling 1 explains why not the strict one), the helper start, same cleanups. Round trip as in 1 on
   `bs.hero.title` with **Weight 500 -> 700** (Oracles bullet; the receipt in `#rolePreviewCss` contains
   `font-weight: 700`). The rerender is the page re-creating its own title: `frame.evaluate` replacing the
   `h1[data-design-id="bs.hero.title"]` with a fresh element carrying the same attributes, class and text (the old
   handle must become disconnected). Then the role still shows weight `700` on the new node, then the same refusal and
   Detect-again step, then Clear returns every computed property to A, removes the owned node and leaves the
   `[style]` count as in A. No `securitypolicyviolation` is recorded in either document (reuse `RECORD_VIOLATIONS`
   from `test_one_command_proxy`). No separate upstream-clean or one-bridge-tag assertion: `test_one_command_proxy.py`
   85-90 already pins the tag, and an unproxied origin cannot contain the bridge, so such a check would pass with
   the feature deleted.
5. **Next.js proxy** (`fixtures/next-app`, class `NextEntrypointTests`,
   `test_next_proxy_detect_apply_rerender_clear`). `start_next()` and `start_command(port)` as in the existing test;
   Round trip as in 1 on `next.hero.title` (Size 48, literals `40px` -> `48px`); the rerender is a CSS hot update
   through the proxy's WebSocket: write `globals.css` with `rgb(51, 51, 51)` -> `rgb(200, 0, 0)` (the existing test's
   bytes) through a small local bounded loop (plan Addendum 16 item 4; the Vite coalescing race that
   `test_r2_react.py:380-397` handles can drop a lone write): rewrite, wait the lead's colour 1 s four times then
   10 s, fail naming the last computed colour. Use the same loop for the forward write and for the restore
   (`restore_css` there is h1-specific, so it is not borrowed). Register the restore cleanup before the first write and
   wait for `rgb(51, 51, 51)` before the next engine. After the forward write: lead colour `rgb(200, 0, 0)` with
   `window.__fksMarker` unchanged (no reload), title still `48px`; the same refusal and Detect-again step; Clear; then
   every text property in A is restored (colour is not in the snapshot). No `hydrat` console error. This class never
   runs `next build` (it would share `.next` with the dev server) and asserts nothing about the unproxied upstream.
6. **Installs are required where the CI job supplies them.** The two npm classes call `require_fixture` (Vite: inside the borrowed `start`; Next: in its own `setUp`, see Fixed design); under `FKS_REQUIRE_FIXTURES=1` a missing install fails, never skips. The module adds no
   skip of its own except the existing `skipIf(NODE is None)`.

## TDD

All behaviour exists on `main`: write the cases as GREEN characterization (no manufactured RED). Prove each with a
mutant, shown failing then restored byte-exact (SHA-256 before and after, mutations in the foreground, no server left
open). Realistic mutants: M1 `fontkit-bridge.js` roles clear leaves the owned sheet installed (cases 1, 2, 4, 5 fail
at "owned node count 0"); M2 `packages/fontkitstudio/src/vite-plugin.js` loses its `apply: 'serve'` guard so the build
carries the bridge tag (case 3 fails naming the file); M3 chosen by you at the rerender seam (for example the bridge
removing its owned sheet on author DOM change) that makes the "still `48px` after the rerender" assertion fail in at
least one case. M4 `fontkit-bridge.js` accepts a stale `pageVersion` on Clear (the `page-changed` refusal is skipped), so the refusal
step in cases 1, 2, 4, 5 fails. Report which mutant failed which case.

## Focused command

```
cd C:/fks/t7i1 && PYTHONPATH=tests FKS_ENGINES=chromium FKS_REQUIRE_FIXTURES=1 python -m unittest test_r2_entrypoints test_support -v
```

Needs installs in the worktree (linked by `link-fixtures.ps1`, or `npm ci --prefix fixtures/<name>`): `vite-react`,
`vite7-react`, `next-app`; `bootstrap5-static` needs none. Run the Next class alone first
(`test_r2_entrypoints.NextEntrypointTests`), it is the slowest. Also run `python -m ruff check tests/test_r2_entrypoints.py`.
Frontend gate, Firefox canary and the node-package suite are not part of this slice.

## Handoff (for the landing)

Commit subject: `test: run role round trips through every entrypoint`. Draft a why-body (wrap at 72) and a ledger
event in product terms. Draft the workflow steps for the controller (no workflow edit here):

- Job `fixtures` (matrix Ubuntu 22/24/26, macOS 24, Windows 24; installs `vite-react`, `vite7-react`, `vite-ts`; Chromium
  installed): a new step after "Fixture tests (never skipped here)", same env (`FKS_ENGINES: chromium`,
  `FKS_REQUIRE_FIXTURES: '1'`, `PYTHONPATH: tests`): `python -m unittest test_r2_entrypoints.ViteEntrypointTests
  test_r2_entrypoints.ProxyEntrypointTests -v`. Supplies cases 1-4. The bundle step already ran.
- Job `next-fixture` (installs `next-app`): a step after "Next.js fixture test (never skipped here)", env adds
  `NEXT_TELEMETRY_DISABLED: '1'`: `python -m unittest test_r2_entrypoints.NextEntrypointTests -v`. Supplies case 5.
- Job `quality-gate`: no step. Its discover run executes `ProxyEntrypointTests` (static fixture) and skips the two npm
  classes (nothing installed yet); record those skip names (`ViteEntrypointTests.*`, `NextEntrypointTests.*`) in the
  evidence as expected there, and read the two installed jobs' logs for "Ran N tests" with zero skipped.

## Open questions

1. **Strict CSP and the role preview.** `test_one_command_proxy`'s server sends `style-src 'self'`, which blocks the
   bridge's inline `<style>` (`installRoleSheet`, `fontkit-bridge.js` 1403-1410), so Apply there ends
   `stylesheet-blocked`. Option A (this brief): the page keeps `script-src 'self'` and adds `'unsafe-inline'` to
   `style-src`. Option B: also add a second case showing the strict policy yields the visible `stylesheet-blocked`
   failure with nothing changed (about 35 more lines; a hostile-boundary case the plan does not ask for). Recommend A;
   B only if the controller wants it.
2. **A workflow guard test.** "Empty pipeline skips cannot constitute R2 fixture acceptance" could also be enforced by a
   test that reads `.github/workflows/quality-gate.yml` and fails unless the three class names appear in steps that set
   `FKS_REQUIRE_FIXTURES: '1'`. It is red until the controller lands the Handoff steps and is text-matching, so it is
   left out. Recommend leaving it out; the CI-log read at the settled wave is the acceptance.
3. **Borrowing methods by assignment** couples this module to four existing test modules' internals. The alternative is
   about 120 copied lines (a fourth copy of the process-start code). Recommend borrowing; if an existing module changes
   shape, this module's import-time assignment fails loudly.

## Controller rulings on the open questions (2026-10-18)

1. CSP: option A stands, because `tests/test_r2_integration.py:625-642` already proves Studio shows "Role preview
   apply rejected (stylesheet-blocked); the previous preview is kept." against the real bridge under `style-src 'none'`
   (bridge-level `style-src 'self'` cases: `test_role_preview.py:345-351`, `test_role_stylesheet.py:550-559`); the
   Bootstrap docstring points there for the contract outcome. The Bootstrap proxy case serves a policy that adds `'unsafe-inline'` to `style-src`, stated in the
   test's docstring as the reason. A strict `style-src 'self'` ending in a visible `stylesheet-blocked` is a contract
   outcome; if no existing test proves Studio shows it against the real bridge, the brief review says so and option B
   (the second, strict case) joins this brief.
2. Workflow guard test: left out.
3. Borrowing: allowed, only of public (non-underscore) methods and classes, each listed by module and name in the
   report; no edits to the lending modules. If a needed member is private, copy it and say why.

## Revision 1 (2026-10-18)

Source facts re-checked at BASE bd20e43 (the review read 362ffd1; the cited files are unchanged).

- C1 (Bootstrap 48px impossible): Oracles bullet and requirement 4 now use Weight 500 -> 700. `app.css` `.hero h1`
  sets only font-size; `bootstrap.min.css` `h1,...{font-weight:500}` is a type selector. Review's fix used as proposed.
- C2 (Vite click swallowed): requirement 1 now clicks `#bridgeModeInteract` and waits for `aria-pressed="true"` first
  (Studio 1107, 2312, 6581; bridge 3851-3893).
- I1 (Next install guard): Fixed design "Reuse" bullet: own `setUp` calls `require_fixture(self, 'next-app')`;
  requirement 6 says where each class gets it.
- I2 (HTTPS guard): Fixed design "HTTPS guard and one own `open_studio`"; `open_studio` removed from the borrow list.
- I3 (Next bounded restore): requirement 5 adds a local rewrite-until-applied loop for the forward write and the restore.
- I4 (vacuous upstream checks): dropped from requirements 4 and 5; requirement 3 states the production-build
  observation is Vite only.
- m1 (ruling 1): ruling 1 gains the `test_r2_integration.py:625-642` line; option B is not added.
- m2 (snapshot wording): Snapshot bullet and requirement 1 separate the three comparisons.
- m3 (`build` borrowed): requirement 3 and the Reuse bullet borrow `ViteBuildGuaranteeTests.build`.
- m4 (proxy setUp duplicates): the Reuse bullet borrows `stop_helper`, `wait_badge`, `select_title`; only the
  `csp=` start lines are repeated; the one-bridge-tag assertion is dropped. Mutant M4 (stale-version Clear) added per
  the review's check list.
- Line budget: about 380 (330 + own `open_studio` 15 + Next loop 20 + Interact click 6 + Weight 3, minus the borrowed
  `build` and proxy helpers about 30 and the dropped upstream checks about 15, plus margin for the extra mutant).

## Revision 2 (2026-10-18; scoped re-review Minors folded by the controller)

- m1: the module's own `open_studio` takes an optional `init_script` argument, added with `add_init_script` before
  `goto`; the Bootstrap case passes `RECORD_VIOLATIONS` through it.
- m2: the two Vite clicks are awaited on the button text `Clicked 2 times` with `wait_for_function` (no sleep).
- m3: mutant M2 changes the plugin's `apply()` to return `true` (at BASE it returns `command === 'serve'`).
- m4: one build-output needle, `fontkit-role-styles`, covers `data-fontkit-role-styles` too.

## Revision 3 (2026-10-18; sdd-reviewer re-review findings folded by the controller, `task-7i1-brief-rereview2.md`)

- I1 (replaces Revision 2 m3): mutant M2 is two edits in `packages/fontkitstudio` `vite-plugin.js` (scratch copy):
  `apply()` returns `true` AND `let studio = options.studio ?? { origin: 'http://127.0.0.1:5000' }`. Only together do
  they put the bridge tag into the production `index.html` (the reviewer built `fixtures/vite-react` with this mutant
  and saw the tag; `apply` alone leaves the build clean because `studio` is set only in `configureServer`).
- m1: drop `select_title` from the borrow list unless a requirement calls it.
- m2: requirement 5 sets `window.__fksMarker = 1` before the forward write and asserts it is still 1 afterwards, so a
  full reload is detected.
