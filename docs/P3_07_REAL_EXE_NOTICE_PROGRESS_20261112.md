# P3-07 — Actual Windows EXE / 71 unresolved NOTICE review roster

**Checked:** 2026-11-12 KST. **Target:** Code Checker 100% customer-release quality after owner sign-off; P95 provisional engineering maintained and **RELEASE HOLD**.

## Objective and design decision
- Reuse existing real native Windows PyInstaller EXE, archive provenance, installed component mapping, original-license candidate staging and 71-name outstanding review queue.
- A: only produce a printable owner worksheet (existing) with no machine-verified investigation state; cheaper but individual reviewed rows can drift from a new binary. **Rejected.**
- B: bind actual Windows EXE SHA-256 to all unresolved archive entries and a fresh local per-entry `UNREVIEWED` progress JSON plus summary. Reject forged `customer_release_ready=True` or stale queue binding; enforce no overwrite. Selected.
- Trigger: scoped feature branch push changes to `scripts/ci_real_frozen_notice_review.py` or `.github/workflows/windows-portable.yml`. Existing Windows job runs all prior EXE/GUI/PDF/native LICENSE metadata and queue steps first, then `python -m scripts.ci_real_frozen_notice_review`.
- Data: locally synthesized test code in EXE, build/archive metadata and only original Windows-hosted candidate; no actual customer EXE, legal original text, credentials, code, account data, paid APIs, network monitoring, GitHub Actions artifact uploads or new deployment. Local progress files vanish with runner, **not** legally effective owner certification.

## Exact evidence
- Code SHA `ec83e83e5a0becc6e9fde61b6e2970d773633e01`.
- [GitHub Actions Tests #43226330001](https://github.com/hibi89/ai-code-checker/actions/runs/43226330001): **16/16 SUCCESS** at exact source SHA.
- [Windows native candidate #43226330609](https://github.com/hibi89/ai-code-checker/actions/runs/43226330609): **1/1 SUCCESS** at exact source SHA. Stage `Validate exact actual EXE NOTICE roster and owner progress gates (local only)` successful; logs `REAL_EXE_NOTICE_REVIEW_QUEUE_PROGRESS_PASS`, `UNRESOLVED_REVIEW_ROWS=71`, `HUMAN_RIGHTS_AND_BUYER_ACCEPTANCE=UNVERIFIED`, `CUSTOMER_RELEASE_READY=False`.
- This native build EXE SHA256: `7579fb43d65a407494f7181419214e32712f2f03b5feb500de494fc1f46c8880`. The exact SHA is checked against archive queue, template and summary, with forged approval and stale queue rejected.
- Still passes earlier `EXTRACTED_KOREAN_PATH_PYTHON_FREE_EXE_SMOKE=PASS` for hosted runner. Hosted Windows Python is installed, though excluded from child PATH; not an actual no-Python buyer PC.
- 71 rows must be individually human reviewed against the **actual original**, ownership/version and redistribution/NOTICE conditions before any legal conclusion. No permission claimed from build metadata.
- Earlier full Python tests and hosted Windows synthetic UI/PDF are CI, not customer physical Windows, human Korean PDF, SmartScreen, actual packet capture or refund/sale approval.

## Status / scoring
- **95% provisional engineering unchanged.** P3-07 improves auditable owner evidence tracking and closes a gap in Windows CI but is not grounds for 96–100%.
- **100% NOT reached.** RELEASE HOLD; all actual buyer-machine and copyright/redistribution/NOTICE/manual product and commercial approvals remain open.
- Latest owner work-marker rule: `[작업중]` is retained in central Kmong table for this **new 100% final-acceptance stage** until target is verified; paused/blocked state alone does not authorize removal.
- Production/Vercel N/A, draft PR #82 not merged, repository main unchanged.

## Owner-only completion gates (no preapproval)
1. On an ordinary clean Windows 10/11 computer with Python not installed, open the actual final candidate EXE and interactively test clipboard/TXT/ZIP/folder/HTML/Markdown/browser-to-PDF with Korean paths, no user-source execution.
2. Keep Defender and SmartScreen enabled, record real warnings/blocked states without bypassing security; if packet capture is authorized, confirm unexpected network connections and privacy.
3. For the **same actual EXE SHA** inspect original Tcl/Tk/CPython/PyInstaller license terms, all unresolved bundled owners/versions/redistribution/attribution/NOTICE rows. Use `scripts.track_notice_review` to record stages (but it deliberately cannot certify release). Generate customer exact ZIP only with verified legal originals using the owner-only private path.
4. Explicitly review customer readme/license/NOTICE, support/refund and price/terms, release/signature SmartScreen consequence; approve exact final binary/package SHA only after all evidence is genuinely reviewed. Until then no customer delivery, sale or public distribution.

## Rollback/traceability
- Previous P3-06 docs `930adb18f4efa1f8330ca631823e3dc5ccdcdf2a`, P3-06 functional `3d92c4c0f3886d80e499261b8b6d44b7791713c4`; P3-07 native code `ec83e83e5a0becc6e9fde61b6e2970d773633e01`. Normal revert possible, no force push, no original changes.
