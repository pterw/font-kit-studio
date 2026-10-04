import { copyFileSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { BRIDGE_FILE, STUDIO_FILE, checkVersions } from './versions.js';

const PACKAGE_DIR = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const REPO_ROOT = resolve(PACKAGE_DIR, '..', '..');

// Copies Studio and the bridge into dist/ so a page never talks to a Studio from another
// release (spec 1.1). Runs as `prepack`, so npm pack and npm publish always bundle.
export function bundle({ root = REPO_ROOT, packageDir = PACKAGE_DIR } = {}) {
  const { version } = JSON.parse(readFileSync(join(packageDir, 'package.json'), 'utf8'));
  checkVersions(root, version);
  const dist = join(packageDir, 'dist');
  mkdirSync(dist, { recursive: true });
  for (const file of [STUDIO_FILE, BRIDGE_FILE]) copyFileSync(join(root, file), join(dist, file));
  copyFileSync(join(root, 'LICENSE'), join(packageDir, 'LICENSE'));
  return version;
}

if (resolve(process.argv[1] ?? '') === fileURLToPath(import.meta.url)) {
  try {
    console.log(`fontkitstudio: bundled Studio and the bridge at ${bundle()}`);
  } catch (error) {
    console.error(`fontkitstudio: ${error.message}`);
    process.exitCode = 1;
  }
}
