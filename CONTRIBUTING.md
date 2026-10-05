# Contributing to Font Kit Studio

Thanks for helping. This page covers what you need to open a good pull request.

## Set up and run

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium firefox   # Firefox is optional (advisory canary)
pre-commit install               # or: python -m pre_commit install
python scripts/serve.py          # Studio and the demo app on localhost
```

`pre-commit install` sets two git hooks. Before each commit they check the staged
changes for trailing whitespace, run ruff on Python files, `node --check` on the bridge
and the package's JavaScript, and the static checks when Studio, the bridge or the
provenance files change; they take a few seconds. The commit-message hook refuses a
message that carries an agent or process signature (see Commit messages below). The
slower checks below still run before you open a pull request, and in CI.

## Before you open a pull request

```bash
git fetch origin tag supplied-v0.1.1      # once; the provenance check needs it
python scripts/verify.py --static-only    # HTML IDs, inline script syntax, provenance
node --check fontkit-bridge.js
python -m ruff check .                    # unused or undefined names, syntax errors
python -m unittest discover -s tests -v   # browser tests (Chromium)
PYTHONPATH=tests FKS_ENGINES=firefox python -m unittest firefox_canary -v   # Firefox canary
python scripts/dev/frontend_gate.py       # layout, contrast, privacy and live-edit checks
python scripts/dev/check_commit_messages.py --range origin/main..HEAD
```

CI runs the same checks on every pull request. Font Kit Studio is a desktop
tool, so the Chromium test suite and the desktop Chromium gate block a merge.
Firefox runs a short canary (`tests/firefox_canary.py`) and the gate's
Firefox profiles; those, and the gate's phone and touch layouts, are
reported as advisory. (The Chromium suite keeps a few 390px layout tests
for the Composer, and those still block.)

## The npm package

`packages/fontkitstudio/` is the `fontkitstudio` command and the `fontkitstudio/vite` plugin.

```bash
npm --prefix packages/fontkitstudio test          # the package's own tests
npm ci --prefix fixtures/vite-react               # install a fixture before its browser tests
```

- The package has zero dependencies, by rule. A test fails if one is added.
- `prepack` bundles Studio and the bridge into the package and checks their versions.
- Fixtures are installed with `npm ci --prefix fixtures/<name>`. Their tests skip without `node_modules`; CI sets `FKS_REQUIRE_FIXTURES=1`, so a missing install fails there.
- Set `NEXT_TELEMETRY_DISABLED=1` when you run the Next.js fixture by hand, so Next.js sends nothing. The Next.js test sets it itself.

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
