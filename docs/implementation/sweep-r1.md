# Sweep: R1 (0.3.0) release point (2026-10-04)

A read-only consistency pass over R1 PR C (PR #12). Three sweeps ran:

- before the docs task, to find its inputs;
- after the first landings;
- at the release point, over the version bump.

Each one searched every tracked file and kept live files apart from point-in-time
records. This file lists what they found and what became of it.

## Fixed in this pull request

- **Docs that predated the one command:**
  - **README:**
    - The Quickstart started with a clone and a script tag.
    - "No npm package".
    - The hand-written Vite recipe.
    - "Add fontkit to your app" and "Why fontkit" (D040).
    - "The Vite and Next.js recipes were not run in a real framework project".
    - The test-module table lacked every module R1 added.
  - **The package README:** "arrives in 0.3.0; this release is the package foundation".
  - All rewritten in task 8c (`tasks/r1-task-8c-review.md`).
- **Studio told npm users to run `python scripts/serve.py` or add a script tag.** The
  sweep found a third place the 8b brief had missed: the status badge's tooltip. Fixed in
  task 8b.
- **A wrong limit in the plan.** The plan said proxy mode keeps Studio's settings apart
  from the app. In fact the app runs at the proxy's address, so its own storage does not
  carry over, and, as a probe in Chromium and Firefox then showed, an app embedded in
  Studio gets its `Lax`, `Strict` and (in Chromium) default cookies only when it runs on
  the same host name as Studio (`127.0.0.1`), in Vite mode too. The README now says so.
- **Select-all in browser tests on macOS.** `Control+A` in 11 lines of 8 files (tests, the
  frontend gate, the screenshot script) is now `ControlOrMeta+A`.
- **The tarball test raced the bundle test** (Node tests share `dist/`). No test writes the
  real bundle now, and a guard enforces it.
- **Versions:** Studio's title and eyebrow, the bridge header, the package and two test
  assertions read 0.3.0. `CHANGELOG.md` is dated, with compare links on `v0.2.1...v0.3.0`.
- **Roadmap docs:**
  - product-direction's "Where it stands" listed the one-command start as not built;
  - the extension note said a script tag is always needed.

  Both are updated at the release point.

## Left as they are, on purpose

- **Live text that names 0.2.1 on purpose:**
  - test docstrings that name the task that added them;
  - the old-name stub, `font_kit_studio_v0.1.1.html`, which goes in the release after
    0.3.0 (D041);
  - the 0.2.1 compare link and the "Shipped (v0.2.1)" history in the roadmap.
- **Point-in-time records** (task records, earlier plans, the spec) keep their wording.
- **`xxx`** in two tests is test data, not a marker.

## Open, for after 0.3.0

- **Cookies of apps used at `localhost`.** Studio and the proxy are served at
  `127.0.0.1`, so an app embedded in Studio from `localhost` loses its `Lax`, `Strict` and
  default cookies (probe: only `SameSite=None` arrives). Serving Studio and the proxy at
  `localhost` (still bound to loopback) would fix it in both modes, but it changes every
  origin the package hands out and has to handle `localhost` resolving to `::1` first. A
  task of its own after 0.3.0; the README states the limit.
- **CSP checks in plugin mode** read the page's meta tag and `server.headers`, not a
  policy set by the app's own middleware (README, known limits).
- **The co-author check** does not match a `#`-prefixed `Co-Authored-By:` line, which git
  does not read as a trailer (from the pre-commit hooks pull request).
- **Earlier follow-ups,** still open in `sweep-v0.2.1-pr-b.md`:
  - dead CSS `.c-field.span-4/.span-6`;
  - unused ids `deviceViewportBar` and `previewScroller`;
  - the bridge pop-out emoji;
  - one `syncRowLayouts()` on Composer show;
  - the 390 px "No bridge answered" badge overflow.
