# R2 F2a brief: React CSS-module and replacement corpus

Plan: docs/plans/2026-10-03-r2-engine.md R2.7F2a. Read the binding detection and
adapter contracts, and .superpowers/sdd/r2/constraints.md in full. Worktree,
BASE, patch and report paths are supplied at dispatch after R2.0 is committed.

## Goal and exact ownership

Create a private React/Vite CSS-module fixture and passing rendered baseline
characterization. Role apply/clear tests belong to F2b after R2.4.
Own only fixtures/vite-react-css-modules/package.json, package-lock.json,
index.html, vite.config.js, src/main.jsx, src/App.jsx, src/App.module.css,
expected-styles.json and tests/test_r2_react.py. No shared harness or package
runtime changes; existing fixtures are read-only references.

## Binding behavior and interfaces

Reuse Vite 8.3.2, React/ReactDOM 19.3.0 exact pins from existing vite-react.
Fixture is private ESM, with dev/build scripts and a committed generated lock.
Use npm ci after lock generation. No React plugin is added; CSS HMR must not
be described as React Fast Refresh. Do not introduce package runtime dependencies.
Provide distinct title/body styles, stable author roles/IDs, CSS-module hashed
class bindings and a stable-class comparison. Literal expected-styles.json has
schema/version and independent normalized tuples/counts/semantic selectors,
documented for later adapter tests. No remote fonts/assets or telemetry.

A keyboard-accessible button changes real React state to replace text nodes,
with deterministic text and the same CSS-module styles on replacements. Assert
old element handles detach, new text renders and actual computed fonts stay.
Do not simulate rerender through page.evaluate DOM replacement; fixture users
must trigger the real state update. Give author roles priority while also
providing a hash-only group; this task characterizes inputs, not engine behavior.

HMR test uses a scratch copy of owned fixture source and that worktree's local
node_modules, excluding .git/generated dist from the copy. Start owned Vite at
loopback/free port, replace an owned CSS declaration through a real file write,
await its computed effect and assert normal app content/state. Cleanup restores
bytes and stops Vite/browser by owned handles in finally. Never mutate shared
fixture bytes while another test uses them. Building the fixture leaves no
Font Kit Studio bridge, role CSS or production instrumentation in emitted assets.

## Tests, RED/GREEN and mutations

New behavior: write one failing browser assertion before its fixture slice.
Existing Vite/CSS-module/React behavior is characterized GREEN; no invented RED
or skipped future role tests. The test must fail if its fixture behavior is removed.
Use existing support shared_runtime/new_context; fixture_support require_fixture
must fail with FKS_REQUIRE_FIXTURES=1 when the fixture is missing. No new helpers
outside owned test module. Read tests/test_one_command_vite.py for owned Vite
startup/readiness/Windows cleanup patterns; use browser conditions, not sleeps.
Verify all-HTTPS regex interception with a separate local canary before app load.
During canary/guard mutations, retain an earlier local-fulfillment HTTPS route.
The later abort guard must increment its own intercept count; removing it fails
that assertion while the earlier fallback still prevents external contact.
Assert computed fonts, rendered replacement and HMR behavior, not message counts.
Independent literal oracle; do not read module generated class names and call
that an exact expected compiler algorithm. Observe hashed classes as uncertain
bindings and prove stable author/class controls separately.
Mutations: remove module styling; prevent actual React replacement; break HMR
computed effect; remove the owned test module's HTTPS-abort guard while retaining
the local fallback. One at a time foreground, precise restoration and cleanup.
Missing-install fail-closed behavior already exists in fixture_support.py:
characterize it GREEN through require_fixture, with that source unchanged.
No new availability wrapper or mutation of the shared helper is required.

Focused (PowerShell, from the named worktree):

```powershell
npm.cmd ci --prefix fixtures/vite-react-css-modules
$env:PYTHONPATH='tests'
$env:FKS_ENGINES='chromium'
$env:FKS_REQUIRE_FIXTURES='1'
python -m unittest test_r2_react test_support -v
npm.cmd --prefix fixtures/vite-react-css-modules run build
python -m ruff check tests/test_r2_react.py
git diff --check
```

## Report and done

Return patch including new files and full report at supplied scratch paths.
Include exact RED/GREEN/mutation/build summaries, JSON schema/fixture URL,
lock/package inventories and counts, scratch byte/process cleanup, applicable
AP3/7/10/13/14 self-review. Return exact future workflow install/module lines
for controller integration in R2.7I; do not edit workflow/canary now.
Draft ledger, material/churn counts and commit subject/why-body. Fixture-only
change needs no user-facing CHANGELOG entry. No role test acceptance by skipping.
You are not alone in the codebase; never revert others and only edit owned paths.
No stage/commit/push/spawn. A denied tool call is reported, never retried through
a different tool. Done means rendered baseline/HMR/replacement and clean build
pass with installed fixture and every owned resource stopped.
