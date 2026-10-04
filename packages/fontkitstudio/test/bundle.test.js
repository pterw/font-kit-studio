import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { bundle } from '../scripts/bundle.js';
import { fakeRoot } from './helpers/fake-root.js';

function fakePackage(version) {
  const dir = mkdtempSync(join(tmpdir(), 'fks-pkg-'));
  writeFileSync(join(dir, 'package.json'), JSON.stringify({ version }));
  return dir;
}

test('copies Studio, the bridge and the licence byte for byte', () => {
  const root = fakeRoot();
  const packageDir = fakePackage('1.2.3');
  bundle({ root, packageDir });
  for (const file of ['fontkit-studio.html', 'fontkit-bridge.js']) {
    assert.deepEqual(readFileSync(join(packageDir, 'dist', file)), readFileSync(join(root, file)));
  }
  assert.deepEqual(readFileSync(join(packageDir, 'LICENSE')), readFileSync(join(root, 'LICENSE')));
});

test('refuses a version mismatch before writing anything', () => {
  const packageDir = fakePackage('1.2.4');
  assert.throws(() => bundle({ root: fakeRoot(), packageDir }), /version mismatch/);
  assert.equal(existsSync(join(packageDir, 'dist')), false);
  assert.equal(existsSync(join(packageDir, 'LICENSE')), false);
});

test('npm pack ships the bundled files and nothing from test/ or scripts/', () => {
  const cwd = fileURLToPath(new URL('..', import.meta.url));
  // One fixed command string through the shell: Windows needs the shell to run npm.cmd, and
  // passing an args array with shell: true is deprecated (DEP0190).
  const result = spawnSync('npm pack --dry-run --json', { cwd, encoding: 'utf8', shell: true });
  assert.equal(result.status, 0, result.stderr);
  // prepack prints its own line before the JSON, so parse from the array's first line.
  const json = result.stdout.slice(result.stdout.search(/^\[/m));
  const files = JSON.parse(json)[0].files.map((f) => f.path).sort();
  for (const want of ['LICENSE', 'README.md', 'bin/fontkitstudio.js', 'dist/fontkit-bridge.js',
    'dist/fontkit-studio.html', 'package.json', 'src/cli.js']) {
    assert.ok(files.includes(want), `tarball lacks ${want}: ${files.join(', ')}`);
  }
  assert.equal(files.some((f) => f.startsWith('test/') || f.startsWith('scripts/')), false);
});
