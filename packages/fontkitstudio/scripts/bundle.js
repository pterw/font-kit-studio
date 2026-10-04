import { copyFileSync, mkdirSync, readFileSync, realpathSync } from 'node:fs';
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

// Compare real paths: run through a symlink, argv[1] keeps the link while import.meta.url does not.
// With no script path on disk (`node -`, `node -e`), this module is not the one being run.
function runDirectly() {
  try {
    return realpathSync(process.argv[1]) === realpathSync(fileURLToPath(import.meta.url));
  } catch {
    return false;
  }
}
const isMain = Boolean(process.argv[1]) && runDirectly();
if (isMain) {
  try {
    console.log(`fontkitstudio: bundled Studio and the bridge at ${bundle()}`);
  } catch (error) {
    console.error(`fontkitstudio: ${error.message}`);
    process.exitCode = 1;
  }
}
