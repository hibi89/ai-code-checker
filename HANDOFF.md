# CODE CHECKER — HANDOFF (10 required items)

Updated: 2026-10-26 KST (exact clock time not captured). Read: HANDOFF.md -> STATUS.md -> AGENTS.md -> REQUIREMENTS.md -> FINAL_PRODUCT_BLUEPRINT.md -> MVP_3DAY_ROADMAP.md -> INPUT_SPEC_V2.md -> source/tests.

## 1. Goal / confirmed requirements / technology
Approved product: offline-first Windows code-risk checker (TXT, ZIP, delimited multi-file TXT, folders, paste), no required AI API/server fees, repeated local use, Korean HTML/Markdown report and browser PDF print. 3 focused days MVP target, then blueprint gap completion, then stability/security hardening, then Kmong. Existing Python >=3.11 CLI and code_input/static_checks reused. Not a comprehensive security certificate.

## 2. Completed and rationale
Day1 developer-preview `offline_core.py` and synthetic `tests/test_offline_core.py` implemented on `feature/offline-core` from main `4c1c100`. Design chose separate local facade rather than rewriting working Gemini CLI; no API retry, secrets or customer code. SourceOrigin maps virtual file line to original TXT; FileCoverage exposes unexamined/limited files.

## 3. Tests / exact commands / success/failure / unverified
`python -m unittest discover -s tests -v` plus `python -m py_compile offline_core.py` and `python offline_core.py assets/pilot-safe.zip` (offline CLI smoke). GitHub workflow executes unit tests and old CLI dry-run; new module is imported by tests.
First feature SHA `118ff8da69ab3e00a18b0420dbd560040195d721`: Linux test run 61/62 PASS, 1 FAIL due invalid synthetic Python escaped-header fixture. Corrected by enclosing marker within a Python string; SHA `6aea33852d40e296d44980a37cb9c9de0c994f9a` had **16/16 GitHub Actions jobs success** (15 test jobs + 1 audit). Additional direct TXT-path test and SyntaxWarning cleanup added with this documentation commit; check latest CI before merger.
No container checkout: network DNS failed. Actual customer Windows EXE, GUI, PDF, complete source accuracy, Windows SmartScreen, privacy traffic monitor remain unverified. No real Gemini generated report historically.

## 4. Complete / active / pending / blocked
Day1 core complete as an implemented prototype with existing CI proof, awaiting current head CI+PR merge. Day2 report, Day3 GUI, design-gap phase, hardening and listing pending. No production release. No blocker needing user local action for documentation/testing.

## 5. Errors / cause / attempts / prohibited repeats / alternatives
First CI failed on test expectation not production scan; change was meaningful and verified in next CI. Prior Gemini 503, rate limit, invalid JSON, APIConnectionError were not a proven live fix; do not auto-retry. Do not run API when developing offline mode. Running untrusted customer code, installing its dependencies, or leaking raw code is prohibited.

## 6. Repo / branch / SHA / principal paths
Public MIT: https://github.com/hibi89/ai-code-checker, working branch `feature/offline-core`, parent main `4c1c10069c3ac20a3342648e3877f1aa1b5fca5f`. Previous pristine v1 main `8c72a6f`. Current feature head MUST be fetched after this document commit; do not assume it equals `6aea338`. Key files: offline_core.py, tests/test_offline_core.py, code_input.py, static_checks.py; docs in main root.

## 7. Production / execution / environment
No Vercel or live URL, local CLI only; deployment status **N/A**, GUI **NOT IMPLEMENTED**. Standalone command `python offline_core.py file.txt --language python`, no account/API, metadata summary JSON. Windows Python interpreter required for this preview; portable package is future work.

## 8. Originals / backup / secrets / protected paths
Original v1 source preserved by additive module; recovery main before work `4c1c100`, old v1 `8c72a6f`. No real customer files, .env/API keys, raw API/model text, proprietary non-public code stored. Public GitHub MIT remains; private code requires explicit approval.

## 9. Next work priorities / acceptance / approvals
Verify current feature CI and merge PR safely to main; next `ㄱ` create `feature/offline-report-ui` on updated main. Day2: file/path/line/evidence verification, deduplicate findings, Korean self-contained HTML+Markdown, explicit partial/cancel states, no source/code execution, tests synthetic safe vs vulnerable. Day3 GUI/portable only after report. External API/cost, new private repo, public release, permissions or live customer data require prior approval.

## 10. Update KST / evidence scope / doc basis
Date 2026-10-26 KST. Current docs commit SHA is intentionally not embedded; always inspect GitHub current head, PR CI, main SHA. Evidence includes GitHub workflow success at `6aea338`; final docs/test commit CI must be separately checked. No local Windows/E2E hardware evidence or actual customer use.
