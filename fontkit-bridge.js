/**
 * Font Kit Studio — Design Bridge Protocol v1 Target SDK
 * =======================================================
 * Standalone, zero-dependency bridge runtime for code-owned web applications.
 * Can be dropped into ANY web project via <script> tag or ESM import.
 *
 * Invariants:
 *  - Running app is the rendering authority.
 *  - Elements are addressed by stable data-design-id API attributes.
 *  - Zero editor chrome leaks into target DOM.
 *  - Cross-origin isolation safe via window.postMessage().
 *
 * Specification: font-kit-studio-v0.2.0-design-bridge-protocol-v1.md
 */

(function (global) {
  'use strict';

  class FontKitBridge {
    constructor(options = {}) {
      this.protocolVersion = 1;
      this.revision = 1;
      this.sessionId = options.sessionId || `fkb-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
      this.options = {
        autoDiscover: true,
        allowedOrigins: options.allowedOrigins || ['*'],
        tokens: options.tokens || {},
        onApplied: options.onApplied || null,
        ...options
      };

      this.targets = new Map();
      this.activeStudioSource = null;
      this.activeStudioOrigin = null;

      this.init();
    }

    init() {
      if (this.options.autoDiscover) {
        this.discoverTargets();
      }

      window.addEventListener('message', (e) => this.handleMessage(e));

      // Observe DOM additions with data-design-id
      if (typeof MutationObserver !== 'undefined') {
        const observer = new MutationObserver(() => this.discoverTargets());
        observer.observe(document.body || document.documentElement, {
          childList: true,
          subtree: true
        });
      }

      // Announce readiness to parent (if in iframe) or opener (if in popup)
      this.announceReadiness();
    }

    announceReadiness() {
      const payload = {
        type: 'design:bridge-ready',
        protocolVersion: this.protocolVersion,
        sessionId: this.sessionId
      };

      if (window.parent && window.parent !== window) {
        window.parent.postMessage(payload, '*');
      }
      if (window.opener) {
        window.opener.postMessage(payload, '*');
      }
    }

    discoverTargets() {
      const elements = document.querySelectorAll('[data-design-id]');
      elements.forEach((el) => {
        const id = el.getAttribute('data-design-id');
        if (!id) return;
        const role = el.getAttribute('data-design-role') || 'generic';
        const computed = window.getComputedStyle(el);

        this.targets.set(id, {
          id,
          role,
          kind: 'text',
          element: el,
          editable: {
            text: true,
            typography: true,
            color: true,
            alignment: true,
            spacing: true
          },
          computed: {
            fontFamily: computed.fontFamily,
            fontSize: computed.fontSize,
            fontWeight: computed.fontWeight,
            color: computed.color,
            letterSpacing: computed.letterSpacing,
            lineHeight: computed.lineHeight
          }
        });
      });
    }

    getTargetManifest() {
      this.discoverTargets();
      const manifest = [];
      for (const [id, t] of this.targets.entries()) {
        manifest.push({
          id: t.id,
          role: t.role,
          kind: t.kind,
          editable: t.editable,
          computed: t.computed
        });
      }
      return manifest;
    }

    getCurrentTokens() {
      const rootStyle = window.getComputedStyle(document.documentElement);
      const tokenKeys = [
        '--font-sans',
        '--font-serif',
        '--font-mono',
        '--font-display',
        '--editorial-size',
        '--mono-spacing',
        '--brand-canvas',
        '--accent-cyan',
        '--accent-emerald',
        '--accent-purple'
      ];

      const tokens = {};
      tokenKeys.forEach((key) => {
        const val = rootStyle.getPropertyValue(key).trim();
        if (val) tokens[key] = val;
      });

      return tokens;
    }

    handleMessage(event) {
      const data = event.data;
      if (!data || typeof data !== 'object' || !data.type) return;

      // Track connecting Studio instance
      if (data.type.startsWith('design:') || data.type.startsWith('fontkit:')) {
        this.activeStudioSource = event.source;
        this.activeStudioOrigin = event.origin;
      }

      switch (data.type) {
        case 'design:hello':
          this.handleHello(event.source, data);
          break;

        case 'design:update':
          this.handleUpdate(event.source, data);
          break;

        case 'design:inspect':
          this.handleInspect(event.source, data);
          break;

        case 'design:ping':
          this.postResponse(event.source, {
            type: 'design:pong',
            revision: this.revision,
            sessionId: this.sessionId
          });
          break;

        case 'fontkit:change':
          this.handleFontKitChange(event.source, data);
          break;
      }
    }

    handleHello(source, message) {
      this.revision++;
      const response = {
        type: 'design:ready',
        protocolVersion: this.protocolVersion,
        sessionId: message.sessionId || this.sessionId,
        revision: this.revision,
        capabilities: {
          inspect: true,
          patch: true,
          assets: false,
          typography: true,
          tokens: true
        },
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight
        },
        tokens: {
          css: this.getCurrentTokens()
        },
        targets: this.getTargetManifest()
      };

      this.postResponse(source, response);
    }

    handleUpdate(source, message) {
      const patch = message.patch || {};
      const canonicalPatch = {};
      const root = document.documentElement;

      // 1. Apply global tokens if provided
      if (patch.tokens && typeof patch.tokens === 'object') {
        canonicalPatch.tokens = {};
        for (const [key, val] of Object.entries(patch.tokens)) {
          if (typeof val === 'string') {
            root.style.setProperty(key, val);
            canonicalPatch.tokens[key] = val;
          }
        }
      }

      // 2. Direct token shortcuts
      ['sans', 'serif', 'mono', 'display'].forEach((role) => {
        if (patch[role]) {
          const varName = `--font-${role}`;
          root.style.setProperty(varName, patch[role]);
          canonicalPatch[varName] = patch[role];
        }
      });

      // 3. Target-specific element mutations
      if (message.targetId) {
        const targetObj = this.targets.get(message.targetId);
        const el = targetObj ? targetObj.element : document.querySelector(`[data-design-id="${message.targetId}"]`);
        if (el) {
          canonicalPatch.targetId = message.targetId;
          canonicalPatch.styles = {};

          if (patch.fontFamily) {
            el.style.fontFamily = patch.fontFamily;
            canonicalPatch.styles.fontFamily = patch.fontFamily;
          }
          if (patch.fontSize) {
            el.style.fontSize = patch.fontSize;
            canonicalPatch.styles.fontSize = patch.fontSize;
          }
          if (patch.fontWeight) {
            el.style.fontWeight = patch.fontWeight;
            canonicalPatch.styles.fontWeight = patch.fontWeight;
          }
          if (patch.color) {
            el.style.color = patch.color;
            canonicalPatch.styles.color = patch.color;
          }
          if (patch.letterSpacing) {
            el.style.letterSpacing = patch.letterSpacing;
            canonicalPatch.styles.letterSpacing = patch.letterSpacing;
          }
          if (patch.lineHeight) {
            el.style.lineHeight = patch.lineHeight;
            canonicalPatch.styles.lineHeight = patch.lineHeight;
          }
        }
      }

      this.revision++;

      // Trigger user application callback if configured
      if (typeof this.options.onApplied === 'function') {
        try {
          this.options.onApplied(canonicalPatch, this.revision);
        } catch (err) {
          console.warn('[FontKitBridge] onApplied callback error:', err);
        }
      }

      // Acknowledge authoritative applied state to Studio
      this.postResponse(source, {
        type: 'design:applied',
        requestId: message.requestId || `req-${Date.now()}`,
        revision: this.revision,
        targetId: message.targetId || 'global',
        canonicalPatch
      });
    }

    handleInspect(source, message) {
      if (!message.targetId) return;
      const targetObj = this.targets.get(message.targetId);
      const el = targetObj ? targetObj.element : document.querySelector(`[data-design-id="${message.targetId}"]`);
      if (!el) {
        this.postResponse(source, {
          type: 'design:inspect-result',
          targetId: message.targetId,
          found: false
        });
        return;
      }

      const rect = el.getBoundingClientRect();
      this.postResponse(source, {
        type: 'design:inspect-result',
        targetId: message.targetId,
        found: true,
        bounds: {
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height,
          top: rect.top,
          left: rect.left
        },
        computed: {
          fontFamily: window.getComputedStyle(el).fontFamily,
          fontSize: window.getComputedStyle(el).fontSize,
          fontWeight: window.getComputedStyle(el).fontWeight,
          color: window.getComputedStyle(el).color
        }
      });
    }

    handleFontKitChange(source, message) {
      if (message.fonts) {
        const root = document.documentElement;
        if (message.fonts.sans) root.style.setProperty('--font-sans', message.fonts.sans);
        if (message.fonts.serif) root.style.setProperty('--font-serif', message.fonts.serif);
        if (message.fonts.mono) root.style.setProperty('--font-mono', message.fonts.mono);
        if (message.fonts.display) root.style.setProperty('--font-display', message.fonts.display);
      }
      this.revision++;
      this.postResponse(source, {
        type: 'fontkit:ack',
        revision: this.revision
      });
    }

    postResponse(targetWindow, message) {
      if (!targetWindow || !targetWindow.postMessage) return;
      try {
        targetWindow.postMessage(message, '*');
      } catch (err) {
        console.warn('[FontKitBridge] postMessage delivery failed:', err);
      }
    }
  }

  // Global factory export
  function initFontKitBridge(options) {
    if (!global.__fontkitBridge) {
      global.__fontkitBridge = new FontKitBridge(options);
    }
    return global.__fontkitBridge;
  }

  // Auto-initialize if running in a browser environment
  if (typeof window !== 'undefined') {
    global.FontKitBridge = FontKitBridge;
    global.initFontKitBridge = initFontKitBridge;
    // Auto-init on DOMContentLoaded
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => initFontKitBridge());
    } else {
      initFontKitBridge();
    }
  }

  // CommonJS / ESM support
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FontKitBridge, initFontKitBridge };
  }
})(typeof window !== 'undefined' ? window : globalThis);
