import { after, before, describe, test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { createServer, request } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { CSP_MESSAGE } from '../src/csp.js';
import { runProxy, startStudio } from '../src/run-proxy.js';
import { startUpstream } from './helpers/upstream.js';

const HTML = { 'content-type': 'text/html; charset=utf-8' };
const BUSY_TEXT =
  /^Font Kit Studio: port (\d+) is busy, so Studio uses port (\d+); its saved settings stay with the old port\.\n$/;

let dir;
let studioFile;
let bridgeFile;
let upstream;
const cleanups = [];

before(async () => {
  dir = mkdtempSync(join(tmpdir(), 'fks-run-proxy-'));
  studioFile = join(dir, 'studio.html');
  bridgeFile = join(dir, 'bridge.js');
  writeFileSync(studioFile, '<!doctype html><title>Studio</title>');
  writeFileSync(bridgeFile, '// bridge\n');
  upstream = await startUpstream({
    '/app': { headers: HTML, body: '<!doctype html><html><head></head><body>app</body></html>' },
    '/csp': {
      headers: { ...HTML, 'content-security-policy': "script-src 'nonce-q'" },
      body: '<!doctype html><html><head></head><body>app</body></html>',
    },
  });
});

after(async () => {
  try {
    for (const cleanup of [...cleanups, () => upstream.close()]) {
      try {
        await cleanup();
      } catch {
        // keep cleaning
      }
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

function sink() {
  const chunks = [];
  return { write: (text) => chunks.push(text), text: () => chunks.join(''), chunks };
}

// Starts a run; the cleanup closes it too (close is idempotent).
async function start(options = {}) {
  const out = sink();
  const err = sink();
  const opened = [];
  const running = await runProxy({
    target: `http://localhost:${upstream.port}/app?x=1`,
    open: false,
    out,
    err,
    openUrl: (url, extra) => opened.push({ url, extra }),
    studioFile,
    bridgeFile,
    ...options,
  });
  cleanups.push(() => running.close());
  return { running, out, err, opened };
}

function get(url) {
  return new Promise((resolve, reject) => {
    const req = request(url, { agent: false }, (res) => {
      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () =>
        resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString('utf8') }),
      );
    });
    req.on('error', reject);
    req.end();
  });
}

async function refuses(url) {
  await assert.rejects(
    get(url),
    (error) => error.code === 'ECONNREFUSED' || error.cause?.code === 'ECONNREFUSED',
  );
}

describe('runProxy', () => {
  test('an IPv6-only fixed Studio conflict falls back with both listeners and the same warning', async () => {
    const holder = createServer();
    await new Promise((resolve, reject) => {
      holder.once('error', reject);
      holder.listen(0, '::1', resolve);
    });
    const port = holder.address().port;
    let studio;
    try {
      const err = sink();
      studio = await startStudio({ studioFile, studioPort: port, host: 'localhost', err });
      assert.notEqual(studio.port, port);
      assert.equal(new URL(studio.url()).hostname, 'localhost');
      assert.match(err.text(), BUSY_TEXT);
      for (const host of ['127.0.0.1', '[::1]']) {
        assert.equal((await get(studio.url().replace('localhost', host))).status, 200);
      }
      const probe = createServer();
      await new Promise((resolve, reject) => {
        probe.once('error', reject);
        probe.listen(port, '127.0.0.1', resolve);
      });
      await new Promise(resolve => probe.close(resolve));
    } finally {
      await studio?.close();
      await new Promise(resolve => holder.close(resolve));
    }
  });
  test('target hostname selects localhost only for localhost, preserving IP targets', async () => {
    for (const [hostname, advertised] of [['localhost', 'localhost'], ['127.0.0.1', '127.0.0.1'], ['[::1]', '127.0.0.1']]) {
      const { running } = await start({ target: `http://${hostname}:${upstream.port}/app?x=1#section` });
      try {
        assert.equal(new URL(running.studioUrl).hostname, advertised);
        assert.equal(new URL(running.proxyOrigin).hostname, advertised);
        assert.equal(new URL(running.studioUrl).searchParams.get('target'), `${running.proxyOrigin}/app?x=1#section`);
        assert.equal((await get(running.proxyOrigin + '/@fontkit/fontkit-bridge.js')).status, 200);
      } finally {
        await running.close();
      }
    }
  });
  test('prints exactly two lines; the Open URL has the token and the proxied target', async () => {
    const { running, out } = await start();
    assert.equal(out.chunks.length, 2);
    const lines = out.text().split('\n');
    assert.equal(lines.length, 3);
    assert.equal(lines[2], '');
    assert.equal(lines[0], 'Font Kit Studio · dev only');
    assert.ok(lines[1].startsWith('Open: '));
    const url = new URL(lines[1].slice('Open: '.length));
    assert.equal(url.origin, new URL(running.studioUrl).origin);
    assert.ok(url.searchParams.get('token').length > 20);
    assert.equal(url.searchParams.get('target'), `${running.proxyOrigin}/app?x=1`);
    assert.equal(lines[1], `Open: ${running.studioUrl}`);
    await running.close();
  });

  test('keeps a hash route in the proxied target', async () => {
    const { running } = await start({ target: `http://localhost:${upstream.port}/app?x=1#/settings` });
    try {
      const target = new URL(running.studioUrl).searchParams.get('target');
      assert.equal(target, `${running.proxyOrigin}/app?x=1#/settings`);
    } finally {
      await running.close();
    }
  });

  test('a GET of the printed target through the proxy is tagged', async () => {
    const { running } = await start();
    const target = new URL(running.studioUrl).searchParams.get('target');
    const page = await get(target);
    assert.equal(page.status, 200);
    assert.match(
      page.body,
      /<script src="\/@fontkit\/fontkit-bridge\.js" data-allowed-origins="http:\/\/localhost:\d+"><\/script>/,
    );
    await running.close();
  });

  test('open: true opens the Studio URL once, after both lines; open: false never', async () => {
    const seen = [];
    const out = sink();
    const running = await runProxy({
      target: `http://localhost:${upstream.port}/app`,
      out,
      err: sink(),
      studioFile,
      bridgeFile,
      openUrl: (url, extra) => seen.push({ url, written: out.text(), err: extra.err }),
    });
    cleanups.push(() => running.close());
    assert.equal(seen.length, 1);
    assert.equal(seen[0].url, running.studioUrl);
    assert.equal(seen[0].written, `Font Kit Studio · dev only\nOpen: ${running.studioUrl}\n`);
    assert.ok(seen[0].err);
    await running.close();

    const quiet = await start({ open: false });
    assert.deepEqual(quiet.opened, []);
    await quiet.running.close();
  });

  test('SIGINT closes both servers and the signal handlers go away', async () => {
    const names = process.platform === 'win32' ? ['SIGINT', 'SIGTERM', 'SIGBREAK'] : ['SIGINT', 'SIGTERM'];
    const baseline = Object.fromEntries(names.map((name) => [name, process.listenerCount(name)]));
    const { running } = await start();
    for (const name of names) assert.equal(process.listenerCount(name), baseline[name] + 1, name);
    const target = new URL(running.studioUrl).searchParams.get('target');
    assert.equal((await get(target)).status, 200);

    process.emit('SIGINT');
    await running.close(); // the same close the handler started: resolves once both are down
    await refuses(running.studioUrl);
    await refuses(target);
    for (const name of names) assert.equal(process.listenerCount(name), baseline[name], name);
  });

  test('close() is idempotent', async () => {
    const { running } = await start();
    await running.close();
    await running.close();
  });

  test('a target that is not local rejects, writes nothing and leaves no Studio server', async () => {
    const out = sink();
    const err = sink();
    await assert.rejects(
      runProxy({ target: 'http://example.com', open: false, out, err, studioFile, bridgeFile }),
      { message: 'Font Kit Studio proxies only a local dev server (localhost, 127.0.0.1 or [::1])' },
    );
    assert.deepEqual([out.chunks, err.chunks], [[], []]);
  });

  test('a rejected proxy closes the Studio server it started', async () => {
    // A studio server on a known port: the run must free it when the proxy start fails.
    const probe = createServer();
    await new Promise((resolve) => probe.listen(0, '127.0.0.1', resolve));
    const port = probe.address().port;
    await new Promise((resolve) => probe.close(resolve));
    await assert.rejects(
      runProxy({
        target: 'http://example.com',
        open: false,
        out: sink(),
        err: sink(),
        studioPort: port,
        studioFile,
        bridgeFile,
      }),
    );
    // The port is free again: a server can bind it.
    const again = createServer();
    cleanups.push(() => new Promise((resolve) => again.close(resolve)));
    await new Promise((resolve, reject) => {
      again.once('error', reject);
      again.listen(port, '127.0.0.1', resolve);
    });
  });

  test('a busy studioPort starts Studio elsewhere and says so', async () => {
    const holder = createServer();
    await new Promise((resolve) => holder.listen(0, '127.0.0.1', resolve));
    cleanups.push(() => new Promise((resolve) => holder.close(resolve)));
    const busy = holder.address().port;
    const { running, err } = await start({ studioPort: busy });
    const match = BUSY_TEXT.exec(err.text());
    assert.ok(match, err.text());
    assert.equal(Number(match[1]), busy);
    assert.notEqual(Number(match[2]), busy);
    assert.equal(new URL(running.studioUrl).port, match[2]);
    await running.close();
  });
});

test('a page whose policy blocks the bridge is reported once on err, not out', async () => {
  const { running, out, err } = await start({ target: `http://localhost:${upstream.port}/csp` });
  const proxied = new URL(running.proxyOrigin);
  await get(`${proxied.origin}/csp`);
  await get(`${proxied.origin}/csp`);
  assert.equal(err.text(), `${CSP_MESSAGE}\n`);
  assert.ok(!out.text().includes('Content-Security-Policy'));
});
