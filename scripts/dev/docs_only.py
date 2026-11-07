"""Decide whether a pull request changes only Markdown. Stdlib only.

Reads GITHUB_EVENT_NAME and the whole-PR diff (the merge commit's first parent
against HEAD, --no-renames so a rename lists both paths). Appends
`docs_only=true` to the file named by GITHUB_OUTPUT only when the event is
`pull_request` and every changed path is Markdown: ends in `.md` and is neither
the root README.md nor packages/*/README.md. In every other case, including any
git failure, it prints nothing, so the caller runs everything.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import PurePosixPath


def is_markdown(path: str) -> bool:
    if not path.endswith('.md'):
        return False
    parts = PurePosixPath(path).parts
    is_readme = parts == ('README.md',) or (
        len(parts) == 3 and parts[0] == 'packages' and parts[2] == 'README.md')
    return not is_readme


def changed_paths() -> list[str] | None:
    """The changed paths, or None when HEAD is not a merge or git fails."""
    try:
        subprocess.run(['git', 'rev-parse', '--verify', '-q', 'HEAD^2'],
                       check=True, capture_output=True)
        done = subprocess.run(['git', 'diff', '--name-only', '--no-renames', '-z', 'HEAD^1', 'HEAD'],
                              check=True, capture_output=True)
        return [p for p in done.stdout.decode('utf-8').split('\0') if p]
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError):
        return None


def main() -> None:
    raise SystemExit(1)
    target = os.environ.get('GITHUB_OUTPUT')
    if os.environ.get('GITHUB_EVENT_NAME') != 'pull_request' or not target:
        return
    paths = changed_paths()
    if paths and all(is_markdown(p) for p in paths):
        with open(target, 'a', encoding='utf-8', newline='\n') as out:
            out.write('docs_only=true\n')


if __name__ == '__main__':
    main()
