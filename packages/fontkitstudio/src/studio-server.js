// Serves the bundled Studio on loopback, only to requests that carry this run's token.
import { randomBytes, timingSafeEqual } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { createServer } from 'node:http';
import { fileURLToPath } from 'node:url';

export const STUDIO_PATH = '/fontkit-studio.html';

const LOOPBACK_HOSTS = ['127.0.0.1', '::1', 'localhost'];
const NO_STORE = {
  'Cache-Control': 'no-store',
  'Referrer-Policy': 'no-referrer',
  'X-Content-Type-Options': 'nosniff',
};

export function newToken() {
  return randomBytes(32).toString('base64url');
}

function tokenMatches(given, expected) {
  const a = Buffer.from(given);
  const b = Buffer.from(expected);
  return a.length === b.length && timingSafeEqual(a, b);
}

export async function startStudioServer({
  studioFile = new URL('../dist/fontkit-studio.html', import.meta.url),
  host = '127.0.0.1',
  port = 0,
  token = newToken(),
} = {}) {
  if (!LOOPBACK_HOSTS.includes(host)) {
    throw new Error(`refusing to bind ${host}: Studio is served on loopback only`);
  }
  const path = studioFile instanceof URL ? fileURLToPath(studioFile) : String(studioFile);
  let studio;
  try {
    studio = await readFile(path);
  } catch (error) {
    throw new Error(
      `cannot read Studio at ${path} (${error.code ?? error.message}); run the bundle step: npm --prefix packages/fontkitstudio run prepack`,
    );
  }

  const server = createServer((req, res) => {
    const send = (status, body, extra = {}) => {
      const isHtml = status === 200;
      res.writeHead(status, {
        ...NO_STORE,
        ...(isHtml ? {} : { Connection: 'close' }),
        'Content-Type': isHtml ? 'text/html; charset=utf-8' : 'text/plain; charset=utf-8',
        'Content-Length': Buffer.byteLength(body),
        ...extra,
      });
      res.end(req.method === 'HEAD' ? undefined : body);
    };

    const requestHost = String(req.headers.host ?? '').toLowerCase();
    const allowedHosts = [`127.0.0.1:${actualPort}`, `localhost:${actualPort}`, `[::1]:${actualPort}`];
    if (!allowedHosts.includes(requestHost)) return send(421, 'Host header not allowed.');

    const origin = req.headers.origin;
    if (origin !== undefined && origin.toLowerCase() !== `http://${requestHost}`) {
      return send(403, 'Origin not allowed.');
    }
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      return send(405, 'Only GET and HEAD.', { Allow: 'GET, HEAD' });
    }

    let url;
    try {
      url = new URL(req.url, 'http://studio.invalid');
    } catch {
      return send(400, 'Bad request.');
    }
    if (url.pathname !== STUDIO_PATH) {
      return send(404, 'Not found. Open the URL the fontkitstudio command printed.');
    }
    const given = url.searchParams.getAll('token');
    if (given.length !== 1 || !tokenMatches(given[0], token)) {
      return send(403, 'Missing or wrong token. Open the URL the fontkitstudio command printed.');
    }
    return send(200, studio);
  });

  let actualPort;
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, host, resolve);
  });
  actualPort = server.address().port;

  const origin = `http://${host === '::1' ? '[::1]' : host}:${actualPort}`;
  return {
    port: actualPort,
    token,
    origin,
    url(target) {
      const query = new URLSearchParams({ token });
      if (target !== undefined) query.set('target', target);
      return `${origin}${STUDIO_PATH}?${query}`;
    },
    close() {
      return new Promise((resolve) => {
        server.close(() => resolve());
        server.closeAllConnections();
      });
    },
  };
}
