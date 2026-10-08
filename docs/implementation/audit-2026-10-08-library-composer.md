# Audit: Library and specimen Composer (2026-10-08)

Read-only observations of released 0.3.1 runtime on `docs/library-composer-audit`,
HEAD `142aa9dc0273efc19e14a67d88f66726b6d665ae` (merged work order PR #17).
The [approved brief](tasks/r2-task-audit-brief.md) owns scope. This report informs
[R2 prerequisites](../plans/2026-10-03-r2-engine.md#approval-and-prerequisites)
and [R3](../specs/2026-10-03-typography-system-design.md#2-the-pairing-system-the-new-composer-approved).
No product changes, tests, source writes or implementation approval result from it.

## Result and evidence limits

The existing Library, three specimen presets, five slot kinds, rows, manual JSON
round trip, token export and acknowledged live Changes output are reachable and
functional in the exercised paths. The most consequential existing issues are
invisible newly added text on the default light sheet, missing accessible names
on inspector controls and no keyboard route for choosing another canvas slot.
The future pairing, catalogue and output model remain future design gaps.

**The initial HTTPS isolation setup failed.** Its Playwright string glob
`https://**` did not match font stylesheet URLs. Initial consent actions reported
16/16 loaded, with zero requests intercepted. Third-party contact may have
occurred; actual network request/byte counts were not logged and are unknown.
No credentials were entered. These loaded/consent-dependent observations are
superseded, not treated as offline or privacy evidence. See D059 in the
[decisions](deviations.md). Pre-consent control evidence uses system fallbacks.

The installed matcher converts that glob to `^https://((.+/)|)$`; a real-shaped
`https://fonts.googleapis.com/css2?...` returns `url_matches=False`. The corrected
regex `^https://` returns true. The controller's independent local-fulfillment
reproduction is [route-guard-evidence.json](../../.superpowers/sdd/r2-audit/route-guard-evidence.json),
with [probe-route-guard.py](../../.superpowers/sdd/r2-audit/probe-route-guard.py).
The audit's [guard-diagnosis.json](../../.superpowers/sdd/r2-audit/guard-diagnosis.json)
records the installed matcher result. No production harness was changed.

`guarded_fonts` rechecks desktop and phone consent, remembered reload, mode
transitions and retry in fresh contexts. Each context first navigates a separate
probe page to harmless `https://audit.invalid/guard`; the regex aborts it and
`blocked_delta=1` is asserted before Studio navigation. Closing that page avoids
an asynchronous browser error-navigation race. Request and abort records are in
[guarded_fonts-evidence.json](../../.superpowers/sdd/r2-audit/guarded_fonts-evidence.json)
and its cleanup record. It intercepted 79 HTTPS attempts: two harmless probes
and 77 font stylesheet attempts across loads, reloads and retries. All font
loads in this accepted rerun failed visibly with system fallbacks. A blanket
zero-third-party-contact claim for the whole audit is not supported.

Exact supersession: `library` states `consent-blocked`, `consent-reload`,
`1440-transition`, `1440-return`; `composer2` states `fonts-blocked`, `1440-final`,
`1440-reload`. `followup/fonts` also yields to the rerun with the pre-navigation
probe. The complete state table marks these rows. Other Library controls were
visited before consent; Composer's complete desktop controls precede its final
Load action, and its phone context is fresh. No accepted conclusion depends on
the incorrectly loaded font shapes.

## Baseline, setup and commands

Windows; Python 3.13; existing Playwright Chromium 151.0.7922.34. Profiles:
1440 x 900 desktop and 390 x 844 narrow phone viewport, with no touch/device
emulation claim. No browser, package or CLI was installed. Agent-browser was
unavailable on PATH; the approved existing Playwright fallback was used.

Scratch Python used `tests/support.py:new_context/shared_runtime`, one driver
per process. It imported existing `scripts/serve.py:Config/make_server`, created
two loopback servers on port 0, assigned their distinct resulting ports to the
config, and set `sync=False` (the `--no-sync` behavior). The CLI rejects two
literal zero ports as equal before binding; direct use of its existing factory
avoids changing source. No write endpoint was exercised. Specimen sync edited
only ephemeral demo browser DOM; import/download fixtures remained in scratch.

Executed commands were `python .superpowers/sdd/r2-audit/audit_runner.py <phase>`
for recon, library, composer, composer2, boundaries, live, live2, followup,
followup2, guarded_fonts, material, material2 and closeout. The report generator is
`python .superpowers/sdd/r2-audit/build_report.py`. Each phase file documents
actual actions. Screenshots, JSON, downloads and measurements live under
`.superpowers/sdd/r2-audit/`; they are local scratch, not committed assets.

Some exploratory scripts stopped at deterministic assumptions: selecting a
disabled one-cut select, expecting a linked import after pop-out had ended the
link, a non-unique screenshot selector, parsing modern `color(srgb ...)` as
`rgb(...)`, and shell quoting while making follow-up files. They are audit-tool
failures, not product defects. Each partial process closed its owned resources;
complete follow-ups supply the affected inventory. A guard probe's aborted
navigation race was corrected by closing the probe page. No denied tool call
occurred. No full unittest suite, frontend gate or Firefox suite was run. Their
prior results are not counted as this audit's probes.

Graph evidence was Tier 2, project `font-kit-studio-local`, generation
2026-10-07T17:07:14Z. `list_projects` reconfirmed the checkout; parent graph
discovery/snippet/trace packet supplied the Composer entry method. Coverage
checks found runtime/support/README metadata changed and docs, scripts and
scratch excluded. Current source supplied inventory assistance; actual browser
actions and rendered measurements decide behavior. The graph's empty runtime
render search was not used to assert absence. No complete graph audit is claimed.

## Reachable inventory and absent states

| Surface | Observed semantic inventory | Absent or restricted state |
|---|---|---|
| Library entry | 16 cards, specimen text, 8-86px size, light/dark theme, font consent, optional empty Adobe kit refusal | No first-run modal, search, compound filters, empty-result route, family selection/apply action, detail dialog or user-switchable list/grid layout |
| Library filters | all16, serif5, display5, variable11, sans8, technical4, geometric2, mono3, typewriter1 | Filters are mutually exclusive; combinations and no-match search cannot be reached |
| Library families | Fraunces, Crimson Pro, Source Serif4, Playfair Display, Instrument Serif, Inter, Space Grotesk, DM Sans, Work Sans, IBM Plex Sans, Archivo, Bricolage Grotesque, Bebas Neue, JetBrains Mono, IBM Plex Mono, Space Mono | One-cut cards show no redundant Regular chip; loaded external face fidelity excluded |
| Library controls | Every exposed style chip; every exposed weight/optical-size axis; changed text, max/min size; CSS readout and computed style | Variable rendering verified as CSS/axis state with fallback metrics, not as the unavailable external face's optical design |
| Composer entry | Editorial Image+Body Row:4 top-level slots with2 row children; Blank Editorial5:5 populated text slots; Asteria Sculptural:5 populated slots | Blank is a specimen preset, not an empty canvas. Slots min1; zero coerces1. No zero-slot state |
| Text slot | 12 roles;8 element kinds;16 families; all enabled cuts and axes; size, line height, tracking,4 alignments,4 transforms, text,3 colour sources | One-cut select disabled with reason; choosing a role replaces that slot's defaults immediately |
| Nontext slots | Image placeholder/SVG/PNG/JPEG refusal, width/opacity/alignment/colour; Rule width/thickness/alignment/colour; Spacer height | JPEG refused. Image width disabled before asset. No individual remove button; Slots trims the tail |
| Row | 2/3/4 children, gap,4 align-items choices, collapse threshold, weights, child jumps, each leaf kind | Nested Row absent from child type select; no child reorder control; child count removes trailing children |
| Shared canvas |4 width options,3 colour sources,22 Tailwind families,11 shades and11 saved colours for canvas and text; up/down order; mode switch | Arbitrary Cartesian combinations and every possible string/number are not exhaustively enumerated |
| Dialogs/import | Native replace-edits confirm accept/decline; JSON/CSS dialogs; copy/download/close/Escape; valid/malformed/missing/empty JSON and chooser cancellation | Native OS file-picker/confirm pixels are not captured by page screenshot; visible outcomes and dialog messages are recorded |
| Output | Composition JSON0.1.1 round trip; CSS-token dialog and matching download bytes; Changes CSS/HTML/JSON after real bridge acknowledgement | No standalone specimen HTML/PDF/PNG export, candidates, scale, roles, guardrails, token-system handoff or font kit |
| Live boundary relevant to Composer | Connected/unsynced/synced, Specimen/Live, viewport buttons, Select/Interact, fullscreen exit, pop-out/focus/dock, linked import, reconnect Reapply/Accept | Sync/Auto-sync disabled with --no-sync reason; write behavior intentionally not visited |

Every table row in the appendix states its route/actions, viewport, screenshot
and rendered/computed result. Library shows grid responsive to viewport; phone
reflows to one card column. The specimen canvas stacks row children when its
measured width is below the chosen threshold. A deliberately lowered240px
threshold can retain columns on phone; this is the user's chosen setting.

## Ranked existing findings

### LC-01: newly added text is nearly invisible on the default sheet

**P1, confirmed desktop and phone.** Fresh Library > Composer > Slots5 > click
new Custom slot. The default Editorial canvas is rgb(245,241,232); the new text
is rgb(238,242,255), contrast **1.008:1**. Expected: new default content remains
readable in the current canvas palette. Actual: its text practically disappears.
Converting a slot/row back to Text and adding row children reproduces the same
pale default class. It is not a claim that all user-chosen colour pairs must pass.

Evidence: `material2/1440-new-slot`, `390-new-slot`, `1440-converted-text`,
`390-converted-text`; [contrast](../../.superpowers/sdd/r2-audit/1440-new-slot-contrast.json)
and phone counterpart. Source assistance: `fontkit-studio.html:2121-2144`
(`makeTextSlot` pale default), `2543-2548` (Slots adds it). Recommend **R3**,
preserving specimen behavior under design2.11; do not add a canvas redesign to R2.

### LC-02: inspector controls have no useful accessible name

**P1, confirmed in Chromium AX on desktop and phone.** Composer > select Text >
Tab through inspector. Family, Role, Element, Size, Line height, Tracking,
Transform, colour source and text controls expose unnamed combobox/slider/
spinbutton/textbox nodes. `labels=[]`, no id/for link and no aria-label confirm
the browser result. Library's axis sliders are similarly unnamed. Expected:
the visible label names the control to assistive technology. Actual: adjacent
visual text is not its accessible name. Disabled selects sometimes acquire
their long reason as a title-based name, not the field label.

Evidence: [desktop AX](../../.superpowers/sdd/r2-audit/1440-inspector-ax.txt),
[labels](../../.superpowers/sdd/r2-audit/1440-labels.json), phone counterparts,
Library AX and `boundaries/*-keyboard` screenshots. Source assistance:
`fontkit-studio.html:2845-2867` and Library axis markup `1540-1554`.
Recommend **R3 accessibility**, already designed in2.12; R2.S1/S2 must apply
its existing accessible-field contract to new role controls without repeating
this defect. This finding does not authorize retrofit work during R2.

### LC-03: keyboard cannot select another specimen slot

**P1, confirmed for the exposed default-sheet controls.** Fresh Composer > Tab
through the complete cycle (100 keystrokes). Focus reaches move buttons and
the selected Wordmark inspector, but no selectable canvas slot. The focused
movers advertise movement rather than selection; the pointer mover probe
changes order while keeping the selected slot.
Expected: a keyboard route chooses H1/Row/Metadata so their existing controls
can be edited. Actual: only pointer clicks select them. Row child jump buttons
are keyboard buttons once a row is selected, but do not provide a way to select
that row initially. Changing Wordmark's Role edits Wordmark, not the other slot.

Evidence: [focus cycle](../../.superpowers/sdd/r2-audit/390-multi-slot-focus.json),
desktop counterpart and [canvas AX](../../.superpowers/sdd/r2-audit/1440-canvas-ax.txt).
`followup/*-multi-focus`, `followup2/390-multi-focus` and material screenshots.
Source assistance: click-only wrapper handling `fontkit-studio.html:2641-2663`.
Recommend **R3 accessibility**, design2.11-2.12. Visible focus rings on the
controls that are focusable work:2px solid rgb(90,58,167), including real Tab
focus on numeric/text fields. That passing behavior does not fix selection.

### LC-04: invalid specimen colour changes rendering without a visible error

**P2, confirmed.** Text colour Custom > type `#102030` > type `oops` using
keystrokes > Tab. The field retains `oops`; the recreated preview loses the
previous rgb(16,32,48) colour and inherits rgb(24,23,20). No rendered alert or
status explains the invalid value. Expected: retain the last valid appearance
and explain invalid input. This is a usability defect, not a security escape.
Evidence: `composer2/1440-hex`, `1440-invalid-color`, phone equivalents, raw
computed preview/statuses. Source assistance: `bindSimpleInput:2800-2818`.
Recommend **R3 specimen control preservation**. Do not infer the live inspector
has the same bug; its validation path is different and was outside this probe.

### LC-05: image colour controls suggest tinting that does not happen

**P2 confusing behavior, confirmed for an SVG with its own fill.** Add Image >
upload local blue asset.svg > set mark colour `#ff0000`. The field retains
`#ff0000`; the image remains blue; the swatch stays its previous colour on this
typing path. The enabled field is labelled Text / mark colour with no
rendered limitation. Width/opacity/alignment do work. Expected: a useful label
or visible explanation of what this field affects. Actual: it affects the
empty placeholder but not this loaded asset's pixels. This matches the earlier
first-run audit's own-fill SVG concern; it is not evidence that SVG should be
parsed or rewritten. Global rule5 keeps it an image.

Evidence: `material2/*-svg-color`, `boundaries/*-asset-svg`, local fixture and
computed img widths/opacity. Recommend **R3**, clarify/disable irrelevant colour
controls while preserving safe image rendering. Raster tinting is not proposed.

## Existing behavior and future design gaps

**Changes-panel gap (R3/R4, not a broken live ledger).** With a real connected
demo, Specimen > type Wordmark shows the changed sheet, but Changes is hidden.
Live App > Changes0 still describes only acknowledged live changes. Explicit
Sync to Live App creates tokens/target changes, and CSS/HTML/JSON then render
those acknowledgements. Specimen's toolbar Export JSON contains composition;
Export CSS is labelled CSS tokens and contains variables. These are separate
from Changes outputs. The tokens do not recreate specimen text, image assets,
alignment, element structure or a full standalone sheet. Do not describe the
current Changes panel as a promised standalone Composer export. Design2.11
preserves the old sheet; design2.1/section3 plan a unified model later.

**R3 gaps:** no full bundled catalogue/search/page-font picker, role workflow,
pairing A/B/C keys, type scale, readability warnings or inline licence choices.
Library cards do carry OFL in the current notes; the gap is the future picker
and handoff labels, not absent current provenance. Library-to-Composer changes
mode only; no selected Library family is carried across. The hero suggests
assigning real roles, but current slot roles are specimen defaults, not detected
page roles. Preserve all working leaf controls and legacy JSON during migration.

**R2 acceptance relevance:** characterize existing specimen/edit/import/export
paths under R2.S2 without adding pairing UI. Detect/Apply/Clear must have visible
reasons and accessible names. Keep role-preview canonical CSS separately labelled
and out of existing exports, as the R2 plan already requires. Runtime changes
must not accidentally reveal Changes for unsent specimen state or persist drafts.

**R4/later:** specimen-sheet export, type-system file/state round trip, safe
diff-confirmed writes, licence/font kit and developer handoff belong to section3
and the agreed release order. No JPEG, nested rows, per-breakpoint editor or
source rewriting is proposed. No recommended fix enlarges this audit's scope.

## Working controls, layout and sampled contrast

Preset selection applies immediately. Untouched Apply explains no edits to
reset; accept replaces edits, decline keeps them and resets the selected preset.
The Blank option intentionally creates five populated editorial roles. Numeric
typing gives rendered line-height42px at24px x1.75 and tracking0.6px at0.025em.
Rows retain2-4 leaves; count changes trim/add the tail; top-level move up/down
restores order. Image SVG/PNG load and JPEG refusal are visible; assets are
session-local and JSON import says to reselect them. A loaded SVG's JSON omits
its data URL but keeps its name; importing it renders `asset.svg - reselect file
to preview` (with the UI's dash glyph), on both profiles. Restore Page Text
returns an explicitly edited demo H1 to its original text and disables itself.
Closing the owned pop-out gives Disconnected and disables Focus; Dock reconnects.
Manual JSON0.1.1 export/
import restores the exercised sheet, while malformed/missing-slots JSON refuses
without changing it. Empty-slots import creates one Custom slot. Reload restores
the default composition; saving a JSON is the available composition persistence.

Both export dialogs work at390px; copy feedback appears and downloaded bytes
equal displayed text. Close and Escape return to the sheet. Native dialog Tab
sequence is Close, textarea, Copy, Download, body, then Close/textarea; background
controls were not traversed in that sample. No exhaustive assistive-technology
or native OS picker test is claimed. Disabled one-cut, missing image-width,
inactive colour source and bridge-only controls carry tooltips; Sync to Live App
and Sync to file also have visible reasons. --no-sync remains visible and inert.

No horizontal document overflow was observed in the retained default/control
states at1440 or390. Row layouts collapse from canvas width, not outer viewport.
For a1440px Live App preview on390px Studio, previewScroller has width340px,
scrollWidth1440px and overflow-x:auto; the app is intentionally wider and can
be scrolled. The previous cropped-without-scrollbar defect is not reproduced.
Phone is a long stacked workflow; truncated native select labels remain
choosable. This is advisory usability context, not a failed touch-size gate.

Sampled default light inspector chrome labels/notes measure5.22:1 on their
opaque background; larger field text samples17.63:1. The transparent/modern
color-mixed navigation background was excluded from the simple RGB calculation,
so this is not a complete contrast audit. User specimen colours are editable;
LC-01 concerns an unreadable supplied default. No material Chromium observation
suggested a Gecko-specific delta needing a focused Firefox probe; Firefox was
not run. No Firefox compatibility or full WCAG conformance claim follows.

## Evidence register

The register contains **613 captured page states/screenshots**, of which
**513 are primary observations** and 100 are duplicate/partial or
superseded. These are audit probes, not automated test-suite counts.

Route shorthand: Library/Composer mean the actual visible mode buttons at
`http://127.0.0.1:<studio-port>/fontkit-studio.html`; Live phases use its
`?target=http://127.0.0.1:<target-port>/demo/` entry. Exact ephemeral URLs and
all rendered controls/options/measurements are in each phase JSON. Each table
row is a state, not an assertion that arbitrary combinations were exhausted.

Register status: P=primary; D=duplicate/partial (complete follow-up owns the conclusion); S=superseded as specified above. Screenshot cells give the full repo-relative scratch path. Recon used an incorrect `.slot` collector before it was corrected to `.flow-slot`: its zero slot/preview metrics are invalid. Complete Composer captures show4 top-level slots plus2 row children initially; no conclusion uses recon zero fields.

### recon

Raw observations: [recon-evidence.json](../../.superpowers/sdd/r2-audit/recon-evidence.json).

| State / evidence status | Viewport | Visible route and actions | Screenshot | Rendered / computed observation |
|---|---|---|---|---|
| library / D | 1440 x 900 | Fresh Studio entry | `.superpowers/sdd/r2-audit/recon-library.png` | 16 visible cards; document width1440px. |
| composer / D | 1440 x 900 | Click Composer | `.superpowers/sdd/r2-audit/recon-composer.png` | Screenshot shows4 top-level slots; zero collector fields INVALID; use composer2 initial. |

### library

Raw observations: [library-evidence.json](../../.superpowers/sdd/r2-audit/library-evidence.json).

| State / evidence status | Viewport | Visible route and actions | Screenshot | Rendered / computed observation |
|---|---|---|---|---|
| 1440-initial / P | 1440 x 900 | Fresh Library; no font consent | `.superpowers/sdd/r2-audit/library-1440-initial.png` | 16 visible cards; document width1440px. |
| 1440-filter-all / P | 1440 x 900 | Library > category all | `.superpowers/sdd/r2-audit/library-1440-filter-all.png` | 16 visible cards; document width1440px. |
| 1440-filter-serif / P | 1440 x 900 | Library > category serif | `.superpowers/sdd/r2-audit/library-1440-filter-serif.png` | 5 visible cards; document width1440px. |
| 1440-filter-display / P | 1440 x 900 | Library > category display | `.superpowers/sdd/r2-audit/library-1440-filter-display.png` | 5 visible cards; document width1440px. |
| 1440-filter-variable / P | 1440 x 900 | Library > category variable | `.superpowers/sdd/r2-audit/library-1440-filter-variable.png` | 11 visible cards; document width1440px. |
| 1440-filter-sans / P | 1440 x 900 | Library > category sans | `.superpowers/sdd/r2-audit/library-1440-filter-sans.png` | 8 visible cards; document width1440px. |
| 1440-filter-technical / P | 1440 x 900 | Library > category technical | `.superpowers/sdd/r2-audit/library-1440-filter-technical.png` | 4 visible cards; document width1440px. |
| 1440-filter-geometric / P | 1440 x 900 | Library > category geometric | `.superpowers/sdd/r2-audit/library-1440-filter-geometric.png` | 2 visible cards; document width1440px. |
| 1440-filter-mono / P | 1440 x 900 | Library > category mono | `.superpowers/sdd/r2-audit/library-1440-filter-mono.png` | 3 visible cards; document width1440px. |
| 1440-filter-typewriter / P | 1440 x 900 | Library > category typewriter | `.superpowers/sdd/r2-audit/library-1440-filter-typewriter.png` | 1 visible cards; document width1440px. |
| 1440-sample-size / P | 1440 x 900 | Type specimen text; Display size End (86px) | `.superpowers/sdd/r2-audit/library-1440-sample-size.png` | All 16 cards: specimen computed 86px. |
| 1440-min-size / P | 1440 x 900 | Display size Home (8px) | `.superpowers/sdd/r2-audit/library-1440-min-size.png` | All 16 cards: specimen computed 8px. |
| 1440-dark / P | 1440 x 900 | Click Dark mode | `.superpowers/sdd/r2-audit/library-1440-dark.png` | 16 visible cards; document width1440px. |
| 1440-empty-adobe / P | 1440 x 900 | Load kit with empty ID; no credentials | `.superpowers/sdd/r2-audit/library-1440-empty-adobe.png` | Paste a kit ID first; empty field refused. |
| family-00-cut-0 / P | 1440 x 900 | Library > all > Fraunces > Regular | `.superpowers/sdd/r2-audit/library-family-00-cut-0.png` | Fraunces: normal, weight400; axes "opsz" 72, "wght" 400. |
| family-00-cut-1 / P | 1440 x 900 | Library > all > Fraunces > Italic | `.superpowers/sdd/r2-audit/library-family-00-cut-1.png` | Fraunces: italic, weight400; axes "opsz" 72, "wght" 400. |
| family-00-axis-0 / P | 1440 x 900 | Library > Fraunces > wght slider End | `.superpowers/sdd/r2-audit/library-family-00-axis-0.png` | Fraunces: italic, weight400; axes "opsz" 72, "wght" 900. |
| family-00-axis-1 / P | 1440 x 900 | Library > Fraunces > opsz slider End | `.superpowers/sdd/r2-audit/library-family-00-axis-1.png` | Fraunces: italic, weight400; axes "opsz" 144, "wght" 900. |
| family-01-cut-0 / P | 1440 x 900 | Library > all > Crimson Pro > Regular | `.superpowers/sdd/r2-audit/library-family-01-cut-0.png` | Crimson Pro: normal, weight400; axes "wght" 400. |
| family-01-cut-1 / P | 1440 x 900 | Library > all > Crimson Pro > Italic | `.superpowers/sdd/r2-audit/library-family-01-cut-1.png` | Crimson Pro: italic, weight400; axes "wght" 400. |
| family-01-axis-0 / P | 1440 x 900 | Library > Crimson Pro > wght slider End | `.superpowers/sdd/r2-audit/library-family-01-axis-0.png` | Crimson Pro: italic, weight400; axes "wght" 900. |
| family-02-cut-0 / P | 1440 x 900 | Library > all > Source Serif 4 > Regular | `.superpowers/sdd/r2-audit/library-family-02-cut-0.png` | Source Serif 4: normal, weight400; axes "opsz" 24, "wght" 400. |
| family-02-cut-1 / P | 1440 x 900 | Library > all > Source Serif 4 > Italic | `.superpowers/sdd/r2-audit/library-family-02-cut-1.png` | Source Serif 4: italic, weight400; axes "opsz" 24, "wght" 400. |
| family-02-axis-0 / P | 1440 x 900 | Library > Source Serif 4 > wght slider End | `.superpowers/sdd/r2-audit/library-family-02-axis-0.png` | Source Serif 4: italic, weight400; axes "opsz" 24, "wght" 900. |
| family-02-axis-1 / P | 1440 x 900 | Library > Source Serif 4 > opsz slider End | `.superpowers/sdd/r2-audit/library-family-02-axis-1.png` | Source Serif 4: italic, weight400; axes "opsz" 60, "wght" 900. |
| family-03-cut-0 / P | 1440 x 900 | Library > all > Playfair Display > Regular | `.superpowers/sdd/r2-audit/library-family-03-cut-0.png` | Playfair Display: normal, weight400; axes "wght" 400. |
| family-03-cut-1 / P | 1440 x 900 | Library > all > Playfair Display > Italic | `.superpowers/sdd/r2-audit/library-family-03-cut-1.png` | Playfair Display: italic, weight400; axes "wght" 400. |
| family-03-axis-0 / P | 1440 x 900 | Library > Playfair Display > wght slider End | `.superpowers/sdd/r2-audit/library-family-03-axis-0.png` | Playfair Display: italic, weight400; axes "wght" 900. |
| family-04-cut-0 / P | 1440 x 900 | Library > all > Instrument Serif > Regular | `.superpowers/sdd/r2-audit/library-family-04-cut-0.png` | Instrument Serif: normal, weight400; axes normal. |
| family-04-cut-1 / P | 1440 x 900 | Library > all > Instrument Serif > Italic | `.superpowers/sdd/r2-audit/library-family-04-cut-1.png` | Instrument Serif: italic, weight400; axes normal. |
| family-05-axis-0 / P | 1440 x 900 | Library > Inter > wght slider End | `.superpowers/sdd/r2-audit/library-family-05-axis-0.png` | Inter: normal, weight400; axes "wght" 900. |
| family-06-axis-0 / P | 1440 x 900 | Library > Space Grotesk > wght slider End | `.superpowers/sdd/r2-audit/library-family-06-axis-0.png` | Space Grotesk: normal, weight400; axes "wght" 700. |
| family-07-cut-0 / P | 1440 x 900 | Library > all > DM Sans > Regular | `.superpowers/sdd/r2-audit/library-family-07-cut-0.png` | DM Sans: normal, weight400; axes "wght" 400. |
| family-07-cut-1 / P | 1440 x 900 | Library > all > DM Sans > Italic | `.superpowers/sdd/r2-audit/library-family-07-cut-1.png` | DM Sans: italic, weight400; axes "wght" 400. |
| family-07-axis-0 / P | 1440 x 900 | Library > DM Sans > wght slider End | `.superpowers/sdd/r2-audit/library-family-07-axis-0.png` | DM Sans: italic, weight400; axes "wght" 1000. |
| family-08-cut-0 / P | 1440 x 900 | Library > all > Work Sans > Regular | `.superpowers/sdd/r2-audit/library-family-08-cut-0.png` | Work Sans: normal, weight400; axes "wght" 400. |
| family-08-cut-1 / P | 1440 x 900 | Library > all > Work Sans > Italic | `.superpowers/sdd/r2-audit/library-family-08-cut-1.png` | Work Sans: italic, weight400; axes "wght" 400. |
| family-08-axis-0 / P | 1440 x 900 | Library > Work Sans > wght slider End | `.superpowers/sdd/r2-audit/library-family-08-axis-0.png` | Work Sans: italic, weight400; axes "wght" 900. |
| family-09-cut-0 / P | 1440 x 900 | Library > all > IBM Plex Sans > Regular | `.superpowers/sdd/r2-audit/library-family-09-cut-0.png` | IBM Plex Sans: normal, weight400; axes normal. |
| family-09-cut-1 / P | 1440 x 900 | Library > all > IBM Plex Sans > Medium | `.superpowers/sdd/r2-audit/library-family-09-cut-1.png` | IBM Plex Sans: normal, weight500; axes normal. |
| family-09-cut-2 / P | 1440 x 900 | Library > all > IBM Plex Sans > SemiBold | `.superpowers/sdd/r2-audit/library-family-09-cut-2.png` | IBM Plex Sans: normal, weight600; axes normal. |
| family-09-cut-3 / P | 1440 x 900 | Library > all > IBM Plex Sans > Bold | `.superpowers/sdd/r2-audit/library-family-09-cut-3.png` | IBM Plex Sans: normal, weight700; axes normal. |
| family-09-cut-4 / P | 1440 x 900 | Library > all > IBM Plex Sans > Italic | `.superpowers/sdd/r2-audit/library-family-09-cut-4.png` | IBM Plex Sans: italic, weight400; axes normal. |
| family-10-cut-0 / P | 1440 x 900 | Library > all > Archivo > Regular | `.superpowers/sdd/r2-audit/library-family-10-cut-0.png` | Archivo: normal, weight400; axes "wght" 400. |
| family-10-cut-1 / P | 1440 x 900 | Library > all > Archivo > Italic | `.superpowers/sdd/r2-audit/library-family-10-cut-1.png` | Archivo: italic, weight400; axes "wght" 400. |
| family-10-axis-0 / P | 1440 x 900 | Library > Archivo > wght slider End | `.superpowers/sdd/r2-audit/library-family-10-axis-0.png` | Archivo: italic, weight400; axes "wght" 900. |
| family-11-axis-0 / P | 1440 x 900 | Library > Bricolage Grotesque > wght slider End | `.superpowers/sdd/r2-audit/library-family-11-axis-0.png` | Bricolage Grotesque: normal, weight400; axes "opsz" 48, "wght" 800. |
| family-11-axis-1 / P | 1440 x 900 | Library > Bricolage Grotesque > opsz slider End | `.superpowers/sdd/r2-audit/library-family-11-axis-1.png` | Bricolage Grotesque: normal, weight400; axes "opsz" 96, "wght" 800. |
| family-13-cut-0 / P | 1440 x 900 | Library > all > JetBrains Mono > Regular | `.superpowers/sdd/r2-audit/library-family-13-cut-0.png` | JetBrains Mono: normal, weight400; axes "wght" 400. |
| family-13-cut-1 / P | 1440 x 900 | Library > all > JetBrains Mono > Italic | `.superpowers/sdd/r2-audit/library-family-13-cut-1.png` | JetBrains Mono: italic, weight400; axes "wght" 400. |
| family-13-axis-0 / P | 1440 x 900 | Library > JetBrains Mono > wght slider End | `.superpowers/sdd/r2-audit/library-family-13-axis-0.png` | JetBrains Mono: italic, weight400; axes "wght" 800. |
| family-14-cut-0 / P | 1440 x 900 | Library > all > IBM Plex Mono > Regular | `.superpowers/sdd/r2-audit/library-family-14-cut-0.png` | IBM Plex Mono: normal, weight400; axes normal. |
| family-14-cut-1 / P | 1440 x 900 | Library > all > IBM Plex Mono > Medium | `.superpowers/sdd/r2-audit/library-family-14-cut-1.png` | IBM Plex Mono: normal, weight500; axes normal. |
| family-14-cut-2 / P | 1440 x 900 | Library > all > IBM Plex Mono > Bold | `.superpowers/sdd/r2-audit/library-family-14-cut-2.png` | IBM Plex Mono: normal, weight700; axes normal. |
| family-14-cut-3 / P | 1440 x 900 | Library > all > IBM Plex Mono > Italic | `.superpowers/sdd/r2-audit/library-family-14-cut-3.png` | IBM Plex Mono: italic, weight400; axes normal. |
| family-15-cut-0 / P | 1440 x 900 | Library > all > Space Mono > Regular | `.superpowers/sdd/r2-audit/library-family-15-cut-0.png` | Space Mono: normal, weight400; axes normal. |
| family-15-cut-1 / P | 1440 x 900 | Library > all > Space Mono > Bold | `.superpowers/sdd/r2-audit/library-family-15-cut-1.png` | Space Mono: normal, weight700; axes normal. |
| family-15-cut-2 / P | 1440 x 900 | Library > all > Space Mono > Italic | `.superpowers/sdd/r2-audit/library-family-15-cut-2.png` | Space Mono: italic, weight400; axes normal. |
| consent-blocked / S | 1440 x 900 | Click Load free fonts; initial guard intended, failed (superseded) | `.superpowers/sdd/r2-audit/library-consent-blocked.png` | Loaded 16/16 free font stylesheets from Google Fonts. |
| consent-reload / S | 1440 x 900 | Reload after remembered font consent; initial guard intended, failed (superseded) | `.superpowers/sdd/r2-audit/library-consent-reload.png` | Free fonts are on: families load as their cards scroll into view. |
| 1440-transition / S | 1440 x 900 | Library > Composer; no family-apply action | `.superpowers/sdd/r2-audit/library-1440-transition.png` | 4 top-level slots; 2 row children; canvas960px. |
| 1440-return / S | 1440 x 900 | Composer > Library; typed specimen survives mode switch | `.superpowers/sdd/r2-audit/library-1440-return.png` | 16 visible cards; document width1440px. |
| 390-initial / P | 390 x 844 | Fresh Library; no font consent | `.superpowers/sdd/r2-audit/library-390-initial.png` | 16 visible cards; document width390px. |
| 390-filter-all / P | 390 x 844 | Library > category all | `.superpowers/sdd/r2-audit/library-390-filter-all.png` | 16 visible cards; document width390px. |
| 390-filter-serif / P | 390 x 844 | Library > category serif | `.superpowers/sdd/r2-audit/library-390-filter-serif.png` | 5 visible cards; document width390px. |
| 390-filter-display / P | 390 x 844 | Library > category display | `.superpowers/sdd/r2-audit/library-390-filter-display.png` | 5 visible cards; document width390px. |
| 390-filter-variable / P | 390 x 844 | Library > category variable | `.superpowers/sdd/r2-audit/library-390-filter-variable.png` | 11 visible cards; document width390px. |
| 390-filter-sans / P | 390 x 844 | Library > category sans | `.superpowers/sdd/r2-audit/library-390-filter-sans.png` | 8 visible cards; document width390px. |
| 390-filter-technical / P | 390 x 844 | Library > category technical | `.superpowers/sdd/r2-audit/library-390-filter-technical.png` | 4 visible cards; document width390px. |
| 390-filter-geometric / P | 390 x 844 | Library > category geometric | `.superpowers/sdd/r2-audit/library-390-filter-geometric.png` | 2 visible cards; document width390px. |
| 390-filter-mono / P | 390 x 844 | Library > category mono | `.superpowers/sdd/r2-audit/library-390-filter-mono.png` | 3 visible cards; document width390px. |
| 390-filter-typewriter / P | 390 x 844 | Library > category typewriter | `.superpowers/sdd/r2-audit/library-390-filter-typewriter.png` | 1 visible cards; document width390px. |
| 390-sample-size / P | 390 x 844 | Type specimen text; Display size End (86px) | `.superpowers/sdd/r2-audit/library-390-sample-size.png` | All 16 cards: specimen computed 86px. |
| 390-min-size / P | 390 x 844 | Display size Home (8px) | `.superpowers/sdd/r2-audit/library-390-min-size.png` | All 16 cards: specimen computed 8px. |
| 390-dark / P | 390 x 844 | Click Dark mode | `.superpowers/sdd/r2-audit/library-390-dark.png` | 16 visible cards; document width390px. |
| 390-empty-adobe / P | 390 x 844 | Load kit with empty ID; no credentials | `.superpowers/sdd/r2-audit/library-390-empty-adobe.png` | Paste a kit ID first; empty field refused. |
| 390-transition / P | 390 x 844 | Library > Composer; no family-apply action | `.superpowers/sdd/r2-audit/library-390-transition.png` | 4 top-level slots; 2 row children; canvas352px. |
| 390-return / P | 390 x 844 | Composer > Library; typed specimen survives mode switch | `.superpowers/sdd/r2-audit/library-390-return.png` | 16 visible cards; document width390px. |

### composer

Raw observations: [composer-evidence.json](../../.superpowers/sdd/r2-audit/composer-evidence.json).

| State / evidence status | Viewport | Visible route and actions | Screenshot | Rendered / computed observation |
|---|---|---|---|---|
| 1440-initial / D | 1440 x 900 | Library > Composer | `.superpowers/sdd/r2-audit/composer-1440-initial.png` | 4 top-level slots; 2 row children; canvas960px. |
| 1440-preset-blank / D | 1440 x 900 | Composer > #compositionPreset > blank | `.superpowers/sdd/r2-audit/composer-1440-preset-blank.png` | Blank — Editorial 5 applied. Every slot is still editable. |
| 1440-preset-asteria / D | 1440 x 900 | Composer > #compositionPreset > asteria | `.superpowers/sdd/r2-audit/composer-1440-preset-asteria.png` | Asteria — Sculptural applied. Every slot is still editable. |
| 1440-preset-rowdemo / D | 1440 x 900 | Composer > #compositionPreset > rowdemo | `.superpowers/sdd/r2-audit/composer-1440-preset-rowdemo.png` | Editorial — Image + Body Row applied. Every slot is still editable. |
| 1440-apply-no-edits / D | 1440 x 900 | Apply preset with untouched current preset | `.superpowers/sdd/r2-audit/composer-1440-apply-no-edits.png` | 4 top-level slots; 2 row children; canvas960px. |
| 1440-width-720 / D | 1440 x 900 | Composer > #canvasWidth > 720 | `.superpowers/sdd/r2-audit/composer-1440-width-720.png` | Canvas computed width723.953px; document width1440px. |
| 1440-width-960 / D | 1440 x 900 | Composer > #canvasWidth > 960 | `.superpowers/sdd/r2-audit/composer-1440-width-960.png` | Canvas computed width949.969px; document width1440px. |
| 1440-width-1200 / D | 1440 x 900 | Composer > #canvasWidth > 1200 | `.superpowers/sdd/r2-audit/composer-1440-width-1200.png` | Canvas computed width1044.19px; document width1440px. |
| 1440-width-100fluid / D | 1440 x 900 | Composer > #canvasWidth > 100% | `.superpowers/sdd/r2-audit/composer-1440-width-100fluid.png` | Canvas computed width1047.92px; document width1440px. |
| 1440-count-8 / D | 1440 x 900 | Type Slots 8, Tab | `.superpowers/sdd/r2-audit/composer-1440-count-8.png` | 8 top-level slots; 2 row children; canvas1048px. |
| 1440-count-1 / D | 1440 x 900 | Type Slots 1, Tab | `.superpowers/sdd/r2-audit/composer-1440-count-1.png` | 1 top-level slots; 0 row children; canvas1048px. |
| 1440-count-0 / D | 1440 x 900 | Type Slots 0, Tab | `.superpowers/sdd/r2-audit/composer-1440-count-0.png` | 1 top-level slots; 0 row children; canvas1048px. |
| 1440-count-4 / D | 1440 x 900 | Type Slots 4, Tab | `.superpowers/sdd/r2-audit/composer-1440-count-4.png` | 4 top-level slots; 0 row children; canvas1048px. |
| 1440-kind-text / D | 1440 x 900 | Composer > [data-bind=type] > text | `.superpowers/sdd/r2-audit/composer-1440-kind-text.png` | 4 top-level slots; 0 row children; canvas1048px. |
| 1440-kind-image / D | 1440 x 900 | Composer > [data-bind=type] > image | `.superpowers/sdd/r2-audit/composer-1440-kind-image.png` | 4 top-level slots; 0 row children; canvas1048px. |
| 1440-kind-rule / D | 1440 x 900 | Composer > [data-bind=type] > rule | `.superpowers/sdd/r2-audit/composer-1440-kind-rule.png` | 4 top-level slots; 0 row children; canvas1048px. |
| 1440-kind-spacer / D | 1440 x 900 | Composer > [data-bind=type] > spacer | `.superpowers/sdd/r2-audit/composer-1440-kind-spacer.png` | 4 top-level slots; 0 row children; canvas1048px. |
| 1440-kind-row / D | 1440 x 900 | Composer > [data-bind=type] > row | `.superpowers/sdd/r2-audit/composer-1440-kind-row.png` | 4 top-level slots; row tracks 286.203px 571.781px. |
| 1440-row-children-2 / D | 1440 x 900 | Row > Children 2, Tab | `.superpowers/sdd/r2-audit/composer-1440-row-children-2.png` | 4 top-level slots; row tracks 286px 572px. |
| 1440-row-children-3 / D | 1440 x 900 | Row > Children 3, Tab | `.superpowers/sdd/r2-audit/composer-1440-row-children-3.png` | 4 top-level slots; row tracks 208.5px 417px 208.5px. |
| 1440-row-children-4 / D | 1440 x 900 | Row > Children 4, Tab | `.superpowers/sdd/r2-audit/composer-1440-row-children-4.png` | 4 top-level slots; row tracks 162px 324px 162px 162px. |
| 1440-row-gap / D | 1440 x 900 | Row Gap End (96px) | `.superpowers/sdd/r2-audit/composer-1440-row-gap.png` | 4 top-level slots; row tracks 118.891px 237.781px 118.891px 118.906px. |
| 1440-row-align-start / D | 1440 x 900 | Composer > #rowAlignItems > start | `.superpowers/sdd/r2-audit/composer-1440-row-align-start.png` | 4 top-level slots; row tracks 118.797px 237.594px 118.797px 118.812px. |
| 1440-row-align-center / D | 1440 x 900 | Composer > #rowAlignItems > center | `.superpowers/sdd/r2-audit/composer-1440-row-align-center.png` | 4 top-level slots; row tracks 118.797px 237.594px 118.797px 118.812px. |
| 1440-row-align-end / D | 1440 x 900 | Composer > #rowAlignItems > end | `.superpowers/sdd/r2-audit/composer-1440-row-align-end.png` | 4 top-level slots; row tracks 118.797px 237.594px 118.797px 118.812px. |
| 1440-row-align-stretch / D | 1440 x 900 | Composer > #rowAlignItems > stretch | `.superpowers/sdd/r2-audit/composer-1440-row-align-stretch.png` | 4 top-level slots; row tracks 118.797px 237.594px 118.797px 118.812px. |
| 1440-ratio / D | 1440 x 900 | Type Child 1 ratio 3.25, Tab | `.superpowers/sdd/r2-audit/composer-1440-ratio.png` | 4 top-level slots; row tracks 266.266px 163.859px 81.9375px 81.9375px. |
| 1440-collapse / D | 1440 x 900 | Type Collapse at 1600, Tab | `.superpowers/sdd/r2-audit/composer-1440-collapse.png` | 4 top-level slots; row tracks 882px. |
| 1440-child / D | 1440 x 900 | Row > child jump; nested Row unavailable | `.superpowers/sdd/r2-audit/composer-1440-child.png` | 4 top-level slots; 4 row children; canvas1048px. |
| 1440-child-kind-image / D | 1440 x 900 | Composer > [data-bind=type] > image | `.superpowers/sdd/r2-audit/composer-1440-child-kind-image.png` | 4 top-level slots; 4 row children; canvas1048px. |
| 1440-child-kind-rule / D | 1440 x 900 | Composer > [data-bind=type] > rule | `.superpowers/sdd/r2-audit/composer-1440-child-kind-rule.png` | 4 top-level slots; 4 row children; canvas1048px. |
| 1440-child-kind-spacer / D | 1440 x 900 | Composer > [data-bind=type] > spacer | `.superpowers/sdd/r2-audit/composer-1440-child-kind-spacer.png` | 4 top-level slots; 4 row children; canvas1048px. |
| 1440-child-kind-text / D | 1440 x 900 | Composer > [data-bind=type] > text | `.superpowers/sdd/r2-audit/composer-1440-child-kind-text.png` | 4 top-level slots; 4 row children; canvas1048px. |
| 1440-typed / D | 1440 x 900 | Child Text > type Typed specimen 0123 | `.superpowers/sdd/r2-audit/composer-1440-typed.png` | Selected rendered text: Typed specimen 0123 |
| 1440-numeric / D | 1440 x 900 | Text > type line height 1.75 and tracking 0.025 | `.superpowers/sdd/r2-audit/composer-1440-numeric.png` | Text line-height42px, tracking0.6px. |
| 1440-move-down / D | 1440 x 900 | First top-level slot > Move down | `.superpowers/sdd/r2-audit/composer-1440-move-down.png` | 4 top-level slots; 4 row children; canvas1048px. |
| 1440-move-up / D | 1440 x 900 | Second top-level slot > Move up (round trip) | `.superpowers/sdd/r2-audit/composer-1440-move-up.png` | 4 top-level slots; 4 row children; canvas1048px. |
| role-Wordmark / D | 1440 x 900 | Composer > [data-bind=role] > Wordmark | `.superpowers/sdd/r2-audit/composer-role-Wordmark.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| role-Display / D | 1440 x 900 | Composer > [data-bind=role] > Display | `.superpowers/sdd/r2-audit/composer-role-Display.png` | Inter, sans-serif, 72px, weight400/normal; "wght" 400. |
| role-H1 / D | 1440 x 900 | Composer > [data-bind=role] > H1 | `.superpowers/sdd/r2-audit/composer-role-H1.png` | Inter, sans-serif, 64px, weight400/normal; "wght" 400. |
| role-H2 / D | 1440 x 900 | Composer > [data-bind=role] > H2 | `.superpowers/sdd/r2-audit/composer-role-H2.png` | Inter, sans-serif, 38px, weight400/normal; "wght" 400. |
| role-H3 / D | 1440 x 900 | Composer > [data-bind=role] > H3 | `.superpowers/sdd/r2-audit/composer-role-H3.png` | Inter, sans-serif, 26px, weight400/normal; "wght" 400. |
| role-Lead / D | 1440 x 900 | Composer > [data-bind=role] > Lead | `.superpowers/sdd/r2-audit/composer-role-Lead.png` | Inter, sans-serif, 22px, weight400/normal; "wght" 400. |
| role-Body / D | 1440 x 900 | Composer > [data-bind=role] > Body | `.superpowers/sdd/r2-audit/composer-role-Body.png` | Inter, sans-serif, 16px, weight400/normal; "wght" 400. |
| role-Accent / D | 1440 x 900 | Composer > [data-bind=role] > Accent | `.superpowers/sdd/r2-audit/composer-role-Accent.png` | Inter, sans-serif, 30px, weight400/normal; "wght" 400. |
| role-Caption / D | 1440 x 900 | Composer > [data-bind=role] > Caption | `.superpowers/sdd/r2-audit/composer-role-Caption.png` | Inter, sans-serif, 12px, weight400/normal; "wght" 400. |
| role-Metadata / D | 1440 x 900 | Composer > [data-bind=role] > Metadata | `.superpowers/sdd/r2-audit/composer-role-Metadata.png` | Inter, sans-serif, 11px, weight400/normal; "wght" 400. |
| role-Code / D | 1440 x 900 | Composer > [data-bind=role] > Code | `.superpowers/sdd/r2-audit/composer-role-Code.png` | Inter, sans-serif, 13px, weight400/normal; "wght" 400. |
| role-Custom / D | 1440 x 900 | Composer > [data-bind=role] > Custom | `.superpowers/sdd/r2-audit/composer-role-Custom.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| element-div / D | 1440 x 900 | Composer > [data-bind=element] > div | `.superpowers/sdd/r2-audit/composer-element-div.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| element-span / D | 1440 x 900 | Composer > [data-bind=element] > span | `.superpowers/sdd/r2-audit/composer-element-span.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| element-h1 / D | 1440 x 900 | Composer > [data-bind=element] > h1 | `.superpowers/sdd/r2-audit/composer-element-h1.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| element-h2 / D | 1440 x 900 | Composer > [data-bind=element] > h2 | `.superpowers/sdd/r2-audit/composer-element-h2.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| element-h3 / D | 1440 x 900 | Composer > [data-bind=element] > h3 | `.superpowers/sdd/r2-audit/composer-element-h3.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| element-p / D | 1440 x 900 | Composer > [data-bind=element] > p | `.superpowers/sdd/r2-audit/composer-element-p.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| element-small / D | 1440 x 900 | Composer > [data-bind=element] > small | `.superpowers/sdd/r2-audit/composer-element-small.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| element-code / D | 1440 x 900 | Composer > [data-bind=element] > code | `.superpowers/sdd/r2-audit/composer-element-code.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| family-fraunces / D | 1440 x 900 | Composer > [data-bind=family] > fraunces | `.superpowers/sdd/r2-audit/composer-family-fraunces.png` | Fraunces, serif, 24px, weight400/normal; "opsz" 72, "wght" 400. |
| cut-fraunces-0 / D | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer-cut-fraunces-0.png` | Fraunces, serif, 24px, weight400/normal; "opsz" 72, "wght" 400. |
| cut-fraunces-1 / D | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer-cut-fraunces-1.png` | Fraunces, serif, 24px, weight400/italic; "opsz" 72, "wght" 400. |
| axis-fraunces-wght / D | 1440 x 900 | fraunces > variable wght End | `.superpowers/sdd/r2-audit/composer-axis-fraunces-wght.png` | Fraunces, serif, 24px, weight900/italic; "opsz" 72, "wght" 900. |
| axis-fraunces-opsz / D | 1440 x 900 | fraunces > variable opsz End | `.superpowers/sdd/r2-audit/composer-axis-fraunces-opsz.png` | Fraunces, serif, 24px, weight900/italic; "opsz" 144, "wght" 900. |
| family-crimson-pro / D | 1440 x 900 | Composer > [data-bind=family] > crimson-pro | `.superpowers/sdd/r2-audit/composer-family-crimson-pro.png` | "Crimson Pro", serif, 24px, weight400/normal; "wght" 400. |
| cut-crimson-pro-0 / D | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer-cut-crimson-pro-0.png` | "Crimson Pro", serif, 24px, weight400/normal; "wght" 400. |
| cut-crimson-pro-1 / D | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer-cut-crimson-pro-1.png` | "Crimson Pro", serif, 24px, weight400/italic; "wght" 400. |
| axis-crimson-pro-wght / D | 1440 x 900 | crimson-pro > variable wght End | `.superpowers/sdd/r2-audit/composer-axis-crimson-pro-wght.png` | "Crimson Pro", serif, 24px, weight900/italic; "wght" 900. |
| family-source-serif-4 / D | 1440 x 900 | Composer > [data-bind=family] > source-serif-4 | `.superpowers/sdd/r2-audit/composer-family-source-serif-4.png` | "Source Serif 4", serif, 24px, weight400/normal; "opsz" 24, "wght" 400. |
| cut-source-serif-4-0 / D | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer-cut-source-serif-4-0.png` | "Source Serif 4", serif, 24px, weight400/normal; "opsz" 24, "wght" 400. |
| cut-source-serif-4-1 / D | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer-cut-source-serif-4-1.png` | "Source Serif 4", serif, 24px, weight400/italic; "opsz" 24, "wght" 400. |
| axis-source-serif-4-wght / D | 1440 x 900 | source-serif-4 > variable wght End | `.superpowers/sdd/r2-audit/composer-axis-source-serif-4-wght.png` | "Source Serif 4", serif, 24px, weight900/italic; "opsz" 24, "wght" 900. |
| axis-source-serif-4-opsz / D | 1440 x 900 | source-serif-4 > variable opsz End | `.superpowers/sdd/r2-audit/composer-axis-source-serif-4-opsz.png` | "Source Serif 4", serif, 24px, weight900/italic; "opsz" 60, "wght" 900. |
| family-playfair-display / D | 1440 x 900 | Composer > [data-bind=family] > playfair-display | `.superpowers/sdd/r2-audit/composer-family-playfair-display.png` | "Playfair Display", serif, 24px, weight400/normal; "wght" 400. |
| cut-playfair-display-0 / D | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer-cut-playfair-display-0.png` | "Playfair Display", serif, 24px, weight400/normal; "wght" 400. |
| cut-playfair-display-1 / D | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer-cut-playfair-display-1.png` | "Playfair Display", serif, 24px, weight400/italic; "wght" 400. |
| axis-playfair-display-wght / D | 1440 x 900 | playfair-display > variable wght End | `.superpowers/sdd/r2-audit/composer-axis-playfair-display-wght.png` | "Playfair Display", serif, 24px, weight900/italic; "wght" 900. |
| family-instrument-serif / D | 1440 x 900 | Composer > [data-bind=family] > instrument-serif | `.superpowers/sdd/r2-audit/composer-family-instrument-serif.png` | "Instrument Serif", serif, 24px, weight400/normal; normal. |
| cut-instrument-serif-0 / D | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer-cut-instrument-serif-0.png` | "Instrument Serif", serif, 24px, weight400/normal; normal. |
| cut-instrument-serif-1 / D | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer-cut-instrument-serif-1.png` | "Instrument Serif", serif, 24px, weight400/italic; normal. |
| family-inter / D | 1440 x 900 | Composer > [data-bind=family] > inter | `.superpowers/sdd/r2-audit/composer-family-inter.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |

### composer2

Raw observations: [composer2-evidence.json](../../.superpowers/sdd/r2-audit/composer2-evidence.json).

| State / evidence status | Viewport | Visible route and actions | Screenshot | Rendered / computed observation |
|---|---|---|---|---|
| 1440-initial / P | 1440 x 900 | Library > Composer | `.superpowers/sdd/r2-audit/composer2-1440-initial.png` | 4 top-level slots; 2 row children; canvas960px. |
| 1440-preset-blank / P | 1440 x 900 | Composer > #compositionPreset > blank | `.superpowers/sdd/r2-audit/composer2-1440-preset-blank.png` | Blank — Editorial 5 applied. Every slot is still editable. |
| 1440-preset-asteria / P | 1440 x 900 | Composer > #compositionPreset > asteria | `.superpowers/sdd/r2-audit/composer2-1440-preset-asteria.png` | Asteria — Sculptural applied. Every slot is still editable. |
| 1440-preset-rowdemo / P | 1440 x 900 | Composer > #compositionPreset > rowdemo | `.superpowers/sdd/r2-audit/composer2-1440-preset-rowdemo.png` | Editorial — Image + Body Row applied. Every slot is still editable. |
| 1440-apply-no-edits / P | 1440 x 900 | Apply preset with untouched current preset | `.superpowers/sdd/r2-audit/composer2-1440-apply-no-edits.png` | 4 top-level slots; 2 row children; canvas960px. |
| 1440-width-720 / P | 1440 x 900 | Composer > #canvasWidth > 720 | `.superpowers/sdd/r2-audit/composer2-1440-width-720.png` | Canvas computed width723.938px; document width1440px. |
| 1440-width-960 / P | 1440 x 900 | Composer > #canvasWidth > 960 | `.superpowers/sdd/r2-audit/composer2-1440-width-960.png` | Canvas computed width956.016px; document width1440px. |
| 1440-width-1200 / P | 1440 x 900 | Composer > #canvasWidth > 1200 | `.superpowers/sdd/r2-audit/composer2-1440-width-1200.png` | Canvas computed width1048px; document width1440px. |
| 1440-width-100fluid / P | 1440 x 900 | Composer > #canvasWidth > 100% | `.superpowers/sdd/r2-audit/composer2-1440-width-100fluid.png` | Canvas computed width1048px; document width1440px. |
| 1440-count-8 / P | 1440 x 900 | Type Slots 8, Tab | `.superpowers/sdd/r2-audit/composer2-1440-count-8.png` | 8 top-level slots; 2 row children; canvas1048px. |
| 1440-count-1 / P | 1440 x 900 | Type Slots 1, Tab | `.superpowers/sdd/r2-audit/composer2-1440-count-1.png` | 1 top-level slots; 0 row children; canvas1048px. |
| 1440-count-0 / P | 1440 x 900 | Type Slots 0, Tab | `.superpowers/sdd/r2-audit/composer2-1440-count-0.png` | 1 top-level slots; 0 row children; canvas1048px. |
| 1440-count-4 / P | 1440 x 900 | Type Slots 4, Tab | `.superpowers/sdd/r2-audit/composer2-1440-count-4.png` | 4 top-level slots; 0 row children; canvas1048px. |
| 1440-kind-text / P | 1440 x 900 | Composer > [data-bind=type] > text | `.superpowers/sdd/r2-audit/composer2-1440-kind-text.png` | 4 top-level slots; 0 row children; canvas1048px. |
| 1440-kind-image / P | 1440 x 900 | Composer > [data-bind=type] > image | `.superpowers/sdd/r2-audit/composer2-1440-kind-image.png` | 4 top-level slots; 0 row children; canvas1048px. |
| 1440-kind-rule / P | 1440 x 900 | Composer > [data-bind=type] > rule | `.superpowers/sdd/r2-audit/composer2-1440-kind-rule.png` | 4 top-level slots; 0 row children; canvas1048px. |
| 1440-kind-spacer / P | 1440 x 900 | Composer > [data-bind=type] > spacer | `.superpowers/sdd/r2-audit/composer2-1440-kind-spacer.png` | 4 top-level slots; 0 row children; canvas1048px. |
| 1440-kind-row / P | 1440 x 900 | Composer > [data-bind=type] > row | `.superpowers/sdd/r2-audit/composer2-1440-kind-row.png` | 4 top-level slots; row tracks 286.203px 571.797px. |
| 1440-row-children-2 / P | 1440 x 900 | Row > Children 2, Tab | `.superpowers/sdd/r2-audit/composer2-1440-row-children-2.png` | 4 top-level slots; row tracks 286px 572px. |
| 1440-row-children-3 / P | 1440 x 900 | Row > Children 3, Tab | `.superpowers/sdd/r2-audit/composer2-1440-row-children-3.png` | 4 top-level slots; row tracks 208.5px 417px 208.5px. |
| 1440-row-children-4 / P | 1440 x 900 | Row > Children 4, Tab | `.superpowers/sdd/r2-audit/composer2-1440-row-children-4.png` | 4 top-level slots; row tracks 162px 324px 162px 162px. |
| 1440-row-gap / P | 1440 x 900 | Row Gap End (96px) | `.superpowers/sdd/r2-audit/composer2-1440-row-gap.png` | 4 top-level slots; row tracks 118.891px 237.781px 118.891px 118.906px. |
| 1440-row-align-start / P | 1440 x 900 | Composer > #rowAlignItems > start | `.superpowers/sdd/r2-audit/composer2-1440-row-align-start.png` | 4 top-level slots; row tracks 118.797px 237.594px 118.797px 118.812px. |
| 1440-row-align-center / P | 1440 x 900 | Composer > #rowAlignItems > center | `.superpowers/sdd/r2-audit/composer2-1440-row-align-center.png` | 4 top-level slots; row tracks 118.797px 237.594px 118.797px 118.812px. |
| 1440-row-align-end / P | 1440 x 900 | Composer > #rowAlignItems > end | `.superpowers/sdd/r2-audit/composer2-1440-row-align-end.png` | 4 top-level slots; row tracks 118.797px 237.594px 118.797px 118.812px. |
| 1440-row-align-stretch / P | 1440 x 900 | Composer > #rowAlignItems > stretch | `.superpowers/sdd/r2-audit/composer2-1440-row-align-stretch.png` | 4 top-level slots; row tracks 118.797px 237.594px 118.797px 118.812px. |
| 1440-ratio / P | 1440 x 900 | Type Child 1 ratio 3.25, Tab | `.superpowers/sdd/r2-audit/composer2-1440-ratio.png` | 4 top-level slots; row tracks 266.266px 163.859px 81.9375px 81.9375px. |
| 1440-collapse / P | 1440 x 900 | Type Collapse at 1600, Tab | `.superpowers/sdd/r2-audit/composer2-1440-collapse.png` | 4 top-level slots; row tracks 882px. |
| 1440-child / P | 1440 x 900 | Row > child jump; nested Row unavailable | `.superpowers/sdd/r2-audit/composer2-1440-child.png` | 4 top-level slots; 4 row children; canvas1048px. |
| 1440-child-kind-image / P | 1440 x 900 | Composer > [data-bind=type] > image | `.superpowers/sdd/r2-audit/composer2-1440-child-kind-image.png` | 4 top-level slots; 4 row children; canvas1048px. |
| 1440-child-kind-rule / P | 1440 x 900 | Composer > [data-bind=type] > rule | `.superpowers/sdd/r2-audit/composer2-1440-child-kind-rule.png` | 4 top-level slots; 4 row children; canvas1048px. |
| 1440-child-kind-spacer / P | 1440 x 900 | Composer > [data-bind=type] > spacer | `.superpowers/sdd/r2-audit/composer2-1440-child-kind-spacer.png` | 4 top-level slots; 4 row children; canvas1048px. |
| 1440-child-kind-text / P | 1440 x 900 | Composer > [data-bind=type] > text | `.superpowers/sdd/r2-audit/composer2-1440-child-kind-text.png` | 4 top-level slots; 4 row children; canvas1048px. |
| 1440-typed / P | 1440 x 900 | Child Text > type Typed specimen 0123 | `.superpowers/sdd/r2-audit/composer2-1440-typed.png` | Selected rendered text: Typed specimen 0123 |
| 1440-numeric / P | 1440 x 900 | Text > type line height 1.75 and tracking 0.025 | `.superpowers/sdd/r2-audit/composer2-1440-numeric.png` | Text line-height42px, tracking0.6px. |
| 1440-move-down / P | 1440 x 900 | First top-level slot > Move down | `.superpowers/sdd/r2-audit/composer2-1440-move-down.png` | 4 top-level slots; 4 row children; canvas1048px. |
| 1440-move-up / P | 1440 x 900 | Second top-level slot > Move up (round trip) | `.superpowers/sdd/r2-audit/composer2-1440-move-up.png` | 4 top-level slots; 4 row children; canvas1048px. |
| role-Wordmark / P | 1440 x 900 | Composer > [data-bind=role] > Wordmark | `.superpowers/sdd/r2-audit/composer2-role-Wordmark.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| role-Display / P | 1440 x 900 | Composer > [data-bind=role] > Display | `.superpowers/sdd/r2-audit/composer2-role-Display.png` | Inter, sans-serif, 72px, weight400/normal; "wght" 400. |
| role-H1 / P | 1440 x 900 | Composer > [data-bind=role] > H1 | `.superpowers/sdd/r2-audit/composer2-role-H1.png` | Inter, sans-serif, 64px, weight400/normal; "wght" 400. |
| role-H2 / P | 1440 x 900 | Composer > [data-bind=role] > H2 | `.superpowers/sdd/r2-audit/composer2-role-H2.png` | Inter, sans-serif, 38px, weight400/normal; "wght" 400. |
| role-H3 / P | 1440 x 900 | Composer > [data-bind=role] > H3 | `.superpowers/sdd/r2-audit/composer2-role-H3.png` | Inter, sans-serif, 26px, weight400/normal; "wght" 400. |
| role-Lead / P | 1440 x 900 | Composer > [data-bind=role] > Lead | `.superpowers/sdd/r2-audit/composer2-role-Lead.png` | Inter, sans-serif, 22px, weight400/normal; "wght" 400. |
| role-Body / P | 1440 x 900 | Composer > [data-bind=role] > Body | `.superpowers/sdd/r2-audit/composer2-role-Body.png` | Inter, sans-serif, 16px, weight400/normal; "wght" 400. |
| role-Accent / P | 1440 x 900 | Composer > [data-bind=role] > Accent | `.superpowers/sdd/r2-audit/composer2-role-Accent.png` | Inter, sans-serif, 30px, weight400/normal; "wght" 400. |
| role-Caption / P | 1440 x 900 | Composer > [data-bind=role] > Caption | `.superpowers/sdd/r2-audit/composer2-role-Caption.png` | Inter, sans-serif, 12px, weight400/normal; "wght" 400. |
| role-Metadata / P | 1440 x 900 | Composer > [data-bind=role] > Metadata | `.superpowers/sdd/r2-audit/composer2-role-Metadata.png` | Inter, sans-serif, 11px, weight400/normal; "wght" 400. |
| role-Code / P | 1440 x 900 | Composer > [data-bind=role] > Code | `.superpowers/sdd/r2-audit/composer2-role-Code.png` | Inter, sans-serif, 13px, weight400/normal; "wght" 400. |
| role-Custom / P | 1440 x 900 | Composer > [data-bind=role] > Custom | `.superpowers/sdd/r2-audit/composer2-role-Custom.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| element-div / P | 1440 x 900 | Composer > [data-bind=element] > div | `.superpowers/sdd/r2-audit/composer2-element-div.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| element-span / P | 1440 x 900 | Composer > [data-bind=element] > span | `.superpowers/sdd/r2-audit/composer2-element-span.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| element-h1 / P | 1440 x 900 | Composer > [data-bind=element] > h1 | `.superpowers/sdd/r2-audit/composer2-element-h1.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| element-h2 / P | 1440 x 900 | Composer > [data-bind=element] > h2 | `.superpowers/sdd/r2-audit/composer2-element-h2.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| element-h3 / P | 1440 x 900 | Composer > [data-bind=element] > h3 | `.superpowers/sdd/r2-audit/composer2-element-h3.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| element-p / P | 1440 x 900 | Composer > [data-bind=element] > p | `.superpowers/sdd/r2-audit/composer2-element-p.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| element-small / P | 1440 x 900 | Composer > [data-bind=element] > small | `.superpowers/sdd/r2-audit/composer2-element-small.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| element-code / P | 1440 x 900 | Composer > [data-bind=element] > code | `.superpowers/sdd/r2-audit/composer2-element-code.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| family-fraunces / P | 1440 x 900 | Composer > [data-bind=family] > fraunces | `.superpowers/sdd/r2-audit/composer2-family-fraunces.png` | Fraunces, serif, 24px, weight400/normal; "opsz" 72, "wght" 400. |
| cut-fraunces-0 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer2-cut-fraunces-0.png` | Fraunces, serif, 24px, weight400/normal; "opsz" 72, "wght" 400. |
| cut-fraunces-1 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer2-cut-fraunces-1.png` | Fraunces, serif, 24px, weight400/italic; "opsz" 72, "wght" 400. |
| axis-fraunces-wght / P | 1440 x 900 | fraunces > variable wght End | `.superpowers/sdd/r2-audit/composer2-axis-fraunces-wght.png` | Fraunces, serif, 24px, weight900/italic; "opsz" 72, "wght" 900. |
| axis-fraunces-opsz / P | 1440 x 900 | fraunces > variable opsz End | `.superpowers/sdd/r2-audit/composer2-axis-fraunces-opsz.png` | Fraunces, serif, 24px, weight900/italic; "opsz" 144, "wght" 900. |
| family-crimson-pro / P | 1440 x 900 | Composer > [data-bind=family] > crimson-pro | `.superpowers/sdd/r2-audit/composer2-family-crimson-pro.png` | "Crimson Pro", serif, 24px, weight400/normal; "wght" 400. |
| cut-crimson-pro-0 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer2-cut-crimson-pro-0.png` | "Crimson Pro", serif, 24px, weight400/normal; "wght" 400. |
| cut-crimson-pro-1 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer2-cut-crimson-pro-1.png` | "Crimson Pro", serif, 24px, weight400/italic; "wght" 400. |
| axis-crimson-pro-wght / P | 1440 x 900 | crimson-pro > variable wght End | `.superpowers/sdd/r2-audit/composer2-axis-crimson-pro-wght.png` | "Crimson Pro", serif, 24px, weight900/italic; "wght" 900. |
| family-source-serif-4 / P | 1440 x 900 | Composer > [data-bind=family] > source-serif-4 | `.superpowers/sdd/r2-audit/composer2-family-source-serif-4.png` | "Source Serif 4", serif, 24px, weight400/normal; "opsz" 24, "wght" 400. |
| cut-source-serif-4-0 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer2-cut-source-serif-4-0.png` | "Source Serif 4", serif, 24px, weight400/normal; "opsz" 24, "wght" 400. |
| cut-source-serif-4-1 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer2-cut-source-serif-4-1.png` | "Source Serif 4", serif, 24px, weight400/italic; "opsz" 24, "wght" 400. |
| axis-source-serif-4-wght / P | 1440 x 900 | source-serif-4 > variable wght End | `.superpowers/sdd/r2-audit/composer2-axis-source-serif-4-wght.png` | "Source Serif 4", serif, 24px, weight900/italic; "opsz" 24, "wght" 900. |
| axis-source-serif-4-opsz / P | 1440 x 900 | source-serif-4 > variable opsz End | `.superpowers/sdd/r2-audit/composer2-axis-source-serif-4-opsz.png` | "Source Serif 4", serif, 24px, weight900/italic; "opsz" 60, "wght" 900. |
| family-playfair-display / P | 1440 x 900 | Composer > [data-bind=family] > playfair-display | `.superpowers/sdd/r2-audit/composer2-family-playfair-display.png` | "Playfair Display", serif, 24px, weight400/normal; "wght" 400. |
| cut-playfair-display-0 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer2-cut-playfair-display-0.png` | "Playfair Display", serif, 24px, weight400/normal; "wght" 400. |
| cut-playfair-display-1 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer2-cut-playfair-display-1.png` | "Playfair Display", serif, 24px, weight400/italic; "wght" 400. |
| axis-playfair-display-wght / P | 1440 x 900 | playfair-display > variable wght End | `.superpowers/sdd/r2-audit/composer2-axis-playfair-display-wght.png` | "Playfair Display", serif, 24px, weight900/italic; "wght" 900. |
| family-instrument-serif / P | 1440 x 900 | Composer > [data-bind=family] > instrument-serif | `.superpowers/sdd/r2-audit/composer2-family-instrument-serif.png` | "Instrument Serif", serif, 24px, weight400/normal; normal. |
| cut-instrument-serif-0 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer2-cut-instrument-serif-0.png` | "Instrument Serif", serif, 24px, weight400/normal; normal. |
| cut-instrument-serif-1 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer2-cut-instrument-serif-1.png` | "Instrument Serif", serif, 24px, weight400/italic; normal. |
| family-inter / P | 1440 x 900 | Composer > [data-bind=family] > inter | `.superpowers/sdd/r2-audit/composer2-family-inter.png` | Inter, sans-serif, 24px, weight400/normal; "wght" 400. |
| axis-inter-wght / P | 1440 x 900 | inter > variable wght End | `.superpowers/sdd/r2-audit/composer2-axis-inter-wght.png` | Inter, sans-serif, 24px, weight900/normal; "wght" 900. |
| family-space-grotesk / P | 1440 x 900 | Composer > [data-bind=family] > space-grotesk | `.superpowers/sdd/r2-audit/composer2-family-space-grotesk.png` | "Space Grotesk", sans-serif, 24px, weight400/normal; "wght" 400. |
| axis-space-grotesk-wght / P | 1440 x 900 | space-grotesk > variable wght End | `.superpowers/sdd/r2-audit/composer2-axis-space-grotesk-wght.png` | "Space Grotesk", sans-serif, 24px, weight700/normal; "wght" 700. |
| family-dm-sans / P | 1440 x 900 | Composer > [data-bind=family] > dm-sans | `.superpowers/sdd/r2-audit/composer2-family-dm-sans.png` | "DM Sans", sans-serif, 24px, weight400/normal; "wght" 400. |
| cut-dm-sans-0 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer2-cut-dm-sans-0.png` | "DM Sans", sans-serif, 24px, weight400/normal; "wght" 400. |
| cut-dm-sans-1 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer2-cut-dm-sans-1.png` | "DM Sans", sans-serif, 24px, weight400/italic; "wght" 400. |
| axis-dm-sans-wght / P | 1440 x 900 | dm-sans > variable wght End | `.superpowers/sdd/r2-audit/composer2-axis-dm-sans-wght.png` | "DM Sans", sans-serif, 24px, weight1000/italic; "wght" 1000. |
| family-work-sans / P | 1440 x 900 | Composer > [data-bind=family] > work-sans | `.superpowers/sdd/r2-audit/composer2-family-work-sans.png` | "Work Sans", sans-serif, 24px, weight400/normal; "wght" 400. |
| cut-work-sans-0 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer2-cut-work-sans-0.png` | "Work Sans", sans-serif, 24px, weight400/normal; "wght" 400. |
| cut-work-sans-1 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer2-cut-work-sans-1.png` | "Work Sans", sans-serif, 24px, weight400/italic; "wght" 400. |
| axis-work-sans-wght / P | 1440 x 900 | work-sans > variable wght End | `.superpowers/sdd/r2-audit/composer2-axis-work-sans-wght.png` | "Work Sans", sans-serif, 24px, weight900/italic; "wght" 900. |
| family-ibm-plex-sans / P | 1440 x 900 | Composer > [data-bind=family] > ibm-plex-sans | `.superpowers/sdd/r2-audit/composer2-family-ibm-plex-sans.png` | "IBM Plex Sans", sans-serif, 24px, weight400/normal; normal. |
| cut-ibm-plex-sans-0 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer2-cut-ibm-plex-sans-0.png` | "IBM Plex Sans", sans-serif, 24px, weight400/normal; normal. |
| cut-ibm-plex-sans-1 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer2-cut-ibm-plex-sans-1.png` | "IBM Plex Sans", sans-serif, 24px, weight500/normal; normal. |
| cut-ibm-plex-sans-2 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 2 | `.superpowers/sdd/r2-audit/composer2-cut-ibm-plex-sans-2.png` | "IBM Plex Sans", sans-serif, 24px, weight600/normal; normal. |
| cut-ibm-plex-sans-3 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 3 | `.superpowers/sdd/r2-audit/composer2-cut-ibm-plex-sans-3.png` | "IBM Plex Sans", sans-serif, 24px, weight700/normal; normal. |
| cut-ibm-plex-sans-4 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 4 | `.superpowers/sdd/r2-audit/composer2-cut-ibm-plex-sans-4.png` | "IBM Plex Sans", sans-serif, 24px, weight400/italic; normal. |
| family-archivo / P | 1440 x 900 | Composer > [data-bind=family] > archivo | `.superpowers/sdd/r2-audit/composer2-family-archivo.png` | Archivo, sans-serif, 24px, weight400/normal; "wght" 400. |
| cut-archivo-0 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer2-cut-archivo-0.png` | Archivo, sans-serif, 24px, weight400/normal; "wght" 400. |
| cut-archivo-1 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer2-cut-archivo-1.png` | Archivo, sans-serif, 24px, weight400/italic; "wght" 400. |
| axis-archivo-wght / P | 1440 x 900 | archivo > variable wght End | `.superpowers/sdd/r2-audit/composer2-axis-archivo-wght.png` | Archivo, sans-serif, 24px, weight900/italic; "wght" 900. |
| family-bricolage-grotesque / P | 1440 x 900 | Composer > [data-bind=family] > bricolage-grotesque | `.superpowers/sdd/r2-audit/composer2-family-bricolage-grotesque.png` | "Bricolage Grotesque", sans-serif, 24px, weight400/normal; "opsz" 48, "wght" 400. |
| axis-bricolage-grotesque-wght / P | 1440 x 900 | bricolage-grotesque > variable wght End | `.superpowers/sdd/r2-audit/composer2-axis-bricolage-grotesque-wght.png` | "Bricolage Grotesque", sans-serif, 24px, weight800/normal; "opsz" 48, "wght" 800. |
| axis-bricolage-grotesque-opsz / P | 1440 x 900 | bricolage-grotesque > variable opsz End | `.superpowers/sdd/r2-audit/composer2-axis-bricolage-grotesque-opsz.png` | "Bricolage Grotesque", sans-serif, 24px, weight800/normal; "opsz" 96, "wght" 800. |
| family-bebas-neue / P | 1440 x 900 | Composer > [data-bind=family] > bebas-neue | `.superpowers/sdd/r2-audit/composer2-family-bebas-neue.png` | "Bebas Neue", sans-serif, 24px, weight400/normal; normal. |
| family-jetbrains-mono / P | 1440 x 900 | Composer > [data-bind=family] > jetbrains-mono | `.superpowers/sdd/r2-audit/composer2-family-jetbrains-mono.png` | "JetBrains Mono", monospace, 24px, weight400/normal; "wght" 400. |
| cut-jetbrains-mono-0 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer2-cut-jetbrains-mono-0.png` | "JetBrains Mono", monospace, 24px, weight400/normal; "wght" 400. |
| cut-jetbrains-mono-1 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer2-cut-jetbrains-mono-1.png` | "JetBrains Mono", monospace, 24px, weight400/italic; "wght" 400. |
| axis-jetbrains-mono-wght / P | 1440 x 900 | jetbrains-mono > variable wght End | `.superpowers/sdd/r2-audit/composer2-axis-jetbrains-mono-wght.png` | "JetBrains Mono", monospace, 24px, weight800/italic; "wght" 800. |
| family-ibm-plex-mono / P | 1440 x 900 | Composer > [data-bind=family] > ibm-plex-mono | `.superpowers/sdd/r2-audit/composer2-family-ibm-plex-mono.png` | "IBM Plex Mono", monospace, 24px, weight400/normal; normal. |
| cut-ibm-plex-mono-0 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer2-cut-ibm-plex-mono-0.png` | "IBM Plex Mono", monospace, 24px, weight400/normal; normal. |
| cut-ibm-plex-mono-1 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer2-cut-ibm-plex-mono-1.png` | "IBM Plex Mono", monospace, 24px, weight500/normal; normal. |
| cut-ibm-plex-mono-2 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 2 | `.superpowers/sdd/r2-audit/composer2-cut-ibm-plex-mono-2.png` | "IBM Plex Mono", monospace, 24px, weight700/normal; normal. |
| cut-ibm-plex-mono-3 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 3 | `.superpowers/sdd/r2-audit/composer2-cut-ibm-plex-mono-3.png` | "IBM Plex Mono", monospace, 24px, weight400/italic; normal. |
| family-space-mono / P | 1440 x 900 | Composer > [data-bind=family] > space-mono | `.superpowers/sdd/r2-audit/composer2-family-space-mono.png` | "Space Mono", monospace, 24px, weight400/normal; normal. |
| cut-space-mono-0 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 0 | `.superpowers/sdd/r2-audit/composer2-cut-space-mono-0.png` | "Space Mono", monospace, 24px, weight400/normal; normal. |
| cut-space-mono-1 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 1 | `.superpowers/sdd/r2-audit/composer2-cut-space-mono-1.png` | "Space Mono", monospace, 24px, weight700/normal; normal. |
| cut-space-mono-2 / P | 1440 x 900 | Composer > [data-bind=styleIndex] > 2 | `.superpowers/sdd/r2-audit/composer2-cut-space-mono-2.png` | "Space Mono", monospace, 24px, weight400/italic; normal. |
| transform-none / P | 1440 x 900 | Composer > [data-bind=transform] > none | `.superpowers/sdd/r2-audit/composer2-transform-none.png` | "Space Mono", monospace, 24px, weight400/italic; normal. |
| transform-uppercase / P | 1440 x 900 | Composer > [data-bind=transform] > uppercase | `.superpowers/sdd/r2-audit/composer2-transform-uppercase.png` | "Space Mono", monospace, 24px, weight400/italic; normal. |
| transform-lowercase / P | 1440 x 900 | Composer > [data-bind=transform] > lowercase | `.superpowers/sdd/r2-audit/composer2-transform-lowercase.png` | "Space Mono", monospace, 24px, weight400/italic; normal. |
| transform-capitalize / P | 1440 x 900 | Composer > [data-bind=transform] > capitalize | `.superpowers/sdd/r2-audit/composer2-transform-capitalize.png` | "Space Mono", monospace, 24px, weight400/italic; normal. |
| align-left / P | 1440 x 900 | Text Alignment left | `.superpowers/sdd/r2-audit/composer2-align-left.png` | "Space Mono", monospace, 24px, weight400/italic; normal. |
| align-center / P | 1440 x 900 | Text Alignment center | `.superpowers/sdd/r2-audit/composer2-align-center.png` | "Space Mono", monospace, 24px, weight400/italic; normal. |
| align-right / P | 1440 x 900 | Text Alignment right | `.superpowers/sdd/r2-audit/composer2-align-right.png` | "Space Mono", monospace, 24px, weight400/italic; normal. |
| align-justify / P | 1440 x 900 | Text Alignment justify | `.superpowers/sdd/r2-audit/composer2-align-justify.png` | "Space Mono", monospace, 24px, weight400/italic; normal. |
| size-max / P | 1440 x 900 | Text Size End 86px | `.superpowers/sdd/r2-audit/composer2-size-max.png` | 4 top-level slots; 4 row children; canvas1048px. |
| size-min / P | 1440 x 900 | Text Size Home 8px | `.superpowers/sdd/r2-audit/composer2-size-min.png` | 4 top-level slots; 4 row children; canvas1048px. |
| 1440-background-custom / P | 1440 x 900 | Composer > #canvasBgSource > custom | `.superpowers/sdd/r2-audit/composer2-1440-background-custom.png` | Canvas rgb(245, 241, 232); selected text rgb(238, 242, 255). |
| 1440-slot-color-custom / P | 1440 x 900 | Composer > [data-bind=colorSource] > custom | `.superpowers/sdd/r2-audit/composer2-1440-slot-color-custom.png` | Canvas rgb(245, 241, 232); selected text rgb(238, 242, 255). |
| 1440-hex / P | 1440 x 900 | Type valid canvas #abcdef and slot #102030 | `.superpowers/sdd/r2-audit/composer2-1440-hex.png` | Canvas rgb(171, 205, 239); selected text rgb(16, 32, 48). |
| 1440-invalid-color / P | 1440 x 900 | Type invalid slot colour oops | `.superpowers/sdd/r2-audit/composer2-1440-invalid-color.png` | Canvas rgb(171, 205, 239); selected text rgb(24, 23, 20). |
| 1440-background-tailwind / P | 1440 x 900 | Composer > #canvasBgSource > tailwind | `.superpowers/sdd/r2-audit/composer2-1440-background-tailwind.png` | Canvas oklch(0.97 0.001 106.424); selected text rgb(24, 23, 20). |
| 1440-slot-color-tailwind / P | 1440 x 900 | Composer > [data-bind=colorSource] > tailwind | `.superpowers/sdd/r2-audit/composer2-1440-slot-color-tailwind.png` | Canvas oklch(0.97 0.001 106.424); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-0 / P | 1440 x 900 | Composer > #canvasBgFamily > slate | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-0.png` | Canvas oklch(0.554 0.046 257.417); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-1 / P | 1440 x 900 | Composer > #canvasBgFamily > gray | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-1.png` | Canvas oklch(0.551 0.027 264.364); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-2 / P | 1440 x 900 | Composer > #canvasBgFamily > zinc | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-2.png` | Canvas oklch(0.552 0.016 285.938); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-3 / P | 1440 x 900 | Composer > #canvasBgFamily > neutral | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-3.png` | Canvas oklch(0.556 0 0); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-4 / P | 1440 x 900 | Composer > #canvasBgFamily > stone | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-4.png` | Canvas oklch(0.553 0.013 58.071); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-5 / P | 1440 x 900 | Composer > #canvasBgFamily > red | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-5.png` | Canvas oklch(0.637 0.237 25.331); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-6 / P | 1440 x 900 | Composer > #canvasBgFamily > orange | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-6.png` | Canvas oklch(0.705 0.213 47.604); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-7 / P | 1440 x 900 | Composer > #canvasBgFamily > amber | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-7.png` | Canvas oklch(0.769 0.188 70.08); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-8 / P | 1440 x 900 | Composer > #canvasBgFamily > yellow | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-8.png` | Canvas oklch(0.795 0.184 86.047); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-9 / P | 1440 x 900 | Composer > #canvasBgFamily > lime | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-9.png` | Canvas oklch(0.768 0.233 130.85); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-10 / P | 1440 x 900 | Composer > #canvasBgFamily > green | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-10.png` | Canvas oklch(0.723 0.219 149.579); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-11 / P | 1440 x 900 | Composer > #canvasBgFamily > emerald | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-11.png` | Canvas oklch(0.696 0.17 162.48); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-12 / P | 1440 x 900 | Composer > #canvasBgFamily > teal | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-12.png` | Canvas oklch(0.704 0.14 182.503); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-13 / P | 1440 x 900 | Composer > #canvasBgFamily > cyan | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-13.png` | Canvas oklch(0.715 0.143 215.221); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-14 / P | 1440 x 900 | Composer > #canvasBgFamily > sky | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-14.png` | Canvas oklch(0.685 0.169 237.323); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-15 / P | 1440 x 900 | Composer > #canvasBgFamily > blue | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-15.png` | Canvas oklch(0.623 0.214 259.815); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-16 / P | 1440 x 900 | Composer > #canvasBgFamily > indigo | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-16.png` | Canvas oklch(0.585 0.233 277.117); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-17 / P | 1440 x 900 | Composer > #canvasBgFamily > violet | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-17.png` | Canvas oklch(0.606 0.25 292.717); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-18 / P | 1440 x 900 | Composer > #canvasBgFamily > purple | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-18.png` | Canvas oklch(0.627 0.265 303.9); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-19 / P | 1440 x 900 | Composer > #canvasBgFamily > fuchsia | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-19.png` | Canvas oklch(0.667 0.295 322.15); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-20 / P | 1440 x 900 | Composer > #canvasBgFamily > pink | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-20.png` | Canvas oklch(0.656 0.241 354.308); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgFamily-21 / P | 1440 x 900 | Composer > #canvasBgFamily > rose | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgFamily-21.png` | Canvas oklch(0.645 0.246 16.439); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgShade-0 / P | 1440 x 900 | Composer > #canvasBgShade > 50 | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgShade-0.png` | Canvas oklch(0.969 0.015 12.422); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgShade-1 / P | 1440 x 900 | Composer > #canvasBgShade > 100 | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgShade-1.png` | Canvas oklch(0.941 0.03 12.58); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgShade-2 / P | 1440 x 900 | Composer > #canvasBgShade > 200 | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgShade-2.png` | Canvas oklch(0.892 0.058 10.001); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgShade-3 / P | 1440 x 900 | Composer > #canvasBgShade > 300 | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgShade-3.png` | Canvas oklch(0.81 0.117 11.638); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgShade-4 / P | 1440 x 900 | Composer > #canvasBgShade > 400 | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgShade-4.png` | Canvas oklch(0.712 0.194 13.428); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgShade-5 / P | 1440 x 900 | Composer > #canvasBgShade > 500 | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgShade-5.png` | Canvas oklch(0.645 0.246 16.439); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgShade-6 / P | 1440 x 900 | Composer > #canvasBgShade > 600 | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgShade-6.png` | Canvas oklch(0.586 0.253 17.585); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgShade-7 / P | 1440 x 900 | Composer > #canvasBgShade > 700 | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgShade-7.png` | Canvas oklch(0.514 0.222 16.935); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgShade-8 / P | 1440 x 900 | Composer > #canvasBgShade > 800 | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgShade-8.png` | Canvas oklch(0.455 0.188 13.697); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgShade-9 / P | 1440 x 900 | Composer > #canvasBgShade > 900 | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgShade-9.png` | Canvas oklch(0.41 0.159 10.272); selected text oklch(0.968 0.007 247.896). |
| palette-canvasBgShade-10 / P | 1440 x 900 | Composer > #canvasBgShade > 950 | `.superpowers/sdd/r2-audit/composer2-palette-canvasBgShade-10.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.968 0.007 247.896). |
| palette-colorFamily-0 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > slate | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-0.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.554 0.046 257.417). |
| palette-colorFamily-1 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > gray | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-1.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.551 0.027 264.364). |
| palette-colorFamily-2 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > zinc | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-2.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.552 0.016 285.938). |
| palette-colorFamily-3 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > neutral | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-3.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.556 0 0). |
| palette-colorFamily-4 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > stone | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-4.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.553 0.013 58.071). |
| palette-colorFamily-5 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > red | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-5.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.637 0.237 25.331). |
| palette-colorFamily-6 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > orange | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-6.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.705 0.213 47.604). |
| palette-colorFamily-7 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > amber | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-7.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.769 0.188 70.08). |
| palette-colorFamily-8 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > yellow | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-8.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.795 0.184 86.047). |
| palette-colorFamily-9 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > lime | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-9.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.768 0.233 130.85). |
| palette-colorFamily-10 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > green | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-10.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.723 0.219 149.579). |
| palette-colorFamily-11 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > emerald | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-11.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.696 0.17 162.48). |
| palette-colorFamily-12 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > teal | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-12.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.704 0.14 182.503). |
| palette-colorFamily-13 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > cyan | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-13.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.715 0.143 215.221). |
| palette-colorFamily-14 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > sky | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-14.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.685 0.169 237.323). |
| palette-colorFamily-15 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > blue | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-15.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.623 0.214 259.815). |
| palette-colorFamily-16 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > indigo | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-16.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.585 0.233 277.117). |
| palette-colorFamily-17 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > violet | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-17.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.606 0.25 292.717). |
| palette-colorFamily-18 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > purple | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-18.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.627 0.265 303.9). |
| palette-colorFamily-19 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > fuchsia | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-19.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.667 0.295 322.15). |
| palette-colorFamily-20 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > pink | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-20.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.656 0.241 354.308). |
| palette-colorFamily-21 / P | 1440 x 900 | Composer > [data-bind=colorFamily] > rose | `.superpowers/sdd/r2-audit/composer2-palette-colorFamily-21.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.645 0.246 16.439). |
| palette-colorShade-0 / P | 1440 x 900 | Composer > [data-bind=colorShade] > 50 | `.superpowers/sdd/r2-audit/composer2-palette-colorShade-0.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.969 0.015 12.422). |
| palette-colorShade-1 / P | 1440 x 900 | Composer > [data-bind=colorShade] > 100 | `.superpowers/sdd/r2-audit/composer2-palette-colorShade-1.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.941 0.03 12.58). |
| palette-colorShade-2 / P | 1440 x 900 | Composer > [data-bind=colorShade] > 200 | `.superpowers/sdd/r2-audit/composer2-palette-colorShade-2.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.892 0.058 10.001). |
| palette-colorShade-3 / P | 1440 x 900 | Composer > [data-bind=colorShade] > 300 | `.superpowers/sdd/r2-audit/composer2-palette-colorShade-3.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.81 0.117 11.638). |
| palette-colorShade-4 / P | 1440 x 900 | Composer > [data-bind=colorShade] > 400 | `.superpowers/sdd/r2-audit/composer2-palette-colorShade-4.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.712 0.194 13.428). |
| palette-colorShade-5 / P | 1440 x 900 | Composer > [data-bind=colorShade] > 500 | `.superpowers/sdd/r2-audit/composer2-palette-colorShade-5.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.645 0.246 16.439). |
| palette-colorShade-6 / P | 1440 x 900 | Composer > [data-bind=colorShade] > 600 | `.superpowers/sdd/r2-audit/composer2-palette-colorShade-6.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.586 0.253 17.585). |
| palette-colorShade-7 / P | 1440 x 900 | Composer > [data-bind=colorShade] > 700 | `.superpowers/sdd/r2-audit/composer2-palette-colorShade-7.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.514 0.222 16.935). |
| palette-colorShade-8 / P | 1440 x 900 | Composer > [data-bind=colorShade] > 800 | `.superpowers/sdd/r2-audit/composer2-palette-colorShade-8.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.455 0.188 13.697). |
| palette-colorShade-9 / P | 1440 x 900 | Composer > [data-bind=colorShade] > 900 | `.superpowers/sdd/r2-audit/composer2-palette-colorShade-9.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.41 0.159 10.272). |
| palette-colorShade-10 / P | 1440 x 900 | Composer > [data-bind=colorShade] > 950 | `.superpowers/sdd/r2-audit/composer2-palette-colorShade-10.png` | Canvas oklch(0.271 0.105 12.094); selected text oklch(0.271 0.105 12.094). |
| 1440-background-saved / P | 1440 x 900 | Composer > #canvasBgSource > saved | `.superpowers/sdd/r2-audit/composer2-1440-background-saved.png` | Canvas rgb(238, 242, 255); selected text oklch(0.271 0.105 12.094). |
| 1440-slot-color-saved / P | 1440 x 900 | Composer > [data-bind=colorSource] > saved | `.superpowers/sdd/r2-audit/composer2-1440-slot-color-saved.png` | Canvas rgb(238, 242, 255); selected text rgb(238, 242, 255). |
| palette-canvasSavedColor-0 / P | 1440 x 900 | Composer > #canvasSavedColor > Asteria Void | `.superpowers/sdd/r2-audit/composer2-palette-canvasSavedColor-0.png` | Canvas rgb(7, 8, 13); selected text rgb(238, 242, 255). |
| palette-canvasSavedColor-1 / P | 1440 x 900 | Composer > #canvasSavedColor > Asteria Abyss | `.superpowers/sdd/r2-audit/composer2-palette-canvasSavedColor-1.png` | Canvas rgb(6, 10, 23); selected text rgb(238, 242, 255). |
| palette-canvasSavedColor-2 / P | 1440 x 900 | Composer > #canvasSavedColor > Asteria Haze | `.superpowers/sdd/r2-audit/composer2-palette-canvasSavedColor-2.png` | Canvas rgb(11, 16, 34); selected text rgb(238, 242, 255). |
| palette-canvasSavedColor-3 / P | 1440 x 900 | Composer > #canvasSavedColor > Asteria Starlight | `.superpowers/sdd/r2-audit/composer2-palette-canvasSavedColor-3.png` | Canvas rgb(234, 238, 251); selected text rgb(238, 242, 255). |
| palette-canvasSavedColor-4 / P | 1440 x 900 | Composer > #canvasSavedColor > Asteria Mist | `.superpowers/sdd/r2-audit/composer2-palette-canvasSavedColor-4.png` | Canvas rgb(152, 163, 197); selected text rgb(238, 242, 255). |
| palette-canvasSavedColor-5 / P | 1440 x 900 | Composer > #canvasSavedColor > Asteria Gold | `.superpowers/sdd/r2-audit/composer2-palette-canvasSavedColor-5.png` | Canvas rgb(229, 199, 142); selected text rgb(238, 242, 255). |
| palette-canvasSavedColor-6 / P | 1440 x 900 | Composer > #canvasSavedColor > Asteria Tender | `.superpowers/sdd/r2-audit/composer2-palette-canvasSavedColor-6.png` | Canvas rgb(220, 168, 183); selected text rgb(238, 242, 255). |
| palette-canvasSavedColor-7 / P | 1440 x 900 | Composer > #canvasSavedColor > Asteria Serene | `.superpowers/sdd/r2-audit/composer2-palette-canvasSavedColor-7.png` | Canvas rgb(157, 189, 214); selected text rgb(238, 242, 255). |
| palette-canvasSavedColor-8 / P | 1440 x 900 | Composer > #canvasSavedColor > Asteria Electric | `.superpowers/sdd/r2-audit/composer2-palette-canvasSavedColor-8.png` | Canvas rgb(184, 162, 218); selected text rgb(238, 242, 255). |
| palette-canvasSavedColor-9 / P | 1440 x 900 | Composer > #canvasSavedColor > Asteria Verdant | `.superpowers/sdd/r2-audit/composer2-palette-canvasSavedColor-9.png` | Canvas rgb(162, 198, 171); selected text rgb(238, 242, 255). |
| palette-canvasSavedColor-10 / P | 1440 x 900 | Composer > #canvasSavedColor > Asteria Vesper | `.superpowers/sdd/r2-audit/composer2-palette-canvasSavedColor-10.png` | Canvas rgb(144, 157, 208); selected text rgb(238, 242, 255). |
| palette-savedColor-0 / P | 1440 x 900 | Composer > [data-bind=savedColor] > Asteria Void | `.superpowers/sdd/r2-audit/composer2-palette-savedColor-0.png` | Canvas rgb(144, 157, 208); selected text rgb(3, 4, 9). |
| palette-savedColor-1 / P | 1440 x 900 | Composer > [data-bind=savedColor] > Asteria Abyss | `.superpowers/sdd/r2-audit/composer2-palette-savedColor-1.png` | Canvas rgb(144, 157, 208); selected text rgb(6, 10, 23). |
| palette-savedColor-2 / P | 1440 x 900 | Composer > [data-bind=savedColor] > Asteria Haze | `.superpowers/sdd/r2-audit/composer2-palette-savedColor-2.png` | Canvas rgb(144, 157, 208); selected text rgb(11, 16, 34). |
| palette-savedColor-3 / P | 1440 x 900 | Composer > [data-bind=savedColor] > Asteria Starlight | `.superpowers/sdd/r2-audit/composer2-palette-savedColor-3.png` | Canvas rgb(144, 157, 208); selected text rgb(238, 242, 255). |
| palette-savedColor-4 / P | 1440 x 900 | Composer > [data-bind=savedColor] > Asteria Mist | `.superpowers/sdd/r2-audit/composer2-palette-savedColor-4.png` | Canvas rgb(144, 157, 208); selected text rgb(152, 163, 197). |
| palette-savedColor-5 / P | 1440 x 900 | Composer > [data-bind=savedColor] > Asteria Gold | `.superpowers/sdd/r2-audit/composer2-palette-savedColor-5.png` | Canvas rgb(144, 157, 208); selected text rgb(230, 200, 141). |
| palette-savedColor-6 / P | 1440 x 900 | Composer > [data-bind=savedColor] > Asteria Tender | `.superpowers/sdd/r2-audit/composer2-palette-savedColor-6.png` | Canvas rgb(144, 157, 208); selected text rgb(220, 168, 183). |
| palette-savedColor-7 / P | 1440 x 900 | Composer > [data-bind=savedColor] > Asteria Serene | `.superpowers/sdd/r2-audit/composer2-palette-savedColor-7.png` | Canvas rgb(144, 157, 208); selected text rgb(157, 189, 214). |
| palette-savedColor-8 / P | 1440 x 900 | Composer > [data-bind=savedColor] > Asteria Electric | `.superpowers/sdd/r2-audit/composer2-palette-savedColor-8.png` | Canvas rgb(144, 157, 208); selected text rgb(184, 162, 218). |
| palette-savedColor-9 / P | 1440 x 900 | Composer > [data-bind=savedColor] > Asteria Verdant | `.superpowers/sdd/r2-audit/composer2-palette-savedColor-9.png` | Canvas rgb(144, 157, 208); selected text rgb(162, 198, 171). |
| palette-savedColor-10 / P | 1440 x 900 | Composer > [data-bind=savedColor] > Asteria Vesper | `.superpowers/sdd/r2-audit/composer2-palette-savedColor-10.png` | Canvas rgb(144, 157, 208); selected text rgb(144, 157, 208). |
| kit-adobe / P | 1440 x 900 | Composer > #kitPreset > adobe | `.superpowers/sdd/r2-audit/composer2-kit-adobe.png` | Adobe Fonts is bring-your-own: paste your own kit ID(s) and press Load. Nothing is prefilled. |
| kit-adobe-empty / P | 1440 x 900 | Kit adobe > Load empty; no credentials | `.superpowers/sdd/r2-audit/composer2-kit-adobe-empty.png` | No Adobe kit IDs supplied. Adobe Fonts is optional; the free Google Fonts need no kit. |
| kit-custom / P | 1440 x 900 | Composer > #kitPreset > custom | `.superpowers/sdd/r2-audit/composer2-kit-custom.png` | Custom kit: type your own kit ID(s) in the field and press Load. Nothing is prefilled. |
| kit-custom-empty / P | 1440 x 900 | Kit custom > Load empty; no credentials | `.superpowers/sdd/r2-audit/composer2-kit-custom-empty.png` | No Adobe kit IDs supplied. Adobe Fonts is optional; the free Google Fonts need no kit. |
| fonts-blocked / S | 1440 x 900 | Composer > Load free fonts; initial guard intended, failed (superseded) | `.superpowers/sdd/r2-audit/composer2-fonts-blocked.png` | Loading 16 free font stylesheets… |
| 1440-final / S | 1440 x 900 | Edited Composer before reload | `.superpowers/sdd/r2-audit/composer2-1440-final.png` | 4 top-level slots; 4 row children; canvas1048px. |
| 1440-reload / S | 1440 x 900 | Reload; Composer default composition restored | `.superpowers/sdd/r2-audit/composer2-1440-reload.png` | 4 top-level slots; 2 row children; canvas960px. |
| 390-initial / P | 390 x 844 | Library > Composer | `.superpowers/sdd/r2-audit/composer2-390-initial.png` | 4 top-level slots; 2 row children; canvas352px. |
| 390-preset-blank / P | 390 x 844 | Composer > #compositionPreset > blank | `.superpowers/sdd/r2-audit/composer2-390-preset-blank.png` | Blank — Editorial 5 applied. Every slot is still editable. |
| 390-preset-asteria / P | 390 x 844 | Composer > #compositionPreset > asteria | `.superpowers/sdd/r2-audit/composer2-390-preset-asteria.png` | Asteria — Sculptural applied. Every slot is still editable. |
| 390-preset-rowdemo / P | 390 x 844 | Composer > #compositionPreset > rowdemo | `.superpowers/sdd/r2-audit/composer2-390-preset-rowdemo.png` | Editorial — Image + Body Row applied. Every slot is still editable. |
| 390-apply-no-edits / P | 390 x 844 | Apply preset with untouched current preset | `.superpowers/sdd/r2-audit/composer2-390-apply-no-edits.png` | 4 top-level slots; 2 row children; canvas352px. |
| 390-width-720 / P | 390 x 844 | Composer > #canvasWidth > 720 | `.superpowers/sdd/r2-audit/composer2-390-width-720.png` | Canvas computed width352px; document width390px. |
| 390-width-960 / P | 390 x 844 | Composer > #canvasWidth > 960 | `.superpowers/sdd/r2-audit/composer2-390-width-960.png` | Canvas computed width352px; document width390px. |
| 390-width-1200 / P | 390 x 844 | Composer > #canvasWidth > 1200 | `.superpowers/sdd/r2-audit/composer2-390-width-1200.png` | Canvas computed width352px; document width390px. |
| 390-width-100fluid / P | 390 x 844 | Composer > #canvasWidth > 100% | `.superpowers/sdd/r2-audit/composer2-390-width-100fluid.png` | Canvas computed width352px; document width390px. |
| 390-count-8 / P | 390 x 844 | Type Slots 8, Tab | `.superpowers/sdd/r2-audit/composer2-390-count-8.png` | 8 top-level slots; 2 row children; canvas352px. |
| 390-count-1 / P | 390 x 844 | Type Slots 1, Tab | `.superpowers/sdd/r2-audit/composer2-390-count-1.png` | 1 top-level slots; 0 row children; canvas352px. |
| 390-count-0 / P | 390 x 844 | Type Slots 0, Tab | `.superpowers/sdd/r2-audit/composer2-390-count-0.png` | 1 top-level slots; 0 row children; canvas352px. |
| 390-count-4 / P | 390 x 844 | Type Slots 4, Tab | `.superpowers/sdd/r2-audit/composer2-390-count-4.png` | 4 top-level slots; 0 row children; canvas352px. |
| 390-kind-text / P | 390 x 844 | Composer > [data-bind=type] > text | `.superpowers/sdd/r2-audit/composer2-390-kind-text.png` | 4 top-level slots; 0 row children; canvas352px. |
| 390-kind-image / P | 390 x 844 | Composer > [data-bind=type] > image | `.superpowers/sdd/r2-audit/composer2-390-kind-image.png` | 4 top-level slots; 0 row children; canvas352px. |
| 390-kind-rule / P | 390 x 844 | Composer > [data-bind=type] > rule | `.superpowers/sdd/r2-audit/composer2-390-kind-rule.png` | 4 top-level slots; 0 row children; canvas352px. |
| 390-kind-spacer / P | 390 x 844 | Composer > [data-bind=type] > spacer | `.superpowers/sdd/r2-audit/composer2-390-kind-spacer.png` | 4 top-level slots; 0 row children; canvas352px. |
| 390-kind-row / P | 390 x 844 | Composer > [data-bind=type] > row | `.superpowers/sdd/r2-audit/composer2-390-kind-row.png` | 4 top-level slots; row tracks 290px. |
| 390-row-children-2 / P | 390 x 844 | Row > Children 2, Tab | `.superpowers/sdd/r2-audit/composer2-390-row-children-2.png` | 4 top-level slots; row tracks 290px. |
| 390-row-children-3 / P | 390 x 844 | Row > Children 3, Tab | `.superpowers/sdd/r2-audit/composer2-390-row-children-3.png` | 4 top-level slots; row tracks 290px. |
| 390-row-children-4 / P | 390 x 844 | Row > Children 4, Tab | `.superpowers/sdd/r2-audit/composer2-390-row-children-4.png` | 4 top-level slots; row tracks 290px. |
| 390-row-gap / P | 390 x 844 | Row Gap End (96px) | `.superpowers/sdd/r2-audit/composer2-390-row-gap.png` | 4 top-level slots; row tracks 290px. |
| 390-row-align-start / P | 390 x 844 | Composer > #rowAlignItems > start | `.superpowers/sdd/r2-audit/composer2-390-row-align-start.png` | 4 top-level slots; row tracks 290px. |
| 390-row-align-center / P | 390 x 844 | Composer > #rowAlignItems > center | `.superpowers/sdd/r2-audit/composer2-390-row-align-center.png` | 4 top-level slots; row tracks 290px. |
| 390-row-align-end / P | 390 x 844 | Composer > #rowAlignItems > end | `.superpowers/sdd/r2-audit/composer2-390-row-align-end.png` | 4 top-level slots; row tracks 290px. |
| 390-row-align-stretch / P | 390 x 844 | Composer > #rowAlignItems > stretch | `.superpowers/sdd/r2-audit/composer2-390-row-align-stretch.png` | 4 top-level slots; row tracks 290px. |
| 390-ratio / P | 390 x 844 | Type Child 1 ratio 3.25, Tab | `.superpowers/sdd/r2-audit/composer2-390-ratio.png` | 4 top-level slots; row tracks 290px. |
| 390-collapse / P | 390 x 844 | Type Collapse at 1600, Tab | `.superpowers/sdd/r2-audit/composer2-390-collapse.png` | 4 top-level slots; row tracks 290px. |
| 390-child / P | 390 x 844 | Row > child jump; nested Row unavailable | `.superpowers/sdd/r2-audit/composer2-390-child.png` | 4 top-level slots; 4 row children; canvas352px. |
| 390-child-kind-image / P | 390 x 844 | Composer > [data-bind=type] > image | `.superpowers/sdd/r2-audit/composer2-390-child-kind-image.png` | 4 top-level slots; 4 row children; canvas352px. |
| 390-child-kind-rule / P | 390 x 844 | Composer > [data-bind=type] > rule | `.superpowers/sdd/r2-audit/composer2-390-child-kind-rule.png` | 4 top-level slots; 4 row children; canvas352px. |
| 390-child-kind-spacer / P | 390 x 844 | Composer > [data-bind=type] > spacer | `.superpowers/sdd/r2-audit/composer2-390-child-kind-spacer.png` | 4 top-level slots; 4 row children; canvas352px. |
| 390-child-kind-text / P | 390 x 844 | Composer > [data-bind=type] > text | `.superpowers/sdd/r2-audit/composer2-390-child-kind-text.png` | 4 top-level slots; 4 row children; canvas352px. |
| 390-typed / P | 390 x 844 | Child Text > type Typed specimen 0123 | `.superpowers/sdd/r2-audit/composer2-390-typed.png` | Selected rendered text: Typed specimen 0123 |
| 390-numeric / P | 390 x 844 | Text > type line height 1.75 and tracking 0.025 | `.superpowers/sdd/r2-audit/composer2-390-numeric.png` | Text line-height42px, tracking0.6px. |
| 390-move-down / P | 390 x 844 | First top-level slot > Move down | `.superpowers/sdd/r2-audit/composer2-390-move-down.png` | 4 top-level slots; 4 row children; canvas352px. |
| 390-move-up / P | 390 x 844 | Second top-level slot > Move up (round trip) | `.superpowers/sdd/r2-audit/composer2-390-move-up.png` | 4 top-level slots; 4 row children; canvas352px. |
| 390-background-custom / P | 390 x 844 | Composer > #canvasBgSource > custom | `.superpowers/sdd/r2-audit/composer2-390-background-custom.png` | Canvas rgb(245, 241, 232); selected text rgb(238, 242, 255). |
| 390-slot-color-custom / P | 390 x 844 | Composer > [data-bind=colorSource] > custom | `.superpowers/sdd/r2-audit/composer2-390-slot-color-custom.png` | Canvas rgb(245, 241, 232); selected text rgb(238, 242, 255). |
| 390-hex / P | 390 x 844 | Type valid canvas #abcdef and slot #102030 | `.superpowers/sdd/r2-audit/composer2-390-hex.png` | Canvas rgb(171, 205, 239); selected text rgb(16, 32, 48). |
| 390-invalid-color / P | 390 x 844 | Type invalid slot colour oops | `.superpowers/sdd/r2-audit/composer2-390-invalid-color.png` | Canvas rgb(171, 205, 239); selected text rgb(24, 23, 20). |
| 390-background-tailwind / P | 390 x 844 | Composer > #canvasBgSource > tailwind | `.superpowers/sdd/r2-audit/composer2-390-background-tailwind.png` | Canvas oklab(0.96778 -0.000639205 0.0000230427); selected text rgb(24, 23, 20). |
| 390-slot-color-tailwind / P | 390 x 844 | Composer > [data-bind=colorSource] > tailwind | `.superpowers/sdd/r2-audit/composer2-390-slot-color-tailwind.png` | Canvas oklch(0.97 0.001 106.424); selected text oklch(0.968 0.007 247.896). |
| 390-background-saved / P | 390 x 844 | Composer > #canvasBgSource > saved | `.superpowers/sdd/r2-audit/composer2-390-background-saved.png` | Canvas oklab(0.962032 0.000750678 -0.0175882); selected text oklch(0.968 0.007 247.896). |
| 390-slot-color-saved / P | 390 x 844 | Composer > [data-bind=colorSource] > saved | `.superpowers/sdd/r2-audit/composer2-390-slot-color-saved.png` | Canvas rgb(238, 242, 255); selected text rgb(238, 242, 255). |
| 390-final / P | 390 x 844 | Edited Composer before reload | `.superpowers/sdd/r2-audit/composer2-390-final.png` | 4 top-level slots; 4 row children; canvas352px. |
| 390-reload / P | 390 x 844 | Reload; Composer default composition restored | `.superpowers/sdd/r2-audit/composer2-390-reload.png` | 4 top-level slots; 2 row children; canvas352px. |

### boundaries

Raw observations: [boundaries-evidence.json](../../.superpowers/sdd/r2-audit/boundaries-evidence.json).

| State / evidence status | Viewport | Visible route and actions | Screenshot | Rendered / computed observation |
|---|---|---|---|---|
| 1440-preset-decline / P | 1440 x 900 | Edit Wordmark; select Asteria; decline Replace edits? | `.superpowers/sdd/r2-audit/boundaries-1440-preset-decline.png` | Kept your edits. The preset was not applied. |
| 1440-preset-accept / P | 1440 x 900 | Select Asteria; accept Replace edits? | `.superpowers/sdd/r2-audit/boundaries-1440-preset-accept.png` | Asteria — Sculptural applied. Every slot is still editable. |
| 1440-image-empty / P | 1440 x 900 | Wordmark Slot type > Image; width disabled until chosen | `.superpowers/sdd/r2-audit/boundaries-1440-image-empty.png` | 5 top-level slots; 0 row children; canvas960px. |
| 1440-asset-svg / P | 1440 x 900 | Image > choose asset.svg | `.superpowers/sdd/r2-audit/boundaries-1440-asset-svg.png` | asset.svg loaded for this session. |
| 1440-asset-png / P | 1440 x 900 | Image > choose asset.png | `.superpowers/sdd/r2-audit/boundaries-1440-asset-png.png` | asset.png loaded for this session. |
| 1440-refused-jpg / P | 1440 x 900 | Image > choose refused.jpg | `.superpowers/sdd/r2-audit/boundaries-1440-refused-jpg.png` | Asset rejected: only PNG and SVG are accepted. |
| 1440-image-controls / P | 1440 x 900 | Image Width End (800), Opacity Home (5%) | `.superpowers/sdd/r2-audit/boundaries-1440-image-controls.png` | 5 top-level slots; 0 row children; canvas960px. |
| 1440-image-align-left / P | 1440 x 900 | Image Alignment left | `.superpowers/sdd/r2-audit/boundaries-1440-image-align-left.png` | 5 top-level slots; 0 row children; canvas960px. |
| 1440-image-align-center / P | 1440 x 900 | Image Alignment center | `.superpowers/sdd/r2-audit/boundaries-1440-image-align-center.png` | 5 top-level slots; 0 row children; canvas960px. |
| 1440-image-align-right / P | 1440 x 900 | Image Alignment right | `.superpowers/sdd/r2-audit/boundaries-1440-image-align-right.png` | 5 top-level slots; 0 row children; canvas960px. |
| 1440-rule-controls / P | 1440 x 900 | Rule > type width75 thickness4 using keystrokes | `.superpowers/sdd/r2-audit/boundaries-1440-rule-controls.png` | 5 top-level slots; 0 row children; canvas960px. |
| 1440-spacer-controls / P | 1440 x 900 | Spacer Height End (240px) | `.superpowers/sdd/r2-audit/boundaries-1440-spacer-controls.png` | 5 top-level slots; 0 row children; canvas960px. |
| 1440-exportJson / P | 1440 x 900 | Composer > exportJson dialog | `.superpowers/sdd/r2-audit/boundaries-1440-exportJson.png` | Composition JSON visible; 3794 displayed chars. |
| 1440-exportJson-copy / P | 1440 x 900 | Export > Copy; rendered Copied state | `.superpowers/sdd/r2-audit/boundaries-1440-exportJson-copy.png` | Composition JSON visible; 3794 displayed chars. |
| 1440-exportJson-download / P | 1440 x 900 | Export > Download; bytes equal displayed text | `.superpowers/sdd/r2-audit/boundaries-1440-exportJson-download.png` | Composition JSON visible; 3794 displayed chars. |
| 1440-exportJson-closed / P | 1440 x 900 | Close export by Escape | `.superpowers/sdd/r2-audit/boundaries-1440-exportJson-closed.png` | 5 top-level slots; 0 row children; canvas960px. |
| 1440-exportCss / P | 1440 x 900 | Composer > exportCss dialog | `.superpowers/sdd/r2-audit/boundaries-1440-exportCss.png` | CSS tokens visible; 1195 displayed chars. |
| 1440-exportCss-copy / P | 1440 x 900 | Export > Copy; rendered Copied state | `.superpowers/sdd/r2-audit/boundaries-1440-exportCss-copy.png` | CSS tokens visible; 1195 displayed chars. |
| 1440-exportCss-download / P | 1440 x 900 | Export > Download; bytes equal displayed text | `.superpowers/sdd/r2-audit/boundaries-1440-exportCss-download.png` | CSS tokens visible; 1195 displayed chars. |
| 1440-exportCss-closed / P | 1440 x 900 | Close export by Close | `.superpowers/sdd/r2-audit/boundaries-1440-exportCss-closed.png` | 5 top-level slots; 0 row children; canvas960px. |
| 1440-import-1440-roundtrip / P | 1440 x 900 | Composer > Import JSON > 1440-roundtrip.json | `.superpowers/sdd/r2-audit/boundaries-1440-import-1440-roundtrip.png` | Composition imported. Image assets must be reselected. |
| 1440-import-malformed / P | 1440 x 900 | Composer > Import JSON > malformed.json | `.superpowers/sdd/r2-audit/boundaries-1440-import-malformed.png` | Import failed: Expected property name or '}' in JSON at position 1 (line 1 column 2) |
| 1440-import-missing / P | 1440 x 900 | Composer > Import JSON > missing.json | `.superpowers/sdd/r2-audit/boundaries-1440-import-missing.png` | Import failed: Missing composition.slots array. |
| 1440-import-empty / P | 1440 x 900 | Composer > Import JSON > empty.json | `.superpowers/sdd/r2-audit/boundaries-1440-import-empty.png` | Composition imported. Image assets must be reselected. |
| 1440-keyboard / P | 1440 x 900 | Composer tab followed by 66 Tab keystrokes; focus path saved | `.superpowers/sdd/r2-audit/boundaries-1440-keyboard.png` | Focus BUTTON ; rgb(90, 58, 167) solid 2px. |
| 1440-fullscreen / P | 1440 x 900 | Specimen > Fullscreen | `.superpowers/sdd/r2-audit/boundaries-1440-fullscreen.png` | Live view; Changes visible, count0; Idle |
| 1440-fullscreen-exit / P | 1440 x 900 | Click visible Exit fullscreen | `.superpowers/sdd/r2-audit/boundaries-1440-fullscreen-exit.png` | Live view; Changes visible, count0; Idle |
| 390-preset-decline / P | 390 x 844 | Edit Wordmark; select Asteria; decline Replace edits? | `.superpowers/sdd/r2-audit/boundaries-390-preset-decline.png` | Kept your edits. The preset was not applied. |
| 390-preset-accept / P | 390 x 844 | Select Asteria; accept Replace edits? | `.superpowers/sdd/r2-audit/boundaries-390-preset-accept.png` | Asteria — Sculptural applied. Every slot is still editable. |
| 390-image-empty / P | 390 x 844 | Wordmark Slot type > Image; width disabled until chosen | `.superpowers/sdd/r2-audit/boundaries-390-image-empty.png` | 5 top-level slots; 0 row children; canvas352px. |
| 390-asset-svg / P | 390 x 844 | Image > choose asset.svg | `.superpowers/sdd/r2-audit/boundaries-390-asset-svg.png` | asset.svg loaded for this session. |
| 390-asset-png / P | 390 x 844 | Image > choose asset.png | `.superpowers/sdd/r2-audit/boundaries-390-asset-png.png` | asset.png loaded for this session. |
| 390-refused-jpg / P | 390 x 844 | Image > choose refused.jpg | `.superpowers/sdd/r2-audit/boundaries-390-refused-jpg.png` | Asset rejected: only PNG and SVG are accepted. |
| 390-image-controls / P | 390 x 844 | Image Width End (800), Opacity Home (5%) | `.superpowers/sdd/r2-audit/boundaries-390-image-controls.png` | 5 top-level slots; 0 row children; canvas352px. |
| 390-image-align-left / P | 390 x 844 | Image Alignment left | `.superpowers/sdd/r2-audit/boundaries-390-image-align-left.png` | 5 top-level slots; 0 row children; canvas352px. |
| 390-image-align-center / P | 390 x 844 | Image Alignment center | `.superpowers/sdd/r2-audit/boundaries-390-image-align-center.png` | 5 top-level slots; 0 row children; canvas352px. |
| 390-image-align-right / P | 390 x 844 | Image Alignment right | `.superpowers/sdd/r2-audit/boundaries-390-image-align-right.png` | 5 top-level slots; 0 row children; canvas352px. |
| 390-rule-controls / P | 390 x 844 | Rule > type width75 thickness4 using keystrokes | `.superpowers/sdd/r2-audit/boundaries-390-rule-controls.png` | 5 top-level slots; 0 row children; canvas352px. |
| 390-spacer-controls / P | 390 x 844 | Spacer Height End (240px) | `.superpowers/sdd/r2-audit/boundaries-390-spacer-controls.png` | 5 top-level slots; 0 row children; canvas352px. |
| 390-exportJson / P | 390 x 844 | Composer > exportJson dialog | `.superpowers/sdd/r2-audit/boundaries-390-exportJson.png` | Composition JSON visible; 3794 displayed chars. |
| 390-exportJson-copy / P | 390 x 844 | Export > Copy; rendered Copied state | `.superpowers/sdd/r2-audit/boundaries-390-exportJson-copy.png` | Composition JSON visible; 3794 displayed chars. |
| 390-exportJson-download / P | 390 x 844 | Export > Download; bytes equal displayed text | `.superpowers/sdd/r2-audit/boundaries-390-exportJson-download.png` | Composition JSON visible; 3794 displayed chars. |
| 390-exportJson-closed / P | 390 x 844 | Close export by Escape | `.superpowers/sdd/r2-audit/boundaries-390-exportJson-closed.png` | 5 top-level slots; 0 row children; canvas352px. |
| 390-exportCss / P | 390 x 844 | Composer > exportCss dialog | `.superpowers/sdd/r2-audit/boundaries-390-exportCss.png` | CSS tokens visible; 1195 displayed chars. |
| 390-exportCss-copy / P | 390 x 844 | Export > Copy; rendered Copied state | `.superpowers/sdd/r2-audit/boundaries-390-exportCss-copy.png` | CSS tokens visible; 1195 displayed chars. |
| 390-exportCss-download / P | 390 x 844 | Export > Download; bytes equal displayed text | `.superpowers/sdd/r2-audit/boundaries-390-exportCss-download.png` | CSS tokens visible; 1195 displayed chars. |
| 390-exportCss-closed / P | 390 x 844 | Close export by Close | `.superpowers/sdd/r2-audit/boundaries-390-exportCss-closed.png` | 5 top-level slots; 0 row children; canvas352px. |
| 390-import-390-roundtrip / P | 390 x 844 | Composer > Import JSON > 390-roundtrip.json | `.superpowers/sdd/r2-audit/boundaries-390-import-390-roundtrip.png` | Composition imported. Image assets must be reselected. |
| 390-import-malformed / P | 390 x 844 | Composer > Import JSON > malformed.json | `.superpowers/sdd/r2-audit/boundaries-390-import-malformed.png` | Import failed: Expected property name or '}' in JSON at position 1 (line 1 column 2) |
| 390-import-missing / P | 390 x 844 | Composer > Import JSON > missing.json | `.superpowers/sdd/r2-audit/boundaries-390-import-missing.png` | Import failed: Missing composition.slots array. |
| 390-import-empty / P | 390 x 844 | Composer > Import JSON > empty.json | `.superpowers/sdd/r2-audit/boundaries-390-import-empty.png` | Composition imported. Image assets must be reselected. |
| 390-keyboard / P | 390 x 844 | Composer tab followed by 66 Tab keystrokes; focus path saved | `.superpowers/sdd/r2-audit/boundaries-390-keyboard.png` | Focus BUTTON ; rgb(90, 58, 167) solid 2px. |
| 390-fullscreen / P | 390 x 844 | Specimen > Fullscreen | `.superpowers/sdd/r2-audit/boundaries-390-fullscreen.png` | Live view; Changes visible, count0; Idle |
| 390-fullscreen-exit / P | 390 x 844 | Click visible Exit fullscreen | `.superpowers/sdd/r2-audit/boundaries-390-fullscreen-exit.png` | Live view; Changes visible, count0; Idle |

### live

Raw observations: [live-evidence.json](../../.superpowers/sdd/r2-audit/live-evidence.json).

| State / evidence status | Viewport | Visible route and actions | Screenshot | Rendered / computed observation |
|---|---|---|---|---|
| 1440-connected / P | 1440 x 900 | Open printed Open URL with target query; demo connected | `.superpowers/sdd/r2-audit/live-1440-connected.png` | Live view; Changes visible, count0; Connected (37 targets) |
| 1440-specimen-connected / P | 1440 x 900 | Connected demo > Specimen; Changes hidden | `.superpowers/sdd/r2-audit/live-1440-specimen-connected.png` | 4 top-level slots; 2 row children; canvas960px. |
| 1440-specimen-edited / P | 1440 x 900 | Edit specimen Wordmark; Changes remains absent | `.superpowers/sdd/r2-audit/live-1440-specimen-edited.png` | 4 top-level slots; 2 row children; canvas960px. |
| 1440-changes-unsynced / P | 1440 x 900 | Specimen edit > Live App; Changes contains no specimen edit | `.superpowers/sdd/r2-audit/live-1440-changes-unsynced.png` | Live view; Changes visible, count0; Connected (37 targets) |
| 1440-synced / P | 1440 x 900 | Specimen > Sync to Live App > Live App; acknowledged Changes | `.superpowers/sdd/r2-audit/live-1440-synced.png` | Live view; Changes visible, count3; Live · rev 1 |
| 1440-codeTabCss / P | 1440 x 900 | Changes > codeTabCss | `.superpowers/sdd/r2-audit/live-1440-codeTabCss.png` | Live view; Changes visible, count3; Live · rev 1 |
| 1440-codeTabCss-download / P | 1440 x 900 | Changes > codeTabCss > Download | `.superpowers/sdd/r2-audit/live-1440-codeTabCss-download.png` | Live view; Changes visible, count3; Live · rev 1 |
| 1440-codeTabHtml / P | 1440 x 900 | Changes > codeTabHtml | `.superpowers/sdd/r2-audit/live-1440-codeTabHtml.png` | Live view; Changes visible, count3; Live · rev 1 |
| 1440-codeTabHtml-download / P | 1440 x 900 | Changes > codeTabHtml > Download | `.superpowers/sdd/r2-audit/live-1440-codeTabHtml-download.png` | Live view; Changes visible, count3; Live · rev 1 |
| 1440-codeTabJson / P | 1440 x 900 | Changes > codeTabJson | `.superpowers/sdd/r2-audit/live-1440-codeTabJson.png` | Live view; Changes visible, count3; Live · rev 1 |
| 1440-codeTabJson-download / P | 1440 x 900 | Changes > codeTabJson > Download | `.superpowers/sdd/r2-audit/live-1440-codeTabJson-download.png` | Live view; Changes visible, count3; Live · rev 1 |
| 1440-changes-copy / P | 1440 x 900 | Changes > CSS > Copy | `.superpowers/sdd/r2-audit/live-1440-changes-copy.png` | Live view; Changes visible, count3; Live · rev 1 |
| 1440-btnDeviceDesktop / P | 1440 x 900 | Live App > viewport btnDeviceDesktop | `.superpowers/sdd/r2-audit/live-1440-btnDeviceDesktop.png` | Live view; Changes visible, count3; Live · rev 1 |
| 1440-btnDeviceLaptop / P | 1440 x 900 | Live App > viewport btnDeviceLaptop | `.superpowers/sdd/r2-audit/live-1440-btnDeviceLaptop.png` | Live view; Changes visible, count3; Live · rev 1 |
| 1440-btnDeviceMobile / P | 1440 x 900 | Live App > viewport btnDeviceMobile | `.superpowers/sdd/r2-audit/live-1440-btnDeviceMobile.png` | Live view; Changes visible, count3; Live · rev 1 |
| 1440-btnDeviceFluid / P | 1440 x 900 | Live App > viewport btnDeviceFluid | `.superpowers/sdd/r2-audit/live-1440-btnDeviceFluid.png` | Live view; Changes visible, count3; Live · rev 1 |
| 1440-interact / P | 1440 x 900 | Live App > Interact | `.superpowers/sdd/r2-audit/live-1440-interact.png` | Live view; Changes visible, count3; Live · rev 1 |
| 1440-select / P | 1440 x 900 | Live App > Select | `.superpowers/sdd/r2-audit/live-1440-select.png` | Live view; Changes visible, count3; Live · rev 1 |
| 1440-theater / P | 1440 x 900 | Live App > Fullscreen | `.superpowers/sdd/r2-audit/live-1440-theater.png` | Live view; Changes visible, count3; Live · rev 1 |
| 1440-theater-escape / P | 1440 x 900 | Fullscreen > Escape | `.superpowers/sdd/r2-audit/live-1440-theater-escape.png` | Live view; Changes visible, count3; Live · rev 1 |
| popout / P | 1440 x 900 | Live App > Pop out; placeholder and focus/dock actions | `.superpowers/sdd/r2-audit/live-popout.png` | Live view; Changes visible, count3; Connected (37 targets) |
| popout-focus / P | 1440 x 900 | Pop-out > Focus pop-out | `.superpowers/sdd/r2-audit/live-popout-focus.png` | Live view; Changes visible, count3; Connected (37 targets) |
| dock / P | 1440 x 900 | Pop-out > Dock back | `.superpowers/sdd/r2-audit/live-dock.png` | Live view; Changes visible, count3; Connected (37 targets) |

### live2

Raw observations: [live2-evidence.json](../../.superpowers/sdd/r2-audit/live2-evidence.json).

| State / evidence status | Viewport | Visible route and actions | Screenshot | Rendered / computed observation |
|---|---|---|---|---|
| 390-connected / P | 390 x 844 | Open printed Open URL with target query; demo connected | `.superpowers/sdd/r2-audit/live2-390-connected.png` | Live view; Changes visible, count0; Connected (37 targets) |
| 390-specimen-connected / P | 390 x 844 | Connected demo > Specimen; Changes hidden | `.superpowers/sdd/r2-audit/live2-390-specimen-connected.png` | 4 top-level slots; 2 row children; canvas352px. |
| 390-specimen-edited / P | 390 x 844 | Edit specimen Wordmark; Changes remains absent | `.superpowers/sdd/r2-audit/live2-390-specimen-edited.png` | 4 top-level slots; 2 row children; canvas352px. |
| 390-changes-unsynced / P | 390 x 844 | Specimen edit > Live App; Changes contains no specimen edit | `.superpowers/sdd/r2-audit/live2-390-changes-unsynced.png` | Live view; Changes visible, count0; Connected (37 targets) |
| 390-synced / P | 390 x 844 | Specimen > Sync to Live App > Live App; acknowledged Changes | `.superpowers/sdd/r2-audit/live2-390-synced.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-codeTabCss / P | 390 x 844 | Changes > codeTabCss | `.superpowers/sdd/r2-audit/live2-390-codeTabCss.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-codeTabCss-download / P | 390 x 844 | Changes > codeTabCss > Download | `.superpowers/sdd/r2-audit/live2-390-codeTabCss-download.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-codeTabHtml / P | 390 x 844 | Changes > codeTabHtml | `.superpowers/sdd/r2-audit/live2-390-codeTabHtml.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-codeTabHtml-download / P | 390 x 844 | Changes > codeTabHtml > Download | `.superpowers/sdd/r2-audit/live2-390-codeTabHtml-download.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-codeTabJson / P | 390 x 844 | Changes > codeTabJson | `.superpowers/sdd/r2-audit/live2-390-codeTabJson.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-codeTabJson-download / P | 390 x 844 | Changes > codeTabJson > Download | `.superpowers/sdd/r2-audit/live2-390-codeTabJson-download.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-changes-copy / P | 390 x 844 | Changes > CSS > Copy | `.superpowers/sdd/r2-audit/live2-390-changes-copy.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-btnDeviceDesktop / P | 390 x 844 | Live App > viewport btnDeviceDesktop | `.superpowers/sdd/r2-audit/live2-390-btnDeviceDesktop.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-btnDeviceLaptop / P | 390 x 844 | Live App > viewport btnDeviceLaptop | `.superpowers/sdd/r2-audit/live2-390-btnDeviceLaptop.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-btnDeviceMobile / P | 390 x 844 | Live App > viewport btnDeviceMobile | `.superpowers/sdd/r2-audit/live2-390-btnDeviceMobile.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-btnDeviceFluid / P | 390 x 844 | Live App > viewport btnDeviceFluid | `.superpowers/sdd/r2-audit/live2-390-btnDeviceFluid.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-interact / P | 390 x 844 | Live App > Interact | `.superpowers/sdd/r2-audit/live2-390-interact.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-select / P | 390 x 844 | Live App > Select | `.superpowers/sdd/r2-audit/live2-390-select.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-theater / P | 390 x 844 | Live App > Fullscreen | `.superpowers/sdd/r2-audit/live2-390-theater.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-theater-escape / P | 390 x 844 | Fullscreen > Escape | `.superpowers/sdd/r2-audit/live2-390-theater-escape.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-linked-import / P | 390 x 844 | Linked composition > Import JSON; visible link-off message | `.superpowers/sdd/r2-audit/live2-390-linked-import.png` | Imported; the link to the page is off. Press Sync to Live App to send this composition. |

### followup

Raw observations: [followup-evidence.json](../../.superpowers/sdd/r2-audit/followup-evidence.json).

| State / evidence status | Viewport | Visible route and actions | Screenshot | Rendered / computed observation |
|---|---|---|---|---|
| fonts / S | 1440 x 900 | Load free fonts with regex HTTPS interception | `.superpowers/sdd/r2-audit/followup-fonts.png` | Loaded 0/16 free font stylesheets; 16 could not load (offline or blocked), so system fallbacks are shown. |
| 1440-linked-import / P | 1440 x 900 | Connected demo > Sync composition > Import JSON; link off | `.superpowers/sdd/r2-audit/followup-1440-linked-import.png` | Imported; the link to the page is off. Press Sync to Live App to send this composition. |
| 1440-import-conflict / P | 1440 x 900 | Import > Live App; mismatch banner | `.superpowers/sdd/r2-audit/followup-1440-import-conflict.png` | Live view; Changes visible, count4; Live · rev 1 |
| 1440-reapply / P | 1440 x 900 | Mismatch > Reapply Studio overrides; banner settles | `.superpowers/sdd/r2-audit/followup-1440-reapply.png` | Live view; Changes visible, count4; Live · rev 5 |
| 1440-reconnect / P | 1440 x 900 | Connect again after changes; no automatic replay | `.superpowers/sdd/r2-audit/followup-1440-reconnect.png` | Live view; Changes visible, count4; Connected (37 targets) |
| 1440-accept / P | 1440 x 900 | Reconnect > Accept Live App state | `.superpowers/sdd/r2-audit/followup-1440-accept.png` | Live view; Changes visible, count0; Connected (37 targets) |
| 1440-multi-focus / P | 1440 x 900 | Default sheet > 101 Tab keystrokes; only movers are keyboard targets | `.superpowers/sdd/r2-audit/followup-1440-multi-focus.png` | Focus SELECT kitPreset; rgb(90, 58, 167) solid 2px. |

### followup2

Raw observations: [followup2-evidence.json](../../.superpowers/sdd/r2-audit/followup2-evidence.json).

| State / evidence status | Viewport | Visible route and actions | Screenshot | Rendered / computed observation |
|---|---|---|---|---|
| 390-linked-import / P | 390 x 844 | Connected demo > Sync composition > Import JSON; link off | `.superpowers/sdd/r2-audit/followup2-390-linked-import.png` | Imported; the link to the page is off. Press Sync to Live App to send this composition. |
| 390-import-conflict / P | 390 x 844 | Import > Live App; mismatch banner | `.superpowers/sdd/r2-audit/followup2-390-import-conflict.png` | Live view; Changes visible, count4; Live · rev 1 |
| 390-reapply / P | 390 x 844 | Mismatch > Reapply Studio overrides; banner settles | `.superpowers/sdd/r2-audit/followup2-390-reapply.png` | Live view; Changes visible, count4; Live · rev 5 |
| 390-reconnect / P | 390 x 844 | Connect again after changes; no automatic replay | `.superpowers/sdd/r2-audit/followup2-390-reconnect.png` | Live view; Changes visible, count4; Connected (37 targets) |
| 390-accept / P | 390 x 844 | Reconnect > Accept Live App state | `.superpowers/sdd/r2-audit/followup2-390-accept.png` | Live view; Changes visible, count0; Connected (37 targets) |
| 390-multi-focus / P | 390 x 844 | Default sheet > 101 Tab keystrokes; only movers are keyboard targets | `.superpowers/sdd/r2-audit/followup2-390-multi-focus.png` | Focus SELECT kitPreset; rgb(90, 58, 167) solid 2px. |
| 390-library-keyboard / P | 390 x 844 | Return Library; Fraunces card AX axis labels inspected | `.superpowers/sdd/r2-audit/followup2-390-library-keyboard.png` | 16 visible cards; document width390px. |

### guarded_fonts

Raw observations: [guarded_fonts-evidence.json](../../.superpowers/sdd/r2-audit/guarded_fonts-evidence.json).

| State / evidence status | Viewport | Visible route and actions | Screenshot | Rendered / computed observation |
|---|---|---|---|---|
| 1440-first-run / P | 1440 x 900 | Fresh context; harmless HTTPS guard aborted before Studio; no fonts requested | `.superpowers/sdd/r2-audit/guarded_fonts-1440-first-run.png` | 16 visible cards; document width1440px. |
| 1440-consent / P | 1440 x 900 | Load free fonts;16 requests intercepted;system fallbacks shown | `.superpowers/sdd/r2-audit/guarded_fonts-1440-consent.png` | Loaded 0/16 free font stylesheets; 16 could not load (offline or blocked), so system fallbacks are shown. |
| 1440-reload / P | 1440 x 900 | Reload after blocked consent;lazy font requests blocked | `.superpowers/sdd/r2-audit/guarded_fonts-1440-reload.png` | Free fonts are on: families load as their cards scroll into view. |
| 1440-composer / P | 1440 x 900 | Remembered blocked consent > Composer; fallback rendering | `.superpowers/sdd/r2-audit/guarded_fonts-1440-composer.png` | 4 top-level slots; 2 row children; canvas960px. |
| 1440-return / P | 1440 x 900 | Composer > Library after blocked consent | `.superpowers/sdd/r2-audit/guarded_fonts-1440-return.png` | 16 visible cards; document width1440px. |
| 1440-retry / P | 1440 x 900 | Composer > retry Load free fonts;16 aborts;failure status | `.superpowers/sdd/r2-audit/guarded_fonts-1440-retry.png` | 4 top-level slots; 2 row children; canvas960px. |
| 390-first-run / P | 390 x 844 | Fresh context; harmless HTTPS guard aborted before Studio; no fonts requested | `.superpowers/sdd/r2-audit/guarded_fonts-390-first-run.png` | 16 visible cards; document width390px. |
| 390-consent / P | 390 x 844 | Load free fonts;16 requests intercepted;system fallbacks shown | `.superpowers/sdd/r2-audit/guarded_fonts-390-consent.png` | Loaded 0/16 free font stylesheets; 16 could not load (offline or blocked), so system fallbacks are shown. |
| 390-reload / P | 390 x 844 | Reload after blocked consent;lazy font requests blocked | `.superpowers/sdd/r2-audit/guarded_fonts-390-reload.png` | Free fonts are on: families load as their cards scroll into view. |
| 390-composer / P | 390 x 844 | Remembered blocked consent > Composer; fallback rendering | `.superpowers/sdd/r2-audit/guarded_fonts-390-composer.png` | 4 top-level slots; 2 row children; canvas352px. |
| 390-return / P | 390 x 844 | Composer > Library after blocked consent | `.superpowers/sdd/r2-audit/guarded_fonts-390-return.png` | 16 visible cards; document width390px. |
| 390-retry / P | 390 x 844 | Composer > retry Load free fonts;16 aborts;failure status | `.superpowers/sdd/r2-audit/guarded_fonts-390-retry.png` | 4 top-level slots; 2 row children; canvas352px. |

### material

Raw observations: [material-evidence.json](../../.superpowers/sdd/r2-audit/material-evidence.json).

| State / evidence status | Viewport | Visible route and actions | Screenshot | Rendered / computed observation |
|---|---|---|---|---|
| 1440-new-slot / D | 1440 x 900 | Default light Editorial sheet > Slots5 > click newly added Custom slot | `.superpowers/sdd/r2-audit/material-1440-new-slot.png` | Canvas rgb(245, 241, 232); selected text rgb(238, 242, 255). |
| 1440-row-expand / D | 1440 x 900 | Row > Collapse at240; desktop/phone tracks measured | `.superpowers/sdd/r2-audit/material-1440-row-expand.png` | 5 top-level slots; row tracks 254px 508px, 256.656px 513.344px. |
| 1440-converted-text / D | 1440 x 900 | Light sheet Row > Text resets to pale default | `.superpowers/sdd/r2-audit/material-1440-converted-text.png` | Canvas rgb(245, 241, 232); selected text rgb(238, 242, 255). |
| 1440-svg-color / D | 1440 x 900 | Blue SVG > mark colour custom#ff0000; image remains blue | `.superpowers/sdd/r2-audit/material-1440-svg-color.png` | Canvas rgb(245, 241, 232); selected text nontext slot. |
| 1440-rule-align-left / D | 1440 x 900 | Rule Alignment left | `.superpowers/sdd/r2-audit/material-1440-rule-align-left.png` | 5 top-level slots; 2 row children; canvas960px. |
| 1440-rule-align-center / D | 1440 x 900 | Rule Alignment center | `.superpowers/sdd/r2-audit/material-1440-rule-align-center.png` | 5 top-level slots; 2 row children; canvas960px. |
| 1440-rule-align-right / D | 1440 x 900 | Rule Alignment right | `.superpowers/sdd/r2-audit/material-1440-rule-align-right.png` | 5 top-level slots; 2 row children; canvas960px. |
| 1440-rule-color-tailwind / D | 1440 x 900 | Rule colour source tailwind | `.superpowers/sdd/r2-audit/material-1440-rule-color-tailwind.png` | Canvas rgb(245, 241, 232); selected text nontext slot. |
| 1440-rule-color-saved / D | 1440 x 900 | Rule colour source saved | `.superpowers/sdd/r2-audit/material-1440-rule-color-saved.png` | Canvas rgb(245, 241, 232); selected text nontext slot. |
| 1440-rule-color-custom / D | 1440 x 900 | Rule colour source custom | `.superpowers/sdd/r2-audit/material-1440-rule-color-custom.png` | Canvas rgb(245, 241, 232); selected text nontext slot. |
| 1440-focus-ring / D | 1440 x 900 | Click Custom colour input then Tab > Text; visible2px purple ring | `.superpowers/sdd/r2-audit/material-1440-focus-ring.png` | Focus TEXTAREA ; rgb(90, 58, 167) solid 2px. |

### material2

Raw observations: [material2-evidence.json](../../.superpowers/sdd/r2-audit/material2-evidence.json).

| State / evidence status | Viewport | Visible route and actions | Screenshot | Rendered / computed observation |
|---|---|---|---|---|
| 1440-new-slot / P | 1440 x 900 | Default light Editorial sheet > Slots5 > click newly added Custom slot | `.superpowers/sdd/r2-audit/material2-1440-new-slot.png` | Canvas rgb(245, 241, 232); selected text rgb(238, 242, 255). |
| 1440-row-expand / P | 1440 x 900 | Row > Collapse at240; desktop/phone tracks measured | `.superpowers/sdd/r2-audit/material2-1440-row-expand.png` | 5 top-level slots; row tracks 254px 508px, 256.656px 513.344px. |
| 1440-converted-text / P | 1440 x 900 | Light sheet Row > Text resets to pale default | `.superpowers/sdd/r2-audit/material2-1440-converted-text.png` | Canvas rgb(245, 241, 232); selected text rgb(238, 242, 255). |
| 1440-svg-color / P | 1440 x 900 | Blue SVG > mark colour custom#ff0000; image remains blue | `.superpowers/sdd/r2-audit/material2-1440-svg-color.png` | Canvas rgb(245, 241, 232); selected text nontext slot. |
| 1440-rule-align-left / P | 1440 x 900 | Rule Alignment left | `.superpowers/sdd/r2-audit/material2-1440-rule-align-left.png` | 5 top-level slots; 2 row children; canvas960px. |
| 1440-rule-align-center / P | 1440 x 900 | Rule Alignment center | `.superpowers/sdd/r2-audit/material2-1440-rule-align-center.png` | 5 top-level slots; 2 row children; canvas960px. |
| 1440-rule-align-right / P | 1440 x 900 | Rule Alignment right | `.superpowers/sdd/r2-audit/material2-1440-rule-align-right.png` | 5 top-level slots; 2 row children; canvas960px. |
| 1440-rule-color-tailwind / P | 1440 x 900 | Rule colour source tailwind | `.superpowers/sdd/r2-audit/material2-1440-rule-color-tailwind.png` | Canvas rgb(245, 241, 232); selected text nontext slot. |
| 1440-rule-color-saved / P | 1440 x 900 | Rule colour source saved | `.superpowers/sdd/r2-audit/material2-1440-rule-color-saved.png` | Canvas rgb(245, 241, 232); selected text nontext slot. |
| 1440-rule-color-custom / P | 1440 x 900 | Rule colour source custom | `.superpowers/sdd/r2-audit/material2-1440-rule-color-custom.png` | Canvas rgb(245, 241, 232); selected text nontext slot. |
| 1440-focus-ring / P | 1440 x 900 | Click Custom colour input then Tab > Text; visible2px purple ring | `.superpowers/sdd/r2-audit/material2-1440-focus-ring.png` | Focus TEXTAREA ; rgb(90, 58, 167) solid 2px. |
| 1440-modal-focus / P | 1440 x 900 | Export CSS >7Tabs; dialog focus cycles within dialog | `.superpowers/sdd/r2-audit/material2-1440-modal-focus.png` | CSS tokens visible; 1282 displayed chars. |
| 1440-cancel-import / P | 1440 x 900 | Import JSON chooser > cancel; sheet preserved | `.superpowers/sdd/r2-audit/material2-1440-cancel-import.png` | asset.svg loaded for this session. |
| 390-new-slot / P | 390 x 844 | Default light Editorial sheet > Slots5 > click newly added Custom slot | `.superpowers/sdd/r2-audit/material2-390-new-slot.png` | Canvas rgb(245, 241, 232); selected text rgb(238, 242, 255). |
| 390-row-expand / P | 390 x 844 | Row > Collapse at240; desktop/phone tracks measured | `.superpowers/sdd/r2-audit/material2-390-row-expand.png` | 5 top-level slots; row tracks 290px, 88.6562px 177.344px. |
| 390-converted-text / P | 390 x 844 | Light sheet Row > Text resets to pale default | `.superpowers/sdd/r2-audit/material2-390-converted-text.png` | Canvas rgb(245, 241, 232); selected text rgb(238, 242, 255). |
| 390-svg-color / P | 390 x 844 | Blue SVG > mark colour custom#ff0000; image remains blue | `.superpowers/sdd/r2-audit/material2-390-svg-color.png` | Canvas rgb(245, 241, 232); selected text nontext slot. |
| 390-rule-align-left / P | 390 x 844 | Rule Alignment left | `.superpowers/sdd/r2-audit/material2-390-rule-align-left.png` | 5 top-level slots; 2 row children; canvas352px. |
| 390-rule-align-center / P | 390 x 844 | Rule Alignment center | `.superpowers/sdd/r2-audit/material2-390-rule-align-center.png` | 5 top-level slots; 2 row children; canvas352px. |
| 390-rule-align-right / P | 390 x 844 | Rule Alignment right | `.superpowers/sdd/r2-audit/material2-390-rule-align-right.png` | 5 top-level slots; 2 row children; canvas352px. |
| 390-rule-color-tailwind / P | 390 x 844 | Rule colour source tailwind | `.superpowers/sdd/r2-audit/material2-390-rule-color-tailwind.png` | Canvas rgb(245, 241, 232); selected text nontext slot. |
| 390-rule-color-saved / P | 390 x 844 | Rule colour source saved | `.superpowers/sdd/r2-audit/material2-390-rule-color-saved.png` | Canvas rgb(245, 241, 232); selected text nontext slot. |
| 390-rule-color-custom / P | 390 x 844 | Rule colour source custom | `.superpowers/sdd/r2-audit/material2-390-rule-color-custom.png` | Canvas rgb(245, 241, 232); selected text nontext slot. |
| 390-focus-ring / P | 390 x 844 | Click Custom colour input then Tab > Text; visible2px purple ring | `.superpowers/sdd/r2-audit/material2-390-focus-ring.png` | Focus TEXTAREA ; rgb(90, 58, 167) solid 2px. |
| 390-modal-focus / P | 390 x 844 | Export CSS >7Tabs; dialog focus cycles within dialog | `.superpowers/sdd/r2-audit/material2-390-modal-focus.png` | CSS tokens visible; 1282 displayed chars. |
| 390-cancel-import / P | 390 x 844 | Import JSON chooser > cancel; sheet preserved | `.superpowers/sdd/r2-audit/material2-390-cancel-import.png` | asset.svg loaded for this session. |

### closeout

Raw observations: [closeout-evidence.json](../../.superpowers/sdd/r2-audit/closeout-evidence.json).

| State / evidence status | Viewport | Visible route and actions | Screenshot | Rendered / computed observation |
|---|---|---|---|---|
| 1440-asset-before-export / P | 1440 x 900 | Image > load local blue SVG before JSON export | `.superpowers/sdd/r2-audit/closeout-1440-asset-before-export.png` | asset.svg loaded for this session. |
| 1440-asset-json / P | 1440 x 900 | Export JSON of loaded SVG; assetDataUrl empty, imageName retained | `.superpowers/sdd/r2-audit/closeout-1440-asset-json.png` | Composition JSON visible; 3996 displayed chars. |
| 1440-asset-reselect / P | 1440 x 900 | Import own loaded-image JSON; asset.svg reselect placeholder | `.superpowers/sdd/r2-audit/closeout-1440-asset-reselect.png` | Composition imported. Image assets must be reselected. |
| 1440-google-preset / P | 1440 x 900 | Custom kit > Free Google Fonts;16 aborted requests,fallback status | `.superpowers/sdd/r2-audit/closeout-1440-google-preset.png` | Loaded 0/16 free font stylesheets; 16 could not load (offline or blocked), so system fallbacks are shown. |
| 1440-live-text / P | 1440 x 900 | Specimen H1 type Audit temporary heading > Sync > Live App;target h1 changed | `.superpowers/sdd/r2-audit/closeout-1440-live-text.png` | Live view; Changes visible, count3; Live · rev 1 |
| 1440-restore / P | 1440 x 900 | Live App > Restore Page Text;original h1 restored and button disabled | `.superpowers/sdd/r2-audit/closeout-1440-restore.png` | Live view; Changes visible, count3; Live · rev 2 |
| 1440-closed-popup / P | 1440 x 900 | Pop out > close owned popup;Focus disabled and Dock available | `.superpowers/sdd/r2-audit/closeout-1440-closed-popup.png` | Live view; Changes visible, count3; Disconnected (window closed) |
| 1440-dock-closed / P | 1440 x 900 | Closed popup > Dock back;real demo connected again | `.superpowers/sdd/r2-audit/closeout-1440-dock-closed.png` | Live view; Changes visible, count3; Connected (37 targets) |
| 390-asset-before-export / P | 390 x 844 | Image > load local blue SVG before JSON export | `.superpowers/sdd/r2-audit/closeout-390-asset-before-export.png` | asset.svg loaded for this session. |
| 390-asset-json / P | 390 x 844 | Export JSON of loaded SVG; assetDataUrl empty, imageName retained | `.superpowers/sdd/r2-audit/closeout-390-asset-json.png` | Composition JSON visible; 3996 displayed chars. |
| 390-asset-reselect / P | 390 x 844 | Import own loaded-image JSON; asset.svg reselect placeholder | `.superpowers/sdd/r2-audit/closeout-390-asset-reselect.png` | Composition imported. Image assets must be reselected. |
| 390-google-preset / P | 390 x 844 | Custom kit > Free Google Fonts;16 aborted requests,fallback status | `.superpowers/sdd/r2-audit/closeout-390-google-preset.png` | Loaded 0/16 free font stylesheets; 16 could not load (offline or blocked), so system fallbacks are shown. |
| 390-live-text / P | 390 x 844 | Specimen H1 type Audit temporary heading > Sync > Live App;target h1 changed | `.superpowers/sdd/r2-audit/closeout-390-live-text.png` | Live view; Changes visible, count3; Live · rev 1 |
| 390-restore / P | 390 x 844 | Live App > Restore Page Text;original h1 restored and button disabled | `.superpowers/sdd/r2-audit/closeout-390-restore.png` | Live view; Changes visible, count3; Live · rev 2 |
| 390-closed-popup / P | 390 x 844 | Pop out > close owned popup;Focus disabled and Dock available | `.superpowers/sdd/r2-audit/closeout-390-closed-popup.png` | Live view; Changes visible, count3; Disconnected (window closed) |
| 390-dock-closed / P | 390 x 844 | Closed popup > Dock back;real demo connected again | `.superpowers/sdd/r2-audit/closeout-390-dock-closed.png` | Live view; Changes visible, count3; Connected (37 targets) |

## Self-review and cleanup

Applicable anti-patterns: AP1-4 boundaries were exercised only through existing
visible UI; no messaging, URL or DOM parser was implemented. AP5 explicit preset
accept/decline and import outcomes were recorded. AP6-9 target restoration and
handshake code were not altered; real Studio/demo evidence was used where the
composition crosses the bridge. AP10 paid kits remained empty and the corrected
font probes use fallbacks. AP11-12 no protocol/doc rename occurred; the new-slot
contrast class was checked through add, conversion and row-child creation.
AP13 every owned browser/context and both server handles closed in finally.
AP14 engines/gates not run and the initial HTTPS failure are disclosed. AP15 no
runtime/history change or commit was made; this document is the task's audit
record. Reference provenance, owner skills and all shared docs remain untouched
by the audit writer.

Each phase has a `*-cleanup.json` with owned context count and closed server
addresses. [cleanup-verification.json](../../.superpowers/sdd/r2-audit/cleanup-verification.json)
records fresh TCP checks of those ports after completion; every connect attempt
failed. Shared browser/driver handles were explicitly closed, not killed by
name. These checks do not claim the checkout had no unrelated owner processes.
The final tracked delta of this writer is only this report. No write endpoint
request occurred in the logged guarded phases; no runtime diff exists. Full
unit/browser gates and commit/push operations remain the controller's work.

## Residual coverage gaps

- External Google/Adobe successful loading, actual face fidelity and paid kit
  behavior were intentionally not accepted evidence. Initial isolation failed;
  request counts for that period are unknown. Guarded failure, consent memory
  and fallback behavior are verified in the fresh rerun.
- Firefox, WebKit, touch hardware, native screen-reader interaction and OS
  file-dialog pixels were not tested. Phone is a viewport profile only.
- Every named semantic control/preset/slot/filter branch was inventoried, but
  arbitrary text/number values and the Cartesian product of22 colours x11
  shades x16 families x12 roles xall layouts were not exhausted. Phone repeats
  structural branches; every cut/axis/palette option is traversed on desktop.
- Import covers own legacy-format output, malformed, missing slots, empty slots,
  cancellation and linked mismatch. Oversized/hostile/future-version JSON and
  every historical Adobe-family alias are not covered by this UX audit; existing
  security tests were not rerun and their protection is not inferred.
- Every image format variant and native picker acceptance filters were not
  separately probed. Loaded-SVG JSON export/import and its reselect placeholder,
  SVG/PNG load and JPEG refusal were rendered on both profiles.
- Per-element inspector edits/reset, arbitrary navigation, arrangement guards
  and server writes are outside the
  Library/specimen traversal; no change to these behaviors is claimed. The
  relevant composition bridge transitions were exercised on the current demo.
- Window-manager focus activation cannot be established from headless pixels;
  the Focus button action, disabled state after close, Dock and reconnect choice
  were visited. Native multi-monitor positioning was not tested.
- Dark Library was rendered on both profiles, but full dark Composer chrome
  contrast and all disabled-tooltip accessibility combinations were not swept.
- There is no search/no-results/detail/family-transfer/empty-canvas control to
  visit. Their absence is current UI inventory, not invented failing states.

The audit is complete as a bounded report with those limitations. It does not
claim every possible state, engine or security case was checked, and does not
authorize R2/R3 implementation. Independent review and controller reconciliation
remain required before the R2 prerequisite can be marked accepted.
