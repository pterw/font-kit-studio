# v0.2 Task H report: Quality Gate workflow, frontend gate and silent-until-asked fonts

State: current as of this write-up. Nothing is committed. Chromium only; Firefox is not installed here, so its first run is in CI.

## What shipped

| File | Purpose |
|---|---|
| `scripts/dev/frontend_gate.py` | Entry point: the check table, the runner, the CLI and the exit code. |
| `scripts/dev/_frontend_gate_shared.py` | Viewport profiles, `Outcome`, `GateContext`, bounded waits, the state driver and the colour probe. No Playwright import. |
| `scripts/dev/_frontend_gate_runtime.py` | Playwright loading, engine launch, the `serve.py` subprocess, the request router and the install guidance. |
| `scripts/dev/_frontend_gate_report.py` | Findings, line format, tally, the exit-code rule and the summary line. Pure. |
| `scripts/dev/_frontend_gate_colour.py` | WCAG colour maths, copied from the sibling project with a provenance note, plus `flatten_layers`. Pure. |
| `scripts/dev/_frontend_gate_live.py` | Connect Studio to the demo, select, type, pop out, reconnect banner, and the live-edit check. |
| `scripts/dev/_frontend_gate_network.py` | Network isolation and free-fonts checks, with pure judges and the retry policy. |
| `scripts/dev/_frontend_gate_layout.py` | Overflow, initial visibility and touch targets. |
| `scripts/dev/_frontend_gate_theme.py` | Theme contrast. |
| `scripts/dev/_frontend_gate_assets.py` | Logo paint. |
| `scripts/dev/check_commit_messages.py` | Mechanical commit-message check (stdlib only). |
| `tests/test_frontend_gate_{report,helpers,runner}.py`, `tests/test_commit_messages.py` | 135 fast unit tests, no browser. |
| `.github/workflows/quality-gate.yml` | CI. |
| `font_kit_studio_v0.1.1.html` | Contrast tokens, silent-until-asked font loading and its hints (CSS, font-loading JS and markup only). |
| `tests/test_studio_live.py` | Free-font tests rewritten or added for the new behaviour. |
| `README.md` | "Development and testing" and "Free fonts". |

## Design

Structure, principles and helpers come from the sibling project's gate (runtime, results, pipeline, layout, theme, assets, forms and colour modules and its `test.yml`). Its app-specific checks (Flask, Tailwind, Last.fm forms, results pages, loading pipeline, heatmap, exports) were left behind.

- **Server.** `scripts/serve.py` runs as a subprocess on two OS-assigned loopback ports with `--no-sync`, so a gate run cannot write to the tree. It is stopped in a `finally` (SIGTERM, then kill). A unit test starts it, reads both origins and proves the port is closed afterwards.
- **One browser context per check, profile and engine.** Touch emulation belongs to a context, and preferences or routes cannot leak between checks.
- **Deterministic network.** Every request leaves through one router. The two served origins pass; everything else is aborted and logged. Only the free-fonts check lets Google Fonts hosts through, and `--offline` closes even that.
- **Bounded waits.** Waits poll every 50 ms rather than on animation frames, because a frame scrolled out of view stops delivering them (the phone profile's live edit hung on this). The only fixed wait is a short "nothing more arrives" pause.
- **Enforcement in one place.** An enforced check's failures are `FAIL`. A report-only check's failures become `REPORT`. A check that raises is always a `FAIL`. Exit 0 needs no `FAIL` and every planned run finished; `REPORT` and `SKIP` never change it. Missing Playwright, a missing browser or an unknown engine exit 1 before any check, with the exact install command.
- **Flags.** `--headed`, `--offline`, `--engines`, and `--artifacts` (screenshots of failing runs, default `work/frontend-gate/`, cleared at the start of each run).

## Check catalogue

Profiles: `desktop` 1280x720, `mobile` 390x844 touch, `wide touch` 1280x800 touch. 15 planned runs per engine.

| # | Check | Profiles | Enforced | Measures |
|---|---|---|---|---|
| 1 | network isolation | desktop | yes | First load of Studio Library, Composer, Studio connected to the demo, and the demo alone makes no request outside the two served origins. Google Fonts and Adobe requests are named in the message. |
| 2 | free fonts load | desktop | yes; needs network, `--offline` gives a counted `SKIP` | After Load free fonts, every one of the 16 families resolves a loaded face. Families still missing are retried twice with a 1 s then 3 s backoff before they fail. |
| 3 | no horizontal overflow | all three | yes | Library, Composer specimen, connected target view with a selection, the demo inside the frame, the pop-out placeholder and the demo standalone never scroll sideways. |
| 4 | initial visibility | desktop, mobile | yes | Things a script reveals later compute `display: none` on load; a missing node fails. |
| 5 | live edit | all three | yes | Select a demo element (tap on touch), type a size, the iframe's computed size and the CSS tab follow, Reset restores the page byte for byte. |
| 6 | logo paint | desktop | yes | Both logos have no text, script or external reference, and every painted colour reaches 3:1 on GitHub light and dark pages, as an image and as inline markup. |
| 7 | theme contrast | desktop, mobile | v0.2 surfaces yes (4.5:1), legacy surfaces `REPORT` | Light and dark through the real toggle; text flattened over the first opaque ancestor background. |
| 8 | touch targets | mobile, wide touch | no, `REPORT` only | 44 px smaller side, label/input pairing, duplicates collapsed, each target reported once. |

### Commit-message check

`python scripts/dev/check_commit_messages.py [--range A..B] [--base REF]`, run in CI on pushes, pull requests and manual runs.

- Rejected: a `*-Session:` trailer whose value holds a URL or a `session_<id>`, or whose name names an AI tool; a `Co-authored-by` trailer whose email is an AI vendor's domain (or a subdomain) or the Copilot identity, or whose whole name is an assistant (`Claude`, `Copilot`, `ChatGPT`, `Gemini`, ...; model suffixes such as `Claude Opus 4.1` included); a "Generated with/by" line that names an AI tool as a whole word or has a claude.ai or anthropic URL.
- Allowed: ordinary human co-authors, including people called Claude or Devin and domains such as `geminitech.com`, `cursorial.org` and `codexlabs.io`. Matching is by exact domain and exact identity, not by substring. Merge commits are skipped.
- `--base REF` checks `REF..HEAD` when the ref exists and is not HEAD, otherwise the last commit. An unreadable range is an error, not a pass.
- Output: `FAIL <short sha> <subject>: <reason>` and a one-line summary.
- Known limit: look-alike Unicode characters in a name or address are not normalised.

## Workflow

`permissions: contents: read`, no secrets, a `concurrency` group that cancels an older run of the same ref, a 30-minute timeout, `workflow_dispatch`.

Step order, cheapest first: full-history checkout with tags (provenance needs the `supplied-v0.1.1` tag), Python 3.11 with pip cache, Node 22, install dependencies, `verify.py --static-only`, `node --check fontkit-bridge.js`, commit-message check, install Chromium and Firefox with `--with-deps`, **the frontend gate** (about 25 s per engine), then the unit suite on both engines (several minutes), then a screenshot upload on failure. The commit check uses `origin/$BASE_REF..HEAD` on pull requests, the pushed range on pushes (falling back to the last commit when the old tip no longer exists), and `--base origin/main` on manual runs.

Validation: `yaml.safe_load` parses it, and `actionlint` 1.7.12 (installed with pip into a scratch directory) reports nothing. A deliberately broken workflow was rejected by the same linter. The workflow itself has not run.

## Silent until asked (Google Fonts)

Studio makes no request outside the server it came from until the user asks for free fonts.

- Asking: Load free fonts (Library or Composer), switching the Composer Kit preset to Free Google Fonts from another preset, or choosing a library family in the Live Target inspector.
- Choosing a family in the Composer's slot inspector is not asking. That inspector says "Shown in a fallback font until you load the free fonts." beside the control; the note disappears once fonts are on.
- The Live Target inspector says "Choosing a library family loads it from Google Fonts." until fonts are on.
- Families the page wants before consent are queued and requested after it.
- Consent is stored under `fontkit-free-fonts` through the guarded store. If storage is blocked Studio still loads on request and asks again next visit.
- Hints sit beside the Library and Composer font controls: fallbacks until loaded, and loading contacts Google Fonts (IP address and font names). The Composer hint makes no claim about an inspector.
- Tests assert rendered outcomes: zero external requests on Library and Composer first load, the hints, the link after each kind of asking, a remembered revisit, blocked storage, and both inspector notes.
- README screenshots were not regenerated: the capture script stubs Google Fonts, so fonts do not change them.

## Contrast fixes

Two scoped tokens were added so v0.1.1 surfaces keep their `--muted`:

| Token | Light | Dark |
|---|---|---|
| `--muted-strong` | `#625e56` (5.23:1 on `--chip`, 6.35 on `--panel`, 5.72 on `--bg`) | `#a7a198` (5.91 / 6.87 / 7.38) |
| `--warn-text` | `#9a3412` (5.34:1 on the badge tint, 6.33 on the bridge bar) | `#fca5a5` (9.28:1 on `--panel`) |

`--muted-strong` replaces `--muted` in eight v0.2 rules. `--warn-text` is used by the bridge badge's error states, the bridge warning, the code warnings and the code status error, which previously had no dark colour.

## Results

| Command | Result |
|---|---|
| `frontend_gate.py --engines chromium --offline` | exit 0: `15 of 15 planned runs finished: 14 passed, 0 failed, 1 skipped; 140 REPORT lines, 1 SKIP lines, 0 FAIL lines` |
| `frontend_gate.py --engines chromium` (online) | exit 1: 14 passed, 1 failed, 0 skipped, 140 REPORT lines. The one failure is `free fonts load`, a sandbox network limit (below). |
| `python3 -m unittest discover -s tests -v` | `Ran 342 tests in 319.548s` `OK` (Chromium) |
| the four gate and commit-check test files alone | `Ran 135 tests in 0.960s` `OK` |
| `scripts/verify.py --static-only` | 5 PASS |
| `node --check fontkit-bridge.js` | rc 0 |
| `check_commit_messages.py --range origin/main..HEAD` | `OK: 35 commits checked` |
| `ruff check --select F,E9` on the new Python | clean |

Online free-fonts: Playwright's Chromium does not use the sandbox's TLS-intercepting proxy, so no stylesheet loads and the failure message says so. With a scratch probe giving Chromium the proxy and ignoring certificate errors, all 16 stylesheets loaded but four font files still failed to arrive through the lossy proxy, and the retries (which re-request stylesheets, not font files) cannot recover those. A green online run needs a real network; CI will show it.

Mutation checks against scratch copies showed the gate catches a removed `[hidden]` rule, forced overflow, a lighter `--muted`, a white logo fill and an external script in the demo.

## REPORT findings (not blocking)

- Touch targets: 67 lines on `mobile` and 71 on `wide touch`: Studio's small buttons, selects and inputs, the Live Target inspector and code panel controls, and the demo's `summary` rows and inputs.
- Legacy contrast: Library `span.tag` chips, `--muted` `#6f6b63` on `--chip` `#ece7dc`, 4.30:1 (55 of them, light mode).

## Open concerns

1. **Firefox is unverified.** The assumptions most likely to differ: `has_touch` and tap, the `color(srgb ...)` serialisation of `color-mix()`, the canvas read-back of an SVG `<img>`, and popup handling. A Firefox-only failure is more likely a gate assumption than an app defect until shown otherwise.
2. **Free-fonts needs a real network** and has not passed anywhere yet.
3. Consent cannot be withdrawn in the UI; the README says to clear site data.
4. The remembered-consent test proves persistence within one browser context, not across a browser restart.

## Changes after second review

- Commit check: identity is now judged by email domain and exact assistant name, not substrings. All of Claudette, Claude Monet, `@geminitech.com`, Devin Patel, Aiderman, `@cursorial.org` and `@codexlabs.io` pass; every earlier must-fail still fails. Banners match whole words. Session trailers are also flagged by AI-tool name or `session_<id>` without a URL. `--base` added. 21 tests.
- Composer hint no longer mentions an inspector; the true sentence moved to the Live Target inspector, and the Composer slot inspector got a fallback note (both disappear once fonts are on).
- Workflow: gate before the unit suite, the slowest-step comment corrected, a concurrency group, manual runs check `origin/main..HEAD`.
- Free-fonts check: bounded retry (two extra attempts, backoff 1 s and 3 s), still enforced, message names TLS-intercepting proxies.
- README: preset wording is "switch the Kit preset to Free Google Fonts"; tests added for the preset path and for blocked storage.
