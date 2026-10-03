# v0.2 review fixes, part 4: report

Scope: three Medium findings from the review of 3a409b8. Each was reproduced
before the fix.

## Colour parser split numbers at an exponent (medium)

- Problem: `_parse_rgb_string` read numbers with `[\d.]+`. Chromium
  serialises a tiny channel with an exponent (`color(srgb 1.00000e-7 0.2
  0.3)`, and `color-mix(in srgb, red 0.00001%, blue)` gives
  `color(srgb 1.19209e-7 0 1)`), so the "e-7" split off, every later channel
  shifted, and the red channel of the first example read as 255.
- Change: `scripts/dev/_frontend_gate_colour.py` reads complete signed
  numbers with an optional exponent (`_NUMBER_RE`).
- Tests: `ColourParsingTests.test_exponent_notation_is_read_as_one_number`
  (exponent channel, exponent alpha, uppercase `E`, `rgba()` alpha, a bare
  `.5`).
- Sibling, fixed in the same change: the in-page `alphaOf` regexes in
  `scripts/dev/_frontend_gate_theme.py` read digits and dots only, so a
  background of `color(srgb 0 0 0 / 1.00000e-7)` (what Chromium computes for
  `color(srgb 0 0 0 / 1e-7)` or a `color-mix()` that is 99.99999% transparent)
  was read as opaque. The walk stopped at that layer, and light text on a
  black page behind it was judged against the wrong surface and reported as
  failing. Both regexes now read a complete signed number with an optional
  exponent. A grep of `scripts/dev` and `docs/assets/screenshots` found no
  other colour-number parsing.
- RED: `tests/test_frontend_gate_theme_browser.py` drives `CONTRAST_JS` in a
  real browser and failed 4 of 4 (the walk returned one layer instead of
  two, and white text on black was reported as a contrast failure). GREEN
  after the fix.

## Default-port origin was refused (medium)

- Problem: with `--studio-port 80`, browsers send `Origin: http://localhost`
  with no port, and the allow-list held only `http://localhost:80`, so Sync
  answered 403 while the Host check passed.
- Change: `Config.origins` in `scripts/serve.py` also holds the portless
  origins when the studio port is 80. `hosts()` already allowed the portless
  Host on port 80, so it needed no change.
- Tests: `test_default_port_origins_and_hosts_omit_the_port` builds the
  config directly (no root needed) and pins both forms, plus the unchanged
  non-default case.

## Screenshot waits stalled on offscreen frames (medium)

- Problem: the `wait_for_function` calls in
  `docs/assets/screenshots/capture.py` used Playwright's default
  `requestAnimationFrame` polling, which can stall for a frame scrolled
  offscreen (the mobile capture) or a backgrounded page.
- Change: all ten calls (the three post-edit frame waits and the others)
  poll on a timer with `POLL_MS = 50`, the gate's value.
- Verified by running the script once: it finished in 4.7 s with exit 0. The
  regenerated PNGs were restored and not committed.
