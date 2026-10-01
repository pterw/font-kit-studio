# Font Kit Studio v0.1.1

A browser tool for comparing fonts and composing typography, PNG/SVG images, rules, spacers, and responsive rows. The app is one self-contained HTML file. Adobe kit loading is optional and requires your own kit access and a network connection.

## Run

Open `font_kit_studio_v0.1.1.html` directly (`file://`) in a modern browser. Select **Flow Composer**, choose **Editorial — Image + Body Row**, then select a row or child to edit it. Rows stack when the actual canvas reaches their collapse width. Imported JSON does not retain session image data; reselect PNG/SVG files.

## Development

The original supplied artifact is preserved at Git tag `supplied-v0.1.1`; implementation is on `feat/v0.1.1-responsive-rows`. There are no app runtime packages. Python and Node are used for verification; browser checks use the development-only Python Playwright installation.

Install Python 3 and Node.js (available as `node`), then run from this folder:

```text
python -m pip install -r requirements-dev.txt
python -m playwright install chromium firefox
python scripts/verify.py
```

The verifier checks static IDs, inline JavaScript syntax, the app SHA-256 and original input hashes against the supplied Git tag, then runs the unittest/browser suite. `python scripts/verify.py --static-only` skips that suite explicitly and does not establish full acceptance. Copies without Git metadata skip provenance verification explicitly. The supplied tag preserves original input; it is not an independently verified release.

- [Implementation plan](docs/plans/2026-09-30-v0.1.1-responsive-rows.md)
- [Progress and agent handoff](docs/implementation/progress.md)
- [Decisions and deviations](docs/implementation/deviations.md)
- [Original design](docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows-design.md)
- [Source provenance](docs/reference/SOURCES.json)

Validation commands and current evidence are recorded in the progress ledger. Read `AGENTS.md` before changing the project.
