# Verification tooling implementation report

Status: DONE, awaiting independent review. This prepares Task 5; no final UI acceptance is claimed.

Owned files: README.md, requirements-dev.txt, scripts/verify.py, and this report. No Git mutation, HTML/test edits or subagents. Pre-edit branch feat/v0.1.1-responsive-rows, HEAD 979fa782d388d232e993b9eb2f5932446d7b84f0; only controller progress ledger was modified. Parent reports graph Transport closed with unknown project/generation; exact source reads supplied evidence instead.

Implemented: development-only Playwright pinned to installed 1.62.0; brief fresh-copy installation/run instructions; standard-library verifier with script-relative root, static duplicate IDs, executable inline script syntax including module extension, temporary scratch, app SHA-256, original manifest hashes compared to supplied Git tag, and default current-interpreter unittest discovery. Missing Git metadata is explicitly skipped; available repository metadata with missing baseline or mismatched hashes fails. Static-only explicitly skips browser tests.

## Checks

Command (repository cwd): `python scripts/verify.py --static-only`

Exit 0, output:

```text
PASS HTML IDs: 38 unique static IDs
PASS JavaScript syntax: 1 executable inline blocks
SHA-256 font_kit_studio_v0.1.1.html: 632ebbbe7cf1dc03159ddc2f80e501eaae6d9d3d341e03888454f4b5686c6aab
PASS provenance: supplied-v0.1.1:font_kit_studio_v0.1.1.html cae14e847640c71f4e1b528222efe2a21372e73dfcaac0ae20c26d5cf546d949
PASS provenance: supplied-v0.1.1:docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows-design.md f8d48f1a23800cf9ac04517575447478b6eff9268333a980a085ac27bc0542a1
PASS provenance: supplied-v0.1.1:docs/reference/2026-09-17-font-kit-studio-v0.1.1-responsive-rows.md e3365196c271a6b8f387cdf9382b58217e7d279b8fd7b4f5356aebdea07b8090
SKIP unittest/browser tests: --static-only; full acceptance not checked
```

Also ran `python C:/Users/peter/Documents/Codex/2026-09-30/ref/outputs/font-kit-studio/scripts/verify.py --static-only` from `C:/Users/peter/Documents/Codex/2026-09-30/ref`: exit 0, same output. This confirms invoking-directory independence.

Temporary negative fixture command (PowerShell, repository cwd):

```powershell
python -c 'import pathlib, shutil, subprocess, sys, tempfile; source=pathlib.Path("scripts/verify.py").resolve(); fixtures=[("duplicate IDs","<div id=same></div><p id=same></p>","HTML IDs: duplicates"),("invalid JavaScript","<script>const = ;</script>","JavaScript syntax: inline block")]; checks=[]; temp=tempfile.TemporaryDirectory(); root=pathlib.Path(temp.name); (root/"scripts").mkdir(); shutil.copyfile(source,root/"scripts/verify.py"); [( (root/"font_kit_studio_v0.1.1.html").write_text(html,encoding="utf-8"), checks.append((name,subprocess.run([sys.executable,str(root/"scripts/verify.py"),"--static-only"],capture_output=True,text=True),expected))) for name,html,expected in fixtures]; [(print(name+": exit "+str(result.returncode)),print(result.stdout+result.stderr), None if result.returncode != 0 and expected in result.stderr else sys.exit(1)) for name,result,expected in checks]; temp.cleanup()'
```

Harness exit 0; exact output (temporary path is run-specific):

```text
duplicate IDs: exit 1
FAIL HTML IDs: duplicates: same

invalid JavaScript: exit 1
PASS HTML IDs: 0 unique static IDs
FAIL JavaScript syntax: inline block 1
C:\Users\peter\AppData\Local\Temp\font-kit-verify-k3qw1o8w\inline-1.js:1

const = ;

      ^

SyntaxError: Unexpected token '='
    at wrapSafe (node:internal/modules/cjs/loader:1787:18)
    at checkSyntax (node:internal/main/check_syntax:76:3)

Node.js v24.16.0
```

Blank lines in Node's Windows stderr were collapsed in the transcription. An earlier fixture harness attempt failed at command quoting before running fixture checks; switching to PowerShell single-quoted Python command and unquoted valid HTML attributes resolved it. No product/source mutation resulted.

## Self-review and limitations

- Subprocess argument lists avoid shell execution; Git blobs remain bytes for reliable hashes; temporary files are automatically removed. No dependencies beyond stdlib in verifier.
- README retains all original links, Adobe access/network caveat, original-baseline distinction and direct-file run instructions.
- Full browser suite intentionally not run during parallel implementation. Controller must run default verifier after app changes stop and arrange separate review.
- Static checks do not establish rendered UI behavior, dynamically created ID uniqueness, external script syntax or HTML conformance. Provenance checks original tagged inputs against manifest, not modified app equality to original input.
- App hash is a point-in-time snapshot while another writer owns HTML; final hash belongs to Task 5.
