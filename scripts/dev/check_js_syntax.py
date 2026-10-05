"""Syntax-check JavaScript files with `node --check`, one file at a time. Stdlib only.

`node --check a.js b.js` checks only `a.js` (node treats the rest as arguments to the
script), so the pre-commit hook, which passes every staged file at once, runs node once
per file here and fails if any file fails.

    python scripts/dev/check_js_syntax.py fontkit-bridge.js packages/fontkitstudio/src/cli.js
"""

from __future__ import annotations

import shutil
import subprocess
import sys


def main(argv: list[str] | None = None) -> int:
    files = sys.argv[1:] if argv is None else argv
    node = shutil.which("node")
    if node is None:
        print("check_js_syntax: node is not on PATH; install Node 22 or later", file=sys.stderr)
        return 1
    failed = [path for path in files if subprocess.run([node, "--check", path], check=False).returncode]
    for path in failed:
        print(f"check_js_syntax: FAIL {path}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
