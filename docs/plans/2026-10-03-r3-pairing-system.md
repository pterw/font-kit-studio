# R3 Pairing system: implementation plan (outline)

Status: **outline** (2026-10-03). Completed, then approved by the owner, after R2 merges.
Roadmap decision 6 is taken in principle (D046: the specimen canvas is a Composer tab fed by
the pairing's roles) and is confirmed with a mockup in this plan.
Design: [typography system design](../specs/2026-10-03-typography-system-design.md),
section 2 items 4-7, 11, 12.

## Goal

The new Composer: choose fonts for each role, compare up to three pairings on the real page,
snap the page to a type scale, and see readability warnings while editing. This is the
release that makes fontkit worth choosing over a font-swap extension.

## Scope

In: the font picker (Google Fonts catalogue snapshot bundled per release, the page's own
fonts labelled "licence unknown", Adobe Fonts with the user's kit); roles from R2 with
rename, merge and split by clicking; candidates A, B and C switched with keys 1, 2, 3; the
type scale (ratio 1.125 to 1.618, or fluid between two widths); guardrails (body under
about 16 px, lines over about 75 characters, contrast, line height, synthetic bold or italic,
total font weight in KB); inspector tweaks become exceptions under their role; Studio's own
accessibility (keyboard, focus, WCAG AA contrast); the old slot canvas kept as the
specimen-sheet export, with composition JSON import kept (global rule 8).

Out: writing the type-system file (R4).

## Tasks (coarse)

- [ ] **R3.1 Catalogue snapshot.** Build step for the bundled Google Fonts metadata; offline
  search and filters; nothing requested until a font is previewed (Rule 7, D028).
- [ ] **R3.2 Roles UI.** List, rename, merge, split by clicking on the page; show each
  role's selector.
- [ ] **R3.3 Candidates.** Three pairings, keyboard switching on the real page.
- [ ] **R3.4 Type scale.** Ratio and fluid modes; roles snap to steps; re-flow on change.
- [ ] **R3.5 Guardrails.** Warnings only, never blocking; each with a test on a fixture.
- [ ] **R3.6 Exceptions.** The Live App inspector writes exceptions under roles (one
  editing model).
- [ ] **R3.7 Specimen canvas.** A Composer tab rendering the pairing's roles (D046); old JSON still imports.
- [ ] **R3.8 Studio accessibility.** Keyboard operation and contrast, enforced by the
  frontend gate.
- [ ] **R3 release point.**

## Exit criteria

- Candidates A, B and C switch on every fixture with the honest-preview counts shown.
- A scale change re-flows the page and roles land on the nearest steps.
- Each guardrail fires on a fixture built to trigger it and stays quiet otherwise.
- v0.1.1 and v0.2 composition JSON still import.
- Studio passes its own keyboard and contrast checks in the frontend gate.

## Open questions

1. The mockup that confirms D046: how canvas slots bind to roles.
2. Whether the Studio single-file rule (global rule 8) still fits a UI this size; any change
   needs an owner ruling before the plan is approved.

## Risks

- Largest UI change so far, inside one HTML file. Mitigation: split into function-disjoint
  tasks with their own test modules; consider the single-file question above early.
- Catalogue snapshot size. Mitigation: metadata only, fonts fetched on preview.

## Ledger

| Date | Event |
|---|---|
| 2026-10-03 | Outline written from the approved design. |
