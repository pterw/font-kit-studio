import { after, before, describe, test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { request } from 'node:http';
import { connect } from 'node:net';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

import { STUDIO_PATH, newToken, startStudioServer } from '../src/studio-server.js';

const MARKER = '<title>Font Kit Studio vT</title>';
const BODY = Buffer.from(`<!doctype html>${MARKER}<p>caf\u00e9</p>`);

let dir;
let server;

before(async () => {
  dir = mkdtempSync(join(tmpdir(), 'fks-studio-'));
  writeFileSync(join(dir, 'studio.html'), BODY);
  server = await startStudioServer({ studioFile: pathToFileURL(join(dir, 'studio.html')) });
});

after(async () => {
  await server.close();
  rmSync(dir, { recursive: true, force: true });
});

// node:http, not fetch: fetch cannot set Host.
function get(path, { method = 'GET', headers = {}, host = `127.0.0.1:${server.port}` } = {}) {
  return new Promise((resolve, reject) => {
    const req = request(
      { host: '127.0.0.1', port: server.port, path, method, headers: { Host: host, ...headers } },
      (res) => {
        const chunks = [];
        res.on('data', (chunk) => chunks.push(chunk));
        res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks) }));
      },
    );
    req.on('error', reject);
    req.end();
  });
}

const good = () => `${STUDIO_PATH}?token=${server.token}`;

function assertHardened(res) {
  assert.equal(res.headers['cache-control'], 'no-store');
  assert.equal(res.headers['referrer-policy'], 'no-referrer');
  assert.equal(res.headers['x-content-type-options'], 'nosniff');
}

describe('studio server', () => {
  test('the right token gets the Studio bytes with hardened headers', async () => {
    const res = await get(good());
    assert.equal(res.status, 200);
    assert.deepEqual(res.body, BODY);
    assert.equal(res.headers['content-type'], 'text/html; charset=utf-8');
    assertHardened(res);
  });

  test('HEAD with the token is 200 with an empty body', async () => {
    const res = await get(good(), { method: 'HEAD' });
    assert.equal(res.status, 200);
    assert.equal(res.body.length, 0);
    assertHardened(res);
  });

  test('a missing or wrong token is 403 and shows no Studio', async () => {
    const right = server.token;
    const sameLength = right.replace(/^./, right[0] === 'A' ? 'B' : 'A');
    const paths = [
      STUDIO_PATH,
      `${STUDIO_PATH}?token=${sameLength}`,
      `${STUDIO_PATH}?token=short`,
      `${STUDIO_PATH}?TOKEN=${right}`,
      `${STUDIO_PATH}?token=${sameLength}&token=${right}`,
    ];
    for (const path of paths) {
      const res = await get(path);
      assert.equal(res.status, 403, path);
      assert.ok(!res.body.includes(MARKER), path);
      assert.equal(res.body.toString(), 'Missing or wrong token. Open the URL the fontkitstudio command printed.');
      assertHardened(res);
    }
  });

  test('a foreign, wrong-port or empty Host is 421; LOCALHOST is fine', async () => {
    for (const host of [`evil.test:${server.port}`, `127.0.0.1:${server.port + 1}`]) {
      const res = await get(good(), { host });
      assert.equal(res.status, 421, JSON.stringify(host));
      assert.equal(res.body.toString(), 'Host header not allowed.');
      assertHardened(res);
    }
    // The http client replaces an empty Host, so send it over a raw socket.
    const raw = await new Promise((resolve, reject) => {
      const socket = connect(server.port, '127.0.0.1', () => {
        socket.write(`GET ${good()} HTTP/1.1\r\nHost: \r\nConnection: close\r\n\r\n`);
      });
      let text = '';
      socket.on('data', (chunk) => { text += chunk; });
      socket.on('end', () => resolve(text));
      socket.on('error', reject);
    });
    assert.match(raw, /^HTTP\/1\.1 421 /);
    assert.ok(!raw.includes(MARKER));
    const res = await get(good(), { host: `LOCALHOST:${server.port}` });
    assert.equal(res.status, 200);
  });

  test('a foreign or null Origin is 403; the same-origin Origin is fine', async () => {
    for (const origin of ['http://evil.test', 'null']) {
      const res = await get(good(), { headers: { Origin: origin } });
      assert.equal(res.status, 403, origin);
      assert.equal(res.body.toString(), 'Origin not allowed.');
      assertHardened(res);
    }
    const res = await get(good(), { headers: { Origin: `http://127.0.0.1:${server.port}` } });
    assert.equal(res.status, 200);
  });

  test('POST, PUT and OPTIONS are 405 with Allow', async () => {
    for (const method of ['POST', 'PUT', 'OPTIONS']) {
      const res = await get(good(), { method });
      assert.equal(res.status, 405, method);
      assert.equal(res.headers.allow, 'GET, HEAD');
      assert.equal(res.body.toString(), 'Only GET and HEAD.');
      assertHardened(res);
    }
  });

  test('any other path is 404', async () => {
    for (const path of ['/', `${STUDIO_PATH}/`, '/%2e%2e/etc/passwd', '/fontkit-bridge.js']) {
      const res = await get(`${path}?token=${server.token}`);
      assert.equal(res.status, 404, path);
      assert.equal(res.body.toString(), 'Not found. Open the URL the fontkitstudio command printed.');
      assertHardened(res);
    }
  });

  test('checks run in order: Host, Origin, method, path, then token', async () => {
    const wrong = `${STUDIO_PATH}?token=wrong`;
    const origin = await get(wrong, { headers: { Origin: 'http://evil.test' } });
    assert.equal(origin.status, 403);
    assert.equal(origin.body.toString(), 'Origin not allowed.');
    assert.equal((await get(wrong, { method: 'POST' })).status, 405);
    assert.equal((await get('/nope?token=wrong')).status, 404);
  });

  test('a non-loopback host is refused and a missing file names its path', async () => {
    await assert.rejects(
      startStudioServer({ host: '0.0.0.0', studioFile: pathToFileURL(join(dir, 'studio.html')) }),
      /refusing to bind 0\.0\.0\.0: Studio is served on loopback only/,
    );
    const missing = join(dir, 'absent.html');
    await assert.rejects(
      startStudioServer({ studioFile: pathToFileURL(missing) }),
      (error) => error.message.includes('absent.html') && error.message.includes('prepack'),
    );
  });

  test('newToken is 43 base64url characters and differs per call', () => {
    const a = newToken();
    assert.match(a, /^[A-Za-z0-9_-]{43}$/);
    assert.notEqual(a, newToken());
  });

  test('url() carries token and target and they parse back', () => {
    const target = 'http://localhost:5173/a?b=c&d=e';
    const parsed = new URL(server.url(target));
    assert.equal(parsed.origin, server.origin);
    assert.equal(parsed.pathname, STUDIO_PATH);
    assert.equal(parsed.searchParams.get('token'), server.token);
    assert.equal(parsed.searchParams.get('target'), target);
    assert.equal(new URL(server.url()).searchParams.has('target'), false);
  });
});
