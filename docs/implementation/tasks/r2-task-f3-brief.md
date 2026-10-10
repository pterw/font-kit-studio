# R2 F3 brief: page and history transition corpus

Plan: docs/plans/2026-10-03-r2-engine.md, R2.7F3. Read its visited-page
contract and .superpowers/sdd/r2/constraints.md in full. The controller supplies
the detached worktree, BASE and scratch output paths at dispatch.

## Goal and exact ownership

Create independent rendered inputs for later route integration. Own only
fixtures/multi-page/index.html, article.html, conflict.html, unvisited.html,
spa.html, app.css, spa.js, expected-styles.json and
tests/test_r2_route_fixtures.py. No runtime, shared harness, workflow or other
fixture changes. Return draft bookkeeping for the controller.

## Binding behavior and interfaces

Ordinary links navigate real documents. Include a deliberately unvisited page,
a semantic selector whose computed signature differs on conflict.html and a
zero-match case using an owned page. Document which owned page provides it;
do not create another page. The unvisited page must not be fetched by default
navigation or preload. Tests may visit it explicitly in a separate baseline
case to characterize its literal style, without claiming it was checked by
the future engine.

The SPA uses native history pushState/replaceState, back/forward and hash
navigation. Render different text/style inputs on actual routes, including
delayed content replacement and same-URL state replacement. Use an explicit
pending/settled condition and an asynchronous event or animation frame for
the delayed renderer, not a fixed test sleep or synthetic bridge notification.
Tests drive accessible links/buttons through the real UI and prove actual URL,
rendered content and computed typography before and after each transition.

Provide literal expected-styles.json with schema/version, semantic selectors,
normalized family/size/weight/case/tracking tuples and counts per document/SPA
state. Expected values cannot be captured from getComputedStyle at runtime or
derived from a future detector. Route names and selectors are a stable interface
for the bridge/Studio writers; explain them in the report. No framework/router
dependency, remote font, network acquisition or extra shared helper.

## Tests and cleanup

Write failing rendered assertions before new fixture behavior. Characterize
existing native history behavior GREEN rather than manufacturing RED. Serve
owned pages through support.route_virtual_origins using shared_runtime and
new_context. Read those implementations; no second Playwright driver.

Install a verified HTTPS-prefix regex guard before navigation. A separate local
canary must exercise its intercept count. Keep an earlier local-fulfillment
HTTPS fallback during guard mutations so a removed abort guard cannot contact
an external site. Every context closes in finally. No unowned server is needed.

Foreground mutation probes alter the conflict signature, disable real history
navigation, prevent delayed replacement, and prevent same-URL replacement.
Each must fail its own rendered assertion. Restore exact bytes in finally.
Also remove the owned abort guard with its local fallback still active and
prove that its intercept assertion fails. Do not delete test assertions to
manufacture a mutation result. Explain any inapplicable guard explicitly.

Focused (PowerShell):

```powershell
$env:PYTHONPATH='tests'
$env:FKS_ENGINES='chromium'
python -m unittest test_r2_route_fixtures test_support -v
python -m ruff check tests/test_r2_route_fixtures.py
python scripts/verify.py --static-only
git diff --check
```

Do not run the full suite, frontend gate or full Firefox suite for this slice.
Firefox canary remains advisory at the settled boundary wave.

## Report and done

Return one patch including new files and a complete report at the supplied
scratch paths. Include exact RED/GREEN and restored mutation commands/counts,
schema/route/selector map, offline guard evidence, cleanup and applicable
AP3/7/10/13/14 checks. Draft ledger text, material/churn counts and a product
commit subject with a why-body. Fixture-only changes need no CHANGELOG entry.

No stage, commit, push or subagents. You are not alone in the codebase; edit
only owned files and never revert others. A denied tool call is reported,
never retried through a different tool. Done means all real transitions and
literal computed oracles pass and every owned resource is closed.
