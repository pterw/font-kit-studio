# Task 2 brief: serve.py refuses port 0 by name

Plan task 2 (E-1a), wave 1, mode code. BASE 5443ff6, worktree `the task's worktree`. Audit row E-1a (`docs/implementation/audit-2026-11-06-real-apps.md`
line 128). Budget: about 40 gross lines (source about 10, tests about 30). Rules: `../constraints.md` (O31 approves New string 6).

## Why

`python scripts/serve.py http://127.0.0.1:5000 --studio-port 0 --target-port 0` exits 2 with "--studio-port and --target-port must
differ" (`scripts/serve.py:726-727` at BASE), which is false and sends the user the wrong way. `--studio-port 0` alone passes the
check and `Config`/`Config.for_proxy` bake the port into Studio's URL, Origin allow-list and the bridge tag origin before any bind
(`scripts/serve.py:68-102`), so the printed address would be `:0` and unusable. Port 0 cannot work here; the user should be told so,
naming the flag. Cause re-read at BASE: it still holds (the only port checks in `main` are the equality test at 726-727 and the
per-server bind errors below it).

## Owned files (exact)

- `scripts/serve.py`: only `main()`, the block at 726-727 (the equality check), plus one module constant for the message if needed
  next to the other message constants (about lines 55-60). Nothing else.
- `tests/test_serve_proxy.py`: one new class `ArgumentTests`, inserted directly after `TargetTests` (ends before `class ReleaseLayoutTests`,
  BASE line 631). Touch no other class.
- `CHANGELOG.md`: one line under Unreleased only if the controller's Task 18 does not own it (it names ledger lines; add nothing, put the
  draft in the report Handoff).

Everything else is read-only. Other tasks edit other regions of these files at the same time.

## Read first

- `scripts/serve.py` 55-70 (message constants), 690-730 (`main`, argument parsing, exits).
- `tests/test_serve_proxy.py` 588-629 (`TargetTests`, in-process `serve.main` call at 614-618 with redirected stdout/stderr), and
  `load_serve` / `free_ports` in `tests/test_preview_server.py`.

## Requirements

1. `--studio-port 0` (with a valid proxy target, other port non-zero and different) returns exit code 2 and writes to stderr exactly
   New string 6 with `{flag}` = `--studio-port`:
   `serve.py: --studio-port 0 is not accepted; pick a port with --studio-port <port>`. Oracle: that literal. Observable: stderr line,
   no server started, nothing on stdout.
2. `--target-port 0` the same, with `--target-port` in both places. Oracle: literal.
3. Both flags 0: the message names `--studio-port` (the first flag checked) and does not contain "must differ". Oracle: literal,
   plus `assertNotIn('must differ', stderr)`. This is the E-1a break itself.
4. Equal non-zero ports (for example both 8123) keep the existing behaviour: exit 2 and the existing "must differ" text. Oracle: a
   second run of the same args at BASE (characterization; do not reword the existing message).
5. The port-0 check sits immediately before the equality check, so it runs first. npm's handling of 0 (E-1b) is out of scope.

## Tests (class `ArgumentTests`, in-process `serve.main(args)` with stdout and stderr redirected)

Use `free_ports()` for the non-zero port so no real port is assumed. Use the target `http://127.0.0.1:5000`; `parse_target` does not
connect.

- `test_a_zero_port_is_refused_by_flag_name` (subTest over the two flags): RED at BASE, because `--studio-port 0` alone is accepted
  and goes on to bind, and `--target-port 0` is not refused by name. Docstring: Given one flag set to 0 and the other free, when main
  runs, then it returns 2 and stderr is exactly the New string 6 line for that flag. To keep the RED from binding a real port, patch
  `serve.server_class` to a recorder that raises as in the test at 600-618; assert `binds` is empty.
- `test_two_zero_ports_are_not_called_equal`: RED at BASE (stderr says "must differ"). Given both ports 0, then stderr is the
  `--studio-port` line and has no "must differ".
- `test_equal_ports_keep_the_old_message`: GREEN characterization. Given both ports 8123, then exit 2 and stderr contains
  "--studio-port and --target-port must differ".

Realistic break to show failing: move the zero check after the equality check, or check only `--studio-port`; the second and first
tests must fail respectively.

## Focused command

From `the task's worktree`, with a 300 s timeout:
`PYTHONPATH=tests FKS_ENGINES=chromium python -m unittest test_serve_proxy test_support -v`
(one module at a time, no shards, no dev server). `ArgumentTests` alone first:
`PYTHONPATH=tests python -m unittest test_serve_proxy.ArgumentTests -v`.

## Patches

One row, so one patch: `task-2-code.patch`. Commit subject: `fix(serve): refuse port 0 by name instead of calling two ports equal`
(66 characters). CHANGELOG draft for the Handoff: "serve.py now refuses `--studio-port 0` and `--target-port 0` by name instead of
reporting two ports as equal."

## Open questions

1. How to emit the message. `parser.error(...)` (used by the equality check) prints a usage block and prefixes `serve.py: error:`, so
   New string 6, which already starts `serve.py: `, would read `serve.py: error: serve.py: --studio-port 0 ...`. Options: (a) follow
   the file's other exits: `print(f"serve.py: ...", file=sys.stderr); return 2` with the string exactly as approved (recommended: the
   approved text appears verbatim and exit 2 is kept); (b) `parser.error` with the string minus its `serve.py: ` prefix (a different
   text than approved). Requirements 1-3 assume (a). The equality check stays on `parser.error`, so its output is unchanged.
2. Argument-error ordering. At BASE, a bad target or a missing asset (exit 1, lines 713-720) is reported before the port check, because
   the check sits at 726. Recommend leaving that order (the plan places the check at 726-727) rather than moving it up.

## Controller rulings

1. Open question 1: option (a). Print New string 6 verbatim to stderr and return 2; the equality check stays on parser.error.
2. Open question 2: keep the order; the port check stays where the plan places it.

## Review fixes (binding: these govern over the text above)

1. The new check returns 2. The equality check stays on `parser.error`, which raises: the third test uses `assertRaises(SystemExit)` and checks `.exception.code == 2`, and its stderr also carries the usage block, so it asserts `contains`.
2. All three tests use the same bind recorder as the first.
3. "stderr is exactly the line" means the literal plus one newline.
