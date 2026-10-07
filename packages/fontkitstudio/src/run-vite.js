// What `fontkitstudio` runs in a Vite project: the project's own Vite, with the plugin added
// in memory (nothing is written to the project), and Studio beside it.
import { openBrowser } from './open-browser.js';
import { loadVite } from './project.js';
import { startStudio } from './run-proxy.js';
import { fontkitStudio } from './vite-plugin.js';

export async function runVite({
  projectDir,
  open = true,
  out = process.stdout,
  err = process.stderr,
  studioPort = 0,
  openUrl = openBrowser,
  studioFile,
  bridgeFile,
} = {}) {
  // The project is the nearest folder with a package.json, which may sit above the one the
  // command runs in; Vite starts there.
  const { vite, projectDir: foundDir } = await loadVite(projectDir);
  let studio;

  let server;
  let appUrl;
  let published = false;
  const printStudio = () => {
    const url = studio.url(appUrl);
    out.write('Font Kit Studio · dev only\n');
    out.write(`Open: ${url}\n`);
    return url;
  };
  try {
    // Start Vite as `vite` itself does when run in the project folder: it finds the config there
    // and resolves the config's own `root` against the working directory. An inline `root` would
    // win the merge and override the config's.
    process.chdir(foundDir);
    server = await vite.createServer({
      plugins: [fontkitStudio({
        bridgeFile,
        startStudio: async (host, local) => {
          studio = await startStudio({ studioPort, studioFile, host, err });
          appUrl = local;
          if (published) printStudio();
          return studio;
        },
        log: (line) => err.write(`${line}\n`),
      })],
    });
    await server.listen();
    server.printUrls();
    appUrl = server.resolvedUrls?.local?.[0];
    if (!appUrl) throw new Error('Font Kit Studio could not tell which address Vite is serving on.');

  } catch (error) {
    try {
      await server?.close();
    } finally {
      await studio?.close();
    }
    throw error;
  }

  const studioUrl = studio.url(appUrl);

  const signals = process.platform === 'win32' ? ['SIGINT', 'SIGTERM', 'SIGBREAK'] : ['SIGINT', 'SIGTERM'];
  let closing;
  const close = () => {
    closing ??= (async () => {
      for (const signal of signals) process.off(signal, close);
      try {
        await server.close();
      } finally {
        await studio.close();
      }
    })();
    return closing;
  };
  for (const signal of signals) process.on(signal, close);

  printStudio();
  published = true;
  if (open) openUrl(studioUrl, { err });

  return { get studioUrl() { return studio.url(appUrl); }, get appUrl() { return appUrl; }, close };
}
