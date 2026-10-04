# R1.2a brief: rename Studio to fontkit-studio.html

Plan: `docs/plans/2026-10-03-r1-one-command.md` (R1.2); execution:
`docs/plans/2026-10-04-r1-pr-a-sdd.md`. Constraints:
`.superpowers/sdd/r1-pr-a/constraints.md` (read all of it first; it has the stall rule and
which gates apply to your diff). Decision: D041.

## Goal

Studio is `fontkit-studio.html`. The old `font_kit_studio_v0.1.1.html` is a stub that
forwards to it with its query and hash, for one release. Every live reference uses the new
name. (The version check and bundle step are R1.2b.)

## Definition of done

- `git mv` rename; `fontkit-studio.html` has the same SHA-256 as the old file had at BASE.
- Opening the old name (file URL) lands on `fontkit-studio.html` with the same query and
  hash, in a real browser (test).
- Every live reference uses the new name (list in step 4); point-in-time records are not
  touched (constraints ruling 5).
- `scripts/verify.py` checks the new file and still verifies provenance against the old
  name at the `supplied-v0.1.1` tag.
- Both Python suite halves pass: every browser test loads Studio by the new name.

## Owns

`font_kit_studio_v0.1.1.html` (becomes the stub), `fontkit-studio.html` (rename only),
`tests/support.py` (the `HTML` constant only), `tests/test_frontend_gate_helpers.py`,
`tests/test_frontend_gate_runner.py`, `tests/test_preview_server.py` (file-name references
only), `tests/test_studio_rename.py` (new), `scripts/serve.py` (`STUDIO_HTML` only),
`scripts/dev/_frontend_gate_shared.py` (`STUDIO_HTML` only), `scripts/verify.py`,
`docs/assets/screenshots/capture.py`, `README.md` (file-name references and a migration
note).

Not yours: `fontkit-bridge.js`, `packages/**` (R1.2b, R1.3), `AGENTS.md` and
`CHANGELOG.md` (shared; draft their lines in the Handoff), `docs/implementation/**`,
older dated plans, `docs/specs/**`.

## Steps

- [ ] **1. Rename.** `git mv font_kit_studio_v0.1.1.html fontkit-studio.html`. Record
  `sha256sum fontkit-studio.html` and compare with `git show BASE:font_kit_studio_v0.1.1.html | sha256sum`.

- [ ] **2. Write the failing stub test** `tests/test_studio_rename.py`:

```python
"""The old Studio file name forwards to fontkit-studio.html for one release (D041)."""
import unittest

from support import ENGINES, HTML, REPO, close_contexts, new_context

OLD = REPO / 'font_kit_studio_v0.1.1.html'


class OldNameForwards(unittest.TestCase):
    def setUp(self):
        self.contexts = []

    def tearDown(self):
        close_contexts(self.contexts)

    def open_old(self, engine, suffix):
        context = new_context(engine)
        self.contexts.append(context)
        page = context.new_page()
        page.goto(OLD.as_uri() + suffix)
        page.wait_for_url(lambda url: '/fontkit-studio.html' in url)
        return page

    def test_forwards_with_query_and_hash(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                suffix = '?target=http%3A%2F%2Flocalhost%3A9%2F&x=1#composer'
                page = self.open_old(engine, suffix)
                self.assertEqual(page.url, HTML.as_uri() + suffix)
                self.assertTrue(page.title().startswith('Font Kit Studio v'))

    def test_forwards_without_query(self):
        for engine in ENGINES:
            with self.subTest(engine=engine):
                page = self.open_old(engine, '')
                self.assertEqual(page.url, HTML.as_uri())

    def test_stub_is_small_and_names_the_new_file(self):
        text = OLD.read_text(encoding='utf-8')
        self.assertLess(len(text.splitlines()), 20)
        self.assertIn('location.replace("fontkit-studio.html" + location.search + location.hash)', text)
        self.assertIn('<a href="fontkit-studio.html">', text)
```

  Check `support.py`'s helper names (`new_context`, `close_contexts`, `ENGINES`, `HTML`,
  `REPO`) before relying on them; use what is there. Update `support.HTML` to
  `REPO / 'fontkit-studio.html'` first. Run it: RED because the old file is gone (step 1).

- [ ] **3. Write the stub** at `font_kit_studio_v0.1.1.html`:

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Font Kit Studio has moved</title>
<script>location.replace("fontkit-studio.html" + location.search + location.hash);</script>
</head>
<body>
<p>Font Kit Studio is now <a href="fontkit-studio.html">fontkit-studio.html</a>. This page forwards there and goes away in the release after 0.3.0.</p>
</body>
</html>
```

  The forward target is a fixed relative file name; the page's own query and hash are
  appended after it, so no input can change the scheme or host (anti-pattern 4). GREEN.

- [ ] **4. Update live references** to `fontkit-studio.html`:
  `tests/support.py:23`; `tests/test_frontend_gate_helpers.py:214,221`;
  `tests/test_frontend_gate_runner.py:232`; `tests/test_preview_server.py:152,155,170,487,503,524`
  (line 593 is a list of overrides paths the server must refuse: use the new name there,
  since it is the Studio file the case protects); `scripts/serve.py:34`;
  `scripts/dev/_frontend_gate_shared.py:21`; `docs/assets/screenshots/capture.py:87`;
  `README.md:46` and `README.md:66`. Rewrite README line 66's sentence: the file is now
  `fontkit-studio.html`; the old name forwards until the release after 0.3.0.
  Then `git grep -n "font_kit_studio_v0.1.1"` and list every remaining hit in the report
  with why it stays (point-in-time, provenance, the stub, or shared-file Handoff).

- [ ] **5. `scripts/verify.py`.** Set `APP = "fontkit-studio.html"`, add
  `SUPPLIED_APP = "font_kit_studio_v0.1.1.html"  # Studio's name at the supplied-v0.1.1 tag (D041)`,
  and in `provenance()` map `name == SUPPLIED_APP` to that path. Run
  `python scripts/verify.py --static-only`: all PASS lines, provenance still verified.

- [ ] **6. Gates** (constraints.md): this diff triggers every gate, both suite halves
  included.

- [ ] **7. Handoff text** (the landing writes these): a CHANGELOG `[Unreleased]` line
  under "Changed" (Studio is `fontkit-studio.html`; the old name forwards until the release
  after 0.3.0); the `AGENTS.md` line 4 file name; the progress.md event.

Commit subject: `refactor(studio): rename Studio to fontkit-studio.html`. Body: why the
name changes (D041: a versionless name that says what the file is and pairs with the
bridge) and that the old name forwards for one release.

## Report

Code phase: `.superpowers/sdd/r1-pr-a/task-2a-code-report.md`. Landing:
`docs/implementation/tasks/r1-task-2a-report.md`.
