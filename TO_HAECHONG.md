# TO_HAECHONG.md — 코드체커 개발 효율 독립 검수 보고서

- 제출 대상: 해총(최상위 통합총괄) / 2026-10-28 KST
- 저장소: `hibi89/ai-code-checker`, 현재 실제 통합 개발 브랜치 `main`. PR #45 병합 후 미병합 PR 0건.
- 개선 **이전 기준**: `f8f1031e7dbbb331fcddd250ccefe82c1463daaa`.
- **개선 및 신규 기능**: PR [#45](https://github.com/hibi89/ai-code-checker/pull/45), 기능 커밋 `063ac7f13ddb7ab6f33861cd5f86edd3bdc2fa92`, 병합된 `main` `e5c6da931506561ca835ea9b68989eb04bdc6eff`.
- 검수 원칙: 기능 구현, CI 통과, 고객 PC 확인, 라이선스·판매 승인은 서로 다른 상태다. 실제 측정하지 않은 시간 절감률과 진척 퍼센트는 기재하지 않는다.

## 1. 기존 병목 TOP 3

1. **GitHub API/커밋·문서 왕복**: 앞선 P2-7~P2-10에서는 작은 코드 변경 후 `STATUS.md`, `HANDOFF.md`, `CODE_CHECKER_RESUME.md`를 별도 문서 커밋으로 반복 갱신했다. 한 기능마다 소스 병합, 문서 커밋, 최종 SHA CI를 따로 기다렸다.
2. **중복 원격 테스트·조회**: `.github/workflows/tests.yml`은 Ubuntu 두 버전·Windows × Python 3.11~3.15 = 15개 테스트 잡 + 1개 의존성 감사 잡을 push/PR마다 실행한다. 이전에는 동일 결과를 계속 폴링하고, 부분 수정에도 전체 검증을 다시 대기했다.
3. **실제 Windows 검증의 여러 수동 명령**: MVP, 컨트롤러, Python 테스트, GUI/PDF 스모크가 여러 스크립트에 흩어져 있어 사용자 또는 총괄이 실행 순서와 결과를 별도로 추적해야 했다.

*근거: PR #42~#45의 소스/문서 커밋과 GitHub Actions 기록, `.github/workflows/tests.yml`의 16잡 정의, 기존 `scripts/mvp_acceptance.py`, `scripts/windows_gui_e2e.py` 등. 특정 병목의 소요시간 비중은 별도 계측하지 않아 **미측정**이다.*

## 2. 발생 원인

- 도구: 이 채팅에서는 GitHub connector로 변경 파일을 원격 반영해야 하므로 파일별 API 쓰기·조회가 많아지는 경향. 반복적인 사용자 PC 동작은 이 환경에서 직접 수행할 수 없다.
- 작업 순서: 작은 기능 구현 후 중복 인수인계 문서 세 개를 매번 갱신한 운영 습관과 필요 이상 잦은 원격 폴링.
- 검증 환경: 전체 16잡 CI와 Windows PyInstaller 패키징은 실제 안정성 근거를 제공하지만 개별 작은 수정 직후 전부 기다리는 것은 낭비. 반대로 **최종 기능 통합, 보안, 고객 실기기 검증은 생략할 수 없다**.

## 3. 실제 적용한 개선 vs 계획

**완료된 변화**
- PR #45의 **관련 파일 7개를 단일 Git tree/기능 커밋**에 반영했다. 코드·기존 회귀테스트·`AGENTS.md` 운영 규칙·최소 `HANDOFF.md` 변경·Windows 자동화·해당 CI 연결을 한 번에 처리. 별도 `STATUS.md`/`CODE_CHECKER_RESUME.md` 갱신 커밋을 만들지 않았다.
- `AGENTS.md`에 '한 기능 단위 → 핵심 검증 → 필요한 통합 CI → 병합', 중복 상태 조회 최소화, 문서 역할 분리, 안전/권한/릴리스 게이트 보존을 영구 지시로 추가.
- 루트 `verify_local.ps1` 도입: 기본 전체 Python 회귀 + 합성 MVP/컨트롤러/규칙; `-Quick`는 구문·MVP·컨트롤러 세 항목만 실행하고 나머지를 **SKIP**으로 기록; `-IncludeGuiSmoke`는 기존 Windows Tk/PDF 합성 스모크 실행. 각각 PASS/FAIL/SKIP, Git SHA, 요약, 미확인 출시 항목을 덮어쓰기 없는 임시 JSON으로 작성. 자동 설치·유료 API·고객 코드·시스템 보안 설정 조작 없음.
- `.github/workflows/windows-portable.yml`에 `verify_local.ps1 -Quick` 실제 Windows 실행 단계를 연결했다.

**미개선/미측정**
- 기존 16잡 매트릭스 구조 자체는 **변경하지 않았다**. 필수 통합 검증 유지 목적이지만 실행비용/대기시간 절감은 측정되거나 입증되지 않았다.
- GitHub connector API 자체의 원격 지연이나 실제 소비자 Windows 실행을 자동 제거한 것은 아니다. 사전/사후 개발 리드타임의 직접 비교자료 **없음**.

## 4. 개선 이후 추가 완성한 실제 기능

- `desktop_core.py`: 스캔 이전 미리보기 화면에서 `제외·미지원 파일 경로` 최대 12개와 `탐색 제외 폴더 경로` 최대 12개를 실제로 표시한다. 12개 초과 시 잔여 수 표시, 하위 제외 폴더 내부 파일 수는 미확인으로 명시. 이전에는 개수만 표시되어 무엇이 누락되는지 사용자가 바로 확인하기 어려웠다.
- ZIP·다중 파일 TXT·폴더 입력에서 민감 파일의 **경로 레이블만** 표시하고 비밀 값이나 원문은 표시하지 않는다. 기존 스캔 경로/라인 근거·미리보기 무효화 규칙 유지.
- `tests/test_desktop_core.py`와 `tests/test_pruned_coverage.py`의 *기존 테스트*를 확장해 위 사용자 기능을 검증했다. 별도 형식 테스트 수 늘리기가 목표가 아니었다.
- 이 기능과 개발 절차 개선을 **동일 PR #45로 완료**했다. 시간 절감률은 측정되지 않았으므로 제품 가치와 운영 개선을 구분해 평가해야 한다.

## 5. 검증 증거 / 원본 대조 기준

| 항목 | 증거 |
|---|---|
| 이전 main | `f8f1031e7dbbb331fcddd250ccefe82c1463daaa` |
| 변경 파일(7개) | `desktop_core.py`, `tests/test_desktop_core.py`, `tests/test_pruned_coverage.py`, `verify_local.ps1`(신규), `.github/workflows/windows-portable.yml`, `AGENTS.md`, `HANDOFF.md` |
| 신규 기능 커밋 | `063ac7f13ddb7ab6f33861cd5f86edd3bdc2fa92` / PR #45 |
| 병합된 main | `e5c6da931506561ca835ea9b68989eb04bdc6eff` |
| 정확한 기능 SHA 전체 CI | [Actions 40552552159](https://github.com/hibi89/ai-code-checker/actions/runs/40552552159) **16/16 PASS**, Ubuntu Python 3.11 299개 테스트 실행/실패 0/SKIP 2 |
| Windows GUI/EXE/PowerShell | [Actions 40552552546](https://github.com/hibi89/ai-code-checker/actions/runs/40552552546) PASS. `verify_local.ps1 -Quick` 로그 **PASS 3 / FAIL 0 / SKIP 4**. 실행 기록의 로컬 SHA는 PR 가상 병합 체크아웃일 수 있으므로 정확한 원격 검증 SHA는 Actions의 `head_sha`로 확인 |
| 병합 main CI | [Actions 40552929581](https://github.com/hibi89/ai-code-checker/actions/runs/40552929581) **16/16 PASS**, SHA `e5c6da931506561ca835ea9b68989eb04bdc6eff` |
| 실고객 Windows/PDF 육안/네트워크 패킷 | **미실행·미승인**. 위 합성 PASS와 구분 |

## 6. 현재 남은 병목과 담당

**AI 총괄이 계속 직접 수행 가능:** Python 엔진 기능 누락·오탐 감소, 안전한 입력/출력 복구, 미리보기 계약/회귀, 합성 Windows GitHub Actions, 기존 스모크 통합, 중요 장애 원인 분리, 최소 인수인계.

**사용자 Windows PC 또는 소유자 승인 필요:** 실제 깨끗한 소비자 Windows 실행과 SmartScreen/Defender 평판·차단 확인, 시스템 패킷 관찰(기본 검사 외부 전송 없음), 한국어 PDF 글리프/레이아웃 육안 확인, 실제 고객 전달/삭제·보관 UX, 포함된 라이선스/NOTICE 원문 법적 검수, 바이너리 배포·상용 판매 결정. 고객 데이터·실 계정·유료 서비스·OS 설정 또는 권한 변경은 자동으로 진행하지 않는다.

## 7. 최우선 개발 및 완료 조건

1. **다음 기능:** 최초 [설계도](FINAL_PRODUCT_BLUEPRINT.md)에 명시됐으나 미구현인 '붙여넣기 가상 파일명 선택'을 실제 입력 UI와 로컬 엔진에 추가. 파일명 경로 탈출/중복 확장자/지원 언어를 엄격히 검증하고, 변경 시 이전 미리보기 무효화; HTML/Markdown 근거에 사용자가 선택한 가상 파일명이 정확히 표시되게 한다.
2. **다음 검증:** 기존 `verify_local.ps1 -Quick`/기능 관련 회귀 → 전체 16잡 CI + 호스티드 Windows Tk/EXE 스모크 정확한 SHA 증명 → 비강제 병합. 실제 고객/릴리스 게이트는 별도 미검증으로 유지.
3. **MVP 현황:** 안전한 입력·Python AST·로컬 보고서·Tk·합성 EXE 경로는 이미 자동 테스트 PASS. 이 작업 이후 추가되는 가상 파일명 UX는 설계 누락 보완이다. '판매 준비 완료'는 아님.
4. **최종 잔여:** Python/제한적 JS/TS 범위 진실성, 실제 소비자 Windows + SmartScreen + 무네트워크 실증 + 한국어 PDF 육안 + 번들 원본 LICENSE/NOTICE + 판매 가이드/지원·환불 규정/소유자 승인. *남은 시간과 최종 완성률은 실측 데이터가 없어 이 보고서에서 임의 추정하지 않는다.*

**해총 검수 요청:** 기능·코드 대조는 KEEP/ACCELERATE 후보. CI 매트릭스 대기시간과 Windows 실기기 검증은 FIX로 남기고, 매 기능의 중복 STATUS/RESUME 문서 갱신은 STOP 대상으로 판정해 주시기 바란다. 이 분류는 자체 제안이며 최종 판정은 해총 몫이다.
