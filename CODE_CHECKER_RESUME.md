# 코드체커 — 새 채팅 자동 작업 재개 안내

> **공식 재개 호출 문구: `[코드체커 깃헙 확인해]`**
>
> 사용자가 새 채팅에서 위 문구 하나만 보내면 이 저장소 `hibi89/ai-code-checker`의 총괄 개발자로서 마지막 완료 작업부터 다음 승인된 개발 단위를 **바로 실행**한다. 같은 정보를 다시 질문하거나 새 설계부터 만들거나 단순 요약만 하고 종료하지 않는다. GitHub 접근 불가 등 실제 차단이 있으면 사실과 실패 원인만 명시한다.

## 1. 처음 읽는 순서

1. GitHub 저장소 `https://github.com/hibi89/ai-code-checker`의 **현재 `main` SHA·최신 브랜치·열린 PR·최신 GitHub Actions 상태** 확인. 아래 기록된 SHA보다 실제 GitHub 상태가 우선한다.
2. `CODE_CHECKER_RESUME.md` → `HANDOFF.md` → `STATUS.md` → `AGENTS.md`.
3. `FINAL_PRODUCT_BLUEPRINT.md` → `MVP_3DAY_ROADMAP.md` → `REQUIREMENTS.md` → `INPUT_SPEC_V2.md` → `ARCHITECTURE_V2.md` → `PRODUCT_STRATEGY_V2.md`.
4. 코드·테스트 확인: `offline_core.py`, `code_input.py`, `static_checks.py`, `review_models.py`, `reporting.py`, `tests/test_offline_core.py`, 기타 기존 테스트. `main.py`/`reviewer.py`는 기존 Gemini 기반 v1 CLI로서 보존.
5. 실제 증거와 완료 상태가 문서 내용보다 우선. 오래된 문구가 있으면 업데이트하고 실행한다.

## 2. 실제 마지막 검증 시점 (2026-10-26 18:51 KST)

- 저장소: `hibi89/ai-code-checker` / Public / MIT.
- **마지막 검증된 `main` SHA: `c1179f8c73725f82b15d8be8310506f9e04d1658`**. 이 문서를 추가하면 SHA가 바뀌므로 다음 채팅에서 반드시 재조회.
- Day 1 기능 병합 PR: [#2](https://github.com/hibi89/ai-code-checker/pull/2), 병합 커밋 `473beb5003aec71eac44861992d2a34bc48dd27f`.
- [병합 후 최신 CI](https://github.com/hibi89/ai-code-checker/actions/runs/40300811155): 15개 OS/Python 테스트 작업 + 1개 의존성 검사 **16/16 성공**. 이전 단위 테스트 실행 로그 Linux 기준 63개 테스트. 이 수치는 고객 PC 실기 검증 결과가 아니다.
- 최신 사용자 지시: **3일 MVP → 최종 설계도 대비 부족 기능 확장 → 최종 보안·안정성·성능 다각 보강 → 크몽 상품화**.
- 사용자 메시지 `ㄱ`도 다음 승인된 작업 진행 신호다. 자동 Gemini 호출, 추가 비용, 저장소 비공개 전환, 외부 고객 코드 전송 승인으로 확대 해석하지 않는다.

## 3. 사업·기술 핵심 목표

- **최종 판매 대상:** 크몽에서 한 번 구매해 반복 사용하는 **Windows 오프라인 코드 위험 진단 프로그램**. 단건 리포트 대행은 별도 보조 서비스. 일회성 가격 가설은 소프트웨어 49,000원, 설치+검수 99,000원, 단건 리포트 40,000원; 실판매 수요·정산 미검증.
- **구매자/판매자 기본 실행 API 비용 0원 목표**, 로그인·구독·클라우드 서버·필수 Gemini 호출 없음. 인건비, 플랫폼 수수료, 기기·전력·코드 서명까지 0원이라는 뜻 아님.
- **입력:** ZIP, 단일 TXT, 다중 파일 표시 TXT (`===== FILE: src/main.py =====`), 폴더, 코드 붙여넣기. 원래 500줄 판매 제한 폐기. 입력별 지원 범위·제외·실패를 표시하며 만능 대용량/취약점 탐지를 보증하지 않음.
- **출력:** 파일·줄·근거·위험 후보·수정 방향·한계가 구분된 **로컬 한국어 HTML / Markdown**. PDF는 처음에 브라우저 인쇄 기능으로 저장.
- **품질 약속:** 코드 실행/자동 수정/의존성 설치 없음. 일부만 검사했다면 complete 판정 금지. 정적 규칙과 AI 판단은 다른 깊이의 검사.

## 4. 완료된 Day 1 (코드 구현 + CI 확인)

- `offline_core.py`: `scan_path()`, `scan_text()`, `OfflineScan`, `SourceOrigin`, `FileCoverage`; 기존 `code_input.py`/ `static_checks.py`를 재사용.
- 1,200줄 Python TXT 언어 선택→가상 Python 파일·정확한 원본 줄 매핑. 엄격한 다중 파일 TXT 분리/중복·경로 탈출 거부. 기존 안전한 ZIP/폴더 로딩.
- 상태 `analyzed / limited / failed / excluded / unsupported`, 종합 `complete / partial`. 안전하지 않은 입력은 `InputError`로 거부(개발용 CLI 종료 코드 2).
- 기존 v1 Gemini CLI 코드는 **변경하지 않음**. 오프라인 코어는 외부 AI를 호출하지 않음.
- 합성 12파일 ZIP, 200파일·12,000줄, 비밀정보 제외, 잘못된 헤더, 깨진 Python, 원본 불변성 등 17개 새 테스트 포함; 전체 Linux 63개 테스트, CI 16/16 성공.
- **미완료:** 고객용 HTML/Markdown 오프라인 보고서, Windows GUI/EXE, 클린 Windows 기기 테스트, 실제 품질 평가 및 크몽 등록.

## 5. 가장 먼저 할 실제 작업 — Day 2 (추가 질문 없이)

현재 `main`에 앞선 동일 작업이 없다면:

1. 새 `feature/offline-report-ui` 브랜치를 **현재 최신 `main`에서** 만든다. 임의로 Day 1부터 반복하지 않는다.
2. `OfflineScan`의 `bundle`, `coverage`, `findings`, `status`, `counts`, `origin_for`를 이용해 별도 오프라인 보고서 모듈 개발. 현재 `reporting.py`의 기존 Gemini Markdown 기능은 가능한 재사용하되 v1 계약을 깨지 않는다.
3. `CodeFinding`의 파일·줄·발췌 인용을 원본 및 마스킹된 `CodeBundle`과 대조. 불일치/미지원/구문 오류/제외 구간을 검증 실패·부분 검사로 명확히 표시. 출처 및 신뢰도에 대한 과장 금지.
4. 중복 발견 정규화, 우선순위별 정렬, 한국어 문제 후보·영향·수정 권고 표시.
5. 외부 스크립트·CDN·폰트·네트워크가 없는 독립 HTML 문서(HTML 이스케이프, XSS 방어)와 Markdown. 사용자가 로컬 브라우저에서 PDF로 저장 가능.
6. 결과 쓰기는 안전한 경로/명시적 파일명/덮어쓰기 방지, 부분 쓰기 방지(원자적 저장); 파일에 민감한 코드 원문이 포함될 수 있으므로 숨은 로깅 금지.
7. **합성 안전/취약/HTML 주입/경로·줄 불일치/중복/부분 검사/보고서 충돌** 테스트 추가. 기존 회귀 전체 실행·실제 GitHub Actions CI 확인. 성공 결과만 완료 처리.
8. `STATUS.md`와 `HANDOFF.md` 최신화, PR에서 코드 차이와 테스트 확인 후 `main`에 병합. Day 3 후보 GUI로 다음 작업 이동.

## 6. 이후 단계 — 순서 변경 금지

- **Day 3:** 간단한 Windows 입력 UI, 검사 버튼, HTML 결과 열기, 포터블 EXE 후보. PyInstaller 가능하나 **실제 Windows 실행 테스트가 없으면 배포 완료 아님**.
- **Phase 2:** [최종 설계도](FINAL_PRODUCT_BLUEPRINT.md) 대조/부족 기능 채우기. JS/TS 실제 분석 능력, 검사 규모·정확도 실측.
- **Phase 3:** ZIP 보안, 경로 문제, 메모리·성능, 라이선스, 정적 규칙 오탐, 개인정보/기밀 파일, SmartScreen, 실행파일 검사, Windows 환경 전수 검증.
- **Phase 4:** 검증된 실제 실행 프로그램·합성 샘플·매뉴얼·지원/환불 정책 등 크몽 상품화. 출시 및 비용/접근권한 변경은 사전 승인.

## 7. 개발 절차 / 안전 금지 사항

- GitHub가 작업 원본이다. `main`에 직접 미검증 기능 덮어쓰지 말고 `feature/*` → 합성 테스트 → CI → PR → 안전 병합 → HEAD 검증.
- 기존 공개 MIT 코드를 폐기하거나 다시 만들지 말 것. 판매 독점 코드를 Public 저장소에 넣지 말고, 비공개 저장소 생성/비용은 사용자 승인 후.
- `.env`, 실제 API 키, 고객 원본 코드·ZIP, Gemini 원문 응답, 비밀정보, 실제 고객 리포트는 GitHub와 출력 로그에 금지.
- 실제 Gemini API 호출, 자동 재시도, 원격 업로드, 추가 서비스비 0원 가정을 벗어난 행위 금지.
- 개발에 부딪히면 같은 방식 1~2회 실패 후 로그 기반 수정·대안 전환. 완료라고 말하기 전에 실제 SHA, CI, 테스트 증거 확보.
- 사용자는 팀장에게 매번 별도 지시할 필요 없음. **'[코드체커 깃헙 확인해]' → 현황 확인 후 Day 2 실제 코드 작업 착수**가 다음 채팅의 기본 행동.

## 8. 정확한 리포트 및 경고 기준

- `OfflineScan.status == "complete"`는 적격 입력 처리와 규칙 실행이 완료됐다는 뜻이지, 오류가 없거나 보안 검증을 통과했다는 뜻 아님.
- 현재 비-Python JS/TS는 generic-patterns-only = `limited`; 언어별 정밀 규칙이 미구현.
- 사용자에게 1,200줄·12,000줄 "확인됨"은 합성 규모 테스트 의미일 뿐 고객 프로젝트의 취약점 전수 검증 뜻 아님.
- 리포트의 파일·줄·코드 발췌는 자료의 민감정보 마스킹 기준을 통과해야 함.

## 9. 재개 커맨드

사용자: **[코드체커 깃헙 확인해]**

총괄 에이전트: GitHub 최신 main/PR/CI, 이 문서와 상태·구현 파일을 확인 → Day 2 구현 브랜치 생성 → 오프라인 한국어 HTML·Markdown 리포트 개발·합성 테스트·PR 병합/현황 기록 → 실제 완료/미완료만 보고. 질문 없이 승인된 작업부터 진행.

이 문서는 작업 재개의 편의를 위한 규칙이며 외부 서비스·GitHub 연결이 없는 환경에서 실제 작업 성공을 보증하지 않는다.
