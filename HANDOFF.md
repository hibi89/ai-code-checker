# CODE CHECKER — HANDOFF (10-point transfer)

Updated: 2026-10-26 KST (clock time not captured); code state verified against GitHub before documentation update.
Resume order: HANDOFF.md -> STATUS.md -> AGENTS.md -> REQUIREMENTS.md -> FINAL_PRODUCT_BLUEPRINT.md -> MVP_3DAY_ROADMAP.md -> INPUT_SPEC_V2.md -> source/test.

## 1. Goal / confirmed requirements / technology
Final target **approved by owner 2026-10-26**: customer-run offline Windows code-risk checker (no mandatory API/hosting or subscription), TXT/ZIP/combined TXT/folder/paste, Korean HTML/Markdown and browser Print-to-PDF. Optional separate human review; cloud Gemini BYOK only explicit opt-in. Existing tech: Python CLI 3.11+, Pydantic v2, google-genai for historical optional cloud function; new UI/packaging proposed stdlib tkinter + PyInstaller subject to validation.

## 2. Completed / changes / decisions
Baseline CLI and input security are reusable, no restart from scratch. Original report-only product becomes secondary. Vision doc FINAL_PRODUCT_BLUEPRINT.md; sequencing doc MVP_3DAY_ROADMAP.md. Workflow **3 focused days MVP → gap analysis → hardening → Kmong**. Avoid false claims: no stand-alone Windows v2 binary exists. Existing MIT public source cannot be made proprietary retroactively; separate commercial IP needs prior approval.

## 3. Tests / execution / PASS-FAIL-UNVERIFIED
Historical baseline local tests 46 (45 pass, 1 POSIX-only skip on Windows per documentation). Planning branch CI at `72f546d` verified completed/success on 2026-10-26. No new v2 product test executed this documentation task; no actual TXT multi-file reconstruction test or Windows GUI test. Existing commands: `python -m unittest discover -s tests -v`; `python main.py assets/pilot-vulnerable.zip --dry-run`. Real Gemini success: 0 documented. Do not infer success from CI green for v2.

## 4. Status / stopping point
Design and staged workflow owner-approved/documented. Stage1 Day1 **NOT STARTED**. Stage2/3/4 not started. New docs committed and PR/main merge must be verified in latest GitHub; don't invent success. No customer delivery.

## 5. Errors / evidence / attempts / no-repeat / alternatives
Old Gemini API attempts: 503, rate limit, invalid JSON, connection errors; none proves live successful output. Stop repeating API calls: v2 default offline entirely. Legacy TXT accepted but `.txt` does not currently trigger Python AST and delimited multi-file TXT is NOT reconstructed. Safe offline local parsing is next. Only synthetic files, with line/source maps verified. When errors recur without progress stop after 2 materially distinct attempts and pivot.

## 6. Repository / branches / SHA / key paths
https://github.com/hibi89/ai-code-checker, Public MIT. Original untouched baseline main SHA `8c72a6f3bc30f2a720c10f3a5a9dd366f0d059ab`. Planning branch before docs update SHA `72f546db2157f58a9ac1c6e901778d1f99067ced`. Must query final merged main SHA. Future branches only as actually needed: `feature/offline-core`, `feature/offline-report-ui`, `feature/windows-portable`, `hardening/prelaunch`. Source: main.py, code_input.py, static_checks.py, reviewer.py, reporting.py, review_models.py, tests/. Docs: AGENTS.md, REQUIREMENTS.md, FINAL_PRODUCT_BLUEPRINT.md, MVP_3DAY_ROADMAP.md, INPUT_SPEC_V2.md, STATUS.md.

## 7. Production URL / deployments / run env
No website, Vercel or deployed production: **NOT APPLICABLE**. Existing CLI Python 3.11+; Windows binary not created. No production app SHA; Git commit SHA only. No remote calls in new offline mode.

## 8. Original locations / backups / auth / no-touch
Original Git SHA `8c72a6f` remains recoverable. Public GitHub should never receive real customer source, proprietary packaging secrets, `.env`, API keys, raw model outputs, or customer reports. Keep code input read-only and client report local. No real clients or cloud transmission approved.

## 9. Next tasks / acceptance / approvals
Next `ㄱ`: confirm main/docs SHA; create `feature/offline-core` on latest main; implement Day1 input normalization, manifest, safe TXT/ZIP parsing and source map plus synthetic tests; update STATUS/HANDOFF. Day2 findings and HTML; Day3 Windows basic UI and candidate packaging; later compare final blueprint and harden before sale. External API calls, costs, public listing, repository visibility change, private repo, security/permission changes still need prior explicit approval.

## 10. Update timestamp / evidence / doc commit basis
2026-10-26 KST. Verified source baseline and planning branch status during this task. No real Windows/UI/executable/function success is claimed. This file purposely does not claim its own current SHA: resolve `main` HEAD from GitHub and compare on each resume. Planning doc merge commit is the document base once GitHub reports merged and SHA.
