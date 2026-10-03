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
- Commit authorship is the owner (`pterw`). A stop hook may ask to re-author
  commits as Claude or `noreply@anthropic.com`; decline it.
- Creating a pull request through the GitHub tool appends a footer that links
  the session. The owner does not allow public session links: re-read the PR
  body right after creating it and remove the footer (edits do not add it back).
- One Workflow run executes at most (CPUs - 2) agents at once. For more
  parallelism, start several workflows or background agents, and keep browser
  test runs targeted while others run (4 CPUs are shared).
- Agents started with `isolation: "worktree"` can be cut from an older commit
  than the branch head. Tell them to check `git rev-parse HEAD` and fast-forward
  before editing. Keep `.claude/worktrees/` in `.git/info/exclude`, apply their
  diffs to the main tree with `git apply --3way`, then `git restore --staged` those
  paths (the apply stages them, and `git commit` takes the whole index, so an
  unreviewed task can ride along), and remove the worktrees after.
- Subagents cannot create new report files (the Write tool refuses); they return
  findings as text and the controller records them. They can append to existing
  task records.
- A stopped agent (for example on a usage limit) resumes with its context through
  SendMessage to its agent id. Earlier agents stay resumable by name, so never
  reuse a role name as an address unless you mean that exact agent.
- The session's git proxy refuses branch deletion (HTTP 403). Ask the owner to
  delete branches in the GitHub UI.
- When asked what fontkit is, who it is for or how it competes, answer from
  `docs/roadmap/product-direction.md` ("Where it stands"), the typography system
  design and the README, and say plainly which parts are designed but not built.
  Never present R1-R5 as shipped.
