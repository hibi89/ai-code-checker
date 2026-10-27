# P1-K — Windows frozen EXE full GUI scenario evidence, 2026-10-27 KST

## Confirmed code and tests
- [PR #22](https://github.com/hibi89/ai-code-checker/pull/22) **merged** as source main `39d5db20ac3db3294bd45ce76f6d32c4f9fab65d` from verified feature `523679d26dc6e7d3a8756bd8a2652cb19a25450f`; rollback prior main `2d7bfd30a0bb50547c86841abc2fbb673339dcb1`.
- `desktop_ui.py` implements explicit developer-only `--scenario-smoke`. Inside the **same process** as the bundled Windows EXE, actual Tk widget callbacks select synthetic paste input, run preview, run offline scan, verify an evidence-backed finding, check Korean HTML/Markdown and local output, and ensure report and cleanup GUI controls are available. Bounded timeouts and fail-closed conditions; temp fixtures automatically removed.
- `scripts/build_windows_portable.ps1` runs the new frozen process scenario immediately after the existing frozen core self-test and Tk window smoke. On failure it rejects the candidate. Regular customer launch with no CLI arguments is unchanged.
- All tests use only synthetic local code, no customer source, new dependency, AI key, network call or upload.

## Actions evidence
- [Tests Actions 40496583577](https://github.com/hibi89/ai-code-checker/actions/runs/40496583577): 16/16 matrix jobs SUCCESS, including Windows and Ubuntu matrix.
- [Windows candidate Actions 40496583605](https://github.com/hibi89/ai-code-checker/actions/runs/40496583605): 1/1 job SUCCESS. Actual log lines show `WINDOWS_BROWSER_PDF_SYNTHETIC_PASS`, `PACKAGED_TK_WINDOW_STARTUP_PASS`, `PACKAGED_TK_FULL_WORKFLOW_PASS`, `CANDIDATE_BUILT_SMOKE_PASS`. These checks ran on the feature head above.
- This specifically closes the gap where Windows CI's full scripted Tk flow ran only in Python source while the previous packaged EXE was checked for self-test and window initialization.

## Design choice and remaining release gates
- Option A: Windows-level network surveillance, AV reputation or SmartScreen automation in hosted CI. The runner is not a clean retail PC; it could introduce OS config/permissions and unreliable observation. This is deferred, not asserted PASS.
- Option B: package-integrated synthetic full GUI test, using existing Tk and Python APIs, no extra costs/runtime deps and little maintenance. Selected and CI tested.
- Windows manual acceptance still **UNVERIFIED**: actual clean consumer PC with Defender, SmartScreen, end-to-end GUI physical interactions, OS-level packet capture, report rendered PDF visual review, original binary NOTICE and redistribution counsel, binary signing, final customer delivery. Not a signed/public EXE, no user-approved launch or sales.
- Product does NOT implement an independent eight-AI council or full JS/TS semantic scanning. Existing Python AST candidate/limited checks and original Gemini v1 distinction remain.
- No Vercel or Production URL (not applicable). `main` docs SHA advances after code merge; check actual HEAD and any post-doc Actions separately.
