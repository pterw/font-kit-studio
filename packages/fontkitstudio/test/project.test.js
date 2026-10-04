import { test } from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import {
  ProjectError, TESTED_VITE_MAJORS, findProjectDir, findVite, isViteProject, loadVite,
} from '../src/project.js';
import { fakeProject } from './helpers/fake-project.js';

const made = [];
function project(options) {
  const dir = fakeProject(options);
  made.push(dir);
  return dir;
}
function emptyDir() {
  const dir = mkdtempSync(join(tmpdir(), 'fks-empty-'));
  made.push(dir);
  return dir;
}
test.after(() => {
  for (const dir of made) rmSync(dir, { recursive: true, force: true });
});

const UNTESTED = (version) => `This project uses Vite ${version}. Font Kit Studio is tested with Vite 7 and 8; use one of those versions.`;

for (const version of ['7.3.6', '8.3.2']) {
  test(`findVite accepts Vite ${version}`, () => {
    const dir = project({ vite: version });
    const found = findVite(dir);
    assert.equal(found.version, version);
    assert.equal(found.major, Number.parseInt(version, 10));
    assert.equal(found.projectDir, dir);
    assert.ok(found.entryUrl.startsWith('file:'), found.entryUrl);
    assert.ok(found.entryUrl.endsWith('node_modules/vite/dist/node/index.js'), found.entryUrl);
  });
}

for (const version of ['6.4.0', '9.0.0']) {
  test(`findVite refuses Vite ${version}`, () => {
    const dir = project({ vite: version });
    assert.throws(() => findVite(dir), (error) => {
      assert.ok(error instanceof ProjectError);
      assert.equal(error.name, 'ProjectError');
      assert.equal(error.message, UNTESTED(version));
      return true;
    });
  });
}

test('findVite names the folder when Vite is not installed', () => {
  const dir = project({ vite: null });
  assert.throws(() => findVite(dir), (error) => {
    assert.ok(error instanceof ProjectError);
    assert.equal(error.message, `Vite is not installed in ${dir}. Run npm install there, then try again.`);
    return true;
  });
});

test('findVite says so when Vite has no readable version', () => {
  const dir = project({ vite: '8.3.2' });
  writeFileSync(join(dir, 'node_modules', 'vite', 'package.json'),
    JSON.stringify({ name: 'vite', exports: { '.': './dist/node/index.js', './package.json': './package.json' } }));
  assert.throws(() => findVite(dir), (error) => {
    assert.ok(error instanceof ProjectError);
    assert.equal(error.message, `Font Kit Studio cannot read the version of Vite in ${dir}. Run npm install there, then try again.`);
    return true;
  });
});

test('findVite finds the project from a subdirectory', () => {
  const dir = project();
  const deep = join(dir, 'src', 'deep');
  mkdirSync(deep, { recursive: true });
  assert.equal(findVite(deep).projectDir, dir);
  assert.equal(findProjectDir(deep), dir);
});

function packageJsonAbove(dir) {
  for (let up = dirname(dir); ; up = dirname(up)) {
    if (existsSync(join(up, 'package.json'))) return true;
    if (dirname(up) === up) return false;
  }
}

test('findProjectDir says so when there is no package.json', (t) => {
  const dir = emptyDir();
  if (packageJsonAbove(dir)) return t.skip(`package.json above ${tmpdir()}`);
  assert.throws(() => findProjectDir(dir), (error) => {
    assert.ok(error instanceof ProjectError);
    assert.equal(error.message, `No package.json in ${dir} or a folder above it. Run Font Kit Studio from your project's folder.`);
    return true;
  });
});

test('a package.json that is not JSON is a ProjectError without parser text', () => {
  const dir = project({ packageJson: '{ "name": "app", ' });
  const expected = `${join(dir, 'package.json')} is not valid JSON, so Font Kit Studio cannot read the project.`;
  for (const call of [() => findVite(dir), () => isViteProject(dir)]) {
    assert.throws(call, (error) => {
      assert.ok(error instanceof ProjectError);
      assert.equal(error.message, expected);
      assert.doesNotMatch(error.message, /SyntaxError|"name"/);
      return true;
    });
  }
});

test('isViteProject reads dependencies, devDependencies and a vite config', () => {
  assert.equal(isViteProject(project({ field: 'dependencies' })), true);
  assert.equal(isViteProject(project({ field: 'devDependencies' })), true);
  assert.equal(isViteProject(project({ vite: null, config: 'vite.config.ts' })), true);
  assert.equal(isViteProject(project({ vite: null })), false);
});

test('isViteProject is false with no package.json', (t) => {
  const bare = emptyDir();
  if (packageJsonAbove(bare)) return t.skip(`package.json above ${tmpdir()}`);
  assert.equal(isViteProject(bare), false);
});

test('loadVite imports the project\'s own Vite', async () => {
  const dir = project({ vite: '8.3.2' });
  const loaded = await loadVite(dir);
  assert.equal(loaded.vite.createServer(), 'fake');
  assert.equal(loaded.vite.version, '8.3.2');
  assert.equal(loaded.version, '8.3.2');
  assert.equal(loaded.major, 8);
  assert.equal(loaded.projectDir, dir);
});

test('the tested Vite majors are 7 and 8 (D043)', () => {
  assert.deepEqual(TESTED_VITE_MAJORS, [7, 8]);
});
