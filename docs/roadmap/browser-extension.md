# Roadmap: a simpler browser extension

Status: **idea, not implemented.** Nothing in this repository builds an extension. This note
says what a first version could be, so the README can point to something honest.

## Why

Today fontkit needs one script tag in the app you want to edit (or a bookmarklet run from a
pop-out window). That is fine for your own project and awkward for everything else: a staging
site you cannot change, a teammate's branch, or a quick look at a page you do not own.

An extension could remove the script tag. You would click the toolbar button on the page you
want to edit, and the extension would load the bridge into that tab for you.

## Goals

- No script tag in the app. Click the button, edit the open tab.
- Studio still runs outside the page being edited. A side panel or popup replaces the
  separate Studio window.
- Same editing model as today: click an element, change typography, see the CSS.
- Nothing is sent to a server. Everything stays in the browser.

## Non-goals for the first version

- **No sync to a file.** Copy and Download only. Writing files needs the dev server, and the
  extension should not talk to one.
- **No arranging or moving elements.** Moves need the guard checks and the HTML output to be
  right first; the typography-only version is smaller and safer.
- No remote scripts. The bridge ships inside the extension package.
- No Firefox build in the first pass.

## Sketch (Manifest V3, Chrome)

| Piece | Idea |
|---|---|
| Permissions | `activeTab`, `scripting` and `sidePanel` (`chrome.sidePanel` needs its own permission). `activeTab` is a temporary grant that covers only the tab the user clicked on. |
| Injection | `chrome.scripting.executeScript({ target: { tabId }, files: ["fontkit-bridge.js"], world: "MAIN" })`, which needs Chrome 111 or newer. The main world is needed because the bridge reads the page's own computed styles and looks for framework markers on elements. |
| Panel | `chrome.sidePanel` with a cut-down Studio: the Live Target inspector and the CSS tab with Copy. A popup is the fallback if a side panel is unavailable. Studio cannot be reused as it is: it is one HTML file with a large inline script, and Manifest V3 extension pages forbid inline scripts under the default content security policy. The panel needs its script moved into a separate file. |
| Transport | See "Open questions": the current bridge only accepts a Studio that is the page's parent or opener. |
| Cleanup | Closing the panel or navigating away drops the session, as the bridge already does when its Studio goes away. |

## Security

- **No `<all_urls>` by default.** `activeTab` only. A "always allow on this site" option, if
  added later, uses optional host permissions that the user grants one origin at a time.
- **Origin pinning stays.** The panel talks to one tab and one origin, and the bridge keeps
  rejecting messages from anything else.
- **No remote code.** No `eval`, no scripts fetched at run time, a strict extension CSP.
- **No page data leaves the browser.** The extension makes no network requests of its own, apart from the Google Fonts stylesheets the user chooses to load (which tell Google the font names and the user's IP address).
- Edits are never written into the page's source. The output is CSS you copy.

## Open questions

1. **Transport.** The bridge trusts a `design:hello` only from `window.parent` or
   `window.opener`. A side panel is neither. Options: add an extension channel to the bridge
   (`chrome.runtime` messages relayed by a small content script), or have the panel open the
   page in a window it controls. Either one changes the trust model and needs its own
   hostile-input tests.
2. **Page CSP.** Does a strict `script-src` on the page affect a file injected with
   `executeScript` in the main world? This needs testing on real sites before we promise
   "works on any page".
3. **Pages the extension cannot touch.** Chrome's own pages, the web store and some PDF
   viewers block injection. The panel needs a clear message instead of failing silently.
4. **Frames.** Should the bridge run in every frame, or only the top document? The current
   bridge assumes one document.
5. **How much of Studio fits in a side panel?** The full Studio is one large HTML file with
   an inline script, which an MV3 extension page may not run. It cannot be reused unchanged.
   A cut-down inspector with its script in a separate file is the likely shape.
6. **Store review.** An extension that edits arbitrary pages needs a clear privacy statement
   and a minimal permission list.
7. **Firefox.** Manifest V3 differs there (for example the side panel API). Decide after the
   Chrome version exists.

## What would make us build it

A handful of people who want to try fontkit on a site they cannot add a script tag to, and
an answer to the transport question that does not weaken the bridge's origin checks.
