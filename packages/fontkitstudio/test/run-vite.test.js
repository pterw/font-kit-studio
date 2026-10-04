import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:net';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { ProjectError } from '../src/project.js';
import { runVite } from '../src/run-vite.js';
import { fakeProject } from './helpers/fake-project.js';

function freePort() {
  return new Promise((resolve, reject) => {
    const server = createServer();
    server.on('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      server.close(() => resolve(port));
    });
  });
}

function canBind(port) {
  return new Promise((resolve) => {
    const server = createServer();
    server.on('error', () => resolve(false));
    server.listen(port, '127.0.0.1', () => server.close(() => resolve(true)));
  });
}

test('an untested Vite refuses before any Studio starts', async () => {
  const dir = fakeProject({ vite: '9.0.0' });
  try {
    await assert.rejects(runVite({ projectDir: dir, open: false }), ProjectError);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test('when Vite fails to start, Studio is closed before the error is rethrown', async () => {
  const dir = fakeProject();
  const files = mkdtempSync(join(tmpdir(), 'fks-run-vite-'));
  const studioFile = join(files, 'studio.html');
  writeFileSync(studioFile, '<!doctype html><title>Studio</title>');
  try {
    // The fake Vite's createServer returns a string, so listen() fails.
    const port = await freePort();
    await assert.rejects(runVite({ projectDir: dir, open: false, studioPort: port, studioFile }), TypeError);
    assert.equal(await canBind(port), true, 'Studio still holds its port');
  } finally {
    rmSync(dir, { recursive: true, force: true });
    rmSync(files, { recursive: true, force: true });
  }
});

test('a Vite that reports no local address is closed with Studio and a plain message', async () => {
  const dir = fakeProject();
  const files = mkdtempSync(join(tmpdir(), 'fks-run-vite-'));
  const studioFile = join(files, 'studio.html');
  writeFileSync(studioFile, '<!doctype html><title>Studio</title>');
  writeFileSync(
    join(dir, 'node_modules', 'vite', 'dist', 'node', 'index.js'),
    `export async function createServer() {
  return { resolvedUrls: { local: [] }, async listen() {}, printUrls() {}, async close() { globalThis.__viteClosed = true; } };
}
`,
  );
  try {
    const port = await freePort();
    await assert.rejects(runVite({ projectDir: dir, open: false, studioPort: port, studioFile }), {
      message: 'Font Kit Studio could not tell which address Vite is serving on.',
    });
    assert.equal(globalThis.__viteClosed, true, 'Vite was not closed');
    assert.equal(await canBind(port), true, 'Studio still holds its port');
  } finally {
    delete globalThis.__viteClosed;
    rmSync(dir, { recursive: true, force: true });
    rmSync(files, { recursive: true, force: true });
  }
});
