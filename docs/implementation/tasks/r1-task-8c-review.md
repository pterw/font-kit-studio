### Spec Compliance
- PASS: Quickstart leads with the three npm paths, Python quickstart retitled "Try the demo, or work without Node" (README.md:38-71).
- PASS: Renames "Add Font Kit Studio to your app" and "Why Font Kit Studio"; every anchor resolves (script below). D040 applied to prose; only identifiers, file names and protocol names (`fontkit:change`, `fontkit:ack`) keep the bare word.
- PASS: Vite recipe uses `fontkitStudio()` from `fontkitstudio/vite`; Next.js leads with the proxy and keeps the script tag; "How these recipes were checked" updated; FAQ "no npm package" gone; Security paragraph added (README.md:595); Development rows, Fixtures paragraph, roadmap and extension lines done.
- PASS: Package README has the description, three commands, two flags, requirements, pointers, Sync note, D040 note, repo link; no badge, image or external load. CONTRIBUTING section has all five items.
- PASS: Owns only README.md, packages/fontkitstudio/README.md, CONTRIBUTING.md; LF endings (0 CR in all three).
- FAIL: Known limit "Saved settings follow the address" (README.md:512-ish, `- **Saved settings follow the address.**`) states the false thing the dispatch warned about, and omits the true limit. See Important 1.
- FAIL (minor): the Vite recipe dropped the old caveat about frameworks that do not call `transformIndexHtml` with no replacement. See Minor 2.

### Checks run
- Proxy-mode limit -> read `src/proxy.js`, `src/run-proxy.js`, `src/run-vite.js`, `src/studio-server.js`, `fontkit-studio.html:1248-1253` -> findings below.
  - The app is shown at `proxy.origin` = `http://127.0.0.1:<random port>` (`run-proxy.js:42-43`; `startProxy` default `host='127.0.0.1'`, `port=0`; there is no flag to set the proxy port). Usual address is typically `localhost:3000`. So app localStorage, sessionStorage, IndexedDB and service workers are per-origin and start empty, new each run.
  - Cookies: `proxy.js` forwards `Set-Cookie` unchanged (only `HOP_BY_HOP` headers dropped, `rewriteLocation` copies the rest); `Domain=` is not rewritten. Cookies key on host not port: a cookie set for `localhost` is not sent to `127.0.0.1`, and a cookie with `Domain=localhost` set through the proxy is rejected by the browser for `127.0.0.1`. If the user passes a `127.0.0.1` target, cookies are shared with the usual address.
  - Studio's own settings: `fontkit-studio.html` only uses `localStorage` through `readStore/writeStore` (free-fonts consent, kit ids). They sit at Studio's origin (`studio-server.js` `origin`, port 0 by default), in BOTH Vite and proxy mode, not at the proxy's address. `--studio-port` pins it; a busy port falls back and says "its saved settings stay with the old port" (`run-proxy.js:17-19`). The standalone plugin has no port option, so its settings never carry over.
  - Vite mode: app stays at Vite's own address (`resolvedUrls.local[0]`), so app storage is unaffected.
- Install lines -> `npm view fontkitstudio versions` -> registry has only `0.0.0-stage`, `0.0.0`; `latest` is `0.0.0`. `npx fontkitstudio` and `npm install --save-dev fontkitstudio` do not work today; they work from the 0.3.0 publish (plan 9b: owner tags after merge).
- Anchors and relative links -> python script slugging every heading in all three files, compared with every `](#...)`/`href="#..."` and every relative path -> no broken anchor, no missing file. Package README link `#if-studio-does-not-connect` targets a heading this patch adds on main (resolves after merge).
- CLI flags/help -> `node packages/fontkitstudio/bin/fontkitstudio.js --help` and `src/cli.js` -> usage, flags, exit 2 (usage, non-URL, non-local proxy target) and exit 1 (project errors) match; `Font Kit Studio · dev only` and `Open:` at `run-vite.js:66-67`, `run-proxy.js:61-62`; opens by default, `--no-open` suppresses.
- Requirements -> `package.json` engines `>=22.12`; `project.js:9` `[7, 8]`; `proxy.js:46-58` http-only, loopback. Docs say "localhost or 127.0.0.1"; code also accepts `[::1]` (understated, harmless).
- Messages -> `csp.js:6-9`, `vite-plugin.js:18-19`, `project.js:68`, `cli.js` no-Vite-project line -> each list item in "If Studio does not connect" matches its string.
- Plugin claims -> `vite-plugin.js`: `apply` serve only; build line text identical to README; host refusal covers `true` and any non-local host; standalone `printUrls` hook prints `Open:`; no browser open (README says "prints"); restart re-runs `configureServer` and starts a new Studio server (new port, new token); CSP check reads `server.headers` and meta only (`:60-61`, `:150-160`).
- Security paragraph -> `studio-server.js:80-95` (Host 421, Origin 403, token 403), `tests/test_node_studio_server.py` docstring (app sees no token, no Referer), `proxy.js` (one tag, only the bridge served, CSP header only read, upgrades piped) -> all true.
- Test rows -> read each module docstring; every `tests/test_*.py` is named in README or covered by `test_frontend_gate_*.py` (loop over tests/). Rows true, one imprecise (Minor 4).
- Fixtures/CI -> `fixtures/*/package.json`, `quality-gate.yml:236-283` -> Vite 7.3.6 and 8.3.2, Next 16.3.8, `npm ci` for four fixtures, `bootstrap5-static` has no install, `FKS_REQUIRE_FIXTURES=1`, `NEXT_TELEMETRY_DISABLED=1` in CI; `test_one_command_next.py:80` sets it too.
- CONTRIBUTING -> `test/package.test.js:11-16` (zero deps, all dependency fields), `scripts/bundle.js` (copies Studio and bridge, `checkVersions`) -> true.
- Sync under npx -> `fontkit-studio.html:3793` `NPX_SYNC_TEXT` (8b) -> README wording matches.
- Not run: test_live_integration, verify, ruff (report carries them; the diff is docs only).

### Strengths
- Every CLI, plugin, message and security claim I traced matches the code; the Studio-hint wording matches 8b's text at HEAD.
- Anchor renames done with no stale `#add-fontkit` link; "Do not paste every string" respected in the troubleshooting list.
- Package README is short and loads nothing.

### Issues
#### Critical
(none)

#### Important
1. **False known-limit line, and the real limit missing** (README.md, section "Known limits of the npm package", the "Saved settings follow the address" bullet). It says "In proxy mode Studio's saved settings sit with the proxy's address, not your app's usual one." That is wrong: Studio's settings sit at Studio's own address (`127.0.0.1:<Studio port>`), in both Vite and proxy mode; the proxy's address holds the APP. The line also tells users `--studio-port` fixes it, which is not true for the app's side (the proxy port is random every run and cannot be set). The report admits the claim "from the plan ... not re-derived in code". The brief said "verify each in the code" and "do not invent behaviour", so the implementer could have avoided it; I rate it an ordinary finding. If the owner reads the brief's line as requiring it, move it to Plan-mandated: the severity stays Important and the line must still change before merge. Replace the one bullet with two:
   - "**In proxy mode your app runs at the proxy's address.** The page loads from `http://127.0.0.1:<port>`, and the port changes each run. Its own localStorage, sessionStorage, IndexedDB and service workers are separate from the ones it has at its usual address, so they start empty. Cookies follow the host name, not the port: cookies the app set for `localhost` are not sent to `127.0.0.1`, and the proxy passes `Set-Cookie` through unchanged, so you may need to sign in again in the proxied page. Vite mode is not affected: the app stays at Vite's own address."
   - "**Studio's saved settings follow Studio's address.** Studio keeps its settings (free-font choice, kit IDs) with its own address, which changes with its port each run. `--studio-port <n>` keeps it on one port; if that port is busy, Studio picks another and says so. A standalone `fontkitStudio()` always picks a new port."
   Also check the package README flag row ("so its settings stay"): true for Studio's settings, acceptable once the README bullet is fixed.

#### Minor
2. **Dropped caveat, unverified** (README.md Vite section, the removed line "Frameworks that handle the HTML entry themselves (SvelteKit, for example) do not call `transformIndexHtml`"). The plugin adds the tag only in `transformIndexHtml` (`vite-plugin.js:130-150`); the new section header still reads "Vite (React, Vue, Svelte)" and the Quickstart says "In a Vite project". Only React fixtures are tested (the page itself says no test runs SvelteKit, Astro or Nuxt). CANNOT VERIFY FROM DIFF whether SvelteKit calls it. Either restore a one-line caveat ("tested on React fixtures; a framework that builds its own HTML may not call `transformIndexHtml`, so use the script tag or the proxy") or drop the Svelte word from what the plugin claims.
3. **"Node 22.12 or later is the only requirement"** (README.md FAQ "One command" bullet) is wrong for Vite mode: Vite 7 or 8 is also required, as the Quickstart says. Drop "only".
4. **Test row imprecise** (README.md `test_one_command_messages.py` row): "a page the proxy leaves as served" does not say what the test checks (the proxy adds exactly one script tag and leaves the body otherwise identical, before and after an edit). Reword.
5. **"Vite and Next.js recipes run in CI"** also covers the Next.js script-tag alternative, which no test runs. Say "the proxy recipe" or note the script-tag layout is illustrative.
6. **Busy-port fallback** is not mentioned beside `--studio-port` (`run-proxy.js:17-19`); covered by the text proposed in Issue 1.

### Plan-mandated (for the owner)
- None counted. See Important 1 for the disputed line.

### Release-window question (install lines)
- `npx fontkitstudio` and `npm install --save-dev fontkitstudio` fail until 0.3.0 is on npm (registry latest is `0.0.0`). The package README is published with 0.3.0, so it needs no note. For the repository README, which lands on `main` some time before the owner tags and approves `npm-release`, acceptable without a "from 0.3.0" banner only if the merge and tag go out together. Recommend one permanent-true line under the Quickstart npx block: "Needs fontkitstudio 0.3.0 or later." It needs no removal after publishing, so it cannot go stale (AP 15). Do not use "arrives in 0.3.0" wording: the grep guard in the brief forbids it and it would need removing. The controller can instead add a 9b "after merge" check that the tag and publish happen next.

### Assessment
**Task quality:** Needs fixes
**Reasoning:** Nearly every claim is backed by the code, and anchors, D040 and the test rows hold. One user-facing known-limit line is false (Studio's settings are not at the proxy's address) and the real proxy-mode limit (the app's own storage and cookies at `127.0.0.1:<random port>`) is not stated, so the page cannot ship as written.
