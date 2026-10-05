# Task 8c code report (mode: code, BASE 60accb0, worktree C:/fks/t8c)

Changed (staged in the worktree, nothing committed): `README.md`, `packages/fontkitstudio/README.md`, `CONTRIBUTING.md`.
Patch: `.superpowers/sdd/r1-pr-c/task-8c-code.patch` (`git apply --check -R` passes). Files written with LF.

## Per brief step
- README 1 Quickstart: done. Leads with the three commands, then the Python quickstart under "### Try the demo, or work without Node". The garbled sweep line (52) was rewritten to point at the script tag "without Node".
- README 2 Renames: done. "Add Font Kit Studio to your app", "Why Font Kit Studio", nav and Quickstart anchors updated (no `#add-fontkit` left). D040 applied to every bare "fontkit" in prose (logo alt, intro, Why table, FAQ, Tailwind, markup, security, roadmap). Identifiers and file names untouched.
- README 3 Recipes: done. Vite uses `fontkitStudio()` (hand-written plugin dropped). Next.js leads with the proxy, script tag kept as alternative. "How these recipes were checked" now says Vite and Next.js run in CI; Astro, SvelteKit, Nuxt illustrative.
- README 4 FAQ: done. "no npm package" gone; "One command" and "Or one script tag" bullets; the browser-extension bullet is now "Sites you do not run".
- README 5 Security: done (new "The npm package" paragraph).
- README 6 Development and testing: done. Added `npm --prefix packages/fontkitstudio test` line, a Fixtures paragraph, nine module rows (`test_one_command_vite/proxy/next/messages`, `test_vite_build_guarantee`, `test_vite_types`, `test_friction`, `test_studio_npx_hints`, `test_precommit_hooks`). `test_node_studio_server` was already present. The friction test is a row plus its description there; there is no separate friction prose block.
- README 7 Known limits: done as two new subsections under "Add Font Kit Studio to your app": "If Studio does not connect" and "Known limits of the npm package". Also a sentence in Sync to file bullets (line 68 area and the Code panel).
- README 8 Roadmap/extension lines: done (roadmap paragraph, FAQ bullet, "What it is" bridge line).
- Package README: rewritten (description, three commands, two flags, requirements, "If Studio does not connect", Sync to file, D040 note, repo link). No badges, no images; the only links are to the repository README.
- CONTRIBUTING: "The npm package" section added.

## Claims and the code that backs them
- Usage, flags, `--help`/`--version`: `src/cli.js:12-21` (USAGE), `:27-52` (parseArgs). Exit codes 2 and 1: `cli.js` main catch and usage branches.
- Opens browser by default, prints `Font Kit Studio · dev only` and `Open:`: `run-vite.js:64-65`, `run-proxy.js:61-63`.
- Vite 7 or 8, another major refused: `project.js:9` (`TESTED_VITE_MAJORS`), `:68`, `:80`.
- Node 22.12: `package.json` engines.
- Proxy accepts only local `http:`: `proxy.js:46-58` (`parseProxyTarget`).
- Vite mode, nothing written, config still loads, in memory: `vite-plugin.js` (`standalone` false path, `api.fontkitStudio.fromCommand` at ~97-98); no file writes in `run-vite.js`.
- Proxy adds one tag and serves the bridge from its own origin: `proxy.js:111` (tag), `:277` (`isBridge`); WebSocket upgrades: `proxy.js:291-307`; CSP header passes through: `proxy.js:125-126` only inspects it.
- Plugin: start with `npm run dev` and print `Open:`: `vite-plugin.js:121-134`; build line: `:17`, `:91-92`; types: `vite-plugin.d.ts`, `package.json` exports.
- Plugin does not open the browser: no open call in `vite-plugin.js` (so the README says it prints the address). Command does: `open-browser.js`.
- Per-run token, Host and Origin checks: `studio-server.js:17-19`, `:31`, `:89-90`; token not sent to the app: `tests/test_node_studio_server.py` docstring.
- Refuses Vite opened to network: `vite-plugin.js:18`, `:21`, `configResolved`.
- Messages: `csp.js:6-9` (own bridge, CSP), `vite-plugin.js:18` (host), `proxy.js:53` (non-local target), `cli.js` (no Vite project), `project.js:68` (untested major).
- Known limits: Sync text `NPX_SYNC_TEXT` in the 8b patch (`fontkit-studio.html`, "Sync to file is not available under npx fontkitstudio. Use Copy or Download in the CSS tab."). CSP reads meta and `server.headers`: `vite-plugin.js:160`, `configResolved` headerPolicies. Restart gives a new Studio URL: the standalone path starts a new Studio server per `configureServer` (`vite-plugin.js:121`). `--studio-port` keeps settings: USAGE text. Saved settings sit with the proxy's address: from the plan (owner question 2), not re-derived in code.
- Fixtures list and Vite 7.3.6 / 8.3.2, Next 16.3.8: `fixtures/*/package.json`; CI `npm ci` lines in `quality-gate.yml`. `bootstrap5-static` has no install, so it is not listed.
- Test module rows: each module's docstring. `NEXT_TELEMETRY_DISABLED`: `tests/test_one_command_next.py:80`. Skip without node_modules: `tests/fixture_support.py:15-23`.

## Evidence
- Anchors: script compared every `](#...)` and `href="#..."` with GitHub-style heading slugs; relative file links checked to exist. Output `ok`, nothing broken.
- Stale grep (`no npm package|arrives in 0.3.0|not run in a real framework project`) over the three files: no matches (rc=1). I reworded the Astro/SvelteKit/Nuxt line to "no test runs them in a framework project" so it stays clear.
- `PYTHONPATH=tests python -m unittest test_live_integration`: Ran 52 tests, OK (it needs no fixture `node_modules`).
- `python scripts/verify.py --static-only`: exit 0, last line "SKIP unittest/browser tests: --static-only; full acceptance not checked".
- `python -m ruff check .`: All checks passed.
- `pre_commit run --files <three>`: whitespace hook Passed (staged); ruff, node syntax, static hooks Skipped (no matching files).
- No test module edited, so `test_support` not run. Full suite not run: docs only, `test_live_integration` was the named gate. No `npm ci` was run; no fixture install needed.
- Processes: only the unittest run (it stops its own server). Scratch `work/` created by the test removed.

## Self-review
- AP 9/11 (rename siblings): grepped `Add fontkit`, `Why fontkit`, `#add-fontkit` in live files: none left. `fontkit-studio.html:3692` badge title is 8b's.
- AP 14: the docs say fixture tests skip locally and CI requires them; nothing here skips.
- AP 15: no process state in the docs.
- D040: only identifiers, file names and the "not the `fontkit` font engine" note keep the bare word.
- Concerns: (1) the docs say `npx fontkitstudio` and `npm install --save-dev fontkitstudio` work, which holds only once 0.2.1 or later is published (9b). (2) The README's "Saved settings follow the address" claim comes from the plan, not the code. (3) Older README lines (Open the Studio HTML file directly, Dev server options) were left alone.

## Handoff
- Commit subject: `docs: lead with npx fontkitstudio and document the package`
- Body draft: The README still led with the Python dev server and said there was no npm package. Lead with the three npm paths (the command in a Vite project, the command in front of another local server, the plugin), keep the Python path for the demo and for Sync to file, and document what the command does not do. Rename the Add and Why sections to Font Kit Studio and update their anchors (D040). Rewrite the Vite and Next.js recipes now that CI runs them. Replace the package README's "arrives in 0.3.0" text, and add an npm section to CONTRIBUTING.
- README material lines: 110 added, 42 removed (`git diff --numstat`); 152 changed lines. CONTRIBUTING +14; package README +48/-7. All three files: 172 added, 49 removed.
- progress.md event draft: `8c: README leads with npx fontkitstudio, package README and CONTRIBUTING document the package; live_integration 52 OK, anchors and stale-claim greps clean.`
- CHANGELOG: nothing required from this task beyond the controller's [Unreleased] line, if wanted: "Document the one command, the Vite plugin and the Next.js proxy path in the README."

## Fix round 1
Only `README.md` changed in this round; the patch is regenerated at the same path (`git apply --check -R` passes).
1. Replaced the false "Saved settings follow the address" bullet with two. Checked in code: `startProxy` defaults `host='127.0.0.1'`, `port=0` (`proxy.js:70-75`, `:334`) and `run-proxy.js` passes no port, so no flag sets it; the proxy forwards `Set-Cookie` unchanged. The first bullet says the app starts with empty storage at the proxy's address, cookies for `localhost` are not sent to `127.0.0.1`, and "the command offers no way around this" (the code offers nothing). The second says Studio's settings follow Studio's address, `--studio-port` keeps it, and a busy port makes Studio pick another and say so (`run-proxy.js:14-19`). Vite mode is not affected.
2. Added "The command needs `fontkitstudio` 0.3.0 or later." under the Quickstart npx block. The package README is unchanged.
3. Restored the `transformIndexHtml` caveat in the Vite recipe: the plugin adds its tag in that step, so frameworks that handle the HTML entry themselves (SvelteKit) do not get it, and the text points to the proxy command.
4. FAQ bullet now says Node 22.12 or later, and in a Vite project the project's own Vite 7 or 8.
5. `test_one_command_messages.py` row now states the three checks from its docstring.
6. "How these recipes were checked" now says what runs in CI (plugin and command on the Vite 7 and 8 fixtures, proxy command on the Next.js 16 fixture) and lists the Next.js script-tag layout with Astro, SvelteKit and Nuxt as illustrative.
Evidence: anchor and relative-link check "links ok"; stale-claim grep no matches (rc=1); `test_live_integration` Ran 52 tests OK; `verify.py --static-only` exit 0; ruff "All checks passed!"; pre_commit on the three files: whitespace Passed, other hooks Skipped (no matching files). Scratch `work/` removed; no processes left.
