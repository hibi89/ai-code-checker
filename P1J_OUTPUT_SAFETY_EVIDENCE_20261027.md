# P1-J: offline report output path guards — 2026-10-27 KST

## Verified branch and CI
- [PR #21](https://github.com/hibi89/ai-code-checker/pull/21) merged into `main` as `8485413205007366ffa683ec272a198f1f47f394`.
- Verified feature head `27d7825a51575fdd9ed82d0774811df48d4699d4`, baseline `d58f1f2459c7964586019b3da889a28b2b2006cb`.
- [General Tests CI 40494794235](https://github.com/hibi89/ai-code-checker/actions/runs/40494794235): 16/16 jobs SUCCESS. Windows Python 3.11 log confirms 175 unit tests run, including 8 new output-safety tests.
- [Windows EXE/Tk/HTML-to-PDF smoke CI 40494794185](https://github.com/hibi89/ai-code-checker/actions/runs/40494794185): 1/1 SUCCESS, including scripted Windows source-folder child-output rejection. Not equivalent to clean retail Windows, physical click, real-life file permissions, packet capture or visual PDF proof.
- [Phase2 synthetic performance/dependency CI 40494794230](https://github.com/hibi89/ai-code-checker/actions/runs/40494794230): 3/3 SUCCESS.

## Implementation, rationale and scope
- Alternative A: OS firewall/packet capture/SmartScreen on CI; privileged/environment-specific, does not verify real customer machine. DEFER to separate independent acceptance.
- Alternative B: enforce local output paths first, no new packages, APIs, privileges, source execution or customer uploads. **Chosen/implemented.**
- `output_safety.py` validates the destination before output directories are created. Rejects lexical UNC/device-looking path roots, existing symlink/reparse/junction components, non-directory destinations and a path equal to or below the folder being scanned.
- `desktop_core.run_scan` validates before reading the project source; `offline_report.write_report` enforces path checks for CLI and Tk outputs, while preserving existing no-overwrite atomic paired creation logic. A single file/paste can write to an ordinary external or sibling folder as before.
- `scripts/map_frozen_licenses.py` includes the new `output_safety` code as a first-party module in the frozen EXE inventory. Does NOT imply original third-party NOTICE or license clearance.
- Tests `tests/test_output_safety.py` (eight synthetic scenarios) + Windows scripted case in `scripts/windows_gui_e2e.py`.

## Explicit limitations and next gates
- This is preflight policy, **not** TOCTOU-proof protection against hostile concurrent filesystem changes. UNC-like paths are blocked but mapped drives or cloud-synced folders are **not** automatically detected or blocked; owners must choose suitable offline local storage. No OS network packet capture was performed; synthetic Python socket patches do not establish an external traffic guarantee.
- No real retail Windows Defender/SmartScreen, antivirus reputation, code-signature approval, clean machine packet inspection, human browser PDF visual review or complete frozen EXE dependency legal NOTICE approval. Customer-ready signing, EXE release, sales and launch remain BLOCKED.
- Legacy Gemini v1 unchanged; JS/TS product coverage is still limited. Vercel/production URL NOT APPLICABLE.
- Recovery: revert PR #21, prior main `d58f1f2459c7964586019b3da889a28b2b2006cb`; never force push.
- Next `ㄱ`: re-read actual live main/CI and close remaining acceptance gates where possible, beginning with real Windows/packet/privacy evidence design or preflight hardening that avoids dangerous file deletion. Keep manual Windows, vendor NOTICE and release gates explicitly unverified.
