# R2 F3 page and history corpus implementation report

Date: 2026-10-08. BASE: 653d71610b409e59d542391b7010bcc8bd61c3a8.
Status: independently Approved.
Scope: the nine paths in r2-task-f3-brief.md. No runtime/helper/dependency changes.

## Delivered behavior and literal interface

Four ordinary documents supply a reused .shared-title selector, an article
with zero matches, a conflict with different computed typography and an
unvisited link that does not preload its destination. A separate explicit
baseline opens that destination; it is not engine checked-page evidence.

The native-history SPA has real pushState/replaceState, Back/Forward and hash
controls. Load delayed content changes the URL while retaining old content
with aria-busy=true. Resolve delayed content schedules requestAnimationFrame
replacement; no timer or fixed test sleep is used. Same-URL replacement changes
actual history state and nodes while preserving query order, hash and length.
Old title handles detach after both delayed and same-URL renders.

expected-styles.json is fontkit-route-style-oracle, schemaVersion 1. Fourteen
literal normalized five-property signatures describe 13 complete snapshots.
The full population includes every visible navigation link and action button.
Ordinary documents have eight eligible parents; settled SPA states have 14,
and pending has 15 because its resolver is visible. Nested text is counted
once per rendered light-DOM direct-text parent. Values are independent literals.
Size is px rounded to two decimals, weight integer, tracking em rounded to
four decimals with normal=0, and family whitespace is normalized.

| Snapshot inputs | Relative URL | Distinct baseline evidence |
| --- | --- | --- |
| ordinary index/article | /index.html; /article.html | shared serif32/700 title; article zero matches |
| conflict/unvisited | /conflict.html; /unvisited.html | serif40/600/uppercase/.025; monospace24/500 |
| initial/detail/note | /spa.html; ?route=detail; ?route=note | native push/replace and history length |
| hash | ?route=note#section | native hash/back/forward and changed fonts |
| pending/delayed | ?route=delayed | retained old render, then new monospace30/500/.03 |
| same URL | /spa.html | cursive24/500/.015 with detached original |
| exact detail/same URL | ?route=detail&b=2&a=1#keep | parameter order/hash preserved across replacement |

Stable author bindings include nav.home/article/conflict/spa/unvisited and
route.title/body/editorial; Editorial is a case-sensitive author role.
#route-content exposes data-view, data-render-state and aria-busy. No history
method is wrapped. Ordinary links request documents; SPA transitions request
none. HTTP request assertions exclude fragments while browser URLs retain them.
Serve fixtures/multi-page at a locally routed test origin; paths remain relative.

## RED/GREEN and mutations

Missing title/conflict/unvisited elements and missing SPA controls fail their
new rendered assertions before their fixture slices are implemented. Existing
native cross-origin history refusal is characterized GREEN: SecurityError
preserves the rendered document and URL. The completed oracle strengthens
passing behavior rather than manufacturing a regression. An initial request
count incorrectly included a hash; observed HTTP request bytes correct that
expectation while the browser URL still requires the exact hash.

All 26 foreground mutations are rejected and exact bytes restored in finally:
17 assertion failures and nine condition/URL timeouts. These cover all five
conflict properties; disabled push/back/forward/popstate/hash; replace becoming
push; delayed/same-URL/state-write/replacement suppression; pending state and
aria-busy; unvisited preload; zero matches; schema/count/population changes;
visible settled resolver; removed HTTPS guard; navigation typography. The
retained-node mutation preserves text/fonts and fails object disconnection.
No test assertion is removed; no mutated source remains.

## Isolation and cleanup

Each fresh shared-runtime context registers earlier local CORS fulfillment,
then the verified HTTPS-prefix abort guard. Blank-page fetches of both ordinary
and stylesheet/query URLs must reject, with exactly two guard intercepts.
Removing the guard retains local fulfillment and fails its own count, so the
mutation never contacts the external network. All fixture requests remain on
the locally served HTTP origin. No remote font or source acquisition occurs.

Contexts and element handles close in finally, with tearDown as a safety net.
No server/npm/framework process is started. Foreground mutation processes exit
and temporary patch-check resources close. Author text uses textContent and
createElement/replaceChildren. AP3/7/10/13/14 cover text safety, absent bridge
instrumentation, local generic fonts, owned cleanup and explicit coverage limits.

## Verification and integration guidance

```powershell
$env:PYTHONPATH='tests'
$env:FKS_ENGINES='chromium'
python -m unittest test_r2_route_fixtures test_support -v
python -m ruff check tests/test_r2_route_fixtures.py
python scripts/verify.py --static-only
node --check fixtures/multi-page/spa.js
node --check fontkit-bridge.js
python -m ruff check . --exclude .agents
git diff --check
```

Writer baseline: 34 Chromium support tests in 16.882 s. Final focused: 43
Chromium tests in 24.133 s, OK, no skips (nine fixture plus 34 support).
Static/provenance, both Node syntax checks, product/scoped Ruff and whitespace
pass. Canonical-archive scratch patch check/application preserves all nine
file bytes. Patch: 574 authored additions, no churn or generated assets.
Full Python/Node suites, frontend, Firefox and messages are not run by this
fixture writer. There is no production detector or checked-inventory claim.

R2.6B/R2.6S consume this route corpus for actual checked-page behavior. Future
runtime tests still cover stale cancellation, BFCache, CSSOM/HMR, inventory
limits and wrapper cleanup. No workflow/canary or CHANGELOG line belongs to
this fixture-only change. Integrated focused gates and independent review are complete and Approved.
R2.7F3 is closed after its reviewed fixture acceptance.
No new deviation is proposed.
