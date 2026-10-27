# P1-T — Recent local report list (2026-10-27 KST)

## Approved design comparison
- Persistent SQLite/JSON index: fast later listings but adds stored report metadata, stale references, cleanup/migration and privacy surface. Rejected.
- On-demand bounded local directory discovery: no persistence, no new dependency/network; cap 512 candidate HTML names, validate local HTML/MD pair and format, list latest 20 by modification time (maximum requested 50). Selected.

## Implementation scope
PR #31 branch feature/p1t-recent-report-list. Added report_history.list_historical_reports; Tk recent-list Toplevel chooser while retaining explicit OS file picker. No in-session deletion authority is conferred. Strict selected-path revalidation happens before open; symlink/hardlink/reparse, outside-folder and network checks from P1-S remain.

## Tests and observed failures
- New 6 synthetic tests for ordering, read-only behavior, missing/invalid pairs, limits, links, stale selection and locality, plus hosted Windows Tk scripted modal selection and deletion separation.
- Early Python Tests runs 40515777904 and 40515927835 failed on Windows only: Windows DirEntry.stat().st_nlink can be 0; path lstat/fstat validator was already the authoritative single-link check. Fixed in e62a1b9.
- Windows Tk 40516387299 reached every GUI scenario including the new recent picker, and emitted GUI_E2E_FAILURE: [] due only to outdated hardcoded 10-result assertion. Updated expected count to 11 in 54edcd2.
- An unexpected empty-list message box could hang a hosted scripted Tk test; synthetic test now fails fast by mocking unexpected info/error dialogs in 0a8a388. This is a test-harness guard only.
- Current final branch source/test HEAD: 54edcd205033a6abb4fb4e9f6bf32ff84e372702. Full final-head CI **PENDING**; do NOT claim PASS, merge, release or customer acceptance without checking live status.

## Security and release limits
Local-only, no customer code execution, no API key/upload/telemetry, no additional dependency, no report or source write, no signing or binary distribution. Listing by mtime is not proof of creation date. Header checks are not cryptographic authenticity. Hostile concurrent filesystem changes and cloud-sync risks remain. Independent clean Windows, Defender/SmartScreen file scan, OS packet capture, Korean PDF visual and original third-party NOTICE/legal signoff remain UNVERIFIED/BLOCKED.

## Next ㄱ
Re-fetch PR #31 live head, ensure both Tests matrix and Windows packaged candidate workflow PASS on the exact same final source HEAD. Inspect any failures first (no blind retries). Merge PR only with green, confirm main commit and post-merge CI. Update STATUS/HANDOFF/RESUME from actual evidence. No force push. No Vercel production deployment for local app.
