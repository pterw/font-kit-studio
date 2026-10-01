# Verification tooling working-file review package

Git base: 979fa782d388d232e993b9eb2f5932446d7b84f0
This immutable package reviews a completed, uncommitted isolated scope. No Git mutation occurred; controller commits after review at a safe point.

## README.md

SHA-256: 89db6c10c287b3fd5a55210a4ec1014cd6abfed972884ed2ed13f50643bbdc85

```diff
--- a/README.md
+++ b/README.md
@@ -1,19 +1,29 @@
 # Font Kit Studio v0.1.1
 
 A browser tool for comparing fonts and composing typography, PNG/SVG images, rules, spacers, and responsive rows. The app is one self-contained HTML file. Adobe kit loading is optional and requires your own kit access and a network connection.
 
 ## Run
 
-Open `font_kit_studio_v0.1.1.html` in a modern browser. Select **Flow Composer**, choose **Editorial — Image + Body Row**, then select a row or child to edit it. Rows stack when the actual canvas reaches their collapse width. Imported JSON does not retain session image data; reselect PNG/SVG files.
+Open `font_kit_studio_v0.1.1.html` directly (`file://`) in a modern browser. Select **Flow Composer**, choose **Editorial — Image + Body Row**, then select a row or child to edit it. Rows stack when the actual canvas reaches their collapse width. Imported JSON does not retain session image data; reselect PNG/SVG files.
 
 ## Development
 
 The original supplied artifact is preserved at Git tag `supplied-v0.1.1`; implementation is on `feat/v0.1.1-responsive-rows`. There are no app runtime packages. Python and Node are used for verification; browser checks use the development-only Python Playwright installation.
+
+Install Python 3 and Node.js (available as `node`), then run from this folder:
+
+```text
+python -m pip install -r requirements-dev.txt
+python -m playwright install chromium firefox
+python scripts/verify.py
+```
+
+The verifier checks static IDs, inline JavaScript syntax, the app SHA-256 and original input hashes against the supplied Git tag, then runs the unittest/browser suite. `python scripts/verify.py --static-only` skips that suite explicitly and does not establish full acceptance. Copies without Git metadata skip provenance verification explicitly. The supplied tag preserves original input; it is not an independently verified release.
 
 - [Implementation plan](docs/plans/2026-09-30-v0.1.1-responsive-rows.md)
 - [Progress and agent handoff](docs/implementation/progress.md)
 - [Decisions and deviations](docs/implementation/deviations.md)
 - [Original design](docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows-design.md)
 - [Source provenance](docs/reference/SOURCES.json)
 
 Validation commands and current evidence are recorded in the progress ledger. Read `AGENTS.md` before changing the project.

```

## requirements-dev.txt

SHA-256: cfa2186c0470feac813f1ac67c71e54a53021ec949026946255874958d245e82

```diff
--- a/requirements-dev.txt
+++ b/requirements-dev.txt
@@ -0,0 +1 @@
+playwright==1.62.0

```

## scripts/verify.py

SHA-256: d74625984e1d44320a8331968e15ba34d7ee73d22c4eb0be348d818f73a217b5

```diff
--- a/scripts/verify.py
+++ b/scripts/verify.py
@@ -0,0 +1,118 @@
+"""Development verification; no runtime dependencies or persistent scratch files."""
+
+import argparse
+from collections import Counter
+import hashlib
+from html.parser import HTMLParser
+import json
+from pathlib import Path
+import subprocess
+import sys
+import tempfile
+
+
+ROOT = Path(__file__).resolve().parents[1]
+APP = "font_kit_studio_v0.1.1.html"
+TAG = "supplied-v0.1.1"
+JS_TYPES = {"", "module", "text/javascript", "application/javascript",
+            "text/ecmascript", "application/ecmascript"}
+
+
+class AppParser(HTMLParser):
+    def __init__(self):
+        super().__init__(convert_charrefs=True)
+        self.ids = Counter()
+        self.scripts = []
+        self.script = None
+        self.module = False
+
+    def handle_starttag(self, tag, attrs):
+        attrs = dict(attrs)
+        if "id" in attrs:
+            self.ids[attrs["id"]] += 1
+        kind = (attrs.get("type") or "").strip().lower()
+        if tag == "script" and "src" not in attrs and kind in JS_TYPES:
+            self.script = []
+            self.module = kind == "module"
+
+    def handle_data(self, data):
+        if self.script is not None:
+            self.script.append(data)
+
+    def handle_endtag(self, tag):
+        if tag == "script" and self.script is not None:
+            self.scripts.append(("".join(self.script), self.module))
+            self.script = None
+
+
+def run(args):
+    return subprocess.run(args, cwd=ROOT, capture_output=True)
+
+
+def provenance():
+    try:
+        available = run(["git", "rev-parse", "--show-toplevel"])
+    except FileNotFoundError:
+        print("SKIP provenance: Git executable unavailable")
+        return
+    if available.returncode or Path(available.stdout.decode().strip()).resolve() != ROOT:
+        print("SKIP provenance: this copy has no repository Git metadata")
+        return
+    manifest = json.loads((ROOT / "docs/reference/SOURCES.json").read_text(encoding="utf-8"))
+    for entry in manifest["files"]:
+        name = entry["source"].replace("\\", "/").rsplit("/", 1)[-1]
+        path = name if name == APP else "docs/reference/" + name
+        baseline = run(["git", "show", f"{TAG}:{path}"])
+        if baseline.returncode:
+            raise ValueError(f"provenance: cannot read {TAG}:{path}")
+        digest = hashlib.sha256(baseline.stdout).hexdigest()
+        if digest != entry["sha256"]:
+            raise ValueError(f"provenance: baseline hash mismatch for {path}")
+        print(f"PASS provenance: {TAG}:{path} {digest}")
+
+
+def main():
+    args = argparse.ArgumentParser(description=__doc__)
+    args.add_argument("--static-only", action="store_true",
+                      help="skip unittest/browser checks; this is not full acceptance")
+    options = args.parse_args()
+    try:
+        content = (ROOT / APP).read_bytes()
+        parser = AppParser()
+        parser.feed(content.decode("utf-8"))
+        parser.close()
+        duplicates = sorted(str(key) for key, count in parser.ids.items() if count > 1)
+        if duplicates:
+            raise ValueError("HTML IDs: duplicates: " + ", ".join(duplicates))
+        print(f"PASS HTML IDs: {len(parser.ids)} unique static IDs")
+        with tempfile.TemporaryDirectory(prefix="font-kit-verify-") as scratch:
+            for index, (source, module) in enumerate(parser.scripts, 1):
+                target = Path(scratch) / f"inline-{index}.{ 'mjs' if module else 'js'}"
+                target.write_text(source, encoding="utf-8")
+                try:
+                    result = run(["node", "--check", str(target)])
+                except FileNotFoundError as error:
+                    raise ValueError("JavaScript syntax: Node executable unavailable") from error
+                if result.returncode:
+                    raise ValueError(f"JavaScript syntax: inline block {index}\n"
+                                     + result.stderr.decode(errors="replace"))
+        print(f"PASS JavaScript syntax: {len(parser.scripts)} executable inline blocks")
+        print(f"SHA-256 {APP}: {hashlib.sha256(content).hexdigest()}")
+        provenance()
+        if options.static_only:
+            print("SKIP unittest/browser tests: --static-only; full acceptance not checked")
+        else:
+            print("RUN unittest/browser tests", flush=True)
+            result = subprocess.run([sys.executable, "-m", "unittest", "discover",
+                                     "-s", "tests", "-v"], cwd=ROOT)
+            if result.returncode:
+                raise ValueError(f"unittest/browser tests: exit {result.returncode}")
+            print("PASS unittest/browser tests")
+        return 0
+    except (OSError, ValueError, KeyError, TypeError) as error:
+        print(f"FAIL {error}", file=sys.stderr)
+        return 1
+
+
+if __name__ == "__main__":
+    sys.exit(main())

```

## docs/implementation/tasks/verification-tooling-report.md

SHA-256: d8267d865222499517e61b0436429fd4cb32a9f0a0b326c423b565c6a435d057

```diff
--- a/docs/implementation/tasks/verification-tooling-report.md
+++ b/docs/implementation/tasks/verification-tooling-report.md
@@ -0,0 +1,63 @@
+# Verification tooling implementation report
+
+Status: DONE, awaiting independent review. This prepares Task 5; no final UI acceptance is claimed.
+
+Owned files: README.md, requirements-dev.txt, scripts/verify.py, and this report. No Git mutation, HTML/test edits or subagents. Pre-edit branch feat/v0.1.1-responsive-rows, HEAD 979fa782d388d232e993b9eb2f5932446d7b84f0; only controller progress ledger was modified. Parent reports graph Transport closed with unknown project/generation; exact source reads supplied evidence instead.
+
+Implemented: development-only Playwright pinned to installed 1.62.0; brief fresh-copy installation/run instructions; standard-library verifier with script-relative root, static duplicate IDs, executable inline script syntax including module extension, temporary scratch, app SHA-256, original manifest hashes compared to supplied Git tag, and default current-interpreter unittest discovery. Missing Git metadata is explicitly skipped; available repository metadata with missing baseline or mismatched hashes fails. Static-only explicitly skips browser tests.
+
+## Checks
+
+Command (repository cwd): `python scripts/verify.py --static-only`
+
+Exit 0, output:
+
+```text
+PASS HTML IDs: 38 unique static IDs
+PASS JavaScript syntax: 1 executable inline blocks
+SHA-256 font_kit_studio_v0.1.1.html: 632ebbbe7cf1dc03159ddc2f80e501eaae6d9d3d341e03888454f4b5686c6aab
+PASS provenance: supplied-v0.1.1:font_kit_studio_v0.1.1.html cae14e847640c71f4e1b528222efe2a21372e73dfcaac0ae20c26d5cf546d949
+PASS provenance: supplied-v0.1.1:docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows-design.md f8d48f1a23800cf9ac04517575447478b6eff9268333a980a085ac27bc0542a1
+PASS provenance: supplied-v0.1.1:docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows.md e3365196c271a6b8f387cdf9382b58217e7d279b8fd7b4f5356aebdea07b8090
+SKIP unittest/browser tests: --static-only; full acceptance not checked
+```
+
+Also ran `python C:/Users/peter/Documents/Codex/2026-09-30/ref/outputs/font-kit-studio/scripts/verify.py --static-only` from `C:/Users/peter/Documents/Codex/2026-09-30/ref`: exit 0, same output. This confirms invoking-directory independence.
+
+Temporary negative fixture command (PowerShell, repository cwd):
+
+```powershell
+python -c 'import pathlib, shutil, subprocess, sys, tempfile; source=pathlib.Path("scripts/verify.py").resolve(); fixtures=[("duplicate IDs","<div id=same></div><p id=same></p>","HTML IDs: duplicates"),("invalid JavaScript","<script>const = ;</script>","JavaScript syntax: inline block")]; checks=[]; temp=tempfile.TemporaryDirectory(); root=pathlib.Path(temp.name); (root/"scripts").mkdir(); shutil.copyfile(source,root/"scripts/verify.py"); [( (root/"font_kit_studio_v0.1.1.html").write_text(html,encoding="utf-8"), checks.append((name,subprocess.run([sys.executable,str(root/"scripts/verify.py"),"--static-only"],capture_output=True,text=True),expected))) for name,html,expected in fixtures]; [(print(name+": exit "+str(result.returncode)),print(result.stdout+result.stderr), None if result.returncode != 0 and expected in result.stderr else sys.exit(1)) for name,result,expected in checks]; temp.cleanup()'
+```
+
+Harness exit 0; exact output (temporary path is run-specific):
+
+```text
+duplicate IDs: exit 1
+FAIL HTML IDs: duplicates: same
+
+invalid JavaScript: exit 1
+PASS HTML IDs: 0 unique static IDs
+FAIL JavaScript syntax: inline block 1
+C:\Users\peter\AppData\Local\Temp\font-kit-verify-k3qw1o8w\inline-1.js:1
+
+const = ;
+
+      ^
+
+SyntaxError: Unexpected token '='
+    at wrapSafe (node:internal/modules/cjs/loader:1787:18)
+    at checkSyntax (node:internal/main/check_syntax:76:3)
+
+Node.js v24.16.0
+```
+
+Blank lines in Node's Windows stderr were collapsed in the transcription. An earlier fixture harness attempt failed at command quoting before running fixture checks; switching to PowerShell single-quoted Python command and unquoted valid HTML attributes resolved it. No product/source mutation resulted.
+
+## Self-review and limitations
+
+- Subprocess argument lists avoid shell execution; Git blobs remain bytes for reliable hashes; temporary files are automatically removed. No dependencies beyond stdlib in verifier.
+- README retains all original links, Adobe access/network caveat, original-baseline distinction and direct-file run instructions.
+- Full browser suite intentionally not run during parallel implementation. Controller must run default verifier after app changes stop and arrange separate review.
+- Static checks do not establish rendered UI behavior, dynamically created ID uniqueness, external script syntax or HTML conformance. Provenance checks original tagged inputs against manifest, not modified app equality to original input.
+- App hash is a point-in-time snapshot while another writer owns HTML; final hash belongs to Task 5.

```
