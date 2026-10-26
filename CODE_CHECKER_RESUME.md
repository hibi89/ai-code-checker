# CODE CHECKER — 새 채팅 자동 재개

공식 시작 입력: [코드체커 깃헙 확인해]. 간단한 후속 신호 ㄱ도 이미 승인된 다음 작업 진행을 뜻합니다. 사용자에게 같은 사실을 다시 묻지 말고 GitHub의 실제 상태를 먼저 확인하십시오.

## 저장소 및 복원 순서

GitHub: https://github.com/hibi89/ai-code-checker (현재 Public/MIT). 연결된 GitHub를 통해 main 최신 SHA, 열린 PR, feature 브랜치, CI Actions부터 조회합니다.
문서: HANDOFF.md → STATUS.md → AGENTS.md → REQUIREMENTS.md → FINAL_PRODUCT_BLUEPRINT.md → MVP_3DAY_ROADMAP.md → INPUT_SPEC_V2.md → 소스/테스트.
문서의 오래된 SHA 또는 진행 상태보다 GitHub 실제 코드/CI/PR 상태를 우선합니다.

## 확정 제품과 실행 원칙

사용자 승인 전략: 3개 개발일 MVP → 최종 설계도 GAP 대조/부족 기능 완성 → 다각도 안정성·보안·성능 보강 → 실기기 검증 후 크몽 판매 승인.
주력 상품은 Windows 고객이 로컬에서 반복 사용하는 코드 위험 진단 프로그램입니다. 기본 입력 TXT/다중 TXT/ZIP/폴더/붙여넣기, 로컬 정적 분석, 근거 대조, 한국어 HTML/Markdown, 브라우저 PDF 인쇄. 기본 모델 호출비/서비스비 0원(기기, 개발인건비, 결제 수수료 등의 전체 운영비 보장은 아님).
원래의 Gemini v1 CLI는 분리 보존합니다. 새 오프라인 GUI는 Gemini 호출을 요구하지 않습니다. Public MIT 소스, 고객 데이터·API 키·상업용 독점 코드는 절대 공개 커밋하지 않습니다.

## 최신 개발 상태 (2026-10-26 KST)

- Day1 오프라인 safe ingest와 Python AST 규칙 엔진: PR #2 main 병합 완료.
- Day2 한국어 HTML/Markdown 자체 포함 보고서, 파일·줄·근거 대조, no-clobber 출력: PR #3 main 병합 완료.
- Day3 Windows 데스크톱 MVP: feature/windows-portable, https://github.com/hibi89/ai-code-checker/pull/4 에 개발 및 검증 진행.
- 새 desktop_core.py (안전한 사전 미리보기 + 실행), desktop_ui.py (Tkinter 선택 화면·붙여넣기·언어·검사/결과 열기), tests/test_desktop_core.py (합성 9개 테스트), requirements-offline.txt (오프라인 Pydantic), scripts/build_windows_portable.ps1, requirements-offline-build.txt, Windows 전용 빌드 smoke CI, DAY3_WINDOWS_GUIDE.md.
- Day3 코드 SHA c6acab56559c22c7545af218d18a67c061e73203: GitHub Actions 40307804095 → 16/16 PASS; Linux 단위 테스트 총 85 PASS. 이후 파일/문서 변경 SHA는 별도 재조회.
- Windows EXE 후보 SHA (CI 40307810915): Windows 2025, Python 3.13.16, PyInstaller 6.22.3, 실제 EXE 빌드 + 합성 --self-test PASS. 산출물 SHA256은 STATUS.md에 있으며 공개 artifact 업로드는 안 했습니다.
- Windows GUI 실제 화면/클릭, PDF 인쇄, 바이러스 경고/SmartScreen, 독립 클린PC, 네트워크 패킷 감시는 모두 미검증입니다. EXE가 판매 가능한 완성품이라는 주장은 금지합니다.
- Vercel: 배포 대상 아님. 로컬 앱.

## 다음 실제 작업

1. PR #4가 아직 열려 있으면 가장 최근 head의 표준 16-job CI + Windows EXE smoke CI 확인, 실패 시 로그 기반 최소 수정. 모두 성공하면 PR을 ready로 표시하고 merge (non-force), main 병합 SHA + CI 확인.
2. Day3가 병합됐으면 최종 제품 설계도 대비 구현/검증/미구현/미검증 GAP 매트릭스 작성. 사용자 ㄱ 시 중요한 기능 누락 보완 및 안전 검증 순으로 진행. 아직 GUI 실기기 시험을 수행할 수 없으면 정확하게 미검증 표시하고, 검증 가능한 테스트부터 확대.
3. 기능 수정 시 새 feature 브랜치, 기존 코드·원본 보존, 합성 회귀 테스트, PR, main CI 검증, STATUS.md/HANDOFF.md 갱신.

## 사용자 승인 경계

자동 Gemini API 호출·유료결제·고객 코드 업로드·레포 공개 범위/권한 변경·비공개 레포 신설·상업 판매는 별도 사용자 승인이 있어야 합니다. 사용자의 ㄱ은 다음 승인된 개발 작업 계속 진행이지 위험 변경 동의가 아닙니다.

## 사용 명령(개발자 로컬에서만)

    python -m pip install -r requirements-offline.txt
    python desktop_ui.py
    python -m unittest discover -s tests -v
    python desktop_ui.py --self-test

윈도우 후보 빌드는 DAY3_WINDOWS_GUIDE.md와 scripts/build_windows_portable.ps1 참조. 고객 실제 코드 파일을 CI/GitHub/외부 AI로 보내지 마세요.
