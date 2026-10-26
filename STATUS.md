# Code Checker Status

Updated: 2026-10-26 KST (time not recorded)
Repository: hibi89/ai-code-checker (public, MIT)
Default branch: main
Main baseline SHA (observed before planning): 8c72a6f3bc30f2a720c10f3a5a9dd366f0d059ab
Planning branch: plan/offline-zero-cost-v2

## Verified existing implementation
- CLI existing code handles file/folder/ZIP, filters, redaction, limited Python AST checks, Gemini single Interactions structured call, cost guard and Markdown report.
- Existing published plan is **report-only**, human-reviewed, with customer NOT receiving software.
- Existing input default max 50 files / 512 KiB, proposal to remove the 500-lines paid scope restriction does not change CLI code.
- Latest baseline commit had GitHub Actions 16 of 16 jobs passed (15 OS/Python tests plus dependency audit), as observed 2026-10-26.
- Existing file PILOT_EVALUATION.md records failed 503/429/json_invalid/APIConnectionError, no confirmed successful real Gemini analysis report.
- Current product is NOT ready for verified customer sales, despite offline unit test/CI results.

## New proposed direction
- Offline-first portable program sale, no mandatory API or account; separate optional seller-assisted report.
- Product targets and price hypotheses in REQUIREMENTS.md / ARCHITECTURE_V2.md / PRODUCT_STRATEGY_V2.md.
- This planning branch changes documentation ONLY; no engine/UI/binary/CI policy implemented or tested.
- Main remains unchanged. No new private repo, API request, third-party service or fee authorized.
- Windows portable build, PDF printing, offline network isolation, Python+JS/TS coverage and vendor support requirements UNVERIFIED.

## Work status
- Complete: baseline repository and CI inspection, current API failure assessment, zero-cost alternatives / legal-tool research, planning branch and documents.
- In progress: owner review of offline-first product pivot.
- Blocked pending approval: material product change, code/CI refactor, any private code repository.
- Not started: real packaged app, clean Windows install test, market listing, payment, release.
- Next package (after approval): lock offline MVP acceptance and implement safe local scan gate on feature/offline-core; run synthetic offline regression, no Gemini usage.

## Security, storage, and deployment
- Production URL/Vercel: not applicable (local CLI; no existing production service verified).
- Private .env and real keys remain on local owner machine, never in repo.
- Historical sample ZIPs are synthetic; no real customer code is authorized for testing.
- CI uses public standard runners; private CI quota is separate if private distribution is later approved.

## Divergence notice
Original PRODUCT_PLAN_KMONG.md still describes a report-delivery service; this v2 proposal would change primary product to offline customer-operated software. Do not silently treat proposal as implemented/approved.
