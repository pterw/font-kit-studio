import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { bundle } from '../scripts/bundle.js';
import { fakeRoot } from './helpers/fake-root.js';
import { guardRealBundle } from './helpers/real-bundle-guard.js';
import { scratchPackage } from './helpers/scratch-package.js';

guardRealBundle();

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

// The two tests below bundle and pack a scratch copy: see helpers/scratch-package.js.
test('npm pack ships the bundled files and nothing from test/ or scripts/', () => {
  const { root, packageDir: cwd } = scratchPackage();
  try {
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
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test('running the script through a directory link still bundles', () => {
  const { root, packageDir } = scratchPackage();
  const linkDir = mkdtempSync(join(tmpdir(), 'fks-link-'));
  const link = join(linkDir, 'pkg');
  // A junction needs no admin rights on Windows.
  symlinkSync(packageDir, link, process.platform === 'win32' ? 'junction' : 'dir');
  try {
    // The scratch copy starts with no dist/ and no LICENSE, so no stale copy can satisfy this.
    assert.equal(existsSync(join(packageDir, 'dist')), false);
    assert.equal(existsSync(join(packageDir, 'LICENSE')), false);
    const result = spawnSync(process.execPath, [join(link, 'scripts', 'bundle.js')], { encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
    assert.deepEqual(readFileSync(join(packageDir, 'dist', 'fontkit-studio.html')),
      readFileSync(join(root, 'fontkit-studio.html')));
    assert.deepEqual(readFileSync(join(packageDir, 'dist', 'fontkit-bridge.js')),
      readFileSync(join(root, 'fontkit-bridge.js')));
    assert.deepEqual(readFileSync(join(packageDir, 'LICENSE')), readFileSync(join(root, 'LICENSE')));
  } finally {
    rmSync(link, { force: true });
    rmSync(linkDir, { recursive: true, force: true });
    rmSync(root, { recursive: true, force: true });
  }
});
