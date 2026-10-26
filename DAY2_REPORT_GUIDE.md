# Day 2 오프라인 한국어 보고서 사용법

대상: Python 3.11 이상 개발자 실행형 프리뷰. **Windows GUI/EXE가 아니며 크몽 판매용 완성품이 아닙니다.**

## 실행 (필수 Gemini 키/AI API 없음)

```powershell
python -m pip install -r requirements.txt
python offline_report.py .\sample.txt --language python --output-dir .\reports --name scan01
python offline_report.py .\project.zip --output-dir .\reports --name zip01
python offline_report.py .\project_folder --output-dir .\reports --name folder01
```

- 단일 TXT에서 `--language python`은 가상 `.py` 파일로 분석합니다. 구분자 있는 통합 TXT는 각 섹션의 확장자로 언어를 지정합니다.
- HTML과 Markdown이 동일 실행으로 로컬에 생성됩니다. `scan01.html`을 웹브라우저에서 열고 **인쇄 → PDF로 저장**하십시오. 인터넷/스크립트/CDN은 필요하지 않습니다.
- 표준 출력에는 상태·건수·로컬 결과 경로만 표시하며 소스 코드나 발견 발췌를 출력하지 않습니다.
- 종료 코드: `0` 처리 범위 complete, `3` 일부 제한/실패/근거 확인 필요로 partial, `2` 입력 차단/출력 실패. Complete는 취약점 부재를 보증하지 않습니다.
- 동일 `--name` 결과 파일이 이미 있으면 덮어쓰지 않고 차단합니다. 새 이름을 지정하십시오.
- 출력 파일에는 **마스킹된 코드 발췌와 경로가 포함될 수 있으므로** 직접 보관·삭제를 관리하십시오.

## 근거 검증 정책

- 발견의 경로·줄 번호·발췌를 **마스킹된 실제 CodeBundle** 내용과 다시 대조합니다. 상속된 `citation_verified` 플래그는 신뢰하지 않습니다.
- 중복 후보는 제거하며, 파일/줄/발췌가 일치하지 않으면 근거 원문을 보고서에 싣지 않고 partial 상태로 내립니다.
- 검사 범위는 `analyzed / limited / failed / excluded / unsupported`로 표시합니다. 비-Python의 일반 패턴 검사, 구문 오류 및 입력 제외를 정밀 분석으로 과장하지 않습니다.
- 단일 TXT/통합 TXT의 가상 파일 라인 번호와 원본 TXT의 라인 번호를 구분합니다.
- HTML은 자체 포함 CSS, CSP와 이스케이프를 사용합니다. 동적 JS, 외부 자산, 자동 AI 호출이 없습니다.

## 테스트와 제약

```powershell
python -m unittest discover -s tests -v
```

실제 지원 확정은 최신 GitHub Actions와 Windows 실기기 결과를 기준으로 판단합니다. `os.link` 기반 임시 파일 완료 후 생성 방식은 일반적인 로컬 NTFS와 POSIX 파일 시스템을 가정하며, 미지원 파일 시스템에서는 덮어쓰기 우회 없이 실패합니다. 멀티 파일 보고서의 단일 트랜잭션은 아니다 보니 예기치 않은 프로세스 강제 종료 시 일부 출력 파일이 남을 수 있으며, 출시 전 강화 대상입니다.

아직 불가: 고객용 Windows GUI/포터블 EXE, 실고객 감사 보증, JS/TS 전용 분석기, 독립 8 AI 에이전트, 서비스 운영/판매.
