# R5 Extension: implementation plan (outline)

Status: **outline** (2026-10-03). Completed, then approved by the owner, after R4 merges and
roadmap decisions 7 (build step, permissions) and 8 (transport) are taken.
Design: [typography system design](../specs/2026-10-03-typography-system-design.md),
section 5; technical sketch and open questions:
[browser extension](../roadmap/browser-extension.md).

## Goal

Someone with no terminal, Node or local project can open any live site, try pairings with
the same engine and pairing system, and download the handoff zip for a developer.

## Scope

In: a Manifest V3 Chrome extension with a side panel; the bridge injected into the active
tab on click (`activeTab`, `scripting`, `sidePanel`); the R2 engine, R3 pairing system and
R4 handoff zip reused; a privacy statement and a minimal permission list for store review.

Out (first version): sync to a file; arranging elements; remote scripts; Firefox (decided
after the Chrome version exists).

## Contract to write first

The transport (decision 8). The bridge today trusts `design:hello` only from its parent or
opener; a side panel is neither. The chosen channel, its origin and session pinning, and its
hostile cases are specified and approved before any code.

## Tasks (coarse)

- [ ] **R5.1 Transport.** Implement decision 8 with hostile-input tests equal to the
  existing boundary's.
- [ ] **R5.2 Panel build.** Studio's pairing UI with its script in separate files (MV3 bans
  inline scripts), per decision 7.
- [ ] **R5.3 Injection and cleanup.** Inject on click; clear message on pages that block
  injection; session dropped on navigation.
- [ ] **R5.4 Real-site checks.** Strict `font-src` and `style-src` sites, frames, Chrome's
  own pages; "works on any site" is claimed only for what was tested.
- [ ] **R5.5 Store package.** Privacy statement, permission justification, listing assets.
- [ ] **R5 release point.**

## Exit criteria

- The panel edits a live tab on the R1-R4 fixtures served from a real origin and on a set of
  public sites named in the completed plan.
- A forged message from the page or another extension is rejected.
- No network request leaves the extension except the font stylesheets the user chooses.

## Risks

- Page security policies block injected fonts or styles. Mitigation: R5.4 before any claim.
- Store review. Mitigation: `activeTab` only by default; optional host permissions only per
  site, if decision 7 allows them.

## Ledger

| Date | Event |
|---|---|
| 2026-10-03 | Outline written from the approved design and the extension sketch. |
