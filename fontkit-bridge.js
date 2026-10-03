/**
 * Font Kit Studio — Design Bridge Protocol v1 Target SDK
 * =======================================================
 * Standalone, zero-dependency bridge runtime for code-owned web applications.
 * Drop it into any web project with a <script> tag (or require it via CommonJS).
 *
 * What it does once a Studio has said hello:
 *  - Reports editable targets (author `data-design-id` elements plus
 *    auto-discovered semantic elements) with their computed typography.
 *  - Validates, canonicalizes and atomically applies targeted patches as
 *    `!important` inline overrides, and can remove/reset them exactly.
 *  - Reports hover, selection and selected-target bounds so the Studio can
 *    draw its own overlays (no editor chrome inside the target by default).
 *  - Keeps a ChangeLedger (CSS declarations, text changes, cleaned HTML,
 *    structural moves, injected font stylesheets) in every `design:ready` and
 *    `design:applied` reply.
 *  - Arranges: `design:move` reorders a target among its siblings or into
 *    another container (DOM move with guards, or a CSS `order` strategy).
 *  - Reports runtime errors the app throws within 1 s of a change as
 *    `design:warning`, and re-applies overrides when a re-render (SPA/HMR)
 *    replaces an element that has an author `data-design-id`.
 *
 * Before any hello the bridge is passive: it does not touch the DOM, intercept
 * clicks, or emit hover/selection, so the instrumented app works standalone.
 *
 * Security (Spec §15): `design:hello` is accepted only from window.parent or
 * window.opener and, when configured, only from `allowedOrigins` (option or
 * `data-allowed-origins="a b"` on the script tag; compared without case, as
 * browsers report origins in lower case). A hello pins the Studio's
 * window, origin and sessionId; every later control message must match all
 * three or it is ignored. Replies are posted to the pinned origin. If a
 * pop-out Studio (window.opener) closes, the session is dropped.
 *
 * Initialisation (one instance per page, kept in window.__fontkitBridge):
 *  - Default: the script auto-initialises (at DOMContentLoaded if the document
 *    is still loading) with window.FONTKIT_BRIDGE_OPTIONS, if that object is set.
 *  - `<script src="fontkit-bridge.js" data-auto-init="false">` disables
 *    auto-init; call initFontKitBridge(options) or new FontKitBridge(options).
 *  - A constructed instance claims window.__fontkitBridge when it is empty, so
 *    a later auto-init reuses it. initFontKitBridge(options) after an instance
 *    exists returns that instance; like the constructor below, it applies an
 *    `allowedOrigins` list that narrows the running policy (never one that widens
 *    it) and warns that the other options were ignored.
 *  - Loading the script more than once keeps the first instance and the first
 *    class (window.FontKitBridge is never replaced).
 *  - `new FontKitBridge(...)` again (HMR) behaves by state. Once a Studio has talked to the
 *    existing bridge, the constructor returns that bridge; it is never replaced and its
 *    options are not merged, except `allowedOrigins`: a list that narrows the running policy
 *    (an open bridge allows everything) is applied, one that would widen it ("*", an origin
 *    not yet allowed, a non-list) is ignored, and a pinned Studio at an origin that is no
 *    longer allowed loses its session. One console warning says what was applied and what
 *    was ignored. A bridge that no Studio has talked to yet, or one that was disposed, is
 *    replaced by the new instance, so changed options apply.
 *  - Subclasses: `new Sub()` while a connected bridge exists returns the running instance
 *    (whatever `super()` returns is `this`), so the rest of the subclass constructor runs
 *    against that instance and `instanceof Sub` is false.
 *  Options: allowedOrigins, autoDiscover, autoDiscoverSemantic,
 *  enableClickToSelect, enableHighlightOverlay (default false), tokens, onApplied.
 *  The Studio can also switch an outline overlay on at runtime with
 *  `design:mode {overlay: true}` (pop-out windows).
 *
 * Legacy image slots accept only PNG/SVG data URLs and always render them
 * through an <img>; SVG markup is never inserted into the page.
 *
 * Specification: font-kit-studio-v0.2.0-design-bridge-protocol-v1.md, and the
 * binding "Protocol contract" in docs/plans/2026-10-02-v0.2.0-live-preview-code-sync.md.
 */

(function (global) {
  'use strict';

  // document.currentScript is only set while this file is first executing.
  const currentScript = typeof document !== 'undefined' ? document.currentScript : null;

  const PROTOCOL_VERSION = 1;
  const DISCOVERY_DEBOUNCE_MS = 120;
  const DISCOVERY_MAX_WAIT_MS = 1000;
  const MAX_ID_LENGTH = 300;
  const OVERLAY_SELECTOR = '#fontkit-bridge-overlay, #fontkit-bridge-hover';
  const PLACED_ASSET_CLASS = 'fontkit-placed-asset';
  const EXCLUDED_SELECTOR = `${OVERLAY_SELECTOR}, .${PLACED_ASSET_CLASS}, script, style, noscript, template, head`;
  const MAX_ASSET_URL_LENGTH = 8 * 1024 * 1024;
  const WARNING_WINDOW_MS = 1000; // runtime errors after an applied update/move become warnings
  const WARNING_MAX_LENGTH = 300;
  const REAPPLY_DEBOUNCE_MS = 30; // re-render replaced an element that carries overrides
  const REAPPLY_WINDOW_MS = 2000;
  const REAPPLY_MAX = 5; // per target within the window: loop guard
  const LOST_MAX = 100;
  const LOST_TTL_MS = 10000; // how long a removed element's overrides wait for a replacement
  const OPENER_POLL_MS = 500;
  const CONTAINER_NAME_MAX = 40;
  // Content-model guard: block-level elements may not be placed in these parents.
  const BLOCK_ELEMENTS = new Set(['div', 'p', 'section', 'article', 'aside', 'header', 'footer', 'nav', 'ul', 'ol',
    'table', 'form', 'figure', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'details']);
  const PHRASING_PARENTS = new Set(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'a', 'button', 'label', 'summary']);
  // Mutation-triggered rediscovery backs off when it runs more than this often.
  const STORM_RUNS = 10;
  const STORM_WINDOW_MS = 2000;
  const STORM_BACKOFF_START_MS = 250;
  const STORM_BACKOFF_MAX_MS = 8000;
  const DATA_URL_ABBREVIATE_OVER = 256;
  const URL_ATTRIBUTES = new Set(['src', 'href', 'poster', 'action', 'data', 'xlink:href']);
  // Element children that are not part of an arrangement.
  const NON_ARRANGEABLE = 'script, style, template, link, meta, noscript';
  const FORM_CONTROLS = 'input, select, textarea, button, fieldset, output';
  const LABELABLE = 'input, select, textarea, button, meter, output, progress';
  // Cannot receive children (void or replaced) or must not: rejected as move containers.
  const NO_CHILDREN = new Set(['area', 'audio', 'base', 'br', 'canvas', 'col', 'embed', 'head', 'hr', 'html',
    'iframe', 'img', 'input', 'link', 'math', 'meta', 'noscript', 'object', 'param', 'script', 'select',
    'source', 'style', 'svg', 'template', 'textarea', 'title', 'track', 'video', 'wbr']);

  // Zero-hook auto-discovery: semantic elements instrumented without markup.
  const SEMANTIC_SELECTORS = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'header p', 'main p', 'article p', 'section p',
    'header a', 'nav a', 'button', '.btn',
    'img', 'svg', 'picture',
    '[class*="title"]', '[class*="heading"]', '[class*="brand"]', '[class*="wordmark"]', '[class*="badge"]', '[class*="stat"]'
  ];

  // Root custom properties always reported when set (in addition to any
  // declared on :root/html in same-origin stylesheets).
  const LEGACY_TOKEN_KEYS = [
    '--font-sans', '--font-serif', '--font-mono', '--font-display',
    '--editorial-size', '--mono-spacing', '--brand-canvas',
    '--accent-cyan', '--accent-emerald', '--accent-purple'
  ];

  const HEX_COLOR = /^#(?:[0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$/i;
  const FUNCTION_COLOR = /^(?:rgba?|hsla?)\([0-9.%,/ ]*\)$/i;
  // Characters/functions never allowed in free-form CSS strings (font stacks, token values).
  const UNSAFE_CSS_STRING = /[;{}<>\\]|url\(|expression\(/i;
  const TOKEN_NAME = /^--[a-z0-9-]{1,120}$/; // Studio validates imported tokens with the same rule
  const BASE64 = /^[A-Za-z0-9+/]+={0,2}$/;
  const SVG_DATA_URL = /^data:image\/svg\+xml(?:;charset=[A-Za-z0-9_-]+)?(;base64)?,([\s\S]*)$/;
  const DATA_URL_IN_ATTRIBUTE = /data:[a-z0-9.+\-/]*(?:;[a-z0-9=._+\-]+)*,[^\s"')]+/gi;
  const TYPEKIT_URL = /^https:\/\/use\.typekit\.net\/[A-Za-z0-9]{6,10}\.css$/;
  const GOOGLE_FONTS_PREFIX = 'https://fonts.googleapis.com/css2?';
  // Percent-escapes are limited to space, plus, comma, colon, semicolon and at.
  const GOOGLE_FONTS_VALUE = /^(?:[A-Za-z0-9+:;,@.\-_~]|%(?:20|2[Bb]|2[Cc]|3[Aa]|3[Bb]|40))+$/;
  const GOOGLE_FONTS_DISPLAY = ['auto', 'block', 'swap', 'fallback', 'optional'];
  const MAX_FONT_URL_LENGTH = 2000;
  const MAX_FONT_FAMILIES = 8;
  const MAX_COMPOSITION_SHEETS = 16;

  // ---------------------------------------------------------------------------
  // Targeted patch rules (binding contract table).
  // canonical(value, record) returns the canonical value, or undefined when the
  // value is not acceptable. toCss(canonical) gives the inline CSS value.
  // `group` is the TargetManifest.editable flag that must be true.
  // ---------------------------------------------------------------------------

  function round(value, places) {
    const factor = 10 ** places;
    return Math.round(value * factor) / factor;
  }

  function numberIn(value, min, max) {
    return typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max;
  }

  function cssSupports(property, value) {
    if (typeof CSS === 'undefined' || typeof CSS.supports !== 'function') return true;
    return CSS.supports(property, value);
  }

  // Trimmed string of 1–300 chars without ; { } < > \ url( expression(, else undefined.
  function safeCssString(value) {
    if (typeof value !== 'string') return undefined;
    const trimmed = value.trim();
    if (trimmed.length < 1 || trimmed.length > 300 || UNSAFE_CSS_STRING.test(trimmed)) return undefined;
    return trimmed;
  }

  // Asset placement accepts only PNG (base64) and SVG (base64 or URL-encoded)
  // data URLs. SVG is only ever rendered through <img>, where it cannot run
  // script; parsed SVG markup is never inserted into the live document.
  function safeAssetUrl(value) {
    if (typeof value !== 'string' || value.length > MAX_ASSET_URL_LENGTH) return null;
    const png = 'data:image/png;base64,';
    if (value.startsWith(png)) return BASE64.test(value.slice(png.length)) ? value : null;
    const svg = SVG_DATA_URL.exec(value);
    if (!svg) return null;
    return !svg[1] || BASE64.test(svg[2]) ? value : null;
  }

  // Font stylesheet URLs: Google Fonts css2 (family/display/text only) or a Typekit
  // kit. Strict string matching, no URL parsing, so nothing is normalised away.
  function safeFontStylesheet(value) {
    if (typeof value !== 'string' || value.length === 0 || value.length > MAX_FONT_URL_LENGTH) return undefined;
    if (TYPEKIT_URL.test(value)) return value;
    if (!value.startsWith(GOOGLE_FONTS_PREFIX)) return undefined;
    const params = value.slice(GOOGLE_FONTS_PREFIX.length).split('&');
    let families = 0;
    let display = 0;
    let text = 0;
    for (const param of params) {
      const at = param.indexOf('=');
      if (at < 1) return undefined;
      const key = param.slice(0, at);
      const val = param.slice(at + 1);
      if (key === 'family') {
        families += 1;
        if (!GOOGLE_FONTS_VALUE.test(val)) return undefined;
      } else if (key === 'display') {
        display += 1;
        if (!GOOGLE_FONTS_DISPLAY.includes(val)) return undefined;
      } else if (key === 'text') {
        text += 1;
        if (!GOOGLE_FONTS_VALUE.test(val) || val.length > 600) return undefined;
      } else {
        return undefined;
      }
    }
    return families >= 1 && families <= MAX_FONT_FAMILIES && display <= 1 && text <= 1 ? value : undefined;
  }

  function nearest(allowed, value) {
    // Ties resolve to the lower weight (allowed is sorted ascending).
    let best = allowed[0];
    for (const candidate of allowed) {
      if (Math.abs(candidate - value) < Math.abs(best - value)) best = candidate;
    }
    return best;
  }

  const PATCH_RULES = {
    fontFamily: {
      group: 'typography',
      css: 'font-family',
      canonical(value) {
        const trimmed = safeCssString(value);
        return trimmed !== undefined && cssSupports('font-family', trimmed) ? trimmed : undefined;
      },
      toCss: (value) => value
    },
    fontSize: {
      group: 'typography',
      css: 'font-size',
      canonical: (value) => (numberIn(value, 4, 400) ? round(value, 2) : undefined),
      toCss: (value) => `${value}px`
    },
    fontWeight: {
      group: 'typography',
      css: 'font-weight',
      canonical(value, record) {
        if (!numberIn(value, 1, 1000)) return undefined;
        const weights = record && record.fontWeights;
        return weights && weights.length ? nearest(weights, value) : Math.round(value);
      },
      toCss: (value) => String(value)
    },
    lineHeight: {
      group: 'typography',
      css: 'line-height',
      canonical: (value) => (numberIn(value, 0.5, 5) ? round(value, 3) : undefined),
      toCss: (value) => String(value)
    },
    letterSpacing: {
      group: 'typography',
      css: 'letter-spacing',
      canonical: (value) => (numberIn(value, -0.5, 2) ? round(value, 4) : undefined),
      toCss: (value) => `${value}em`
    },
    color: {
      group: 'color',
      css: 'color',
      canonical(value) {
        if (typeof value !== 'string') return undefined;
        if (!HEX_COLOR.test(value) && !FUNCTION_COLOR.test(value)) return undefined;
        const lower = value.toLowerCase();
        return cssSupports('color', lower) ? lower : undefined;
      },
      toCss: (value) => value
    },
    textAlign: {
      group: 'alignment',
      css: 'text-align',
      canonical: (value) => (['left', 'center', 'right', 'justify', 'start', 'end'].includes(value) ? value : undefined),
      toCss: (value) => value
    },
    textTransform: {
      group: 'typography',
      css: 'text-transform',
      canonical: (value) => (['none', 'uppercase', 'lowercase', 'capitalize'].includes(value) ? value : undefined),
      toCss: (value) => value
    },
    text: {
      group: 'text',
      css: null,
      canonical: (value) => (typeof value === 'string' && value.length <= 5000 ? value : undefined),
      toCss: null
    },
    // Not an inline style: injects a <link data-fontkit-font> (see setFontSheet).
    fontStylesheet: {
      group: null,
      css: null,
      canonical: safeFontStylesheet,
      toCss: null
    }
  };

  // ---------------------------------------------------------------------------
  // Small DOM helpers
  // ---------------------------------------------------------------------------

  function isPlainObject(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
  }

  function isNonEmptyString(value, max = MAX_ID_LENGTH) {
    return typeof value === 'string' && value.length > 0 && value.length <= max;
  }

  function cssEscape(value) {
    if (typeof CSS !== 'undefined' && typeof CSS.escape === 'function') return CSS.escape(value);
    return String(value).replace(/[^a-zA-Z0-9_\u00A0-\uFFFF-]/g, (ch) => `\\${ch}`);
  }

  // `[data-design-id="..."]` for any id. Inside the quotes `"` and `\` get a backslash, and every character that could
  // end the string, the rule or a <style> element (`; { } < > ( ) / * !` and control characters) is written as a CSS
  // hex escape (`\3b `), so the selector text never holds a raw character that is special in CSS or HTML.
  function designIdSelector(id) {
    const value = String(id).replace(/["\\]|[\u0000-\u001f\u007f;{}<>()/*!]/g,
      (ch) => (ch === '"' || ch === '\\' ? `\\${ch}` : `\\${ch.codePointAt(0).toString(16)} `));
    return `[data-design-id="${value}"]`;
  }

  function collapse(text) {
    return String(text || '').replace(/\s+/g, ' ').trim();
  }

  function rectOf(el) {
    const r = el.getBoundingClientRect();
    return { x: r.left, y: r.top, width: r.width, height: r.height };
  }

  function sameRect(a, b) {
    return !!a && !!b && a.x === b.x && a.y === b.y && a.width === b.width && a.height === b.height;
  }

  // First direct child text node with visible characters (mixed-content text slot).
  function firstTextNode(el) {
    for (const node of el.childNodes) {
      if (node.nodeType === 3 && node.data.trim().length > 0) return node;
    }
    return null;
  }

  function parseWeights(raw) {
    if (!raw) return null;
    const weights = raw.split(/[\s,]+/)
      .map((part) => Number(part))
      .filter((n) => Number.isInteger(n) && n >= 1 && n <= 1000);
    const unique = Array.from(new Set(weights)).sort((a, b) => a - b);
    return unique.length ? unique : null;
  }

  // allowedOrigins: option (array or space/comma separated string) or the
  // script tag's data-allowed-origins. null means "any origin, pinned on hello".
  function resolveAllowedOrigins(option) {
    let list = option;
    if (list == null && typeof document !== 'undefined') {
      const script = currentScript || document.querySelector('script[src*="fontkit-bridge"][data-allowed-origins]');
      if (script && script.hasAttribute('data-allowed-origins')) list = script.getAttribute('data-allowed-origins');
    }
    if (list == null) return null;
    list = parseOriginList(list);
    if (list !== null && !list.length) console.warn('[FontKitBridge] allowedOrigins is empty; no Studio can connect.');
    return list;
  }

  // A list of origins (array or space/comma separated string) without trailing slashes, in lower case (browsers
  // report an origin's scheme and host in lower case, so `HTTP://Studio.Test` must still match); null means "any
  // origin" (a `*` in the list).
  function parseOriginList(list) {
    if (typeof list === 'string') list = list.split(/[\s,]+/);
    list = Array.from(list).map((origin) => String(origin).trim().replace(/\/+$/, '').toLowerCase()).filter(Boolean);
    return list.includes('*') ? null : list;
  }

  // Composition `fontStylesheets`: a list of up to MAX_COMPOSITION_SHEETS stylesheet URLs, each as strict as the
  // per-target `fontStylesheet` key. Returns { sheets } (unique, in order) or { requested } for the first bad value.
  function checkCompositionSheets(value) {
    if (!Array.isArray(value)) return { requested: typeof value === 'string' ? value.slice(0, 200) : `a ${value === null ? 'null' : typeof value} value` };
    if (value.length > MAX_COMPOSITION_SHEETS) return { requested: `${value.length} stylesheets` };
    const sheets = [];
    for (const url of value) {
      if (safeFontStylesheet(url) === undefined) return { requested: typeof url === 'string' ? url.slice(0, 200) : `a ${url === null ? 'null' : typeof url} value` };
      if (!sheets.includes(url)) sheets.push(url);
    }
    return { sheets };
  }

  // First invalid token in a composition patch, as { property, requested }, or null.
  // A null value is valid: it removes Studio's override of that custom property.
  function invalidTokenInPatch(patch) {
    if (isPlainObject(patch.tokens)) {
      for (const [name, value] of Object.entries(patch.tokens)) {
        if (!TOKEN_NAME.test(name) || (value !== null && safeCssString(value) === undefined)) return { property: 'tokens', requested: name };
      }
    }
    for (const role of ['sans', 'serif', 'mono', 'display']) {
      if (patch[role] && safeCssString(patch[role]) === undefined) return { property: role, requested: String(patch[role]).slice(0, 80) };
    }
    return null;
  }

  // What a later call (`new FontKitBridge(options)` or `initFontKitBridge(options)`) may still change on a bridge that is
  // already running: an `allowedOrigins` list that narrows its policy, and nothing else. Returns the sentence for the
  // console warning that says what was applied and what was ignored, and whether the policy actually changed.
  function narrowRunningBridge(running, rawOptions) {
    const given = isPlainObject(rawOptions) ? rawOptions : {};
    const parts = [];
    let changed = false;
    if (given.allowedOrigins != null) {
      const describe = () => (running.allowedOrigins === null ? 'any origin' : (running.allowedOrigins.join(' ') || 'no origin'));
      const before = describe();
      const outcome = running.narrowAllowedOrigins(given.allowedOrigins);
      changed = outcome.changed;
      const after = describe();
      parts.push(!outcome.applied ? `allowedOrigins ignored (it would not narrow the running policy: ${before})`
        : outcome.changed ? `allowedOrigins narrowed to ${after} (was: ${before})` : `allowedOrigins unchanged (${after})`);
    }
    const ignored = Object.keys(given).filter((key) => key !== 'allowedOrigins');
    if (ignored.length) parts.push(`ignored: ${ignored.join(', ')}`);
    return { sentence: parts.length ? `${parts.join('; ')}.` : 'Its options were ignored.', changed };
  }

  class FontKitBridge {
    constructor(rawOptions) {
      // One bridge per page. When a Studio has already talked to the bridge on this page, a second
      // `new FontKitBridge(...)` (an HMR re-run, say) returns that instance instead of starting a duplicate that
      // would answer the Studio as well and capture the first one's edits as its "originals". Its options are not
      // merged into the running bridge, with one exception: an `allowedOrigins` list that narrows the running
      // policy (an open bridge allows everything) is applied, so a security option is never silently dropped. It can
      // never widen the policy, and a pinned Studio at an origin that is no longer allowed loses its session.
      // Everything else is ignored, and the warning says what was applied and what was ignored. A bridge that no
      // Studio has talked to yet (or a disposed one) is replaced instead, so changed options apply (see below).
      if (typeof window !== 'undefined') {
        const running = global.__fontkitBridge;
        if (running && !running.disposed && running.everConnected && typeof running.narrowAllowedOrigins === 'function') {
          console.warn('[FontKitBridge] A bridge already exists on this page; new FontKitBridge() returned it. '
            + `${narrowRunningBridge(running, rawOptions).sentence} `
            + 'Set window.FONTKIT_BRIDGE_OPTIONS or use data-auto-init="false" to configure the first one.');
          return running;
        }
      }
      const options = isPlainObject(rawOptions) ? rawOptions : {};
      this.initOptions = rawOptions; // initFontKitBridge() tells a reused object from a new one
      this.protocolVersion = PROTOCOL_VERSION;
      this.revision = 0;
      this.options = {
        autoDiscover: true,
        autoDiscoverSemantic: true,
        enableHighlightOverlay: false, // the Studio draws overlays (Spec §2.4)
        enableClickToSelect: true,
        tokens: {},
        onApplied: null,
        ...options
      };
      this.allowedOrigins = resolveAllowedOrigins(options.allowedOrigins);

      // Pinned Studio session (set by design:hello).
      this.studioSource = null;
      this.studioOrigin = null;
      this.sessionId = null;
      this.mode = 'select';
      this.active = false;
      this.everConnected = false; // a Studio has said hello at least once
      this.auto = false; // set when the page's script tag created this instance
      this.disposed = false;
      this.listeners = [];
      this.openerTimer = null;
      this.overlayRequested = false; // design:mode {overlay: true}

      // Targets: id -> record {id, element, stable, role, name, kind, fontWeights}.
      this.targets = new Map();
      this.elementIds = new WeakMap(); // element -> target id
      this.bridgeAttrs = new WeakMap(); // element -> Map(attribute -> value the bridge wrote)
      this.autoCounter = 0;
      this.warnedDuplicates = new Set();

      // Original state, captured once per element before the bridge first touches it.
      this.styleState = new WeakMap(); // element -> {snapshot, raw, cssText, props}
      this.styledElements = new Set();
      this.textState = new WeakMap(); // element -> {leaf, nodes|node, originalData, original}
      this.textElements = new Set();
      this.tokenOverrides = new Map(); // '--name' -> value (ledger tokens)
      this.attrState = new WeakMap(); // element -> Map(attribute -> original value or null)
      this.attrElements = new Set();
      this.placedAssets = new WeakMap(); // target element -> bridge-inserted <img>
      this.placedElements = new Set();
      this.changeOrder = new Set(); // target ids, ordered by first change

      // Arrangement: container keys, original child order (captured once while a
      // container differs from it), elements the bridge moved, css-order groups.
      this.containerKeys = new WeakMap(); // element -> 'container:<n>'
      this.containerByKey = new Map();
      this.containerCounter = 0;
      this.orderState = new Map(); // container -> {nodes, elements}, ordered by first change
      this.originalHome = new WeakMap(); // element -> container it originally lived in
      this.bridgeMoved = new WeakSet();
      this.cssOrderGroups = new WeakMap(); // parent -> Set of elements given an order
      this.domVersion = 0; // bumped on structural/class/id mutations (selector cache)
      this.selectorCache = new WeakMap();

      // Font stylesheets: url -> <link>, and which target asked for which url.
      this.fontSheets = new Map();
      this.fontRefs = new Map();
      this.compositionSheets = new Set(); // stylesheets the latest composition update asked for (see setCompositionSheets)

      // SPA/HMR: overrides of removed author targets, kept so a re-render can get them back.
      this.lost = new Map(); // targetId -> {element}
      this.reapplyLog = new Map(); // targetId -> [timestamps]
      this.warnedLoops = new Set();
      this.discoveryFast = false;
      this.discoveryRuns = [];
      this.discoveryBackoff = 0;
      this.lastDiscoveryRun = 0;
      this.warnedStorm = false;
      this.watchers = []; // runtime-error windows after applied updates/moves

      // Hover / selection / bounds.
      this.hoverId = null;
      this.pointer = null;
      this.hoverFrame = 0;
      this.selectedId = null;
      this.selectedElement = null;
      this.lastBounds = null;
      this.boundsFrame = 0;
      this.resizeObserver = null;
      this.mutationObserver = null;
      this.discoveryTimer = null;
      this.discoveryFirstQueued = 0;

      this.overlayEl = null;
      this.hoverOverlayEl = null;
      this.hoverBadgeEl = null;

      // The first instance owns the global slot, so a deferred auto-init (or a
      // second initFontKitBridge call) reuses it instead of adding an open bridge.
      // An auto-created instance that no Studio has talked to yet is replaced, so
      // `new FontKitBridge({allowedOrigins})` is safe whatever the script order.
      if (typeof window !== 'undefined') {
        const existing = global.__fontkitBridge;
        if (!existing) {
          global.__fontkitBridge = this;
        } else {
          // Only a replaceable instance gets here (the check at the top returned any other): one that no
          // Studio has talked to yet, or one that was disposed.
          if (typeof existing.dispose === 'function') existing.dispose();
          global.__fontkitBridge = this;
        }
      }

      this.init();
    }

    listen(target, type, handler, options) {
      target.addEventListener(type, handler, options);
      this.listeners.push([target, type, handler, options]);
    }

    init() {
      if (typeof window === 'undefined') return;
      this.listen(window, 'message', (e) => this.handleMessage(e));

      // Listeners are always installed but stay inert until a Studio session exists.
      this.listen(document, 'click', (e) => this.handleDocumentClick(e), true);
      this.listen(document, 'pointermove', (e) => this.handlePointerMove(e), { capture: true, passive: true });
      this.listen(document, 'mouseout', (e) => {
        if (!e.relatedTarget) this.setHover(null);
      }, true);
      this.listen(window, 'scroll', () => this.scheduleBounds(), true);
      this.listen(window, 'resize', () => this.scheduleBounds());
      // Runtime errors are only reported inside the window that follows a change.
      this.listen(window, 'error', (e) => this.noteRuntimeError(e && e.message ? e.message : 'Script error'));
      this.listen(window, 'unhandledrejection', (e) => {
        const reason = e && e.reason;
        const text = reason && reason.message ? reason.message : String(reason);
        this.noteRuntimeError(`Unhandled promise rejection: ${text}`);
      });

      this.announceReadiness();
    }

    // Removes every listener, observer, timer and node of this instance. Only
    // used when a constructed instance replaces an unconnected auto instance.
    dispose() {
      if (this.disposed) return;
      this.disposed = true;
      this.listeners.forEach(([target, type, handler, options]) => target.removeEventListener(type, handler, options));
      this.listeners = [];
      if (this.mutationObserver) this.mutationObserver.disconnect();
      if (this.resizeObserver) this.resizeObserver.disconnect();
      clearTimeout(this.discoveryTimer);
      clearInterval(this.openerTimer);
      if (this.hoverFrame && typeof cancelAnimationFrame !== 'undefined') cancelAnimationFrame(this.hoverFrame);
      if (this.boundsFrame && typeof cancelAnimationFrame !== 'undefined') cancelAnimationFrame(this.boundsFrame);
      this.active = false;
      this.dropSession();
      this.removeOverlay();
    }

    // First hello: discover targets, start observers and (optionally) overlays.
    activate() {
      if (this.active) return;
      this.active = true;
      this.discoverTargets();

      if (typeof MutationObserver !== 'undefined') {
        this.mutationObserver = new MutationObserver((records) => this.handleMutations(records));
        // childList drives discovery; class/id changes only invalidate cached selectors; an author
        // data-design-id set in place (an auto target promoted by an app update) is discovered too.
        this.mutationObserver.observe(document.body || document.documentElement,
          { childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'id', 'data-design-id'] });
      }
      if (typeof ResizeObserver !== 'undefined') {
        this.resizeObserver = new ResizeObserver(() => this.scheduleBounds());
      }
      this.updateOverlay();
    }

    handleMutations(records) {
      let relevant = false;
      let fast = this.lost.size > 0;
      records.forEach((record) => {
        if (record.type === 'attributes') {
          if (this.isOverlayNode(record.target)) return;
          this.domVersion += 1;
          if (record.attributeName === 'data-design-id' && !this.isBridgeAttr(record.target, 'data-design-id')) {
            const id = record.target.getAttribute('data-design-id');
            const known = this.recordFor(record.target);
            if (isNonEmptyString(id) && !(known && known.id === id)) relevant = true;
            // The author id was taken away: the target needs an auto id (see demote).
            if (!isNonEmptyString(id) && known && known.stable) relevant = true;
          }
          return;
        }
        if (this.isOverlayNode(record.target)) return;
        const nodes = Array.from(record.addedNodes).concat(Array.from(record.removedNodes))
          .filter((node) => !this.isOverlayNode(node));
        if (!nodes.length) return;
        relevant = true;
        this.domVersion += 1;
        if (!fast) fast = Array.from(record.removedNodes).some((node) => this.holdsOverrides(node));
      });
      if (relevant) this.scheduleDiscovery(fast);
    }

    // True when a removed node is, or contains, an element the bridge changed.
    holdsOverrides(node) {
      if (!node || node.nodeType !== 1) return false;
      const check = (set) => Array.from(set).some((el) => node === el || node.contains(el));
      return check(this.styledElements) || check(this.textElements);
    }

    isOverlayNode(node) {
      return !!node && node.nodeType === 1 && !!node.closest && !!node.closest(OVERLAY_SELECTOR);
    }

    // ---------------------------------------------------------------------
    // Optional in-target overlay (off by default; the Studio draws overlays).
    // ---------------------------------------------------------------------

    // The outline exists while the page asked for it (enableHighlightOverlay) or
    // the Studio did (design:mode {overlay: true}); it is removed otherwise.
    updateOverlay() {
      const wanted = !!this.options.enableHighlightOverlay || this.overlayRequested;
      if (wanted && !this.overlayEl) {
        this.setupOverlay();
        const selected = this.selectedId ? this.targets.get(this.selectedId) : null;
        if (selected) this.showActiveSelection(selected);
        const hovered = this.hoverId ? this.targets.get(this.hoverId) : null;
        if (hovered && !selected) this.showHoverOutline(hovered);
      } else if (!wanted && this.overlayEl) {
        this.removeOverlay();
      }
    }

    removeOverlay() {
      [this.overlayEl, this.hoverOverlayEl].forEach((node) => {
        if (node && node.parentNode) node.parentNode.removeChild(node);
      });
      this.overlayEl = null;
      this.hoverOverlayEl = null;
      this.hoverBadgeEl = null;
    }

    setupOverlay() {
      if (typeof document === 'undefined') return;
      if (document.getElementById('fontkit-bridge-overlay')) return;

      const overlay = document.createElement('div');
      overlay.id = 'fontkit-bridge-overlay';
      overlay.style.cssText = `
        position: fixed;
        pointer-events: none;
        z-index: 999999;
        display: none;
        border: 2px solid #0284c7;
        box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.8), 0 0 16px rgba(2, 132, 199, 0.45);
        border-radius: 4px;
        transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
        box-sizing: border-box;
      `;

      const badge = document.createElement('div');
      badge.id = 'fontkit-bridge-badge';
      badge.style.cssText = `
        position: absolute;
        bottom: calc(100% + 4px);
        left: -2px;
        background: #0284c7;
        color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        white-space: nowrap;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
        letter-spacing: 0.04em;
        text-transform: uppercase;
      `;
      overlay.appendChild(badge);

      // Hover Outline element
      const hoverOverlay = document.createElement('div');
      hoverOverlay.id = 'fontkit-bridge-hover';
      hoverOverlay.style.cssText = `
        position: fixed;
        pointer-events: none;
        z-index: 999998;
        display: none;
        border: 2px dashed #38bdf8;
        background: rgba(56, 189, 248, 0.08);
        border-radius: 4px;
        transition: all 0.12s ease;
        box-sizing: border-box;
      `;
      const hoverBadge = document.createElement('div');
      hoverBadge.style.cssText = `
        position: absolute;
        bottom: calc(100% + 2px);
        left: -2px;
        background: #0284c7;
        color: #ffffff;
        font-family: monospace;
        font-size: 10px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 3px;
        white-space: nowrap;
        pointer-events: none;
      `;
      hoverOverlay.appendChild(hoverBadge);

      (document.body || document.documentElement).appendChild(overlay);
      (document.body || document.documentElement).appendChild(hoverOverlay);
      this.overlayEl = overlay;
      this.hoverOverlayEl = hoverOverlay;
      this.hoverBadgeEl = hoverBadge;
    }

    placeOverlay(overlay, el) {
      const rect = el.getBoundingClientRect();
      overlay.style.display = 'block';
      overlay.style.top = `${rect.top}px`;
      overlay.style.left = `${rect.left}px`;
      overlay.style.width = `${rect.width}px`;
      overlay.style.height = `${rect.height}px`;
    }

    showHoverOutline(record) {
      if (!this.hoverOverlayEl || !record) return;
      this.placeOverlay(this.hoverOverlayEl, record.element);
      if (this.hoverBadgeEl) this.hoverBadgeEl.textContent = `⚡ Click to Edit: ${record.role}`;
    }

    hideHoverOutline() {
      if (this.hoverOverlayEl) this.hoverOverlayEl.style.display = 'none';
    }

    showActiveSelection(record) {
      if (!this.overlayEl) return;
      if (!record) {
        this.overlayEl.style.display = 'none';
        return;
      }
      this.hideHoverOutline();
      this.placeOverlay(this.overlayEl, record.element);
      const badge = document.getElementById('fontkit-bridge-badge');
      if (badge) badge.textContent = `✓ Selected: ${record.name || 'Element'}`;
    }

    // ---------------------------------------------------------------------
    // Messaging and session gating
    // ---------------------------------------------------------------------

    announceReadiness() {
      // No page data: anyone who frames the page may see this.
      const payload = { type: 'design:bridge-ready', protocolVersion: this.protocolVersion };
      if (window.parent && window.parent !== window) window.parent.postMessage(payload, '*');
      if (window.opener) window.opener.postMessage(payload, '*');
    }

    isStudioWindow(source) {
      if (!source) return false;
      if (window.parent && window.parent !== window && source === window.parent) return true;
      return !!window.opener && source === window.opener;
    }

    originAllowed(origin) {
      return this.allowedOrigins === null || this.allowedOrigins.includes(origin);
    }

    // Applies an `allowedOrigins` request only when it narrows the running policy: every requested origin is already
    // allowed (an open bridge allows everything), and the request is a list, not "any origin". Never widens.
    // A pinned Studio whose origin is no longer allowed is dropped, like a hello from a disallowed origin is ignored:
    // the bridge goes inert and applies nothing more. Returns { applied, changed }.
    narrowAllowedOrigins(requested) {
      if (typeof requested !== 'string' && !Array.isArray(requested)) return { applied: false, changed: false };
      const list = parseOriginList(requested);
      const current = this.allowedOrigins;
      if (list === null || (current !== null && !list.every((origin) => current.includes(origin)))) {
        return { applied: false, changed: false };
      }
      const next = Array.from(new Set(list));
      const changed = current === null || next.length !== current.length;
      this.allowedOrigins = next;
      if (this.studioSource && !this.originAllowed(this.studioOrigin)) this.dropSession();
      return { applied: true, changed };
    }

    // A pop-out Studio (window.opener) can close without saying goodbye: drop the
    // session on the next event so the page stops intercepting clicks.
    studioAlive() {
      if (!this.studioSource) return false;
      let closed = false;
      try {
        closed = this.studioSource.closed === true;
      } catch (e) {}
      if (closed) this.dropSession();
      return !closed;
    }

    dropSession() {
      this.studioSource = null;
      this.studioOrigin = null;
      this.sessionId = null;
      this.mode = 'select';
      this.hoverId = null;
      this.overlayRequested = false;
      clearInterval(this.openerTimer);
      this.openerTimer = null;
      this.hideHoverOutline();
      this.clearSelection();
      this.updateOverlay();
    }

    // A pop-out Studio can be closed with no further event: poll so the outline
    // goes away and the page stops intercepting clicks.
    watchOpener() {
      clearInterval(this.openerTimer);
      this.openerTimer = null;
      if (window.opener && this.studioSource === window.opener) {
        this.openerTimer = setInterval(() => this.studioAlive(), OPENER_POLL_MS);
      }
    }

    isFromSession(event, data) {
      return this.studioSource !== null
        && event.source === this.studioSource
        && event.origin === this.studioOrigin
        && data.sessionId === this.sessionId;
    }

    post(message) {
      if (!this.studioAlive()) return;
      const payload = { type: message.type, protocolVersion: this.protocolVersion, sessionId: this.sessionId, ...message };
      try {
        this.studioSource.postMessage(payload, this.studioOrigin === 'null' ? '*' : this.studioOrigin);
      } catch (err) {
        console.warn('[FontKitBridge] postMessage delivery failed:', err);
      }
    }

    handleMessage(event) {
      if (this.disposed) return;
      const data = event.data;
      if (!isPlainObject(data) || typeof data.type !== 'string') return;
      if (!data.type.startsWith('design:') && !data.type.startsWith('fontkit:')) return;
      if (data.protocolVersion !== PROTOCOL_VERSION) return;

      if (data.type === 'design:hello') {
        this.handleHello(event, data);
        return;
      }
      if (!this.isFromSession(event, data)) return;

      switch (data.type) {
        case 'design:update':
          this.handleUpdate(data);
          break;
        case 'design:reset':
          this.handleReset(data);
          break;
        case 'design:restore-text':
          this.handleRestoreText(data);
          break;
        case 'design:select':
          this.handleSelect(data.targetId, data.requestId);
          break;
        case 'design:move':
          this.handleMove(data);
          break;
        case 'design:highlight':
          this.handleHighlight(data);
          break;
        case 'design:mode':
          this.handleMode(data);
          break;
        case 'fontkit:change':
          this.handleFontKitChange(data);
          break;
        default:
          break;
      }
    }

    handleHello(event, data) {
      if (!this.isStudioWindow(event.source) || !this.originAllowed(event.origin)) return;
      if (!isNonEmptyString(data.sessionId, 200)) return;
      // Once pinned, only the same window and origin may start a new session
      // (a closed opener Studio unpins first, see studioAlive()).
      if (this.studioAlive() && (event.source !== this.studioSource || event.origin !== this.studioOrigin)) return;

      this.studioSource = event.source;
      this.studioOrigin = event.origin;
      this.sessionId = data.sessionId;
      this.everConnected = true;
      this.mode = 'select';
      this.hoverId = null;
      this.overlayRequested = false; // a new session starts without the Studio's overlay
      this.watchOpener();
      this.clearSelection();
      this.updateOverlay();

      // activate() runs the first discovery itself; later hellos rediscover.
      if (this.active) this.discoverTargets();
      else this.activate();
      this.post({
        type: 'design:ready',
        revision: this.revision,
        capabilities: { inspect: true, patch: true, typography: true, text: true, tokens: true, reset: true },
        viewport: { width: window.innerWidth, height: window.innerHeight },
        tokens: { css: this.getCurrentTokens() },
        targets: this.getTargetManifest(false),
        changes: this.buildLedger()
      });
    }

    reject(requestId, reason, detail, targetId) {
      const message = {
        type: 'design:rejected',
        requestId: typeof requestId === 'string' || typeof requestId === 'number' ? requestId : null,
        revision: this.revision,
        reason
      };
      if (typeof targetId === 'string') message.targetId = targetId;
      if (detail) message.detail = detail;
      this.post(message);
    }

    // Common request checks. Returns false (after replying) when rejected.
    checkRequest(data, { requireRevision = true, requireRequestId = true } = {}) {
      const targetId = typeof data.targetId === 'string' ? data.targetId : undefined;
      if (requireRequestId ? !isNonEmptyString(data.requestId, 200)
        : data.requestId !== undefined && data.requestId !== null && !isNonEmptyString(data.requestId, 200)) {
        this.reject(data.requestId, 'invalid-message', { field: 'requestId' }, targetId);
        return false;
      }
      const hasRevision = data.baseRevision !== undefined && data.baseRevision !== null;
      if ((requireRevision || hasRevision) && !(Number.isInteger(data.baseRevision) && data.baseRevision >= 0)) {
        this.reject(data.requestId, 'invalid-message', { field: 'baseRevision' }, targetId);
        return false;
      }
      return true;
    }

    checkRevision(data) {
      if (data.baseRevision === undefined || data.baseRevision === null || data.baseRevision === this.revision) return true;
      this.reject(data.requestId, 'revision-conflict', { baseRevision: data.baseRevision, revision: this.revision },
        typeof data.targetId === 'string' ? data.targetId : undefined);
      return false;
    }

    // Successful mutation: bump revision by exactly one and acknowledge. With
    // watch, runtime errors in the next second are reported as design:warning.
    acknowledge(data, fields, { watch = false } = {}) {
      this.revision += 1;
      if (watch) this.watchRuntimeErrors(data.requestId, fields.targetId);
      const message = {
        type: 'design:applied',
        requestId: data.requestId === undefined ? null : data.requestId,
        revision: this.revision,
        ...fields,
        changes: this.buildLedger()
      };
      this.post(message);
      this.scheduleBounds();
      if (typeof this.options.onApplied === 'function') {
        try {
          this.options.onApplied(fields.canonicalPatch, this.revision);
        } catch (err) {
          console.warn('[FontKitBridge] onApplied callback error:', err);
        }
      }
    }

    // Errors/rejections the app throws shortly after the bridge changed something
    // are very likely caused by it: the Studio shows them next to the change.
    watchRuntimeErrors(requestId, targetId) {
      const now = Date.now();
      this.watchers = this.watchers.filter((watcher) => watcher.until >= now);
      this.watchers.push({ requestId: typeof requestId === 'string' ? requestId : null, targetId, until: now + WARNING_WINDOW_MS });
    }

    noteRuntimeError(message) {
      const now = Date.now();
      this.watchers = this.watchers.filter((watcher) => watcher.until >= now);
      const watcher = this.watchers[this.watchers.length - 1]; // the most recent change
      if (!watcher || !this.studioSource) return;
      this.post({
        type: 'design:warning',
        requestId: watcher.requestId,
        targetId: watcher.targetId,
        kind: 'runtime-error',
        message: String(message).slice(0, WARNING_MAX_LENGTH)
      });
    }

    // ---------------------------------------------------------------------
    // design:update — targeted (validated, atomic) and legacy composition
    // ---------------------------------------------------------------------

    handleUpdate(data) {
      if (data.targetId === undefined || data.targetId === null) {
        this.handleCompositionUpdate(data);
        return;
      }
      if (!this.checkRequest(data)) return;
      if (!isNonEmptyString(data.targetId)) {
        this.reject(data.requestId, 'invalid-message', { field: 'targetId' });
        return;
      }
      const targetId = data.targetId;
      if (!isPlainObject(data.patch)) {
        this.reject(data.requestId, 'invalid-message', { field: 'patch' }, targetId);
        return;
      }
      if (!this.checkRevision(data)) return;
      const record = this.findTarget(targetId);
      if (!record) {
        this.reject(data.requestId, 'unknown-target', { targetId }, targetId);
        return;
      }

      // Validate the whole patch before touching the DOM: a rejection changes nothing.
      const editable = this.editableFor(record);
      const entries = Object.entries(data.patch);
      for (const [key] of entries) {
        const rule = Object.prototype.hasOwnProperty.call(PATCH_RULES, key) ? PATCH_RULES[key] : null;
        if (!rule || (rule.group && !editable[rule.group])) {
          this.reject(data.requestId, 'unsupported-property', { property: key }, targetId);
          return;
        }
      }
      const operations = [];
      for (const [key, value] of entries) {
        const rule = PATCH_RULES[key];
        if (value === null) {
          operations.push({ key, rule, value: null });
          continue;
        }
        const canonical = rule.canonical(value, record);
        if (canonical === undefined) {
          this.reject(data.requestId, 'unsupported-value', { property: key, requested: value }, targetId);
          return;
        }
        operations.push({ key, rule, value: canonical });
      }

      const el = record.element;
      const canonicalPatch = {};
      for (const { key, rule, value } of operations) {
        canonicalPatch[key] = value;
        if (key === 'fontStylesheet') {
          this.setFontSheet(record, value);
        } else if (key === 'text') {
          if (value === null) this.restoreText(el);
          else this.setText(el, value);
        } else if (value === null) {
          this.clearStyle(el, rule.css);
        } else {
          this.setStyle(el, rule.css, rule.toCss(value));
        }
      }
      this.noteChange(record);
      this.acknowledge(data, { targetId, canonicalPatch, target: this.manifestFor(record) }, { watch: true });
    }

    handleCompositionUpdate(data) {
      if (!this.checkRequest(data, { requireRevision: false })) return;
      if (!isPlainObject(data.patch)) {
        this.reject(data.requestId, 'invalid-message', { field: 'patch' });
        return;
      }
      if (!this.checkRevision(data)) return;
      // Tokens are all-or-nothing: one invalid name or value rejects the update instead of being dropped silently.
      const badToken = invalidTokenInPatch(data.patch);
      if (badToken) {
        this.reject(data.requestId, 'unsupported-value', { property: badToken.property, requested: badToken.requested });
        return;
      }
      // The library fonts the composition sends: all-or-nothing as well, and they never reach the page unvalidated.
      let sheets;
      if (Object.prototype.hasOwnProperty.call(data.patch, 'fontStylesheets')) {
        const checked = checkCompositionSheets(data.patch.fontStylesheets);
        if (!checked.sheets) {
          this.reject(data.requestId, 'unsupported-value', { property: 'fontStylesheets', requested: checked.requested });
          return;
        }
        sheets = checked.sheets;
      }
      this.activate();

      const patch = data.patch;
      const canonicalPatch = {};
      if (sheets !== undefined) {
        this.setCompositionSheets(sheets);
        canonicalPatch.fontStylesheets = sheets;
      }

      // 1. Global CSS tokens
      if (isPlainObject(patch.tokens)) {
        canonicalPatch.tokens = {};
        for (const [key, value] of Object.entries(patch.tokens)) {
          // null removes the override; a name Studio never overrode is ignored and not reported.
          if (value === null) {
            if (this.removeToken(key)) canonicalPatch.tokens[key] = null;
            continue;
          }
          const canonical = this.setToken(key, value);
          if (canonical !== undefined) canonicalPatch.tokens[key] = canonical;
        }
      }

      // Direct token shortcuts
      ['sans', 'serif', 'mono', 'display'].forEach((role) => {
        const varName = `--font-${role}`;
        const canonical = patch[role] ? this.setToken(varName, patch[role]) : undefined;
        if (canonical !== undefined) canonicalPatch[varName] = canonical;
      });

      // 2. Live Movement in Wireframe Setup Up and Down (Reordering)
      const slots = Array.isArray(patch.slots) ? patch.slots.filter(isPlainObject) : null;
      if (isPlainObject(patch.layout) && Array.isArray(patch.layout.order)) {
        this.applyWireframeMovement(patch.layout.order.filter(isPlainObject), slots || []);
      } else if (slots) {
        this.applyWireframeMovement(slots.map((s, idx) => ({ id: s.id, role: s.role, index: idx })), slots);
      }

      // 3. Structured Slots Synchronization (Live text, typography, and PNG / SVG placement)
      if (slots) slots.forEach((slot) => this.applySlotUpdate(slot));

      this.acknowledge(data, { targetId: 'global', canonicalPatch }, { watch: true });
    }

    // ---------------------------------------------------------------------
    // design:reset / design:restore-text
    // ---------------------------------------------------------------------

    handleReset(data) {
      if (!this.checkRequest(data)) return;
      const hasTarget = data.targetId !== undefined && data.targetId !== null;
      if (hasTarget && !isNonEmptyString(data.targetId)) {
        this.reject(data.requestId, 'invalid-message', { field: 'targetId' });
        return;
      }
      if (!this.checkRevision(data)) return;

      if (hasTarget) {
        const record = this.findTarget(data.targetId);
        if (!record) {
          this.reject(data.requestId, 'unknown-target', { targetId: data.targetId }, data.targetId);
          return;
        }
        this.releaseCssOrder(record.element);
        this.resetElement(record.element);
        this.releaseFontRef(record.id);
        this.lost.delete(record.id);
        this.noteChange(record);
        this.restoreElementPosition(record.element);
        this.acknowledge(data, { targetId: record.id, canonicalPatch: {}, target: this.manifestFor(record), reset: true });
        return;
      }

      // Everything: placed assets, every bridge-touched element (styles, tokens
      // on :root, wireframe helpers), every text change and attribute write, every
      // moved child, every injected font stylesheet.
      Array.from(this.placedElements).forEach((el) => this.removePlacedAsset(el));
      Array.from(this.styledElements).forEach((el) => this.resetStyles(el));
      Array.from(this.textElements).forEach((el) => this.restoreText(el));
      Array.from(this.attrElements).forEach((el) => this.restoreAttrs(el));
      this.restoreAllOrder();
      this.removeAllFontSheets();
      this.tokenOverrides.clear();
      this.lost.clear();
      this.reapplyLog.clear();
      this.cssOrderGroups = new WeakMap();
      this.acknowledge(data, { targetId: 'global', canonicalPatch: {}, reset: true });
    }

    handleRestoreText(data) {
      if (!this.checkRequest(data, { requireRevision: false, requireRequestId: false })) return;
      if (!this.checkRevision(data)) return;
      Array.from(this.textElements).forEach((el) => this.restoreText(el));
      this.acknowledge(data, { targetId: 'global', canonicalPatch: {} });
    }


    // ---------------------------------------------------------------------
    // design:move
    // ---------------------------------------------------------------------

    // `to` is exactly one of {index}, {before}, {after}, {container, index?}.
    parseMoveTarget(to) {
      if (!isPlainObject(to)) return { error: 'to' };
      const keys = Object.keys(to);
      const has = (key) => Object.prototype.hasOwnProperty.call(to, key);
      const integer = (value) => Number.isInteger(value);
      if (keys.length === 1 && has('index')) return integer(to.index) ? { form: 'index', index: to.index } : { error: 'to.index' };
      if (keys.length === 1 && (has('before') || has('after'))) {
        const form = has('before') ? 'before' : 'after';
        return isNonEmptyString(to[form]) ? { form, ref: to[form] } : { error: `to.${form}` };
      }
      if (has('container') && keys.every((key) => key === 'container' || key === 'index')) {
        if (!isNonEmptyString(to.container)) return { error: 'to.container' };
        if (has('index') && !integer(to.index)) return { error: 'to.index' };
        return { form: 'container', container: to.container, index: has('index') ? to.index : undefined };
      }
      return { error: 'to' };
    }

    rejectMove(data, targetId, reason, extra) {
      this.reject(data.requestId, 'unsupported-value', { property: 'to', requested: data.to, reason, ...extra }, targetId);
    }

    rejectGuard(data, targetId, guard) {
      this.reject(data.requestId, 'unsupported-value', {
        property: guard.guard === 'css-order' ? 'strategy' : 'move',
        requested: guard.guard === 'css-order' ? 'css-order' : data.to,
        ...guard
      }, targetId);
    }

    handleMove(data) {
      if (!this.checkRequest(data)) return;
      if (!isNonEmptyString(data.targetId)) {
        this.reject(data.requestId, 'invalid-message', { field: 'targetId' });
        return;
      }
      const targetId = data.targetId;
      const to = this.parseMoveTarget(data.to);
      if (to.error) {
        this.reject(data.requestId, 'invalid-message', { field: to.error }, targetId);
        return;
      }
      if (data.strategy !== undefined && typeof data.strategy !== 'string') {
        this.reject(data.requestId, 'invalid-message', { field: 'strategy' }, targetId);
        return;
      }
      if (data.force !== undefined && typeof data.force !== 'boolean') {
        this.reject(data.requestId, 'invalid-message', { field: 'force' }, targetId);
        return;
      }
      if (!this.checkRevision(data)) return;
      const record = this.findTarget(targetId);
      if (!record) {
        this.reject(data.requestId, 'unknown-target', { targetId }, targetId);
        return;
      }
      const strategy = data.strategy === undefined ? 'dom' : data.strategy;
      if (strategy !== 'dom' && strategy !== 'css-order') {
        this.reject(data.requestId, 'unsupported-value', { property: 'strategy', requested: data.strategy }, targetId);
        return;
      }

      // Resolve the destination: parent plus the position among its other children.
      const el = record.element;
      let destParent;
      let referenceEl = null;
      let position;
      if (to.form === 'index') {
        destParent = el.parentElement;
      } else if (to.form === 'container') {
        destParent = this.resolveContainer(to.container);
        if (!destParent) return this.rejectMove(data, targetId, 'unknown-container');
        if (destParent === el) return this.rejectMove(data, targetId, 'into-self');
        if (el.contains(destParent)) return this.rejectMove(data, targetId, 'into-descendant');
      } else {
        const reference = this.findTarget(to.ref);
        if (!reference) {
          this.reject(data.requestId, 'unknown-target', { targetId: to.ref, field: `to.${to.form}` }, targetId);
          return;
        }
        if (reference.element === el) return this.rejectMove(data, targetId, 'relative-to-self');
        if (el.contains(reference.element)) return this.rejectMove(data, targetId, 'into-descendant');
        referenceEl = reference.element;
        destParent = referenceEl.parentElement;
      }
      if (!destParent || NO_CHILDREN.has(destParent.localName)) return this.rejectMove(data, targetId, 'void-or-replaced-container');
      const others = this.orderedSiblings(destParent).filter((sibling) => sibling !== el);
      if (to.form === 'before' || to.form === 'after') {
        const at = others.indexOf(referenceEl);
        if (at < 0) return this.rejectMove(data, targetId, 'unarrangeable-reference');
        position = to.form === 'before' ? at : at + 1;
      } else {
        position = to.index === undefined ? others.length : to.index;
        if (position < 0 || position > others.length) return this.rejectMove(data, targetId, 'index-out-of-range', { count: others.length + 1 });
      }

      let finalIndex = position;
      if (strategy === 'css-order') {
        const parent = el.parentElement;
        const guard = !parent || !this.isFlexOrGrid(parent)
          ? { guard: 'css-order', message: 'The CSS order strategy needs a flex or grid parent.', overridable: false }
          : (destParent !== parent
            ? { guard: 'css-order', message: 'The CSS order strategy cannot move an element into another container.', overridable: false }
            : null);
        if (guard) {
          this.rejectGuard(data, targetId, guard);
          return;
        }
        const desired = others.slice();
        desired.splice(position, 0, el);
        this.applyCssOrder(parent, desired);
      } else {
        const guard = this.moveGuard(el, destParent, data.force === true);
        if (guard) {
          this.rejectGuard(data, targetId, guard);
          return;
        }
        this.moveInDom(el, destParent, others, position);
        finalIndex = this.orderedSiblings(destParent).indexOf(el);
        this.registerSibling(el);
      }
      this.pruneOrderState();
      this.acknowledge(data, {
        targetId: record.id,
        canonicalPatch: { move: { container: this.containerKey(destParent), index: finalIndex } },
        target: this.manifestFor(record)
      }, { watch: true });
    }

    moveInDom(el, destParent, others, position) {
      const sourceParent = el.parentElement;
      this.captureOrder(sourceParent);
      this.captureOrder(destParent);
      this.bridgeMoved.add(el);
      if (sourceParent === destParent && this.orderedSiblings(destParent).indexOf(el) === position) return;
      this.domVersion += 1; // cached selectors (nth-of-type) are stale from here on
      if (position < others.length) destParent.insertBefore(el, others[position]);
      else if (others.length) others[others.length - 1].after(el);
      else destParent.appendChild(el);
    }

    // Assigns `order` to every sibling so the visual order matches `desired`
    // while the DOM stays untouched. Recorded as ledger declarations.
    applyCssOrder(parent, desired) {
      const group = this.cssOrderGroups.get(parent) || new Set();
      desired.forEach((sibling, index) => {
        this.registerSibling(sibling);
        const sibRecord = this.recordFor(sibling);
        if (!sibRecord) return;
        this.setStyle(sibling, 'order', String(index));
        group.add(sibling);
        this.noteChange(sibRecord);
      });
      this.cssOrderGroups.set(parent, group);
    }

    // Resetting one element of a css-order group clears the whole group.
    releaseCssOrder(el) {
      const parent = el.parentElement;
      const group = parent ? this.cssOrderGroups.get(parent) : null;
      if (!group || !group.has(el)) return;
      group.forEach((sibling) => {
        this.clearStyle(sibling, 'order');
        const sibRecord = this.recordFor(sibling);
        if (sibRecord) this.noteChange(sibRecord);
      });
      this.cssOrderGroups.delete(parent);
    }

    // ---------------------------------------------------------------------
    // Move guards (dom strategy). Returns null, or {guard, message, overridable, framework?}.
    // ---------------------------------------------------------------------

    commonAncestor(nodes) {
      let ancestor = nodes[0].parentElement;
      while (ancestor && !nodes.every((node) => ancestor.contains(node))) ancestor = ancestor.parentElement;
      return ancestor;
    }

    moveGuard(el, destParent, force) {
      const controls = Array.from(el.querySelectorAll(FORM_CONTROLS));
      if (el.matches(FORM_CONTROLS)) controls.unshift(el);

      // 1. Form controls must keep their form owner.
      const newOwner = destParent.closest('form');
      for (const control of controls) {
        if (control.hasAttribute('form')) continue; // explicit owner: position does not matter
        const owner = control.form;
        if (owner && !el.contains(owner) && owner !== newOwner) {
          return { guard: 'form-owner', overridable: false,
            message: 'This move would take a form control out of its form, so it would no longer be submitted with it.' };
        }
      }

      // 2. A radio input must stay inside the container that holds its group.
      const radios = controls.filter((control) => control.localName === 'input' && control.type === 'radio' && control.name);
      if (radios.length) {
        const allRadios = Array.from(el.getRootNode().querySelectorAll('input[type="radio"]'));
        for (const radio of radios) {
          const group = allRadios.filter((other) => other.name === radio.name && other.form === radio.form);
          if (group.every((other) => el.contains(other))) continue;
          const holder = this.commonAncestor(group);
          if (holder && !holder.contains(destParent)) {
            return { guard: 'radio-group', overridable: false,
              message: `This move would separate the radio input "${radio.name}" from the rest of its group.` };
          }
        }
      }

      // 3. Label and aria references that resolve today must still resolve.
      const reference = this.referenceBreak(el, destParent);
      if (reference) return { ...reference, overridable: false };

      // 4. Content model: a block-level element would end up inside a phrasing parent.
      if (destParent !== el.parentElement && BLOCK_ELEMENTS.has(el.localName) && PHRASING_PARENTS.has(destParent.localName)) {
        return { guard: 'content-model', overridable: false,
          message: `A <${el.localName}> cannot be placed inside a <${destParent.localName}>; the browser would repair the markup differently.` };
      }

      // 5. Framework-managed subtrees: the framework may undo or fight the move.
      const framework = this.frameworkOf(el) || this.frameworkOf(destParent);
      if (framework && !force) {
        return { guard: 'framework-managed', overridable: true, framework,
          message: `This part of the page is managed by ${framework === 'unknown' ? 'a framework' : framework}; it may undo a DOM move. Use the CSS order strategy, or move anyway.` };
      }
      return null;
    }

    referenceBreak(el, destParent) {
      // Implicit labels: a control leaving the <label> that wraps it loses its label.
      const labelable = Array.from(el.querySelectorAll(LABELABLE));
      if (el.matches(LABELABLE)) labelable.unshift(el);
      for (const control of labelable) {
        for (const label of Array.from(control.labels || [])) {
          if (label.hasAttribute('for') || el.contains(label) || !label.contains(control)) continue;
          if (!label.contains(destParent)) {
            return { guard: 'label-reference', message: 'This move would take an input out of the <label> that wraps it.' };
          }
        }
      }

      // Id references (label[for], aria-controls/labelledby/describedby) are scoped
      // to the root they live in: they only break when the root changes.
      const sourceRoot = el.getRootNode();
      const destRoot = destParent.getRootNode();
      if (sourceRoot === destRoot || typeof sourceRoot.getElementById !== 'function' || typeof destRoot.getElementById !== 'function') return null;
      const ARIA = ['aria-controls', 'aria-labelledby', 'aria-describedby'];
      const idsOf = (node) => (node.getAttribute('id') ? [node.getAttribute('id')] : []);
      const insideIds = new Set();
      [el].concat(Array.from(el.querySelectorAll('[id]'))).forEach((node) => idsOf(node).forEach((id) => insideIds.add(id)));
      const refs = (node) => {
        const out = [];
        if (node.localName === 'label' && node.getAttribute('for')) out.push(['label-reference', node.getAttribute('for')]);
        ARIA.forEach((name) => {
          (node.getAttribute(name) || '').split(/\s+/).filter(Boolean).forEach((id) => out.push(['aria-reference', id]));
        });
        return out;
      };
      for (const node of [el].concat(Array.from(el.querySelectorAll('*')))) {
        for (const [guard, id] of refs(node)) {
          const today = sourceRoot.getElementById(id);
          if (today && !el.contains(today) && destRoot.getElementById(id) !== today) {
            return { guard, message: `The reference to #${id} would stop resolving after this move.` };
          }
        }
      }
      for (const node of Array.from(sourceRoot.querySelectorAll('label[for], [aria-controls], [aria-labelledby], [aria-describedby]'))) {
        if (el.contains(node)) continue;
        for (const [guard, id] of refs(node)) {
          if (insideIds.has(id) && sourceRoot.getElementById(id) && el.contains(sourceRoot.getElementById(id))) {
            return { guard, message: `A reference to #${id} from elsewhere would stop resolving after this move.` };
          }
        }
      }
      return null;
    }

    // ---------------------------------------------------------------------
    // Original child order (captured once while a container differs from it)
    // ---------------------------------------------------------------------

    captureOrder(container) {
      if (!container || this.orderState.has(container)) return;
      const elements = this.childElements(container);
      this.orderState.set(container, { nodes: Array.from(container.childNodes), elements });
      elements.forEach((child) => {
        if (!this.originalHome.has(child)) this.originalHome.set(child, container);
      });
    }

    // Children now in the container that count for comparing: the originals and
    // anything the bridge moved here, never elements the app added.
    structureChildren(container, state) {
      const known = new Set(state.elements);
      return this.childElements(container).filter((child) => known.has(child) || this.bridgeMoved.has(child));
    }

    structureDiffers(container) {
      const state = this.orderState.get(container);
      if (!state) return false;
      const expected = state.elements.filter((child) => child.parentNode !== null);
      const now = this.structureChildren(container, state);
      return expected.length !== now.length || expected.some((child, index) => child !== now[index]);
    }

    // Containers back in their original order (or gone) are forgotten.
    pruneOrderState() {
      Array.from(this.orderState.entries()).forEach(([container, state]) => {
        if (container.isConnected && this.structureDiffers(container)) return;
        // Same element order as the original: also put whitespace/text nodes back.
        if (container.isConnected && state.elements.every((child) => child.parentNode === container)) {
          this.restoreNodeOrder(container, state);
        }
        this.orderState.delete(container);
        state.elements.forEach((child) => {
          if (this.originalHome.get(child) === container) this.originalHome.delete(child);
        });
      });
    }

    buildStructure() {
      this.pruneOrderState();
      const structure = [];
      this.orderState.forEach((state, container) => {
        const author = container.getAttribute('data-design-id');
        structure.push({
          containerKey: this.containerKey(container),
          selector: this.containerSelector(container),
          stable: !!author && !this.isBridgeAttr(container, 'data-design-id'),
          name: this.containerName(container),
          html: this.cleanHTML(container),
          order: this.childElements(container).map((child) => this.nameOfElement(child)),
          // The same children by target id: names can repeat, ids cannot, so a saved order can be replayed.
          orderIds: this.childElements(container).map((child) => {
            this.registerSibling(child);
            const record = this.recordFor(child);
            return record ? record.id : '';
          })
        });
      });
      return structure;
    }

    // Reset-all: every captured container gets its original nodes back, in order.
    restoreAllOrder() {
      const states = Array.from(this.orderState.entries());
      states.forEach(([container, state]) => {
        state.nodes.forEach((node) => {
          if (node.parentNode && node.parentNode !== container) container.appendChild(node);
        });
      });
      states.forEach(([container, state]) => this.restoreNodeOrder(container, state));
      this.domVersion += 1;
      this.orderState.clear();
      this.originalHome = new WeakMap();
    }

    // Puts the container's original nodes (text included) back in their original
    // order; nodes already in place are not touched.
    restoreNodeOrder(container, state) {
      const nodes = state.nodes.filter((node) => node.parentNode === container);
      const original = new Set(nodes);
      const current = Array.from(container.childNodes).filter((node) => original.has(node));
      if (current.every((node, index) => node === nodes[index])) return; // foreign nodes may sit between
      let ref = nodes.length ? nodes[nodes.length - 1].nextSibling : null;
      for (let i = nodes.length - 1; i >= 0; i -= 1) {
        if (nodes[i].nextSibling !== ref) container.insertBefore(nodes[i], ref);
        ref = nodes[i];
      }
    }

    // Reset of one target: back into its original container, before the element
    // that originally followed it (or after the one that preceded it).
    restoreElementPosition(el) {
      const home = this.originalHome.get(el);
      const state = home ? this.orderState.get(home) : null;
      if (!home || !state || !home.isConnected) return;
      this.domVersion += 1;
      const originalIndex = state.elements.indexOf(el);
      const successor = state.elements.slice(originalIndex + 1).find((child) => child !== el && child.parentNode === home);
      const current = this.childElements(home);
      const at = current.indexOf(el);
      const next = at >= 0 ? current[at + 1] || null : undefined;
      if (successor) {
        if (next !== successor) home.insertBefore(el, successor);
      } else if (next !== null) {
        const last = current.filter((child) => child !== el).pop();
        if (last) last.after(el);
        else home.appendChild(el);
      }
      this.pruneOrderState();
    }

    // ---------------------------------------------------------------------
    // Font stylesheets (patch key fontStylesheet)
    // ---------------------------------------------------------------------

    // The target's stylesheet reference becomes `url` (null drops it). One <link>
    // per distinct URL; a link goes away when no target references it any more.
    setFontSheet(record, url) {
      const previous = this.fontRefs.get(record.id);
      if (url === null) {
        this.releaseFontRef(record.id);
        return;
      }
      this.fontRefs.set(record.id, url);
      this.ensureFontLink(url);
      if (previous && previous !== url) this.releaseUnusedFontSheet(previous);
    }

    ensureFontLink(url) {
      const existing = this.fontSheets.get(url);
      if (existing && existing.isConnected) return;
      const link = document.createElement('link');
      link.setAttribute('rel', 'stylesheet');
      link.setAttribute('href', url);
      link.setAttribute('data-fontkit-font', '');
      (document.head || document.documentElement).appendChild(link);
      this.fontSheets.set(url, link);
    }

    releaseFontRef(targetId) {
      const url = this.fontRefs.get(targetId);
      if (url === undefined) return;
      this.fontRefs.delete(targetId);
      this.releaseUnusedFontSheet(url);
    }

    // The composition's own references: each update is the complete set it needs. A sheet stays while a target
    // or the composition still refers to it, like any other reference.
    setCompositionSheets(urls) {
      const previous = this.compositionSheets;
      this.compositionSheets = new Set(urls);
      urls.forEach((url) => this.ensureFontLink(url));
      previous.forEach((url) => {
        if (!this.compositionSheets.has(url)) this.releaseUnusedFontSheet(url);
      });
    }

    releaseUnusedFontSheet(url) {
      if (Array.from(this.fontRefs.values()).includes(url) || this.compositionSheets.has(url)) return;
      const link = this.fontSheets.get(url);
      if (link && link.parentNode) link.parentNode.removeChild(link);
      this.fontSheets.delete(url);
    }

    removeAllFontSheets() {
      this.fontSheets.forEach((link) => {
        if (link.parentNode) link.parentNode.removeChild(link);
      });
      this.fontSheets.clear();
      this.fontRefs.clear();
      this.compositionSheets.clear();
    }

    // ---------------------------------------------------------------------
    // Recording setters: every bridge mutation goes through these so the
    // original state can be restored exactly and the ledger stays complete.
    // ---------------------------------------------------------------------

    captureStyle(el) {
      let state = this.styleState.get(el);
      if (!state) {
        const snapshot = new Map();
        for (let i = 0; i < el.style.length; i += 1) {
          const prop = el.style[i];
          snapshot.set(prop, { value: el.style.getPropertyValue(prop), priority: el.style.getPropertyPriority(prop) });
        }
        state = { snapshot, raw: el.getAttribute('style'), cssText: el.style.cssText, props: new Map() };
        this.styleState.set(el, state);
      }
      return state;
    }

    // ledger:false marks bridge mechanics (wireframe transitions/order, asset
    // container layout) that are restored and stripped but not reported as CSS.
    setStyle(el, prop, value, { important = true, ledger = true } = {}) {
      if (!el || !el.style) return false;
      const custom = prop.startsWith('--');
      if (!custom && !cssSupports(prop, value)) return false;
      const state = this.captureStyle(el);
      const priority = important ? 'important' : '';
      if (el.style.getPropertyValue(prop) !== String(value) || el.style.getPropertyPriority(prop) !== priority) {
        el.style.setProperty(prop, value, priority);
      }
      if (custom && el.style.getPropertyValue(prop) === '' && value !== '') return false;
      state.props.set(prop, { value: String(value), ledger });
      this.styledElements.add(el);
      return true;
    }

    clearStyle(el, prop) {
      const state = this.styleState.get(el);
      if (!state || !state.props.has(prop)) return;
      const original = state.snapshot.get(prop);
      if (original) el.style.setProperty(prop, original.value, original.priority);
      else el.style.removeProperty(prop);
      state.props.delete(prop);
      if (state.props.size === 0) {
        this.styledElements.delete(el);
        this.restoreStyleAttribute(el, state);
      }
    }

    // When nothing else changed the inline style, put back the author's exact attribute text.
    restoreStyleAttribute(el, state) {
      if (el.style.cssText !== state.cssText) return;
      // Reading the attribute first flushes Chromium's lazy CSSOM → attribute
      // sync; otherwise it can re-serialize an empty style="" after removal.
      el.getAttribute('style');
      if (state.raw === null) el.removeAttribute('style');
      else el.setAttribute('style', state.raw);
    }

    resetStyles(el) {
      const state = this.styleState.get(el);
      if (!state) return;
      Array.from(state.props.keys()).forEach((prop) => this.clearStyle(el, prop));
    }

    // Legacy token write. Returns the canonical (trimmed) value, or undefined when rejected.
    setToken(name, value) {
      const safe = safeCssString(value);
      if (typeof name !== 'string' || !TOKEN_NAME.test(name) || safe === undefined) return undefined;
      if (!this.setStyle(document.documentElement, name, safe, { important: false, ledger: false })) return undefined;
      this.tokenOverrides.set(name, safe);
      return safe;
    }

    // Removes Studio's override of a token: the root's original inline value (or its absence) comes back
    // exactly, because the original was captured once, before the first write. True when something was removed.
    removeToken(name) {
      if (!this.tokenOverrides.has(name)) return false;
      this.clearStyle(document.documentElement, name);
      this.tokenOverrides.delete(name);
      return true;
    }

    // Text slot: a leaf element's whole content, else its first non-empty text node.
    textEditable(el) {
      const state = this.textState.get(el);
      if (state) return state.leaf || state.node.parentNode === el;
      return el.children.length === 0 || !!firstTextNode(el);
    }

    captureText(el) {
      let state = this.textState.get(el);
      if (!state) {
        if (el.children.length === 0) {
          state = { leaf: true, nodes: Array.from(el.childNodes), original: el.textContent };
        } else {
          const node = firstTextNode(el);
          if (!node) return null;
          state = { leaf: false, node, originalData: node.data, original: node.data.trim() };
        }
        this.textState.set(el, state);
      }
      return state;
    }

    setText(el, text) {
      const state = this.captureText(el);
      if (!state) return false;
      if (state.leaf) {
        el.textContent = text;
      } else {
        // Keep the surrounding whitespace so inline siblings stay spaced.
        const lead = state.originalData.match(/^\s*/)[0];
        const trail = state.originalData.match(/\s*$/)[0];
        state.node.data = lead + text + trail;
      }
      this.textElements.add(el);
      return true;
    }

    restoreText(el) {
      const state = this.textState.get(el);
      if (!state || !this.textElements.has(el)) return;
      if (state.leaf) {
        while (el.firstChild) el.removeChild(el.firstChild);
        state.nodes.forEach((node) => el.appendChild(node));
      } else {
        state.node.data = state.originalData;
      }
      this.textElements.delete(el);
    }

    resetElement(el) {
      this.removePlacedAsset(el);
      this.resetStyles(el);
      this.restoreText(el);
      this.restoreAttrs(el);
    }

    // Attribute writes (legacy <img src>), original captured once per attribute.
    setAttr(el, name, value) {
      let state = this.attrState.get(el);
      if (!state) {
        state = new Map();
        this.attrState.set(el, state);
      }
      if (!state.has(name)) state.set(name, el.getAttribute(name));
      if (value === null) el.removeAttribute(name);
      else el.setAttribute(name, value);
      this.attrElements.add(el);
    }

    restoreAttrs(el) {
      const state = this.attrState.get(el);
      if (!state || !this.attrElements.has(el)) return;
      state.forEach((original, name) => {
        if (original === null) el.removeAttribute(name);
        else el.setAttribute(name, original);
      });
      this.attrElements.delete(el);
    }

    // Current and original values of an element's text slot (trimmed).
    currentText(el) {
      const state = this.textState.get(el);
      if (state && !state.leaf) return state.node.data.trim();
      if (el.children.length === 0) return el.textContent.trim();
      const node = firstTextNode(el);
      return node ? node.data.trim() : collapse(el.textContent);
    }

    originalText(el) {
      const state = this.textState.get(el);
      return state ? state.original.trim() : this.currentText(el);
    }

    // ---------------------------------------------------------------------
    // ChangeLedger
    // ---------------------------------------------------------------------

    declarationsFor(el) {
      const declarations = {};
      const state = this.styleState.get(el);
      if (state) {
        state.props.forEach((entry, prop) => {
          if (entry.ledger) declarations[prop] = entry.value;
        });
      }
      return declarations;
    }

    textChanged(el) {
      return this.textElements.has(el) && this.currentText(el) !== this.originalText(el);
    }

    isDirty(record) {
      return Object.keys(this.declarationsFor(record.element)).length > 0 || this.textChanged(record.element);
    }

    noteChange(record) {
      if (this.isDirty(record)) this.changeOrder.add(record.id);
      else this.changeOrder.delete(record.id);
    }

    buildLedger() {
      const targets = [];
      Array.from(this.changeOrder).forEach((id) => {
        const record = this.targets.get(id);
        if (!record || !this.isDirty(record)) {
          this.changeOrder.delete(id);
          return;
        }
        const el = record.element;
        targets.push({
          targetId: record.id,
          selector: this.selectorFor(record),
          stable: record.stable,
          name: record.name,
          role: record.role,
          declarations: this.declarationsFor(el),
          text: this.textChanged(el) ? this.currentText(el) : null,
          originalText: this.originalText(el),
          html: this.cleanHTML(el)
        });
      });
      return {
        tokens: Object.fromEntries(this.tokenOverrides),
        targets,
        structure: this.buildStructure(),
        imports: Array.from(this.fontSheets.keys())
      };
    }

    // outerHTML with bridge state removed: auto data-design-* attributes,
    // bridge inline overrides (author style restored), overlay nodes. Current text kept.
    cleanHTML(el) {
      const clone = el.cloneNode(true);
      const originals = [el].concat(Array.from(el.querySelectorAll('*')));
      const copies = [clone].concat(Array.from(clone.querySelectorAll('*')));
      originals.forEach((original, index) => {
        const copy = copies[index];
        if (!copy) return;
        const state = this.styleState.get(original);
        if (state && state.props.size && copy.style) {
          state.props.forEach((entry, prop) => {
            const before = state.snapshot.get(prop);
            if (before) copy.style.setProperty(prop, before.value, before.priority);
            else copy.style.removeProperty(prop);
          });
          this.restoreStyleAttribute(copy, state);
        }
        const added = this.bridgeAttrs.get(original);
        if (added) {
          added.forEach((value, name) => {
            if (original.getAttribute(name) === value) copy.removeAttribute(name);
          });
        }
        Array.from(copy.attributes).forEach((attr) => {
          const short = this.abbreviateDataUrls(attr.name, attr.value);
          if (short !== attr.value) copy.setAttribute(attr.name, short);
        });
      });
      Array.from(clone.querySelectorAll(OVERLAY_SELECTOR)).forEach((node) => node.remove());
      return clone.outerHTML;
    }

    // Long data: URLs in the ledger html: URL-bearing attributes (the whole
    // value, each srcset candidate separately) and url(...) in style. Text
    // attributes such as title are never touched.
    abbreviateDataUrls(name, value) {
      if (value.length <= DATA_URL_ABBREVIATE_OVER || !value.includes('data:')) return value;
      const short = (url) => {
        if (url.length <= DATA_URL_ABBREVIATE_OVER) return url;
        const comma = url.indexOf(',');
        return `${url.slice(0, comma >= 0 && comma < 100 ? comma + 1 : 5)}…(${url.length} bytes)`;
      };
      const lower = name.toLowerCase();
      if (URL_ATTRIBUTES.has(lower)) return /^\s*data:/i.test(value) ? short(value.trim()) : value;
      if (lower === 'srcset') {
        return value.replace(/data:[^\s]+/gi, (token) => {
          const trailing = token.endsWith(',') ? ',' : '';
          return short(trailing ? token.slice(0, -1) : token) + trailing;
        });
      }
      if (lower === 'style') return value.replace(DATA_URL_IN_ATTRIBUTE, short);
      return value;
    }

    // Author ids → attribute selector; auto targets → #id or a short
    // tag.class:nth-of-type path (at least 4 entries, anchored at the nearest
    // unique id). The selector is verified: querySelectorAll(selector) must be
    // exactly this element, otherwise the path is extended up to the body.
    selectorFor(record) {
      if (record.stable) return designIdSelector(record.id);
      return this.uniqueSelector(record.element);
    }

    uniqueSelector(el) {
      const cached = this.selectorCache.get(el);
      if (cached && cached.version === this.domVersion) return cached.selector;
      const selector = this.computeSelector(el);
      this.selectorCache.set(el, { version: this.domVersion, selector });
      return selector;
    }

    computeSelector(el) {
      const unique = (selector) => {
        try {
          const found = document.querySelectorAll(selector);
          return found.length === 1 && found[0] === el;
        } catch (e) {
          return false;
        }
      };
      if (el.id && unique(`#${cssEscape(el.id)}`)) return `#${cssEscape(el.id)}`;

      // Steps from the element up to (not including) an anchor: a unique id, or the body.
      const chain = [];
      let anchor = null;
      let node = el;
      while (node && node.nodeType === 1 && node !== document.documentElement) {
        if (node === document.body) {
          anchor = 'body';
          break;
        }
        if (node !== el && node.id) {
          const idSelector = `#${cssEscape(node.id)}`;
          let count = 0;
          try {
            count = document.querySelectorAll(idSelector).length;
          } catch (e) {}
          if (count === 1) {
            anchor = idSelector;
            break;
          }
        }
        chain.unshift(this.selectorStep(node));
        node = node.parentElement;
      }

      // Top-down entries; try the short form first and extend until unique.
      const entries = (anchor && anchor !== 'body' ? [anchor] : []).concat(chain);
      let candidate = '';
      for (let count = Math.min(4, entries.length); count <= entries.length; count += 1) {
        candidate = entries.slice(-count).join(' > ');
        if (unique(candidate)) return candidate;
      }
      if (anchor === 'body') {
        candidate = ['body'].concat(entries).join(' > ');
      }
      return candidate;
    }

    selectorStep(node) {
      const tag = node.localName;
      const classes = Array.from(node.classList || []).map((cls) => `.${cssEscape(cls)}`).join('');
      let index = 1;
      for (let sibling = node.previousElementSibling; sibling; sibling = sibling.previousElementSibling) {
        if (sibling.localName === tag) index += 1;
      }
      return `${tag}${classes}:nth-of-type(${index})`;
    }

    // ---------------------------------------------------------------------
    // Target discovery and manifests
    // ---------------------------------------------------------------------

    // An attribute is bridge-owned only while it still holds the value the bridge
    // wrote; an author or framework that overwrites it takes it over.
    isBridgeAttr(el, name) {
      const added = this.bridgeAttrs.get(el);
      return !!added && added.has(name) && el.getAttribute(name) === added.get(name);
    }

    authorAttr(el, name) {
      return this.isBridgeAttr(el, name) ? null : el.getAttribute(name);
    }

    setBridgeAttr(el, name, value) {
      if (el.hasAttribute(name) && !this.isBridgeAttr(el, name)) return;
      let added = this.bridgeAttrs.get(el);
      if (!added) {
        added = new Map();
        this.bridgeAttrs.set(el, added);
      }
      added.set(name, value);
      if (el.getAttribute(name) !== value) el.setAttribute(name, value); // never rewrite an unchanged value
    }

    recordFor(el) {
      const id = this.elementIds.get(el);
      const record = id !== undefined ? this.targets.get(id) : null;
      return record && record.element === el ? record : null;
    }

    // Role/name/kind/constraints may be refreshed; original text/style never are.
    refreshRecord(record) {
      const el = record.element;
      const tag = el.localName;
      record.role = this.authorAttr(el, 'data-design-role') || record.role || this.inferRoleFromElement(el);
      record.name = this.authorAttr(el, 'data-design-name') || record.name || this.generateFriendlyName(el, record.role);
      const kindAttr = el.getAttribute('data-design-kind');
      record.kind = kindAttr === 'image' || kindAttr === 'text' ? kindAttr
        : (['img', 'svg', 'picture', 'canvas', 'video'].includes(tag) ? 'image' : 'text');
      record.fontWeights = parseWeights(el.getAttribute('data-design-weights'));
    }

    registerAuthor(el) {
      const id = el.getAttribute('data-design-id');
      if (!isNonEmptyString(id)) return false;
      const known = this.recordFor(el);
      if (known && known.id === id) {
        this.refreshRecord(known);
        return false;
      }
      const existing = this.targets.get(id);
      if (existing && existing.element !== el && existing.element.isConnected) {
        if (!this.warnedDuplicates.has(id)) {
          this.warnedDuplicates.add(id);
          console.warn(`[FontKitBridge] Duplicate data-design-id "${id}" ignored (Spec §4.1).`);
        }
        return false;
      }
      if (existing && existing.element !== el) this.stashLost(existing);
      if (known) this.targets.delete(known.id);
      const record = { id, element: el, stable: true, role: null, name: null, kind: 'text', fontWeights: null };
      this.refreshRecord(record);
      this.targets.set(id, record);
      this.elementIds.set(el, id);
      if (known) this.promote(known, record);
      const lost = this.lost.get(id);
      if (lost && lost.element !== el) {
        this.lost.delete(id);
        this.reapplyFrom(record, lost.element);
      }
      return true;
    }

    // The same element was registered under another id (an auto target that got an author data-design-id).
    // Its edits stay with the element: the originals (style, text, moves) are keyed by element and are never
    // captured again, so only what is keyed by id moves, and the manifest names the id it replaced.
    promote(old, record) {
      record.previousId = old.id;
      this.changeOrder = new Set(Array.from(this.changeOrder).map((id) => (id === old.id ? record.id : id)));
      if (this.fontRefs.has(old.id)) {
        this.fontRefs.set(record.id, this.fontRefs.get(old.id));
        this.fontRefs.delete(old.id);
      }
      if (this.selectedId === old.id) this.selectedId = record.id;
      if (this.hoverId === old.id) this.hoverId = record.id;
      this.reapplyLog.delete(old.id);
      // An author id now names the element: the role and name the bridge wrote for the auto target go, so the
      // markup is back to what the author wrote (and the leftovers are not mistaken for author hints later).
      if (record.stable) this.dropBridgeAttrs(record.element, ['data-design-role', 'data-design-name']);
    }

    dropBridgeAttrs(el, names) {
      const added = this.bridgeAttrs.get(el);
      names.forEach((name) => {
        if (!this.isBridgeAttr(el, name)) return;
        el.removeAttribute(name);
        added.delete(name);
      });
    }

    // An author target lost its data-design-id (an app update removed it). The edit follows the element, as for a
    // promotion: the originals are keyed by element and stay, the record moves to a fresh auto id, and the manifest
    // names the author id it replaced so Studio can follow. Targets that were edited, selected by role or semantic
    // stay ordinary targets; others are kept for arrangement only, like any other sibling.
    demote(old) {
      const el = old.element;
      this.targets.delete(old.id);
      const ordinary = !!this.authorAttr(el, 'data-design-role') || this.isSemanticElement(el) || this.isDirty(old);
      const record = this.registerAuto(el, !ordinary);
      this.promote(old, record);
    }

    // A re-render removed an author target that had overrides: remember its
    // element so the replacement (same data-design-id) can get them back.
    stashLost(record) {
      if (!record.stable || record.element.isConnected || !this.isDirty(record)) return;
      this.lost.set(record.id, { element: record.element, at: Date.now() });
      if (this.lost.size > LOST_MAX) this.lost.delete(this.lost.keys().next().value);
    }

    // Copies the ledger-visible overrides of a removed element onto its
    // replacement. At most REAPPLY_MAX times per target and REAPPLY_WINDOW_MS, so
    // an app that re-renders on every change cannot trap the bridge in a loop.
    reapplyFrom(record, oldEl) {
      const now = Date.now();
      const history = (this.reapplyLog.get(record.id) || []).filter((at) => now - at < REAPPLY_WINDOW_MS);
      if (history.length >= REAPPLY_MAX) {
        this.reapplyLog.set(record.id, history);
        if (!this.warnedLoops.has(record.id)) {
          this.warnedLoops.add(record.id);
          console.warn(`[FontKitBridge] "${record.id}" keeps being re-rendered; not re-applying its overrides again.`);
        }
        return;
      }
      history.push(now);
      this.reapplyLog.set(record.id, history);
      this.warnedLoops.delete(record.id);

      const el = record.element;
      const declarations = this.declarationsFor(oldEl);
      Object.keys(declarations).forEach((prop) => this.setStyle(el, prop, declarations[prop]));
      if (this.textChanged(oldEl) && this.textEditable(el)) this.setText(el, this.currentText(oldEl));
      this.noteChange(record);
    }

    registerAuto(el, arrangementOnly = false) {
      const role = this.authorAttr(el, 'data-design-role') || this.inferRoleFromElement(el);
      let id;
      do {
        this.autoCounter += 1;
        id = `auto:${el.localName}:${role}:${this.autoCounter}`;
      } while (this.targets.has(id));
      const name = this.authorAttr(el, 'data-design-name') || this.generateFriendlyName(el, role);
      this.setBridgeAttr(el, 'data-design-id', id);
      this.setBridgeAttr(el, 'data-design-role', role);
      this.setBridgeAttr(el, 'data-design-name', name);
      const record = { id, element: el, stable: false, role, name, kind: 'text', fontWeights: null, arrangementOnly };
      this.refreshRecord(record);
      this.targets.set(id, record);
      this.elementIds.set(el, id);
      return record;
    }

    ensureTarget(el) {
      return this.recordFor(el) || (el.hasAttribute('data-design-id') && !this.isBridgeAttr(el, 'data-design-id')
        && this.registerAuthor(el) && this.recordFor(el)) || this.registerAuto(el);
    }

    isExcluded(el) {
      return !!el.closest(EXCLUDED_SELECTOR);
    }

    // Returns true when the set of targets changed.
    discoverTargets() {
      if (typeof document === 'undefined') return false;
      let changed = false;

      const expired = Date.now() - LOST_TTL_MS;
      this.lost.forEach((entry, id) => {
        if (entry.at < expired) this.lost.delete(id);
      });
      for (const [id, record] of this.targets) {
        if (!record.element.isConnected) {
          this.stashLost(record);
          this.targets.delete(id);
          changed = true;
        }
      }

      // An author id the element no longer carries: the same element, now under an auto id. (A different author
      // id is a promotion, handled by registerAuthor below.)
      Array.from(this.targets.values()).forEach((record) => {
        const el = record.element;
        if (!record.stable || !el.isConnected) return;
        if (isNonEmptyString(el.getAttribute('data-design-id')) && !this.isBridgeAttr(el, 'data-design-id')) return;
        this.demote(record);
        changed = true;
      });

      // 1. Author data-design-id elements (highest authority)
      document.querySelectorAll('[data-design-id]').forEach((el) => {
        if (this.isBridgeAttr(el, 'data-design-id') || this.isExcluded(el)) return;
        if (this.registerAuthor(el)) changed = true;
      });

      // 2. Role-only author hints and zero-hook semantic auto-discovery
      if (this.options.autoDiscover !== false) {
        const selectors = ['[data-design-role]'];
        if (this.options.autoDiscoverSemantic !== false) selectors.push(...SEMANTIC_SELECTORS);
        let candidates = [];
        try {
          candidates = Array.from(document.querySelectorAll(selectors.join(', ')));
        } catch (e) {}
        candidates.forEach((el) => {
          const known = this.recordFor(el);
          if (known) {
            // Semantic, or an author-supplied role: an ordinary target after all.
            // (The bridge's own data-design-role attribute does not count.)
            if (known.arrangementOnly && (this.authorAttr(el, 'data-design-role') || this.isSemanticElement(el))) {
              known.arrangementOnly = false;
            }
            return;
          }
          if (this.isExcluded(el)) return;
          if (el.hasAttribute('data-design-id') && !this.isBridgeAttr(el, 'data-design-id')) return;
          // Matched only by a role the bridge wrote itself (an arrangement-only element that left the page and
          // came back): not a hint. The sibling pass below registers it again if it still needs an id.
          if (!this.authorAttr(el, 'data-design-role') && !this.isSemanticElement(el)) return;
          this.registerAuto(el);
          changed = true;
        });
      }

      // Every sibling of a target is a target too (arrangement needs an id for each).
      const parents = new Set();
      Array.from(this.targets.values()).forEach((record) => {
        const parent = record.element.parentElement;
        if (!parent || parents.has(parent)) return;
        parents.add(parent);
        this.childElements(parent).forEach((child) => {
          if (this.registerSibling(child)) changed = true;
        });
      });
      return changed;
    }

    // Registers an element as target if it is not one (author id if it has one).
    // Returns true when a new record was created.
    registerSibling(el) {
      if (this.recordFor(el) || this.isExcluded(el)) return false;
      if (el.hasAttribute('data-design-id') && !this.isBridgeAttr(el, 'data-design-id')) return this.registerAuthor(el);
      // Only registered for arrangement (it has no author id, role or semantic
      // selector): addressable by id, but never hovered or clicked in the page.
      const ordinary = !!this.authorAttr(el, 'data-design-role') || this.isSemanticElement(el);
      this.registerAuto(el, !ordinary);
      return true;
    }

    isSemanticElement(el) {
      if (this.options.autoDiscover === false || this.options.autoDiscoverSemantic === false) return false;
      try {
        return el.matches(SEMANTIC_SELECTORS.join(', '));
      } catch (e) {
        return false;
      }
    }

    // Debounced rediscovery. `fast` (a re-render removed an element that has
    // overrides) shortens the wait so the replacement is restyled quickly.
    scheduleDiscovery(fast = false) {
      const now = Date.now();
      if (!this.discoveryTimer) this.discoveryFirstQueued = now;
      if (fast) this.discoveryFast = true;
      clearTimeout(this.discoveryTimer);
      let wait = now - this.discoveryFirstQueued >= DISCOVERY_MAX_WAIT_MS ? 0
        : (this.discoveryFast ? REAPPLY_DEBOUNCE_MS : DISCOVERY_DEBOUNCE_MS);
      if (this.discoveryBackoff) wait = Math.max(wait, this.discoveryBackoff);
      this.discoveryTimer = setTimeout(() => {
        this.discoveryTimer = null;
        this.discoveryFast = false;
        if (this.disposed) return;
        this.noteDiscoveryRun();
        if (this.discoverTargets() && this.studioSource) {
          this.post({ type: 'design:targets', targets: this.getTargetManifest(false) });
        }
        this.syncSelection();
      }, wait);
    }

    // An app that mutates the page in response to the bridge's own attribute
    // writes can loop with it. When rediscovery fires more than STORM_RUNS times
    // in STORM_WINDOW_MS the wait doubles (250 ms up to 8 s) for as long as the
    // storm lasts; a quiet period resets it.
    noteDiscoveryRun() {
      const now = Date.now();
      const gap = now - this.lastDiscoveryRun;
      this.lastDiscoveryRun = now;
      this.discoveryRuns = this.discoveryRuns.filter((at) => now - at < STORM_WINDOW_MS);
      this.discoveryRuns.push(now);
      if (this.discoveryRuns.length > STORM_RUNS || (this.discoveryBackoff && gap < this.discoveryBackoff * 2)) {
        if (!this.discoveryBackoff && !this.warnedStorm) {
          this.warnedStorm = true;
          console.warn('[FontKitBridge] The page keeps mutating in response to rediscovery; slowing down.');
        }
        this.discoveryBackoff = Math.min(this.discoveryBackoff ? this.discoveryBackoff * 2 : STORM_BACKOFF_START_MS, STORM_BACKOFF_MAX_MS);
      } else {
        this.discoveryBackoff = 0;
        this.warnedStorm = false;
      }
    }

    // After rediscovery: a selected target that is gone clears the selection; one
    // that a re-render replaced (same author id) stays selected on the new element.
    syncSelection() {
      if (!this.selectedId) return;
      const record = this.targets.get(this.selectedId);
      if (!record || !record.element.isConnected) {
        this.selectRecord(null, false);
        return;
      }
      if (record.element !== this.selectedElement) {
        this.selectedElement = record.element;
        if (this.resizeObserver) {
          this.resizeObserver.disconnect();
          this.resizeObserver.observe(record.element);
        }
      }
      this.scheduleBounds();
    }

    // Exact lookup; one synchronous rediscovery covers just-inserted elements.
    findTarget(id) {
      if (typeof id !== 'string') return null;
      let record = this.targets.get(id);
      if (record && !record.element.isConnected) record = null;
      if (!record) {
        this.discoverTargets();
        record = this.targets.get(id) || null;
      }
      return record;
    }

    closestTarget(node) {
      let el = node && node.nodeType === 1 ? node : node && node.parentElement;
      while (el) {
        const record = this.recordFor(el);
        if (record && !record.arrangementOnly) return record;
        el = el.parentElement;
      }
      return null;
    }

    editableFor(record) {
      const el = record.element;
      if (record.kind === 'image') {
        return { text: false, typography: false, color: el.localName === 'svg', alignment: false };
      }
      return { text: this.textEditable(el), typography: true, color: true, alignment: true };
    }

    manifestFor(record, context) {
      const el = record.element;
      const computed = window.getComputedStyle(el);
      const manifest = {
        id: record.id,
        role: record.role,
        name: record.name,
        kind: record.kind,
        tag: el.localName,
        stable: record.stable,
        selector: this.selectorFor(record),
        editable: this.editableFor(record),
        arrangement: this.arrangementFor(record, context || this.manifestContext()),
        text: collapse(el.textContent).slice(0, 200),
        computed: {
          fontFamily: computed.fontFamily,
          fontSize: computed.fontSize,
          fontWeight: computed.fontWeight,
          lineHeight: computed.lineHeight,
          letterSpacing: computed.letterSpacing,
          color: computed.color,
          textAlign: computed.textAlign,
          textTransform: computed.textTransform
        }
      };
      if (record.arrangementOnly) manifest.arrangementOnly = true;
      if (record.previousId) manifest.previousId = record.previousId;
      if (record.fontWeights) manifest.constraints = { fontWeights: record.fontWeights.slice() };
      return manifest;
    }

    getTargetManifest(rediscover = true) {
      if (rediscover) this.discoverTargets();
      const context = this.manifestContext(true);
      return Array.from(this.targets.values()).map((record) => this.manifestFor(record, context));
    }

    // ---------------------------------------------------------------------
    // Arrangement: siblings, candidate containers, framework detection
    // ---------------------------------------------------------------------

    isArrangeable(el) {
      return el.nodeType === 1 && !el.matches(NON_ARRANGEABLE) && !this.isOverlayNode(el)
        && !el.classList.contains(PLACED_ASSET_CLASS);
    }

    childElements(parent) {
      return Array.from(parent.children).filter((child) => this.isArrangeable(child));
    }

    isFlexOrGrid(parent) {
      const display = window.getComputedStyle(parent).display;
      return display === 'flex' || display === 'inline-flex' || display === 'grid' || display === 'inline-grid';
    }

    // Siblings in the order they are laid out: DOM order, or for flex/grid parents
    // the visual order (stable sort by the computed CSS `order`).
    orderedSiblings(parent) {
      const kids = this.childElements(parent);
      if (kids.length < 2 || !this.isFlexOrGrid(parent)) return kids;
      return kids
        .map((el, index) => ({ el, index, order: parseInt(window.getComputedStyle(el).order, 10) || 0 }))
        .sort((a, b) => a.order - b.order || a.index - b.index)
        .map((entry) => entry.el);
    }

    // 'react' | 'vue' | 'svelte' | 'unknown' | null for the element or its nearest managed ancestor.
    frameworkOf(el, memo = new Map()) {
      if (!el || el.nodeType !== 1) return null;
      if (memo.has(el)) return memo.get(el);
      let found = null;
      let keys = [];
      try {
        keys = Object.getOwnPropertyNames(el);
      } catch (e) {}
      for (const key of keys) {
        if (key.startsWith('__reactFiber$') || key.startsWith('__reactProps$') || key.startsWith('__reactContainer$')
          || key === '_reactRootContainer') {
          found = 'react';
        } else if (key === '__vue__' || key === '__vueParentComponent' || key === '__vue_app__') {
          found = 'vue';
        } else if (key.startsWith('__svelte')) {
          found = 'svelte';
        }
        if (found) break;
      }
      if (!found && el.hasAttribute('ng-version')) found = 'unknown';
      if (!found) found = this.frameworkOf(el.parentElement, memo);
      memo.set(el, found);
      return found;
    }

    // Stable key of a container: its author data-design-id, else 'container:<n>'.
    containerKey(el) {
      const author = el.getAttribute('data-design-id');
      if (author && !this.isBridgeAttr(el, 'data-design-id')) return author;
      let key = this.containerKeys.get(el);
      if (!key) {
        this.containerCounter += 1;
        key = `container:${this.containerCounter}`;
        this.containerKeys.set(el, key);
        this.containerByKey.set(key, el);
      }
      return key;
    }

    resolveContainer(key) {
      if (typeof key !== 'string' || !key) return null;
      const mapped = this.containerByKey.get(key);
      if (mapped) return mapped.isConnected ? mapped : null;
      const record = this.targets.get(key);
      if (record && record.stable && record.element.isConnected) return record.element;
      const found = Array.from(document.querySelectorAll('[data-design-id]')).find((el) =>
        !this.isBridgeAttr(el, 'data-design-id') && el.getAttribute('data-design-id') === key);
      return found || null;
    }

    // data-design-name, aria-label, first heading text (<= 40 chars), #id, tag.class.
    containerName(el) {
      const short = (text) => {
        const clean = collapse(text);
        return clean.length > CONTAINER_NAME_MAX ? `${clean.slice(0, CONTAINER_NAME_MAX - 1)}…` : clean;
      };
      const author = this.authorAttr(el, 'data-design-name');
      if (author) return author;
      const aria = short(el.getAttribute('aria-label') || '');
      if (aria) return aria;
      const heading = el.querySelector('h1, h2, h3, h4, h5, h6');
      const headingText = heading ? short(heading.textContent) : '';
      if (headingText) return headingText;
      if (el.id) return `#${el.id}`;
      const cls = (el.classList && el.classList[0]) || '';
      return `${el.localName}${cls ? `.${cls}` : ''}`;
    }

    containerSelector(el) {
      const author = el.getAttribute('data-design-id');
      if (author && !this.isBridgeAttr(el, 'data-design-id')) return designIdSelector(author);
      return this.uniqueSelector(el);
    }

    nameOfElement(el) {
      const record = this.recordFor(el);
      return record ? record.name : this.generateFriendlyName(el, this.inferRoleFromElement(el));
    }

    // Candidate destinations, in document order: order containers plus every
    // element that is the parent of two or more registered targets.
    candidateContainers() {
      const counts = new Map();
      this.targets.forEach((record) => {
        const parent = record.element.parentElement;
        if (record.element.isConnected && parent) counts.set(parent, (counts.get(parent) || 0) + 1);
      });
      const set = new Set();
      document.querySelectorAll('[data-design-order-container="true"]').forEach((el) => {
        if (!this.isExcluded(el) && !NO_CHILDREN.has(el.localName)) set.add(el);
      });
      counts.forEach((count, parent) => {
        if (count >= 2 && !NO_CHILDREN.has(parent.localName) && !this.isOverlayNode(parent)) set.add(parent);
      });
      return Array.from(set)
        .sort((a, b) => (a.compareDocumentPosition(b) & 4 ? -1 : 1))
        .map((el) => ({ el, key: this.containerKey(el), name: this.containerName(el) }));
    }

    // Bulk manifests (design:ready, design:targets) carry no candidate containers.
    manifestContext(bulk = false) {
      return {
        containers: bulk ? [] : this.candidateContainers(),
        frameworks: new Map(),
        siblingLists: new Map(),
        parents: new Map(),
        bulk
      };
    }

    arrangementFor(record, context) {
      const el = record.element;
      const parent = el.parentElement;
      let list = parent ? context.siblingLists.get(parent) : null;
      if (parent && !list) {
        list = [];
        this.orderedSiblings(parent).forEach((child) => {
          this.registerSibling(child);
          const sibling = this.recordFor(child);
          if (sibling) list.push({ id: sibling.id, name: sibling.name, tag: child.localName });
        });
        context.siblingLists.set(parent, list);
      }
      list = list || [];
      let index = list.findIndex((entry) => entry.id === record.id);
      const missing = index < 0;
      if (missing) index = list.length;
      let holder = parent ? context.parents.get(parent) : null;
      if (parent && !holder) {
        holder = {
          containerKey: this.containerKey(parent),
          containerName: this.containerName(parent),
          containerSelector: this.containerSelector(parent),
          cssOrderAvailable: this.isFlexOrGrid(parent)
        };
        context.parents.set(parent, holder);
      }
      const arrangement = {
        containerKey: holder ? holder.containerKey : null,
        containerName: holder ? holder.containerName : '',
        containerSelector: holder ? holder.containerSelector : '',
        index,
        count: list.length + (missing ? 1 : 0),
        cssOrderAvailable: holder ? holder.cssOrderAvailable : false,
        frameworkManaged: this.frameworkOf(el, context.frameworks)
      };
      // Bulk manifests (design:ready, design:targets) carry neither siblings nor
      // containers: both grow with the page size per target.
      if (!context.bulk) {
        arrangement.siblings = list.map((entry) => ({ ...entry }));
        if (missing) arrangement.siblings.push({ id: record.id, name: record.name, tag: el.localName });
        arrangement.containers = context.containers.filter((c) => !el.contains(c.el)).map((c) => ({ key: c.key, name: c.name }));
      }
      return arrangement;
    }

    getCurrentTokens() {
      const root = document.documentElement;
      const names = new Set(LEGACY_TOKEN_KEYS);
      const isRootSelector = (selector) => selector.split(',').some((part) => /^\s*(?::root|html)\s*$/i.test(part));
      const collect = (rules) => {
        Array.from(rules || []).forEach((rule) => {
          if (rule.style && rule.selectorText && isRootSelector(rule.selectorText)) {
            for (let i = 0; i < rule.style.length; i += 1) {
              if (rule.style[i].startsWith('--')) names.add(rule.style[i]);
            }
          }
          if (rule.cssRules) collect(rule.cssRules);
        });
      };
      Array.from(document.styleSheets || []).forEach((sheet) => {
        try {
          collect(sheet.cssRules);
        } catch (e) {} // cross-origin stylesheet
      });
      for (let i = 0; i < root.style.length; i += 1) {
        if (root.style[i].startsWith('--')) names.add(root.style[i]);
      }
      Object.keys(this.options.tokens || {}).forEach((name) => names.add(name));

      const rootStyle = window.getComputedStyle(root);
      const tokens = {};
      names.forEach((name) => {
        const value = rootStyle.getPropertyValue(name).trim();
        if (value) tokens[name] = value;
      });
      return tokens;
    }

    inferRoleFromElement(el) {
      const tag = el.tagName.toLowerCase();
      const cls = (el.getAttribute('class') || '').toLowerCase();
      const id = (el.id || '').toLowerCase();

      if (tag === 'img' || tag === 'svg' || tag === 'picture' || cls.includes('logo') || cls.includes('mark') || cls.includes('icon') || id.includes('logo')) {
        return 'image';
      }
      if (cls.includes('wordmark') || cls.includes('brand') || id.includes('brand')) {
        return 'wordmark';
      }
      if (tag === 'h1' || cls.includes('hero-title') || cls.includes('display')) {
        return 'display';
      }
      if (tag === 'h2' || cls.includes('title') || cls.includes('heading')) {
        return 'title';
      }
      if (tag === 'h3' || tag === 'h4') {
        return 'subhead';
      }
      if (cls.includes('tagline') || cls.includes('deck') || cls.includes('lead') || cls.includes('editorial') || cls.includes('narrative')) {
        return 'editorial';
      }
      if (cls.includes('badge') || cls.includes('chip') || cls.includes('pill') || cls.includes('tag')) {
        return 'badge';
      }
      if (cls.includes('stat') || cls.includes('metric') || cls.includes('kpi') || cls.includes('counter')) {
        return 'stat';
      }
      if (tag === 'button' || cls.includes('btn')) {
        return 'button';
      }
      if (tag === 'p') {
        return 'body';
      }
      return 'generic';
    }

    generateFriendlyName(el, role) {
      const text = collapse(el.textContent);
      const tag = el.tagName.toUpperCase();
      if (text.length > 0 && text.length <= 25) {
        return `${tag}: "${text}"`;
      }
      if (text.length > 25) {
        return `${tag}: "${text.slice(0, 22)}…"`;
      }
      if (el.getAttribute('alt')) {
        return `Image: ${el.getAttribute('alt')}`;
      }
      return `${role.toUpperCase()} (${tag})`;
    }

    // ---------------------------------------------------------------------
    // Hover, selection, mode, bounds
    // ---------------------------------------------------------------------

    isSelecting() {
      return this.mode === 'select' && this.options.enableClickToSelect !== false && this.studioAlive();
    }

    handlePointerMove(e) {
      if (!this.isSelecting()) return;
      this.pointer = { x: e.clientX, y: e.clientY, target: e.target };
      if (this.hoverFrame) return;
      this.hoverFrame = requestAnimationFrame(() => {
        this.hoverFrame = 0;
        const point = this.pointer;
        if (!point || !this.isSelecting()) return;
        const hit = document.elementFromPoint(point.x, point.y) || point.target;
        const record = this.isOverlayNode(hit) ? null : this.closestTarget(hit);
        this.setHover(record ? record.id : null);
      });
    }

    // Emits design:hover only when the logical target changes.
    setHover(id) {
      if (id === this.hoverId || !this.isSelecting()) return;
      this.hoverId = id;
      const record = id ? this.targets.get(id) : null;
      const message = { type: 'design:hover', targetId: record ? id : null };
      if (record) {
        message.rect = rectOf(record.element);
        message.name = record.name;
        message.role = record.role;
        this.showHoverOutline(record);
      } else {
        this.hideHoverOutline();
      }
      this.post(message);
    }

    handleDocumentClick(e) {
      if (!this.isSelecting()) return;
      const record = this.closestTarget(e.target);
      if (!record) return;
      // Select mode: the click selects instead of following links or firing app handlers.
      e.preventDefault();
      e.stopPropagation();
      this.selectRecord(record, false);
    }

    // design:mode {mode?: 'select' | 'interact', overlay?: boolean}. A malformed
    // field ignores the whole message.
    handleMode(data) {
      const { mode, overlay } = data;
      if (mode === undefined && overlay === undefined) return;
      if (mode !== undefined && mode !== 'select' && mode !== 'interact') return;
      if (overlay !== undefined && typeof overlay !== 'boolean') return;
      if (mode === 'interact') this.setHover(null);
      if (mode !== undefined) this.mode = mode;
      if (overlay !== undefined) {
        this.overlayRequested = overlay;
        this.updateOverlay();
      }
    }

    // An optional requestId (a short string) is echoed in the reply, so Studio can tell the answer to its own request
    // from a selection the user made in the page.
    handleSelect(targetId, requestId) {
      const echo = isNonEmptyString(requestId, 100) ? requestId : undefined;
      if (targetId === null || targetId === undefined) {
        this.selectRecord(null, false, echo);
        return;
      }
      this.selectRecord(this.findTarget(targetId), true, echo);
    }

    // Legacy: treated as design:select, with the old slot heuristics as a fallback.
    handleHighlight(data) {
      let record = this.findTarget(data.targetId);
      if (!record) {
        const el = this.resolveElementForSlot({ id: data.targetId, role: data.role || '', index: data.slotIndex });
        record = el ? this.ensureTarget(el) : null;
      }
      this.selectRecord(record, true);
    }

    clearSelection() {
      this.selectedId = null;
      this.selectedElement = null;
      this.lastBounds = null;
      if (this.resizeObserver) this.resizeObserver.disconnect();
      this.showActiveSelection(null);
    }

    selectRecord(record, scroll, requestId) {
      this.clearSelection();
      const echo = requestId === undefined ? {} : { requestId };
      if (!record) {
        this.post({ type: 'design:selected', targetId: null, ...echo });
        return;
      }
      const el = record.element;
      if (scroll) {
        const r = el.getBoundingClientRect();
        const offscreen = r.top < 0 || r.bottom > window.innerHeight || r.left < 0 || r.right > window.innerWidth;
        if (offscreen && typeof el.scrollIntoView === 'function') el.scrollIntoView({ block: 'nearest' });
      }
      this.selectedId = record.id;
      this.selectedElement = el;
      this.lastBounds = rectOf(el);
      if (this.resizeObserver) this.resizeObserver.observe(el);
      this.showActiveSelection(record);
      this.post({ type: 'design:selected', targetId: record.id, rect: this.lastBounds, target: this.manifestFor(record), ...echo });
    }

    scheduleBounds() {
      if (!this.selectedId || this.boundsFrame || typeof requestAnimationFrame === 'undefined') return;
      this.boundsFrame = requestAnimationFrame(() => {
        this.boundsFrame = 0;
        this.emitBounds();
      });
    }

    emitBounds() {
      if (!this.selectedId) return;
      let record = this.targets.get(this.selectedId);
      if (!record || !record.element.isConnected) {
        // Maybe a re-render replaced it (same author id): look before giving up.
        this.discoverTargets();
        record = this.targets.get(this.selectedId);
      }
      if (!record || !record.element.isConnected) {
        this.selectRecord(null, false);
        return;
      }
      if (record.element !== this.selectedElement) {
        this.selectedElement = record.element;
        if (this.resizeObserver) {
          this.resizeObserver.disconnect();
          this.resizeObserver.observe(record.element);
        }
      }
      const rect = rectOf(record.element);
      if (sameRect(rect, this.lastBounds)) return;
      this.lastBounds = rect;
      this.showActiveSelection(record);
      this.post({ type: 'design:bounds', targetId: record.id, rect });
    }

    // ---------------------------------------------------------------------
    // Legacy composition helpers (slots / layout / fontkit:change)
    // ---------------------------------------------------------------------

    handleFontKitChange(message) {
      if (isPlainObject(message.fonts)) {
        ['sans', 'serif', 'mono', 'display'].forEach((role) => {
          if (typeof message.fonts[role] === 'string') this.setToken(`--font-${role}`, message.fonts[role]);
        });
      }
      this.revision += 1;
      this.post({ type: 'fontkit:ack', revision: this.revision, changes: this.buildLedger() });
    }

    /**
     * Live Movement in Wireframe: Handles up & down movement of sections / elements.
     */
    applyWireframeMovement(orderList, slotsList = []) {
      if (!Array.isArray(orderList)) return;

      const orderContainers = document.querySelectorAll('[data-design-order-container="true"], main, #main-content-flow');

      orderContainers.forEach((container) => {
        const children = Array.from(container.children);
        if (children.length <= 1) return;
        this.captureOrder(container); // recorded in the ledger's structure, undone by reset

        // Apply smooth transition CSS (bridge mechanics: restored, not reported)
        children.forEach((child) => {
          if (!child.style.transition) {
            this.setStyle(child, 'transition', 'transform 0.3s cubic-bezier(0.2, 0.9, 0.3, 1), opacity 0.2s ease, order 0.25s ease', { important: false, ledger: false });
          }
        });

        // Map order based on slot index
        orderList.forEach((item, slotIndex) => {
          const slot = slotsList.find((s) => s && s.id !== undefined && s.id === item.id) || item;
          const matchedEl = this.resolveElementForSlot({ ...item, targetId: slot.targetId, type: slot.type });
          if (matchedEl && container.contains(matchedEl)) {
            let containerChild = matchedEl;
            while (containerChild.parentElement && containerChild.parentElement !== container) {
              containerChild = containerChild.parentElement;
            }

            if (containerChild && containerChild.parentElement === container) {
              this.setStyle(containerChild, 'order', String(slotIndex), { important: false, ledger: false });
            }
          }
        });

        // Physical DOM reordering if ordered items share direct parent
        const rankedChildren = [];
        children.forEach((child) => {
          const rawOrder = child.style.order;
          if (rawOrder !== '') {
            rankedChildren.push({ child, order: parseInt(rawOrder, 10) });
          }
        });

        if (rankedChildren.length > 1) {
          rankedChildren.sort((a, b) => a.order - b.order);
          this.domVersion += 1;
          rankedChildren.forEach((item) => {
            this.bridgeMoved.add(item.child);
            container.appendChild(item.child);
          });
        }
      });

      // Dispatch layout change event
      try {
        window.dispatchEvent(new CustomEvent('design:order-changed', { detail: { order: orderList } }));
      } catch (e) {}
    }

    /**
     * Resolves matching DOM element for a given slot (legacy heuristics).
     */
    resolveElementForSlot(slot) {
      if (!slot) return null;
      const role = String(slot.role || '').toLowerCase();
      const type = slot.type || 'text';

      // 1. Direct targetId / id match
      if (typeof slot.targetId === 'string') {
        const direct = this.findTarget(slot.targetId);
        if (direct) return direct.element;
      }
      if (typeof slot.id === 'string' && this.targets.has(slot.id)) {
        return this.targets.get(slot.id).element;
      }

      // 2. Direct data-design-id by role slug
      const slugId = role.replace(/[^a-z0-9]/g, '.');
      if (slugId) {
        const directSlug = document.querySelector(`[data-design-id*="${slugId}"]`);
        if (directSlug) return directSlug;
      }

      // 3. Image / Graphic / Mark
      if (type === 'image' || role.includes('image') || role.includes('graphic') || role.includes('mark') || role.includes('icon') || role.includes('logo')) {
        const imgTarget = document.querySelector('[data-design-id*="mark"], [data-design-id*="graphic"], [data-design-role="image"], img[data-design-id]');
        if (imgTarget) return imgTarget;
      }

      // 4. Wordmark / Brand
      if (role.includes('wordmark') || role.includes('brand')) {
        const brandEl = document.querySelector('[data-design-id*="brand.wordmark"], [data-design-id*="brand"], [data-design-role="display"]');
        if (brandEl) return brandEl;
      }

      // 5. Title / H1 / H2 / Hero / Heading / Display
      if (role === 'h1' || role === 'h2' || role.includes('title') || role.includes('hero') || role.includes('heading') || role.includes('display')) {
        const titleEl = document.querySelector('[data-design-id*="hero.title"], [data-design-id*="title"], [data-design-role="display"], h1, h2');
        if (titleEl) return titleEl;
      }

      // 6. Tagline / Editorial / Accent / Narrative / Quote
      if (role.includes('tagline') || role.includes('editorial') || role.includes('accent') || role.includes('narrative') || role.includes('quote')) {
        const narrativeEl = document.querySelector('[data-design-id*="tagline"], [data-design-id*="narrative"], [data-design-role="editorial"]');
        if (narrativeEl) return narrativeEl;
      }

      // 7. Body / Deck / Paragraph
      if (role.includes('body') || role.includes('deck') || role.includes('paragraph') || role.includes('lead')) {
        const bodyEl = document.querySelector('[data-design-id*="deck"], [data-design-role="body"], p[data-design-id]');
        if (bodyEl) return bodyEl;
      }

      // 8. Badge / Metric / Stat / Metadata
      if (role.includes('badge') || role.includes('metric') || role.includes('stat') || role.includes('metadata') || role.includes('kpi')) {
        const badgeEl = document.querySelector('[data-design-id*="stat"], [data-design-id*="badge"], [data-design-role="stat"], [data-design-role="metric"]');
        if (badgeEl) return badgeEl;
      }

      // 9. Index-based fallback across primary targets
      const primaryTargets = Array.from(document.querySelectorAll('[data-design-id]')).filter((el) => !this.isExcluded(el));
      if (Number.isInteger(slot.index) && primaryTargets[slot.index]) {
        return primaryTargets[slot.index];
      }

      return null;
    }

    /**
     * Applies one legacy slot (typography, text, colour, spacer, rule or PNG/SVG
     * placement). Styles and text go through the recording setters, so they
     * appear in the ChangeLedger and are undone by reset.
     */
    applySlotUpdate(slot) {
      if (!slot) return;
      const el = this.resolveElementForSlot(slot);
      if (!el || this.isExcluded(el)) return;
      const record = this.ensureTarget(el);

      // A. PNG / SVG Asset Placement
      if (slot.type === 'image') {
        this.placeAsset(record, slot);
        this.noteChange(record);
        return;
      }

      // B. Typography & Text Content
      if (slot.type === 'text') {
        // ONLY update text content if explicitly marked as touched/edited by the user
        // This protects the application's actual content from being overwritten with preset dummy poetry
        if (slot.textTouched && slot.text !== undefined && slot.text !== null && this.textEditable(el)) {
          this.setText(el, String(slot.text));
        }

        if (slot.fontFamily) this.setStyle(el, 'font-family', String(slot.fontFamily));
        if (slot.size) this.setStyle(el, 'font-size', `${slot.size}px`);
        if (slot.weight) this.setStyle(el, 'font-weight', String(slot.weight));
        if (slot.lineHeight) this.setStyle(el, 'line-height', String(slot.lineHeight));
        if (typeof slot.tracking === 'number') this.setStyle(el, 'letter-spacing', `${slot.tracking / 1000}em`);
        if (slot.colorHex) this.setStyle(el, 'color', String(slot.colorHex));
        if (slot.align) this.setStyle(el, 'text-align', String(slot.align));
        if (slot.transform) this.setStyle(el, 'text-transform', String(slot.transform));
      }

      // C. Spacer Height
      if (slot.type === 'spacer' && slot.spacerHeight) {
        this.setStyle(el, 'margin-top', `${slot.spacerHeight}px`);
      }

      // D. Rule Width & Thickness
      if (slot.type === 'rule') {
        if (slot.ruleWidth) this.setStyle(el, 'width', `${slot.ruleWidth}%`);
        if (slot.ruleThickness) this.setStyle(el, 'border-top-width', `${slot.ruleThickness}px`);
        if (slot.colorHex) this.setStyle(el, 'border-color', String(slot.colorHex));
      }

      this.noteChange(record);
    }

    /**
     * Places a PNG or SVG asset for a legacy image slot. Only data URLs accepted
     * by safeAssetUrl() are used; anything else is ignored. The asset is always
     * rendered through an <img> (an SVG image cannot run script), and every
     * change (src, inline styles, inserted <img>, hidden inline <svg>) is
     * recorded so reset restores the original exactly.
     */
    placeAsset(record, slot) {
      const url = safeAssetUrl(slot.assetDataUrl);
      if (!url) return;
      const el = record.element;
      const tag = el.localName;
      const width = numberIn(slot.imageWidth, 1, 4000) ? slot.imageWidth : 180;
      const opacity = numberIn(slot.opacity, 0, 1) ? slot.opacity : 1;
      const size = (img) => {
        img.style.width = `${width}px`;
        img.style.opacity = String(opacity);
      };

      // The target is itself an <img>: swap its source.
      if (tag === 'img') {
        this.setAttr(el, 'src', url);
        if (el.hasAttribute('srcset')) this.setAttr(el, 'srcset', null);
        this.setStyle(el, 'width', `${width}px`);
        this.setStyle(el, 'opacity', String(opacity));
        return;
      }

      // An inline <svg> target: hide it and show the asset as an <img> sibling.
      if (tag === 'svg') {
        size(this.placedImage(el, url, slot, 'after'));
        this.setStyle(el, 'display', 'none', { ledger: false });
        return;
      }

      // Container element (e.g. <div> or <figure>): append the asset inside it.
      // Clear a lone placeholder emoji (restored with the original text on reset).
      const text = el.textContent;
      if (!this.placedAssets.get(el) && text.length < 5 && /[\u{1F300}-\u{1F9FF}]/u.test(text) && this.textEditable(el)) {
        this.setText(el, '');
      }
      size(this.placedImage(el, url, slot, 'inside'));
      this.setStyle(el, 'display', 'flex', { ledger: false });
      this.setStyle(el, 'align-items', 'center', { ledger: false });
      this.setStyle(el, 'justify-content', 'center', { ledger: false });
    }

    // The bridge-owned <img> for a target, created on first use.
    placedImage(el, url, slot, where) {
      let img = this.placedAssets.get(el);
      if (!img || !img.isConnected) {
        img = document.createElement('img');
        img.className = PLACED_ASSET_CLASS;
        img.alt = typeof slot.imageName === 'string' ? slot.imageName.slice(0, 200) : 'Placed asset';
        img.style.cssText = 'display: inline-block; max-width: 100%; height: auto; object-fit: contain; border-radius: 4px;';
        if (where === 'after') el.after(img);
        else el.appendChild(img);
        this.placedAssets.set(el, img);
        this.placedElements.add(el);
      }
      img.setAttribute('src', url);
      return img;
    }

    removePlacedAsset(el) {
      const img = this.placedAssets.get(el);
      if (img) img.remove();
      this.placedAssets.delete(el);
      this.placedElements.delete(el);
    }
  }

  // Global factory: returns the single page instance, creating it if needed.
  // Options passed after an instance exists cannot take effect, so they warn.
  function initFontKitBridge(options) {
    const existing = global.__fontkitBridge;
    if (existing) {
      if (options !== undefined && existing instanceof FontKitBridge) {
        // Like the constructor, only an allowedOrigins list that narrows the running policy is applied: a security
        // option is never silently dropped, and never widens what is already allowed. The options object the bridge
        // was built from is read again too: the bridge copied its list at construction, so a page that edited
        // `allowedOrigins` on that object since would otherwise keep the wider policy. Narrowing is idempotent, so
        // the plain `initFontKitBridge(window.FONTKIT_BRIDGE_OPTIONS)` changes nothing and stays quiet.
        const reused = options === existing.initOptions;
        const outcome = existing.disposed ? { sentence: 'Options ignored.', changed: false } : narrowRunningBridge(existing, options);
        if (!reused || outcome.changed) {
          console.warn('[FontKitBridge] initFontKitBridge(): a bridge already exists. ' + `${outcome.sentence} `
            + 'Add data-auto-init="false" to the script tag (or set window.FONTKIT_BRIDGE_OPTIONS) to configure it.');
        }
      }
      return existing;
    }
    return new FontKitBridge(options); // the constructor claims global.__fontkitBridge
  }

  // Auto-init uses window.FONTKIT_BRIDGE_OPTIONS (read when it runs) and is a
  // no-op when the page already constructed or initialised its own instance.
  function autoInit() {
    if (global.__fontkitBridge) return;
    const options = isPlainObject(global.FONTKIT_BRIDGE_OPTIONS) ? global.FONTKIT_BRIDGE_OPTIONS : undefined;
    const instance = initFontKitBridge(options);
    if (instance) instance.auto = true; // a later `new FontKitBridge()` may replace it until a Studio connects
  }

  // Auto-initialize in browser unless the script tag says data-auto-init="false"
  if (typeof window !== 'undefined' && typeof document !== 'undefined') {
    // A second load (double include, HMR) keeps the first class and instance.
    if (!global.FontKitBridge) global.FontKitBridge = FontKitBridge;
    if (!global.initFontKitBridge) global.initFontKitBridge = initFontKitBridge;
    const autoInitDisabled = !!currentScript && currentScript.getAttribute('data-auto-init') === 'false';
    if (!autoInitDisabled) {
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoInit);
      } else {
        autoInit();
      }
    }
  }

  // CommonJS support
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FontKitBridge, initFontKitBridge, PATCH_RULES };
  }
})(typeof window !== 'undefined' ? window : globalThis);
