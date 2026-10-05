### Spec Compliance
- PASS: every 'Control+A' replaced by 'ControlOrMeta+A'; 11 one-line substitutions in 8 files (capture.py:109, _frontend_gate_live.py:109, test_live_integration.py:198, test_one_command_messages.py:164, test_one_command_next.py:203,223, test_one_command_proxy.py:109, test_one_command_vite.py:211, test_studio_dead_controls.py:524,534,547). Includes the two failing CI sites (vite:211, proxy:109).
- PASS: nothing else changed. Patch and `git diff --cached --stat` agree: 8 files, 11 insertions, 11 deletions, all the same substitution.
- PASS: class is complete. No Control+ literal remains.

### Checks run
- Remaining Control-modified keystrokes -> `git grep -n "Control+"` (excluding lockfiles) -> no hits.
- Other select-all / modifier keystrokes -> `git grep -E "press\(['\"][^'\"]*\+|keyboard\.(down|up)|select_text|triple|click_count|clickCount|\.select\(\)"` over tests, scripts, docs/assets -> only Shift+Tab (tests/test_studio_controls.py:624, test_studio_visual.py:292) and Alt+Arrow* (tests/test_studio_live.py:1363-1429). No Control+Backspace, Control+Arrow, Control+C/V, no keyboard.down('Control'), no triple-click or select_text.
- Shift+Tab -> focus traversal, same on macOS. Alt+Arrow* -> app-level keydown shortcuts for arrange (not text editing); they are asserted against app behaviour, not OS word-motion, so not part of this class. Not changed, correct.
- ControlOrMeta valid -> installed playwright 1.62.0 (pip show; driver package.json "version": "1.62.0"; requirements-dev.txt:1 pins playwright==1.62.0). driver types.d.ts:2267 lists "ControlOrMeta" modifier and coreBundle.js contains the string; documented as resolving to Meta on macOS, Control elsewhere. The driver's resolveSmartModifierString (coreBundle.js:20799) maps ControlOrMeta to Meta when process.platform is darwin, else Control; types.d.ts:21487 documents `page.keyboard.press('ControlOrMeta+A')` itself.
- Working tree unrelated state -> git status shows only the 8 staged files plus untracked .claude/, MEMORY-local.md (pre-existing).

### Strengths
- Complete sweep of the class, including the two non-test sites (dev gate script and screenshot capture) that would have failed on macOS later.
- No behaviour change on Windows/Linux (Control stays Control).

### Issues
#### Critical
None.
#### Important
None.
#### Minor
- Five sites (test_live_integration.py type_into, _frontend_gate_live.py type_into, capture.py type_into, plus inline copies in messages/next/proxy/vite/dead_controls) repeat the same click+select-all+type sequence; a shared helper would prevent a recurrence. Not asked for; out of scope.
- I did not execute a macOS run; the macOS behaviour rests on Playwright's documented semantics and the next macOS CI cell.

### Plan-mandated (for the owner)
None.

### Assessment
**Task quality:** Approved
**Reasoning:** The substitution is mechanical, complete across every Control-modified keystroke in the repo, valid in the pinned Playwright 1.62.0, and changes nothing else.
