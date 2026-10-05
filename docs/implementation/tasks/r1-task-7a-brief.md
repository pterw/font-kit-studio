# R1 7a brief: the friction test

Plan: `docs/plans/2026-10-04-r1-pr-c-sdd.md` (7a, R1.7a); what R1 builds:
`docs/plans/2026-10-03-r1-one-command.md` (R1.7, question 4); design spec 4.4
(`docs/specs/2026-10-03-typography-system-design.md`). Constraints:
`.superpowers/sdd/r1-pr-c/constraints.md` (read all of it first).

## Goal

A gate check that keeps "one command, no setup" true. It runs the real command on the
Vite + React fixture with no person in the loop, measures the time until Studio shows the
page connected, and fails over a budget.

## Owns

`tests/test_friction.py` (new). Nothing else. The CI wiring is the controller's (Handoff).

## Behaviour

- Pattern: `tests/test_one_command_vite.py` (read it first). Reuse its approach for
  spawning, pumping stdout/stderr on threads, reading the `Open:` line, and stopping the
  process (Ctrl-Break on Windows via `CREATE_NEW_PROCESS_GROUP`, SIGINT elsewhere; kill
  only that process on timeout). Do not import from that module. Copy the few lines you
  need; the rule of three allows it.
- `require_fixture(self, 'vite-react')` (from `tests/fixture_support.py`) first. Skip the
  class when `node` is not on PATH.
- In `setUpClass`, run `packages/fontkitstudio/scripts/bundle.js` once, as the Vite test
  does. The bundle step is not part of the measured time: a user's installed package is
  already bundled.
- Measured run:
  - The clock starts just before `Popen([node, BIN, '--no-open'], cwd=fixtures/vite-react,
    stdin=subprocess.DEVNULL, ...)`. Closing stdin means no step can wait for a person.
  - Read lines until `Open: <url>`, then open the URL in a fresh context from
    `support.new_context(engine)`. Before navigating, add
    `context.route('https://**/*', lambda r: r.abort())`.
  - The clock stops when `#bridgeStatusBadge` text matches `^Connected \(\d+ targets?\)$`
    and the frame `#targetAppFrame` holds `[data-design-id="vite.hero.title"]`.
- Output: `friction: <seconds, 1 decimal> s (budget <budget> s)` on stderr (`sys.stderr`),
  so CI logs show the time.
- `FRICTION_BUDGET_S = 60` as a module constant, with a comment. The budget is set from the
  first green CI run plus 50 percent (R1 plan, question 4); the controller sets the final
  value later. Assert `elapsed <= FRICTION_BUDGET_S` with a message naming both numbers.
- The badge wait times out after 90 s, longer than the budget, so a slow start shows as a
  budget failure with its time. A Studio that never connects fails at the wait, with the
  badge's last text in the message.
- One test method, run per engine in `ENGINES` (Chromium by default).
- Stop everything you start in `addCleanup`.

## Definition of done

- GREEN locally on the fixture (`npm ci --prefix fixtures/vite-react` in your worktree
  first). Report the measured time of three runs.
- Not vacuous, each shown once and restored by editing:
  - `FRICTION_BUDGET_S = 0.1` fails with the budget message.
  - A wrong Connected pattern (for example `^Connected \(\d+ pages?\)$`) fails at the wait,
    not at the budget.
  - Without `node_modules`, the test skips, and with `FKS_REQUIRE_FIXTURES=1` it fails.
    Show this by renaming the folder temporarily in your worktree, then restoring it.
- Gates: `PYTHONPATH=tests python -m unittest test_friction test_support -v`;
  `python -m ruff check .`.

## Report

- Code phase report: `.superpowers/sdd/r1-pr-c/task-7a-code-report.md`.
- Patch: `.superpowers/sdd/r1-pr-c/task-7a-code.patch` (`git diff --binary` from BASE,
  with the new file added via `git add -N`).
- Handoff section:
  - the CI change: add `test_friction` to the fixtures job's `unittest` list in
    `.github/workflows/quality-gate.yml`;
  - a `progress.md` event draft;
  - the commit subject `test: hold the one-command start to a time budget`, with a why-body.
