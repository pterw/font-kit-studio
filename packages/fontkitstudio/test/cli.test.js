import { after, before, test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { cpSync, existsSync, mkdtempSync, readFileSync, realpathSync, rmSync, writeFileSync } from 'node:fs';
import { connect, createServer as createNetServer } from 'node:net';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { bundle } from '../scripts/bundle.js';
import { USAGE, main } from '../src/cli.js';
import { fakeProject } from './helpers/fake-project.js';

const BIN = fileURLToPath(new URL('../bin/fontkitstudio.js', import.meta.url));
const { version } = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
const run = (...args) => spawnSync(process.execPath, [BIN, ...args], { encoding: 'utf8' });

test('--version prints the package version', () => {
  const result = run('--version');
  assert.equal(result.status, 0);
  assert.equal(result.stdout, `${version}\n`);
});

test('--help prints usage', () => {
  const result = run('--help');
  assert.equal(result.status, 0);
  assert.match(result.stdout, /^Usage: fontkitstudio/);
});

test('an unknown argument exits 2 and names it', () => {
  const result = run('--bogus');
  assert.equal(result.status, 2);
  assert.match(result.stderr, /unknown argument "--bogus"/);
  assert.match(result.stderr, /Usage: fontkitstudio/);
});

// ---- the command's arguments (R1.4d) ----
const dirs = [];
after(() => {
  for (const dir of dirs) rmSync(dir, { recursive: true, force: true });
});

before(() => {
  // Only the in-process tests that really start Studio need the bundled copy; refusals do not.
  if (!existsSync(new URL('../dist/fontkit-studio.html', import.meta.url))) bundle();
});

function project(options) {
  const dir = fakeProject(options);
  dirs.push(dir);
  return dir;
}

function runIn(cwd, ...args) {
  return spawnSync(process.execPath, [BIN, ...args], { encoding: 'utf8', cwd, timeout: 20000 });
}

function assertUsageError(result, text) {
  assert.equal(result.status, 2, result.stderr);
  assert.equal(result.stdout, '');
  assert.ok(result.stderr.startsWith(text), result.stderr);
}

test('a folder that is not a Vite project exits 2 and names the folder and the fallback', () => {
  const dir = project({ vite: null });
  const result = runIn(dir);
  assert.equal(result.status, 2);
  assert.equal(
    result.stderr,
    `Font Kit Studio found no Vite project in ${realpathSync(dir)}. Run it in your Vite project, or give your dev server's address: npx fontkitstudio http://localhost:3000\n`,
  );
  assert.equal(result.stdout, '');
});

test('--no-open and --studio-port do not turn a non-Vite folder into a Vite project', () => {
  const dir = project({ vite: null });
  const result = runIn(dir, '--no-open', '--studio-port=5123');
  assert.equal(result.status, 2);
  assert.match(result.stderr, /^Font Kit Studio found no Vite project in /);
});

test('an untested Vite major exits 1 with the project message', () => {
  const dir = project({ vite: '9.0.0' });
  const result = runIn(dir, '--no-open');
  assert.equal(result.status, 1);
  assert.equal(
    result.stderr,
    'This project uses Vite 9.0.0. Font Kit Studio is tested with Vite 7 and 8; use one of those versions.\n',
  );
});

test('a project that lists Vite but has none installed exits 1 and says to install it', () => {
  const dir = project({ vite: null });
  writeFileSync(
    join(dir, 'package.json'),
    JSON.stringify({ name: 'app', devDependencies: { vite: '^8.0.0' } }),
  );
  const result = runIn(dir, '--no-open');
  assert.equal(result.status, 1);
  assert.equal(result.stderr, `Vite is not installed in ${realpathSync(dir)}. Run npm install there, then try again.\n`);
});

for (const bad of ['0', '70000', 'abc', '1.5', '-1', '']) {
  test(`--studio-port ${JSON.stringify(bad)} exits 2`, () => {
    assertUsageError(
      runIn(project({ vite: null }), '--studio-port', bad),
      'fontkitstudio: --studio-port needs a port number from 1 to 65535\n',
    );
  });
}

test('--studio-port=abc and a missing port value exit 2', () => {
  const dir = project({ vite: null });
  const text = 'fontkitstudio: --studio-port needs a port number from 1 to 65535\n';
  assertUsageError(runIn(dir, '--studio-port=abc'), text);
  assertUsageError(runIn(dir, '--studio-port'), text);
});

test('two positional arguments exit 2', () => {
  assertUsageError(
    runIn(project({ vite: null }), 'a', 'b'),
    'fontkitstudio: give one dev server address, not two\n',
  );
});

test('an argument that is not a URL exits 2 and quotes it', () => {
  assertUsageError(
    runIn(project({ vite: null }), 'not a url'),
    'fontkitstudio: "not a url" is not a URL. Give your dev server\'s address, such as http://localhost:3000\n',
  );
});

test('an https or remote address exits 2 with the proxy message', () => {
  const dir = project({ vite: null });
  for (const url of ['https://localhost:3000', 'http://example.com']) {
    const result = runIn(dir, url, '--no-open');
    assert.equal(result.status, 2, `${url}: ${result.stderr}`);
    assert.equal(result.stderr, 'Font Kit Studio proxies only a local dev server (localhost or 127.0.0.1)\n');
    assert.equal(result.stdout, '');
  }
});

test('an unknown flag still wins over a good URL, in any order', () => {
  const result = runIn(project({ vite: null }), 'http://localhost:3000', '--bogus');
  assert.equal(result.status, 2);
  assert.match(result.stderr, /unknown argument "--bogus"/);
  assert.match(result.stderr, /Usage: fontkitstudio \[<url>\]/);
});

test('--help states both forms and the two options', () => {
  const result = run('--help');
  for (const text of ['--no-open', '--studio-port <n>', 'fontkitstudio http://localhost:3000']) {
    assert.ok(result.stdout.includes(text), text);
  }
});

test('USAGE names the running version', () => {
  assert.ok(USAGE.includes(`Font Kit Studio ${version}: try type on your running web app, in development only.`));
});

test('no message carries a stack trace', () => {
  const result = runIn(project({ vite: '9.0.0' }), '--no-open');
  assert.doesNotMatch(result.stderr, /\n\s+at /);
});

// ---- opening the browser, in process with an injected opener ----
function stubVite(dir) {
  writeFileSync(
    join(dir, 'node_modules', 'vite', 'dist', 'node', 'index.js'),
    `export async function createServer() {
  return {
    resolvedUrls: { local: ['http://localhost:5173/'] },
    async listen() {},
    printUrls() {},
    async close() {},
  };
}\n`,
  );
}

function refused(port) {
  return new Promise((resolve) => {
    const socket = connect(port, '127.0.0.1');
    socket.on('connect', () => socket.destroy(() => resolve(false)));
    socket.on('error', () => resolve(true));
  });
}

function sink() {
  const chunks = [];
  return { write: (text) => chunks.push(text), text: () => chunks.join('') };
}

// Starts the command in process; the runner keeps SIGTERM handlers, so emitting it closes it.
async function startCommand(argv, cwd) {
  const opened = [];
  const out = sink();
  const err = sink();
  const code = await main(argv, { out, err, cwd, openUrl: (url) => opened.push(url) });
  const stop = async () => {
    process.emit('SIGTERM');
    const studioPort = Number(/Open: http:\/\/127\.0\.0\.1:(\d+)\//.exec(out.text())?.[1]);
    const deadline = Date.now() + 5000;
    while (studioPort && !(await refused(studioPort))) {
      assert.ok(Date.now() < deadline, 'Studio did not stop');
      await new Promise((resolve) => setImmediate(resolve));
    }
  };
  return { code, opened, out, err, stop };
}

test('a Vite project opens the browser on the Open: URL unless --no-open', async () => {
  const dir = project();
  stubVite(dir);
  const withOpen = await startCommand([], dir);
  try {
    assert.equal(withOpen.code, 0, withOpen.err.text());
    const lines = withOpen.out.text().split('\n');
    assert.equal(lines[0], 'Font Kit Studio · dev only');
    assert.match(lines[1], /^Open: http:\/\/127\.0\.0\.1:\d+\//);
    assert.deepEqual(withOpen.opened, [lines[1].slice('Open: '.length)]);
  } finally {
    await withOpen.stop();
  }
  const quiet = await startCommand(['--no-open'], dir);
  try {
    assert.equal(quiet.code, 0, quiet.err.text());
    assert.match(quiet.out.text(), /^Font Kit Studio · dev only\nOpen: http:\/\/127\.0\.0\.1:\d+\//);
    assert.deepEqual(quiet.opened, []);
  } finally {
    await quiet.stop();
  }
});

test('--studio-port reaches Studio in a Vite project', async () => {
  const dir = project();
  stubVite(dir);
  const probe = createNetServer();
  await new Promise((resolve) => probe.listen(0, '127.0.0.1', resolve));
  const { port } = probe.address();
  await new Promise((resolve) => probe.close(resolve));
  const started = await startCommand(['--no-open', `--studio-port=${port}`], dir);
  try {
    assert.equal(started.code, 0, started.err.text());
    assert.match(started.out.text(), new RegExp(`Open: http://127\.0\.0\.1:${port}/`));
  } finally {
    await started.stop();
  }
});

test('a URL argument runs the proxy and opens unless --no-open', async () => {
  const dir = project({ vite: null });
  const withOpen = await startCommand(['http://localhost:3000'], dir);
  try {
    assert.equal(withOpen.code, 0, withOpen.err.text());
    assert.equal(withOpen.opened.length, 1);
    assert.match(withOpen.opened[0], /^http:\/\/127\.0\.0\.1:\d+\/.*target=/);
  } finally {
    await withOpen.stop();
  }
  const quiet = await startCommand(['--no-open', 'http://localhost:3000'], dir);
  try {
    assert.equal(quiet.code, 0, quiet.err.text());
    assert.deepEqual(quiet.opened, []);
  } finally {
    await quiet.stop();
  }
});

// ---- refusals happen before any server starts ----
test('a refused URL beside a busy --studio-port exits 2 with the refusal and no fallback line', async () => {
  const holder = createNetServer();
  await new Promise((resolve) => holder.listen(0, '127.0.0.1', resolve));
  try {
    const { port } = holder.address();
    for (const url of ['https://localhost:3000', 'http://example.com']) {
      const result = runIn(project({ vite: null }), url, '--studio-port', String(port));
      assert.equal(result.status, 2, result.stderr);
      assert.equal(result.stderr, 'Font Kit Studio proxies only a local dev server (localhost or 127.0.0.1)\n');
      assert.doesNotMatch(result.stderr, /busy/);
    }
  } finally {
    await new Promise((resolve) => holder.close(resolve));
  }
});

test('with no dist/ at all, a refused URL still exits 2 with the refusal', () => {
  const copy = mkdtempSync(join(tmpdir(), 'fks-nodist-'));
  dirs.push(copy);
  for (const name of ['bin', 'src', 'package.json']) {
    cpSync(fileURLToPath(new URL(`../${name}`, import.meta.url)), join(copy, name), { recursive: true });
  }
  assert.equal(existsSync(join(copy, 'dist')), false);
  const result = spawnSync(process.execPath, [join(copy, 'bin', 'fontkitstudio.js'), 'http://example.com'], {
    encoding: 'utf8',
    timeout: 20000,
  });
  assert.equal(result.status, 2, result.stderr);
  assert.equal(result.stderr, 'Font Kit Studio proxies only a local dev server (localhost or 127.0.0.1)\n');
});

test('an address that parses but is not http or https gets the not-a-URL message', () => {
  for (const arg of ['localhost:3000', 'ftp://x']) {
    assertUsageError(
      runIn(project({ vite: null }), arg),
      `fontkitstudio: ${JSON.stringify(arg)} is not a URL. Give your dev server's address, such as http://localhost:3000\n`,
    );
  }
});
