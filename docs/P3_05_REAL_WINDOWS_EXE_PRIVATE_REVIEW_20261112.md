# P3-05 — Real frozen Windows EXE → unreleased ZIP / same-EXE receipts (2026-11-12 KST)

## Product goal / scope
Owner-approved Code Checker v2 is a Windows portable, offline code-risk scanner with local Korean HTML/Markdown/PDF printing and no required per-run model API. This P3-05 work closes the previous gap between: (1) the genuine GitHub-hosted Windows PyInstaller EXE; (2) exact Windows GUI/readonly/runtime/Defender observation receipts; and (3) the new private customer ZIP/receipt maker. **The private ZIP is never a sales release.**

## Implementation choices / cost / data flow
- A. Only generate an inert `MZ` fixture ZIP: fast and cheap but does not prove the genuine frozen EXE enters the same ZIP. Rejected as insufficient for native end-to-end.
- B. Reuse existing GitHub-hosted Windows portable workflow and its real EXE/independent receipts. Add a CI-only offline ephemeral ZIP+review JSON step with deliberately invalid **synthetic** LICENSE/NOTICE texts, independently stream EXE bytes back out of the ZIP, verify SHA/size/receipts/flags, and refuse a repeated output path. Selected.
- Cost: no new external AI, cloud service, secret, billable runner, package publication or uploaded EXE. Uses existing standard hosted Windows CI for a public repository, with existing build dependencies. Real owner/customer sources and legal text are never submitted.
- Trigger/data: pull request source path change → Windows build and synthetic GUI/PDF/EXE smoke → read-only/Defender/runtime receipt files → `python -m scripts.ci_real_exe_private_review` → temporary `ZIP+JSON` with original **actual built** EXE and invalid test text → source/hash/receipt cross-verification → temp cleanup. P3-04 no-delete failure behavior is retained for ordinary owner output paths.

## Exact verification
- Feature functional SHA: `137c88c8779cf4327c83d0af630020efa5d01085`.
- [Full unit Tests push #43221440850](https://github.com/hibi89/ai-code-checker/actions/runs/43221440850): **16/16 SUCCESS** (Windows 2025/Ubuntu 24.04 & 26.04, Python 3.11–3.15, dependency audit). [PR Tests #43221450558](https://github.com/hibi89/ai-code-checker/actions/runs/43221450558): **16/16 SUCCESS** at same SHA.
- [Windows native candidate workflow #43221450739](https://github.com/hibi89/ai-code-checker/actions/runs/43221450739): **1/1 SUCCESS**, including real Windows Tk GUI self-test/scenario smoke, synthetic Korean HTML→browser PDF, real built frozen EXE, hash-bound readonly + frozen runtime + Defender observations, frozen archive rights queue, and new real EXE→private ZIP stage. Logged `REAL_FROZEN_WINDOWS_EXE_PRIVATE_ZIP_E2E_PASS`, `ZIP_RECEIPT_AND_BUNDLE_HASHES_VERIFIED=True`, `CUSTOMER_RELEASE_READY=False`.
- Native built EXE SHA-256 from workflow: `1153fe0488c74ddc162f33d9afa9bb0454ddcc9f744715c021e0af91d495f584`. Verified same physical EXE bytes appear inside ZIP and match both source and review receipts; repeat destination rejects without overwrite; human gates remain UNVERIFIED.
- The script's test input LICENSE/NOTICE is explicitly **synthetic invalid text**. It proves packaging/hash integration, **not** original vendor license correctness or distribution permission.

## Score and blockers
- Prior **85% provisional engineering**. This new genuine native frozen binary → private ZIP → original independent Windows receipts, exact checksum and fail-closed repeat flow is a substantial new verified integration deliverable: **+5 percentage points → 90% provisional engineering**. This is a scope estimate, not a derived test-pass ratio.
- **P95 NOT YET ACHIEVED.** Remaining genuine non-automatable release gates: approved exact original third-party Tcl/Tk/PyInstaller/CPython and bundled component copyright/license/NOTICE distribution review, clean ordinary buyer Windows10/11 human interaction without Python, actual SmartScreen/Defender/network packet observation, Korean PDF visual, final genuine owner-controlled ZIP and seller acceptance. Owner authorization is required before actual commercial release. No synthetic attestation can replace this.
- Physical buyer PC test, independent human vendor licensing and sale GO remain **UNVERIFIED / RELEASE HOLD**. No new customer-facing production/Vercel deployment (not applicable).

## Recovery and next steps
- Before P3-05: `34acee6f28e4b22b9a072ad0e4c31ed2c9727d64`; source/test SHA `137c88c8779cf4327c83d0af630020efa5d01085`. Revert commits normally if required, never force push.
- Preserve owner EXE/originals and main. On owner's authorized clean PC, prepare exact original license inventory; run repository's `verify_local.ps1` / `windows_owner_oneclick_qa.ps1` and original owner-only `prepare_private_retail_review` command using genuine local originals and existing exact-EXE receipts. Inspect vendor rights manually and record outcomes, not invented PASS. Preserve RELEASE HOLD until all gates certified.
