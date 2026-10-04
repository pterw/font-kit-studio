# Changelog

All notable changes to fontkit (Font Kit Studio). Format: [Keep a
Changelog](https://keepachangelog.com/en/1.1.0/). Dates are ISO.

Two things have their own version numbers:

- The exported JSON stays at format version `0.1.1`, with an optional `live`
  field (saved overrides, tokens, DOM order). Older files still import.
- The Design Bridge Protocol is version 1 (`protocolVersion: 1`). Every change
  so far is additive.

## [Unreleased] - v0.2.1

Not released yet. The first half is merged to `main`; the rest is in review.

### Added

- Controls that would do nothing are disabled, with the reason in the
  tooltip: Sync to Live App with no page, Restore Page Text, Reset this
  element, Sync to file, Copy and Download with no changes, Load free fonts
  once loaded, single-cut styles, Image Width with no image, Focus pop-out.
- First-run help: the Target URL box starts empty and says what to enter;
  the dev server prints one `Open:` URL, names a busy port, and opens a
  browser only with `--open`; Studio offers "Connect to the demo" and never
  connects by itself.
- An Exit button in fullscreen, plus `Esc`. A favicon for Studio and the demo.

### Changed

- Preview widths (390 / 1024 / 1440) scroll under the preview instead of
  cropping it. Nothing is scaled.
- The `--font-serif` token comes from a slot's role or serif tag, never a
  fixed slot. Sans and mono follow the same rule, so the default preset no
  longer sends `--font-sans`.
- Importing while linked to the page keeps the import's state, ends the link
  and shows the reconnect banner if the page differs (D035).
- Fullscreen no longer connects to the Target URL.
- The preset select applies on change and asks before replacing slot edits.
- Library says which fonts are loaded, including ones loaded from the Composer.

### Fixed

- A late edit reply after an import no longer overwrites it (D038).
- A selection made before a reload no longer pulls the inspector back.
- Sync to file and Auto-sync never write a placeholder over an existing
  overrides file in a fresh session. After you reset the last change, Sync
  clears the file.
- Dead or misleading controls: preset select, custom kit, single-cut
  "Regular" chips, the demo's plan buttons, Move into (starts empty), a click
  on an Arrange sibling (now selects it), the recursion message (keeps your
  text), the invalid colour message (the previous colour stays), and a note
  that an SVG's own fills win.
- A target URL like `http:example.com` is refused instead of resolving
  against Studio.
- An element with a duplicate `data-design-id` no longer discards its
  container's saved DOM order.
- A composition with more than 16 library fonts names the ones not sent.

### Known limitations

- The Studio file is still `font_kit_studio_v0.1.1.html` until the rename
  (R1).
- Firefox runs a short canary in CI, not the full suite, and its results are
  advisory. Chromium is the tested browser.
- Reapply cannot undo a DOM move that reached the page after an import, and
  cannot replay a Move anyway.

## [0.2.0] - 2026-10-03

The live preview. The tag `v0.2.0` will point at a6d2751 (PR #1 merged at
32c087a, PR #2 at a6d2751).

### Added

- **Live preview:** open your own app beside Studio, click an element, edit
  font, size, line height, tracking, weight, case, alignment, colour or text.
  Studio shows what the page confirmed, not what it asked for.
- **Design Bridge Protocol v1** and `fontkit-bridge.js`: dependency-free,
  development only, inert until Studio connects.
- **Inspector** with Select and Interact modes, stable names from
  `data-design-*` attributes, and auto-discovered targets whose selectors
  are labelled unstable.
- **Changes panel** (CSS, HTML, JSON tabs) with Copy, Download, Sync to file
  and Auto-sync. Text and DOM moves go to the HTML tab, not the CSS.
- **Sync to file** through `python scripts/serve.py`: two loopback ports, one
  atomic write to one `.css` file.
- **Arrange:** move elements by CSS order or DOM order, with guards for
  forms, radio groups, labels, content model and framework-managed DOM
  (Move anyway for the last).
- **Pop-out window** for apps that refuse framing.
- **Reconnect banner:** a reloaded page is never restyled without your choice
  (Reapply Studio overrides, or Accept target state).
- Composition tokens, CSS order and DOM order saved in `live` and replayed by
  Reapply. Composer Sync to Live App also sends each font's stylesheet.
- **Free fonts only on request** (D028, D031, D032). Adobe Fonts is
  bring-your-own.
- MIT licence (D025), logos, the "Halyard" demo, and a CI quality gate.

### Changed

- A `null` composition token removes Studio's override and restores the
  page's own value.
- Composer tracking reaches the page in em; it used to arrive 1000 times too
  small.

### Fixed

- Fixes to the supplied v0.1.1 file: fractional row counts, hidden
  descendants kept after a row shrinks, row alignment, a breakpoint field
  showing a clamped value, a crash on numeric roles, role and property CSS
  collisions, a metadata data-URL leak, malformed slot and background data
  accepted on import, a late image read landing on the wrong slot, and an
  empty kit list not round-tripping. A rejected import keeps your state.
- DOM moves survive a reload.
- Removing a `data-design-id` while editing keeps the edit.
- A late reply no longer moves the selection off your pick.
- A mixed-case origin list no longer refuses a valid Studio.
- Hot reload no longer starts a second bridge that captured edits as
  originals.
- Ids with `; { } < > ( ) / * !` keep their rules in Copy, Download and Sync.

### Security

- Both sides check source window, origin, protocol version and session on
  every message, and post to the pinned origin, never `*` (except an opaque
  `null` origin and the data-free `design:bridge-ready`).
- No untrusted markup is parsed into a live page. Text goes in as text,
  images as `<img>`.
- Target URLs are `http:` or `https:` only (`file:` only from a file);
  `?target=javascript:...` no longer runs in Studio's origin.
- Values are allow-listed: CSS values, font stylesheet URLs, token names.
- The dev server checks `Host` and `Origin`, limits writes to 1 MiB, writes
  atomically and does not follow symlinks out of the repository.

### Removed

- The legacy SVG placement that inserted parsed markup, the unused
  `design:select-slot`, `design:inspect` and `design:ping` messages, and the
  uncalled `registerElementTarget` method (D022, D024).
- A prefilled Adobe kit ID. Defaults are free OFL fonts, empty credentials.

### Known limitations

- Studio's title and eyebrow, and the file name, still say v0.1.1 (D009a).
- Edits made while the page is reloading are dropped.
- Reapply cannot replay a Move anyway.
- Firefox was not run locally; CI results are advisory.

## [0.1.1] - 2026-09-30

The supplied single-file Studio, preserved at the tag `supplied-v0.1.1`.

### Added

- **Library:** a specimen browser for 16 free fonts.
- **Composer:** responsive rows of 2 to 4 leaf slots, PNG and SVG marks.
- JSON import and export (format version `0.1.1`) and CSS export.

### Known limitations

- Nested rows and JPEG assets are out of scope.

[Unreleased]: https://github.com/pterw/font-kit-studio/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/pterw/font-kit-studio/compare/supplied-v0.1.1...v0.2.0
[0.1.1]: https://github.com/pterw/font-kit-studio/tree/supplied-v0.1.1
