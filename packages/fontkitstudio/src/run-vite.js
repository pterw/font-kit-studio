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
  const { vite } = await loadVite(projectDir);
  const studio = await startStudio({ studioPort, studioFile, err });

  let server;
  let appUrl;
  try {
    server = await vite.createServer({
      root: projectDir,
      plugins: [fontkitStudio({ studio, bridgeFile, log: (line) => err.write(`${line}\n`) })],
    });
    await server.listen();
    server.printUrls();
    appUrl = server.resolvedUrls?.local?.[0];
    if (!appUrl) throw new Error('Font Kit Studio could not tell which address Vite is serving on.');

  } catch (error) {
    try {
      await server?.close();
    } finally {
      await studio.close();
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

  out.write('Font Kit Studio · dev only\n');
  out.write(`Open: ${studioUrl}\n`);
  if (open) openUrl(studioUrl, { err });

  return { studioUrl, appUrl, close };
}
