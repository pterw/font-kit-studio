import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

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
