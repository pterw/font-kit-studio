# Implementation progress

Plans: `docs/plans/2026-09-30-v0.1.1-responsive-rows.md` (complete), `docs/plans/2026-10-02-v0.2.0-live-preview-code-sync.md` (complete). Decisions and deviations: `deviations.md`. Task reports and reviews: `tasks/`.

## Current state

- **v0.2.0 and its known-limit fixes are merged** (PR #1 and PR #2, 2026-10-03; `main` at a6d2751). Next, on `ccr-9eab25c9-mgatzt` restarted from `main`: the fit-and-finish pull request listed in `audit-2026-10-03-first-run-and-controls.md` (scope awaits the owner's go-ahead; how the owner launched the demo decides which first-run fix leads), including D035 (an import while linked keeps the imported tokens). Branch `wip/addendum-7` is obsolete; the owner deletes it in the GitHub UI.
- **Next release.** The typography system design is approved: `docs/specs/2026-10-03-typography-system-design.md` (releases R1 one command, R2 engine, R3 pairing system, R4 output and handoff, R5 extension). Its R1 plan follows the fit-and-finish pull request; the proposed package name is `fontkitstudio` (design section 6). Open owner decisions are listed in the design's section 6 (package name, Studio file name, specimen canvas location).
- **Evidence.** 517 tests pass in Chromium locally; Firefox runs in CI only and is advisory (D029).

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

- **Review fixes (PR #1).** External review findings, each reproduced with a failing test first and independently reviewed:
  - Studio and bridge state: synced CSS keeps rules for auto-discovered targets whose selectors use `>` and escaped class names, with a linear-time selector check that hostile targets cannot stall. Reapply removes target-only composition tokens (a `null` token value now removes an override) and reports success only when the target matches Studio. Every timed-out request stays tracked until its late reply, and a late rejection is shown to the user.
  - Tooling: the dev server no longer follows symlinks out of the repository or to hidden files. The logo check's CSS/URL scans are case-insensitive and its contrast judgement honours a colour's own alpha. The commit check no longer flags human names such as "Claude Proctor" while still catching model names. An empty or unknown `FKS_ENGINES` is an error. The gate's font measurement runs under one shared 15 s deadline, so a font load that never answers counts as missing and the retry and FAIL reporting still run (worst case about 109 s per online run). Colour parsing in the contrast checks (Python and in-page) reads numbers in exponent form, which Chromium uses for tiny channels and alphas. With the studio on port 80 the dev server accepts the port-less Origin browsers send. The screenshot script polls its waits on an interval so an offscreen frame cannot stall it.
  - Promoted targets: when an auto-discovered element gains a `data-design-id`, its edits, originals and change-order place move to the new id, and its manifest carries `previousId`. Studio re-keys a saved override under that old id without sending anything to the page; a `previousId` naming a target still on the page is ignored. Known limits (author-to-author renames carry edits with the element; removing the attribute is not noticed) are in the task report.
  - Repeated construction: once a Studio has talked to the bridge, a second `new FontKitBridge(...)` returns it; only an `allowedOrigins` list that narrows the policy is applied, dropping a Studio that is no longer allowed. An unconnected or disposed bridge is replaced, so hot-reload options apply.
  - Author ids with CSS-special characters keep their rules: the bridge writes `; { } < > ( ) / * !` and control characters as CSS escapes, Studio's selector grammar accepts them, and CSS comments neutralise `/*`, `*/`, `<` and `>`.
  - 434 tests (Chromium); records in `tasks/v02-review-fixes-*.md`.
- **Addendum 7, known-limit fixes (2026-10-03).** Each item reproduced with a failing test first, then independently reviewed (`tasks/v02-addendum-7-review.md`: Approved with fixes; the fixes were re-reviewed and approved):
  - DOM moves survive a reload: Studio saves them as `live.structure` and Reapply replays them after its resets. Only a user's DOM move enters the saved order; a reset, a connect or Accept never adopts a container the page reordered by itself (stricter than the review's R2 suggestion, which kept adoption on connect, because a composition sync reorders containers too). A container is replayed only while it still holds a saved child, and failures name the step and say what was already applied.
  - The reconnect banner explains 0 live edits after a sync and says Accept replaces saved overrides, tokens and DOM order; a removed author id moves the edit to an auto id with `previousId`; a late acknowledgement no longer moves the selection off the user's pick (`requestId` on `design:select`).
  - Origins compare without case and `initFontKitBridge` narrows a running bridge; Composer tracking arrives in thousandths of an em; composition updates carry `fontStylesheets`, sent only after the free-fonts ask, and imported or applied documents wait for the ask too (D031, D032).
  - Review found and fixed: page-only containers saved by a reset, Reapply undoing its own saved move (hidden by the fake's visual-order `orderIds`), a saved export its own import refused, status lines that promised a restore, imported fonts reaching Google before the ask, and test gaps shown by surviving mutations.
  - 517 tests (Chromium; Firefox not run here); offline frontend gate OK; the online free-fonts check could not run here (the gate's browser has no proxy) and runs in CI. Decisions D020 (extended), D021 (closed), D031, D032, D033.
- **PR #2 review fixes (2026-10-03).** Codex: pressing Load free fonts after a linked Composer sync now re-sends the composition with its stylesheets; consent alone still sends nothing to an unlinked page (Rule 6). Reviewed in `tasks/v02-addendum-7-review.md`; 519 tests (Chromium).
  - Copilot findings, each reproduced first and fixed test-first:
    - A reset of an unrelated element no longer overwrites or drops a saved DOM order after the page changed it in session; Studio keeps the saved order and shows the banner.
    - A DOM move made while the banner is open is not saved when it would put an element in two saved containers or exceed 100 containers, and the status says so.
    - `initFontKitBridge` narrows the allow-list even when given back the options object the bridge was built from.
    - The banner no longer promises a smaller CSS file, or 0 live edits, for text-only saved edits.
    - Selections Studio makes for the user are tracked like its own refreshes, so a late reply cannot override a newer page click.
  - One builder now sets a composition's complete stylesheet set for Sync, linked edits, the consent re-send and Reapply, so a streamed edit no longer releases a saved token's font.
  - A real Studio + real bridge test covers Load free fonts after a linked sync. Limits recorded in D034.
  - A reset whose reply names the element's container no longer drops a saved container the page restored since the last reply (the fake target's `resetNamesTarget` switch covers it). The banner heading now says what raised it: a reconnect, the page changing a saved DOM order, or an import.
  - 548 tests (Chromium; Firefox not run here); offline frontend gate OK.
