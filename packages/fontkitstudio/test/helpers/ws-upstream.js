// A node:http server on loopback that answers the RFC 6455 handshake and then echoes raw bytes.
// No WebSocket library: the proxy only has to carry bytes, so bytes are what the tests send.
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';

const GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11';

export function acceptKey(key) {
  return createHash('sha1')
    .update(key + GUID)
    .digest('base64');
}

// upgrades records the headers of every upgrade request that arrived.
export async function startWsUpstream() {
  const upgrades = [];
  const sockets = new Set();
  const server = createServer((req, res) => {
    res.writeHead(404, { 'content-length': 0 });
    res.end();
  });
  server.on('upgrade', (req, socket, head) => {
    upgrades.push({ url: req.url, headers: req.headers });
    sockets.add(socket);
    socket.on('close', () => sockets.delete(socket));
    socket.on('error', () => {});
    socket.write(
      'HTTP/1.1 101 Switching Protocols\r\n' +
        'Upgrade: websocket\r\n' +
        'Connection: Upgrade\r\n' +
        `Sec-WebSocket-Accept: ${acceptKey(String(req.headers['sec-websocket-key']))}\r\n\r\n`,
    );
    if (head.length > 0) socket.write(head);
    socket.pipe(socket);
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const { port } = server.address();
  return {
    origin: `http://127.0.0.1:${port}`,
    port,
    upgrades,
    close() {
      return new Promise((resolve) => {
        server.close(() => resolve());
        for (const socket of sockets) socket.destroy();
        server.closeAllConnections();
      });
    },
  };
}
