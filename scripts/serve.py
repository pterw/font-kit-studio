"""Font Kit Studio local preview server (development only, Python stdlib).

Serves the repository on two loopback ports so the demo app runs cross-origin from Studio:

  studio port  Studio HTML + GET /__fontkit/status + PUT /__fontkit/overrides.css
  demo port    the same files (e.g. /demo/), no /__fontkit/* endpoints (--target-port)

Studio's "Sync to file" writes the overrides stylesheet (a path inside this repository,
fixed on the command line) which the demo app links after its own CSS. All responses
are sent with Cache-Control: no-store.

  python3 scripts/serve.py [--host 127.0.0.1] [--studio-port 8000] [--target-port 8001]
                           [--overrides demo/fontkit-overrides.css] [--no-sync] [--open] [--quiet]
"""

import argparse
import errno
import html
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import posixpath
import signal
import sys
import tempfile
import threading
from urllib.parse import unquote
import webbrowser

REPO = Path(__file__).resolve().parents[1]
STUDIO_HTML = "fontkit-studio.html"
MAX_BYTES = 1024 * 1024
ENDPOINTS = "/__fontkit/"
INDEX_NAMES = ("index.html", "index.htm")  # what SimpleHTTPRequestHandler serves for a directory


class Config:
    def __init__(self, host, studio_port, target_port, overrides, sync, quiet):
        self.host = host
        self.overrides = overrides
        self.overrides_rel = overrides.relative_to(REPO).as_posix()
        self.sync = sync
        self.quiet = quiet
        public = "localhost" if host in ("127.0.0.1", "0.0.0.0", "") else host
        self.studio_url = f"http://{public}:{studio_port}"
        self.target_url = f"http://{public}:{target_port}/demo/"
        self.studio_path = f"/{STUDIO_HTML}?target={self.target_url}"
        self.open_url = f"{self.studio_url}{self.studio_path}"  # printed as "Open:", launched by --open
        # Browsers leave the port out of `Origin` on the default port, so port 80 is allowed
        # both ways (hosts() does the same for the Host header).
        self.origins = {f"http://{name}:{studio_port}" for name in ("localhost", "127.0.0.1", public)}
        if studio_port == 80:
            self.origins |= {f"http://{name}" for name in ("localhost", "127.0.0.1", public)}
        self.write_lock = threading.Lock()

    def hosts(self, port):
        """Host header values accepted on `port` (DNS-rebinding guard), lower-case."""
        names = {"localhost", "127.0.0.1", "[::1]"}
        if self.host not in ("", "0.0.0.0"):
            names.add(self.host.lower())
        allowed = {f"{name}:{port}" for name in names}
        return allowed | names if port == 80 else allowed


class Handler(SimpleHTTPRequestHandler):
    config = None   # set per server class
    studio = False  # True on the studio port
    timeout = 30    # seconds; a stalled client cannot hold a worker thread forever

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format, *args):
        if not self.config.quiet:
            super().log_message(format, *args)

    def clean_path(self):
        """Normalised URL path ('/a/b'), or None when any segment is hidden (dot-prefixed).

        Splits the raw request path exactly as SimpleHTTPRequestHandler.translate_path does,
        so the check sees the same path that would be served.
        """
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        path = posixpath.normpath(unquote(path, errors="surrogatepass"))
        parts = [part for part in path.split("/") if part]
        if any(part.startswith(".") for part in parts):
            return None
        return "/" + "/".join(parts)

    def real_path_servable(self):
        """True when the file this request would serve is inside the repository and not hidden.

        clean_path() only judges the URL, but the inherited handler follows file system
        links, so a link inside the repository can reach an outside or hidden file. Judge the
        resolved path instead: the one the handler would open, including the index file it
        picks for a directory.
        """
        served = Path(self.translate_path(self.path))
        if not repo_servable(served):
            return False
        if served.is_dir():
            index = next((served / name for name in INDEX_NAMES if (served / name).is_file()), None)
            return index is None or repo_servable(index)  # no index: list_directory answers 404
        return True

    def send_bytes(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_json(self, status, data):
        self.send_bytes(status, json.dumps(data).encode(), "application/json")

    def redirect(self, location):
        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def fail(self, status, message):
        self.close_connection = True
        self.send_json(status, {"ok": False, "error": message})

    def host_allowed(self):
        host = (self.headers.get("Host") or "").strip().lower()
        accepted = self.config.hosts(self.server.server_address[1])
        if host in accepted:
            return True
        if "text/html" in (self.headers.get("Accept") or "").lower():
            self.close_connection = True
            self.send_bytes(HTTPStatus.MISDIRECTED_REQUEST, misdirected_page(accepted).encode(),
                            "text/html; charset=utf-8")
        else:
            self.fail(HTTPStatus.MISDIRECTED_REQUEST, "Host header not allowed")
        return False

    def do_GET(self):
        if not self.host_allowed():
            return
        path = self.clean_path()
        if path is None:
            return self.send_error(HTTPStatus.NOT_FOUND)
        if (path + "/").startswith(ENDPOINTS):
            if self.studio and path == ENDPOINTS + "status":
                return self.send_json(200, {"sync": self.config.sync,
                                            "overrides": self.config.overrides_rel,
                                            "target": self.config.target_url})
            return self.send_error(HTTPStatus.NOT_FOUND)
        if path == "/":
            return self.redirect(self.config.studio_path if self.studio else "/demo/")
        if not self.real_path_servable():
            return self.send_error(HTTPStatus.NOT_FOUND)
        if path == "/" + self.config.overrides_rel and not self.config.overrides.is_file():
            return self.send_bytes(200, b"", "text/css; charset=utf-8")
        return super().do_HEAD() if self.command == "HEAD" else super().do_GET()

    do_HEAD = do_GET

    def do_PUT(self):
        if not self.host_allowed():
            return
        path = self.clean_path()
        if not (self.studio and path == ENDPOINTS + "overrides.css"):
            hidden = path is None or (path + "/").startswith(ENDPOINTS)
            status = HTTPStatus.NOT_FOUND if hidden else HTTPStatus.METHOD_NOT_ALLOWED
            self.close_connection = True
            return self.send_error(status)
        if not self.config.sync:
            return self.fail(403, "sync is disabled (--no-sync)")
        origin = self.headers.get("Origin")
        if origin is not None and origin not in self.config.origins:
            return self.fail(403, "origin not allowed")
        if (self.headers.get("Content-Type") or "").split(";")[0].strip().lower() != "text/css":
            return self.fail(415, "Content-Type must be text/css")
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            return self.fail(411, "Content-Length required")
        if length < 0:
            return self.fail(400, "bad Content-Length")
        if length > MAX_BYTES:
            return self.fail(413, f"body exceeds {MAX_BYTES} bytes")
        body = self.rfile.read(length)
        if len(body) != length:
            return self.fail(400, "incomplete body")
        try:
            write_atomic(self.config, body)
        except OSError as error:
            return self.fail(500, f"write failed: {error.strerror or error}")
        self.send_json(200, {"ok": True, "bytes": length, "path": self.config.overrides_rel})

    def list_directory(self, path):
        self.send_error(HTTPStatus.NOT_FOUND)
        return None


def misdirected_page(accepted):
    """The 421 answer for a browser: plain HTML from config values only, never the request's Host."""
    names = ", ".join(f"<code>{html.escape(name)}</code>" for name in sorted(accepted))
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        "<title>Wrong address</title></head>"
        "<body><h1>Wrong address for this server</h1>"
        f"<p>This server only answers requests addressed to {names}. It refuses other host "
        "names to block DNS-rebinding attacks.</p>"
        "<p>To use another address, restart it with <code>--host &lt;address&gt;</code>, "
        "for example <code>--host 192.168.1.20</code>.</p></body></html>")


def repo_servable(path):
    """True when `path`, with every link followed, is inside the repository with no hidden part."""
    try:
        rel = path.resolve().relative_to(REPO)
    except (OSError, RuntimeError, ValueError):  # outside the repo, a link loop, a NUL byte
        return False
    return not any(part.startswith(".") for part in rel.parts)


def write_atomic(config, body):
    target = config.overrides
    with config.write_lock:
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(body)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp, 0o644)
            os.replace(temp, target)
        except BaseException:
            try:
                os.unlink(temp)
            except FileNotFoundError:
                pass
            raise


def resolve_overrides(value):
    """Return the absolute overrides path (relative paths are relative to the repo) or raise."""
    path = Path(value)
    path = (path if path.is_absolute() else REPO / path).resolve()
    if path == REPO or REPO not in path.parents:
        raise ValueError(f"--overrides must resolve inside the repository ({REPO}): {value}")
    rel = path.relative_to(REPO)
    if any(part.startswith(".") for part in rel.parts[:-1]) or rel.name.startswith("."):
        raise ValueError(f"--overrides must not be a hidden path: {value}")
    if path.suffix.lower() != ".css":
        raise ValueError(f"--overrides must be a .css file: {value}")
    if path.is_dir():
        raise ValueError(f"--overrides is a directory: {value}")
    return path


def make_server(config, host, port, studio):
    handler = type("StudioHandler" if studio else "TargetHandler", (Handler,),
                   {"config": config, "studio": studio})
    server_class = ThreadingHTTPServer
    if sys.platform == "win32":
        # On Windows SO_REUSEADDR lets a second server bind a port that is already taken. The
        # option only counts when set before bind, so it goes on the class, not the instance.
        server_class = type("ExclusiveHTTPServer", (ThreadingHTTPServer,), {"allow_reuse_address": False})
    server = server_class((host, port), partial(handler, directory=str(REPO)))
    server.daemon_threads = True
    return server


def main(argv=None):
    parser = argparse.ArgumentParser(description="Font Kit Studio local preview server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--studio-port", type=int, default=8000)
    parser.add_argument("--target-port", type=int, default=8001)
    parser.add_argument("--overrides", default="demo/fontkit-overrides.css",
                        help="stylesheet Studio may write (repo-relative; must stay inside the repo)")
    parser.add_argument("--no-sync", dest="sync", action="store_false",
                        help="refuse PUT /__fontkit/overrides.css")
    parser.add_argument("--open", action="store_true", help="open Studio in the default browser")
    parser.add_argument("--quiet", action="store_true", help="do not log requests")
    args = parser.parse_args(argv)

    try:
        overrides = resolve_overrides(args.overrides)
    except ValueError as error:
        parser.error(str(error))
    if args.studio_port == args.target_port:
        parser.error("--studio-port and --target-port must differ")

    config = Config(args.host, args.studio_port, args.target_port, overrides, args.sync, args.quiet)
    servers = []
    for flag, port, studio in (("--studio-port", args.studio_port, True),
                               ("--target-port", args.target_port, False)):
        try:
            servers.append(make_server(config, args.host, port, studio))
        except OSError as error:
            in_use = error.errno in {errno.EADDRINUSE, getattr(errno, "WSAEADDRINUSE", None)}
            if in_use:
                print(f"serve.py: {flag} {port} is in use; pick another with {flag} <port>", file=sys.stderr)
            else:  # e.g. a --host this machine does not own: the port flag is not the cause
                print(f"serve.py: cannot listen on {args.host}:{port} ({flag}): {error}", file=sys.stderr)
            for server in servers:
                server.server_close()
            return 1

    stop = threading.Event()
    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, lambda *_: stop.set())
    threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in servers]
    for thread in threads:
        thread.start()

    print(f"Studio:  {config.studio_url}{config.studio_path}")
    # The demo app's own address, on its own port. It is context, not the link to open: the Open: line below is.
    print(f"Demo:    {config.target_url}")
    print(f"Sync:    {'on' if config.sync else 'off'} -> {config.overrides_rel}")
    print("Press Ctrl-C to stop.")
    print(f"Open: {config.open_url}", flush=True)
    if args.open and not webbrowser.open(config.open_url):
        print("serve.py: no browser could be opened; use the Open: URL above.", file=sys.stderr)
    while not stop.wait(0.5):
        pass
    for server in servers:
        server.shutdown()
        server.server_close()
    print("Stopped.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
