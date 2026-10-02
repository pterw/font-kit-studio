"""Gate runtime: Playwright loading, browser launch, the served app, request routing.

Serving and browser lifecycle live here and nowhere else, so every other
module can assume a page that is already pointed at a running app and
already isolated from the network.

The server is the real `scripts/serve.py`, run as a subprocess on two
OS-assigned loopback ports (Studio on one, the demo target on the other, so
they stay cross-origin exactly as a user runs them). A subprocess is stopped
by signal and cannot outlive the gate's `finally`, and it is the same
mechanism `tests/test_live_integration.py` already trusts. `--no-sync` makes
the server refuse writes, so a gate run can never touch the working tree.

The gate never downloads tooling. A missing Playwright or browser becomes a
`GateError` carrying the exact install command.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from urllib.parse import urlsplit

from scripts.dev._frontend_gate_shared import (
    DEFAULT_ENGINES,
    KNOWN_ENGINES,
    REPO_ROOT,
    VIEWPORTS,
    NetworkLog,
)

#: Printed when Playwright or a browser build is missing. The first form is for
#: a developer machine; a container with a browser preinstalled should set the
#: FKS_*_EXECUTABLE variables instead (see AGENTS.md), and the error says so.
SETUP_COMMAND = "python -m playwright install chromium firefox"

SERVE_SCRIPT = REPO_ROOT / "scripts" / "serve.py"

#: How long the server gets to start listening. A cold interpreter on a busy
#: runner needs well under a second; fifteen leaves headroom without hiding a
#: server that never starts.
SERVER_START_TIMEOUT_S = 15

#: Stylesheet and font-file hosts the free-fonts check lets through.
GOOGLE_FONTS_HOSTS = ("fonts.googleapis.com", "fonts.gstatic.com")


class GateError(RuntimeError):
    """A gate prerequisite is missing, so no check could run."""


def parse_engines(text: str | None) -> tuple[str, ...]:
    """Parse a comma list of engine names, rejecting anything the gate cannot launch.

    Duplicates collapse (first wins) so "chromium,chromium" cannot double the
    planned runs, and an unknown name is an error rather than a silent skip:
    a typo that quietly ran zero engines would print a green summary.
    """
    if text is None or not text.strip():
        return DEFAULT_ENGINES
    engines: list[str] = []
    for part in text.split(","):
        name = part.strip().lower()
        if not name:
            continue
        if name not in KNOWN_ENGINES:
            raise GateError(
                f"unknown engine {name!r}; choose from {', '.join(KNOWN_ENGINES)}"
            )
        if name not in engines:
            engines.append(name)
    if not engines:
        raise GateError("no engines selected")
    return tuple(engines)


def executable_for(engine: str, environ=None) -> str | None:
    """The explicit browser binary for an engine, from FKS_<ENGINE>_EXECUTABLE.

    The same variables `tests/support.py` reads, so one container setup
    serves both the test suite and the gate.
    """
    environ = os.environ if environ is None else environ
    return environ.get(f"FKS_{engine.upper()}_EXECUTABLE") or None


def load_playwright():
    """Return sync_playwright, or explain exactly how to install it.

    The gate never downloads tooling on its own. Implicit installs turn a
    two-second failure into a silent multi-hundred-megabyte download.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise GateError(
            "Playwright is not installed. Run: "
            "python -m pip install -r requirements-dev.txt, then: "
            f"{SETUP_COMMAND}"
        ) from exc
    return sync_playwright


def launch_browser(playwright, engine: str, *, headless: bool = True):
    """Launch one engine, translating a missing build into guidance.

    Pinning the package does not fetch the browser. A missing build and a
    wrong executable path look completely different but share one remedy, so
    the message carries both the install command and the override variable.
    """
    options = {"headless": headless}
    executable = executable_for(engine)
    if executable:
        options["executable_path"] = executable
    try:
        return getattr(playwright, engine).launch(**options)
    except Exception as exc:
        raise GateError(
            f"{engine} is not available to Playwright ({type(exc).__name__}). "
            f"Run: {SETUP_COMMAND}  "
            f"(or set FKS_{engine.upper()}_EXECUTABLE to an installed binary)"
        ) from exc


def free_ports(count: int = 2) -> list[int]:
    """Ask the OS for free loopback ports, held open together so they differ.

    There is a window between closing these and the server binding them.
    `serve_app` retries when the server loses that race, the same trade the
    existing live-integration tests make.
    """
    sockets = []
    try:
        for _ in range(count):
            sock = socket.socket()
            sock.bind(("127.0.0.1", 0))
            sockets.append(sock)
        return [sock.getsockname()[1] for sock in sockets]
    finally:
        for sock in sockets:
            sock.close()


@dataclass(frozen=True)
class ServedApp:
    """The two origins the dev server answers on."""

    studio_origin: str
    target_origin: str

    @property
    def origins(self) -> frozenset[str]:
        """Both origins, for the request router."""
        return frozenset({self.studio_origin, self.target_origin})


def _listening(port: int) -> bool:
    """True when something accepts a connection on the loopback port."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def _start_server(log) -> tuple[subprocess.Popen, int, int]:
    """Start serve.py once on fresh ports and wait, bounded, until both listen.

    Raises GateError with the server's own output if it exits or never
    listens, because "connection refused" from the first page load would hide
    the real reason.
    """
    studio_port, target_port = free_ports()
    process = subprocess.Popen(
        [
            sys.executable,
            str(SERVE_SCRIPT),
            "--quiet",
            "--no-sync",
            "--studio-port",
            str(studio_port),
            "--target-port",
            str(target_port),
        ],
        cwd=REPO_ROOT,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    deadline = time.monotonic() + SERVER_START_TIMEOUT_S
    while time.monotonic() < deadline:
        if process.poll() is not None:
            break
        if _listening(studio_port) and _listening(target_port):
            return process, studio_port, target_port
        time.sleep(0.05)
    _stop_server(process)
    log.seek(0)
    raise GateError(
        f"scripts/serve.py did not start listening: {log.read().decode(errors='replace').strip()}"
    )


def _stop_server(process: subprocess.Popen) -> None:
    """Stop the server: SIGTERM first (serve.py shuts down cleanly), kill as a last resort."""
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@contextmanager
def serve_app() -> Iterator[ServedApp]:
    """Serve the real Studio and demo on free loopback ports for the block.

    The shutdown sits in a finally block: a failing check must never leave a
    listening process behind. Retries a few times because a port can be
    taken between "free" and "bound".
    """
    with tempfile.TemporaryFile() as log:
        process = None
        last_error = None
        for _ in range(3):
            try:
                process, studio_port, target_port = _start_server(log)
                break
            except GateError as error:
                last_error = error
        if process is None:
            raise last_error
        try:
            yield ServedApp(
                studio_origin=f"http://localhost:{studio_port}",
                target_origin=f"http://localhost:{target_port}",
            )
        finally:
            _stop_server(process)


def request_origin(url: str) -> str:
    """The scheme://host[:port] of a URL, lower-cased, for origin comparison."""
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}".lower()


def classify_request(
    url: str, served_origins: frozenset[str], allowed_hosts: Sequence[str]
) -> str:
    """Decide what the router does with a request: "serve", "allow" or "block".

    "serve" is one of the two origins the gate owns. "allow" is an external
    host the current check explicitly opted into (Google Fonts, free-fonts
    check only). Everything else is "block": aborted and logged. Only
    http(s) reaches the router (Playwright does not route data: or blob:
    URLs), so a non-network scheme is not a leak and is not classified here.
    """
    origin = request_origin(url)
    if origin in served_origins:
        return "serve"
    host = urlsplit(url).hostname or ""
    if host in allowed_hosts:
        return "allow"
    return "block"


def make_router(served: ServedApp, allowed_hosts: Sequence[str], log: NetworkLog):
    """Return a one-parameter route handler bound to this run's policy.

    A factory closure rather than a lambda with default arguments:
    Playwright inspects a handler's parameter count, and a second parameter
    with a default is overwritten by the request object at call time.
    """

    def handler(route):
        url = route.request.url
        decision = classify_request(url, served.origins, allowed_hosts)
        if decision == "serve":
            route.continue_()
            return
        log.external.append(url)
        if decision == "allow":
            route.continue_()
        else:
            route.abort()

    return handler


def new_run_context(browser, profile: str, served: ServedApp, allowed_hosts=()):
    """Open an isolated browser context and page for one profile.

    Returns (context, page, network_log, errors). Every request leaves
    through the router, so no check can reach the network by accident.
    """
    context = browser.new_context(**VIEWPORTS[profile])
    log = NetworkLog()
    context.route("**/*", make_router(served, allowed_hosts, log))
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    return context, page, log, errors
