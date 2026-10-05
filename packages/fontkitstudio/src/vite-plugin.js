// Vite plugin: in `vite dev` only, serves the bundled bridge from the app's own origin and
// tags every HTML page with one classic script that pins Studio's origin.
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

import {
  BRIDGE_TWICE_MESSAGE,
  CSP_MESSAGE,
  blocksSameOriginScript,
  loadsOwnBridge,
  metaPolicies,
} from './csp.js';
import { startStudioServer } from './studio-server.js';

export const BRIDGE_PATH = '/@fontkit/fontkit-bridge.js';

export const BUILD_LINE = 'Font Kit Studio · dev only: not added to this build';
export const HOST_ERROR = 'Font Kit Studio runs only on localhost; remove --host or server.host to use it';
export const START_LINE = '  Font Kit Studio · dev only';

const LOCAL_SERVER_HOSTS = [undefined, 'localhost', '127.0.0.1', '::1', '[::1]'];
const LOCAL_HOSTNAMES = ['127.0.0.1', 'localhost', '[::1]'];
const ORIGIN_ERROR =
  'Font Kit Studio: studio.origin must be a local http origin such as http://127.0.0.1:5000';

function checkLocalOrigin(origin) {
  let url;
  try {
    url = new URL(origin);
  } catch {
    throw new Error(ORIGIN_ERROR);
  }
  if (url.protocol !== 'http:' || !LOCAL_HOSTNAMES.includes(url.hostname) || url.origin !== origin) {
    throw new Error(ORIGIN_ERROR);
  }
}

let buildLinePrinted = false;

// The policy headers the dev server will send on every page, from `server.headers`.
function headerPolicies(headers) {
  if (!headers || typeof headers !== 'object') return [];
  return Object.entries(headers)
    .filter(([name]) => name.toLowerCase() === 'content-security-policy')
    .map(([, value]) => (Array.isArray(value) ? value : String(value)))
    .flat();
}

export function fontkitStudio(options = {}) {
  const {
    bridgeFile = new URL('../dist/fontkit-bridge.js', import.meta.url),
    studioFile,
  } = options;
  let studio = options.studio;
  if (studio) checkLocalOrigin(studio.origin);
  const standalone = !studio;
  let bridge;
  let standDown = false;
  let headers = [];
  let viteServer;
  let logger;
  const said = new Set();

  // Each warning is said once per run, through the options' log or Vite's own logger.
  function warnOnce(message) {
    if (said.has(message)) return;
    said.add(message);
    if (options.log) options.log(message);
    else if (logger) logger.warn(message);
    else process.stderr.write(`${message}\n`);
  }

  function serveBridge(req, res, next) {
    const isRead = req.method === 'GET' || req.method === 'HEAD';
    // The raw path before any query, compared exactly: nothing to parse, so nothing to throw,
    // and '//host/@fontkit/fontkit-bridge.js' is not the bridge.
    if (!isRead || req.url.split('?', 1)[0] !== BRIDGE_PATH) return next();
    res.writeHead(200, {
      'Content-Type': 'text/javascript; charset=utf-8',
      'Content-Length': bridge.length,
      'Cache-Control': 'no-store',
      'X-Content-Type-Options': 'nosniff',
    });
    res.end(req.method === 'HEAD' ? undefined : bridge);
    return undefined;
  }

  return {
    name: 'fontkit-studio',
    apply(config, { command }) {
      if (command === 'build' && !buildLinePrinted) {
        buildLinePrinted = true;
        process.stdout.write(`${BUILD_LINE}\n`);
      }
      return command === 'serve';
    },
    // The command's instance says so, so a permanent one in the project's config stands down.
    ...(standalone ? {} : { api: { fontkitStudio: { fromCommand: true } } }),

    configResolved(config) {
      if (!LOCAL_SERVER_HOSTS.includes(config.server?.host)) throw new Error(HOST_ERROR);
      logger = config.logger;
      headers = headerPolicies(config.server?.headers);
      if (!standalone) return;
      standDown = config.plugins.some(
        (plugin) => plugin.name === 'fontkit-studio' && plugin.api?.fontkitStudio?.fromCommand === true,
      );
    },

    async configureServer(server) {
      if (standDown) return;
      viteServer = server;
      const path = bridgeFile instanceof URL ? fileURLToPath(bridgeFile) : String(bridgeFile);
      try {
        bridge = await readFile(path);
      } catch {
        throw new Error(
          `Font Kit Studio cannot read the bridge at ${path}; run npm --prefix packages/fontkitstudio run prepack`,
        );
      }

      if (standalone) {
        const started = await startStudioServer(studioFile === undefined ? {} : { studioFile });
        studio = started;
        const printUrls = server.printUrls.bind(server);
        let printed = false;
        server.printUrls = () => {
          printUrls();
          if (printed) return;
          printed = true;
          const local = server.resolvedUrls?.local?.[0];
          server.config.logger.info(START_LINE);
          server.config.logger.info(`  Open: ${started.url(local)}`);
        };
        if (server.httpServer) {
          server.httpServer.on('close', () => started.close());
        } else {
          const close = server.close.bind(server);
          server.close = async () => {
            await started.close();
            return close();
          };
        }
      }

      server.middlewares.use(serveBridge);
    },

    transformIndexHtml(html) {
      if (standDown || !studio) return [];
      if (loadsOwnBridge(html)) warnOnce(BRIDGE_TWICE_MESSAGE);
      // The address the dev server listens on is the one Studio opens the app at; without it
      // (middleware mode, a page before listen) only 'self', '*' and 'http:' allow.
      let pageOrigin;
      try {
        pageOrigin = new URL(viteServer?.resolvedUrls?.local?.[0]).origin;
      } catch {
        pageOrigin = undefined;
      }
      if (blocksSameOriginScript([...headers, ...metaPolicies(html)], pageOrigin)) warnOnce(CSP_MESSAGE);
      return [
        {
          tag: 'script',
          attrs: { src: BRIDGE_PATH, 'data-allowed-origins': studio.origin },
          injectTo: 'head-prepend',
        },
      ];
    },
  };
}
