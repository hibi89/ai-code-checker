# CODE CHECKER — STATUS

Updated: 2026-10-26 KST. Product phase: MVP Day 1 merged; Windows product not yet available.
Main merge SHA: 473beb5003aec71eac44861992d2a34bc48dd27f. Day 1 PR: https://github.com/hibi89/ai-code-checker/pull/2 (merged).
Repository: https://github.com/hibi89/ai-code-checker (Public/MIT).

## Approved strategy
3-focused-day MVP -> compare implementation with FINAL_PRODUCT_BLUEPRINT.md and fill gaps -> security, stability and performance hardening -> Kmong after actual customer-use verification.
Primary product: offline Windows checker with no mandatory API, hosting, subscription, account or network transfer. No 500-line licensing cap; tested resource limits still apply.

## Day 1 implemented
- offline_core.py provides scan_path / scan_text over preserved code_input.py and static_checks.py; existing main.py/Gemini CLI unchanged.
- Single TXT with chosen Python/JS/TS suffix; Python AST runs only on Python sources; other languages generic-only and explicitly limited.
- Strict multi-file TXT section headers, path collision/traversal checks, origin-file and original-line source mapping.
- ZIP, folder, and file input reuse bounded readers, secret redaction and dangerous path protections; neither original code nor dependencies are executed.
- OfflineScan tracks analyzed, limited, failed, excluded, unsupported and overall complete/partial. Metadata-only CLI JSON; partial exit 3, blocked exit 2.
- Developer command: python offline_core.py project.zip or python offline_core.py file.txt --language python.

## Verification
- CI of feature 30b5b1761d552aa52957b74431381d4e01aafd1c: 16/16 successful jobs. Linux run: 63 tests. Main merge 473beb5003aec71eac44861992d2a34bc48dd27f: 16/16 successful jobs.
- Synthesized 1,200-line TXT, 12-file ZIP, 200-file / 12,000-line folder, unsafe ZIP, malformed markers, source lines, secret exclusion and no execution tested.
- First CI 118ff8d failed due invalid Python test fixture. A later CI 43e4583 failed due escaped newline fixture. Both were fixed and green at 30b5b17; no need to repeat either failed method.
- The container could not clone GitHub because DNS was unavailable. CI logs establish tests, not independent local Windows execution.
- Real Windows executable, GUI, HTML/PDF report, full network monitoring, commercial quality and customer delivery: not implemented or unverified. No paid API requests made.

## Work board
| Stage | Status |
|---|---|
| Day1 safe offline inputs, source map, coverage | MERGED and GitHub CI passed |
| Day2 Korean HTML/Markdown report and validation | NOT STARTED |
| Day3 Windows GUI and portable candidate | NOT STARTED |
| Blueprint gap filling | NOT STARTED |
| Final hardening and commercial release | NOT STARTED |

## Recovery / next task
Last stable pre-Day1 main: 4c1c10069c3ac20a3342648e3877f1aa1b5fca5f; original v1: 8c72a6f3bc30f2a720c10f3a5a9dd366f0d059ab. No force push.
Next user ㄱ: inspect latest main SHA, HANDOFF, source, create feature/offline-report-ui from main; build Korean offline HTML+Markdown reporting, evidence/location consistency checks, no silent success, synthetic tests and CI.
No Vercel or production URL: local-only software. Do not upload customer source, API keys or proprietary material to public GitHub; external API, paid costs, security settings, or public sale need approval.

## 채팅 이전 및 자동 재개 포인트 (2026-10-26 KST)

- 공식 사용 문구: **`[코드체커 깃헙 확인해]`**. 자세한 절차: [CODE_CHECKER_RESUME.md](CODE_CHECKER_RESUME.md).
- 최종 확인된 기능 병합 상태: `main` `c1179f8c73725f82b15d8be8310506f9e04d1658`, [Actions 16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40300811155). **이후 문서 커밋에 따른 새 HEAD는 매번 GitHub에서 재확인.**
- 현재 개발 단위: Day 1 완료. **Day 2는 아직 시작하지 않음.** Day 2 목표는 안전한 한국어 오프라인 HTML·Markdown 리포트 생성·실제 근거 검증·누락/부분 검사 표시·회귀 테스트.
- 구현 재개 시 `main` 최신 SHA로부터 `feature/offline-report-ui` 브랜치 생성, GitHub PR·CI 검증 후 병합. 이 인수인계 작업은 **문서 변경만** 포함, 새 제품 기능 검증은 없음.
- 고객 Windows GUI/EXE, 실행파일 서명·경고 확인, 상품 등록은 여전히 미완료. Gemini 사용량/연동 문제는 오프라인 핵심 개발의 선행 조건이 아님.
