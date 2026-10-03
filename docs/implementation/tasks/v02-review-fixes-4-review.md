# Review: v0.2 review fixes, part 4

Verdict: **Approved**. No required changes; four informational notes.

Scope: `scripts/dev/_frontend_gate_colour.py`, `scripts/dev/_frontend_gate_theme.py`,
`scripts/serve.py`, `docs/assets/screenshots/capture.py`,
`tests/test_frontend_gate_helpers.py`, `tests/test_preview_server.py` and the new
`tests/test_frontend_gate_theme_browser.py`. The bridge, Studio HTML and
bridge/studio/live tests were ignored. Engine: Chromium only (Firefox not run).
All scratch scripts lived outside the repo. The one server I started (port 80;
I only sent PUTs that fail before any write) was stopped by PID and port 80 is
free again.

## Gate evidence

- `python -m unittest tests.test_frontend_gate_helpers tests.test_preview_server tests.test_frontend_gate_theme_browser tests.test_frontend_gate_fonts tests.test_frontend_gate_report tests.test_frontend_gate_runner`:
  `Ran 186 tests in 12.362s` / `OK`.
- `frontend_gate.py --offline --engines chromium`:
  `SUMMARY OK: 15 of 15 planned runs finished. Blocking: 7 runs, 6 passed, 0 failed, 1 skipped. Advisory: 8 runs, 0 ADVISORY lines. 140 REPORT lines, 1 SKIP lines, 0 FAIL lines`.
- `verify.py --static-only`: `PASS HTML IDs: 88 unique static IDs`, `PASS JavaScript syntax`, provenance PASS.
- Not run: `capture.py` (it rewrites the committed PNGs); I relied on the writer's
  report of a 4.7 s clean run and read the diff instead.

## 1. Number regex (colour module and in-page alphaOf)

`_NUMBER_RE = [+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?` (case-insensitive).

- Reads one number across an exponent: `color(srgb 1e-7 0.2 0.3)` gives
  `(2.55e-05, 51.0, 76.5, 1.0)`; `1e5`, `1.e5`, `-.5`, `+1.` are single numbers.
- Odd inputs do not crash or run away: `1e` gives `['1']`, `1e+` gives `['1']`,
  `.e5` gives `['5']`, `--1` gives `['-1']`, `1e-7e3` gives `['1e-7', '3']`,
  `1,e,2` gives `['1', '2']`. The old `[\d.]+` raised `ValueError` on a lone `.`;
  the new one is slightly more forgiving there. Nothing relevant to a computed
  colour.
- It does not match the letters of `srgb`, `color` or `rgba`: the pattern needs a
  digit first, and `findall('srgb')` is `[]`. A hue unit cannot reach it because
  hue forms are refused first.
- Python timing: 200,000-character hostile strings finish in 0.001 to 0.01 s. The
  match always succeeds after the number, so there is no backtracking.
- Unsupported forms are still refused loudly, because the refusal happens on the
  function prefix before any number is read: `oklch(`, `hsl(`, `#fff`, `lab(`,
  `color(display-p3 ...)`, `color(srgb-linear ...)`, `color(xyz ...)` and `hsl(1e2 1 1)`
  all raise `ValueError`.
- In-page regexes (`slashAlpha`, `commaAlpha`) are the same number pattern
  anchored to the end. Because they are anchored, a failing tail can backtrack
  quadratically: 20,000 digits took about 0.2 to 0.4 s and 100,000 digits about
  6 to 9 s. The old `[\d.]+\s*\)$` had the same shape, and the input is a computed
  colour string a few dozen characters long, so this is not a regression and not
  reachable in practice.
- Two behaviours the change did not touch and I did not ask for: percentages are
  read as bare numbers (`rgb(1 2 3 / 50%)` gives alpha 50, `rgb(10% 20% 30%)` gives
  channels 10, 20, 30), and a negative channel is now kept instead of having its
  sign dropped. Chromium never serialises a computed colour with percentages, so
  both are theoretical. See note 1.

## 2. serve.py default-port origin

- `Config.origins` gains `http://localhost`, `http://127.0.0.1` and the public name
  only when `studio_port == 80`. Config check: port 80 gives
  `{http://127.0.0.1, http://127.0.0.1:80, http://localhost, http://localhost:80}`;
  port 8000 gives only the `:8000` pair, so no portless origin opens on any other
  port. `0.0.0.0` binds map to the same set.
- Hostile origins on the port-80 config are all still rejected: `null`,
  `http://localhost:8000`, `http://evil.test`, `http://localhost.evil.test`,
  `https://localhost`, `http://localhost:`, `http://LOCALHOST`, empty string and
  `http://[::1]`.
- Real server, started on port 80 and driven with `curl` PUTs (wrong content type, so
  nothing could be written): `Origin: http://localhost`, `http://127.0.0.1` and
  `http://localhost:80` reached the next check (`415`); `null`,
  `http://localhost:8000`, `http://evil.test` and `http://[::1]` got `403`. Host
  header: `localhost` `302`, `evil.test` `421`, `localhost:8000` `421`.
  `git status` shows no change under `demo/`.
- IPv6: `[::1]` is allowed as a Host but has never been an allowed Origin (before or
  after). Not in scope, and the rule "reject what you do not list" holds. Studio
  never opens from a `[::1]` URL in the docs.
- Cosmetic only: the startup banner prints `http://localhost:80/...` on port 80.
  The URL works, so I left it.
- Test: `test_default_port_origins_and_hosts_omit_the_port` builds `Config`
  directly (no root needed) for three hosts, pins both origin forms plus the Host
  values, and pins the non-80 case, including `assertNotIn('http://localhost')`.
  Mutation: with the `if studio_port == 80:` branch disabled the portless origin
  is gone and the test's `assertIn` would fail. It is a config-level test, not an
  HTTP one, which is reasonable given binding port 80 needs root. The real-server
  check above covers the HTTP path.

## 3. capture.py waits

- All 10 `wait_for_function` calls now pass `polling=POLL_MS` (grep: 0 without).
  `POLL_MS = 50` matches the gate's value. The comment explains why (offscreen
  frame never runs a rAF callback).
- Informational: three calls are not `wait_for_function` and still use
  Playwright's default waiting: `page.wait_for_selector('#liveArrange')` (line 170)
  and `locator.wait_for(state='visible')` (lines 123, 129, 180). Those wait on the
  main Studio page, which does run animation frames, not on the offscreen frame the
  finding describes. I did not change or require anything here; if the mobile
  capture ever stalls on one of them, that is the next place to look.

## Test quality

- `tests/test_frontend_gate_theme_browser.py` runs the real `CONTRAST_JS` in a real
  browser against two near-transparent layers, asserts the walk's layer list and the
  judged result, and uses `support.ENGINES` and `launch`. Browsers are closed with
  `addCleanup`; the runtime is stopped in `tearDownClass`. No sleeps, no servers.
- Mutation: with the in-page regexes put back to `[\d.]+`, 4 of 4 sub-tests fail
  (walk returns one layer; white text on black is judged against the transparent
  layer). With `_NUMBER_RE` put back to `[\d.]+`,
  `test_exponent_notation_is_read_as_one_number` fails. Neither test is vacuous.
- The helper test covers the exponent channel, an exponent alpha, uppercase `E`,
  `rgba()` alpha and a bare `.5`.

## Style

Matches the surrounding code. Comments explain why. The report section is accurate
and honest about the one script run.

## Informational notes (no action needed)

1. Percentages and a negative sign are not specially handled by the colour parser
   (see section 1); fine while only Chromium-computed colours reach it.
2. Anchored in-page regexes are quadratic on absurdly long input (see section 1).
3. The `[::1]` Origin and the banner text on port 80 (see section 2).
4. `wait_for_selector` and `locator.wait_for` in `capture.py` (see section 3).
