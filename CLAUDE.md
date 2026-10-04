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
- Merging several worktree tasks into one tree: `git apply --3way` refuses when the
  target file already has uncommitted edits from another task; stage that state first
  (`git add` the file) so it becomes the merge's "ours", apply, then unstage. To commit
  one task out of a tree that holds several, apply that task's patch with
  `git apply --cached` (index only) and commit; the other tasks stay in the working
  tree. Copy whole files from a worktree only while that agent is the sole writer of
  the file. Run every task's test module on the merged tree before committing: tasks
  that are disjoint in code can still collide in behaviour (one task's new status
  wording or token rule breaking another task's assertions).
- Subagents cannot create new report files (the Write tool refuses); they return
  findings as text and the controller records them. They can append to existing
  task records.
- A stopped agent (for example on a usage limit) resumes with its context through
  SendMessage to its agent id. Earlier agents stay resumable by name, so never
  reuse a role name as an address unless you mean that exact agent.
- The session's git proxy refuses branch deletion and tag pushes (HTTP 403). The owner
  does those from a local clone after pulling; list what is needed in one line.
- When asked what fontkit is, who it is for or how it competes, answer from
  `docs/roadmap/product-direction.md` ("Where it stands"), the typography system
  design and the README, and say plainly which parts are designed but not built.
  Never present R1-R5 as shipped.
- After the owner merges a pull request from the session branch, bring the branch up to
  `main` with `git merge --ff-only origin/main`; resetting it (`checkout -B`) is refused as
  destructive.
- Line budget (D036): release-point evidence, the sweep and ledger entries count toward a
  pull request's changed lines. Leave about 300 lines of room for review fixes.
- A release-point doc pass of small, already-located edits is faster done by the controller
  than dispatched: a docs agent can spend its whole run re-reading. Dispatch when edits need
  research the controller has not done.
