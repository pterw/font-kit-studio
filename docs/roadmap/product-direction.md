# Roadmap: product direction

Status: **direction, not a commitment.** Nothing here is built unless a plan in
`docs/plans/` says so. Written 2026-10-03.

## Who fontkit is for

The main user is someone who wants to change the fonts on a real page and watch the result
while they try things:

- a UI developer who wants to settle a font pairing on the actual page, not a mock-up;
- someone who does not write front-end code but wants a quick, practical font change they
  can see, iterate on and hand over.

They should be able to start on **any site**, quickly, without learning the tool first.

## What fontkit is, in one line

A typography workbench for live pages: pick fonts and a type scale, see them on the real page
at once, and take away output you own. It works with any stack and needs no account.

## How it differs

General visual editors (Cursor's visual editor, Onlook, Builder.io Fusion, Chrome DevTools)
treat typography as one property among many and assume you have the source code. Free
font-swap extensions (FontMee, TypeTaster, Fontastic and others) let anyone try a heading
and body font on any site, but stop there. fontkit keeps typography at the centre and
turns what you try into code you keep:

- **Pairing on the real page.** Try a pairing across the whole page, not in a specimen.
- **Type scales.** Generate a scale (modular ratios, fluid `clamp()` sizes), map it onto
  headings and body text, and see the page snap to it.
- **Readability guardrails while you edit.** Contrast, minimum size, line length (warn above
  about 75 characters), line height, and the download cost of the fonts in use. The frontend
  gate already measures contrast; the product should show it.
- **Output that feeds a design system.** CSS variables and design tokens (CSS, W3C
  design-tokens JSON, a Tailwind theme), not only an overrides file, so edits do not become a
  second source of truth.
- **Licence labels.** Mark each font as OFL, commercial or self-hosted, so nobody ships a font
  they cannot use.
- **Trust.** No account, no data collection, works offline, silent until asked (D028).

There is no technical moat. The bet is that a focused, trustworthy tool beats a feature inside
a general editor.

## Surfaces and order

The agreed design and release order now live in
[the typography system design](../specs/2026-10-03-typography-system-design.md). In short:
one command for Vite and React projects and a local proxy for any other dev server come
first (R1); then the detection engine (R2), the pairing system (R3) and output and
handoff (R4); then the browser extension for non-developers (R5). Source rewriting and
"promote to source" come later.

Box-model handles and per-breakpoint editing are what general editors compete on. They
stay out of scope: they pull fontkit into the fight it is least likely to win.

## A consumer option worth keeping in view

People already restyle sites so they can read them: hyperlegible or dyslexia-friendly fonts,
wider spacing, larger body text. A "make any site readable my way" mode with per-site and
global presets would serve real users who are not developers. It needs saved edits applied
automatically on chosen sites, which means optional host permissions granted one site at a
time. Treat it as a possible direction, not the plan.

## Decisions this needs from the owner

- **Build step.** Global rule 8 keeps Studio a single file with no build. A Manifest V3
  extension page cannot run Studio's inline script, so the extension panel needs its script in
  separate files. Either the extension is hand-written files with no build, or it gets its own
  build. Studio itself can stay as it is either way.
- **Permissions.** `activeTab` plus a click keeps store review simple. Per-site automatic
  styling needs optional host permissions. Decide before promising "always on" presets.

## Risks to check early

- **Page security policies.** A strict `font-src` or `style-src` on a site may block injected
  fonts or styles. `chrome.scripting.insertCSS` and loading fonts through the extension may
  avoid this; it must be tested on real sites before "works on any site" is claimed.
- **Store review and privacy.** The extension needs a privacy statement and a minimal
  permission list.
- **Scope.** One maintainer cannot build three surfaces at once. Sequence them.

## Where it stands (2026-10-03)

Be exact about this when describing fontkit to anyone: the shipped product and the pitched
product are not the same thing yet.

- **Shipped (v0.2.0):** live per-element editing of a page that loads the bridge, DOM
  moves with guards, an overrides stylesheet the dev server writes, the Library and the
  Composer. Covered by 548 browser tests, hostile-input cases on every boundary, and a CI
  gate for network isolation and contrast. The first-run experience has known defects
  (`docs/implementation/audit-2026-10-03-first-run-and-controls.md`).
- **Designed, not built:** everything in "How it differs" above. One-command start (R1),
  role detection (R2), pairing and type scales (R3), token output (R4), the extension (R5).
- **Against "just looking", fontkit loses today.** A font-swap extension is faster for a
  quick peek because fontkit needs a script tag in the page. That is by design (Studio
  never runs inside the page it edits) and R1 and R5 remove the friction without giving up
  the design.
- **The extension earns its place only with the engine.** Click-and-swap alone is a
  smaller DevTools. It ships after R2-R4 so it carries roles, pairings, scales and handoff
  into a tab the user does not own; built earlier it would be the DevTools remake it is
  accused of being.
- **The README is the product page**, and does not position fontkit against competitors;
  that comparison lives here. A separate product page makes sense once R1 ships and there is
  a one-command story for people who do not start from a repository.
