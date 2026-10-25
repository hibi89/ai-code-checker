# AI Code Checker

로컬에서 실행하는 AI 보조 코드 검수 CLI입니다. 선택한 프로젝트의 지원 파일을 안전하게 모아, 로컬 정적 검사와 Gemini Interactions API의 **단일 분석 호출**로 한국어 검수 리포트를 만듭니다. API 요청은 `store=false`로 보내 서버에 다시 불러올 Interaction 기록을 만들지 않습니다.

하나의 AI 모델이 보안·신뢰성·테스트·구조·유지보수·성능·자원관리·복잡도/비용의 8개 관점을 확인합니다. 서로 독립된 8개 AI나 사람 리뷰어가 검토하는 서비스는 아닙니다.

## 기능

- 폴더, ZIP, 단일 파일, 표준 입력 지원
- 폴더 입력에서는 심볼릭 링크와 일반 파일이 아닌 항목을 따라가거나 열지 않음
- ZIP을 디스크에 풀지 않고 제한된 크기만 읽음
- .env, 개인키 등 민감 파일은 열지 않고 제외
- 코드 안에서 알려진 API 키·토큰 패턴과 자격증명 값을 마스킹
- 이메일, 한국 휴대전화, 주민등록번호 형태를 전송 전에 마스킹
- Python 구문과 일부 위험 패턴을 코드 실행 없이 로컬 점검
- Gemini 요청 전에 예상 원가를 계산하고 설정 상한을 넘으면 호출 중단
- AI가 제시한 파일·줄·코드 발췌가 입력 원문에 있는지 확인
- 실제 사용 토큰 수와 예상 API 원가를 코드 없이 로컬 JSONL로 기록
- 한국어 Markdown 리포트 생성

## 요구 사항

- Python 3.11 이상 (CI 검증: Python 3.11~3.15)
- Google Gemini API 키

## 설치 (Windows PowerShell)

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
~~~

.env에 GEMINI_API_KEY를 입력합니다. .env 파일은 입력 프로젝트에서 읽거나 업로드하지 않습니다.

## 사용법

~~~powershell
# 프로젝트 폴더
python main.py .\path\to\project

# ZIP
python main.py .\project.zip

# 단일 파일
python main.py .\main.py

# 외부 API 없이 입력 필터와 정적 검사만 확인
python main.py .\path\to\project --dry-run

# 표준 입력
Get-Content -Raw .\main.py | python main.py --filename main.py
~~~

코드를 Gemini로 보내기 전에 전송 동의 화면이 나옵니다. 자동화·비대화형 실행에서는 --confirm-upload를 명시해야 합니다.

`--dry-run`은 실제 파일 목록, 마스킹 및 정적 검사 결과와 예상 최대 API 원가를 보여줍니다. 설정한 원가 상한을 넘는지도 확인하지만, 어떤 경우에도 외부 API를 호출하지 않습니다.

~~~powershell
python main.py .\project.zip --confirm-upload --order-ref KM-001
~~~

기본 리포트는 사용자 홈의 `.ai-code-checker/reports/`에 저장되고, 기존 파일은 덮어쓰지 않습니다. 리포트에는 코드 발췌가 포함될 수 있으니 기밀 자료로 취급하고 안전하게 삭제하세요. 사용량 로그는 사용자 홈의 `.ai-code-checker/usage.jsonl`에 저장하며 코드 원문은 기록하지 않습니다. 새 로그를 기록할 때 90일이 지난 로그 행을 정리합니다.

AI 응답에서 8개 점검 관점이 빠지거나 중복되면 리포트에 불완전 상태를 표시하고 CLI가 오류 코드로 끝납니다. 불완전 리포트는 고객에게 납품하지 말고 다시 확인하세요.

## 입력 및 비용 한도

기본값은 최대 50개 파일, 파일당 128 KiB, 프로젝트 전체 512 KiB, ZIP 20 MiB입니다. .git, 가상환경, 의존성·빌드 폴더, 잠금 파일, 키·인증서, .env 계열 파일은 제외됩니다. UTF-8 텍스트만 읽으며 Python, JavaScript/TypeScript, Java, Go, Rust, C/C++, C#, PHP, Ruby, Swift/Kotlin, SQL, 셸, 일반 설정 파일 등을 지원합니다.

기본 모델은 `gemini-3.1-flash-lite`입니다. `.env.example`의 입력·출력 단가는 Google Gemini API Standard 유료 등급의 2026-10-26 목록 가격 기준입니다. 예를 들어 입력 10,000 토큰과 출력 2,048 토큰이면 약 $0.0056 (환율 1달러=1,324.45원 가정 시 약 8원)입니다. 기본 요청당 사전 원가 상한은 $0.05이며, 실제 청구액은 토큰 수·환율·세금·계정 조건에 따라 달라집니다. 다른 모델을 지정하면 입력·출력 단가도 함께 바꾸세요. 고객 코드를 처리하는 판매 운영에는 무료 등급을 사용하지 않고, Google의 유료 등급과 데이터 처리 조건을 확인하세요. [Gemini API 가격](https://ai.google.dev/gemini-api/docs/pricing) · [모델 정보](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite)

## 보안 및 한계

- 원본 코드를 실행하거나 의존성을 설치하지 않습니다.
- 비밀정보·개인정보 탐지는 패턴 기반이므로 모든 값을 찾는다고 보장하지 않습니다. 전송 전 직접 확인하세요.
- AI가 만든 발견 항목의 발췌 일치는 위치 확인일 뿐, 결함 판정 자체의 검증은 아닙니다. High/Critical 항목은 사람이 원본과 실행 맥락을 확인해야 합니다.
- 이 도구는 테스트 실행, 침투 테스트, 보안 인증 또는 무결점 보증을 제공하지 않습니다.
- 선택 파일과 마스킹된 코드가 동의 후 Google Gemini API로 전송됩니다.
- Interaction 저장을 끄더라도 Zero Data Retention을 제공하는 것은 아닙니다. 결제가 활성화된 Gemini 유료 프로젝트에서는 프롬프트·응답을 제품 개선에 사용하지 않지만, Google 정책상 악용 모니터링을 위해 입력·맥락·응답이 최대 55일 보관될 수 있습니다. [Interactions 저장 설정](https://ai.google.dev/gemini-api/docs/interactions-overview) · [Google 데이터 처리 및 보관 안내](https://ai.google.dev/gemini-api/docs/usage-policies)
- 고객 코드는 클라우드 동기화 폴더 밖에서 처리하세요. 판매 운영 시 작업 사본·리포트 사본·임시 파일을 납품 후 7일 안에 직접 삭제해야 합니다. Google 측 보관은 별도입니다.
- API 오류 `HTTP 401 UNAUTHENTICATED`는 보통 키가 없거나 유효하지 않거나 만료된 경우입니다. Google AI Studio의 API Keys 화면에서 키 상태·유형과 연결 프로젝트를 확인하고, 오래된 Standard 키라면 Gemini API 제한을 적용하거나 새 키를 발급해 로컬 `.env`의 `GEMINI_API_KEY`만 교체한 뒤 다시 확인하세요. 2026-05-28부터 AI Studio 신규 키는 auth key로 발급되며, 제한이 없는 Standard 키는 거절될 수 있습니다. 키를 저장소·채팅·이슈에 올리지 마세요. [키 유형·관리 안내](https://ai.google.dev/gemini-api/docs/api-key) · [401 오류 안내](https://ai.google.dev/gemini-api/docs/api-errors)
- API 오류 `HTTP 503 UNAVAILABLE`은 일시적인 서버 과부하나 중단일 수 있습니다. 먼저 잠시 뒤 다시 시도하세요. 이 CLI는 중복 비용을 막기 위해 생성 요청을 자동 재시도하지 않으므로, 반복 호출보다 잠시 기다렸다 한 번 재시도하는 편이 낫습니다. 503만으로 키가 잘못됐다고 판단하지 마세요. [Gemini API 오류 안내](https://ai.google.dev/gemini-api/docs/api-errors)
- 연결 오류나 타임아웃은 요청 처리 여부를 확인할 수 없을 수 있습니다. 네트워크를 점검하고 Google 사용량을 확인한 뒤 재시도하세요.

## 검수

~~~powershell
python -m unittest discover -s tests -v
~~~

공개 저장소의 GitHub Actions는 push/PR마다 Ubuntu 24.04·26.04 및 Windows Server 2025에서 Python 3.11~3.15 조합의 컴파일, 자동 테스트, 외부 API 없는 dry-run을 실행하고, 별도 작업에서 `requirements.txt`의 알려진 취약점을 `pip-audit`로 확인합니다. Python 3.10은 2026-10-01 보안 지원이 종료되어 지원 대상에서 제외했습니다.

## 상품 설계 문서

[상품화 일정, 범위, 가격 실험, 비용 가정 및 출시 전 검수 기준](PRODUCT_PLAN_KMONG.md)

[크몽 서비스 제목, 패키지 설명, 준비사항 및 FAQ 초안](KMONG_LISTING_DRAFT.md)

[Gemini 실 API 인증 후 정확도·원가·처리시간 파일럿 절차](PILOT_EVALUATION.md)

[크몽 주문 접수, 외부 전송 동의, 로컬 보관, 납품 전 검수와 삭제 절차](KMONG_ORDER_OPERATIONS.md)

크몽 등록용 메인 이미지 후보는 [assets/kmong-thumbnail-kmong-ready.png](assets/kmong-thumbnail-kmong-ready.png) (4:3)입니다. 예전 아이디어 시안은 [assets/kmong-thumbnail-concept.jpg](assets/kmong-thumbnail-concept.jpg)입니다. 합성 코드로 만든 결과물 서식 예시는 [output/pdf/sample-report-example.pdf](output/pdf/sample-report-example.pdf)이며 실제 분석 결과가 아닙니다.

## 라이선스

MIT. LICENSE를 확인하세요.
