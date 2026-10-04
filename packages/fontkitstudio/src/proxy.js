// A loopback proxy in front of a dev server that is not Vite: it forwards everything,
// serves the bridge itself and adds one script tag to HTML pages.
import { readFile } from 'node:fs/promises';
import { Agent, createServer, request } from 'node:http';
import { connect } from 'node:net';
import { fileURLToPath } from 'node:url';

export const BRIDGE_PATH = '/@fontkit/fontkit-bridge.js';

const LOOPBACK_HOSTS = ['127.0.0.1', '::1', 'localhost'];
const LOOPBACK_URL_HOSTNAMES = ['localhost', '127.0.0.1', '[::1]'];
const HOP_BY_HOP = [
  'connection',
  'keep-alive',
  'proxy-connection',
  'te',
  'trailer',
  'transfer-encoding',
  'upgrade',
];

function parseUrl(text) {
  try {
    return new URL(text);
  } catch {
    return undefined;
  }
}

// Inserts the tag after <head>, else <html>, else a leading doctype, else at 0. Works on
// latin1 so every byte of the page, whatever its encoding, comes out as it went in.
export function insertTag(buffer, tag) {
  const text = buffer.toString('latin1');
  const found =
    /<head(\s[^>]*)?>/i.exec(text) ??
    /<html(\s[^>]*)?>/i.exec(text) ??
    /^(\xEF\xBB\xBF)?\s*<!doctype[^>]*>/i.exec(text);
  const at = found ? found.index + found[0].length : 0;
  return Buffer.from(text.slice(0, at) + tag + text.slice(at), 'latin1');
}

export async function startProxy({
  target,
  studio,
  bridgeFile = new URL('../dist/fontkit-bridge.js', import.meta.url),
  host = '127.0.0.1',
  port = 0,
  maxHtmlBytes = 8 * 1024 * 1024,
} = {}) {
  const targetUrl = parseUrl(String(target));
  if (
    !targetUrl ||
    targetUrl.protocol !== 'http:' ||
    !LOOPBACK_URL_HOSTNAMES.includes(targetUrl.hostname)
  ) {
    throw new Error('Font Kit Studio proxies only a local dev server (localhost or 127.0.0.1)');
  }
  const studioUrl = parseUrl(String(studio?.origin));
  if (
    !studioUrl ||
    studioUrl.protocol !== 'http:' ||
    !LOOPBACK_URL_HOSTNAMES.includes(studioUrl.hostname) ||
    studioUrl.pathname !== '/' ||
    studioUrl.search !== '' ||
    studioUrl.hash !== '' ||
    studioUrl.username !== '' ||
    studioUrl.password !== ''
  ) {
    throw new Error(
      'Font Kit Studio: studio.origin must be a local http origin such as http://127.0.0.1:5000',
    );
  }
  if (!LOOPBACK_HOSTS.includes(host)) {
    throw new Error(`refusing to bind ${host}: the proxy runs on loopback only`);
  }
  const bridgePath = bridgeFile instanceof URL ? fileURLToPath(bridgeFile) : String(bridgeFile);
  let bridge;
  try {
    bridge = await readFile(bridgePath);
  } catch {
    throw new Error(
      `Font Kit Studio cannot read the bridge at ${bridgePath}; run npm --prefix packages/fontkitstudio run prepack`,
    );
  }

  const targetOrigin = targetUrl.origin;
  const targetHostname = targetUrl.hostname.replace(/^\[|\]$/g, '');
  const targetPort = Number(targetUrl.port || 80);
  const tag = `<script src="${BRIDGE_PATH}" data-allowed-origins="${studioUrl.origin}"></script>`;
  const agent = new Agent({ keepAlive: true });
  let proxyOrigin;
  let actualPort;
  let allowedHosts;
  let ownOrigins;

  // An absolute location at the dev server's origin points back at the proxy.
  function rewriteLocation(headers) {
    if (typeof headers.location !== 'string') return headers;
    const location = parseUrl(headers.location);
    if (!location || location.origin !== targetOrigin) return headers;
    return {
      ...headers,
      location: proxyOrigin + location.pathname + location.search + location.hash,
    };
  }

  // The rest of a URL that sits under one of the proxy's own loopback origins, else undefined.
  function underProxy(value) {
    const lower = value.toLowerCase();
    for (const own of ownOrigins) {
      if (!lower.startsWith(own)) continue;
      const rest = value.slice(own.length);
      if (rest === '' || '/?#'.includes(rest[0])) return rest;
    }
    return undefined;
  }

  function forwardHeaders(headers) {
    const out = {};
    for (const [name, value] of Object.entries(headers)) {
      if (!HOP_BY_HOP.includes(name)) out[name] = value;
    }
    out.host = targetUrl.host;
    out['accept-encoding'] = 'identity';
    if (typeof out.origin === 'string' && underProxy(out.origin) === '') out.origin = targetOrigin;
    if (typeof out.referer === 'string') {
      const rest = underProxy(out.referer);
      if (rest !== undefined) out.referer = targetOrigin + rest;
    }
    return out;
  }

  function isTaggable(method, upstream) {
    const type = String(upstream.headers['content-type'] ?? '')
      .split(';')[0]
      .trim()
      .toLowerCase();
    const encoding = String(upstream.headers['content-encoding'] ?? 'identity').toLowerCase();
    return (
      method !== 'HEAD' &&
      upstream.statusCode === 200 &&
      type === 'text/html' &&
      encoding === 'identity'
    );
  }

  function forward(req, res) {
    const proxied = request(
      {
        agent,
        hostname: targetHostname,
        port: targetPort,
        method: req.method,
        path: req.url,
        headers: forwardHeaders(req.headers),
      },
      (upstream) => {
        const fail = () => res.destroy();
        upstream.on('error', fail);

        if (!isTaggable(req.method, upstream)) {
          res.writeHead(upstream.statusCode, rewriteLocation(upstream.headers));
          upstream.pipe(res);
          return;
        }
        const chunks = [];
        let size = 0;
        const onData = (chunk) => {
          chunks.push(chunk);
          size += chunk.length;
          if (size <= maxHtmlBytes) return;
          // Too big to tag: send what is buffered, then stream the rest.
          upstream.off('data', onData);
          upstream.off('end', onEnd);
          res.writeHead(upstream.statusCode, rewriteLocation(upstream.headers));
          for (const buffered of chunks) res.write(buffered);
          upstream.pipe(res);
        };
        const onEnd = () => {
          const page = insertTag(Buffer.concat(chunks), tag);
          const headers = rewriteLocation({ ...upstream.headers });
          delete headers['transfer-encoding'];
          delete headers.etag;
          delete headers['last-modified'];
          headers['content-length'] = String(page.length);
          headers['cache-control'] = 'no-store';
          res.writeHead(upstream.statusCode, headers);
          res.end(page);
        };
        upstream.on('data', onData);
        upstream.on('end', onEnd);
      },
    );
    proxied.on('error', () => {
      if (res.headersSent) {
        res.destroy();
        return;
      }
      const body = `Font Kit Studio cannot reach the dev server at ${targetOrigin}. Is it running?`;
      res.writeHead(502, {
        'content-type': 'text/plain; charset=utf-8',
        'content-length': Buffer.byteLength(body),
        connection: 'close',
      });
      res.end(body);
    });
    res.on('close', () => {
      if (!res.writableFinished) proxied.destroy();
    });
    req.on('error', () => proxied.destroy());
    req.pipe(proxied);
  }

  const server = createServer((req, res) => {
    const send = (status, body, headers = {}) => {
      res.writeHead(status, {
        'content-type': 'text/plain; charset=utf-8',
        'content-length': Buffer.byteLength(body),
        connection: 'close',
        ...headers,
      });
      res.end(req.method === 'HEAD' ? undefined : body);
    };

    const requestHost = String(req.headers.host ?? '').toLowerCase();
    if (!allowedHosts.includes(requestHost)) return send(421, 'Host header not allowed.');
    if (!req.url.startsWith('/')) return send(400, 'Bad request.');

    const isBridge = req.url.split('?')[0] === BRIDGE_PATH;
    if (isBridge && (req.method === 'GET' || req.method === 'HEAD')) {
      res.writeHead(200, {
        'content-type': 'text/javascript; charset=utf-8',
        'content-length': bridge.length,
        'cache-control': 'no-store',
        'x-content-type-options': 'nosniff',
      });
      res.end(req.method === 'HEAD' ? undefined : bridge);
      return;
    }
    forward(req, res);
  });

  // WebSocket upgrades (the app's own hot reload): the same Host and request-line checks,
  // then the same header rewrites, then raw bytes both ways until either side ends.
  const upgraded = new Set();
  const refuse = (socket, line) => {
    socket.write(`HTTP/1.1 ${line}\r\nConnection: close\r\nContent-Length: 0\r\n\r\n`, () =>
      socket.destroy(),
    );
  };
  server.on('upgrade', (req, socket, head) => {
    socket.on('error', () => socket.destroy());
    const requestHost = String(req.headers.host ?? '').toLowerCase();
    if (!allowedHosts.includes(requestHost)) return refuse(socket, '421 Misdirected Request');
    if (!req.url.startsWith('/')) return refuse(socket, '400 Bad Request');

    const headers = forwardHeaders(req.headers);
    headers.connection = req.headers.connection;
    headers.upgrade = req.headers.upgrade;
    const lines = [`${req.method} ${req.url} HTTP/1.1`];
    for (const [name, value] of Object.entries(headers)) {
      for (const one of Array.isArray(value) ? value : [value]) lines.push(`${name}: ${one}`);
    }
    const upstream = connect(targetPort, targetHostname);
    upgraded.add(socket);
    upgraded.add(upstream);
    const drop = () => {
      socket.destroy();
      upstream.destroy();
      upgraded.delete(socket);
      upgraded.delete(upstream);
    };
    socket.on('close', drop);
    upstream.on('close', drop);
    upstream.on('error', drop);
    upstream.on('connect', () => {
      upstream.write(`${lines.join('\r\n')}\r\n\r\n`);
      if (head.length > 0) upstream.write(head);
      socket.pipe(upstream);
      upstream.pipe(socket);
    });
  });

  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, host, resolve);
  });
  actualPort = server.address().port;
  allowedHosts = [`127.0.0.1:${actualPort}`, `localhost:${actualPort}`, `[::1]:${actualPort}`];
  ownOrigins = allowedHosts.map((allowed) => `http://${allowed}`);
  proxyOrigin = `http://${host === '::1' ? '[::1]' : host}:${actualPort}`;

  return {
    origin: proxyOrigin,
    port: actualPort,
    close() {
      return new Promise((resolve) => {
        server.close(() => {
          agent.destroy();
          resolve();
        });
        server.closeAllConnections();
        for (const socket of upgraded) socket.destroy();
      });
    },
  };
}
