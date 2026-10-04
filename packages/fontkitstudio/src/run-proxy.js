// What `fontkitstudio <url>` runs: Studio, then the proxy in front of the user's dev server.
import { openBrowser } from './open-browser.js';
import { startProxy } from './proxy.js';
import { startStudioServer } from './studio-server.js';

export async function runProxy({
  target,
  open = true,
  out = process.stdout,
  err = process.stderr,
  studioPort = 0,
  openUrl = openBrowser,
  studioFile,
  bridgeFile,
} = {}) {
  // An undefined file falls back to the package's dist/ copy inside each starter.
  const startStudio = (port) => startStudioServer({ port, studioFile });

  let studio;
  try {
    studio = await startStudio(studioPort);
  } catch (error) {
    if (studioPort === 0 || error.code !== 'EADDRINUSE') throw error;
    studio = await startStudio(0);
    err.write(
      `Font Kit Studio: port ${studioPort} is busy, so Studio uses port ${studio.port}; its saved settings stay with the old port.\n`,
    );
  }

  let proxy;
  try {
    proxy = await startProxy({ target, studio, bridgeFile });
  } catch (error) {
    await studio.close();
    throw error;
  }

  const targetUrl = new URL(String(target));
  const studioUrl = studio.url(proxy.origin + targetUrl.pathname + targetUrl.search);

  const signals = process.platform === 'win32' ? ['SIGINT', 'SIGTERM', 'SIGBREAK'] : ['SIGINT', 'SIGTERM'];
  let closing;
  const close = () => {
    closing ??= (async () => {
      for (const signal of signals) process.off(signal, close);
      try {
        await proxy.close();
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

  return { studioUrl, proxyOrigin: proxy.origin, close };
}
