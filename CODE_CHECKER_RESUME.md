# 코드체커 — 새 채팅 자동 작업 재개 (2026-10-26 KST)

> 공식 트리거: **[코드체커 깃헙 확인해]**. 축약 신호 **ㄱ**도 이미 승인된 다음 작업 진행을 뜻합니다.

## 자동 복원 순서

1. GitHub [`hibi89/ai-code-checker`](https://github.com/hibi89/ai-code-checker)에서 **실제 `main` SHA, 열린 PR, 브랜치, 최신 CI** 확인. 기록상 SHA는 과거 기준일 수 있습니다.
2. `HANDOFF.md` → `STATUS.md` → `AGENTS.md` → `REQUIREMENTS.md` → `FINAL_PRODUCT_BLUEPRINT.md` → `MVP_3DAY_ROADMAP.md` → `INPUT_SPEC_V2.md` → 실제 코드/테스트 순으로 읽습니다.
3. 미완료 승인 작업부터 진행하고, 새로운 비용·API 호출·민감 데이터 전송·저장소 권한/공개 변경·판매 공개만 별도 사전 승인받습니다. 이미 확정된 방향을 되묻지 않습니다.

## 최신 작업 맥락

- 사업 방향: **3일 오프라인 Windows MVP → 최종 설계도와 부족 기능 비교/보강 → 보안·안정성·성능 심층 강화 → 크몽 상품화**. Windows 프로그램 일회성 구매 가설 49,000원, 설치·검수 99,000원, 단건 리포트 40,000원(미검증 가격).
- 오프라인 기본 제품은 TXT·ZIP·폴더·붙여넣기(다중 구분자 TXT 포함)를 정적 규칙으로 검사하고 한국어 HTML·Markdown 보고서를 생성합니다. AI API 필요 없음. 기존 Gemini CLI는 별도 보존.
- Day1: 오프라인 입력·정적 검사 코어 [PR #2](https://github.com/hibi89/ai-code-checker/pull/2) main 병합. 합성 1,200줄 TXT, 12파일 ZIP, 200파일 12,000줄 등 CI PASS.
- Day2: `feature/offline-report-ui`에서 `offline_report.py` + `tests/test_offline_report.py` + `DAY2_REPORT_GUIDE.md` 추가. 독립 HTML/CSP, Markdown, 출처·줄·발췌 재검증, partial 검증 실패, 중복 제거, 원자적 no-clobber 파일 출력. 기존 AI 보고서 변경 없음.
- 검증된 Day2 코드 SHA `7103c6768ac3dc7899856b38c23c86d2c39befed`, [Actions 16/16 PASS / 전체 76 unittest PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40305312358). 이 SHA 이후 문서가 추가됐으므로 **최종 브랜치 HEAD 및 CI 재검증이 필수**.
- 작업 PR: [#3 병합](https://github.com/hibi89/ai-code-checker/pull/3). 병합 `main` SHA `7a5e78d8dca2bb678636b71be9d278fe2d137df2`. 이후 문서 SHA는 최신 GitHub 조회 필요.
- 아직 미구현/미검증: Windows GUI·EXE·고객 PC 실행·실제 PDF 인쇄·네트워크 관찰·상업 출시·비-Python 전문 분석. **코드 모듈 CI 성공을 최종 상품 완성이라고 주장하지 않습니다.**

## 다음 실제 작업

1. **PR #3가 아직 열려 있으면:** 최종 HEAD·Actions 상태 확인 → 오류 있으면 한 번 진단·수정 → CI PASS면 draft 해제·병합 → 병합 SHA 및 main CI 확인 → STATUS/HANDOFF 갱신.
2. **PR #3가 병합되어 있으면:** 최신 main에서 `feature/windows-portable` 신규 브랜치 생성 후 Day3 MVP 진행. GUI에서 TXT/ZIP/폴더/붙여넣기 및 언어 선택, 검사 버튼, HTML 열기 지원; 실패·partial 상태를 표시하고 합성 테스트 검증. PyInstaller는 후보이며 **clean Windows 검증 전 EXE 완성 아님**.
3. 완료한 커밋과 실제 CI 검증만 보고합니다. 현시점 합성 테스트 이외 Windows 고객 서비스는 미검증입니다.

## 안전·출고 제한

- GitHub Public/MIT. 민감한 유료 독점 모듈·실고객 ZIP/코드/키/토큰·원본 Gemini 응답 등은 절대 commit 금지. 필요할 경우 별도 비공개 저장소 사용자 승인.
- 입력 코드 실행, 의존성 설치, 플러그인 실행, 숨은 네트워크 요청·텔레메트리 없음. 외부 Gemini 호출 및 비용은 명시적 승인 전 금지.
- 보고서 complete는 검사 정책에 따른 입력 처리 완료이고 취약점 부재 보장이 아님. JS/TS는 제한적 패턴 검사. 브라우저 PDF 경로는 아직 실기기 검증 필요.
- 수정은 feature branch → 테스트/CI → PR → main → STATUS/HANDOFF 최신화. force push, 무의미한 빈 커밋 금지.
