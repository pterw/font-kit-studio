# Font Kit Studio v0.1.1

A browser tool for comparing fonts and composing typography, PNG/SVG images, rules, spacers, and responsive rows. The app is one self-contained HTML file. Adobe kit loading is optional and requires your own kit access and a network connection.

## Run

Open `font_kit_studio_v0.1.1.html` in a modern browser. Select **Flow Composer**, choose **Editorial — Image + Body Row**, then select a row or child to edit it. Rows stack when the actual canvas reaches their collapse width. Imported JSON does not retain session image data; reselect PNG/SVG files.

## Development

The original supplied artifact is preserved at Git tag `supplied-v0.1.1`; implementation is on `feat/v0.1.1-responsive-rows`. There are no app runtime packages. Python and Node are used for verification; browser checks use the development-only Python Playwright installation.

- [Implementation plan](docs/plans/2026-09-30-v0.1.1-responsive-rows.md)
- [Progress and agent handoff](docs/implementation/progress.md)
- [Decisions and deviations](docs/implementation/deviations.md)
- [Original design](docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows-design.md)
- [Source provenance](docs/reference/SOURCES.json)

Validation commands and current evidence are recorded in the progress ledger. Read `AGENTS.md` before changing the project.
