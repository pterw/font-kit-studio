# R2 F2a React corpus implementation report

Date: 2026-10-08. BASE: 653d71610b409e59d542391b7010bcc8bd61c3a8.
Status: independently Approved; controller landing pending.
Scope: the nine paths in r2-task-f2a-brief.md. No runtime/shared-helper changes.

## Delivered behavior

The private ESM fixture pins Vite 8.3.2 and React/react-dom 19.3.0, with a
generated lockfile. No React plugin, remote font or Fast Refresh claim is added.
Literal expected-styles.json covers six direct-text parents in five semantic
rows and four style signatures. Author display/body roles and IDs coexist with
generated module classes, a hash-only paragraph and a stable class comparison.
Expected values never come from runtime styles or compiler hash predictions.

Enter/Space activate a real React state update. A keyed section replaces the
title/body nodes; previous handles detach, new text renders and fonts remain.
CSS HMR changes scratch-source title size from 40px to 44px, then restores it.
The document marker, React generation and title node survive. Explicit module
naming and acceptance of that CSS dependency keep this fixture's mappings
stable during declaration edits; this is not universal compiler detection.

The existing require_fixture helper fails closed with FKS_REQUIRE_FIXTURES=1
and no install. Each browser uses a source copy and verified HTTPS-prefix guard
before navigation. Blank-page fetch canaries prove interception; the earlier
local CORS fallback remains during guard mutations. The fixture requests no
external font/assets and emitted builds contain no bridge instrumentation.

## Literal interface

Schema: fontkit-fixture-styles, version 1. Size is px rounded to two decimals,
weight numeric, case the computed enum, tracking em rounded to four decimals.
Family normalization preserves case and quotes. Binding metadata describes
author roles/IDs and source class inputs independently of generated names.

| Semantic input | Parents | Family / px / weight / case / em |
| --- | ---: | --- |
| display heading | 1 | serif / 40 / 600 / uppercase / .02 |
| authored body paragraphs | 2 | sans-serif / 18 / 400 / none / 0 |
| hash-only paragraph | 1 | monospace / 14 / 500 / lowercase / .04 |
| stable class paragraph | 1 | sans-serif / 18 / 400 / none / 0 |
| replacement button | 1 | sans-serif / 16 / 500 / none / 0 |

Role preview/apply/clear tests belong to F2b. No future acceptance skip is added.

## RED/GREEN and mutations

The first title assertion observes unstyled Times New Roman/32/700/none/0,
then the authored serif/40/600/uppercase/.02 tuple passes. The expanded oracle
first fails on missing body/hash/stable/action elements, then passes after
their markup/styles. A static replacement button first times out; real keyed
state replacement passes. Existing binding/install behavior is characterized
GREEN rather than given an artificial failing baseline.

Initial CSS updates reload the document despite changing the computed size.
Installed Vite source confirms module updates propagate to their importer.
Stable module names alone retain that failure; accepting the CSS dependency
preserves state and nodes. The final HMR gate checks all three observations.

Five restored foreground probes fail meaningfully: empty module CSS changes
five literal tuples; removing the section key keeps an old node connected;
a 43px update fails the expected 44px effect; removing the abort guard produces
local fulfillment and zero aborts; removing module acceptance exposes a full
reload. Each restores exact bytes in finally and stops owned test resources.

Canary verification originally stalls when closing a page after two aborted
main-document navigations. A bounded trace identifies that operation, without
establishing its underlying browser cause. The working blank-page fetch pattern
preserves isolation and normal cleanup; ordinary tests subsequently complete.

## Verification and limits

```powershell
npm.cmd ci --prefix fixtures/vite-react-css-modules
$env:PYTHONPATH='tests'
$env:FKS_ENGINES='chromium'
$env:FKS_REQUIRE_FIXTURES='1'
python -u -m unittest test_r2_react test_support -v
npm.cmd --prefix fixtures/vite-react-css-modules run build
python -m ruff check tests/test_r2_react.py
git diff --check
```

Writer results: 39 Chromium tests in 30.733 s, OK, no skips (five fixture and
34 support). npm ci installs 18 packages, audits 19 and reports zero
vulnerabilities. The lock lists 44 records including platform optional packages.
Build: 16 modules, 659ms, three clean assets. Scoped Ruff/byte whitespace pass.
The patch has 407 authored additions and 827 generated lockfile additions.
No generated dist/node_modules are included. Full suites, frontend, package,
Firefox, static and commit-message gates are not run by this fixture writer.

Normal contexts, Vite listeners and output readers close; scratch CSS and
shared-source bytes restore exactly. Five earlier interrupted source copies
remain ignored outside the patch. New successful tests remove their own copies.
No broader browser lifecycle guarantee follows from the canary recovery.
AP3/7/10: text rendering, no bridge instrumentation or credentials/remote assets.
AP13/14: normal resource cleanup and retained-copy/engine limits are explicit.

## Integration guidance

R2.7I installs this fixture with npm ci, builds it and adds test_r2_react to the
installed Chromium fixture job under FKS_REQUIRE_FIXTURES=1. This task changes
no workflow/canary. F2b supplies real role preview after R2.4; fixture-only work
needs no CHANGELOG line. Controller integration and independent review remain
required before closing R2.7F2a.
