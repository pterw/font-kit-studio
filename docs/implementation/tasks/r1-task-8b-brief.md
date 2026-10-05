# R1 8b brief: Studio's hints under `npx fontkitstudio`

Plan: `docs/plans/2026-10-04-r1-pr-c-sdd.md` (8b, R1.8b). Constraints:
`.superpowers/sdd/r1-pr-c/constraints.md` (read all of it first). Code: `fontkit-studio.html`
(single file; read the places named below), `packages/fontkitstudio/src/studio-server.js`
(how the package serves Studio, `?token=`), `tests/test_node_studio_server.py` (how a
browser test opens Studio from the package's server).

## Goal

The npm package serves Studio at `/fontkit-studio.html?token=...&target=...` from its own
loopback server. That server has no `/__fontkit/status` and no sync endpoint. The package
also does not contain `scripts/serve.py`. Studio still tells such a user to "Run python
scripts/serve.py", or to add a script tag that the command already added. Under the package,
those messages must say what an npm user can actually do. Under `serve.py` or `file://`,
nothing changes.

## Owns

- In `fontkit-studio.html`: the strings and the selection code for
  - `#bridgeHint` (about line 1104, and where it is shown, about 3835);
  - `BLOCKED_LOOPBACK_TEXT` (about 3788) and its use;
  - the Sync-unavailable messages (about 5654 and 5676).
- `tests/test_studio_npx_hints.py` (new).

## Behaviour

- **The test for "served by the package":** Studio's own `location.search` has a non-empty
  `token` parameter, read once at start-up. No other signal; do not probe the network for
  it.
- **For each message,** work out from the code whether it can show under the package, and
  say which in the report:
  - **Sync to file** (the `/__fontkit/status` miss): under the package, "Sync to file is not
    available under npx fontkitstudio. Use Copy or Download in the CSS tab." The control
    stays disabled with that reason, as today.
  - **The bridge hint** (`#bridgeHint`): under the package, "npx fontkitstudio adds the
    bridge to the page itself. If Studio does not connect, the terminal where the command
    runs says why." Drop the script-tag advice there. `#bridgeHintServe` stays hidden.
  - **`BLOCKED_LOOPBACK_TEXT`:** if it cannot show under the package (Studio is on
    loopback), leave it, and say why in the report. If it can, give it a package wording
    that does not name `serve.py`.
- **Text handling:** text goes through `textContent` (global rule 5; AP 3). Keep the copy
  short and plain. Say "Font Kit Studio" where the product is named (D040).
- **Without a token,** every message is byte for byte today's.

## Tests (`tests/test_studio_npx_hints.py`)

- **Under the package:** serve Studio with the package's server through its helper
  (`packages/fontkitstudio/test/helpers/serve-studio.js`, as
  `tests/test_node_studio_server.py` does).
  - Point it at a target where nothing answers (a free port with no listener). Assert the
    rendered hint and the Sync reason (the `title` of the Sync button, or the visible
    reason line; check how Studio shows it) contain the package wording and not
    `serve.py`.
  - Block `https://**`.
- **Under `serve.py`:** open the same flow through `scripts/serve.py` (pattern:
  `tests/test_preview_server.py` or `support`'s server helpers). The `serve.py` wording is
  unchanged.
- **Assertions:** assert rendered text (`inner_text`, `text_content`, attributes), never
  page source.
- **Mutation,** shown and restored: make Studio ignore the token. The package-wording
  assertions fail.

## Definition of done

- **RED, then GREEN:** `PYTHONPATH=tests python -m unittest test_studio_npx_hints -v`.
- **Run the tests that read these strings today:** grep `tests/` for "serve.py", "No bridge
  answered", "Sync to file needs" and "bridgeHint", and run those modules plus
  `test_support`.
- **Run** `python scripts/verify.py --static-only` and `python scripts/dev/frontend_gate.py`.
  Studio changed, so the gate must pass. Quote its last line.
- **Run** `python -m ruff check .`.

## Report

- Code phase report: `.superpowers/sdd/r1-pr-c/task-8b-code-report.md`.
- Patch: `.superpowers/sdd/r1-pr-c/task-8b-code.patch`.
- Handoff:
  - **CHANGELOG.** A line for `CHANGELOG.md` under Unreleased, Changed, for example:
    "Studio opened by `npx fontkitstudio` no longer points to `scripts/serve.py`; it says
    what to do instead."
  - **Ledger.** A `progress.md` event draft.
  - **Commit.** The subject `feat(studio): give npx users hints they can follow`, with a
    why-body.
