"""A static file server that sends a strict Content-Security-Policy on every response (tests only)."""

import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

CSP = "script-src 'self'; style-src 'self'"


class CspHandler(SimpleHTTPRequestHandler):
    policy = CSP

    def end_headers(self):
        self.send_header('Content-Security-Policy', self.policy)
        super().end_headers()

    def log_message(self, *args):
        pass


class CspServer(ThreadingHTTPServer):
    daemon_threads = True


def start_csp_server(directory, csp=CSP):
    """Serve `directory` on 127.0.0.1:0 with the policy `csp`; return (server, origin). The
    caller stops it with server.shutdown() and server.server_close()."""
    handler = type('PolicyHandler', (CspHandler,), {'policy': csp})
    server = CspServer(('127.0.0.1', 0), partial(handler, directory=str(directory)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f'http://127.0.0.1:{server.server_address[1]}'
