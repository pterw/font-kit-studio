# v0.2 Task H review: Quality Gate workflow, frontend gate, silent-until-asked fonts

Scope: `scripts/dev/**`, `.github/workflows/quality-gate.yml`, `tests/test_frontend_gate_*.py`, `tests/test_commit_messages.py`, README (Development and testing, Free fonts), the Studio CSS tokens and font-loading code, `.github/pull_request_template.md`, `CONTRIBUTING.md` and the `AGENTS.md` diff. Spec: plan Addendum 4 and D028.

Checks run (Chromium only, `FKS_ENGINES=chromium`, `FKS_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium`):

| Command | Result |
|---|---|
| `frontend_gate.py --engines chromium --offline` | exit 0, 15 of 15 runs, 14 passed, 1 skipped, 0 FAIL, 140 REPORT, 1 SKIP (18 s) |
| `frontend_gate.py --engines chromium` (online) | exit 1, 15 of 15 runs, only `free fonts load` fails (see Important 5) |
| `python3 -m unittest discover -s tests -v` | `Ran 330 tests ... OK` (320 s) |
| `scripts/verify.py --static-only` | PASS (88 IDs, 1 JS block, 3 provenance blobs) |
| `node --check fontkit-bridge.js` | rc 0 |
| `check_commit_messages.py --range origin/main..HEAD` | OK, 35 commits |

After the runs no server or browser process was left (`ps`). Firefox was not run (not installed); it stays unverified until CI.

### Spec Compliance

- **Network isolation (D028).** Met. A fresh context with every non-loopback request routed and logged made zero external requests on first load of Library, Composer, Target App connected to the demo, and the pop-out (scrolled, then idle). `localStorage["fontkit-free-fonts"]` stays unset until the user asks.
- **Asking.** Met for all three triggers, each verified with a fresh context:
  - Library **Load free fonts**: 16 stylesheet requests, key set to `yes`.
  - Composer **Load free fonts**: 16 requests.
  - Kit preset switched to Free Google Fonts (after Adobe): 16 requests. Adobe alone makes none.
  - Live Target inspector family pick: the five cards that were visible plus the picked family load (and the bridge adds the stylesheet in the target), key set.
- **Consent remembered, guarded.** Reload loads the visible cards without a click (5 families). With a throwing `localStorage` there are no page errors and the click still loads all 16 (it just asks again next visit).
- **Queue.** Families wanted before consent are queued in `deferredFonts` and requested after consent; confirmed by the inspector pick pulling the five visible cards' families.
- **Composer slot inspector pick is not asking.** Confirmed: picking a family there makes zero requests and the slot renders a generic fallback (`monospace`). This is consistent with D028 and defensible (it is a local mock-up, the Live Target pick is the one that needs the stylesheet in a real page). See Important 2 for the wording problem it exposes.
- **Hints at 390 px.** Both hints are visible, no overflow (`scrollWidth == clientWidth`, 370 and 340 px wide). The Composer hint sits directly under the **Load free fonts** button.
- **Gate checks 1 to 8 of Addendum 4.** Present with the profiles and enforcement the plan states. `GOOGLE_ON_FIRST_LOAD_ENFORCED` no longer exists; a Google stylesheet on first load is now a FAIL.
- **Workflow.** `permissions: contents: read`, no secrets, majors pinned (`checkout@v4`, `setup-python@v5`, `setup-node@v4`, `upload-artifact@v4`), `fetch-depth: 0` plus `fetch-tags: true` (the `supplied-v0.1.1` tag exists on origin), Firefox installed, screenshots uploaded on failure, 30 minute timeout. Order is not fully cheapest first (Important 4).

### Strengths

- The gate measures computed reality: computed `display`, computed colours flattened over the first opaque ancestor, `scrollWidth` against `clientWidth`, the live iframe's computed font size and a byte-identical Reset, and logo paint read back from canvas pixels.
- A check that raises is a FAIL. Proven by accident in a scratch copy where a missing logo file produced `FAIL logo paint: raised FileNotFoundError ...` and the run still counted toward the 15 planned.
- Exit rule is correct and in one place: FAIL or a run-count shortfall gives 1; REPORT never does; SKIP is counted (`1 skipped`) and does not change the exit code. Prerequisite errors exit 1 before any check.
- Mutations I applied in a scratch copy were all caught:
  - consent forced on: 3 enforced `network isolation` FAILs naming the surface and the families;
  - `--muted-strong` back to `#6f6b63` and dark `--warn-text` back to `#c2410c`: `theme contrast` FAILs on desktop and mobile (dark badge 2.58:1, dark warnings 3.40:1);
  - logo asset removed: FAIL, as above.
- Network routing is deterministic: one router per context, served origins pass, everything else is aborted and logged; only the free-fonts check opts Google in, and `--offline` closes even that.
- Server lifecycle: `serve.py` as a subprocess on OS-assigned ports, `--no-sync`, stopped in `finally` (SIGTERM, kill as last resort). No stray process after four runs.
- Contrast fixes are measured and sound (table below); legacy tokens untouched.
- Commit check handles the real banner forms: `Co-Authored-By` trailers in any case and spacing, a `Generated with [tool](https://...)` banner with and without a leading emoji or bullet, non-breaking spaces, and a `Claude-Session:` trailer with a URL. Merge commits are skipped.
- The new Studio tests assert rendered outcomes (requests, link elements, hint text, remembered consent across a reload), not just that code ran.

Contrast (computed from the CSS tokens; gate agrees):

| Token | Light | Dark |
|---|---|---|
| `--muted-strong` on bg / panel / chip | 5.72 / 6.35 / 5.23 | 7.38 / 6.87 / 5.91 |
| `--warn-text` on bg / panel / chip | 6.47 / 7.19 / 5.93 | 9.96 / 9.28 / 7.98 |
| `--warn-text` on the red-tinted bar over bg / panel / chip | 5.45 / 6.00 / 5.02 | 8.73 / 8.04 / 6.92 |

`--muted` is unchanged in both themes (`#6f6b63`, `#a7a198`); the 55 Library `.tag` chips remain a legacy REPORT at 4.30:1. Dark mode: `--muted-strong` equals dark `--muted`, the dark warning colour is the same `#fca5a5` as before, and the code panel's dark error status improves from 3.40:1 to 9.28:1. No regression found.

### Issues

#### Critical

None.

#### Important

1. **The commit check blocks legitimate human co-authors.** `scripts/dev/check_commit_messages.py:38-47,77-80` matches each marker as a substring of the whole trailer. Verified failures (all exit 1) for `Co-authored-by: Claudette Dupont <claudette@example.org>`, `Claude Monet <cmonet@example.org>`, `Dana Lee <dana@geminitech.com>`, `Devin Patel <devin@example.com>`, `Ada Aiderman <a@example.com>`, `Pat <pat@cursorial.org>`, `Sam <sam@codexlabs.io>`. `CONTRIBUTING.md` and the README promise human co-authors are welcome, so a contributor with a first name like Claude or Devin is blocked and told they carry "agent signatures". The marker list is also too loose in itself (`cursor`, `devin`, `aider`, `codex`, `gemini` are ordinary words or names). Fix: judge a co-author by its email address first (domains such as `anthropic.com`, `openai.com`, the `users.noreply.github.com` identities for Copilot), and by name only as an exact assistant identity (the assistant's own product name, with or without a model suffix). For the "Generated with/by" banner a whole-word tool match is fine. Add the cases above to `tests/test_commit_messages.py` as must-pass.

2. **The Composer hint tells users something untrue.** `font_kit_studio_v0.1.1.html:1063` and `:1483-1486` say "Choosing a library family in the inspector also loads it." In the Composer the inspector on screen is the slot inspector (`#slotInspector`), where a pick loads nothing (verified: zero requests, fallback face, no consent stored). Only the Live Target inspector loads. Fix: say "Choosing a library family in the Live Target inspector (Target App view) also loads it", and consider showing that sentence only in the Target App view. A one-line note in the slot inspector ("Shown in a fallback font until you load the free fonts") would also remove the surprise of picking Fraunces and seeing a generic serif. I would keep the slot pick as not-asking; it is a mock-up and the hint beside the button is the right place to ask.

3. **`AGENTS.md` Gates section omits the new gate.** It lists `verify.py`, `node --check` and `unittest` as the pre-commit gates but not `python scripts/dev/frontend_gate.py` or the commit check, which CI now enforces; an agent following it will push a red PR. Add both to "Gates" (and say `--offline` plus the `FKS_*` variables for containers). Also reconcile the new "History tells the product story" rule with lines it contradicts: "Markdown Authoring Rules" still says ledger entries cover verdict and RED/GREEN evidence, and commit rule 1 requires a ledger update in each work commit, while the new rule forbids recording review and fix-round counts in committed docs. State which committed records are exempt (the internal ledger) in one place and link to it from the other.

4. **Workflow order is not cheapest-first, and its comment is wrong.** `.github/workflows/quality-gate.yml:92-107`: the full test suite runs before the gate, and the comment calls the gate "the slowest step". Measured: the gate takes 18 s per engine, the suite 320 s on Chromium alone. A layout, contrast or privacy regression therefore reports after roughly ten minutes instead of two. Fix: run the gate before the suite, and correct the comment.

5. **The free-fonts check makes CI depend on Google, with no retry.** `scripts/dev/_frontend_gate_network.py:check_free_fonts_load` fails when any one of the 16 families does not resolve a loaded face; it runs once per engine. Cause of the local failure confirmed as the sandbox, not Studio: Chromium gets `net::ERR_CERT_AUTHORITY_INVALID` (the sandbox proxy intercepts TLS with a CA the browser does not trust); with TLS errors ignored 11 of 16 families load and the check names the other five, so the per-family logic works but the link is lossy. Recommendation: keep it enforced (it is the only proof that the families and their stylesheet URLs still exist, and a real rename at Google is a real defect), but make it flake-tolerant: after the first settle, retry the families that failed up to two more times (Studio's `loadAllFreeFonts` already re-creates errored links on a second click) with a short backoff, and fail only if a family is still missing after the last attempt. Keep the "probably unreachable" message for the all-missing case, and mention TLS-intercepting proxies in it. Do not make the step `continue-on-error`.

#### Minor

6. `scripts/dev/check_commit_messages.py:57`: a `Claude-Session: session_<id>` trailer without a URL passes (verified). The README says "with a URL", so this is as documented, but the trailer is still a session identifier. Fix: also flag a `*-Session:` trailer when its name or value names an AI marker or the value looks like `session_<id>`. Unicode lookalikes in both name and email (`Сlаudе <noreply@аnthropic.com>`) pass; that is disproportionate to chase, but stripping non-ASCII before matching would close the easy cases.
7. `.github/workflows/quality-gate.yml:55-70`: on a force-pushed `main` whose old tip is gone, and on `workflow_dispatch`, only the last commit is checked. Low risk (only `main` triggers on push); for dispatch, prefer `origin/main..HEAD` when HEAD is not main. The pull-request range (`origin/${BASE_REF}..HEAD`, with full history, merge commit skipped) is correct. Consider a `concurrency` group so a new push cancels the old run.
8. README Free fonts and the code hint say "choose the Free Google Fonts preset", but it is the preselected value, so it only fires after switching the Kit preset away and back (verified). No test covers it, and none covers blocked storage. Fix: reword to "switch the Kit preset to Free Google Fonts" and add both tests next to `test_choosing_a_family_in_the_live_inspector_counts_as_asking`.
9. There is no way to withdraw consent in the UI; the README says to clear site data. Acceptable for 0.2; note it for later.
10. `docs/agents/global-rules.md` rule 8 still says Google Fonts stylesheets "load on demand", and neither rule 7 nor 8 states D028's silence, although the gate's docstring cites rule 7 as its basis. Add one sentence to rule 7: Studio makes no third-party request until the user asks.
11. `CONTRIBUTING.md`: the "Before you open a pull request" block omits `python scripts/dev/check_commit_messages.py --range origin/main..HEAD` although the page says CI rejects such commits, and omits `git fetch origin tag supplied-v0.1.1` (provenance fails without it; the README has it). The "More detail" link goes to `docs/agents/global-rules.md`, which cites deviation numbers (D016) and `AGENTS.md`; either link the README sections instead or accept that one reference. Otherwise the page is contributor-facing: no plans, ledgers, reviews or deviation registers, and the commands and claims are accurate. `.github/pull_request_template.md` is clean.
12. The implementer report is out of date against the tree (it still describes the first-load Google REPORT, the four contrast FAILs and 311 tests); the controller should refresh it before it is used as evidence.

### Assessment

The gate is honest and deterministic: it measures computed values, treats a raised check as a failure, keeps REPORT out of the exit code, counts SKIP, cleans up after itself, and my own mutations were all caught. Silent-until-asked holds in every view, all three triggers load and remember consent through guarded storage, queued families load afterwards, hints are visible at 390 px, and the contrast fixes meet 4.5:1 in both themes without touching legacy `--muted`. The blockers are narrow: the commit check rejects ordinary human co-authors (which contradicts the public docs), the Composer hint misdescribes where a family pick loads, `AGENTS.md` omits the new gates, and the workflow runs the 18-second gate after the five-minute suite. The free-fonts check should be kept enforced but given a bounded retry. Firefox remains unverified until CI.

**Task quality:** Approved with fixes

## Re-review after second changes

Re-run (Chromium only): offline gate exit 0 (15 of 15 runs, 14 passed, 1 skipped, 0 FAIL, 140 REPORT); `python3 -m unittest discover -s tests -v` `Ran 342 tests ... OK` (320 s, matches the report); `verify.py --static-only` PASS (88 IDs, 1 JS block, 3 provenance blobs); `node --check fontkit-bridge.js` rc 0; `check_commit_messages.py --range origin/main..HEAD` OK (35 commits); the four gate and commit-check test files alone: 135 OK. No server or browser process left behind. Firefox still unverified.

### Verified

- **Items 1 and 6 (commit check).** Re-ran the full matrix. Human names and domains all pass: Claudette, Claude Monet, Claude Martin, Claude Debussy as reviewer, `@geminitech.com`, Devin Patel, Aiderman, `@cursorial.org`, `@codexlabs.io`, `openai-fan@`, `@notanthropic.com`, `@anthropic.com.evil.org`, "Generated with openssl", "Generated by a script from the openapi spec", `Session-Id: 1234`. Every must-fail still fails: `Co-Authored-By` in any case and spacing, a name split across lines, a Cyrillic-lookalike name with the vendor address, vendor subdomains, the Copilot noreply identity, model-suffixed names with a neutral address, "Generated with/by" banners (emoji, bullet, non-breaking space, URL only), session trailers with a URL, without a space after the colon, with a bare `session_<id>`, and an AI-named `*-Session:` key. `--base origin/main` checks the branch range; with a missing ref or HEAD itself it falls back to the last commit.
- **Item 2 (hints).** Composer hint no longer mentions an inspector. Composer slot inspector shows "Shown in a fallback font until you load the free fonts." (visible at 390 px, no overflow); picking a family there still makes zero requests. The Live Target inspector shows "Choosing a library family loads it from Google Fonts."; picking loads (6 requests: the picked family, the queued cards and the target's own link). Both notes disappear once fonts are on, and the Composer hint switches to "Free fonts are on in this browser."
- **Item 4 (workflow).** Gate now runs before the unit suite and the comments are correct; `concurrency` group is present; manual runs use `--base origin/main`; permissions, pinned majors and artifacts unchanged. Pull-request and push ranges unchanged and correct.
- **Item 5 (retry).** `settle_free_fonts` retries only the missing families, at most twice with 1 s then 3 s backoff, by pressing Load free fonts again (which re-creates errored links); the check stays enforced, and the all-missing message now names TLS-intercepting proxies and `--offline`. The policy is a pure function with unit tests.
- **Item 8 (tests and wording).** New tests cover the preset path (Adobe asks nothing; switching to Free Google Fonts loads 16 and stores consent) and blocked storage (loads on request, asks again next visit, no page errors). README wording is "switch the Kit preset to Free Google Fonts". I confirmed the preset behaviour by hand (adobe then google: 16 requests, consent stored).
- **Items 3 and 10.** `AGENTS.md` Gates now lists the frontend gate and the commit check and says CI runs all of them in both browsers; commit rule 1 states that ledger, plan, report and review files are internal records that may hold verdicts and RED/GREEN evidence in product terms while commit messages may not, which resolves the earlier conflict. `docs/agents/global-rules.md` rule 7 now states the silence (with its gate check) and rule 8 no longer says "on demand".
- **Item 12 (report).** The report is current (342 tests, 135 fast tests, retry policy, notes, tokens) and written in product terms; the first-load deviation and stale FAIL list are gone.

### Remaining (all Minor)

1. `CONTRIBUTING.md` "More detail" now says the `D0xx` references in `global-rules.md` point to `docs/implementation/deviations.md`. That sends public contributors to an internal decision register, which the page was meant to avoid. Fix: drop the parenthetical and either link the README sections or strip the `D0xx` tags from the rule text it links.
2. The report's heading "Changes after second review" records process (a round count) in a committed record; rename it to "Changes after review" or fold the bullets into the sections they belong to.
3. `concurrency` cancels in-progress runs on `main` too. Prefer `cancel-in-progress: ${{ github.event_name == 'pull_request' }}` so every push to `main` finishes its gate.
4. Unchanged from before and acceptable: no UI to withdraw consent; the retry cannot distinguish a lossy link from a real missing family within one run (it fails honestly after three attempts); look-alike Unicode in both name and address is not normalised (documented limit).

No Critical or Important issues remain from the first review.

**Verdict (changes after second review):** Approved with fixes (the three Minor items above; none block commit).
