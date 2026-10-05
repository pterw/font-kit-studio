import { test } from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';

import { browserCommand, openBrowser } from '../src/open-browser.js';

const SPECIAL = 'http://127.0.0.1:5000/fontkit-studio.html?token=a&target=http%3A%2F%2Fx%2F%3Fq%3D1';

test('browserCommand keeps the URL as one unchanged argument on every platform', () => {
  assert.deepEqual(browserCommand('win32', SPECIAL), {
    command: 'rundll32',
    args: ['url.dll,FileProtocolHandler', SPECIAL],
  });
  assert.deepEqual(browserCommand('darwin', SPECIAL), { command: 'open', args: [SPECIAL] });
  assert.deepEqual(browserCommand('linux', SPECIAL), { command: 'xdg-open', args: [SPECIAL] });
  assert.equal(browserCommand('freebsd', 'http://a/').command, 'xdg-open');
});

function fakeSpawn() {
  const calls = [];
  const child = new EventEmitter();
  child.unrefs = 0;
  child.unref = () => {
    child.unrefs += 1;
  };
  const spawnFn = (command, args, options) => {
    calls.push({ command, args, options });
    return child;
  };
  return { calls, child, spawnFn };
}

test('openBrowser spawns detached without a shell and lets go of the child', () => {
  const { calls, child, spawnFn } = fakeSpawn();
  openBrowser(SPECIAL, { err: { write() {} }, spawnFn, platform: 'linux' });
  assert.equal(calls.length, 1);
  assert.equal(calls[0].command, 'xdg-open');
  assert.deepEqual(calls[0].args, [SPECIAL]);
  assert.equal(calls[0].options.detached, true);
  assert.equal(calls[0].options.stdio, 'ignore');
  assert.equal(calls[0].options.shell, false);
  assert.equal(child.unrefs, 1);
});

test('openBrowser writes one line to err when no browser can be started', () => {
  const { child, spawnFn } = fakeSpawn();
  const written = [];
  openBrowser('http://127.0.0.1:5000/', {
    err: { write: (text) => written.push(text) },
    spawnFn,
    platform: 'linux',
  });
  assert.deepEqual(written, []);
  child.emit('error', new Error('spawn xdg-open ENOENT'));
  assert.deepEqual(written, ['Font Kit Studio could not open a browser; open the URL above.\n']);
});

const LINE = 'Font Kit Studio could not open a browser; open the URL above.\n';

function opened() {
  const { child, spawnFn } = fakeSpawn();
  const written = [];
  openBrowser('http://127.0.0.1:5000/', {
    err: { write: (text) => written.push(text) },
    spawnFn,
    platform: 'linux',
  });
  return { child, written };
}

test('openBrowser reports a command that starts and exits nonzero', () => {
  const { child, written } = opened();
  child.emit('exit', 1, null);
  assert.deepEqual(written, [LINE]);
});

test('openBrowser stays silent when the command exits 0', () => {
  const { child, written } = opened();
  child.emit('exit', 0, null);
  assert.deepEqual(written, []);
});

test('openBrowser reports once when error is followed by exit', () => {
  const { child, written } = opened();
  child.emit('error', new Error('spawn xdg-open ENOENT'));
  child.emit('exit', 1, null);
  assert.deepEqual(written, [LINE]);
});

test('openBrowser reports a command ended by a signal', () => {
  const { child, written } = opened();
  child.emit('exit', null, 'SIGTERM');
  assert.deepEqual(written, [LINE]);
});
