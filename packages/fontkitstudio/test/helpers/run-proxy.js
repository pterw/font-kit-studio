// Runs the proxy runner for a browser test: argv = target, studioFile, bridgeFile.
// stdout gets the runner's two lines; the runner stops when stdin ends.
import { runProxy } from '../../src/run-proxy.js';

const [target, studioFile, bridgeFile] = process.argv.slice(2);
const running = await runProxy({ target, open: false, studioFile, bridgeFile });
process.stdin.resume();
process.stdin.on('end', async () => {
  await running.close();
  process.exit(0);
});
