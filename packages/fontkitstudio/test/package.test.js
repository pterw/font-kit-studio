import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync, readdirSync, rmSync, statSync } from 'node:fs';
import { execFileSync, execSync } from 'node:child_process';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { guardRealBundle } from './helpers/real-bundle-guard.js';
import { scratchPackage } from './helpers/scratch-package.js';

guardRealBundle();

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
    return statSync(path).isDirectory() ? sourceFiles(path) : /\.(c|m)?js$|\.d\.ts$/.test(path) ? [path] : [];
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
    if (file.endsWith('.d.ts')) continue; // declarations have their own, stricter guard below
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

// The project's own Vite is loaded by a computed path (createRequire + import()); only
// src/project.js may do that, so every other file stays checkable by the guard above.
test('only src/project.js loads code by a computed path', () => {
  const allowed = join(PKG_DIR, 'src', 'project.js');
  for (const file of ['bin', 'src'].flatMap((dir) => sourceFiles(join(PKG_DIR, dir)))) {
    if (file === allowed) continue;
    const text = readFileSync(file, 'utf8');
    assert.doesNotMatch(text, /\bcreateRequire\b/, `${file} uses createRequire`);
    assert.doesNotMatch(text, /\bimport\(\s*(?!['"])/, `${file} has a computed import()`);
    assert.doesNotMatch(text, /\brequire\(\s*(?!['"])/, `${file} has a computed require()`);
  }
});

test('exports["./vite"] ships its types and its code', () => {
  const entry = pkg.exports['./vite'];
  assert.equal(entry.default, './src/vite-plugin.js');
  assert.equal(typeof entry.types, 'string', 'exports["./vite"].types is missing');
  assert.ok(existsSync(join(PKG_DIR, entry.types)), `${entry.types} does not exist`);
  assert.ok(pkg.files.some((f) => entry.types.startsWith(`./${f}`)),
    `${entry.types} lies under no "files" entry, so npm would not ship it`);
});

// The one import a declaration may have is the project's own Vite, as a type: nothing to
// install, nothing loaded at run time.
test('declaration files import only vite, as types', () => {
  const declarations = sourceFiles(join(PKG_DIR, 'src')).filter((f) => f.endsWith('.d.ts'));
  assert.ok(declarations.length > 0, 'src/ has no .d.ts to guard');
  for (const file of declarations) {
    const text = readFileSync(file, 'utf8');
    for (const match of text.matchAll(SPECIFIER)) {
      const spec = match[1] ?? match[2] ?? match[3] ?? match[4];
      assert.equal(spec, 'vite', `${file} imports ${spec}: a declaration may import only vite`);
    }
    for (const match of text.matchAll(/^\s*import\b(?!\s+type\s)[^\n]*$/gm)) {
      assert.fail(`${file}: "${match[0].trim()}" must be an import type`);
    }
    assert.doesNotMatch(text, /\bimport\s*\(|\brequire\b/, `${file} loads a module by call`);
  }
});

// What the tarball holds is what users run: Studio, the bridge, the source and the docs, and
// nothing else. The expected list comes from src/ and bin/, so a new source file needs no edit
// here, but a stray file type (a fixture, a test, a scratch file) does.
//
// It packs a copy of the package in a scratch repository, not the real directory: other test
// files used to delete the real dist/ and LICENSE while they ran in parallel, which emptied
// this tarball on CI; no test touches them now (helpers/real-bundle-guard.js). The bundle step runs explicitly, so the list does not depend on
// npm running prepack either.
test('the tarball holds exactly the shipped files', () => {
  const { root, packageDir: dir } = scratchPackage();
  try {
    execFileSync(process.execPath, [join(dir, 'scripts', 'bundle.js')], { cwd: dir, stdio: 'pipe' });
    // One command string with shell: true: npm is npm.cmd on Windows, and an args array with
    // shell: true warns DEP0190. prepack prints a line before the JSON, so parse from the '['.
    const out = execSync('npm pack --dry-run --json', {
      cwd: dir, encoding: 'utf8', shell: true, stdio: ['ignore', 'pipe', 'pipe'],
    });
    const [{ files }] = JSON.parse(out.slice(out.indexOf('[')));
    const expected = [
      'LICENSE', 'README.md', 'package.json',
      ...['bin', 'src'].flatMap((d) => readdirSync(join(PKG_DIR, d))
        .filter((name) => /\.js$|\.d\.ts$/.test(name)).map((name) => `${d}/${name}`)),
      'dist/fontkit-studio.html', 'dist/fontkit-bridge.js',
    ].sort();
    assert.deepEqual(files.map((f) => f.path).sort(), expected);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
