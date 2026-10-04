// Vite plugin: in `vite dev` only, serves the bundled bridge from the app's own origin and
// tags every HTML page with one classic script that pins Studio's origin.
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

import { startStudioServer } from './studio-server.js';

export const BRIDGE_PATH = '/@fontkit/fontkit-bridge.js';

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

export function fontkitStudio(options = {}) {
  const {
    bridgeFile = new URL('../dist/fontkit-bridge.js', import.meta.url),
    studioFile,
  } = options;
  let studio = options.studio;
  if (studio) checkLocalOrigin(studio.origin);
  const standalone = !studio;
  let bridge;

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
    apply: 'serve',

    async configureServer(server) {
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
          server.config.logger.info(`  Font Kit Studio: ${started.url(local)}`);
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

    transformIndexHtml() {
      if (!studio) return [];
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
