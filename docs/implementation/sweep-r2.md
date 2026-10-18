# R2 (0.4.0) live-claim sweep

Date: 2026-10-18. Tree: `d49158b` (PR C code complete), branch `feat/r2-visited-pages`. Live files: README.md, the
package README, CONTRIBUTING.md, AGENTS.md, docs/agents/, docs/roadmap/, docs/specs/, CHANGELOG.md's newest section,
the ledger's Current state and every non-Markdown file. Point-in-time records (dated CHANGELOG entries, plans,
deviations, task records, verification and sweep files) describe their own time and are not changed.

| Claim | Where it lives | Result |
|---|---|---|
| Version labels | Studio title and eyebrow, bridge header, package.json, the vite-ts linked lock record | All read 0.4.0. Protocol 1 and export JSON format 0.1.1 stay and are asserted. |
| Remaining 0.3.x mentions | README and package README settings note, README command floor, release-note test data | Historical upgrade note (0.3.0 to 0.3.1), a correct compatibility floor ("0.3.0 or later" for the command, roles need 0.4.0) and synthetic test input. Kept. |
| Old Studio file name | README, CHANGELOG 0.4.0 Removed, scripts/verify.py, tests/test_studio_rename.py | Only where its removal is explained, in provenance (the supplied-v0.1.1 tag) and in the test that it is absent. |
| "Not built" | README roadmap paragraph, docs/roadmap/product-direction.md | Names pairing, type scales, token output and the extension only; role detection is listed as built for 0.4.0 and not yet released. |
| Role messages and capabilities | README protocol table and Detected roles section | `design:roles-page` and `capabilities.roleRevision` documented as the code sends them. |
| Tool and model names | scripts/dev/check_commit_messages.py, its tests, .gitignore, AGENTS.md | Only in the commit-signature checker, its tests, ignore rules and the agent rules. None in product docs. |
| Process terms | fontkit-studio.html, scripts/dev/_frontend_gate_report.py, tests/test_studio_live.py | Pre-existing wording ("Fullscreen Controller", a log reader, a 0.2-era docstring). None added by R2. |

No live claim needed a change after the release-point docs landed. Known limits shipped in 0.4.0 are listed in the
README's Detected roles section and in [verification](verification-r2.md#known-limits-shipped-in-040).
