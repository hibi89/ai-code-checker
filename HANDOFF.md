# CODE CHECKER — HANDOFF (10-point)

Updated 2026-10-26 KST; actual main merge SHA 473beb5003aec71eac44861992d2a34bc48dd27f. Refresh current branch SHA before any work.
Read HANDOFF.md -> STATUS.md -> AGENTS.md -> REQUIREMENTS.md -> FINAL_PRODUCT_BLUEPRINT.md -> MVP_3DAY_ROADMAP.md -> INPUT_SPEC_V2.md -> actual code/tests.

## 1. Goal / confirmed requirements / technology
Approved Windows local offline code-risk checker, TXT/ZIP/combined TXT/folder/paste, Korean HTML/Markdown and browser Print-to-PDF, optional human report. No required API/server/account or recurring fee. Delivery: 3-day MVP -> blueprint gap fill -> broad hardening -> Kmong. Existing Python 3.11+ CLI and Pydantic-based models remain, optional Gemini legacy path separate.

## 2. Completed functionality and decisions
Day1 additive offline_core.py (SourceOrigin, FileCoverage, OfflineScan, scan_path, scan_text), metadata-only developer CLI, reused code_input.py safety and static_checks.py Python AST. Delimited multi-file TXT validates markers/paths and preserves source line mappings; single TXT requires language for AST. Public MIT existing code retained intact; no restart from scratch. PR #2 merged.

## 3. Tests, commands, count, evidence
Offline check: python -m unittest discover -s tests -v; python offline_core.py assets/pilot-safe.zip; python offline_core.py sample.txt --language python. GitHub Actions feature 30b5b17: 16/16 jobs success, Linux test log 63 tests; main merged commit 473beb5003aec71eac44861992d2a34bc48dd27f: 16/16 jobs success. Cases: 1,200-line TXT, 12-file ZIP, 200-file 12,000-line synthetic project, safe/unsafe paths, provenance, masked secrets and input non-execution. No live customer data, Gemini request, Windows binary or external service tests.

## 4. Completed / active / pending / blocked
Day1 core DONE as an integrated developer preview. Day2 report not started; Day3 Windows GUI not started; blueprint gaps, full security hardening and Kmong delivery pending. Not a finished application, no customer sale.

## 5. Errors / root causes / attempted methods / avoid / alternatives
Initial 118ff8d failed 1 of 62 tests: escaped header was inserted as invalid Python source; fix used triple quoted valid Python. Subsequent 43e4583 failed single added test: fixture contained literal backslash-n instead of newlines; corrected in 30b5b17. No unresolved regression in latest main CI. Historical Gemini 503, 429, JSON-invalid, connection errors are not relevant to offline flow; do not rerun unapproved paid APIs. Do not run customer-provided code or config/plugins.

## 6. GitHub repo / branches / SHA / paths
Public repo https://github.com/hibi89/ai-code-checker ; main SHA 473beb5003aec71eac44861992d2a34bc48dd27f, initial Day1 base 4c1c10069c3ac20a3342648e3877f1aa1b5fca5f, original 8c72a6f. Day1 branch feature/offline-core; next feature/offline-report-ui created only when starting Day2. Files: offline_core.py, tests/test_offline_core.py, code_input.py, static_checks.py, review_models.py, README.md, STATUS.md, HANDOFF.md. This docs commit SHA must be fetched from GitHub after updating (self reference omitted).

## 7. Production URL / Vercel / environment / commands
No Vercel, web deployment or production service, status NOT APPLICABLE. Current developer tool needs Python and installed runtime dependencies; Windows packaged GUI unimplemented. Commands above; report generator is planned for Day2.

## 8. Originals / backups / secrets and forbidden edits
Original v1 remains in history, source untouched by v2 Day1. Never publish .env, customer code, real API keys, provider output or confidential paid packaging modules to public MIT repo. Local customer source must remain unchanged and offline; future private repository would need separate user approval.

## 9. Next priority, procedure, acceptance, approval
On user ㄱ: read latest HEAD and files; create feature/offline-report-ui from main; implement Day2 Korean self-contained HTML and Markdown report on OfflineScan, deduplicate findings and verify file/line/excerpt; show partial/unsupported/failed, escape HTML/Markdown, atomic no-overwrite output and synthetic safe-vulnerable regression. Merge PR only after CI. Day3 follows with basic Windows GUI and candidate packager. Extra cost, real data external upload, private repo, permissions changes or selling require consent.

## 10. Update time / evidence limitations / document base
2026-10-26 KST (exact clock time not recorded). Verified main 473beb5003aec71eac44861992d2a34bc48dd27f and GitHub Actions 16/16. Current documentation commit later than main SHA above, so fetch actual HEAD after this update. GitHub CI is not independent clean Windows GUI, privacy traffic, or real customer use verification.

## 11. 새 채팅 원문 트리거 (2026-10-26 KST, 최신)

**사용자 입력: `[코드체커 깃헙 확인해]`.** 이 메시지는 'GitHub를 확인하고 같은 총괄 자격으로 다음 승인된 작업을 시작하라'는 뜻이다. 설계 재논의/추가 질문을 하지 말고 [CODE_CHECKER_RESUME.md](CODE_CHECKER_RESUME.md)를 읽은 뒤 실제 저장소의 SHA·열린 PR·CI를 먼저 확인한다. **최종 검증된 이전 `main`은 `c1179f8c73725f82b15d8be8310506f9e04d1658`, [16/16 CI 성공](https://github.com/hibi89/ai-code-checker/actions/runs/40300811155)**. 이 후 문서 커밋으로 HEAD가 바뀌므로 반드시 최신값 사용. Day 1 병합 완료, **다음 작업은 Day 2 `feature/offline-report-ui`에서 한국어 HTML·Markdown 오프라인 리포트 + 근거 검증 + 합성 회귀 테스트**. 그다음 Day 3 Windows GUI. 외부 API 호출·유료 작업·고객 코드 전송은 별도 승인 필요.
