// A real node:http server on loopback that stands in for the user's dev server in proxy tests.
import { createServer } from 'node:http';

// routes: pathname -> { status, headers, body } or (req) => { status, headers, body }.
// Unknown paths answer 404 "not found". requests records every request that arrived.
export async function startUpstream(routes) {
  const requests = [];
  const server = createServer((req, res) => {
    const chunks = [];
    req.on('data', (chunk) => chunks.push(chunk));
    req.on('end', () => {
      requests.push({
        method: req.method,
        url: req.url,
        headers: req.headers,
        body: Buffer.concat(chunks),
      });
      const pathname = req.url.split('?')[0];
      const route = routes[pathname];
      const answer = typeof route === 'function' ? route(req) : route;
      if (answer === undefined) {
        res.writeHead(404, { 'content-type': 'text/plain' });
        res.end('not found');
        return;
      }
      const body = answer.body ?? '';
      const headers = { ...answer.headers };
      const framed = 'transfer-encoding' in headers || 'content-length' in headers;
      if (!framed && answer.status !== 304) headers['content-length'] = Buffer.byteLength(body);
      res.writeHead(answer.status ?? 200, headers);
      res.end(body);
    });
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const { port } = server.address();
  return {
    origin: `http://127.0.0.1:${port}`,
    port,
    requests,
    close() {
      return new Promise((resolve) => {
        server.close(() => resolve());
        server.closeAllConnections();
      });
    },
  };
}
