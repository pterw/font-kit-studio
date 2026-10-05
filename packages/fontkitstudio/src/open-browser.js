// Opens a URL in the user's default browser without a shell, so & and ? stay literal.
import { spawn } from 'node:child_process';

export function browserCommand(platform, url) {
  if (platform === 'win32') return { command: 'rundll32', args: ['url.dll,FileProtocolHandler', url] };
  if (platform === 'darwin') return { command: 'open', args: [url] };
  return { command: 'xdg-open', args: [url] };
}

export function openBrowser(
  url,
  { err = process.stderr, spawnFn = spawn, platform = process.platform } = {},
) {
  const { command, args } = browserCommand(platform, url);
  const child = spawnFn(command, args, { detached: true, stdio: 'ignore', shell: false });
  // One line at most, whether the command could not start (error) or started and failed (exit).
  let reported = false;
  const report = () => {
    if (reported) return;
    reported = true;
    err.write('Font Kit Studio could not open a browser; open the URL above.\n');
  };
  child.on('error', report);
  child.on('exit', (code, signal) => {
    if (code !== 0 || signal) report();
  });
  child.unref();
}
