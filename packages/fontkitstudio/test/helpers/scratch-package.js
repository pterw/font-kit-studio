import { copyFileSync, cpSync, mkdirSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const PKG_DIR = fileURLToPath(new URL('../..', import.meta.url));
const REPO_ROOT = join(PKG_DIR, '..', '..');

// A scratch repository laid out like this one (Studio, the bridge and the licence at the
// root, the package under packages/fontkitstudio) holding a copy of the package without its
// dist/ and LICENSE. Tests that bundle or pack work here: the real dist/ and LICENSE are
// shared by every test file, which node --test runs in parallel, so no test may write or
// delete them. Returns { root, packageDir }; the caller removes root.
export function scratchPackage() {
  const root = mkdtempSync(join(tmpdir(), 'fks-scratch-'));
  for (const file of ['fontkit-studio.html', 'fontkit-bridge.js', 'LICENSE']) {
    copyFileSync(join(REPO_ROOT, file), join(root, file));
  }
  const packageDir = join(root, 'packages', 'fontkitstudio');
  mkdirSync(packageDir, { recursive: true });
  for (const entry of ['bin', 'src', 'scripts', 'package.json', 'README.md']) {
    cpSync(join(PKG_DIR, entry), join(packageDir, entry), { recursive: true });
  }
  return { root, packageDir };
}
