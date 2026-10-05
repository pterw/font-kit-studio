"""Print one version's section of CHANGELOG.md, for the GitHub Release notes.

Usage: python scripts/dev/release_notes.py <version> [--changelog PATH]

The body under "## [<version>] - YYYY-MM-DD", up to the next "## [" heading, goes to
stdout as UTF-8 with LF. Exit 1 with one line on stderr when there is nothing to
release (no section, no ISO date, "Unreleased", an empty body); exit 2 when the
version text is not X.Y.Z with an optional pre-release. Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

DEFAULT_CHANGELOG = Path(__file__).resolve().parents[2] / "CHANGELOG.md"
VERSION = re.compile(r"v?(\d+\.\d+\.\d+(?:-[0-9A-Za-z][0-9A-Za-z.-]*)?)")
HEADING = re.compile(r"^## \[([^\]]*)\](?: - (\S+))?\s*$")
LINK_DEFINITION = re.compile(r"^\[[^\]]+\]:\s+\S+")
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def section(text: str, version: str) -> str:
    """The body of `version`'s section, or raise ValueError saying why not."""
    if version == "Unreleased":
        raise ValueError("Unreleased is not a release")
    lines = text.replace("\r\n", "\n").split("\n")
    start = None
    end = len(lines)
    for number, line in enumerate(lines):
        match = HEADING.match(line)
        if start is None:
            if match and match.group(1) == version:
                stamp = match.group(2)
                try:
                    if stamp is None or not ISO_DATE.fullmatch(stamp):
                        raise ValueError
                    date.fromisoformat(stamp)
                except ValueError:
                    raise ValueError(f"the [{version}] heading has no ISO date (YYYY-MM-DD)") from None
                start = number + 1
        elif line.startswith("## ["):
            end = number
            break
    if start is None:
        raise ValueError(f"no section for [{version}]")
    block = lines[start:end]
    # The last section is followed by the file's link definitions, "[x]: url".
    while block and (not block[-1].strip() or LINK_DEFINITION.match(block[-1])):
        block.pop()
    while block and not block[0].strip():
        block.pop(0)
    body = "\n".join(block)
    if not body.strip():
        raise ValueError(f"the [{version}] section is empty")
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("version", help="0.3.0 or v0.3.0")
    parser.add_argument("--changelog", type=Path, default=DEFAULT_CHANGELOG)
    args = parser.parse_args(argv)
    if args.version == "Unreleased":
        print("release_notes: Unreleased is not a release", file=sys.stderr)
        return 1
    match = VERSION.fullmatch(args.version)
    if not match:
        print(f"release_notes: {args.version!r} is not X.Y.Z", file=sys.stderr)
        return 2
    try:
        body = section(args.changelog.read_text(encoding="utf-8"), match.group(1))
    except (OSError, ValueError) as error:
        print(f"release_notes: {error}", file=sys.stderr)
        return 1
    sys.stdout.buffer.write((body + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
