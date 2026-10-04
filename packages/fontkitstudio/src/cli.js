import { readFileSync } from 'node:fs';

import { isViteProject, ProjectError } from './project.js';
import { parseProxyTarget, ProxyTargetError } from './proxy.js';
import { runProxy } from './run-proxy.js';
import { runVite } from './run-vite.js';

const { version } = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));

export const USAGE = `Usage: fontkitstudio [<url>] [--no-open] [--studio-port <n>] [--help] [--version]

Font Kit Studio ${version}: try type on your running web app, in development only.

  fontkitstudio                          in a Vite project: run its dev server with Studio
  fontkitstudio http://localhost:3000    any other local dev server: Studio through a proxy
  --no-open                              print the URL instead of opening the browser
  --studio-port <n>                      keep Studio on one port, so its settings stay
`;

const PORT_ERROR = 'fontkitstudio: --studio-port needs a port number from 1 to 65535\n';

function parsePort(text) {
  if (typeof text !== 'string' || !/^\d+$/.test(text)) return null;
  const port = Number(text);
  return port >= 1 && port <= 65535 ? port : null;
}

// Returns { error } or the parsed options; --help and --version win wherever they stand.
function parseArgs(argv) {
  const parsed = { open: true, studioPort: 0, url: undefined };
  const positionals = [];
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--help' || arg === '-h') return { help: true };
    if (arg === '--version' || arg === '-v') return { showVersion: true };
    if (arg === '--no-open') {
      parsed.open = false;
    } else if (arg === '--studio-port' || arg.startsWith('--studio-port=')) {
      const value = arg === '--studio-port' ? argv[(i += 1)] : arg.slice('--studio-port='.length);
      const port = parsePort(value);
      if (port === null) return { error: PORT_ERROR };
      parsed.studioPort = port;
    } else if (arg.startsWith('-')) {
      return { error: `fontkitstudio: unknown argument ${JSON.stringify(arg)}\n\n${USAGE}` };
    } else {
      positionals.push(arg);
    }
  }
  if (positionals.length > 1) return { error: 'fontkitstudio: give one dev server address, not two\n' };
  [parsed.url] = positionals;
  return parsed;
}

// Returns the exit code: 0 once started (the servers then keep the process alive), 2 for usage
// errors, 1 for start-up failures. openUrl is a test seam; undefined means the real opener.
export async function main(argv, { out, err, cwd = process.cwd(), openUrl }) {
  const args = parseArgs(argv);
  if (args.showVersion) {
    out.write(`${version}\n`);
    return 0;
  }
  if (args.help) {
    out.write(USAGE);
    return 0;
  }
  if (args.error) {
    err.write(args.error);
    return 2;
  }

  const { open, studioPort, url } = args;
  try {
    if (url !== undefined) {
      try {
        const { protocol } = new URL(url);
        if (protocol !== 'http:' && protocol !== 'https:') throw new Error('scheme');

      } catch {
        err.write(
          `fontkitstudio: ${JSON.stringify(url)} is not a URL. Give your dev server's address, such as http://localhost:3000\n`,
        );
        return 2;
      }
      parseProxyTarget(url); // refuse before any server starts
      await runProxy({ target: url, open, out, err, studioPort, openUrl });
    } else {
      if (!isViteProject(cwd)) {
        err.write(
          `Font Kit Studio found no Vite project in ${cwd}. Run it in your Vite project, or give your dev server's address: npx fontkitstudio http://localhost:3000\n`,
        );
        return 2;
      }
      await runVite({ projectDir: cwd, open, out, err, studioPort, openUrl });
    }
    return 0;
  } catch (error) {
    if (!(error instanceof Error)) throw error;
    err.write(`${error.message}\n`);
    if (error instanceof ProjectError) return 1;
    return error instanceof ProxyTargetError ? 2 : 1;
  }
}
