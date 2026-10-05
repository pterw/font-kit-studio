### Re-review of Important 1 and Minors 2-6 (8c fix round 1)

### Spec Compliance
- PASS Important 1: the false "Saved settings follow the address" bullet is replaced by two bullets (README.md:516-517), both true at HEAD.
  - Bullet 1, app at the proxy's address: `proxy.origin` is `http://127.0.0.1:<port>` (`startProxy` defaults `host='127.0.0.1'`, `port=0`; `run-proxy.js` passes neither; no CLI flag for it), so "the port changes each run; no flag sets it" holds. Per-origin storage and service workers start empty: correct. Cookies follow the host name: `localhost` cookies are not sent to `127.0.0.1`: correct. `Set-Cookie` passes through unchanged (`proxy.js` drops only `HOP_BY_HOP`; `rewriteLocation` copies the rest): correct. Vite mode unaffected (app stays at `resolvedUrls.local[0]`): correct. This is the true limit the dispatch described.
  - Bullet 2, Studio's settings: `fontkit-studio.html` writes only free-fonts consent and kit IDs to localStorage at Studio's own origin; port is random unless `--studio-port`; busy port falls back and writes "port N is busy, so Studio uses port M ..." to the terminal (`run-proxy.js:14-19`). Matches "picks another and says so on the terminal".
- PASS Minor 2 (0.3.0 note): README.md:44 "The command needs `fontkitstudio` 0.3.0 or later." Permanent-true, needs no later removal; matches my recommendation. Package README unchanged, correct (it ships with 0.3.0).
- PASS Minor 3 (transformIndexHtml caveat restored, README.md:359): the plugin does add its tag only in `transformIndexHtml` (`vite-plugin.js`), and the text sends users to the proxy command. The statement that SvelteKit does not call it is the original README's own claim, restored unchanged; I could not verify it against SvelteKit source here and did not re-derive it.
- PASS Minor 4 (FAQ requirement, README.md:309): "Node 22.12 or later, and in a Vite project the project's own Vite 7 or 8" matches `engines` and `project.js:9`.
- PASS Minor 5 (`test_one_command_messages` row, README.md:651): the three clauses match the module docstring (network-open Vite refused, one plain line, exit 1; Bootstrap page gets exactly one tag and an identical body before and after a live edit; blocking CSP reported once, Studio does not connect).
- PASS Minor 6 (CI claim, README.md:335): "plugin and the command on Vite 7 and 8 fixtures, proxy command in front of a Next.js 16 fixture" matches `quality-gate.yml:236-283` and the fixtures; the Next.js script-tag layout is now listed as illustrative with Astro, SvelteKit and Nuxt.
- PASS: only README.md changed (the report says so; the other two files' staged content is as reviewed in round 0). No new links or anchors added by this round.

### Checks run
- Proxy-mode bullets -> re-read `proxy.js`, `run-proxy.js`, `run-vite.js` at HEAD of the main checkout -> as above.
- Strings -> grep of the staged README for each fixed line -> present at the lines cited.
- Not run: test_live_integration, ruff, verify (docs-only change; the report carries them).

### Issues
#### Critical
(none)

#### Important
(none)

#### Minor
1. README.md:516 "The command offers no way around this" is slightly absolute for cookies: a target given as `http://127.0.0.1:<port>` shares cookies with the usual 127.0.0.1 address, because cookies ignore ports. True for the app's storage (no way around), not for cookies. Optional: "Pass the address as `127.0.0.1` to share cookies; storage still starts empty."
2. README.md:359: the restored caveat is under the plugin recipe, but `npx fontkitstudio` in a Vite project uses the same plugin and has the same limit. Optional: "so the plugin and the command's Vite mode do not inject there".

### Plan-mandated (for the owner)
- None.

### Assessment
**Task quality:** Approved
**Reasoning:** The false settings line is replaced by two accurate bullets that match the code, and all five Minors are fixed and verified; two optional Minor wording points remain.
