# CODE CHECKER — STATUS (source of truth)

Updated: 2026-10-26 KST; status snapshot from GitHub after latest design review.
Repository: https://github.com/hibi89/ai-code-checker | Public / MIT | baseline main before docs: `8c72a6f3bc30f2a720c10f3a5a9dd366f0d059ab`.
Planning branch baseline: `plan/offline-zero-cost-v2` at `72f546db2157f58a9ac1c6e901778d1f99067ced` before this documentation update. Always query actual HEAD for current SHA.

## Decisions approved (not completed product)
- **FINAL_PRODUCT_BLUEPRINT.md**: offline Windows repeat-use software, ZIP/TXT/combined TXT/folder/paste, source-safe static scanning, Korean local HTML/Markdown/print-to-PDF; no mandatory recurring server/API charges; optional human report and opt-in AI mode.
- **MVP_3DAY_ROADMAP.md**: 3 focused day MVP target -> blueprint gap filling -> broad security/reliability/performance/privacy/quality hardening -> verified Windows delivery and Kmong listing.
- Old 500-line commercial limit removed from **new software plan**; actual v1 CLI max 50 files / total 512KiB still in code. v2 1,200/12,000-line tests and >=200-file benchmark planned, not implemented.
- Approved to document roadmap on `main` via PR; separate release, paid usage, external upload, permissions, repository privacy and new private repo still require prior approval.

## Verified existing code and QA
- v1 code: Python CLI with file/folder/ZIP input, safe filtering/masking, limited Python AST rules, Gemini Interactions single-call optional cloud review and Markdown reporting; **does not yet include Windows v2 GUI or standalone binary**.
- TXT exists as generic input but not reliably routed to Python AST; combined multi-file TXT reconstruction not implemented.
- Historical local QA: 46 tests / 45 pass / 1 POSIX-only skip on Windows from source documentation. GitHub Actions for planning branch at `72f546d`: completed success; no new v2 source test in this task.
- Real Gemini output pilot: no confirmed successful report; historical RateLimitError, JSON-invalid and APIConnectionError. No fresh paid API call authorized.

## Work board
| Stage | State | Proof needed |
|---|---|---|
| Product vision / milestones / GitHub docs | APPROVED & DOCUMENTED | GitHub docs commit/PR and main HEAD verify |
| Stage 1 Day 1 offline core | NOT STARTED | Synthetic input + manifest + baseline regression |
| Stage 1 Day 2 findings/report | NOT STARTED | Offline Python scan → correct Korean HTML |
| Stage 1 Day 3 basic Windows UX | NOT STARTED | Real Windows run or honestly mark unverified |
| Stage 2 blueprint gaps | NOT STARTED | Feature-by-feature gap and test matrix |
| Stage 3 hardening | NOT STARTED | Windows, offline network, security, false positives |
| Stage 4 Kmong launch | NOT STARTED | Human buyer trial, packaging, support and listing approval |

## Recovery / branch strategy
- Source backup/recovery point: original `main` commit `8c72a6f`. Documentation change must not rewrite or delete original CLI.
- `plan/offline-zero-cost-v2`: docs planning branch, to be merged to main with PR after verification.
- Do not create future branches prematurely; on the first `ㄱ` implementation turn, create `feature/offline-core` from observed current main.
- No server/Vercel deployment; local product only. Production URL/production deployment SHA **not applicable**.
- Public repository: neither customer source nor secrets nor proprietary future commercial implementation modules.

## Next immediate task
Start Phase 1 Day 1: manifest/virtual source normalization for TXT ZIP folder/paste, source mapping, partial-scan handling, synthetic 1,200-line sample and tests. Use no Gemini API, paid providers or actual customer code.
