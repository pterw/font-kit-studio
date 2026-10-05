import { after, before, describe, test } from 'node:test';
import assert from 'node:assert/strict';
import { randomBytes } from 'node:crypto';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { request } from 'node:http';
import { connect } from 'node:net';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { gzipSync } from 'node:zlib';

import { BRIDGE_TWICE_MESSAGE, CSP_MESSAGE } from '../src/csp.js';
import { BRIDGE_PATH, ProxyTargetError, parseProxyTarget, startProxy } from '../src/proxy.js';
import { startUpstream } from './helpers/upstream.js';
import { acceptKey, startWsUpstream } from './helpers/ws-upstream.js';

const STUDIO = { origin: 'http://127.0.0.1:5000' };
const TAG = `<script src="/@fontkit/fontkit-bridge.js" data-allowed-origins="${STUDIO.origin}"></script>`;
const BRIDGE = Buffer.from('// bridge\nwindow.fontkitBridge = "café";\n');
const HTML = { 'content-type': 'text/html; charset=utf-8' };

const PAGE = Buffer.from(
  '<!doctype html><html><head><meta charset="utf-8"><title>café</title></head><body>café</body></html>',
);
const PNG = randomBytes(300);
const GZIPPED = gzipSync(PAGE);
const EXACT = Buffer.from(`<head>${'a'.repeat(58)}`);
const OVER = Buffer.from(`<head>${'a'.repeat(59)}`);

let dir;
let bridgeFile;
let upstream;
let proxy;
let small;
const closers = [];

before(async () => {
  dir = mkdtempSync(join(tmpdir(), 'fks-proxy-'));
  writeFileSync(join(dir, 'bridge.js'), BRIDGE);
  bridgeFile = pathToFileURL(join(dir, 'bridge.js'));
  upstream = await startUpstream({
    '/page': {
      headers: {
        ...HTML,
        etag: '"v1"',
        'last-modified': 'Wed, 01 Jan 2025 00:00:00 GMT',
        'cache-control': 'max-age=3600',
        'content-security-policy': "script-src 'self'",
        'x-app': 'kept',
      },
      body: PAGE,
    },
    '/header': {
      headers: HTML,
      body: '<header>top</header><html lang="en"><body>café</body></html>',
    },
    '/fragment': { headers: HTML, body: '<!doctype html><p>hi</p>' },
    '/upper': { headers: { 'content-type': 'TEXT/HTML' }, body: PAGE },
    '/xhtml': { headers: { 'content-type': 'application/xhtml+xml' }, body: PAGE },
    '/json': { headers: { 'content-type': 'application/json' }, body: '{"a":"<head>"}' },
    '/js': { headers: { 'content-type': 'text/javascript' }, body: 'var a = "<head>";' },
    '/css': { headers: { 'content-type': 'text/css' }, body: 'a { color: red }' },
    '/png': { headers: { 'content-type': 'image/png', etag: '"p"' }, body: PNG },
    '/missing-html': { status: 404, headers: HTML, body: PAGE },
    '/not-modified': { status: 304, headers: { ...HTML, etag: '"v1"' } },
    '/gzip': { headers: { ...HTML, 'content-encoding': 'gzip' }, body: GZIPPED },
    '/exact': { headers: HTML, body: EXACT },
    '/over': { headers: HTML, body: OVER },
    '/chunked-small': {
      headers: { ...HTML, 'transfer-encoding': 'chunked' },
      body: Buffer.from('<head><p>café</p>'),
    },
    '/chunked': {
      headers: { ...HTML, 'transfer-encoding': 'chunked' },
      body: Buffer.alloc(100, 'x'),
    },
    '/echo': (req) => ({ status: 201, headers: { 'content-type': 'text/plain' }, body: req.url }),
    '/redirect-abs': (req) => ({
      status: 302,
      headers: { location: `http://127.0.0.1:${req.socket.localPort}/login?next=/a#x` },
    }),
    '/redirect-netpath': (req) => ({
      status: 302,
      headers: { location: `//localhost:${req.socket.localPort}/login?next=/a#x` },
    }),
    '/redirect-netpath-ip': (req) => ({
      status: 302,
      headers: { location: `//127.0.0.1:${req.socket.localPort}/x` },
    }),
    '/redirect-netpath-other': { status: 302, headers: { location: '//example.com/x' } },
    '/redirect-netpath-port': (req) => ({
      status: 302,
      headers: { location: `//localhost:${req.socket.localPort + 1}/x` },
    }),
    // Browsers read backslashes as slashes in http URLs, so this is a network-path redirect too.
    '/redirect-backslash': (req) => ({
      status: 302,
      headers: { location: `\\\\localhost:${req.socket.localPort}/b` },
    }),
    '/redirect-https': (req) => ({
      status: 302,
      headers: { location: `https://localhost:${req.socket.localPort}/x` },
    }),
    // The target is 127.0.0.1; localhost on the same port is the same server.
    '/redirect-abs-localhost': (req) => ({
      status: 302,
      headers: { location: `http://localhost:${req.socket.localPort}/c` },
    }),
    '/redirect-rel': { status: 302, headers: { location: '/login' } },
    '/redirect-other': { status: 302, headers: { location: 'http://example.com/' } },
    '/redirect-html': (req) => ({
      status: 200,
      headers: { ...HTML, location: `http://127.0.0.1:${req.socket.localPort}/where` },
      body: PAGE,
    }),
  });
  proxy = await startProxy({ target: upstream.origin, studio: STUDIO, bridgeFile });
  small = await startProxy({
    target: upstream.origin,
    studio: STUDIO,
    bridgeFile,
    maxHtmlBytes: 64,
  });
});

after(async () => {
  try {
    for (const close of [() => proxy.close(), () => small.close(), () => upstream.close(), ...closers]) {
      try {
        await close();
      } catch {
        // keep closing the rest
      }
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

// Starts a proxy that must not start; if it does, it is closed and the test fails.
async function mustRefuse(options, expected) {
  let started;
  try {
    started = await startProxy({ studio: STUDIO, bridgeFile, ...options });
  } catch (error) {
    return expected(error);
  }
  closers.push(() => started.close());
  return assert.fail('startProxy should have refused');
}

// node:http, not fetch: fetch cannot set Host.
function get(path, { method = 'GET', headers = {}, host, body, via = proxy } = {}) {
  return new Promise((resolve, reject) => {
    const req = request(
      {
        host: '127.0.0.1',
        port: via.port,
        path,
        method,
        headers: { Host: host ?? `127.0.0.1:${via.port}`, ...headers },
      },
      (res) => {
        const chunks = [];
        res.on('data', (chunk) => chunks.push(chunk));
        res.on('end', () =>
          resolve({ status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks) }),
        );
      },
    );
    req.on('error', reject);
    req.end(body);
  });
}

// A raw socket: node:http cannot send an empty Host or an absolute-form request line.
function raw(text) {
  return new Promise((resolve, reject) => {
    const socket = connect(proxy.port, '127.0.0.1');
    const chunks = [];
    socket.on('connect', () => socket.write(text));
    socket.on('data', (chunk) => chunks.push(chunk));
    socket.on('error', reject);
    socket.on('close', () => {
      const answer = Buffer.concat(chunks).toString('latin1');
      resolve({ status: Number(answer.split(' ')[1]), text: answer });
    });
  });
}

const sawCount = () => upstream.requests.length;

describe('tag insertion', () => {
  test('tags a page after <head> and leaves every other byte alone', async () => {
    const answer = await get('/page');
    const at = PAGE.indexOf('<head>') + '<head>'.length;
    const expected = Buffer.concat([PAGE.subarray(0, at), Buffer.from(TAG), PAGE.subarray(at)]);
    assert.equal(answer.status, 200);
    assert.deepEqual(answer.body, expected);
    assert.equal(answer.headers['content-length'], String(expected.length));
    assert.equal(answer.headers.etag, undefined);
    assert.equal(answer.headers['last-modified'], undefined);
    assert.equal(answer.headers['cache-control'], 'no-store');
    assert.equal(answer.headers['content-security-policy'], "script-src 'self'");
    assert.equal(answer.headers['x-app'], 'kept');
    assert.equal(answer.headers['transfer-encoding'], undefined);
  });

  test('uses <html> when there is no <head>, never <header>, and a doctype last', async () => {
    const header = (await get('/header')).body.toString('utf8');
    assert.equal(header, `<header>top</header><html lang="en">${TAG}<body>café</body></html>`);
    const fragment = (await get('/fragment')).body.toString('utf8');
    assert.equal(fragment, `<!doctype html>${TAG}<p>hi</p>`);
  });

  test('tags text/html with parameters or capitals, passes other types untouched', async () => {
    assert.ok((await get('/page')).body.includes(TAG));
    assert.ok((await get('/upper')).body.includes(TAG));
    const untouched = [
      ['/xhtml', PAGE, 'application/xhtml+xml'],
      ['/json', Buffer.from('{"a":"<head>"}'), 'application/json'],
      ['/js', Buffer.from('var a = "<head>";'), 'text/javascript'],
      ['/css', Buffer.from('a { color: red }'), 'text/css'],
      ['/png', PNG, 'image/png'],
    ];
    for (const [path, body, type] of untouched) {
      const answer = await get(path);
      assert.deepEqual(answer.body, body, path);
      assert.equal(answer.headers['content-type'], type, path);
      assert.equal(answer.headers['content-length'], String(body.length), path);
    }
    assert.equal((await get('/png')).headers.etag, '"p"');
  });

  test('passes a 404 page, a 304 and a HEAD untouched', async () => {
    const missing = await get('/missing-html');
    assert.equal(missing.status, 404);
    assert.deepEqual(missing.body, PAGE);

    const notModified = await get('/not-modified');
    assert.equal(notModified.status, 304);
    assert.equal(notModified.headers.etag, '"v1"');
    assert.equal(notModified.headers['cache-control'], undefined);

    const before = sawCount();
    const head = await get('/page', { method: 'HEAD' });
    assert.equal(sawCount(), before + 1);
    assert.equal(upstream.requests.at(-1).method, 'HEAD');
    assert.equal(head.status, 200);
    assert.equal(head.body.length, 0);
    assert.equal(head.headers['content-length'], String(PAGE.length));
    assert.equal(head.headers.etag, '"v1"');
    assert.equal(head.headers['cache-control'], 'max-age=3600');
  });

  test('tags a page of exactly maxHtmlBytes and passes one byte more through', async () => {
    assert.equal(EXACT.length, 64);
    assert.equal(OVER.length, 65);
    const tagged = await get('/exact', { via: small });
    assert.ok(tagged.body.includes(TAG));
    const passed = await get('/over', { via: small });
    assert.deepEqual(passed.body, OVER);
    assert.equal(passed.headers['content-length'], '65');
    assert.equal(passed.headers['cache-control'], undefined);
  });

  test('tags a chunked page under the limit and sets its length', async () => {
    const answer = await get('/chunked-small');
    const expected = Buffer.concat([
      Buffer.from('<head>'),
      Buffer.from(TAG),
      Buffer.from('<p>café</p>'),
    ]);
    assert.deepEqual(answer.body, expected);
    assert.equal(answer.headers['content-length'], String(expected.length));
    assert.equal(answer.headers['transfer-encoding'], undefined);
  });

  test('streams a chunked page that passes maxHtmlBytes while being read', async () => {
    const answer = await get('/chunked', { via: small });
    assert.deepEqual(answer.body, Buffer.alloc(100, 'x'));
    assert.equal(answer.headers['transfer-encoding'], 'chunked');
    assert.equal(answer.headers['cache-control'], undefined);
  });

  test('passes compressed HTML through and asks upstream for identity', async () => {
    const answer = await get('/gzip', { headers: { 'accept-encoding': 'gzip, br' } });
    assert.deepEqual(answer.body, GZIPPED);
    assert.equal(answer.headers['content-encoding'], 'gzip');
    assert.equal(upstream.requests.at(-1).url, '/gzip');
    assert.equal(upstream.requests.at(-1).headers['accept-encoding'], 'identity');
  });
});

describe('the bridge path', () => {
  test('serves the bridge itself, with or without a query, and never asks upstream', async () => {
    const before = sawCount();
    for (const path of [BRIDGE_PATH, `${BRIDGE_PATH}?v=1`]) {
      const answer = await get(path);
      assert.equal(answer.status, 200);
      assert.deepEqual(answer.body, BRIDGE);
      assert.equal(answer.headers['content-type'], 'text/javascript; charset=utf-8');
      assert.equal(answer.headers['cache-control'], 'no-store');
      assert.equal(answer.headers['x-content-type-options'], 'nosniff');
    }
    const head = await get(BRIDGE_PATH, { method: 'HEAD' });
    assert.equal(head.status, 200);
    assert.equal(head.body.length, 0);
    assert.equal(sawCount(), before);
  });

  test('forwards look-alike paths unchanged and maps nothing to a local file', async () => {
    assert.equal(BRIDGE_PATH, '/@fontkit/fontkit-bridge.js');
    for (const path of [
      '/@fontkit/../package.json',
      '/@fontkit/../@fontkit/fontkit-bridge.js',
      '/%40fontkit/fontkit-bridge.js',
      '/..%2f..%2fetc/passwd',
      '/@fontkit/fontkit-bridge.js/',
      '/@fontkit/fontkit-bridge.jsx',
    ]) {
      const answer = await get(path);
      assert.equal(upstream.requests.at(-1).url, path);
      assert.equal(answer.status, 404);
      assert.equal(answer.body.toString(), 'not found');
    }
  });

  test('forwards a POST to the bridge path', async () => {
    const before = sawCount();
    const answer = await get(BRIDGE_PATH, { method: 'POST', body: 'x' });
    assert.equal(sawCount(), before + 1);
    assert.equal(answer.status, 404);
  });
});

describe('Host and request line', () => {
  test('refuses a foreign Host and an empty Host, accepts localhost in any case', async () => {
    const before = sawCount();
    const evil = await get('/page', { host: `evil.test:${proxy.port}` });
    assert.equal(evil.status, 421);
    assert.equal(evil.body.toString(), 'Host header not allowed.');
    const wrongPort = await get('/page', { host: '127.0.0.1:1' });
    assert.equal(wrongPort.status, 421);
    const empty = await raw('GET /page HTTP/1.1\r\nHost:\r\nConnection: close\r\n\r\n');
    assert.equal(empty.status, 421);
    assert.equal(sawCount(), before);

    for (const host of [`localhost:${proxy.port}`, `LOCALHOST:${proxy.port}`]) {
      const ok = await get('/page', { host });
      assert.equal(ok.status, 200);
    }
    assert.equal(sawCount(), before + 2);
  });

  test('refuses an absolute-form request line and *', async () => {
    const before = sawCount();
    const absolute = await raw(
      `GET http://example.com/ HTTP/1.1\r\nHost: 127.0.0.1:${proxy.port}\r\nConnection: close\r\n\r\n`,
    );
    assert.equal(absolute.status, 400);
    assert.ok(absolute.text.endsWith('Bad request.'));
    const star = await raw(
      `OPTIONS * HTTP/1.1\r\nHost: 127.0.0.1:${proxy.port}\r\nConnection: close\r\n\r\n`,
    );
    assert.equal(star.status, 400);
    assert.equal(sawCount(), before);
  });
});

describe('forwarding', () => {
  test('keeps method, path, query, body and type, and rewrites only the listed headers', async () => {
    const payload = JSON.stringify({ a: 1, b: 'café' });
    await get('/echo?x=1&y=%20z', {
      method: 'POST',
      body: payload,
      headers: {
        'content-type': 'application/json',
        'content-length': String(Buffer.byteLength(payload)),
        origin: proxy.origin,
        referer: `${proxy.origin}/from?q=1`,
        'proxy-connection': 'keep-alive',
        te: 'trailers',
        'x-custom': 'yes',
      },
    });
    const seen = upstream.requests.at(-1);
    assert.equal(seen.method, 'POST');
    assert.equal(seen.url, '/echo?x=1&y=%20z');
    assert.equal(seen.body.toString('utf8'), payload);
    assert.equal(seen.headers['content-type'], 'application/json');
    assert.equal(seen.headers.host, `127.0.0.1:${upstream.port}`);
    assert.equal(seen.headers.origin, upstream.origin);
    assert.equal(seen.headers.referer, `${upstream.origin}/from?q=1`);
    assert.equal(seen.headers['x-custom'], 'yes');
    assert.equal(seen.headers['proxy-connection'], undefined);
    assert.equal(seen.headers.te, undefined);
  });

  test('leaves a foreign origin and a foreign referer alone', async () => {
    await get('/echo', {
      headers: { origin: 'http://evil.test', referer: `${proxy.origin}0/x` },
    });
    const seen = upstream.requests.at(-1);
    assert.equal(seen.headers.origin, 'http://evil.test');
    assert.equal(seen.headers.referer, `${proxy.origin}0/x`);
  });

  test('treats every loopback form of the proxy origin as its own', async () => {
    const port = proxy.port;
    await get('/echo', {
      host: `localhost:${port}`,
      headers: {
        origin: `http://localhost:${port}`,
        referer: `http://LOCALHOST:${port}/a`,
      },
    });
    let seen = upstream.requests.at(-1);
    assert.equal(seen.headers.origin, upstream.origin);
    assert.equal(seen.headers.referer, `${upstream.origin}/a`);
    await get('/echo', {
      headers: { origin: `http://[::1]:${port}`, referer: `http://[::1]:${port}/b?c=1` },
    });
    seen = upstream.requests.at(-1);
    assert.equal(seen.headers.origin, upstream.origin);
    assert.equal(seen.headers.referer, `${upstream.origin}/b?c=1`);
    await get('/echo', {
      headers: { origin: `http://localhost:${port + 1}`, referer: `http://localhost:${port + 1}/a` },
    });
    seen = upstream.requests.at(-1);
    assert.equal(seen.headers.origin, `http://localhost:${port + 1}`);
    assert.equal(seen.headers.referer, `http://localhost:${port + 1}/a`);
  });

  test('sends a // path to the dev server as a path, never to another host', async () => {
    const before = sawCount();
    const answer = await raw(
      `GET //evil.test/x HTTP/1.1\r\nHost: 127.0.0.1:${proxy.port}\r\nConnection: close\r\n\r\n`,
    );
    assert.equal(answer.status, 404);
    assert.equal(sawCount(), before + 1);
    assert.equal(upstream.requests.at(-1).url, '//evil.test/x');
    assert.equal(upstream.requests.at(-1).headers.host, `127.0.0.1:${upstream.port}`);
  });

  test('forwards a body sent without a length', async () => {
    const status = await new Promise((resolve, reject) => {
      const req = request(
        {
          host: '127.0.0.1',
          port: proxy.port,
          path: '/echo',
          method: 'PUT',
          headers: { Host: `127.0.0.1:${proxy.port}` },
        },
        (res) => {
          res.resume();
          res.on('end', () => resolve(res.statusCode));
        },
      );
      req.on('error', reject);
      req.write('part one;');
      req.end('part two');
    });
    assert.equal(status, 201);
    assert.equal(upstream.requests.at(-1).body.toString(), 'part one;part two');
  });

  test('rewrites a location at the upstream origin to the proxy origin', async () => {
    const absolute = await get('/redirect-abs');
    assert.equal(absolute.status, 302);
    assert.equal(absolute.headers.location, `${proxy.origin}/login?next=/a#x`);
    assert.equal((await get('/redirect-rel')).headers.location, '/login');
    assert.equal((await get('/redirect-other')).headers.location, 'http://example.com/');
    assert.equal((await get('/redirect-netpath')).headers.location, `${proxy.origin}/login?next=/a#x`);
    assert.equal((await get('/redirect-netpath-ip')).headers.location, `${proxy.origin}/x`);
    assert.equal((await get('/redirect-netpath-other')).headers.location, '//example.com/x');
    const otherPort = await get('/redirect-netpath-port');
    assert.equal(otherPort.headers.location, `//localhost:${upstream.port + 1}/x`);
    assert.equal((await get('/redirect-backslash')).headers.location, `${proxy.origin}/b`);
    assert.equal((await get('/redirect-https')).headers.location, `https://localhost:${upstream.port}/x`);
    assert.equal((await get('/redirect-abs-localhost')).headers.location, `${proxy.origin}/c`);
    const html = await get('/redirect-html');
    assert.equal(html.headers.location, `${proxy.origin}/where`);
    assert.ok(html.body.includes(TAG));
  });

  test('answers 502 with a fixed text when the dev server is not running', async () => {
    const gone = await startUpstream({});
    const { origin } = gone;
    await gone.close();
    const dead = await startProxy({ target: origin, studio: STUDIO, bridgeFile });
    closers.push(() => dead.close());
    const answer = await get('/page', { via: dead });
    assert.equal(answer.status, 502);
    assert.match(answer.headers['content-type'], /^text\/plain/);
    assert.equal(
      answer.body.toString(),
      `Font Kit Studio cannot reach the dev server at ${origin}. Is it running?`,
    );
  });
});

describe('start-up refusals', () => {
  const TARGET_TEXT = 'Font Kit Studio proxies only a local dev server (localhost or 127.0.0.1)';
  const STUDIO_TEXT =
    'Font Kit Studio: studio.origin must be a local http origin such as http://127.0.0.1:5000';

  for (const target of [
    'http://example.com',
    'http://10.0.0.5:3000',
    'https://localhost:3000',
    'file:///etc/passwd',
    'localhost:3000',
    '',
  ]) {
    test(`refuses target ${JSON.stringify(target)}`, async () => {
      await mustRefuse({ target }, (error) => assert.equal(error.message, TARGET_TEXT));
    });
  }

  for (const origin of ['http://example.com:5000', 'http://127.0.0.1:5000/x']) {
    test(`refuses studio origin ${origin}`, async () => {
      await mustRefuse({ target: upstream.origin, studio: { origin } }, (error) => {
        assert.equal(error.message, STUDIO_TEXT);
        assert.ok(!error.message.includes(origin));
      });
    });
  }

  test('refuses a missing studio', async () => {
    await mustRefuse({ target: upstream.origin, studio: undefined }, (error) =>
      assert.equal(error.message, STUDIO_TEXT),
    );
  });

  test('refuses to bind a non-loopback host', async () => {
    await mustRefuse({ target: upstream.origin, host: '0.0.0.0' }, (error) =>
      assert.equal(error.message, 'refusing to bind 0.0.0.0: the proxy runs on loopback only'),
    );
  });

  test('refuses a missing bridge file', async () => {
    const missing = join(dir, 'nope.js');
    await mustRefuse({ target: upstream.origin, bridgeFile: missing }, (error) =>
      assert.equal(
        error.message,
        `Font Kit Studio cannot read the bridge at ${missing}; run npm --prefix packages/fontkitstudio run prepack`,
      ),
    );
  });
});

describe('WebSocket upgrade', () => {
  const KEY = 'dGhlIHNhbXBsZSBub25jZQ==';
  const ACCEPT = acceptKey(KEY);
  let ws;
  let wsProxy;

  before(async () => {
    ws = await startWsUpstream();
    wsProxy = await startProxy({ target: ws.origin, studio: STUDIO, bridgeFile });
  });

  after(async () => {
    await wsProxy.close();
    await ws.close();
  });

  function upgradeRequest({ host, origin, referer, path = '/socket?x=1' }) {
    const lines = [
      `GET ${path} HTTP/1.1`,
      `Host: ${host}`,
      'Upgrade: websocket',
      'Connection: Upgrade',
      `Sec-WebSocket-Key: ${KEY}`,
      'Sec-WebSocket-Version: 13',
      'Sec-WebSocket-Protocol: vite-hmr',
    ];
    if (origin) lines.push(`Origin: ${origin}`);
    if (referer) lines.push(`Referer: ${referer}`);
    return `${lines.join('\r\n')}\r\n\r\n`;
  }

  // Collects what the socket receives; waitFor resolves once `done(text)` holds.
  function client(via, text) {
    const socket = connect(via.port, '127.0.0.1');
    const chunks = [];
    let ended = false;
    const waiting = [];
    const check = () => {
      const received = Buffer.concat(chunks);
      for (const w of [...waiting]) {
        if (w.done(received, ended)) {
          waiting.splice(waiting.indexOf(w), 1);
          w.resolve(received);
        }
      }
    };
    socket.on('data', (chunk) => {
      chunks.push(chunk);
      check();
    });
    socket.on('close', () => {
      ended = true;
      check();
    });
    socket.on('error', () => {});
    socket.write(text);
    closers.push(() => socket.destroy());
    return {
      socket,
      // Fails after 3 s instead of hanging when the proxy does not do what the test expects.
      waitFor: (done) =>
        new Promise((resolve, reject) => {
          const timer = setTimeout(() => reject(new Error('timed out waiting for the socket')), 3000);
          waiting.push({
            done,
            resolve: (received) => {
              clearTimeout(timer);
              resolve(received);
            },
          });
          check();
        }),
    };
  }

  const headEnd = (received) => received.includes('\r\n\r\n');

  test('passes the handshake and the bytes through, as the dev server', async () => {
    const proxyHost = `127.0.0.1:${wsProxy.port}`;
    const c = client(
      wsProxy,
      upgradeRequest({ host: proxyHost, origin: wsProxy.origin, referer: `${wsProxy.origin}/page` }),
    );
    const head = (await c.waitFor(headEnd)).toString('latin1');
    assert.match(head, /^HTTP\/1\.1 101 /);
    assert.ok(head.includes(`Sec-WebSocket-Accept: ${ACCEPT}`));
    const frame = Buffer.from([0x81, 0x85, 1, 2, 3, 4, 0x49, 0x67, 0x6f, 0x68, 0x6e]);
    const mark = head.indexOf('\r\n\r\n') + 4;
    c.socket.write(frame);
    const received = await c.waitFor((r) => r.length >= mark + frame.length);
    assert.deepEqual(received.subarray(mark, mark + frame.length), frame);

    assert.equal(ws.upgrades.length, 1);
    const seen = ws.upgrades[0];
    assert.equal(seen.url, '/socket?x=1');
    assert.equal(seen.headers.host, `127.0.0.1:${ws.port}`);
    assert.equal(seen.headers.origin, ws.origin);
    assert.equal(seen.headers.referer, `${ws.origin}/page`);
    assert.equal(seen.headers['sec-websocket-key'], KEY);
    assert.equal(seen.headers['sec-websocket-protocol'], 'vite-hmr');
    assert.equal(seen.headers.upgrade, 'websocket');
    c.socket.destroy();
  });

  test('refuses a foreign Host with 421 and the dev server sees nothing', async () => {
    const seenBefore = ws.upgrades.length;
    const c = client(wsProxy, upgradeRequest({ host: 'evil.example' }));
    const received = (await c.waitFor((r, ended) => ended)).toString('latin1');
    assert.equal(
      received,
      'HTTP/1.1 421 Misdirected Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n',
    );
    assert.equal(ws.upgrades.length, seenBefore);
  });

  test('refuses an absolute-form upgrade with 400', async () => {
    const seenBefore = ws.upgrades.length;
    const c = client(
      wsProxy,
      upgradeRequest({ host: `127.0.0.1:${wsProxy.port}`, path: 'http://evil.example/socket' }),
    );
    const received = (await c.waitFor((r, ended) => ended)).toString('latin1');
    assert.equal(
      received,
      'HTTP/1.1 400 Bad Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n',
    );
    assert.equal(ws.upgrades.length, seenBefore);
  });

  test('forwards bytes sent with the handshake (the upgrade head)', async () => {
    // One write, so the bytes after the blank line reach the proxy as the upgrade's `head`.
    const c = client(wsProxy, `${upgradeRequest({ host: `127.0.0.1:${wsProxy.port}` })}early-bytes`);
    const received = await c.waitFor((r) => r.includes('early-bytes'));
    assert.match(received.toString('latin1'), /^HTTP\/1\.1 101 /);
  });

  test('an upstream that closes ends the browser socket',{ timeout: 10000 }, async () => {
    const ownWs = await startWsUpstream();
    const own = await startProxy({ target: ownWs.origin, studio: STUDIO, bridgeFile });
    closers.push(() => own.close(), () => ownWs.close());
    const c = client(own, upgradeRequest({ host: `127.0.0.1:${own.port}` }));
    await c.waitFor(headEnd);
    await ownWs.close();
    await c.waitFor((r, ended) => ended);
  });

  test('close() destroys an open upgraded socket and resolves', { timeout: 10000 }, async () => {
    const own = await startProxy({ target: ws.origin, studio: STUDIO, bridgeFile });
    const c = client(own, upgradeRequest({ host: `127.0.0.1:${own.port}` }));
    await c.waitFor(headEnd);
    await own.close();
    await c.waitFor((r, ended) => ended);
  });
});

test('parseProxyTarget returns local http targets and refuses the rest with a ProxyTargetError', () => {
  assert.equal(parseProxyTarget('http://localhost:3000/a?b=1').port, '3000');
  assert.equal(parseProxyTarget('http://127.0.0.1:3000').hostname, '127.0.0.1');
  for (const bad of ['https://localhost:3000', 'http://example.com', 'not a url', 'ftp://localhost']) {
    assert.throws(
      () => parseProxyTarget(bad),
      (error) =>
        error instanceof ProxyTargetError &&
        error.message === 'Font Kit Studio proxies only a local dev server (localhost or 127.0.0.1)',
    );
  }
});

describe('warnings about pages the bridge may not reach (R1.6)', () => {
  const OWN_BRIDGE_PAGE = '<html><head><script src="/js/fontkit-bridge.js"></script></head><body>x</body></html>';
  const CSP_META_PAGE = `<html><head><meta http-equiv="Content-Security-Policy" content="script-src 'nonce-q'"></head></html>`;
  const FINE_META_PAGE = `<html><head><meta http-equiv="Content-Security-Policy" content="script-src 'self'"></head></html>`;
  let warn;
  let lines;
  let warnProxy;

  const csp = (value, name = 'content-security-policy') => ({ ...HTML, [name]: value });

  before(async () => {
    warn = await startUpstream({
      '/own-bridge': { headers: HTML, body: OWN_BRIDGE_PAGE },
      '/own-bridge-2': { headers: HTML, body: OWN_BRIDGE_PAGE },
      '/own-bridge-json': { headers: { 'content-type': 'application/json' }, body: OWN_BRIDGE_PAGE },
      '/plain': { headers: HTML, body: PAGE },
      '/csp-header': { headers: csp("script-src 'nonce-q'"), body: PAGE },
      '/csp-header-2': { headers: csp("default-src 'none'"), body: PAGE },
      '/csp-fine': { headers: csp("script-src 'self'"), body: PAGE },
      '/csp-report-only': {
        headers: csp("script-src 'none'", 'content-security-policy-report-only'),
        body: PAGE,
      },
      '/csp-meta': { headers: HTML, body: CSP_META_PAGE },
      '/csp-meta-fine': { headers: HTML, body: FINE_META_PAGE },
      '/csp-and-own': { headers: csp("script-src 'nonce-q'"), body: OWN_BRIDGE_PAGE },
    });
  });
  after(() => warn.close());

  // A fresh proxy per case: "once per run" is a property of one proxy.
  async function fresh(tests) {
    lines = [];
    warnProxy = await startProxy({
      target: warn.origin,
      studio: STUDIO,
      bridgeFile,
      log: (line) => lines.push(line),
    });
    try {
      await tests();
    } finally {
      await warnProxy.close();
    }
  }
  const page = (path) => get(path, { via: warnProxy });

  test('a page that loads its own bridge is still tagged and warns once across two pages', () =>
    fresh(async () => {
      const first = await page('/own-bridge');
      await page('/own-bridge-2');
      assert.ok(first.body.toString().includes(TAG));
      assert.deepEqual(lines, [BRIDGE_TWICE_MESSAGE]);
    }));

  test('a page without its own bridge, and a non-HTML answer, say nothing', () =>
    fresh(async () => {
      await page('/plain');
      await page('/own-bridge-json');
      assert.deepEqual(lines, []);
    }));

  test('a blocking CSP header warns once across two pages', () =>
    fresh(async () => {
      const first = await page('/csp-header');
      await page('/csp-header-2');
      assert.equal(first.headers['content-security-policy'], "script-src 'nonce-q'");
      assert.ok(first.body.toString().includes(TAG));
      assert.deepEqual(lines, [CSP_MESSAGE]);
    }));

  test('a blocking CSP meta tag warns', () =>
    fresh(async () => {
      await page('/csp-meta');
      assert.deepEqual(lines, [CSP_MESSAGE]);
    }));

  test('a CSP that allows self, or only reports, says nothing', () =>
    fresh(async () => {
      for (const path of ['/csp-fine', '/csp-report-only', '/csp-meta-fine']) await page(path);
      assert.deepEqual(lines, []);
    }));

  test('a page with both problems prints each message once, in order', () =>
    fresh(async () => {
      await page('/csp-and-own');
      await page('/csp-and-own');
      assert.deepEqual(lines, [BRIDGE_TWICE_MESSAGE, CSP_MESSAGE]);
    }));
});
