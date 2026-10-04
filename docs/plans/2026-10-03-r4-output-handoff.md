# R4 Output and handoff: implementation plan (outline)

Status: **outline** (2026-10-03). Completed, then approved by the owner, after R3 merges.
Design: [typography system design](../specs/2026-10-03-typography-system-design.md),
section 3 and section 4.2.

## Goal

Turn a chosen pairing into files the user keeps: one type-system file the app imports, a
self-hosted font kit with licences, design-system exports, and a handoff zip for a
developer.

## Scope

In: the type-system file (default `src/fontkit.css`) with header, font loading, `:root`
variables, adapter variables, role rules and a versioned JSON state block; safe writes with
diff, click and hash check through the Node entry and `serve.py`; import of v0.2
`fontkit-overrides.css` as exceptions, once, with confirmation; exports (W3C design tokens,
Tailwind v4 and v3, Bootstrap Sass); the font kit (woff2 for OFL and Apache fonts, licence
files, Latin subset by default); licence labels; the "Give this to a developer" zip with
`FONTKIT.md`; the Vite module-graph check that says whether the file is imported.

Out: source rewriting and "promote to source" (Later).

## Tasks (coarse)

- [ ] **R4.1 File format.** Layout, format version, state block parser with size limits;
  hostile and malformed blocks ignored with a message.
- [ ] **R4.2 Preview equals file.** The bridge applies exactly the bytes that will be
  written; a byte-for-byte guarantee test.
- [ ] **R4.3 Safe writes.** Allow-listed paths, diff then click, hash check refusing a
  hand-edited file, atomic writes, symlink confinement; in both Node and `serve.py`.
- [ ] **R4.4 v0.2 overrides import.** Offered once as exceptions, then retired.
- [ ] **R4.5 Exports.** Tokens, Tailwind v4, Tailwind v3, Bootstrap Sass, each with a
  fixture test.
- [ ] **R4.6 Font kit and licences.** Download, subset choice, `@font-face`, licence text;
  Adobe never downloaded; unknown fonts left alone.
- [ ] **R4.7 Handoff zip.** Built in the browser with no dependency; `FONTKIT.md`.
- [ ] **R4.8 Round trip and migration.** Reopen from the state block; migrate an older
  format; refuse a newer unknown one.
- [ ] **R4 release point.**

## Exit criteria

All guarantees in spec section 4.2 that concern output pass on every fixture: preview equals
file, round trip, one model, format version; plus the write-endpoint hostile cases in 4.3.

## Open questions

1. Zip building without dependencies: a minimal stored (uncompressed) zip writer, or
   deflate via `CompressionStream`. Proposal: `CompressionStream` where available.
2. Default font folder per project type.

## Risks

- Writing into a user's project is the highest-stakes action fontkit takes. Mitigation:
  Rule 6 tests at every write path, and the hash check from the first version.
- Licence data accuracy. Mitigation: licences come from the catalogue metadata; anything
  not identified is labelled "unknown", never guessed.

## Ledger

| Date | Event |
|---|---|
| 2026-10-03 | Outline written from the approved design. |
