import { readFileSync } from 'node:fs';

const { version } = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));

export const USAGE = `Usage: fontkitstudio [--help] [--version]

Font Kit Studio ${version}: try type on your running web app, in development only.
`;

// Returns the exit code; R1.4 adds the runners behind the no-argument form.
export async function main(argv, { out, err }) {
  const [arg] = argv;
  if (argv.length === 1 && (arg === '--version' || arg === '-v')) {
    out.write(`${version}\n`);
    return 0;
  }
  if (argv.length === 0 || (argv.length === 1 && (arg === '--help' || arg === '-h'))) {
    out.write(USAGE);
    return 0;
  }
  err.write(`fontkitstudio: unknown argument ${JSON.stringify(arg)}\n\n${USAGE}`);
  return 2;
}
