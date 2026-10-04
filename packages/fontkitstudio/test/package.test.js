import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const PKG_DIR = fileURLToPath(new URL('..', import.meta.url));
const pkg = JSON.parse(readFileSync(join(PKG_DIR, 'package.json'), 'utf8'));

test('has no runtime dependencies (spec 4.5, D030)', () => {
  for (const field of ['dependencies', 'optionalDependencies', 'bundleDependencies',
    'bundledDependencies', 'devDependencies']) {
    const value = pkg[field];
    assert.ok(value === undefined || Object.keys(value).length === 0,
      `${field} must stay empty: Font Kit Studio ships with zero dependencies`);
  }
  const peers = Object.keys(pkg.peerDependencies ?? {});
  for (const name of peers) {
    assert.equal(name, 'vite', `only the project's own Vite may be a peer, found ${name}`);
    assert.equal(pkg.peerDependenciesMeta?.[name]?.optional, true,
      `peer ${name} must be optional so npm never installs it`);
  }
});

function sourceFiles(dir) {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? sourceFiles(path) : /\.(c|m)?js$/.test(path) ? [path] : [];
  });
}

const SPECIFIER = new RegExp([
  // import 'x', import a from 'x', export * from 'x', export { a } from 'x'
  /\b(?:import|export)\s*(?:[^'"()]*?\bfrom\s*)?['"]([^'"]+)['"]/,
  // import('x'), import('x', { with: ... })
  /\bimport\(\s*['"]([^'"]+)['"]/,
  // require('x'), createRequire(import.meta.url)('x')
  /\brequire\(\s*['"]([^'"]+)['"]\s*\)/,
  /\bcreateRequire\([^)]*\)\(\s*['"]([^'"]+)['"]/,
].map((pattern) => pattern.source).join('|'), 'g');

test('shipped code imports only node built-ins and its own files', () => {
  for (const file of ['bin', 'src'].flatMap((dir) => sourceFiles(join(PKG_DIR, dir)))) {
    for (const match of readFileSync(file, 'utf8').matchAll(SPECIFIER)) {
      const spec = match[1] ?? match[2] ?? match[3] ?? match[4];
      assert.ok(spec.startsWith('node:') || spec.startsWith('.'),
        `${file} imports ${spec}: only node:* and relative imports are allowed`);
    }
  }
});

test('declares what npm needs to run and ship it', () => {
  assert.equal(pkg.type, 'module');
  assert.equal(pkg.engines.node, '>=22.12');
  assert.equal(pkg.bin.fontkitstudio, 'bin/fontkitstudio.js');
  assert.deepEqual(pkg.files, ['bin/', 'src/', 'dist/']);
  const bin = readFileSync(join(PKG_DIR, pkg.bin.fontkitstudio), 'utf8');
  // .gitattributes pins LF: with CRLF, Linux and macOS look for an interpreter named "node\r".
  assert.ok(bin.startsWith('#!/usr/bin/env node\n'), 'the bin needs an LF node shebang');
});
