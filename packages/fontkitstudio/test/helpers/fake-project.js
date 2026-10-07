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

// The startup seam: resolve URLs during listen and invoke the configured plugin hooks,
// as Vite does. It serves no app; real-browser tests own that separate boundary.
export function stubViteServer(dir, { local = 'http://localhost:5173/' } = {}) {
  writeFileSync(join(dir, 'node_modules', 'vite', 'dist', 'node', 'index.js'), `
export async function createServer({ plugins = [] } = {}) {
  const config = { plugins, server: { host: 'localhost' }, logger: { info() {}, warn() {} } };
  const server = {
    config, resolvedUrls: null, middlewares: { use() {} },
    async listen() { server.resolvedUrls = { local: [${JSON.stringify(local)}] }; return server; },
    printUrls() {}, async close() { globalThis.__viteClosed = true; },
    async restart() {
      await server.close();
      Object.assign(server, await createServer({ plugins }));
      await server.listen();
    },
  };
  for (const plugin of plugins) plugin.configResolved?.(config);
  for (const plugin of plugins) await plugin.configureServer?.(server);
  globalThis.__viteServer = server;
  return server;
}
`);
}
