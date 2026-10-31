# Frozen EXE 실제 Tk 다중 입력 E2E 검증 (Windows hosted candidate)

**개선 대상:** 개발 Python으로 실행한 `scripts/windows_gui_e2e.py`에는 TXT, ZIP, 폴더, 붙여넣기, 취소·실패가 이미 포함돼 있었다. 그러나 EXE 자체의 `--scenario-smoke`는 붙여넣기 Python 1건만 검사해, PyInstaller 실행파일의 ZIP·폴더·TXT 처리에 누락된 런타임 모듈이나 포장 오류가 있는지 직접 확인하지 못했다.

## 설계 선택

- A: 기존 개발용 Tk GUI 테스트만 유지하고 Windows 실행파일에서는 1개 붙여넣기만 스모크 — 실행비용 최소지만 배포대상 EXE의 경로형 입력은 미검증.
- **B: 기존 EXE `--scenario-smoke`를 하나의 Tk 실행에서 5개 합성 시나리오로 확장** — 새로운 실행 옵션·의존성·프로그램·빌드 도구 없음. 고객 EXE 내부에서 실제 Tk 버튼(미리보기→검사), worker, 보고서 생성·열기 권한, 안전 차단을 검증해 기능 품질 향상.

## 실행 및 검증 범위

기존 `scripts/windows_local_exe_smoke.ps1`와 `.github/workflows/windows-portable.yml`의 EXE 후보 smoke가 **변경 없이 동일 옵션**으로 호출한다. 수정하는 것은 `desktop_ui.py`의 `packaged_scenario_smoke_test`뿐이다. 무해한 임시 파일을 사용하여:

1. 메모리 붙여넣기 → 한국어 HTML/Markdown + Python 위험 검사.
2. TXT 파일 + Python 언어 선택 → 유효 보고서.
3. ZIP(Python + JavaScript) → 위험 탐지/제한 분석 1개 표시.
4. 폴더(Python + .git 제외) → 보고서 및 제외 subtree 1개 표시.
5. 경로 탈출을 포함한 악성 ZIP → 미리보기 차단, 이전 보고서/삭제 권한 해제, 새 결과 없음.

각 보고서는 같은 비동기화 임시 작업 공간에 **서로 다른 파일명**으로 생성되고, 생성된 4개 HTML/MD 파일쌍 존재·소스 TXT 바이트 보존을 확인한다. 실제 사용자 코드를 읽거나 실행하지 않고, 외부 네트워크나 브라우저·AI API를 호출하지 않는다. CI에서 실행하는 Windows 2025 hosted worker는 실제 고객 Win10/11 사람 조작, SmartScreen·Defender·패킷 캡처·한글 PDF 육안 검증 및 라이선스/NOTICE 검수의 대체물이 아니다.

**출시 차단:** Tcl/Tk 공식 원문과 정확 번들 DLL의 권리·전체 미확정 archive 행의 NOTICE, 실소비자 OS, 가격/지원/환불·실 고객 ZIP·소유자 명시 판매 승인 미완료. `--scenario-smoke` 통과해도 판매/배포하지 않는다.
