# Font Kit Studio v0.1.1

> **Single-file typography studio, flow composer, and zero-hook live visual editor for modern web applications.**

Font Kit Studio is a self-contained browser environment for evaluating font pairings, composing typography with PNG/SVG brand assets and responsive rules, and **live visual editing of external web applications in real time**. 

The application runs entirely in a single HTML file (`font_kit_studio_v0.1.1.html`) with zero npm build steps or server dependencies. Adobe Typekit loading is supported on demand with your own kit ID.

---

## ⚡ Key Capabilities

- **Flow Composer**: Multi-slot typography layout engine with responsive row wrapping, PNG/SVG brand mark placement, horizontal rules, and dynamic spacer controls.
- **Zero-Hook Universal Design Bridge**: Drop `fontkit-bridge.js` into **any** web application with a single script tag. No React/Vue hooks, no npm wrappers, no component rewrites, and no required `data-` attributes.
- **Bi-Directional Live Sync**:
  - Click any element in your live web app to select and inspect it in Font Kit Studio.
  - Adjust font family, font size, tracking, line height, or color in Studio to stream live CSS updates (`!important` overrides) directly into the target app.
- **Theater Fullscreen Mode**: Expand the Composer to an immersive `100vw × 100vh` workspace with high z-index and instant `Escape` key toggle.
- **Responsive Device Breakpoints**: Test your live typography across standardized viewports:
  - 📱 **Mobile (390px)**: iPhone / compact mobile audit.
  - 💻 **Laptop (1024px)**: Tablet and laptop viewport testing.
  - 🖥️ **Desktop (1440px)**: High-resolution desktop canvas.
  - ⛶ **Fluid (100%)**: Full-width fluid testing.
- **Content Protection & Restoration**: Prevents preset specimen text from overwriting live application copy, with a dedicated `↻ Restore Page Text` button to revert copy changes while retaining typography styling.
- **Anti-Recursion Defense**: Automatic detection of nested iframes prevents infinite iframe rendering loops when hosting Font Kit Studio inside a parent application that is itself connected to Studio.

---

## 🚀 Quickstart

### 1. Standalone Font Studio
Open `font_kit_studio_v0.1.1.html` directly in any modern browser (`file://` or `http://localhost:8000/font-kit-studio/font_kit_studio_v0.1.1.html`).

1. Select **Flow Composer** at the top.
2. Select any preset (e.g. *Asteria Starlight*, *Editorial — Image + Body Row*).
3. Adjust typography, font sizes, tracking, or drop in your local SVG/PNG logos.

---

### 2. Live Visual Web App Integration (Zero Hooks)

You can live-edit **any** web app (Vanilla HTML, React, Vue, Next.js, Svelte, Astro, Tailwind, DaisyUI) in 30 seconds:

#### Step 1: Add the Bridge Script
Add `fontkit-bridge.js` to your web app's HTML (or inject via `<head>`):

```html
<!-- In your web application's index.html -->
<script src="path/to/fontkit-bridge.js"></script>
```

*Or via dynamic injection / CDN:*
```html
<script src="https://cdn.jsdelivr.net/gh/pterw/font-kit-studio@main/fontkit-bridge.js"></script>
```

#### Step 2: Connect in Font Kit Studio
1. In Font Kit Studio, switch to **Flow Composer**.
2. In the **Target Application Bridge** bar, enter your app's URL (e.g. `http://localhost:3000/` or `http://localhost:8000/`).
3. Click **Connect Target**.
4. The status badge will show `Connected (XX targets)`. You are now in live visual editing mode!
5. Hover over any heading, paragraph, button, or logo on your page to see the visual highlight box, then click to edit its typography, size, and styling directly from the Studio sliders.

---

## 🔌 Integration Patterns

### A. Zero-Configuration Auto-Discovery (Default)
When `fontkit-bridge.js` is loaded without arguments, it automatically scans and instruments all semantic elements:
- Headings: `<h1>` through `<h6>` &rarr; mapped to `display`, `title`, `subhead`
- Editorial & Lead: `<header p>`, `<main p>`, `<article p>` &rarr; mapped to `editorial`, `body`
- Interactive: `<button>`, `.btn`, `<a>` &rarr; mapped to `button`
- Brand & Graphics: `<img>`, `<svg>`, `<picture>`, `.brand`, `.mark` &rarr; mapped to `image`
- Badges & Metrics: `.badge`, `.chip`, `.stat` &rarr; mapped to `metadata`

**Dynamic SPAs (React / Vue / Next.js)**: A built-in `MutationObserver` automatically detects elements added dynamically via client-side routing or state changes.

---

### B. Bookmarklet / DevTools Injection (Edit ANY Live Site)
To live-edit a remote staging site, production app, or third-party page where you do not want to alter source code:

1. Create a browser bookmark with this URL:
```javascript
javascript:(function(){if(window.__fontkitBridge)return;var s=document.createElement('script');s.src='http://localhost:8000/fontkit-bridge.js';document.head.appendChild(s);})();
```
2. Navigate to any website.
3. Click the bookmarklet (or paste into Chrome DevTools Console).
4. In Font Kit Studio, enter the website's URL and click **Connect Target**.

---

### C. Explicit Data Attributes (Optional Power-User Mode)
For precise control over element names and roles in team design systems:

```html
<!-- Explicit role, ID, and friendly label -->
<h1 data-design-id="hero.title" data-design-role="display" data-design-name="Hero Headline">
  The Future of Medicine
</h1>

<p data-design-id="hero.lead" data-design-role="editorial" data-design-name="Lead Editorial Copy">
  Precision insights from genome to phenome.
</p>

<div data-design-id="brand.logo" data-design-role="image" data-design-name="Brand Logo SVG">
  <svg>...</svg>
</div>
```

---

## 🛠️ Architecture: Design Bridge Protocol v1

Communication between Font Kit Studio and the target application is orchestrated through the asynchronous **Design Bridge Protocol v1** over `window.postMessage`:

```text
+----------------------------+                     +----------------------------+
|     Font Kit Studio        |                     |     Target Web App         |
|  (Host / Visual Editor)    |                     |   (Client / fontkit-bridge)|
+----------------------------+                     +----------------------------+
              |                                                   |
              | <---- design:bridge-ready (Target Loaded) ------- |
              | ----- design:hello (Handshake Version 1) -------> |
              | <---- design:ready (Manifest of 40+ Targets) ---- |
              |                                                   |
              | ====== Real-Time Bi-Directional Editing ======== |
              |                                                   |
              | <---- design:select-slot (Element Clicked) ------ |
              | ----- design:apply (Typography Overrides) ------> |
              | <---- design:applied (Revision Acknowledged) ---- |
              | ----- design:restore-text (Restore Page Copy) --> |
```

### Protocol Message Types

| Message `type` | Sender | Description |
|---|---|---|
| `design:bridge-ready` | Bridge | Emitted when `fontkit-bridge.js` mounts in the target window. |
| `design:hello` | Studio | Acknowledges bridge and establishes protocol session. |
| `design:ready` | Bridge | Sends complete manifest of all detected targets and computed CSS. |
| `design:select-slot` | Bridge | Notifies Studio that the user clicked a specific element on the live page. |
| `design:apply` | Studio | Streams updated styles (font-family, size, weight, line-height, color) to target. |
| `design:applied` | Bridge | Confirms styling applied with incremental revision counter. |
| `design:restore-text` | Studio | Signals bridge to restore original DOM text while preserving typography styles. |

---

## 💻 Fullscreen Theater & Keyboard Controls

| Control | Shortcut / Trigger | Action |
|---|---|---|
| `⛶ Fullscreen` | Button on toolbar | Toggles full-window theater mode (`100vw × 100vh`, z-index 999999). |
| `✕ Exit` | `Escape` key | Instantly exits theater mode and restores normal studio layout. |
| `📱 390` | Button on toolbar | Constrains target iframe to 390px (mobile portrait). |
| `💻 1024` | Button on toolbar | Constrains target iframe to 1024px (tablet / laptop). |
| `🖥️ 1440` | Button on toolbar | Constrains target iframe to 1440px (desktop canvas). |
| `⛶ Fluid` | Button on toolbar | Restores 100% fluid responsive width. |
| `↻ Restore Page Text` | Button on toolbar | Reverts altered text copy back to original live web app content. |

---

## 🧪 Development & Verification

Font Kit Studio maintains strict offline self-containment, ID uniqueness, and zero runtime dependencies. Verification is automated via Python and Playwright.

### Prerequisites
- Python 3.10+
- Node.js (for syntax validation via `node --check`)

### Install Dependencies
```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium firefox
```

### Run Static & Provenance Verification
```bash
python scripts/verify.py --static-only
```
Checks:
- Static HTML ID uniqueness across all elements.
- JavaScript syntax in executable inline blocks.
- SHA-256 provenance hashes against baseline git tags.

### Run Full Test Suite (Browser & Integration Tests)
```bash
python -m unittest discover -s tests -v
```
Runs all 20 Playwright browser test suites across:
- `test_task1_single_file_runtime_and_dom`: Static ID and canvas DOM integrity.
- `test_task2_composition_engine_and_crud`: Slot addition, reordering, and removal.
- `test_task3_preset_system_and_offline_data`: Offline presets and responsive row collapse.
- `test_task4_export_and_import_mechanics`: JSON export, import, and round-tripping.
- `test_task5_offline_layouts_and_dynamic_ids`: Mobile 390px layout bounds and dynamic ID handling.

---

## 📄 Provenance & Heritage

The original supplied artifact is preserved at Git tag `supplied-v0.1.1`. Implementation and protocol extensions are maintained on `main`.

- [Design Bridge Protocol v1 Specification](font-kit-studio-v0.2.0-design-bridge-protocol-v1.md)
- [Original Design Document](docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows-design.md)
- [Source Provenance Ledger](docs/reference/SOURCES.json)

---

## ⚖️ License

MIT License. Designed and maintained for open-source visual web typography.
