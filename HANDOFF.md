# CODE CHECKER — HANDOFF (10-point / 2026-10-26 KST)

> Official resume trigger: **[코드체커 깃헙 확인해]** or **ㄱ**. Check real GitHub SHA/PR/CI first. Read `CODE_CHECKER_RESUME.md` → this file → `STATUS.md` → `AGENTS.md` → `REQUIREMENTS.md` → `FINAL_PRODUCT_BLUEPRINT.md` → `MVP_3DAY_ROADMAP.md` → source/tests. Newest verified GitHub evidence overrides stale text.

## 1. Goal, product, confirmed technology
Owner-approved plan: 3 focused MVP days → gap review vs final blueprint → broad stability/privacy/security/performance hardening → Kmong after real-world checks. Principal product: repeat-use Windows offline code-risk checker; ZIP/TXT/multi-file TXT/folder/paste, Korean HTML/Markdown, PDF via browser Print, no required cloud/API/service subscription. Keep original Gemini CLI optional and unchanged. Existing Python 3.11+, Pydantic, safe `code_input.py` + `static_checks.py`, additive `offline_core.py`.

## 2. Implemented features, changes, rationale
- Day1 **main MERGED** PR #2; strict TXT reconstruction, source line mapping, 200-file bounded collector, Python AST/generic checks, coverage and partial states; no customer-code execution.
- Day2 **feature branch implemented and CI tested**: `offline_report.py` renders self-contained Korean HTML (CSP, no scripts, CSS inline) and escaped Markdown; deterministic masked-evidence verification, original TXT line references, duplicate removal, severity sort, partial status on forged/unverified findings, per-file coverage, explicit limitations.
- `write_report` uses completed temporary UTF-8 files and atomic hard links to avoid overwriting, rolls back on detected publish errors. CLI `python offline_report.py SOURCE --output-dir reports --name scan01` returns 0 complete, 3 partial, 2 blocked. Existing `reporting.py` untouched.
- Rationale: standalone offline reporter instead of modifying Gemini report path. No additional dependencies or paid calls.

## 3. Tests, commands, count and evidence
- Developer check: `python -m unittest discover -s tests -v`; functional: `python offline_report.py synthetic.txt --language python --output-dir reports --name scan01`.
- GitHub Actions for Day2 code SHA `7103c6768ac3dc7899856b38c23c86d2c39befed`: [16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40305312358), Linux log reports **76 unit tests PASS**. 15 OS/Python jobs + dependency-audit. Synthetic TXT/ZIP, partial/failure/unsupported, forged citation, HTML/XSS and Markdown escaping, duplicates, secrets masked, no-network mock, no-clobber/rollback covered.
- No local Git clone (container DNS failure). Green CI does not prove actual Windows GUI/EXE, browser print, Windows NTFS write or customer acceptance.

## 4. Done / in progress / pending / blocked
- Day1: DONE, merged and CI green.
- Day2: FEATURE IMPLEMENTED, validated code SHA 7103c67 green; [PR #3](https://github.com/hibi89/ai-code-checker/pull/3) opened as draft, docs and final merge/main CI pending at time of authoring.
- Day3: NOT STARTED. Windows input selection UI, launch report, optional PyInstaller candidate and clean-device verification.
- Final blueprint gap fill, security/product polish, Kmong: NOT STARTED. Sale prohibited until gates.

## 5. Failures, evidence, root cause, avoid repeating
- First Day2 full test run at `edf7ae7` reported 2/76 test failures: tests compared raw visible location string with intentionally escaped Markdown. Corrected to check HTML visible locations at `7103c67`. No code escaping weakened.
- Earlier Day1 two malformed synthetic fixture failures were fixed before merge. Do not repeat those fixture errors.
- Local direct GitHub clone hit DNS failure; use connected GitHub source and remote CI, not repeated blind clone attempts. Do not run customer project scripts or paid Gemini automatically.

## 6. Repository / branch / verified refs / paths
- `hibi89/ai-code-checker` public MIT: https://github.com/hibi89/ai-code-checker
- At Day2 branch creation: `main` `6fb334a8215d42babfd4748eb020657b148b27ba` (CI success). Work branch `feature/offline-report-ui`. Feature latest includes documentation after proven code SHA, so re-query SHA.
- Key new paths: `offline_report.py`, `tests/test_offline_report.py`, `DAY2_REPORT_GUIDE.md`, `STATUS.md`, this file. Original v1 base and history preserved, no force push.

## 7. Deployment, URL, environment, execution
- No Vercel or production website, **not applicable**. Python 3.11+ dependencies via `requirements.txt` for developer preview. Windows packaged GUI/EXE not implemented; cannot mark customer product complete.
- HTML locally generated and browser Print-to-PDF. Real browser rendering/printing and Windows clean install unverified.

## 8. Source, rollback, backup and secrets
- Restore path: current feature commits revert, or original main from `6fb334a`; original v1 preserved in Git history. Source loader never modifies input.
- Public MIT repository: never commit .env, real API keys, customer ZIP/code, AI raw responses, proprietary future paid packaging or identifiable reports. No automatic network, telemetry, external script/CDN/Google Fonts.
- Report may contain redacted source snippets and paths; customers must store/delete locally. Atomic pair commit cannot guarantee two-file transaction after an abrupt process kill; future hardening.

## 9. Next priorities, procedure, success and approvals
1. Verify latest `feature/offline-report-ui` PR #3 and its **final head CI** (not only old code SHA). If successful, mark ready, merge non-force into `main`, and verify new main SHA + CI.
2. Update `STATUS.md`, `HANDOFF.md` after merge with actual SHA; avoid obsolete “Day2 not started” note.
3. Next user's **ㄱ**: Day3 fresh `feature/windows-portable` from real current main. Implement minimum Windows-friendly local UI and package candidate. No claim of working EXE without Windows clean-device E2E.
4. Preserve source and APIs; offline, no account/paid model calls. Permissions/visibility change, private repo, customer upload, selling or paying costs still need explicit authorization.

## 10. Timestamp, evidence scope, documentation baseline
- Written **2026-10-26 KST**, exact clock minute not claimed. Current Day2 docs based on verified code SHA `7103c67`, initial Day2 main base `6fb334a`, PR #3. The docs commit SHA self-reference is intentionally omitted; **always fetch current remote HEAD**.
- Verification: 16/16 CI and 76 unit tests on synthetic fixtures only. Browser and Windows product tests remain UNVERIFIED. The product remains PARTIAL COMPLETE despite report module code success.
