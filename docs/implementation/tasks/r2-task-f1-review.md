# R2.7F1 independent implementation review

Date: 2026-10-08. Verdict: **Approved**.
Branch: `feat/r2-detection`.
BASE/HEAD: `653d71610b409e59d542391b7010bcc8bd61c3a8`.
Scope: the staged thirteen-path F1 fixture/test change, its complete report,
and the controller's accompanying provenance and execution records.

## Findings

No Critical, Important or Minor defect found in this bounded change.
This accepts the static fixture corpus and its rendered characterization.
It does not accept a detector, framework adapter, route integration or timing
budget implementation. R2.7F2a and R2.7F3 remain incomplete.

## Contract and quality checks

- Read the complete F1 brief and report, all authored fixture sources and
  literal JSON oracles, the complete new test module, current shared harness,
  approved detection contract/R2.7F1 and execution constraints. Ownership
  matches the thirteen planned paths. No runtime or existing vendor edit is
  present. The unchanged Bootstrap 5 hero retains its original tags, IDs,
  text, button and script integration; its title still renders at 40px.
- Bootstrap 4 and 5 independently render 20/25 eligible parents and 16/18
  identities. The oracles explicitly carry all five normalized properties,
  counts, full identities, variants and complete bindings. Semantic class
  selectors and author-ID metadata agree with the real elements. Trimmed
  Editorial has two variants; lowercase editorial is a separate identity.
  The Bootstrap 5 variables and the banner-free Bootstrap 4 fallback input
  are rendered evidence, with adapter selection explicitly deferred.
- The large fixture has exactly 5,000 eligible light-DOM direct-text parents,
  twenty distinct signatures and 250 members each. Independent probes also
  checked the complete g00.000 through g19.249 ID set and each binding's
  declared ID range. Nested parents remain separate; two direct text nodes
  on the outer parent count once. Range geometry includes display:contents
  despite its zero element box. Hidden, transparent, zero-area, chrome and
  out-of-scope text are excluded; below-viewport text is included.
- All seven near-duplicate cases preserve exact groups while distinguishing
  inclusive size/weight/tracking boundaries, values immediately outside them,
  and different family/case. Native a/B/7 keystrokes render a/aB/aB7, dispatch
  three input acknowledgements and preserve the entire corpus. The state-only
  animation-frame heartbeat adds no text parent. These are future performance
  inputs; this task makes no <=2,000ms detector claim.
- HTTPS blocking precedes navigation, uses the verified prefix regex and
  exercises two fetch canaries. An earlier local CORS-enabled fulfillment
  remains active. Independently removing only the abort registration in an
  in-memory copy fails the guard assertion without external browser contact.
  Context ownership and cleanup use the existing shared driver APIs; the
  fixture test introduces no server, package install or second driver.
- Four independent mutations were rejected: changed g01 font size, a newly
  visible 5,001st parent, loss of the nested parent and removal of the HTTPS
  abort guard. The three page mutations were restored and the complete oracle
  rechecked after each. No source bytes were edited by these probes.
- Addendum 4/D060 and the scoped Git attribute agree with strict Bootstrap 4
  byte preservation. Existing Bootstrap 5 accepts only its documented exact
  LF/CRLF forms. The staged controller records distinguish BASE CI, writer
  evidence, current review and unfinished tasks. F1 checkboxes remain pending
  controller closure. Fixture-only changes require no CHANGELOG entry.
- The F3 durable brief is the same previously reviewed 84-line brief; no
  separate scratch draft exists. Its current ownership, async history and
  same-URL behavior, literal oracles, isolation and focused gates still match
  that preparation verdict. The combined detection brief's body compares
  exactly with its approved scratch draft; only its first heading loses
  "draft". Neither preparation approval claims implementation completion.

## Independent verification

```powershell
$env:PYTHONPATH='tests'
$env:FKS_ENGINES='chromium'
python -m unittest test_r2_static_fixtures test_support -v
python scripts/verify.py --static-only
node --check fontkit-bridge.js
node --check fixtures/large-page/app.js
python -m ruff check tests/test_r2_static_fixtures.py
python -m ruff check . --exclude .agents
python -m ruff check .
git diff --cached --check
git diff --check
```

Focused Chromium: **44 tests, 28.925 seconds, OK, zero skips** (ten new fixture
tests and 34 support tests). Static checks pass: 96 unique Studio IDs, inline
JavaScript syntax and three supplied provenance hashes. Both Node syntax
checks, scoped/product-tree Ruff and staged/unstaged whitespace pass.
Exact `python -m ruff check .` exits 1 for the same four preserved owner-skill
findings at scan.py lines 21, 23, 24 and 294; that exact gate is not passing.

Read-only Python stdin probes used subprocess Git blob reads, hashlib,
urllib.request against the two recorded tagged Bootstrap 4 source URLs and a
fresh owned TemporaryDirectory under .superpowers/sdd/r2. The checkout command
was `git -c core.autocrlf=true checkout-index --prefix=<fresh-directory>/ --`
followed by the two Bootstrap 4 vendor paths. Current bytes, staged blobs,
fresh checkout bytes and independently fetched upstream bytes are identical:

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| Bootstrap 4 CSS | 162264 | f886516f3d41e9e7bd994c7f7a39a89cafae9483f90396cb0ddeafe8d1ea5e72 |
| Bootstrap 4 LICENSE | 1131 | 53d2513c8df48a817d70537cc906b8e9c7bf2513328ff66847894773e615b37e |

`git check-attr --cached text -- <vendor paths>` reports text unset only for
the new Bootstrap 4 files, unspecified for the existing Bootstrap 5 files.
All three Bootstrap 5 vendor index blobs equal BASE; current CSS/LICENSE/JS
bytes equal their exact CRLF conversion, with no content change. The complete
Bootstrap 4 MIT notice and upstream banner were checked. Git hash-object with
each path's attributes confirms all thirteen tested source/test files and
.gitattributes match their staged blobs. The reviewed test blob is
`a53f9ae0323e70207de9a3aec161e9b3fd13d28d`; the attribute blob is
`ee51cc6eb9232cb60ad1840c8e4abff83e2266db`.

The extra Python stdin browser probe completed in 8.306 seconds, checked
complete binding metadata/identity uniqueness on all three fixtures and
rejected the four mutations described above. All review contexts closed in
finally; the shared driver/browser closed at process exit. The fresh checkout
directory was removed by its owning TemporaryDirectory. No fixture, source,
vendor, index, HEAD, branch, dist or bundle bytes were changed. Only this review
record is written.

## Evidence limits

Live graph status/coverage confirmed font-kit-studio-local ready, generation
2026-10-07T17:07:14Z, 2637 nodes/12760 edges. Coverage was rechecked for all
thirteen F1 paths, report, plan, attributes and support.py. Fixtures/docs are
excluded/not tracked; the new test is not tracked; attributes/support report
metadata_changed. Current direct source, staged blobs and real Chromium
rendering decide this review. No graph-completeness claim is made.

The report's historical RED and 24 distinct final mutation cases were read;
this review independently reran the final focused gate and four risk mutations,
not all historical writer commands. Full Python/frontend/package/Firefox suites
and commit-message checks were not run for this authorized focused fixture
review. BASE CI results were read as controller records, not rerun or claimed
as evidence for these new fixtures. FIRST detector performance and runtime
acceptance remain requirements of later tasks.

## Bookkeeping closure review (2026-10-08)

Verdict: **Approved**. At unchanged HEAD `653d716`, all thirteen staged
source/test blob IDs and the .gitattributes blob exactly match the Approved
snapshot; their current checkout hashes match too. A complete before/after
comparison of plan checkbox lines finds exactly five changes, all F1 items
from unchecked to checked. Every other task checkbox is unchanged. F2a/F3,
protocol/detection and later runtime acceptance stay open, with none of their
source staged. The new plan row, Current state and latest ledger event accurately
record fixture-only approval and the controller's complete report/verdict read
before the pending atomic landing. The earlier pending-closure wording above
describes the implementation-review snapshot. No browser gate is rerun for this
records-only closure. Only this review addendum is written; no index mutation.
