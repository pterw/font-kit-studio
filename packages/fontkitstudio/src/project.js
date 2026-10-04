// Finds the user's project and loads the project's own Vite (never a copy of ours, D030).
// This is the only shipped file that loads code by a computed path; the guard in
// test/package.test.js keeps it that way.
import { existsSync, readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';

export const TESTED_VITE_MAJORS = [7, 8];

const VITE_CONFIGS = ['js', 'mjs', 'cjs', 'ts', 'mts', 'cts'].map((ext) => `vite.config.${ext}`);

export class ProjectError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ProjectError';
  }
}

export function findProjectDir(startDir) {
  for (let dir = startDir; ; dir = dirname(dir)) {
    if (existsSync(join(dir, 'package.json'))) return dir;
    if (dirname(dir) === dir) break;
  }
  throw new ProjectError(`No package.json in ${startDir} or a folder above it. Run Font Kit Studio from your project's folder.`);
}

// Never include the parser's message: it can quote file contents.
function readJson(path) {
  try {
    return JSON.parse(readFileSync(path, 'utf8'));
  } catch {
    throw new ProjectError(`${path} is not valid JSON, so Font Kit Studio cannot read the project.`);
  }
}

function hasViteConfig(dir) {
  return VITE_CONFIGS.some((name) => existsSync(join(dir, name)));
}

function listsVite(pkg) {
  return ['dependencies', 'devDependencies'].some((field) => {
    const deps = pkg?.[field];
    return deps !== null && typeof deps === 'object' && Object.hasOwn(deps, 'vite');
  });
}

export function isViteProject(startDir) {
  let projectDir;
  try {
    projectDir = findProjectDir(startDir);
  } catch {
    return hasViteConfig(startDir);
  }
  return listsVite(readJson(join(projectDir, 'package.json'))) || hasViteConfig(projectDir);
}

function resolveFrom(projectDir, specifier) {
  const require = createRequire(join(projectDir, 'package.json'));
  try {
    return require.resolve(specifier);
  } catch {
    throw new ProjectError(`Vite is not installed in ${projectDir}. Run npm install there, then try again.`);
  }
}

function untested(version) {
  return new ProjectError(`This project uses Vite ${version}. Font Kit Studio is tested with Vite ${TESTED_VITE_MAJORS.join(' and ')}; use one of those versions.`);
}

export function findVite(startDir) {
  const projectDir = findProjectDir(startDir);
  readJson(join(projectDir, 'package.json'));
  const pkgPath = resolveFrom(projectDir, 'vite/package.json');
  const version = readJson(pkgPath).version;
  if (typeof version !== 'string') {
    throw new ProjectError(`Font Kit Studio cannot read the version of Vite in ${projectDir}. Run npm install there, then try again.`);
  }
  const major = Number.parseInt(version, 10);
  if (!TESTED_VITE_MAJORS.includes(major)) throw untested(version);
  const entryUrl = pathToFileURL(resolveFrom(projectDir, 'vite')).href;
  return { projectDir, version, major, entryUrl };
}

export async function loadVite(startDir) {
  const { projectDir, version, major, entryUrl } = findVite(startDir);
  const vite = await import(entryUrl);
  return { vite, projectDir, version, major };
}
