import { after, before, describe, test } from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { createServer, request } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { BRIDGE_PATH, fontkitStudio } from '../src/vite-plugin.js';

const BRIDGE_TEXT = '// bridge marker\n';
const STUDIO_MARKER = 'Font Kit Studio vT';
const LINE_PREFIX = '  Font Kit Studio: ';
const ORIGIN_ERROR =
  'Font Kit Studio: studio.origin must be a local http origin such as http://127.0.0.1:5000';

function fakeViteServer({ local = 'http://localhost:5173/', withHttpServer = true } = {}) {
  const logs = [];
  const handlers = [];
  const server = {
    config: { logger: { info: (line) => logs.push(line) } },
    httpServer: withHttpServer ? new EventEmitter() : null,
    middlewares: { use: (fn) => handlers.push(fn) },
    resolvedUrls: null,
    printUrls() {
      logs.push('vite urls');
    },
    async close() {
      logs.push('vite closed');
      server.httpServer?.emit('close');
    },
  };
  return {
    server,
    logs,
    handlers,
    listen() {
      server.resolvedUrls = { local: [local], network: [] };
    },
  };
}

function fetchRaw(url, method = 'GET') {
  return new Promise((resolve, reject) => {
    const req = request(url, { method, agent: false }, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () =>
        resolve({ status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks).toString() }),
      );
    });
    req.on('error', reject);
    req.end();
  });
}

async function assertRefused(url) {
  await assert.rejects(fetchRaw(url), (error) => {
    assert.equal(error.code, 'ECONNREFUSED');
    return true;
  });
}

function studioUrlFrom(logs) {
  const lines = logs.filter((l) => l.startsWith(LINE_PREFIX));
  assert.equal(lines.length, 1);
  return lines[0].slice(LINE_PREFIX.length);
}

describe('fontkitStudio Vite plugin', () => {
  let dir;
  let bridgeFile;
  let studioFile;
  const cleanups = [];

  before(() => {
    dir = mkdtempSync(join(tmpdir(), 'fks-vite-'));
    bridgeFile = join(dir, 'fontkit-bridge.js');
    studioFile = join(dir, 'fontkit-studio.html');
    writeFileSync(bridgeFile, BRIDGE_TEXT);
    writeFileSync(studioFile, `<title>${STUDIO_MARKER}</title>`);
  });

  after(async () => {
    for (const cleanup of cleanups) await cleanup();
    rmSync(dir, { recursive: true, force: true });
  });

  // Mount the captured middleware on a real loopback server whose fallback answers 404 "next".
  async function mount(handler) {
    const http = createServer((req, res) =>
      handler(req, res, () => {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('next');
      }),
    );
    await new Promise((resolve) => http.listen(0, '127.0.0.1', resolve));
    cleanups.push(
      () =>
        new Promise((resolve) => {
          http.close(() => resolve());
          http.closeAllConnections();
        }),
    );
    return `http://127.0.0.1:${http.address().port}`;
  }

  async function readyPlugin() {
    const plugin = fontkitStudio({
      studio: { origin: 'http://127.0.0.1:5999', url: (t) => `http://127.0.0.1:5999/?t=${t}` },
      bridgeFile,
    });
    const fake = fakeViteServer();
    await plugin.configureServer(fake.server);
    return { plugin, fake, base: await mount(fake.handlers[0]) };
  }

  // Standalone plugins start a real Studio server; close it if a test fails before its own close.
  function standalone(fakeOptions) {
    const plugin = fontkitStudio({ bridgeFile, studioFile });
    const fake = fakeViteServer(fakeOptions);
    cleanups.push(() => fake.server.httpServer?.emit('close') ?? fake.server.close());
    return { plugin, fake };
  }

  test('is named fontkit-studio and applies to serve only', () => {
    const plugin = fontkitStudio();
    assert.equal(plugin.name, 'fontkit-studio');
    assert.equal(plugin.apply, 'serve');
    assert.equal(BRIDGE_PATH, '/@fontkit/fontkit-bridge.js');
  });

  test('tags every page with one classic same-origin script and no inline code', () => {
    const plugin = fontkitStudio({
      studio: { origin: 'http://127.0.0.1:5999', url: () => 'unused' },
      bridgeFile,
    });
    const tags = plugin.transformIndexHtml('<html></html>');
    assert.deepEqual(tags, [
      {
        tag: 'script',
        attrs: { src: '/@fontkit/fontkit-bridge.js', 'data-allowed-origins': 'http://127.0.0.1:5999' },
        injectTo: 'head-prepend',
      },
    ]);
    for (const name of ['type', 'async', 'defer']) assert.ok(!(name in tags[0].attrs), name);
    assert.ok(!('children' in tags[0]));
  });

  test('serves the bridge on the exact path, with or without a query', async () => {
    const { base } = await readyPlugin();
    for (const path of [BRIDGE_PATH, `${BRIDGE_PATH}?v=1`]) {
      const res = await fetchRaw(base + path);
      assert.equal(res.status, 200);
      assert.equal(res.body, BRIDGE_TEXT);
      assert.equal(res.headers['content-type'], 'text/javascript; charset=utf-8');
      assert.equal(res.headers['content-length'], String(Buffer.byteLength(BRIDGE_TEXT)));
      assert.equal(res.headers['cache-control'], 'no-store');
      assert.equal(res.headers['x-content-type-options'], 'nosniff');
    }
    const head = await fetchRaw(base + BRIDGE_PATH, 'HEAD');
    assert.equal(head.status, 200);
    assert.equal(head.body, '');
    assert.equal(head.headers['content-length'], String(Buffer.byteLength(BRIDGE_TEXT)));
  });

  test('passes every other request to next', async () => {
    const { base } = await readyPlugin();
    const cases = [
      ['GET', '/'],
      ['GET', '/@fontkit/other.js'],
      ['GET', '/@fontkit/../package.json'],
      ['GET', `${BRIDGE_PATH}/`],
      ['GET', '/%40fontkit/fontkit-bridge.js'],
      ['GET', `//evil.test${BRIDGE_PATH}`],
      ['GET', '//['],
      ['POST', BRIDGE_PATH],
    ];
    for (const [method, path] of cases) {
      const res = await fetchRaw(base + path, method);
      assert.equal(res.status, 404, `${method} ${path}`);
      assert.equal(res.body, 'next', `${method} ${path}`);
    }
  });

  test('refuses an origin that is not a local http origin, without echoing it', () => {
    const bad = [
      'http://example.com:5999',
      'https://127.0.0.1:5999',
      'http://10.0.0.5:5999',
      'http://127.0.0.1:5999/path',
      'javascript:alert(1)',
      '',
    ];
    for (const origin of bad) {
      assert.throws(
        () => fontkitStudio({ studio: { origin, url: () => '' }, bridgeFile }),
        (error) => {
          assert.equal(error.message, ORIGIN_ERROR);
          assert.ok(origin === '' || !error.message.includes(origin));
          return true;
        },
        origin,
      );
    }
  });

  test('standalone: starts Studio, prints its URL once, closes with the dev server', async () => {
    const { plugin, fake } = standalone();
    await plugin.configureServer(fake.server);
    fake.listen();
    fake.server.printUrls();
    fake.server.printUrls();

    assert.equal(fake.logs.filter((l) => l === 'vite urls').length, 2);
    assert.ok(fake.logs.findIndex((l) => l.startsWith(LINE_PREFIX)) > fake.logs.indexOf('vite urls'));
    const studioUrl = studioUrlFrom(fake.logs);
    assert.equal(new URL(studioUrl).searchParams.get('target'), 'http://localhost:5173/');
    const res = await fetchRaw(studioUrl);
    assert.equal(res.status, 200);
    assert.ok(res.body.includes(STUDIO_MARKER));

    const [tag] = plugin.transformIndexHtml('');
    assert.equal(tag.attrs['data-allowed-origins'], new URL(studioUrl).origin);

    fake.server.httpServer.emit('close');
    await assertRefused(studioUrl);
  });

  test('standalone without resolved URLs prints Studio without a target', async () => {
    const { plugin, fake } = standalone();
    await plugin.configureServer(fake.server);
    fake.server.printUrls();
    const studioUrl = studioUrlFrom(fake.logs);
    assert.equal(new URL(studioUrl).searchParams.get('target'), null);
    fake.server.httpServer.emit('close');
    await assertRefused(studioUrl);
  });

  test('standalone in middleware mode closes Studio when the server closes', async () => {
    const { plugin, fake } = standalone({ withHttpServer: false });
    await plugin.configureServer(fake.server);
    fake.listen();
    fake.server.printUrls();
    const studioUrl = studioUrlFrom(fake.logs);
    assert.equal((await fetchRaw(studioUrl)).status, 200);
    await fake.server.close();
    assert.ok(fake.logs.includes('vite closed'));
    await assertRefused(studioUrl);
  });

  test('a missing bridge file names the prepack step', async () => {
    const plugin = fontkitStudio({ bridgeFile: join(dir, 'missing.js'), studioFile });
    const fake = fakeViteServer();
    await assert.rejects(plugin.configureServer(fake.server), (error) => {
      assert.match(
        error.message,
        /^Font Kit Studio cannot read the bridge at .*missing\.js; run npm --prefix packages\/fontkitstudio run prepack$/,
      );
      return true;
    });
  });

  test('adds no tag before a Studio is known', () => {
    const plugin = fontkitStudio({ bridgeFile, studioFile });
    assert.deepEqual(plugin.transformIndexHtml('<html></html>'), []);
  });

  describe('one Studio when the command runs the project', () => {
    const STUDIO = { origin: 'http://127.0.0.1:5999', url: (t) => `http://127.0.0.1:5999/?t=${t}` };

    test("a plugin given a Studio exposes the command's api flag; a standalone one does not", () => {
      assert.deepEqual(fontkitStudio({ studio: STUDIO, bridgeFile }).api, {
        fontkitStudio: { fromCommand: true },
      });
      assert.equal(fontkitStudio({ bridgeFile, studioFile }).api, undefined);
    });

    test('a standalone instance stands down when the command added its own: no Studio, no middleware, no log, no tag', async () => {
      const mine = fontkitStudio({ bridgeFile, studioFile });
      const commands = fontkitStudio({ studio: STUDIO, bridgeFile });
      mine.configResolved({ plugins: [{ name: 'other' }, mine, commands] });
      const fake = fakeViteServer();
      await mine.configureServer(fake.server);
      fake.listen();
      fake.server.printUrls();
      assert.equal(fake.handlers.length, 0);
      assert.deepEqual(fake.logs, ['vite urls']);
      assert.equal(fake.server.httpServer.listenerCount('close'), 0);
      assert.deepEqual(mine.transformIndexHtml('<html></html>'), []);
      assert.equal(commands.transformIndexHtml('<html></html>').length, 1);
    });

    test('a standalone instance alone, or beside look-alikes, keeps working', async () => {
      const { plugin, fake } = standalone();
      plugin.configResolved({
        plugins: [
          plugin,
          { name: 'fontkit-studio' },
          { name: 'fontkit-studio', api: { fontkitStudio: { fromCommand: false } } },
          { name: 'other', api: { fontkitStudio: { fromCommand: true } } },
        ],
      });
      await plugin.configureServer(fake.server);
      assert.equal(fake.handlers.length, 1);
      assert.equal(plugin.transformIndexHtml('<html></html>').length, 1);
      fake.server.httpServer.emit('close');
    });

    test("the command's own instance never stands down", async () => {
      const commands = fontkitStudio({ studio: STUDIO, bridgeFile });
      commands.configResolved({ plugins: [commands, fontkitStudio({ studio: STUDIO, bridgeFile })] });
      const fake = fakeViteServer();
      await commands.configureServer(fake.server);
      assert.equal(fake.handlers.length, 1);
      assert.equal(commands.transformIndexHtml('<html></html>').length, 1);
    });
  });

  test('is importable as fontkitstudio/vite', async () => {
    const viaName = await import('fontkitstudio/vite');
    assert.equal(viaName.fontkitStudio, fontkitStudio);
  });
});
