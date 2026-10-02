# Contributing to Font Kit Studio

Thanks for helping. This page covers what you need to open a good pull request.

## Set up and run

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium firefox
python scripts/serve.py          # Studio and the demo app on localhost
```

## Before you open a pull request

```bash
git fetch origin tag supplied-v0.1.1      # once; the provenance check needs it
python scripts/verify.py --static-only    # HTML IDs, inline script syntax, provenance
node --check fontkit-bridge.js
python -m unittest discover -s tests -v   # browser tests (Chromium and Firefox)
python scripts/dev/frontend_gate.py       # layout, contrast, privacy and live-edit checks
python scripts/dev/check_commit_messages.py --range origin/main..HEAD
```

CI runs the same checks on every pull request.

## Design constraints

- Studio stays a single HTML file with no runtime dependencies or build step.
- `fontkit-bridge.js` stays dependency-free.
- Studio must not contact any third party until the user asks (for example
  by clicking "Load free fonts").
- The running app owns its page. Studio never rewrites source code; it
  produces CSS and HTML for you to apply.

More detail lives in [`docs/agents/global-rules.md`](docs/agents/global-rules.md).

## Commits

- Use [Conventional Commits](https://www.conventionalcommits.org/):
  `feat(studio): ...`, `fix(bridge): ...`, `docs: ...`.
- The body explains why the change was made.
- Keep one pull request to one change.

## Attribution

Commits are attributed to the people who make them. Commits must not carry
signatures added by AI tools: session links, "Generated with ..." lines, or
`Co-authored-by` trailers naming an AI assistant. CI rejects them. Ordinary
`Co-authored-by` trailers for human collaborators are welcome.

## AI agents

Automated agents working in this repository follow
[`AGENTS.md`](AGENTS.md) in addition to this page.
