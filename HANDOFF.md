# Code Checker Handoff (Planning Branch)

Updated: 2026-10-26 KST (time not recorded)
Read order on resume: HANDOFF.md -> STATUS.md -> AGENTS.md -> REQUIREMENTS.md -> ARCHITECTURE_V2.md -> PRODUCT_STRATEGY_V2.md -> current source.

## 1. Goal / confirmed / tech
Existing product: Python 3.11+, google-genai >=2.18.1,<3, Pydantic 2, Interactions API, local CLI; originally seller-run Markdown report service. Proposed v2: reusable offline Windows code-risk checker, local HTML/PDF printing, optional human report, **not yet owner-approved for implementation**.

## 2. Completed and decisions
Current baseline inspected, broad CI results checked, shortcomings assessed. Chosen proposal: reuse code, don't rewrite from scratch; default offline, no mandatory cloud. Removed 500-line product cap in proposal only; distinguish total traversal from analyzed coverage. Existing MIT license/public nature requires honest paid differentiation.

## 3. Tests and verification
Existing baseline local evidence: 46 tests (45 pass, 1 POSIX-only skip on Windows) as recorded in existing docs. GitHub Actions 16/16 successful on baseline. No new v2 product tests, app builds or offline network tests. Actual Gemini successful report still 0 in records; no API calls performed for this proposal.

## 4. Complete / active / pending / blocked
Complete planning and GitHub documentation branch; waiting owner decision on implementation, pricing, public/private packaging; v2 GUI/report adapters not coded. Never claim docs equal product.

## 5. Errors / root evidence / failed attempts / stop conditions
Previous: API 503, rate limits, JSON-invalid and connection errors; causes vary, no proven fix to live generation. Never repeatedly retry uncertain requests, never leak .env or originals. Offline redesign avoids default API dependency, but may reduce semantic analysis quality. Test with vulnerable/safe fixtures before promoting.

## 6. Repo / branch / SHA / paths
Public: https://github.com/hibi89/ai-code-checker
Default main baseline SHA: 8c72a6f3bc30f2a720c10f3a5a9dd366f0d059ab
Plan branch: plan/offline-zero-cost-v2; resulting commit to be verified after writing.
Baseline source: main.py, reviewer.py, code_input.py, static_checks.py, reporting.py, review_models.py, tests/.
Plan docs: AGENTS.md, REQUIREMENTS.md, ARCHITECTURE_V2.md, PRODUCT_STRATEGY_V2.md, STATUS.md, HANDOFF.md.

## 7. Production / commands / environment
Production URL/Vercel: NOT APPLICABLE for current local CLI. Existing offline check: `python -m unittest discover -s tests -v`; `python main.py assets/pilot-safe.zip --dry-run`. Do NOT run real AI without explicit authorization. No Windows portable v2 binary is available.

## 8. Originals / backups / secrets / no-touch
Existing main SHA is recovery point, main files unchanged. Historical PRODUCT_PLAN_KMONG.md is valid historical scope; don't replace without approved change. Never store customer code, API keys, .env, paid responses, private program modules or secrets in public repo.

## 9. Next priorities, completion, approvals
(1) Owner approves or revises report-versus-software model and proposed prices; (2) clarify open MIT core vs proprietary packaging in private repo (explicit approval required); (3) implement offline scan manifest, code hygiene and safe report gate; (4) run Python synthetic vulnerable+safe fixtures; (5) Windows packaged clean-machine offline QA; (6) create actual listing and verify platform delivery and refund expectations. Any private repository, release, product-code modification, cloud upload or paid signing requires approval.

## 10. Update metadata / evidence limits
Date: 2026-10-26 KST (time not recorded). Verified baseline main Git SHA, repo public state and Actions 16 checks; no fresh model run, customer shipment, Windows EXE, website or human quality review. Document baseline commit SHA is 8c72a6f3bc30f2a720c10f3a5a9dd366f0d059ab; planning commit SHA must be taken from GitHub after this document is committed (self-referential SHA intentionally not embedded). On resume compare actual branch tip, main tip and documents.
