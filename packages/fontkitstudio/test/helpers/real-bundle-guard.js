import { after } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const PKG_DIR = fileURLToPath(new URL('../..', import.meta.url));

function snapshot() {
  const state = {};
  const record = (path) => {
    try {
      const { mtimeMs } = statSync(path);
      state[path] = { mtimeMs, bytes: readFileSync(path).toString('base64') };
    } catch {
      state[path] = null;
    }
  };
  record(join(PKG_DIR, 'LICENSE'));
  let names = [];
  try { names = readdirSync(join(PKG_DIR, 'dist')); } catch { /* no dist/ */ }
  names.forEach((name) => record(join(PKG_DIR, 'dist', name)));
  state.dist = names.sort();
  return state;
}

// Call once at the top of a test file. The real dist/ and LICENSE are read by many files at
// once, so when this file's tests are done they must be exactly as they were when it started:
// same files, same bytes, same modification times. A test that deletes or rewrites them (even
// with the same bytes) fails here, by name, instead of making another file flaky.
export function guardRealBundle() {
  const before = snapshot();
  after(() => {
    assert.deepEqual(snapshot(), before, 'a test deleted or rewrote the real dist/ or LICENSE');
  });
}
