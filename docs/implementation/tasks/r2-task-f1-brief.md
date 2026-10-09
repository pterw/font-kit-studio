# R2 F1 brief: static typography and performance corpus

Plan: docs/plans/2026-10-03-r2-engine.md, R2.7F1 and binding detection contract.
Read .superpowers/sdd/r2/constraints.md in full. Code worktree/BASE/patch/report
are supplied at dispatch after the reviewed R2.0 work-order commit.

## Goal and exact ownership

Create offline static rendered oracles independent of the future detector.
Own only:

- fixtures/bootstrap4-static/index.html, app.css, expected-styles.json,
  vendor/bootstrap.min.css and vendor/LICENSE;
- fixtures/bootstrap5-static/index.html, app.css and expected-styles.json;
- fixtures/large-page/index.html, app.js, app.css and expected-styles.json;
- tests/test_r2_static_fixtures.py.

Names after each fixture prefix resolve inside that directory. Existing BS5
vendor files are read-only. No shared harness, runtime or package edits. Return
draft bookkeeping; only the controller edits shared records/CHANGELOG/CI.

## Binding behavior

Read all R2.7F1 checkboxes and Detection/performance. Bootstrap 4.6.2 minified
CSS/license comes from the tagged twbs/bootstrap upstream. Record exact source
URL, version and SHA-256 in expected-styles.json metadata; preserve source bytes.
Existing BS5.3.8 vendor bytes/license/hash remain unchanged. Browser requests are
offline; acquiring these specified source assets is separately allowed.

Both Bootstrap versions exercise display, h1-h6, lead, small, btn, nav-link,
navbar-brand, card-title and form-label classes, plus author-role grouping inputs.
Unknown-version fallback is characterized through a scratch page variant using
owned source; do not add an unowned fixture file or implement adapter detection.
Preserve original BS5 hero IDs/text and existing integration semantics.

The large page has exactly 5,000 eligible light-DOM text parents, 20 deterministic
styles of 250 each. Literal tuples/counts in JSON are the oracle, not generated
from a detector/computed-style capture at test runtime. Include nested/dedup
cases inside those 5,000; hidden/transparency/excluded-control cases are outside.
No visible label or heartbeat output adds another eligible parent. Families
use local generic stacks; no remote or downloaded font assets.
Inside/on/outside near-duplicate cases remain among the same 20 tuples and
exercise family/case equality and <=1px/<=100weight/<=0.02em boundaries. Use
exact finite literals that the later engine can compare independently.

Heartbeat records JS state. An aria-labelled input renders typed values through
its native value (excluded by first detector); test keystrokes and visible value.
No arbitrary delay/sleep. Literal corpus must remain identical after typing.
Cooperative detector/budget assertions belong to R2.2, not a fake detector here.

## Interfaces and tests

Each expected-styles.json documents a schema/version and literal eligible
counts, normalized five-property signatures, expected groups and bindings.
Use explicit semantic selectors and stable author-role/ID evidence that later
tests can consume; keep expected metadata separate from group tuples.
Provide a fixture map/schema explanation in the report for the bridge writer.
New test module can serve via tests/support.py route_virtual_origins at a fake
HTTP origin; use new_context and owned cleanup. Verify an HTTPS-prefix regex
with a separate locally intercepted canary before loading a fixture (D059).
During the canary and any guard mutation, retain an earlier HTTPS route that
fulfills locally. The later abort guard must increment its own intercept count;
removing it must fail that assertion while the local fallback prevents contact.
No new shared helper; tests/support.py and fixture_support.py are read-only.

Vertical slices: failing rendered fixture test, minimal fixture, GREEN. Existing
BS5 behavior is characterized passing before its extension. Assert computed
family/size/weight/case/tracking and element counts from real rendered pages.
Eligibility test counts direct text parents once; it also independently tests
range geometry for display:contents, hidden/transparency and nested exclusions.
Use literal oracle values, not expected = current getComputedStyle results.
Mutation probes independently alter one tuple, remove a parent/dedup case,
make a hidden case visible and remove heartbeat/input acknowledgement; each
must fail a behavior assertion. Restore exact bytes in finally, run foreground.
Record any guard not relevant to this fixture-only slice explicitly.

Focused (PowerShell):

```powershell
$env:PYTHONPATH='tests'
$env:FKS_ENGINES='chromium'
python -m unittest test_r2_static_fixtures test_support -v
python -m ruff check tests/test_r2_static_fixtures.py
python scripts/verify.py --static-only
git diff --check
```

## Report and done

Return one patch including new files, full report at supplied scratch path,
RED/GREEN/mutation commands+summary counts, Bootstrap URLs/hashes, JSON schema,
computed oracle observations, existing-fixture compatibility and process/context
cleanup. List AP3/7/10/13/14 and applicable test-quality checks. Draft ledger,
CHANGELOG only if a shipped user behavior changes (fixtures alone do not),
material/churn counts and product-focused commit subject/why-body.
Do not commit, stage, push, spawn or edit another writer's files. You are not
alone in the codebase; accommodate others and never revert their edits.
A denied tool call is reported, never retried through a different tool.
Done means independent literal rendered oracles pass, vendor provenance matches,
all owned resources close and no unowned/runtime file changes exist.
