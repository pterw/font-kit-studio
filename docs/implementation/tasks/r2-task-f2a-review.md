# R2.7F2a independent implementation review

Date: 2026-10-08. Verdict: **Approved**.
Root: feat/r2-detection.
HEAD: 6a7327bd2d901f4c668c476a8048658f82c682b6.
Writer BASE: 653d71610b409e59d542391b7010bcc8bd61c3a8.
Scope: the staged nine-path React fixture/test change and its accompanying
durable report, S1 preparation brief and controller ledger changes.

## Findings

No Critical, Important or Minor defect found in this bounded change.
This accepts the React baseline, replacement and CSS HMR fixture inputs.
F2b role preview/apply/clear, detector/adapter implementation and S1 runtime
acceptance remain separate. F2a checkboxes await controller closure.

## Contract and source checks

- Read the complete F2a brief, 105-line durable report and complete original
  implementer report, including the earlier block, recovery and retained-copy
  limitations. Read all nine owned files, the full generated lockfile and
  current fixture-support/Vite lifecycle helpers. The applicable approved
  binding detection/adapter contracts, F2a/F2b boundaries and constraints
  distinguish characterization from future engine behavior.
- The private ESM package has exact Vite 8.3.2 and React/react-dom 19.3.0
  pins, dev/build scripts and no React plugin. Package-lock v3 agrees with
  the manifest, has 44 records, registry resolved URLs and integrity hashes;
  installed direct-dependency versions match the lock. No package runtime,
  existing fixture, shared helper, workflow or app runtime edit is staged.
- Literal schema/version and five-property normalized tuples describe six
  direct-text parents in five semantic rows, with four distinct styles.
  Title/body author roles and IDs, a hash-only paragraph and stable-copy
  class remain distinct binding inputs. Tests observe generated class names
  without predicting an exact hash algorithm or claiming adapter selection.
  An extra independent light-DOM range traversal confirms exactly six
  eligible parents and four distinct signatures.
- Enter and Space activate the actual React button/state update. The keyed
  section replaces title/body nodes and text nodes; old handles detach,
  deterministic new text renders and every literal tuple remains correct.
  Handles are disposed in finally. No evaluate-based replacement or fake
  bridge is used for these fixture inputs.
- CSS HMR uses real scratch-source writes for 40px -> 44px -> 40px. Tests
  check computed fonts, the document marker, retained title node, generation-1
  React text and stable comparison content. Explicit scoped naming and CSS
  dependency acceptance are deliberate fixture configuration. The source,
  reports and tests correctly call this CSS HMR, with no Fast Refresh claim.
- Installed-fixture coverage fails closed with FKS_REQUIRE_FIXTURES=1 via
  unchanged require_fixture. The new test characterizes that existing helper
  directly, without adding an availability wrapper or future acceptance skips.
  Every app uses a separate copy excluding .git/node_modules/dist/.fks-*.
  Vite binds 127.0.0.1 with an OS-assigned port; process waits, reader exit and
  listener refusal establish normal cleanup. Shared source bytes are checked.
- Blank-page fetch canaries prove both HTTPS requests are aborted before app
  navigation, with zero fallback requests. The earlier local CORS fulfillment
  stays active; removing only the later abort route produces two local
  fulfillments and a failed guard assertion. Successful app runs add no HTTPS
  requests. The former aborted-navigation canary is absent from current code.
- Scratch production build emits three assets without bridge entry points,
  role stylesheet markers or Font Kit instrumentation. This is the private
  fixture's production boundary, not new package-plugin production coverage.
- The staged S1 brief body exactly matches the independently approved scratch
  draft; only its heading loses "draft". The ledger distinguishes complete F1,
  pending F2a acceptance and F3/detection work in flight. S1 remains preparation
  approval requiring committed R2.2. No fixture-only CHANGELOG line is needed.

## Independent gates

```powershell
$env:PYTHONPATH='tests'
$env:FKS_ENGINES='chromium'
$env:FKS_REQUIRE_FIXTURES='1'
python -m unittest test_r2_react test_support -v
python scripts/verify.py --static-only
node --check fontkit-bridge.js
node --check fixtures/vite-react-css-modules/vite.config.js
python -m ruff check tests/test_r2_react.py
python -m ruff check . --exclude .agents
python -m ruff check .
git diff --cached --check
git diff --check
```

Focused Chromium: **39 tests, 31.957 seconds, OK, zero skips** (five fixture
tests and 34 support tests). Static: 96 unique Studio IDs, inline JS syntax
and all three supplied provenance hashes pass, with browser tests explicitly
skipped by --static-only. Both Node checks, scoped/product-tree Ruff and both
whitespace checks independently exit 0. Exact Ruff exits 1 for the same four
preserved owner-skill findings at scan.py lines 21, 23, 24 and 294; it is not
reported as passing.

Read-only Python stdin inventory/build probes verify lock/direct installed
versions and copy the eight staged fixture files into an owned temporary
directory under the fixture. The build command is
`npm.cmd --prefix <owned-scratch-project> run build`, using the existing local
installation without changing node_modules or root dist. Independent build:
16 modules, 263ms, three assets (HTML 406 bytes, CSS 528, JS 220921). Each was
scanned for fontkit-bridge.js, /@fontkit/, design:hello, __fontkitBridge and
data-fontkit-role-style; none appears. A first completed build probe encountered
a cp1252 output-encoding error while printing its captured checkmark. Its
temporary directory closed normally; rerun with PYTHONIOENCODING=utf-8 supplies
the complete successful evidence above. This display error is not a product RED.

## Independent mutation probes

Python stdin probes run existing single behavior tests with unittest.TestResult,
using mutations in each owned scratch copy or an in-memory copy of the test
module. Shared staged fixture/test bytes are never modified. Each scratch
source mutation restores its exact original bytes before owned Vite shutdown.

| Mutation | Observed rejection | Time |
| --- | --- | ---: |
| Empty module CSS | Literal rendering differs: five failures, one test | 3.759s |
| Remove section key | Updated text leaves old element connected: one failure | 3.226s |
| Remove CSS dependency acceptance | Document marker lost to full reload: one failure | 3.913s |
| Write 43px while retaining the 44px expectation | Actual 44px condition times out: one error | 13.472s |
| Remove HTTPS abort registration in memory | Aborts 0, local fallback 2, fulfilled/fulfilled: one failure | 2.569s |

All five probes reject their targeted behavior; no test assertion was deleted.
CSS restores to 40px in the HMR probe's finally. Page contexts close, Vite exits,
readers finish and owned ports refuse connections through the tested cleanup.
The subsequent independent six-parent/four-signature probe passes. Before/after
byte snapshots of all nine shared source/test files are equal; the set of root
.fks-* copies is unchanged. Both owned production-build directories are removed
by their TemporaryDirectory owners. Five older ignored interrupted copies under
C:/fks/r2f2a remain outside this review; no deletion was attempted or all-copies-
removed claim made. The underlying earlier browser close stall remains unresolved.

## Reviewed snapshot and limits

Current checkout hashes match these staged blob IDs after all probes:

| Fixture-relative path (test is repo-relative) | Git blob |
| --- | --- |
| expected-styles.json | 15d9041b5915a6cf02d258897bcd59ce9f39a825 |
| index.html | 0ce9ea4ded4bca080aa72fd64866127180a8740b |
| package-lock.json | e54289e8399998b28fec59295391f00fd0b653fe |
| package.json | dc955aaa2534e887c1f3ebfe5a5b5b6a15c67d8b |
| src/App.jsx | e34732579cd6fbdb6f9a567c5bd7823dcd778d23 |
| src/App.module.css | 1710d47eb1543e62f4282e9f432538bbd13e4c56 |
| src/main.jsx | 57eed31152b345da5d5aca9d58873fb90af5ee3c |
| vite.config.js | 1534a9f1d0d2f000bd778788d75fd25c74576f4c |
| tests/test_r2_react.py | cdf43a92ac7ee3d4303e861ddcf1ef4328130150 |

Live graph status/coverage confirmed font-kit-studio-local ready, generation
2026-10-07T17:07:14Z, 2637 nodes/12760 edges. Coverage includes every nine-path
F2 input, relevant support/lifecycle helpers, report, S1 brief and plan. Fixtures/
docs are excluded, the new test not tracked, helpers metadata_changed. Current
direct source, staged blobs and real Chromium behavior decide acceptance; no
graph-completeness or detached-index claim is made.

npm ci/audit was not rerun by this read-only reviewer; the installed pin/lock
agreement is independently checked and the controller's fresh install evidence
remains separate. Historical writer RED commands were read, not reproduced;
final rendering, cleanup and all five mutation classes were independently run.
Full suites/frontend/package/Firefox and commit-message gates are not run for
this focused fixture review. There is no detector budget, role preview or future
implementation acceptance. Only this review file is written; source, index,
HEAD and branch remain unchanged.

## Bookkeeping closure review (2026-10-08)

Verdict: **Approved**. HEAD remains 6a7327b. All nine staged source/test blob
IDs and current checkout hashes exactly match the Approved snapshot above.
Comparison of every plan checkbox against HEAD finds only four changes, all
F2a items from unchecked to checked. F2b, F3, detection and Studio runtime tasks
remain unchanged/open. F3's nine source paths and report are unstaged and outside
this verdict/landing; production bridge/Studio source is not staged.

The plan row, report's Approved/landing-pending status, Current state and latest
ledger acceptance event agree with fixture-only completion. The ledger keeps
controller 39/34.245s and independent 39/31.957s results separate, discloses exact
Ruff and retained-copy limitations, and describes CI 37868105663 at 6a7327b as
the controller's fully read prior-head evidence, not acceptance for F2/F3. The
controller confirms the full report/verdict read before the pending landing.
All 66 local Markdown links in the four reviewed staged record/brief documents
resolve. Earlier pending-checkbox wording above records the initial snapshot.
No browser/source gate is repeated for this records-only closure. Only this
review addendum is written; source, index, HEAD and branch are unchanged.
