# R2 F1 static corpus implementation report

Date: 2026-10-08. Worktree: C:/fks/r2f1 (detached).
BASE and unchanged HEAD: 653d71610b409e59d542391b7010bcc8bd61c3a8.
Status: owned implementation ready for independent review. Controller must land
its separately owned Addendum 4 / D060 / .gitattributes correction before
integration; no unowned file was edited here.

## Fixed scope and product

Only the thirteen brief paths change. No Studio, bridge, shared harness,
package, workflow, plan, ledger or CHANGELOG edit is in the patch. No stage,
commit, push, merge, spawn or background mutation occurred.

| Fixture | Eligible direct-text parents | Expected identity groups | Coverage |
|---|---:|---:|---|
| bootstrap4-static | 20 | 16 | Display 1-4, h1-h6, lead, small, btn, nav-link, navbar-brand, card-title, form-label, author roles |
| bootstrap5-static | 25 | 18 | Display 1-6, same semantic classes, original three hero targets, author roles |
| large-page | 5000 | 20 | Exactly 250 parents in each literal tuple; nested/dedup and threshold cases within that count |

Both Bootstrap fixtures contain author roles ` Editorial `, `Editorial` and
`editorial`. Trimming produces a two-element Editorial identity with two
variants and a separate one-element lowercase identity despite equal styles.
The original BS5 hero tags, IDs, texts, button type, vendor script and 40px
heading remain. The new local generic body family makes fixture signatures
deterministic; no remote font or downloaded font asset is used.

The large page generates authored IDs g00.000 through g19.249. g00.001 is nested
inside g00.000; two direct text nodes in the outer parent count once.
g00.002 uses display:contents and has zero element-box width but positive text
range geometry. g00.003 contains an excluded hidden descendant. Below-viewport
text remains eligible. Hidden/visibility/collapse/transparent/zero-area,
editor-overlay/placed-asset, textarea/select, SVG, shadow, pseudo, template and
frame cases remain outside the 5000 corpus. Hidden native controls are present.

A fixed aria-labelled input displays a/B/7 through real keystrokes and native
value a/aB/aB7. Every input event records acknowledgement and event count in
window.fixtureProbe. requestAnimationFrame advances state-only heartbeat;
no visible label/output adds text parents. Corpus tuples remain identical.

## Literal oracle schema and bridge-writer map

All three expected-styles.json files use schema `fontkit-static-style-oracle`,
schemaVersion 1. Metadata is separate from the tuples and groups. Nothing
captures computed styles or calls a detector to generate expected values.
The JSON is standalone, readable authored data; one element/group/threshold
record per line avoids repetitive indentation without changing parsed values.
The final three files total 273 lines, down from 2841 before compaction.

- eligibleParentCount/groupCount are literal counts.
- Bootstrap elements contain id, semantic selector, five-property signature
  and trimmed authorRole (or null). Their groups contain full identity,
  elementCount, variants with counts, and complete bindings with author IDs.
- Large-page groups additionally contain a signature and a binding with a
  deterministic authorIds prefix/range. Expected IDs are fixture labels;
  future detected IDs are not required to match them.
- Every signature has fontFamily (normalized whitespace, preserved case),
  fontSize (px rounded to two decimals), fontWeight (integer), textTransform
  (computed enum), letterSpacing (em, normal=0, rounded to four decimals).
- thresholdCases supplies explicit pair outcomes and reasons: g00/g01 inside,
  g00/g02 exactly 1px/100weight/0.02em on inclusive bounds, g03 size 1.01px,
  g04 weight 101, g05 tracking 0.0201em outside; g06 family differs and g07 case
  differs. All remain separate exact groups; no merging/transitive collapse.
- nested, exclusions and outsideScope describe reusable eligibility probes.
- metadata.probe names input selector/state and acknowledgement semantics.
- metadata.vendor records source URLs, SHA-256, byte lengths and MIT licence.
  BS5 allowedByteForms lists exactly the canonical LF and existing CRLF forms.

Rendered validation independently reads direct text ranges and computed styles,
then compares each actual parent to literal JSON. It checks counts, unique IDs,
role identity, variant counts, exact binding match sets and deduplicated unions.
It is fixture characterization, not a detector or performance implementation.

## Vendor provenance and portability ruling

BS4 assets were acquired only from these separately allowed tagged raw files;
no denied directory URL was retried:

- https://raw.githubusercontent.com/twbs/bootstrap/v4.6.2/dist/css/bootstrap.min.css
- https://raw.githubusercontent.com/twbs/bootstrap/v4.6.2/LICENSE

| BS4 asset | Exact upstream bytes | Raw upstream SHA-256 | Prospective raw Git object ID |
|---|---:|---|---|
| CSS | 162264 | f886516f3d41e9e7bd994c7f7a39a89cafae9483f90396cb0ddeafe8d1ea5e72 | 83a71b1f50721c12da8e13b8d476cad8ec471e92 |
| MIT LICENSE | 1131 | 53d2513c8df48a817d70537cc906b8e9c7bf2513328ff66847894773e615b37e | dda75ca9a5bb0052cfa3bc7184450a84ee66f764 |

BS4 is not committed here. Its proposed blob bytes/SHA-256 equal the raw upstream
bytes. Tests reject even CRLF conversion. Controller must add only
`fixtures/bootstrap4-static/vendor/** -text` to its owned .gitattributes and
record the portability decision before landing, as instructed separately.

Existing BS5 vendor files never change. Version/source URLs remain recorded as
5.3.8 tagged upstream provenance; fresh upstream acquisition was not performed.
Canonical hashes below are verified directly against BASE Git blobs; the exact
checkout hashes are also verified. Normalizing CRLF produces those same blobs.

| BS5 asset/form | Bytes | SHA-256 | Existing Git object ID |
|---|---:|---|---|
| CSS LF blob | 232066 | 8f8173cb2d8f867274aeb0cb15328e60f490c7f272351e51a55f1dabb486e4ff | c558c23e686c9473d35abc3aa3b16cec11b6f7d7 |
| CSS existing CRLF checkout | 232071 | 247a0bff4f567611b8d2613c8b1b76be603b0fb008076f868239c36480dbf562 | same unchanged blob |
| Licence LF blob | 1093 | 4620c84ad5ce8602ff65640ed6b7c8b78ebb9e036584f0ebc1ccc88206a4bb51 | fa7c00bc4ebd5dc9c0b1e7f8c4b6a202fd9fa816 |
| Licence existing CRLF checkout | 1114 | c5f361fe9af814f57c925bfdadbb3d1857e511fa9feef485cdc5cae817ad44dd | same unchanged blob |

Untouched BS5 bundle checkout SHA-256:
9436953f4c2d40be1def855f4c98d950312c726de61752f65622c18c8c2148b5;
existing Git object 881b51776c82ddd6bd7225fb03f6e9bb07f53c40.
BS5 checks accept only the two recorded hash/length pairs and reject altered
bytes. They exercise both forms in memory; no read-only vendor file is mutated.
BS4 checks exercise rejection of CRLF in memory. The portability RED was the
LF BS5 hash 8f8173... differing from checkout-only expectation 247a0b...; after
the exact-form metadata/test correction both explicit forms pass.

## Test-first and characterization evidence

All commands use C:/fks/r2f1, PYTHONPATH=tests, FKS_ENGINES=chromium.
Approved seams are real rendered fixture behavior and vendor provenance.
TDD skill and tests/mocking references were read; no unapproved seam was added.

| Slice / focused unittest method | RED | Minimal GREEN |
|---|---|---|
| existing_bootstrap5_hero_remains_rendered | Existing behavior characterized passing | Same IDs/texts/40px remain |
| bootstrap4_heading_is_rendered_from_local_vendor_css | h1 count 0 != 1 | Two tests pass after minimal page/vendor |
| bootstrap_semantic_class_corpus_is_rendered | Both corpus h1 class counts 0 != 1 | Three tests pass after class corpus; real navbar parent enables BS5 brand variable |
| large_corpus_has_exactly_5000_rendered_direct_text_parents | Missing page fallback yielded 1 != 5000 | Exactly 5000, 20 x 250 pass |
| nested_dedup_and_excluded_text_have_independent_range_geometry | Nested target count 0 != 1 | Nested/dedup/range/exclusions pass |
| heartbeat_and_real_typing_acknowledgement_preserve_corpus | Textbox count 0 != 1 | Native typed values, acknowledgements and heartbeat pass |
| literal tuples/roles/bindings, variables, unknown-version input | Existing authored fixture behavior characterized | Ten fixture tests pass |
| vendor LF/CRLF portability | Canonical LF BS5 hash rejected by checkout-only expectation | Exact LF/CRLF whitelist; BS4 remains strict |

The independently worked first small-text expectation used browser-UA 80%;
rendering disagreed. Direct BS4 vendor source `.small,small{font-size:.875em;...}`
establishes 14px at 16px root; the oracle was corrected to the source rule.
Unknown-version evidence removes only the version banner in a disposable owned
source copy, preserves every literal rendered tuple, and has no BS5 variables.
It supplies fallback input; adapter selection itself belongs to R2.4.

Example exact commands used for RED/GREEN:

```powershell
$env:PYTHONPATH='tests'
$env:FKS_ENGINES='chromium'
python -m unittest test_r2_static_fixtures -v
python -m unittest test_r2_static_fixtures.StaticFixturesTest.test_bootstrap_semantic_class_corpus_is_rendered -v
python -m unittest test_r2_static_fixtures.StaticFixturesTest.test_large_corpus_has_exactly_5000_rendered_direct_text_parents -v
python -m unittest test_r2_static_fixtures.StaticFixturesTest.test_nested_dedup_and_excluded_text_have_independent_range_geometry test_r2_static_fixtures.StaticFixturesTest.test_heartbeat_and_real_typing_acknowledgement_preserve_corpus -v
python -m unittest test_r2_static_fixtures.StaticFixturesTest.test_vendor_sources_and_existing_bootstrap5_variables -v
```

## Restored foreground mutations

The driver executes `python -m unittest test_r2_static_fixtures.StaticFixturesTest.<method> -v`
in a foreground subprocess, timeout 30/50 seconds. Each source replacement is
inside try/finally; original read_bytes are restored and compared exactly.
Contexts/canary pages close even when assertions/condition waits fail. Every
HTTPS guard mutation retains the earlier local fulfillment route with CORS
headers. No browser canary or mutation contacts a host.

Method abbreviations: tuples=all_literal_style_tuples_counts_roles_and_bindings_match_rendering;
count=large_corpus_has_exactly_5000_rendered_direct_text_parents;
nested=nested_dedup_and_excluded_text_have_independent_range_geometry;
input=heartbeat_and_real_typing_acknowledgement_preserve_corpus;
vendor=vendor_sources_and_existing_bootstrap5_variables;
threshold=near_duplicate_literals_cover_inclusive_and_outside_boundaries.
All method names have test_ prefix. Initial 22 distinct probes plus two new
portability probes give 24 distinct guarded cases. There were 28 executions:
27 rejected and one initial focused threshold survival, corrected and re-probed.

| Mutation (one independent replacement) | Target path / method | Observed rejection |
|---|---|---|
| g00 family serif -> sans-serif | large-page/app.css / tuples | Signature family mismatch |
| g00 size 20px -> 22px | large-page/app.css / tuples | Signature size mismatch |
| g00 weight 400 -> 600 | large-page/app.css / tuples | Signature weight mismatch |
| g00 case none -> uppercase | large-page/app.css / tuples | Signature case mismatch |
| g00 tracking normal -> 1px | large-page/app.css / tuples | Signature 0.05em != 0 |
| Skip group19 sample249 | large-page/app.js / count | 4999 != 5000 |
| Do not append nested child | large-page/app.js / nested | Nested count 0 != 1 |
| Remove outer suffix direct text node | large-page/app.js / nested | 1 != 2 direct text nodes |
| Remove hidden attribute from hidden-direct | large-page/index.html / count | 5001 != 5000 |
| display:contents -> block | large-page/app.css / nested | Box width 1408 != 0 despite positive text range |
| Heartbeat +=1 -> +=0 | large-page/app.js / input | Condition timeout 5000ms |
| Acknowledgement assignment -> empty string | large-page/app.js / input | Condition timeout 5000ms |
| Input event count +=1 -> +=0 | large-page/app.js / input | 0 != 3 |
| Remove responsiveness input | large-page/index.html / input | Textbox count 0 != 1 |
| Editorial author role -> editorial | bootstrap4-static/index.html / tuples | Wrong case-sensitive identity |
| h1 class -> heading-one | bootstrap4-static/index.html / semantic corpus | Semantic target count 0 != 1 |
| Brand variable 1.25rem -> 1.5rem | bootstrap5-static/app.css / vendor | Computed variable mismatch |
| MIT -> MUTATED licence bytes | bootstrap4-static/vendor/LICENSE / vendor | Exact hash/length not allowed |
| Remove later HTTPS abort route | test_r2_static_fixtures.py / original hero | Own abort count 0 != 2; local fallback remains |
| Disable scratch version-banner removal | test_r2_static_fixtures.py / unknown-version | Version banner remains |
| schemaVersion 1 -> 2 | large-page/expected-styles.json / tuples | 2 != 1 |
| Change only g02 identity size 21 -> 21.01 | large-page/expected-styles.json / threshold | Identity != signature after focused check added |
| Rename allowedByteForms key | bootstrap5-static/expected-styles.json / vendor | CRLF checkout not in LF-only whitelist |
| Blindly normalize CRLF before byte check | test_r2_static_fixtures.py / vendor | Strict BS4 rejection assertion not raised |

The initial threshold mutation changed the duplicate identity tuple, while that
focused test read group.signature. It initially passed; the whole rendered
oracle already checked identity. The focused threshold test now explicitly
checks identity/signature consistency. The same mutation fails after the fix
and again in final probes. No surviving probe is presented as rejected before
that fix. Final provenance/threshold run rejected five probes and restored all
bytes, including the strict BS4 and exact BS5-form guards.

## Fresh verification and cleanup

Baseline: static/provenance, bridge syntax, product Ruff and whitespace pass;
34 test_support Chromium tests pass in 17.420s. Final settled owned source:

```powershell
$env:PYTHONPATH='tests'
$env:FKS_ENGINES='chromium'
python -m unittest test_r2_static_fixtures test_support -v
python -m ruff check tests/test_r2_static_fixtures.py
python scripts/verify.py --static-only
node --check fontkit-bridge.js
node --check fixtures/large-page/app.js
python -m ruff check . --exclude .agents
git diff --check
git diff --cached --check
```

Results: `Ran 44 tests in 26.588s`, `OK`, 0 skips, Chromium only (10 fixture,
34 support). Both Ruff commands: `All checks passed!`. Node checks exit 0.
Static: 96 unique IDs, inline syntax PASS, all three supplied provenance PASS;
explicit `SKIP unittest/browser tests: --static-only; full acceptance not checked`.
Both whitespace commands exit 0. Full suites, frontend gate, Node package,
Firefox/full Gecko and commit-message checks were not run in this fixture-only,
uncommitted slice, as dispatched. No production detection/budget/cooperative
scan, protocol hostility, Apply/Clear or adapter implementation is claimed.

The patch uses standard repo-relative Git headers and includes all 11 new files
without staging. Separate disposable copy from
`git -c core.autocrlf=false archive --format=zip <BASE>` passes
`git -c core.autocrlf=false apply --check <patch>` and apply. All thirteen owned
result bytes match this worktree; existing BS5 canonical vendor blobs match.
The first archive inherited autocrlf=true and produced CRLF, so context matching
failed. A direct archive/blob comparison proved the cause; canonical archive
fixed the scratch check. No landing checkout was used for patch testing.

Every new_context is owned and closed by tearDown/close_contexts. Separate
canary pages close in finally before fixture navigation. Shared browser/driver
close through support's process-exit hook. Foreground mutation children exit;
no new fixture server or npm process was launched. Disposable unknown-version
and patch-check directories close via TemporaryDirectory. No read-only BS5
vendor bytes were changed, including for mutations. No denied call occurred.
No staged diff; HEAD remains BASE. No unowned code change exists.

## Self-review and remaining integration requirement

AP3: only textContent/native values; no untrusted markup injected. AP7: no bridge
instrumentation; fixtures do not activate a bridge. AP10: local generic families,
no credentials. AP13: no owned persistent server; contexts/processes close.
AP14: explicit gate/engine limits; no production detector or performance claim.
Tests assert computed tuples/counts, visible native input, range geometry and
binding membership, not message-send side effects or raw markup. No fixed
sleeps, second Playwright driver, fake detector or fake bridge boundary is added.
Mutation sensitivity proves fixture deletion/tuple/count/liveness changes fail.

Graph context was confirmed with list_projects/check_index_coverage: Tier 2,
font-kit-studio-local, generation 2026-10-07T17:07:14Z. Fixtures are excluded;
new paths are missing in the landing graph; support/test_support/bridge metadata
changed. Current worktree source and rendered evidence decide; no exhaustive
graph verification is claimed. Parent supplied structural route/harness traces.

The strict BS4 .gitattributes rule is controller-owned and not in this patch.
Keep its exact bytes and record the separately approved portability ruling
before staging/landing. Review can proceed against this fixed patch; integration
is not declared complete until that controller change is present and reviewed.

## Churn, draft ledger and commit wording

Source delta: 780 material lines; 29 untouched copied BS4 vendor lines
(163395 bytes), counted separately as churn. JSON compaction removes only
repetitive formatting; tuple values/counts and assertions remain. No generated
lockfile/dependency churn. Controller records/review/attribute rule add their own
material lines to the PR total; this report is outside the code patch.

Draft ledger: R2.7F1 supplies Bootstrap 4/5 literal rendered style oracles and an
exact 5000-parent, 20-tuple offline corpus. Ten new fixture tests plus 34 harness
tests pass in Chromium; 24 distinct restored guard probes reject final changes.
Original BS5 targets/vendor remain; D060 records exact-source BS4 handling and
explicit BS5 LF/CRLF forms. Verdict: pending independent review. Scope/commit
range: controller to supply. Next: reviewed controller portability record/rule,
F1 atomic landing, then R2.1/R2.2 consume the literal oracle. Firefox/full
suite/frontend/package remain settled-wave gates. No CHANGELOG line: fixtures
alone do not change shipped user behavior.

Suggested subject: test: add literal static typography corpora

Suggested why-body:

The detection engine needs independent rendered evidence for framework
classes, author roles and text eligibility before it is implemented.
Add offline Bootstrap and exact-size page corpora with literal style
oracles, boundary cases and live input probes to anchor those checks.
