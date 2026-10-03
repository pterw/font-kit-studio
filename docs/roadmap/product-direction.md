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
treat typography as one property among many and assume you have the source code. fontkit
keeps typography at the centre:

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

## Surfaces

The bridge protocol is the engine. It can sit behind more than one front end:

| Surface | For | Priority |
|---|---|---|
| Browser extension (side panel) | Anyone, on any site, nothing added to the app | **Lead.** This is the only surface that meets "any site, no setup". See [browser-extension.md](browser-extension.md). |
| Standalone Studio (exists) | Your own app, offline work, any stack | Reference implementation. |
| Dev-server plugin (Vite, Next) | Developers who want edits written into their project | Later, if developers ask for it. |

## Order

1. Finish the v0.2 pull request, including the known-limit fixes (plan Addendum 7).
2. Solve the extension transport: a side panel is not the page's parent or opener, so the
   bridge needs an extension channel with the same origin and session checks and its own
   hostile-input tests.
3. Extension first version: side panel, any tab, font swap and pairing, type scale,
   readability guardrails, CSS and token export, per-site saved edits.
4. Type-scale, guardrail and token features in Studio as well.
5. Arranging in the extension (the guarded moves that Studio already has).
6. Only then consider box-model editing, breakpoints or a dev-server plugin.

Box-model handles and per-breakpoint editing are what general editors compete on. They are
deliberately late: they pull fontkit into the fight it is least likely to win.

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
