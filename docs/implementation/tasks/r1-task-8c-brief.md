# R1 8c brief: README, package README, CONTRIBUTING

Plan: `docs/plans/2026-10-04-r1-pr-c-sdd.md` (8c, R1.8c); what R1 builds:
`docs/plans/2026-10-03-r1-one-command.md` (R1.8). Constraints:
`.superpowers/sdd/r1-pr-c/constraints.md` (read all of it first). D040 (public name), D051
(the command opens the browser; terminal-only dev marker) in
`docs/implementation/deviations.md`. Located inputs from two sweeps:
`.superpowers/sdd/r1-pr-c/sweep-8c-inputs.md`. Treat it as a list of places to look, not as
quotes: one quoted line in it was wrong. Check every item against the current file.

## Goal

A developer who lands on the README or on npm's page for `fontkitstudio` learns how to use
Font Kit Studio from the docs:

- `npx fontkitstudio` in a Vite project;
- `npx fontkitstudio http://localhost:<port>` in front of any other local dev server
  (Next.js named);
- `fontkitStudio()` from `fontkitstudio/vite` for a permanent setup.

The Python dev server and the script tag stay documented as the path with no Node. Every
claim matches the code as it is now.

## Owns

`README.md`, `packages/fontkitstudio/README.md`, `CONTRIBUTING.md`. Nothing else.
- Studio's text belongs to 8b, already landed.
- CHANGELOG, the roadmap and product-direction are the controller's.

## Facts to use (verify each in the code before you write it)

- **CLI** (`packages/fontkitstudio/src/cli.js`; run `node packages/fontkitstudio/bin/fontkitstudio.js --help`):
  - `fontkitstudio [<url>] [--no-open] [--studio-port <n>] [--help] [--version]`;
  - it opens the browser by default (D051);
  - it prints `Font Kit Studio · dev only` and `Open: <url>`;
  - usage errors exit 2, start-up failures exit 1.
- **Requirements:** Node 22.12 or later (`engines`); Vite 7 or 8 in Vite mode (another
  major is refused with a message). Proxy mode accepts only a local `http:` target
  (localhost or 127.0.0.1).
- **What it does:**
  - **Vite mode:** runs the project's own Vite with the plugin added in memory. Nothing is
    written to the project; the project's `vite.config` still loads.
  - **Proxy mode:** a loopback proxy that adds one script tag to HTML pages and serves the
    bridge from the app's own origin. The app's CSP header passes through unchanged, and
    WebSocket upgrades (hot reload) pass through.
  - **Plugin:** `fontkitStudio()` in `vite.config` starts Studio with `npm run dev`, is left
    out of `vite build` (the build says so), and ships TypeScript types.
  - **Security:** Studio is served on loopback with a per-run token in its URL, plus Host and
    Origin checks. The command refuses a Vite server opened to the network.
- **Messages it prints** (`src/csp.js`, `src/vite-plugin.js`): a page that loads its own
  bridge, a CSP that blocks the bridge, a non-local host. Name them in a short
  "If Studio does not connect" list. Do not paste every string.
- **Known limits** (plan, owner question 2):
  - Sync to file needs `python scripts/serve.py`; the npm command does not serve it, and
    Studio says so.
  - In proxy mode the app runs at the proxy's address, so its own browser storage
    (localStorage, IndexedDB, service workers) is not the storage it has at its usual
    address. (Corrected at review: an earlier draft said Studio's settings.)
  - A standalone `fontkitStudio()` gets a new Studio URL when Vite restarts after a config
    change.
  - The plugin sees a CSP that middleware sets only when the page carries it in a meta tag.

## README.md

1. **Quickstart.** Lead with the command, in a few lines (Vite project; any other local
   server by URL; permanent plugin). Then the existing Python quickstart, re-titled as the
   way to try the demo or work without Node. Keep its steps accurate.
2. **"Add fontkit to your app"** becomes "Add Font Kit Studio to your app". Update every
   anchor link that points at it (grep `#add-fontkit`). Rename "Why fontkit" the same way,
   with its links. Apply D040 to user-facing prose you touch. Keep `fontkit-bridge.js`,
   `fontkit-studio.html` and code identifiers as they are.
3. **Recipes:**
   - **Vite:** `import { fontkitStudio } from 'fontkitstudio/vite'` and
     `plugins: [fontkitStudio()]`, run in CI on the fixtures. Drop the hand-written plugin.
   - **Next.js:** lead with `npx fontkitstudio http://localhost:3000` next to `next dev`,
     proven on a Next 16 fixture in CI. Keep the script-tag layout as the alternative.
   - **"How these recipes were checked":** Vite and Next.js are now run in CI.
     Astro, SvelteKit and Nuxt stay illustrative.
4. **FAQ and Quick facts.** Lines that say "no npm package" or "one script tag" are now
   wrong or incomplete. Fix them.
5. **Security model:** add a short paragraph for the package's server and proxy (loopback,
   per-run token, Host and Origin checks, dev only, the proxy never serves a local file but
   the bridge).
6. **Development and testing:**
   - add the Node package tests (`npm --prefix packages/fontkitstudio test`) and the
     fixtures (`npm ci --prefix fixtures/<name>`; tests skip without `node_modules`, CI sets
     `FKS_REQUIRE_FIXTURES=1`);
   - add the friction test;
   - add rows to the module table for every test module that is missing:
     `test_one_command_vite`, `test_one_command_proxy`, `test_one_command_messages`,
     `test_vite_build_guarantee`, `test_friction`, `test_one_command_next`,
     `test_vite_types`, `test_studio_npx_hints`, and `test_precommit_hooks` if absent.
     Read each module's docstring for its row.
7. **Known limits:** add the list above in the right section, short.
8. **Roadmap / extension lines:** where they say a script tag is needed today, say the
   command removes it for local apps, and the extension (not built) is for sites you do not
   run.

## packages/fontkitstudio/README.md (npm's page)

Replace "arrives in 0.3.0; this release is the package foundation". Include:
- a one-line description;
- the three commands;
- the two flags;
- the requirements;
- the "If Studio does not connect" pointers;
- Sync to file needing the repository's dev server;
- the D040 note that `fontkit-bridge.js` belongs to Font Kit Studio and has no relation to
  the `fontkit` font engine;
- a link to the repository README.

Keep it short: npm users skim. No badges and no external images; the page must not load
anything.

## CONTRIBUTING.md

A short "The npm package" section:
- `npm --prefix packages/fontkitstudio test`;
- zero dependencies by rule (a test fails if one is added);
- `prepack` bundles Studio and the bridge and checks their versions;
- fixtures are installed with `npm ci --prefix fixtures/<name>`;
- `NEXT_TELEMETRY_DISABLED=1` for the Next fixture.

## Style

`AGENTS.md`, "Markdown Authoring Rules". Plain English, short sentences, active voice.
Match the README's existing tone and formatting. Do not restructure sections you do not
need to touch. Do not invent behaviour: if the code does not do it, do not write it.

## Definition of done

- **Links:** every link and anchor in the three files resolves. Check README anchors with a
  quick script that compares `](#...)` targets with heading slugs, GitHub style.
- **No stale claims:** `git grep -n -i "no npm package\|arrives in 0.3.0\|not run in a real framework project"`
  finds nothing in the three files.
- **Tests that read the README:** `PYTHONPATH=tests python -m unittest test_live_integration -v`.
  It runs the README's own script tag and bookmarklet, so a recipe change must keep them
  working. Also run `python scripts/verify.py --static-only`, `python -m ruff check .` and
  `python -m pre_commit run --files <your three files>`.
- **Report:** list each claim you added, with the file:line in the code that backs it.

## Report

- Code phase report: `.superpowers/sdd/r1-pr-c/task-8c-code-report.md`.
- Patch: `.superpowers/sdd/r1-pr-c/task-8c-code.patch`.
- Handoff:
  - a `progress.md` event draft;
  - the commit subject `docs: lead with npx fontkitstudio and document the package`, with a
    why-body;
  - the README's material line count.
