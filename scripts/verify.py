"""Development verification; no runtime dependencies or persistent scratch files."""

import argparse
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
APP = "font_kit_studio_v0.1.1.html"
TAG = "supplied-v0.1.1"
JS_TYPES = {"", "module", "text/javascript", "application/javascript",
            "text/ecmascript", "application/ecmascript"}


class AppParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = Counter()
        self.scripts = []
        self.script = None
        self.module = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids[attrs["id"]] += 1
        kind = (attrs.get("type") or "").strip().lower()
        if tag == "script" and "src" not in attrs and kind in JS_TYPES:
            self.script = []
            self.module = kind == "module"

    def handle_data(self, data):
        if self.script is not None:
            self.script.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.script is not None:
            self.scripts.append(("".join(self.script), self.module))
            self.script = None


def run(args):
    return subprocess.run(args, cwd=ROOT, capture_output=True)


def provenance():
    try:
        available = run(["git", "rev-parse", "--show-toplevel"])
    except FileNotFoundError:
        print("SKIP provenance: Git executable unavailable")
        return
    if available.returncode or Path(available.stdout.decode().strip()).resolve() != ROOT:
        print("SKIP provenance: this copy has no repository Git metadata")
        return
    manifest = json.loads((ROOT / "docs/reference/SOURCES.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        name = entry["source"].replace("\\", "/").rsplit("/", 1)[-1]
        path = name if name == APP else "docs/reference/" + name
        baseline = run(["git", "show", f"{TAG}:{path}"])
        if baseline.returncode:
            raise ValueError(f"provenance: cannot read {TAG}:{path}")
        digest = hashlib.sha256(baseline.stdout).hexdigest()
        if digest != entry["sha256"]:
            raise ValueError(f"provenance: baseline hash mismatch for {path}")
        print(f"PASS provenance: {TAG}:{path} {digest}")


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--static-only", action="store_true",
                      help="skip unittest/browser checks; this is not full acceptance")
    options = args.parse_args()
    try:
        content = (ROOT / APP).read_bytes()
        parser = AppParser()
        parser.feed(content.decode("utf-8"))
        parser.close()
        duplicates = sorted(str(key) for key, count in parser.ids.items() if count > 1)
        if duplicates:
            raise ValueError("HTML IDs: duplicates: " + ", ".join(duplicates))
        print(f"PASS HTML IDs: {len(parser.ids)} unique static IDs")
        with tempfile.TemporaryDirectory(prefix="font-kit-verify-") as scratch:
            for index, (source, module) in enumerate(parser.scripts, 1):
                target = Path(scratch) / f"inline-{index}.{ 'mjs' if module else 'js'}"
                target.write_text(source, encoding="utf-8")
                try:
                    result = run(["node", "--check", str(target)])
                except FileNotFoundError as error:
                    raise ValueError("JavaScript syntax: Node executable unavailable") from error
                if result.returncode:
                    raise ValueError(f"JavaScript syntax: inline block {index}\n"
                                     + result.stderr.decode(errors="replace"))
        print(f"PASS JavaScript syntax: {len(parser.scripts)} executable inline blocks")
        print(f"SHA-256 {APP}: {hashlib.sha256(content).hexdigest()}")
        provenance()
        if options.static_only:
            print("SKIP unittest/browser tests: --static-only; full acceptance not checked")
        else:
            print("RUN unittest/browser tests", flush=True)
            result = subprocess.run([sys.executable, "-m", "unittest", "discover",
                                     "-s", "tests", "-v"], cwd=ROOT)
            if result.returncode:
                raise ValueError(f"unittest/browser tests: exit {result.returncode}")
            print("PASS unittest/browser tests")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
