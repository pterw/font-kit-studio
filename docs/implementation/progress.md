# Implementation progress

Plans: `docs/plans/2026-09-30-v0.1.1-responsive-rows.md` (complete), `docs/plans/2026-10-02-v0.2.0-live-preview-code-sync.md` (complete). Decisions and deviations: `deviations.md`. Task reports and reviews: `tasks/`.

## Current state

v0.1.1 is complete. The v0.2.0 plan is complete: live preview of a target page, the Live Target inspector, the code panel with copy, download and sync, arrange with guards, pop-out, free fonts, end-to-end tests and the README. The CI workflow and the frontend gate (Task H) are complete; Studio makes no third-party request until the user loads free fonts (D028). Chromium is verified locally (342 tests, gate 0 enforced failures offline); Firefox is first verified in CI (D010). Open polish items from the final review are listed in `final-review-v0.2.md` (I2, M1-M9).

## Recovery

Read this record and `deviations.md`, then `git log` and `git status`. Completed tasks are not repeated. Full briefs, reports, review packages and verdicts live in `docs/implementation/tasks`. The source tag `supplied-v0.1.1` is the original input, not an independently verified release.

## v0.1.1

The supplied HTML already implemented rows, so the work characterized existing behaviour and fixed actual defects (D001). Every task was independently reviewed. The final suite is 20 browser tests in Chromium and Firefox (`verification.md`).

- **Task 1, row model and selection.** Fixed fractional row counts, hidden descendants retained after a row shrinks, and the version mismatch.
- **Task 2, row rendering.** Fixed row alignment (start, center, end) by removing a forced child height. Weighted 2-4 column tracks, gap, source order and the container-width collapse boundaries (679/680/681) are covered; the layout follows the canvas width, not the nominal width.
- **Task 3, row inspector.** Fixed the breakpoint field showing a value the model had clamped, and associated row labels with their controls. Covered real keyboard entry, upper bounds, leaf controls, child summary and breadcrumb, and top-level reorder.
- **Task 4, import, export and images.** Fixed a crash on numeric roles, role/property CSS collisions, a metadata data-URL leak, acceptance of malformed slot and background data, a delayed image read updating the wrong slot, and an explicit empty kit list not round-tripping. Candidate state is validated before it is published, so a rejected import leaves the previous state intact.
- **Task 5, final verification.** Added Library and dynamic-ID acceptance, screenshots and the verification evidence; no product fix was required.
- **Verification tooling.** `scripts/verify.py` (static checks, provenance, full suite) and `requirements-dev.txt`.

## v0.2.0

Every implementation task was independently reviewed. Final suite on Chromium: 201 tests (bridge 83, v0.1.1 20, integration 16, preview server 18, Studio live 64).

- **Task A, preview server and demo.** `scripts/serve.py` (two loopback ports, status endpoint, atomic overrides write) and an offline demo target page. Defects found and fixed: no Host-header check (DNS rebinding), an empty reply when the write failed, no socket timeout, and a path check on the raw request path. Final: 18 server tests.
- **Task B, bridge runtime and change ledger.** Protocol v1 with origin and session pinning, validated atomic patches, revisions and a change ledger. Defects found and fixed: the restore-text crash, original text recaptured on rediscovery, click interception without a connected Studio, and no origin or session gating. Review also found script execution through legacy SVG placement (now `<img>` data URLs only), an `allowedOrigins` option defeated by auto-init, and broken base64 SVG. Final: 33 bridge tests.
- **Task C, Studio client, Live Target inspector and code panel.** Origin and session gating, status badge, `?target=` auto-connect, select/interact modes, Studio-owned overlays, CSS/HTML/JSON tabs with copy, download and sync, JSON `live` field, reconnect banner. Defects found and fixed: spoofed `applied` messages accepted, composition broadcast on connect, `?target=javascript:` executing in Studio's origin, a keystroke size bug, auto-sync shrinking the overrides file, and composition tokens dropped after a reload. Final: 49 tests (29 Studio live, 20 v0.1.1).
- **Task D, integration and README.** Real Studio, bridge, demo and server driven end to end, the README with logo, workflows, integration recipes and protocol tables, and the MIT license. Defects found and fixed: pop-out opened a tab instead of a window, unused `design:inspect` and `design:ping` messages, inconsistent token rules between Studio and bridge, unguarded `localStorage`, and the anti-recursion check under loopback aliases. Final: 201 tests across the suite.
- **Task E, bridge arrangement and fonts.** `design:move` with DOM and CSS-order strategies, move guards (form owner, radio group, label/aria references, content model, framework-managed), runtime-error warnings, pop-out overlay, font stylesheets with a strict URL allow-list, SPA and HMR robustness. Defects found and fixed: quadratic bulk manifests (8.36 MB on a 718-target page, now linear), arrangement-only targets cleared on rediscovery, and hit-testing that selected whole lists. Final: 101 tests (83 bridge, 18 server).
- **Task F, Studio arrange UI, pop-out and free fonts.** Arrange section with strategy toggle and guard messages, pop-out window with dock, 16 free OFL fonts with Adobe as opt-in, saved tokens and css-order moves in the `live` field. Defects found and fixed: Reapply dropped the font stylesheet, reset-then-replay was not transactional (a rejected follow-up emptied the overrides file), DOM-move undo was silent, and Alt+Left/Right was hijacked. Final: 182 tests at the time (the full suite later reached 201).
- **Task G, README logo.** Light and dark outlined SVG wordmarks from OFL fonts, with licences in `docs/assets/README.md`; contrast checked on light and dark GitHub backgrounds. Docs-only asset, no tests.
- **Task H, CI and frontend gate.** Quality Gate workflow (static checks, commit-message check, frontend gate, full suite in Chromium and Firefox) and the fontkit frontend gate: network isolation, free fonts with bounded retry, overflow, initial visibility, live edit on every profile, logo paint, contrast on v0.2 surfaces, touch targets as report-only. Fixed four contrast defects on v0.2 surfaces and made Studio silent until the user asks for free fonts. The commit check rejects AI-tool signatures and allows human co-authors. 342 tests; independently reviewed. The first CI run (Chromium and Firefox) found that the demo header overflowed a phone-width preview in Firefox, whose font metrics are wider; the header now wraps on narrow screens.

## v0.2.0 release-point checks

- Sweep: `sweep-v0.2.md` (dead code, contract drift, stale docs; Must-fix items M1-M3 resolved).
- Final whole-branch review: `final-review-v0.2.md`, "Ready with notes".
- Gate evidence: `verification-v0.2.md` (static checks, provenance, 201 tests, bridge syntax check, Studio and demo smoke at 1440x900 and 390x844).
- Code-review handoff: `handoff-code-review-v0.2.md`.
