# P1-I — current-session paired local report cleanup evidence (2026-10-27 KST)

## Purpose and verified implementation
- [PR #20](https://github.com/hibi89/ai-code-checker/pull/20) was merged as source main SHA `779b611bf2f932fa219631c32f810fa3253111c4` from feature SHA `78d5ad675ee0bf7d2502fc91e8d72db4fe5b9825`.
- Target: explicit user-confirmed removal of only the HTML and Markdown report pair created in the currently active session. Never automatically delete reports or source code and never enumerate or delete arbitrary directories.
- `report_cleanup.py` records parent directory, regular-file identity (device/inode/mtime/size) and SHA-256 of each of the two files, with a 32 MiB per-file cap for receipt generation. It validates both files before unlinking either. Symlinks, hardlinks, altered files, missing partner, unexpected directory changes and unverified receipts fail closed. This is session-local memory metadata only, not a durable proof against a hostile actor racing filesystem operations.
- `desktop_core.py` creates an optional receipt only after a completed report write; absence disables GUI deletion without changing scan status. `desktop_ui.py` prompts with exact paths, defaults to *No*, removes only upon explicit confirmation, disables stale/ongoing/cancelled actions, and reports partial I/O failure without a false success claim.
- `scripts/map_frozen_licenses.py` adds only the project's new first-party `report_cleanup` Python module to the conservative package classification. **No** third-party legal notice or release approval was changed.

## Design comparisons
- Unattended folder cleanup: may remove unrelated reports, hard to recover, no direct API cost but unacceptable safety risk; rejected.
- User confirmation plus two-file receipt: zero new runtime dependencies/API expense, testable, limited scope and maintainable; chosen.
- Recycle Bin integration or complex transactional staging: user-visible recovery potential but adds OS-specific support/code, not part of this MVP; deferred.

## Verification
- [Standard CI run 40493402697](https://github.com/hibi89/ai-code-checker/actions/runs/40493402697): 16/16 jobs SUCCESS, including Windows Python 3.11 **167 unit tests PASS**.
- [Windows packaged GUI/EXE run 40493399705](https://github.com/hibi89/ai-code-checker/actions/runs/40493399705): 1/1 job SUCCESS, including synthetic Tk cancellation and confirmed/declined report deletion, packaged candidate smoke and provenance assertions.
- New synthetic `tests/test_report_cleanup.py`: 8 contract cases (exact scope, tamper, missing pair, symlink, hardlink, unrelated targets, second-delete refusal and non-atomic I/O failure). First run failed with two uncaught FileNotFoundError paths; fixed in `report_cleanup.py`.
- Initial Windows package provenance run failed because new first-party module was not listed in the component mapper; corrected category and added synthetic regression. An initial regression had a mistaken fixed expected unresolved count; replaced with comparison to original fixture's unresolved count. Final CI PASS.
- No live customer's code was executed or uploaded in these tests. Synthetic Windows hosted runner is not a verified retail consumer PC.

## Limits and gates
- Deletion of two files is **not atomic**: a permission or I/O failure during the second unlink can leave only the Markdown file. The UI reports this and requires manual inspection. Receipt is not persisted between app sessions. No recycling/undo mechanism.
- Directory-wide deletion, deletion of arbitrary or historical reports, or deleting source code is absent.
- Windows physical interaction on retail machines, Defender/SmartScreen, operating-system packet capture, visual Korean PDF review, code signing, actual binary license/NOTICE attribution/commercial legal approval, independent security-rule accuracy and user acceptance remain **UNVERIFIED**.
- This is a developer-only unsigned Windows candidate, not a customer-ready release. Vercel / Production URL: NOT APPLICABLE.
- Rollback by PR #20 revert, or prior main `a5ab0ab0745ca1b6b3cc31e1af0a009dbf6a7a79`. Never force push. This file is documentation; any subsequent docs commit changes live HEAD and CI must be checked again.
