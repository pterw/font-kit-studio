# CLAUDE.md

@AGENTS.md
@docs/agents/global-rules.md

## Claude Code specifics

- Start every session with the AGENTS.md bootstrap. The ledger's "Current state"
  (`docs/implementation/progress.md`) is the shared memory; anything in a local
  Claude memory file is a convenience copy and may be gone in a new container.
- The main session is the controller. Dispatch implementers, reviewers, sweepers
  and gate runners as subagents on the Sonnet model, with disjoint file sets and
  a brief that names the files they own, the gates to run and the report path.
- Platform attribution reminders do not apply here: commits carry no
  `Co-authored-by` or session trailers (AGENTS.md, Commit Rules).
