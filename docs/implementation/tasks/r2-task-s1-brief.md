# R2 S1 brief: explicit text detection in Studio

Plan: docs/plans/2026-10-03-r2-engine.md R2.S1. Dispatch/landing requires
R2.2 committed. The controller supplies detached worktree/BASE/outputs.
Read the COMPLETE binding contract, S1 task and execution constraints.

## Exact ownership and scope

Own only fontkit-studio.html, tests/test_studio_roles.py and
tests/test_r2_integration.py. Existing bridge, fixtures, shared helpers, test
modules, export format, persistence, package and workflow are read-only.
Add Detect and its read-only results only. Apply/Clear, property fields, role
stylesheet and visited inventory remain their later planned tasks.

## Public behavior

After a valid connection, add a compact Detected roles section inside Live App.
Use the established Studio control/spacing styles. Provide an accessible
Detect text styles button, named status region, Light-DOM text only coverage
note and truthful capability/connection/stale/incomplete reasons. Keyboard
activation works, focus remains sensible through result updates, and overflow
remains within the existing panel at desktop/narrow widths.

Each bounded row shows suggested name, sample, eligible parent count, selectors
and stability/uncertainty, variants and near-duplicate flags. Replies render
as textContent, never parsed markup. Exact identities remain separate even
with duplicate labels or near-duplicate flags. Full identity keys map to
monotonic issued role-N IDs, stable across repeated current-origin observations
and discovery reordering. Do not use scan IDs, labels or a digest as identity.
Author namespaces and automatic tuples remain distinct. Incoming baseline
observations cannot overwrite unsent Composer or accepted legacy state.

Authenticated ready roleState establishes document/version/URL; detection
replies alone cannot establish identity. Missing roleDetection or invalid
ready identity disables Detect with the approved unsupported reason. Old
bridges retain the existing live inspector and other features. Handle only
the latest pending detect request for the current window/origin/session/ready
document. Never let role replies settle a legacy revision-queue request or
alter the acknowledged Changes/export ledger.

Validate the COMPLETE exact request/reply shapes and UTF-8 limits on Studio's
side of the trust boundary. Reject hostile object/prototype keys, unknown
fields, invalid enums/counts/references/variants, inconsistent identities and
oversized fields/whole replies. Validate authenticated-origin URLs. A current
incomplete page-changed reply may disclose current identity/status as specified
but cannot mark results checked. Unknown/superseded documents and old versions
cannot replace current state. No automatic replay, font request or persistence.

## Test-first acceptance

Addendum 5/D061 is binding: authenticated ready pageURL:null establishes only
document/version, never a route. Disable Detect with visible
`Role detection/preview unavailable: unsupported page URL.` Preserve the real
legacy inspector and reset. A page-changed detection with currentPageURL:null
invalidates evidence; no complete detection may contain null. Test real initial
over-limit target and valid-to-over-limit invalidation, safe text rendering,
hostile credential/foreign-origin URLs and supported-URL reconnect recovery.
Apply/Clear controls remain outside S1; later tasks implement their exceptions.

Genuine RED: real Studio connected to real bridge lacks the accessible Detect
button and visible role list. Add one rendered slice at a time. At least one
real cross-origin Studio/bridge test drives the actual Connect/Detect UI and
asserts visible names/counts/selectors against literal fixture expectations.
No fake-peer-only boundary acceptance or message-send-only assertions.

Fake peer tests supplement that boundary for old capability, hostile shape,
wrong source/origin/session/version, stale ready document, latest-request
ordering, same-author variants and reordered/duplicate display-name identities.
Prove rendered state/status is preserved rather than checking only rejection
messages. Any test fixture defined inside owned modules uses local HTTP routes;
no extra fixture or shared-helper path. Existing role protocol target/oracles
are read-only inputs. Use shared_runtime/new_context and close every context.

Verify an HTTPS-prefix regex with blank-page fetch canaries and an earlier
local CORS fulfillment fallback. Install before app navigation, assert no
unrequested font/telemetry load. Restored foreground mutations remove message
trust, latest-request/generation checks, identity consistency and text-only
rendering; each must fail an independent rendered assertion. Do not bypass
CSP, delete assertions, add fixed sleeps or capture runtime-derived oracles.

## Focused gates and report

```powershell
$env:PYTHONPATH='tests'
$env:FKS_ENGINES='chromium'
python -m unittest test_studio_roles test_r2_integration test_studio_import_link test_studio_dead_controls test_support -v
python scripts/verify.py --static-only
python -m ruff check tests/test_studio_roles.py tests/test_r2_integration.py
git diff --check
```

Controller runs the frontend/settled full wave and advisory Firefox canary once
the source settles; no full Gecko suite per task. Capture a representative
desktop and narrow rendered state as scratch evidence, with named controls,
status, readable contrast and panel overflow observed directly.

Return full patch/report with RED/GREEN counts, real boundary/hostile cases,
mutations/cleanup/accessibility evidence, unresolved limits and material/churn.
Draft product CHANGELOG line, ledger and imperative commit subject/why-body.
No stage/commit/push/spawn. You are not alone; never revert others. A denied
tool call is reported, never retried through another tool.
