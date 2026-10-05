import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

// A project folder in a temp dir. vite: a version string for a fake node_modules/vite, or null.
export function fakeProject({ vite = '8.3.2', field = 'devDependencies', packageJson, config } = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'fks-project-'));
  const pkg = { name: 'app', private: true, [field]: vite ? { vite: `^${vite}` } : {} };
  writeFileSync(join(dir, 'package.json'), packageJson ?? JSON.stringify(pkg, null, 2));
  if (config) writeFileSync(join(dir, config), 'export default {};\n');
  if (vite) {
    const viteDir = join(dir, 'node_modules', 'vite');
    mkdirSync(join(viteDir, 'dist', 'node'), { recursive: true });
    writeFileSync(join(viteDir, 'package.json'), JSON.stringify({
      name: 'vite', version: vite, type: 'module',
      exports: { '.': './dist/node/index.js', './package.json': './package.json' },
    }));
    writeFileSync(join(viteDir, 'dist', 'node', 'index.js'),
      `export const version = ${JSON.stringify(vite)};\nexport function createServer() { return 'fake'; }\n`);
  }
  return dir;
}
