# Design: fontkit typography system (pairing, output, low-friction setup)

Status: **approved by the owner (2026-10-03)**, including the self-review additions
(entry for non-developers, font choice, multi-page roles, one editing model, file format
version, release and supply chain, Studio accessibility, Next.js, performance). Section 6
lists the decisions that were open; they were answered on 2026-10-04 (D040-D049).
Nothing here is built. Implementation starts only from a plan in `docs/plans/`.

Related: [product direction](../roadmap/product-direction.md),
[browser extension](../roadmap/browser-extension.md), global rules 1, 5, 6 and 8
(`docs/agents/global-rules.md`), decision D030.

## Who it is for

Someone who wants to change the fonts on their own site and keep the result:

- a UI developer who wants to settle a pairing on the real page;
- someone who does not write front-end code and will hand the result to a developer.

"Just looking" is not a goal; free font-swap extensions already do that. fontkit is
worth using only if the pairing you try becomes code you keep: you apply it yourself,
or you hand it to a developer. Both paths must be first class.

The two users need different ways in. The developer works from a terminal in a local
project (section 1). The non-developer usually has no terminal, Node or local project;
their way in is the browser extension (release R5), which reuses the same engine, pairing
system and handoff.

Decided output order: **A** (a generated type-system file the app imports) first;
**B** (rewriting source) and **C** (a reviewed "promote to source" patch) later, tied.
B conflicts with global rule 1 as written; the rule is amended before B is built.

## 1. Starting fontkit (approved)

Goal: one command, no edits to the project, nothing written until the user confirms.

The command is written `npx fontkit` below for readability. The npm name `fontkit` already
belongs to an unrelated, widely used font engine, so the real package name is an open
decision (section 6).

| Project | Command | What happens |
|---|---|---|
| Vite (React or any Vite app) | `npx fontkit` | Runs the project's own Vite through its JavaScript API with the fontkit plugin added in memory, then opens Studio connected to the app. No config edit, no script tag. Stopping the command removes fontkit. |
| Any other local dev server (Bootstrap on WordPress, Rails, Django, PHP, static) | `npx fontkit http://localhost:8000` | **Proxy mode.** A loopback proxy in front of the existing dev server adds the bridge to HTML responses. The bridge is served from the app's own origin, so a `script-src 'self'` policy still allows it. Only `localhost` and loopback targets are accepted. |
| Permanent Vite setup | `fontkit()` in `vite.config` | fontkit starts with the normal `npm run dev`. |
| Next.js and other non-Vite React setups | `npx fontkit http://localhost:3000` | Proxy mode in front of the framework's own dev server. |
| Anything else | script tag, or `python scripts/serve.py` | Unchanged from v0.2. |
| Live sites you do not run locally (non-developers) | Browser extension (R5) | Same engine and handoff; output is the handoff zip. |

Rules for every entry point:

- **Dev only.** The plugin and proxy refuse to run in a production build and say so.
- **Visible.** The page and the terminal show "fontkit · dev only" while it runs.
- **Secure.** Loopback only; the existing Host and Origin checks; a per-run token in
  Studio's URL so another local page cannot drive it; the bridge keeps origin and
  session pinning.
- **No silent failure.** If Studio cannot connect (another bridge, a security policy,
  an unsupported project), it says what and why.
- **Packaging.** The Vite integration is a Node package with zero runtime
  dependencies that uses the project's own Vite (global rule 8, D030).
- **No telemetry.** No entry point sends usage data anywhere.

### 1.1 Releasing the package

- Semantic versioning and a changelog.
- The package bundles Studio and the bridge at matching versions, so a page never talks
  to a Studio from another release.
- Published from GitHub Actions with npm provenance, so users can verify the package was
  built from this repository.
- Tested on Linux, macOS and Windows, and on the Node LTS versions current when the plan
  is written.

## 2. The pairing system: the new Composer (approved)

**One editing model.** The pairing system and single-element tweaks write to the same
type-system file. A tweak to one element (today's Live App inspector) becomes an
**exception** rule in that file, under its role. There is one file and one preview. An
existing `fontkit-overrides.css` from v0.2 is offered for import once, as exceptions,
and then retired; nothing is imported without the user confirming.

**Principle: what you preview is the file.** The live preview applies exactly the CSS
that will be written, as one stylesheet the bridge owns. It does not set inline styles
per element. This is safe with React (rules bind by selector, so re-renders and hot
reloads cannot wipe them), cannot drift from the output, and undoes cleanly by removing
the stylesheet.

1. **Detect.** The bridge groups the page's visible text into the text styles in use
   (family, size, weight, case, tracking), with element counts, sample text, shared
   class names and near-duplicates flagged.
2. **Roles.** Each group becomes a role with a suggested name. The user renames,
   merges or splits roles by clicking elements. A `data-design-role` attribute
   overrides the grouping. Every role shows the selector it will write.
3. **Framework adapters** choose names, selectors and output targets:

   | Detected | Behaviour |
   |---|---|
   | Bootstrap 5 (`--bs-body-font-family` on `:root`) | Role names from Bootstrap classes (`.display-*`, `.h1`-`.h6`, `.lead`, `.small`, `.btn`, `.nav-link`, `.navbar-brand`, `.card-title`, `.form-label`). The body pairing sets Bootstrap's own variables (`--bs-body-font-family`, `--bs-font-sans-serif`, `--bs-font-monospace`). Headings get rules on `h1, .h1, ...`, because Bootstrap 5 sets the heading family in Sass, not a CSS variable. The adapter detects the version and does not assume one. |
   | Bootstrap 4 and older | Plain selector rules. |
   | Tailwind | Role CSS plus a theme export (section 3). |
   | React, any styling | Selectors prefer stable class names and `data-design-role`; hashed CSS-module class names are flagged as unstable. |

4. **Choosing fonts.** The picker covers:
   - the full Google Fonts catalogue, from a snapshot bundled with each release (search,
     category filters, variable axes, available weights), so browsing works offline and
     nothing is requested until a font is previewed (global rule 7, D028);
   - the fonts the page already loads, including self-hosted brand fonts, which can be
     used in a pairing but are labelled "licence unknown" unless identified;
   - Adobe Fonts with the user's own kit, as today.
5. **Candidates.** Up to three pairings (A, B, C), switched with keys `1` `2` `3` on the
   real page. A candidate is roles mapped to family and weight, plus a type scale.
6. **Type scale.** A base size and a ratio (1.125 to 1.618), or fluid between two
   viewport widths. Detected roles snap to the nearest steps; changing the ratio
   re-flows the page.
7. **Guardrails** (warnings, never blocking): body under about 16px; lines over about
   75 characters; contrast; line height out of range; synthetic bold or italic; total
   font weight in KB.
8. **Honest preview.** If a role's rule loses to the app's own CSS, fontkit says so, for
   example "Body: 6 of 42 elements kept their old font; overridden by `.card p`".
9. **More than one page.** The file applies to the whole site, so roles are built from
   every page and route visited in the session (SPA route changes included). Each role
   shows the pages it was checked on and warns that other pages are unchecked; a selector
   that matches elements of a different style on another visited page is flagged.
10. **Security.** Studio sends structured roles (selector plus properties), never raw
   CSS. The bridge builds the stylesheet itself, validating selectors with the hardened
   selector grammar and values with the existing validators (global rule 5).
11. **The old Composer.** Its slot canvas stays as a specimen-sheet export, and existing
   composition JSON still imports into it (global rule 8).
12. **Studio's own accessibility.** Every control is keyboard-operable with a visible
    focus, and Studio's text meets WCAG AA contrast; the frontend gate checks both.
13. **Performance.** Style detection on a page with several thousand text elements
    finishes within a budget set in the plan, without blocking the page; a test enforces
    it.

## 3. Output and handoff (approved)

### 3.1 The type-system file

One file that fontkit owns, by default `src/fontkit.css` (Vite) or a path the user picks
inside the project (proxy and script-tag setups). Layout:

1. A header comment: generated by fontkit, do not edit by hand, how to regenerate.
2. Font loading: either `@font-face` rules for the self-hosted kit (3.3) or a Google
   Fonts `@import`, with a comment saying the import contacts Google on every page view.
3. `:root` variables: one family variable per role (`--fk-font-display`), the scale
   steps (`--fk-step-0` ... `--fk-step-5`), line heights and tracking.
4. Adapter variables, for example `--bs-body-font-family: var(--fk-font-body)`.
5. Role rules on the reviewed selectors, using the variables.
6. A state block: the roles, candidates, scale and exceptions as JSON inside a comment,
   so opening fontkit again restores the session from the file in git. No separate state
   file. The block and the file carry a **format version** from the first release, and
   later releases migrate older versions.
   It is parsed as data, size-limited and validated; a malformed block is ignored with
   a message, never executed.

The app imports the file once (`import './fontkit.css'` last, or a `<link>`).
fontkit shows the exact line, copies it, and in Vite checks the module graph to report
"fontkit.css is imported by src/main.jsx" or "fontkit.css is not imported yet".

### 3.2 Writing safely

- Writes happen only through the local entry point (plugin, proxy or `serve.py`), to
  an allow-listed set of paths: the type-system file and the font folder.
- Every write shows a diff first and needs a click (global rule 6).
- If the file on disk changed since fontkit last wrote it (hash mismatch), fontkit
  refuses to overwrite and shows the difference.
- Atomic writes, size limits, no paths outside the project root, symlinks resolved
  and confined as `serve.py` does today.

### 3.3 Font kit (self-hosting)

- For OFL and Apache-licensed fonts: download the chosen families and weights as
  `woff2` into `public/fonts/` (configurable), write `@font-face` rules, and add each
  family's licence text next to the files.
- Subsets default to Latin; others are opt-in.
- Self-hosting removes the Google request from production pages, which also matters
  for privacy rules in some jurisdictions.
- Adobe Fonts are never downloaded; they are labelled "hosted by Adobe, kit required".
- Fonts the page already uses and fontkit cannot identify are labelled "licence
  unknown" and left alone.

### 3.4 Licence labels

Every family in the pairing shows its licence (OFL, Apache, commercial or unknown), its
source, and whether it can be self-hosted. The handoff (3.6) repeats them.

### 3.5 Exports for design systems

| Export | Contents |
|---|---|
| W3C design tokens | A Design Tokens Format Module 2025.10 JSON file: font families, weights, sizes (the scale), line heights and letter spacing, with aliases from roles to scale steps. |
| Tailwind v4 | An `@theme` block with `--font-*` and `--text-*` variables, so utilities such as `font-display` and `text-step-2` exist. |
| Tailwind v3 | A `theme.extend` object for `tailwind.config.js`. |
| Bootstrap (Sass) | `$font-family-sans-serif`, `$headings-font-family`, `$font-size-base`, `$h1-font-size` ... for projects that compile Bootstrap. |

### 3.6 Handoff to a developer

A "Give this to a developer" view that produces one download (a zip built in the
browser, no dependencies):

- the type-system file and the font folder;
- the chosen export (tokens, Tailwind or Bootstrap Sass);
- a short `FONTKIT.md`: what changed, the one line to add, the licences, and how to
  open fontkit again on the file.

Screenshots are not in the first version: Studio cannot capture a cross-origin page.

## 4. Testing (approved)

Global rule 8 and the AGENTS.md test rules still apply: real browsers, real cross-origin
frames, a hostile case at every trust boundary, no vacuous tests.

### 4.1 Real apps in CI

| Fixture | Covers |
|---|---|
| Vite + React (plain CSS) | `npx` runner, plugin in `vite.config`, hot reload keeping the preview, React re-renders. |
| Vite + React with CSS modules | Hashed class names flagged as unstable; `data-design-role` binding. |
| Bootstrap 5 static site, Bootstrap CSS vendored | Proxy mode in front of `serve.py`; Bootstrap adapter (roles named from classes, `--bs-*` variables); an app CSP of `script-src 'self'`. |
| Bootstrap 4 page | Fallback to plain selector rules. |
| Next.js app | Proxy mode in front of `next dev`, including its hot reload. |
| Multi-page site | Roles across visited pages; the unchecked-pages warning. |
| Large page (several thousand text elements) | The detection time budget. |

Fixtures are committed with lockfiles and installed with `npm ci` in CI. Vite major
versions to test are fixed in the plan, from what is current at that time.

### 4.2 Guarantees, each with its own test

- **Preview equals file:** the stylesheet the bridge applies and the file written to disk
  are byte for byte the same.
- **Clean undo:** removing the fontkit stylesheet leaves the page's DOM and computed
  styles as they were before.
- **Never in production:** `vite build` with the plugin produces output with no bridge
  and no fontkit stylesheet.
- **Honest preview:** an app rule that beats a role rule is reported with the element
  count and the winning selector.
- **Round trip:** reopening fontkit on a written file restores roles, candidates and
  scale from the state block.
- **Detection:** on each fixture, the detected text styles match an expected list.
- **One model:** an inspector tweak and a role change land in the same file, and the
  preview still equals the file.
- **Format version:** a file written by an older format version is migrated, and a
  newer unknown version is refused with a message.
- **Accessibility:** keyboard operation and contrast of Studio's own UI.

### 4.3 Hostile cases at the new boundaries

| Boundary | Hostile cases |
|---|---|
| Proxy | Non-loopback target refused; a wrong `Host` header (DNS rebinding); path traversal through the proxy; the bridge only added to `text/html`; the app's CSP header passed through unchanged; oversized responses; WebSocket (hot reload) passed through untouched. |
| Write endpoint (Node and `serve.py`) | Missing or wrong per-run token; wrong `Origin`; a path outside the allow-list; a symlink escape; a file edited by hand since the last write (refused); oversized body. |
| State block | Malformed, oversized or hostile JSON is ignored with a message and never executed. |
| Role stylesheet | Hostile selectors and values sent by a fake Studio are rejected by the bridge, which builds the CSS itself. |
| Font catalogue and page fonts | Hostile family names and URLs from the page are shown as text only and never loaded unless allow-listed. |

### 4.4 The friction test

A gate check runs the one-command setup on the Vite + React fixture and measures the time
until Studio shows the page connected, with no manual step. It fails if any step needs a
person or the time exceeds a budget set in the plan. This keeps "little setup" true.

### 4.5 The Node package

Unit tests use Node's built-in test runner, so the package keeps zero dependencies. A test
fails if `package.json` gains a runtime dependency (D030).

## 5. Build order (approved)

Each release has its own plan, branch and pull request from `main`, after PR #1 merges.
Status and plan links per release: [roadmap ledger](../plans/2026-10-03-roadmap.md).

| Release | Scope | Why this position |
|---|---|---|
| R1 One command | The Node package: Vite runner, `vite.config` plugin, proxy mode, the per-run token, the dev-only refusal, connection to the existing Studio; the release pipeline (1.1). Real-app fixtures and the friction test in CI. | Lowest friction first, so the owner can try fontkit on real apps immediately. Every later release is tested on these fixtures. |
| R2 Engine | Text-style detection (with the performance budget and multi-page roles), the bridge-owned role stylesheet and its protocol messages, framework adapters (Bootstrap 5 and 4, React), the honest-preview reports. | The pairing UI needs it; it is testable on the R1 fixtures without new UI. |
| R3 Pairing system | The new Composer: font picker with the catalogue snapshot, roles, candidates A/B/C, type scale, guardrails, exceptions from the inspector, Studio accessibility; the old canvas as the specimen-sheet export with JSON import kept. | Built on R2. |
| R4 Output and handoff | The type-system file with versioned state block, safe writes with diff and hash check (Node and `serve.py`), import of v0.2 overrides as exceptions, exports (tokens, Tailwind v4 and v3, Bootstrap Sass), the font kit, licence labels, the handoff zip. | Turns a chosen pairing into code the user keeps. |
| R5 Extension | The browser extension for non-developers: side panel, any live site, the same engine and pairing system, output as the handoff zip. See [browser-extension.md](../roadmap/browser-extension.md). | Brings in the second user soon after the product is complete, reusing everything above. |
| Later | "Promote to source" (C); source rewriting (B), after global rule 1 is amended. | Owner priority: A first, then B and C. |

## 6. Open decisions

Answered on 2026-10-04: 1 by D040 (`fontkitstudio`), 2 by D046
(in principle) and 3 by D041 (`fontkit-studio.html`). The reasons are in
`docs/implementation/deviations.md`; the arguments below are kept as the record.

1. **Package and command name.** `fontkit` on npm is an unrelated font engine with millions
   of weekly downloads, so `npx fontkit` would run the wrong package. Options: a scoped name
   (`@pterw/fontkit`, run as `npx @pterw/fontkit`) or a distinct name (for example
   `fontkit-studio`, if free when checked). The product name may also be worth revisiting,
   since search results for "fontkit" are dominated by that engine.
   Owner proposal (2026-10-03): `fontkitstudio`, run as `npx fontkitstudio`. It and
   `fontkit-studio` were both unregistered on npm that day. Confirm, and register the
   name, when the R1 plan is written.
2. **Where the specimen canvas lives** once the pairing system replaces the Composer's
   main view: a tab inside the Composer, or a separate "Specimen" mode.
3. **Studio's file name and version label.** R1 bundles Studio in the package, which is
   the natural point to replace `font_kit_studio_v0.1.1.html` and the `v0.1.1` label
   (D009, D009a) with a versionless name and the real version.
