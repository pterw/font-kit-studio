# Independent verification tooling task

## Goal

Make the development checks reproducible from a fresh copy while the app implementation proceeds separately. This supports Task 5; it does not claim final acceptance of a changing app.

## Ownership

Own README.md, requirements-dev.txt, scripts/verify.py and docs/implementation/tasks/verification-tooling-report.md only. Do not change HTML, tests, plans, ledgers, original reference documents or any other report. Other agents own those files. Do not stage, commit or otherwise mutate Git state; the controller will commit this isolated scope at a safe point and assign its own reviewer. Do not spawn subagents.

## Requirements

- Keep the app a single self-contained HTML file, with no runtime packages. Python Playwright is development-only; use the actual installed version for reproducibility. Explain installing the Python package and Chromium/Firefox development browsers, Node for JavaScript syntax, and running checks. README remains brief.
- Add one small Python standard-library script runnable as `python scripts/verify.py`. Locate the app relative to the script, never relative to the invoking directory. Extract executable inline script blocks using HTMLParser, check each with `node --check` in a temporary directory, reject duplicate static HTML IDs, compute SHA-256, and compare original input provenance to Git tag supplied-v0.1.1 when Git metadata is available. Each failure must return nonzero and describe the failing check.
- The script runs `python -m unittest discover -s tests -v` using the current interpreter and repository cwd by default. Allow `--static-only` for a focused tooling check without rerunning the evolving browser suite; clearly report that browser tests were skipped in that mode. Never make skipped checks look like a full pass. No generated output overwrites source files or leaves untracked scratch.
- Prefer a simple implementation with subprocess argument lists and temporary files, not a framework. Preserve the README's plan/progress/deviation links, original-baseline distinction, optional Adobe kit description, and file:// run instructions.
- Exercise static-only against the current artifact, and meaningful failure checks in temporary fixtures (at least duplicate IDs and invalid JS) without touching app/tests. Do not run the full browser suite during this parallel setup: Task 5 owns the final full run after source changes stop.
- Write the report with commands, outputs, self-review and limitations. Return DONE/concerns, assigned files and a short check summary. Parent will review before accepting.

## Evidence context

Graph service unavailable: parent list_projects/search_graph/check_index_coverage returned Transport closed, project/generation unknown. Exact supplied paths and current source are the fallback; make no graph or final UI acceptance claims. The user explicitly permits concurrent agents with no overlapping scopes, and requires an independent reviewer after every implementation.
