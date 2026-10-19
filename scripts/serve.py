"""Font Kit Studio local preview server (development only, Python stdlib).

Serves the repository on two loopback ports so the demo app runs cross-origin from Studio:

  studio port  Studio HTML + GET /__fontkit/status + PUT /__fontkit/overrides.css
  demo port    the same files (e.g. /demo/), no /__fontkit/* endpoints (--target-port)

Studio's "Sync to file" writes the overrides stylesheet (a path inside this repository,
fixed on the command line) which the demo app links after its own CSS. All responses
are sent with Cache-Control: no-store.

  python3 scripts/serve.py [--host 127.0.0.1] [--studio-port 8000] [--target-port 8001]
                           [--overrides demo/fontkit-overrides.css] [--no-sync] [--open] [--quiet]

With an app address, serve.py instead serves Studio and a reverse proxy in front of that app
(loopback only) that adds the bridge to its HTML pages:

  python3 serve.py http://127.0.0.1:5000 [--studio-port 8000] [--target-port 8001] [--open] [--quiet]
"""

import argparse
import errno
import html
from functools import partial
import http.client
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import posixpath
import re
import selectors
import signal
import socket
import sys
import tempfile
import threading
from urllib.parse import quote, unquote, urlsplit
import webbrowser

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
STUDIO_HTML = "fontkit-studio.html"
BRIDGE_JS = "fontkit-bridge.js"
BRIDGE_PATH = "/@fontkit/fontkit-bridge.js"
TARGET_ERROR = "Font Kit Studio proxies only a local dev server (localhost, 127.0.0.1 or [::1])"
PLAIN_ERROR = ("the demo app needs the repository. To edit your own app, pass its address: "
               "python serve.py http://127.0.0.1:5000")
ASSET_ERROR = f"cannot find {STUDIO_HTML} or {BRIDGE_JS} next to serve.py or in the repository"
LOOPBACK_URL_HOSTS = ("localhost", "127.0.0.1", "[::1]")
HOP_BY_HOP = ("connection", "keep-alive", "proxy-connection", "te", "trailer", "transfer-encoding", "upgrade")
MAX_HTML_BYTES = 8 * 1024 * 1024  # the Node proxy's limit: a larger page streams through untagged
MAX_BYTES = 1024 * 1024
CSP_MESSAGE = ("Font Kit Studio: this page's Content-Security-Policy blocks the bridge (it does not allow the "
               "page's own scripts). Add 'self' to script-src while you develop.")
BRIDGE_TWICE_MESSAGE = ("Font Kit Studio: this page also loads its own fontkit-bridge.js. If Studio does not "
                        "connect, remove that script while you use serve.py.")
SCRIPT_DIRECTIVES = ("script-src-elem", "script-src", "default-src")
HOST_SOURCE = re.compile(r"(?:([a-z][a-z0-9+.-]*)://)?(\[[^\]]+\]|[^:/\s]+)(?::([0-9]+|\*))?(/\S*)?",
                         re.IGNORECASE | re.ASCII)
SPACE = " \t\n\v\f\r"  # what strip() removes; str.strip() with no argument also takes 0x1C-0x1F and 0x85
ENDPOINTS = "/__fontkit/"
INDEX_NAMES = ("index.html", "index.htm")  # what SimpleHTTPRequestHandler serves for a directory


class Config:
    def __init__(self, host, studio_port, target_port, overrides, sync, quiet):
        self.host = host
        self.overrides = overrides
        self.overrides_rel = overrides.relative_to(REPO).as_posix()
        self.sync = sync
        self.quiet = quiet
        self.proxy = False
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

    @classmethod
    def for_proxy(cls, name, studio_port, proxy_port, target, quiet):
        """Proxy mode: `target` is parse_target()'s result, `name` the host name both servers use."""
        self = cls.__new__(cls)
        self.host, self.overrides, self.overrides_rel = "127.0.0.1", None, ""
        self.sync, self.quiet, self.proxy, self.proxy_port = False, quiet, True, proxy_port
        self.studio_url = f"http://{name}:{studio_port}"
        # A browser leaves the port out of `Origin` on port 80, and the tag must name what it sends.
        self.studio_origin = f"http://{name}" if studio_port == 80 else self.studio_url
        self.proxy_origin = f"http://{name}:{proxy_port}"
        self.target_url = (self.proxy_origin + target.path + (f"?{target.query}" if target.query else "")
                           + (f"#{target.fragment}" if target.fragment else ""))
        self.studio_path = f"/{STUDIO_HTML}?target={quote(self.target_url, safe=':/')}"
        self.open_url = f"{self.studio_url}{self.studio_path}"
        self.origins = {f"http://{n}:{studio_port}" for n in ("localhost", "127.0.0.1")}
        if studio_port == 80:
            self.origins |= {"http://localhost", "http://127.0.0.1"}
        self.write_lock = threading.Lock()
        return self

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
        if self.config.proxy:  # Studio's server serves Studio and its status check, nothing else
            if path != "/" + STUDIO_HTML:
                return self.send_error(HTTPStatus.NOT_FOUND)
            return self.send_bytes(200, find_asset(STUDIO_HTML).read_bytes(), "text/html; charset=utf-8")
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


def server_class():
    if sys.platform == "win32":
        # On Windows SO_REUSEADDR lets a second server bind a port that is already taken. The
        # option only counts when set before bind, so it goes on the class, not the instance.
        return type("ExclusiveHTTPServer", (ThreadingHTTPServer,), {"allow_reuse_address": False})
    return ThreadingHTTPServer


def make_server(config, host, port, studio):
    handler = type("StudioHandler" if studio else "TargetHandler", (Handler,),
                   {"config": config, "studio": studio})
    server = server_class()((host, port), partial(handler, directory=str(REPO)))
    server.daemon_threads = True
    return server


def bracketed(parts):
    """The host as WHATWG spells it: urlsplit drops the brackets of an IPv6 address."""
    host = parts.hostname or ""
    return f"[{host}]" if ":" in host else host


def parse_target(url):
    """The one check of the address to proxy: a local http dev server. Raises ValueError(TARGET_ERROR)."""
    try:
        parts = urlsplit(url)
        host, _ = bracketed(parts), parts.port  # .port raises ValueError for a bad port
    except ValueError:
        raise ValueError(TARGET_ERROR) from None
    if parts.scheme != "http" or host not in LOOPBACK_URL_HOSTS:
        raise ValueError(TARGET_ERROR)
    return parts._replace(path=parts.path or "/")


def insert_tag(page, tag):
    """After <head ...>, else <html ...>, else a leading (BOM +) doctype, else at 0. Byte-preserving."""
    # Known divergence: a bytes \s is ASCII whitespace only; JavaScript's also matches the byte 0xA0.
    for pattern in (rb"<head(\s[^>]*)?>", rb"<html(\s[^>]*)?>", rb"^(\xef\xbb\xbf)?\s*<!doctype[^>]*>"):
        found = re.search(pattern, page, re.IGNORECASE)
        if found:
            return page[:found.end()] + tag + page[found.end():]
    return tag + page


# The functions down to tunnel() port packages/fontkitstudio/src/csp.js and run on a page decoded as latin-1,
# as Node does. re.ASCII keeps \s, \b and the case folding to what JavaScript does on those characters.
# Known divergence: JavaScript's \s and trim() also match the byte 0xA0; here only ASCII whitespace does.
def parse_origin(page_origin):
    """The page's own origin when it is a plain http one, as (host, port); anything else gives None."""
    if not isinstance(page_origin, str):
        return None
    try:
        parts = urlsplit(page_origin)
        port = parts.port
    except ValueError:
        return None
    if parts.scheme != "http" or not parts.hostname:
        return None
    return bracketed(parts), str(port or 80)


def source_allows_bridge(value, origin):
    """Whether one host-source names the page's origin and the bridge's path.

    Scheme and host compare without case; the path keeps its case, as browsers compare it
    case-sensitively. Anything that does not parse, or is not clearly the page's origin, does not match.
    """
    found = HOST_SOURCE.fullmatch(value)  # fullmatch: `$` would also match before a trailing newline
    if not found:
        return False
    scheme, host, port, path = found.groups()
    port = port or "80"
    if scheme is not None and scheme.lower() != "http":
        return False
    if host.lower() != origin[0] or port not in ("*", origin[1]):
        return False
    if not path:
        return True
    return BRIDGE_PATH.startswith(path) if path.endswith("/") else path == BRIDGE_PATH


def policy_blocks(policy, origin):
    """One policy: the first of script-src-elem, script-src, default-src that it sets decides."""
    directives = {}
    for part in policy.split(";"):
        name, *values = re.split(r"\s+", part.strip(SPACE), flags=re.ASCII)
        if name and name.lower() not in directives:
            directives[name.lower()] = values
    key = next((name for name in SCRIPT_DIRECTIVES if name in directives), None)
    if key is None:
        return False
    values = directives[key]
    if any(value.lower() == "'strict-dynamic'" for value in values):
        return True
    return not any(value.lower() in ("'self'", "*", "http:")
                   or (origin is not None and source_allows_bridge(value, origin)) for value in values)


def blocks_same_origin_script(policy, page_origin=None):
    """policy: a header value (policies may be comma-separated) or a list of them.

    Several policies all apply, so one that blocks is enough. page_origin (optional, such as
    'http://localhost:5173'): a source that names it also allows the bridge. Non-text policies never block.
    """
    origin = parse_origin(page_origin)
    return any(policy_blocks(one, origin)
               for each in (policy if isinstance(policy, list) else [policy])
               if isinstance(each, str) for one in each.split(","))


def attribute(tag, name):
    pattern = rf"\s{name}\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s\"'>]+))"
    found = re.search(pattern, tag, re.IGNORECASE | re.ASCII)
    return next((group for group in found.groups() if group is not None), None) if found else None


def meta_policies(html):
    """The content of every <meta http-equiv="Content-Security-Policy"> in a page."""
    if not isinstance(html, str):
        return []
    policies = []
    for tag in re.findall(r"<meta\b[^>]*>", html, re.IGNORECASE | re.ASCII):
        equiv, content = attribute(tag, "http-equiv"), attribute(tag, "content")
        if equiv is not None and equiv.strip(SPACE).lower() == "content-security-policy" and content is not None:
            policies.append(content)
    return policies


def loads_own_bridge(html):
    """Whether the page already has a <script src> that names fontkit-bridge."""
    if not isinstance(html, str):
        return False
    return any("fontkit-bridge" in (attribute(tag, "src") or "").lower()
               for tag in re.findall(r"<script\b[^>]*>", html, re.IGNORECASE | re.ASCII))


def tunnel(client, upstream, first=b""):
    """Raw bytes both ways until either side reaches EOF or errors; then both sockets close."""
    try:
        upstream.sendall(first)
        with selectors.DefaultSelector() as selector:
            selector.register(client, selectors.EVENT_READ, upstream)
            selector.register(upstream, selectors.EVENT_READ, client)
            while True:
                for key, _ in selector.select():
                    data = key.fileobj.recv(65536)
                    if not data:
                        return
                    key.data.sendall(data)
    except OSError:
        pass
    finally:  # either side ending ends both; the shutdown gives the client its EOF now
        try:
            client.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        client.close()
        upstream.close()


def rewrite_location(value, target_port, proxy_origin):
    """Absolute or //-relative http: Location under a loopback name and the target port -> proxy origin + rest."""
    try:
        parts = urlsplit("http://" + value[2:] if re.match(r"[\\/]{2}", value) else value)
        port = parts.port
    except ValueError:  # what a browser cannot parse stays as the app sent it
        return value
    if parts.scheme != "http" or bracketed(parts) not in LOOPBACK_URL_HOSTS or (port or 80) != target_port:
        return value
    return (proxy_origin + (parts.path or "/") + (f"?{parts.query}" if parts.query else "")
            + (f"#{parts.fragment}" if parts.fragment else ""))


def find_asset(name):
    """Next to serve.py first, then the repository root."""
    for folder in (HERE, REPO):
        if (folder / name).is_file():
            return folder / name
    raise FileNotFoundError(name)


class ProxyHandler(BaseHTTPRequestHandler):
    """Forwards every request to the app, tags its HTML pages and serves the bridge itself."""
    config = target = target_origin = target_host = tag = bridge = hosts = own_origins = None
    said = said_lock = None  # the warnings already printed in this run, set by run_proxy

    def log_message(self, format, *args):
        if not self.config.quiet:
            super().log_message(format, *args)

    def reply(self, status, body, headers):
        self.started = True
        self.send_response_only(status)
        for pair in (*headers, ("Content-Length", str(len(body))), ("Connection", "close")):
            self.send_header(*pair)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def send_text(self, status, text):
        self.reply(status, text.encode(), [("Content-Type", "text/plain; charset=utf-8")])

    def under_proxy(self, value):
        """The rest of a URL under one of the proxy's own loopback origins, else None."""
        for own in self.own_origins:
            rest = value[len(own):]
            if value.lower().startswith(own) and (rest == "" or rest[0] in "/?#"):
                return rest
        return None

    def forward_headers(self, close=True):
        """The request's (name, value) pairs for the app: duplicates kept, Host and Accept-Encoding replaced."""
        out = []
        for name, value in self.headers.items():
            lower = name.lower()
            rest = self.under_proxy(value) if lower in ("origin", "referer") else None
            if lower in HOP_BY_HOP or lower in ("host", "accept-encoding"):
                continue
            if rest == "" and lower == "origin":
                value = self.target_origin
            elif rest is not None and lower == "referer":
                value = self.target_origin + rest
            out.append((name, value))
        out += [("Host", self.target_host), ("Accept-Encoding", "identity")]
        return out + [("Connection", "close")] if close else out

    def response_headers(self, resp):
        return [(name, rewrite_location(value, self.target.port or 80, self.config.proxy_origin)
                 if name.lower() == "location" else value)
                for name, value in resp.getheaders() if name.lower() not in HOP_BY_HOP]

    def send_head(self, resp, headers):
        self.started = True
        self.send_response_only(resp.status, resp.reason)
        for pair in (*headers, ("Connection", "close")):
            self.send_header(*pair)
        self.end_headers()

    def send_tagged(self, resp, page):
        body = insert_tag(page, self.tag)
        skip = ("content-length", "etag", "last-modified", "cache-control")
        headers = [pair for pair in self.response_headers(resp) if pair[0].lower() not in skip]
        self.send_head(resp, headers + [("Content-Length", str(len(body))), ("Cache-Control", "no-store")])
        self.wfile.write(body)

    def stream(self, resp, first=b""):
        if first:
            self.wfile.write(first)
        while chunk := resp.read1(65536):  # read1, not read(n): a live stream must not wait for 64 KiB
            self.wfile.write(chunk)

    def taggable(self, resp):
        kind = (resp.getheader("Content-Type") or "").split(";")[0].strip().lower()
        return (self.command != "HEAD" and resp.status == 200 and kind == "text/html"
                and resp.getheader("Content-Encoding", "identity").lower() == "identity")

    def host_ok(self):
        return (self.headers.get("Host") or "").strip().lower() in self.hosts

    def say(self, message):
        """One line on stderr, once per run, flushed before the page that caused it is sent."""
        with self.said_lock:
            if message in self.said:
                return
            self.said.add(message)
            try:  # a closed or broken stderr must not fail the page; the line is lost, the page is served
                print(message, file=sys.stderr, flush=True)
            except (OSError, ValueError):
                pass

    def check_page(self, resp, page):
        html = page.decode("latin-1")
        if loads_own_bridge(html):
            self.say(BRIDGE_TWICE_MESSAGE)
        policies = [resp.getheader("Content-Security-Policy"), *meta_policies(html)]
        if blocks_same_origin_script(policies, self.config.proxy_origin):
            self.say(CSP_MESSAGE)

    def is_upgrade(self):
        tokens = ",".join(self.headers.get_all("Connection", [])).lower().split(",")
        return "Upgrade" in self.headers and "upgrade" in (token.strip() for token in tokens)

    def refuse(self, line):
        self.wfile.write(f"HTTP/1.1 {line}\r\nConnection: close\r\nContent-Length: 0\r\n\r\n".encode())

    def buffered(self):
        """The bytes the client sent past the request head that rfile already holds, taken without blocking."""
        self.connection.setblocking(False)
        try:
            pending = self.rfile.peek(1)  # a blocking peek on an empty buffer would wait for the client
        finally:
            self.connection.setblocking(True)
        return self.rfile.read(len(pending))

    def upgrade(self):
        """A WebSocket (the app's own hot reload): the same checks and rewrites, then raw bytes both ways."""
        self.close_connection = True
        if not self.host_ok():
            return self.refuse("421 Misdirected Request")
        if not self.path.startswith("/"):
            return self.refuse("400 Bad Request")
        try:
            upstream = socket.create_connection((self.target.hostname, self.target.port or 80))
        except OSError:  # the app is down: the client just loses the connection
            return
        headers = self.forward_headers(close=False)
        headers += [(name, ", ".join(self.headers.get_all(name))) for name in ("Connection", "Upgrade")]
        head = f"{self.command} {self.path} HTTP/1.1\r\n" + "".join(f"{n}: {v}\r\n" for n, v in headers) + "\r\n"
        tunnel(self.connection, upstream, head.encode("latin-1") + self.buffered())

    def forward(self):
        self.started = False
        if self.is_upgrade():
            return self.upgrade()
        if not self.host_ok():
            return self.send_text(421, "Host header not allowed.")
        if not self.path.startswith("/"):
            return self.send_text(400, "Bad request.")
        if self.path.split("?", 1)[0] == BRIDGE_PATH and self.command in ("GET", "HEAD"):
            return self.reply(200, self.bridge, [("Content-Type", "text/javascript; charset=utf-8"),
                                                 ("Cache-Control", "no-store"),
                                                 ("X-Content-Type-Options", "nosniff")])
        if "Transfer-Encoding" in self.headers and "Content-Length" not in self.headers:
            return self.send_error(HTTPStatus.LENGTH_REQUIRED)
        try:
            length = int(self.headers.get("Content-Length") or 0)
            if length < 0:
                raise ValueError(length)
        except ValueError:
            return self.send_text(400, "Bad request.")
        conn = http.client.HTTPConnection(self.target.hostname, self.target.port or 80, timeout=None)
        try:
            try:
                conn.putrequest(self.command, self.path, skip_host=True, skip_accept_encoding=True)
                for name, value in self.forward_headers():
                    conn.putheader(name, value)
            except ValueError:  # e.g. a non-ASCII byte in the request target
                return self.send_text(400, "Bad request.")
            conn.endheaders()
            while length:
                chunk = self.rfile.read(min(65536, length))
                if not chunk:  # the client left mid-upload: abandon the app's request too
                    self.close_connection = True
                    return
                conn.send(chunk)
                length -= len(chunk)
            resp = conn.getresponse()
            page = resp.read(MAX_HTML_BYTES + 1) if self.taggable(resp) else None
            if page is not None and len(page) <= MAX_HTML_BYTES:
                self.check_page(resp, page)
                return self.send_tagged(resp, page)
            self.send_head(resp, self.response_headers(resp))
            self.stream(resp, page or b"")
        except (OSError, http.client.HTTPException):
            self.close_connection = True  # with the headers out already, nothing more can be said
            if not self.started:
                self.send_text(502, f"Font Kit Studio cannot reach the dev server at {self.target_origin}. "
                                    "Is it running?")
        finally:
            conn.close()

    do_GET = do_HEAD = do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = forward


def run_proxy(config, target, studio_origin):
    """The proxy server on config's proxy port, bound but not serving; requests forwarded with http.client."""
    own = config.hosts(config.proxy_port)
    port = target.port or 80
    suffix = f":{port}" if port != 80 else ""
    handler = type("ProxyHandler", (ProxyHandler,), {
        "config": config, "target": target, "hosts": own, "said": set(), "said_lock": threading.Lock(),
        "own_origins": tuple(f"http://{host}" for host in own),
        "target_origin": f"http://{bracketed(target)}{suffix}", "target_host": bracketed(target) + suffix,
        "tag": f'<script src="{BRIDGE_PATH}" data-allowed-origins="{studio_origin}"></script>'.encode(),
        "bridge": find_asset(BRIDGE_JS).read_bytes()})
    server = server_class()((config.host, config.proxy_port), handler)
    server.daemon_threads = True
    return server


def main(argv=None):
    parser = argparse.ArgumentParser(description="Font Kit Studio local preview server")
    parser.add_argument("target", nargs="?", help="address of your app (http://127.0.0.1:5000): "
                        "proxy it and add the bridge to its pages instead of serving the demo")
    parser.add_argument("--host", default="127.0.0.1", help="address to bind (ignored with an app address)")
    parser.add_argument("--studio-port", type=int, default=8000)
    parser.add_argument("--target-port", type=int, default=8001)
    parser.add_argument("--overrides", default="demo/fontkit-overrides.css",
                        help="stylesheet Studio may write (repo-relative; must stay inside the repo)")
    parser.add_argument("--no-sync", dest="sync", action="store_false",
                        help="refuse PUT /__fontkit/overrides.css")
    parser.add_argument("--open", action="store_true", help="open Studio in the default browser")
    parser.add_argument("--quiet", action="store_true", help="do not log requests")
    args = parser.parse_args(argv)

    target = None
    if args.target:
        try:
            target = parse_target(args.target)
            for name in (STUDIO_HTML, BRIDGE_JS):
                find_asset(name)
        except (ValueError, FileNotFoundError) as error:
            print(f"serve.py: {error if isinstance(error, ValueError) else ASSET_ERROR}", file=sys.stderr)
            return 1
    elif HERE.name != "scripts" or not (REPO / "demo" / "index.html").is_file():
        print(f"serve.py: {PLAIN_ERROR}", file=sys.stderr)
        return 1
    else:
        try:
            overrides = resolve_overrides(args.overrides)
        except ValueError as error:
            parser.error(str(error))
    if args.studio_port == args.target_port:
        parser.error("--studio-port and --target-port must differ")

    if target:
        name = "localhost" if target.hostname == "localhost" else "127.0.0.1"
        config = Config.for_proxy(name, args.studio_port, args.target_port, target, args.quiet)
        target_server = partial(run_proxy, config, target, config.studio_origin)
    else:
        config = Config(args.host, args.studio_port, args.target_port, overrides, args.sync, args.quiet)
        target_server = partial(make_server, config, config.host, args.target_port, False)
    servers = []
    for flag, port, make in (("--studio-port", args.studio_port,
                              partial(make_server, config, config.host, args.studio_port, True)),
                             ("--target-port", args.target_port, target_server)):
        try:
            servers.append(make())
        except OSError as error:
            in_use = error.errno in {errno.EADDRINUSE, getattr(errno, "WSAEADDRINUSE", None)}
            if in_use:
                print(f"serve.py: {flag} {port} is in use; pick another with {flag} <port>", file=sys.stderr)
            else:  # e.g. a --host this machine does not own: the port flag is not the cause
                print(f"serve.py: cannot listen on {config.host}:{port} ({flag}): {error}", file=sys.stderr)
            for server in servers:
                server.server_close()
            return 1

    stop = threading.Event()
    # SIGBREAK is the graceful stop Windows can deliver to a child process (Ctrl-Break).
    for signum in (signal.SIGINT, signal.SIGTERM, getattr(signal, 'SIGBREAK', signal.SIGTERM)):
        signal.signal(signum, lambda *_: stop.set())
    threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in servers]
    for thread in threads:
        thread.start()

    print(f"Studio:  {config.studio_url}{config.studio_path}")
    if target:
        print(f"App:     {args.target}")  # the address as typed; the Open: line carries the proxy's
    else:
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
