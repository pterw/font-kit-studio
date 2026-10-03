# Design: fontkit typography system (pairing, output, low-friction setup)

Status: **draft.** Sections 1 and 2 are approved by the owner (2026-10-03).
Section 3 is proposed and awaits approval. Sections 4 and 5 are not written yet.
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

Decided output order: **A** (a generated type-system file the app imports) first;
**B** (rewriting source) and **C** (a reviewed "promote to source" patch) later, tied.
B conflicts with global rule 1 as written; the rule is amended before B is built.

## 1. Starting fontkit (approved)

Goal: one command, no edits to the project, nothing written until the user confirms.

| Project | Command | What happens |
|---|---|---|
| Vite (React or any Vite app) | `npx fontkit` | Runs the project's own Vite through its JavaScript API with the fontkit plugin added in memory, then opens Studio connected to the app. No config edit, no script tag. Stopping the command removes fontkit. |
| Any other local dev server (Bootstrap on WordPress, Rails, Django, PHP, static) | `npx fontkit http://localhost:8000` | **Proxy mode.** A loopback proxy in front of the existing dev server adds the bridge to HTML responses. The bridge is served from the app's own origin, so a `script-src 'self'` policy still allows it. Only `localhost` and loopback targets are accepted. |
| Permanent Vite setup | `fontkit()` in `vite.config` | fontkit starts with the normal `npm run dev`. |
| Anything else | script tag, or `python scripts/serve.py` | Unchanged from v0.2. |

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

## 2. The pairing system: the new Composer (approved)

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

4. **Candidates.** Up to three pairings (A, B, C), switched with keys `1` `2` `3` on the
   real page. A candidate is roles mapped to family and weight, plus a type scale.
5. **Type scale.** A base size and a ratio (1.125 to 1.618), or fluid between two
   viewport widths. Detected roles snap to the nearest steps; changing the ratio
   re-flows the page.
6. **Guardrails** (warnings, never blocking): body under about 16px; lines over about
   75 characters; contrast; line height out of range; synthetic bold or italic; total
   font weight in KB.
7. **Honest preview.** If a role's rule loses to the app's own CSS, fontkit says so, for
   example "Body: 6 of 42 elements kept their old font; overridden by `.card p`".
8. **Security.** Studio sends structured roles (selector plus properties), never raw
   CSS. The bridge builds the stylesheet itself, validating selectors with the hardened
   selector grammar and values with the existing validators (global rule 5).
9. **The old Composer.** Its slot canvas stays as a specimen-sheet export, and existing
   composition JSON still imports into it (global rule 8).

## 3. Output and handoff (proposed)

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
6. A state block: the roles, candidates and scale as JSON inside a comment, so opening
   fontkit again restores the session from the file in git. No separate state file.
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

## 4. Testing (not written yet)

To cover: real React + Vite apps and a real Bootstrap 5 page in CI; both entry points;
hostile cases at every new boundary (proxy targets, the write endpoint, the state block,
role selectors); the "preview equals file" guarantee byte for byte.

## 5. Build order (not written yet)

To be proposed after sections 3 and 4 are approved.
