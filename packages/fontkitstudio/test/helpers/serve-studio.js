// Starts the Studio server for a browser test: argv = studioFile, target.
// Prints the Studio URL on one line and stops when stdin closes.
import { startStudioServer } from '../../src/studio-server.js';

const [studioFile, target] = process.argv.slice(2);
const server = await startStudioServer({ studioFile });
process.stdout.write(`${server.url(target)}\n`);
process.stdin.resume();
process.stdin.on('end', async () => { await server.close(); process.exit(0); });
