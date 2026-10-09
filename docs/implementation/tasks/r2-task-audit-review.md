# R2 prerequisite Library/Composer audit: independent review

Date: 2026-10-08. Initial verdict: **Approved with fixes**.

Scope: the bounded read-only audit and controller reconciliation, not R2
runtime approval or authorization to fix the legacy UI. Review BASE and HEAD:
`142aa9dc0273efc19e14a67d88f66726b6d665ae`; branch
`docs/library-composer-audit`. The reviewed report has 1,050 lines and SHA256
`D454F870606884EB3D593E78D65102968B3C0CC2F5581CE862A7788F64B524DE`.

## Strengths

- The report distinguishes released behavior from future design gaps, records
  reachable entry/action sequences, and discloses absent controls without
  manufacturing failing states. The evidence register and residual gaps limit
  the completeness claim (report lines 94-115, 274-286, 1016-1050).
- D059 is candid about the failed initial guard and unknown contact counts.
  Eight superseded rows remain visibly marked S; accepted font evidence uses
  pre-navigation regex interception. No whole-audit zero-contact claim remains
  (report lines 19-52; deviations.md:53).
- All five core findings are supported by current rendered behavior. The
  existing acknowledged Changes ledger is correctly separated from unsent
  specimen state and composition/token exports (report lines 200-230).
- The five controller document changes reconcile the report without changing
  runtime files, protocol, thresholds, release, or implementation ownership.
  R2.0 remains unchecked pending this review and final owner approval. Addendum
  2 retains the R3/later ownership of legacy defects and future output; R2.S2
  preserves existing behavior and separates role-preview CSS from exports.

## Issues

### Critical

None found in this bounded review.

### Important

None found in this bounded review. The P1 runtime defects are existing audited
findings, not defects introduced by this documentation delta or permission to
fix them now.

### Minor: correct before accepting the audit record

1. **LC-05 swatch claim is inaccurate for its recorded typing path.**
   `docs/implementation/audit-2026-10-08-library-composer.md:188-189` says
   "Swatch changes" after typing `#ff0000`. On both fresh 1440 and 390 profiles,
   the swatch remains `rgb(230, 200, 141)` before and after typing; the field
   retains `#ff0000` and the own-fill SVG remains blue. The inspected screenshot
   also shows the unchanged yellow swatch. `fontkit-studio.html:2771-2818`
   explains this: typing updates slot state and calls renderCanvas; it does not
   recreate the inspector or update its swatch. Replace that clause with the
   field's actual visible result, or explicitly describe the stale swatch. Keep
   the core loaded-image/placeholder limitation and its R3 classification.
   Evidence: `review/probe-evidence.json` swatch_before/swatch_after_typing and
   `review/390-svg.png`, under `.superpowers/sdd/r2-audit/`.

2. **LC-01 source citation ends before the pale default.**
   Report lines 130-131 cite `fontkit-studio.html:2121-2142`, but the
   `colorHex: "#eef2ff"` assignment is at line 2144. Extend that source range.
   The rendered contrast finding itself is confirmed independently.

3. **Make superseded guard captions unambiguous when read alone.**
   Report lines 361-362 and 701 still describe their initial action as HTTPS
   blocked, despite S status and the clear top-level disclosure. Prefer
   "initial guard intended; failed (superseded)" for those action cells. This
   avoids a standalone table row sounding like accepted isolation evidence.
   Do not change the original observed loaded/failure result or erase the
   failed setup record.

The controller's cleanup wording correction is accepted: the current ledger
says no successful connection was established in 26 saved-port checks. Saved
`connect_ex=10035` is not a literal connection-refused response. Server handle
closure is evidenced separately by the finally cleanup; the report itself
accurately says every connect attempt failed at lines 1007-1011.

## Reading and evidence basis

Read AGENTS.md and global-rules.md in full; the approved audit brief in full;
the entire 1,050-line report in bounded chunks; product direction and approved
typography design in full; R2 scope/prerequisites/Addenda 1-2/R2.0/S1/S2;
ledger Current state and current R2 events; and the complete five-document
delta against BASE. Read current source around the material findings, the
server factory/setup and shared browser/context lifecycle. The requesting-code-
review template and verification-before-completion skill informed this review.
Agent-browser's skill was read; its CLI is unavailable on PATH, so the approved
existing Playwright fallback was used. No installation or browser download.

Tier 2 graph health was independently confirmed: font-kit-studio-local,
ready, 2,637 nodes and 12,760 edges; coverage reports generation
2026-10-07T17:07:14Z. Docs, scripts and scratch are excluded; AGENTS/runtime/
support report metadata_changed with no recorded gap. Direct current reads
and runtime probes supply the evidence. The parent Composer entry/trace packet
is orientation only; no graph completeness or runtime absence claim follows.

`python .superpowers/sdd/r2-audit/check-records.py` was read and independently
run. It confirms P513/D92/S8; 613 unique PNG files with valid headers, exactly
matching raw-record screenshot membership; 59 local document links; 26 fresh
saved-port checks with no successful connection; and 79 accepted guarded HTTPS
intercepts (2 harmless probes and 77 font attempts). These checks do not prove
every screenshot's visual claim, arbitrary state combinations, or full WCAG
conformance. Material screenshots were independently inspected and reproduced.

## Focused Chromium reproduction

Command (PowerShell):

```powershell
python .superpowers/sdd/r2-audit/review/probe.py > .superpowers/sdd/r2-audit/review/probe-output.txt
```

Final run: exit 0; Chromium 151.0.7922.34; fresh 1440x900 and 390x844 profiles;
six contexts total. Each context first aborts a separate harmless HTTPS probe
with regex `^https://` and closes the probe page before Studio navigation.
Two real loopback servers use port 0 and sync=False. The final run logs 38
HTTPS aborts (6 guard probes, 32 font stylesheet attempts), zero pageerrors,
and no non-GET/HEAD request. Offline consent visibly reaches the 16-load
failure message on both profiles. No external request succeeds, credential is
entered, or write endpoint is exercised in this independent run.

- LC-01: Slots 5 creates Custom text with foreground rgb(238,242,255) on
  rgb(245,241,232), contrast 1.008:1, on both profiles. Screenshot and computed
  values agree. The supplied new-slot default, not user-chosen combinations,
  is the defect.
- LC-02: current text inspector AX contains unnamed combobox, slider,
  spinbutton and textbox entries. Its adjacent visual labels yield labels=[]
  with no aria-label. Row controls already have for/id associations; the
  report correctly scopes the unnamed legacy controls. Library-axis source
  and supplied AX evidence also agree; this review did not repeat every axis.
- LC-03: 110 real Tab keystrokes on each default sheet leave Wordmark selected
  and expose no canvas-slot selection target. Focusing the second slot's Move
  down and pressing Enter changes its DOM order while keeping Wordmark
  selected. This closes the keyboard-activation alternative to the writer's
  pointer-mover probe. Pointer selection does open another slot's inspector.
- LC-04: real typing of #102030 yields rgb(16,32,48); typing oops and Tab retains
  oops while preview falls back to rgb(24,23,20), with only the previous preset
  status and no invalid-colour explanation, on both profiles.
- LC-05: real SVG upload shows the blue #336699 asset after typing #ff0000.
  The image's source remains the own-fill SVG. The field stays enabled and
  gives no loaded-image colour limitation. The swatch qualification above is
  necessary. Uploaded SVG remains an img; no markup parsing is recommended.
- Manual exported composition JSON reimports with the image data omitted and
  the visible asset.svg reselect placeholder, on both profiles.
- With real Studio and bridge, unsent specimen typing leaves Changes hidden
  on Specimen and Changes 0 on Live App. Explicit Sync produces Changes 3 and
  canonical CSS variables. This is acknowledged live output, not a standalone
  specimen export or future unified model.
- Document widths remain 1440 and 390 in the exercised states. On narrow
  Studio, the 1440 Live App control yields previewScroller width340,
  scrollWidth1440 and overflow-x:auto, confirming intentional inner scrolling.

Raw reviewer files: probe.py, probe-output.txt, probe-evidence.json;
1440-inspector-ax.txt and 390-inspector-ax.txt; 1440-roundtrip.json and
390-roundtrip.json; screenshots 1440-new-text.png, 390-new-text.png,
1440-invalid-color.png, 390-invalid-color.png, 1440-svg.png, 390-svg.png,
1440-changes.png, 390-changes.png. All are local scratch under
`.superpowers/sdd/r2-audit/review/`, not committed assets or suite tests.

## Fresh fast checks

| Command | Result |
|---|---|
| python scripts/verify.py --static-only | exit0; 96 unique IDs, inline JS syntax and all three supplied-v0.1.1 provenance hashes pass; suite explicitly skipped |
| node --check fontkit-bridge.js | exit0 |
| python -m ruff check . | exit1; the same four preserved untracked owner-skill errors at scan.py:21,23,24,294 |
| python -m ruff check . --exclude .agents | exit0; All checks passed |
| git diff --check | exit0; LF/CRLF notices only |
| git diff --exit-code BASE -- fontkit-studio.html fontkit-bridge.js scripts tests demo | exit0; no runtime/test/demo delta |
| python .superpowers/sdd/r2-audit/check-records.py | exit0; register/path/link/guard/port results above |

Full Python/Node suites, frontend gate and Firefox were not run, as this approved
read-only audit review is bounded to focused Chromium probes. No observation
suggested a concrete Gecko delta. No automated suite count or compatibility
claim follows. Commit-message gates and final controller landing checks are
outside this review; no commit was created.

## Cleanup and assessment

All owned contexts and shared browser/driver handles close in finally; both
owned servers shut down and close. The final run's ports 55953 and 55954 produce
connect_ex10035 after closure, with no successful connection. This does not
claim literal ECONNREFUSED or inspect unrelated owner processes. No tracked
file other than this review was written by the reviewer; no index/branch/HEAD,
source, shared doc, commit/push or external-review mutation was performed.

**Approved with fixes.** Correct the minor factual/citation/caption issues in
the report before accepting the audit prerequisite, then obtain a scoped
re-review of those edits. The bounded coverage and phase reconciliation are
otherwise sufficient. This verdict does not approve the R2 runtime plan,
legacy fixes, merging, or a release.

## Final scoped verdict (2026-10-08)

**Approved.** The three requested minor correction categories are resolved.
Reviewed report: 1,051 lines; SHA256
`FE799AC9D94396E52ED170F633233F10E5ECD5528A844A0AEF558189B3467EA1`.
The exact BASE/HEAD and branch remain unchanged.

Read the complete saved correction diff and the updated finding/register
passages. An independent replacement comparison against
`.superpowers/sdd/r2-audit/report-before-minor-fixes.md` confirms that only the
three requested categories changed; its original hash is the initial reviewed
D454F870... digest. LC-01 now includes source line 2144. LC-05 now reports the
retained #ff0000 field, unchanged blue image and previous swatch colour on this
typing path, agreeing with the independent probe. All three S-row guard
captions explicitly describe the failed initial guard and supersession while
preserving the original observations. No new runtime scope follows.

Fresh `python .superpowers/sdd/r2-audit/check-records.py` exits 0: P513/D92/S8,
613 unique PNG paths/header/raw-record matches, 59 local document links,
26 saved-port checks with no successful connection and 79 accepted guarded
HTTPS intercepts. `git diff --check` exits 0 (LF/CRLF notices only), and the
explicit runtime/test/demo diff against BASE remains empty. No browser rerun
was needed for these evidence-only wording corrections; the initial focused
Chromium evidence and all disclosed limits still apply. Exact Ruff's known
owner-skill findings are not claimed fixed.

This final verdict accepts the bounded audit record and its reviewed phase
classification. It permits the controller to close R2.0's audit execution and
classification items after its final bookkeeping consistency check. Final R2
engine-plan approval and execution constraints remain open. No runtime fix,
merge, release, or external review is authorized by this verdict.

## Publication-record scoped verdict (2026-10-08)

**Approved for the currently pending-CI record.** Read the complete committed
five-document reconciliation delta from 142aa9d to
`e15d200db2ffb32e56ea0b17dcaecda5b652979f` and the complete current two-document
publication delta. The committed closure matches the final audit verdict:
only R2.0 audit execution/classification are checked; final engine approval and
execution constraints remain unchecked. Current state, brief and roadmap agree
that the bounded audit is accepted and R2 remains planned. No runtime scope
or deviation beyond D059 is added.

Direct read-only commands `gh pr view 18 --json number,url,state,isDraft,
baseRefName,headRefName,headRefOid,additions,deletions,files` and
`gh run view 37861702853 --json headSha,status,conclusion,url` confirm an open
draft PR #18 against main on docs/library-composer-audit at the exact local
HEAD e15d200. The run is in_progress with an empty conclusion at that same
head. The publication event accurately says pending and claims no hosted pass.
The PR link belongs in the roadmap and does not imply an engine PR or merge.

PR additions1341 + deletions12 and local seven-file numstat confirm 1,353
changed lines for the published audit baseline, with no generated/rename churn.
The pending follow-up is separate from that baseline count. The report hash
remains FE799AC9D94396E52ED170F633233F10E5ECD5528A844A0AEF558189B3467EA1.
Fresh git diff --check exits0, and the runtime/test/demo diff from original
BASE to current HEAD is empty. No local browser/full-suite rerun was performed
for these publication records. The exact-head CI result/advisories still need
the controller's completed log review and a scoped record confirmation before
landing any replacement completed-CI wording.

## Completed-CI record scoped verdict (2026-10-08)

**Approved.** The completed-CI publication event matches the saved job metadata,
quality-gate summaries and a fresh direct gh run view. Run 37861702853 is
completed/success at exact HEAD e15d200db2ffb32e56ea0b17dcaecda5b652979f, with
all 12 jobs completed/success. The event explicitly limits this proof to the
published audit baseline and does not attribute it to a future metadata commit.

Independently read all twelve job status/name/conclusion records, all thirty
frontend PASS records and its summary, all twelve Chromium skip records, and
both unittest summaries from audit-ci-jobs.json and audit-quality.log. Chromium
reports Ran 859 in 615.786s, OK (skipped=12); Firefox reports Ran 51 in 103.326s and
OK with no skip records. Frontend reports 30 of 30 finished, seven blocking passes,
23 advisory runs, zero ADVISORY/SKIP/FAIL lines and 332 REPORT lines; counting
actual frontend messages confirms 30 PASS and 332 touch reports. The controller
read each advisory report; this scoped review confirms the complete count and
summary rather than independently replaying the touch-target audit.

The current workflow's installed-fixture selections at lines 270 and 309 include
all eleven skipped fixture cases other than test_one_command_messages host
refusal. That excluded case remains clearly disclosed; a successful job is
not treated as proof of that omitted test. No workflow change follows. Coverage
was checked for these additional evidence paths; raw scratch is excluded, so
the results above rely on exact reads, not graph completeness.

Read the complete final two-document publication diff: the PR #18 link and phase
remain unchanged; final R2 work-order approval is open. Report hash remains
FE799AC9D94396E52ED170F633233F10E5ECD5528A844A0AEF558189B3467EA1. Fresh
git diff --check exits 0 with only LF/CRLF notices. No new local browser or full
suite was run for this record confirmation. No issues found; the controller may
land the reviewed publication records under existing task-branch authority.
