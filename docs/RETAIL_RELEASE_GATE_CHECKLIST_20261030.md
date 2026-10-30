# Code Checker — 크몽 출시 필수 검수 정본 (2026-10-30 KST)

> **상태: 출시 미승인 / 외부 배포 금지.** 이 문서는 확인된 공식 라이선스 출처와 실제 사용자 PC 실증 절차를 한곳에 연결한다. 법률적 판단이나 배포 권한의 증명, 판매자의 출시 승인을 대체하지 않는다. 기존 Public/MIT 자체 코드, Gemini v1 및 해커톤 배포와 무관한 **오프라인 Windows 단독 프로그램**만 다룬다.

## 1. 결정과 판단 기준

- 사용자에게 판매할 후보는 **29,000원 일회성, Windows 포터블 EXE**, 실제 판매가/지원/환불은 별도 최종 승인.
- 개발자 합성 CI PASS와 고객용 수락 PASS를 구별. Windows 2025 hosted runner는 깨끗한 소비자 Windows 10/11이 아니다.
- EXE 파일명만 보거나 설치된 Python wheel의 메타데이터만으로 실제 **동봉 바이너리의 출처·버전·재배포 권한**을 입증하지 않는다.
- 현재 `scripts/audit_frozen_exe.py` → `scripts/map_frozen_licenses.py` → `scripts/reconcile_native_build.py` → EXE/PKG TOC → `scripts/reconcile_notice_gaps.py`가 EXE SHA 및 출처 후보를 로컬에서 수집하지만, `notice_ready_to_distribute=false`와 `customer_release_ready=false`를 유지한다.

## 2. 공식 원문 확인 — 특정 후보에 대한 검수 출발점

| 구성요소 | 확인한 공식 원문 | 검수 실무상 유의점 | 판정 |
|---|---|---|---|
| CPython 3.13 (Windows 빌드 CI Python 3.13) | [Python 3.13 History and License](https://docs.python.org/3.13/license.html) | PSF License v2, 저작권 표시/라이선스 유지 및 Python 자체에 포함된 외부 라이선스 목록 확인. 정확한 EXE 내 CPython 바이너리와 해당 버전 원본 일치 검수 필요 | **원문 위치 확인, 실제 동봉분 미검증** |
| Tcl/Tk | [Tcl/Tk Licensing Terms](https://www.tcl-lang.org/software/tcltk/license.html) | 배포 시 기존 저작권 및 `license.terms` 통지문 포함 조건 확인. 실제 번들 Tcl/Tk 버전·리소스·추가 패키지 별도 확인 | **원문 위치 확인, 동봉/NOTICE 미검증** |
| PyInstaller 6.22.3 | [공식 PyInstaller 6.22.3 License](https://pyinstaller.org/en/stable/license.html) | 상용 앱 번들 생성은 예외에 의해 허용될 수 있으나 **종속 구성요소 라이선스 준수는 별개 의무**. 수정 PyInstaller 배포 여부와 정확한 EXE 포함분 확인 | **공식 허용 범위 확인, 전체 의존성 미검증** |
| Microsoft / Visual C++ runtime 등 | [Microsoft Redistribute Visual C++ files](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170) | 제공된 redistributable 또는 특정 DLL의 재배포는 **라이선스·REDIST 목록 조건**에 종속. EXE에 실제 포함된 파일/출처/라이선스 검증 없이 배포 가능하다고 단정 금지 | **법적 주의 원문 확인, 포함 여부·권한 미검증** |
| pydantic, pydantic-core, annotated-types, typing-extensions 및 기타 설치/동봉 패키지 | 빌드 환경의 각 패키지 **정확한 버전의 원본 LICENSE/NOTICE 및 배포 파일** | pip 목록은 단순 환경 정보. 실제 CArchive/PYZ, native DLL/PYD/데이터와 매핑하고 저작권·표시 의무 별도 확인 | **원본별 미완료** |
| Code Checker 자체 소스 | 저장소 루트 [LICENSE](../LICENSE) | 공개 MIT 소스와 고객 소프트웨어의 이용조건을 모순되게 설명하지 말 것. 기존 자체 MIT 및 제3자 의무 유지 | **정본 존재, 실제 고객 전달물 미작성** |

**중요:** 공식 페이지의 일반적 상업적 허용 가능성과 **현재 만든 정확한 실행 파일을 배포해도 된다는 승인**은 다르다. 사용한 버전과 바이너리를 확정하기 전에는 NOTICE 파일을 확정하지 않는다.

## 3. 실제 EXE 라이선스 승인 체크 (독립 리뷰)

1. **한 개의 빌드만 고정:** 소스 commit SHA, Windows 버전, Python 버전, pinned 패키지 버전, EXE SHA-256/크기 기록. GitHub CI에 남은 과거 빌드 증거를 현재 EXE로 재사용 금지.
2. 개발용 로컬 Windows 환경에서 이미 승인·설치된 의존성으로 `./scripts/build_windows_portable.ps1` 실행. 새 패키지 설치·네트워크 다운로드는 별도 결정 필요.
3. 같은 빌드에 대해 `scripts/audit_frozen_exe.py`, `scripts/map_frozen_licenses.py`, `scripts/reconcile_native_build.py`, `scripts/reconcile_exe_toc.py`, `scripts/reconcile_pkg_toc.py`, `scripts/reconcile_notice_gaps.py` 순서로 실제 EXE·빌드 TOC 대응 확인. 기존 CI `.github/workflows/windows-portable.yml`의 정확한 인수를 참고.
4. CPython, Tcl/Tk, PyInstaller bootloader, 컴파일된 네이티브 모듈, 모든 동봉 패키지/폰트·리소스·MS DLL의 **원본 출처·정확 버전·허용 조건·필요 통지**를 사람이 확인한다. 동봉되지 않은 *build-only* 패키지는 해당 이유를 기록하되 자동으로 면제하지 않는다.
5. 고객에게 실제 전달될 압축 묶음에 필요한 **원본 LICENSE/NOTICE 및 저작권 텍스트**를 빠짐없이 포함한다. 빌드 환경에서 수집한 `NOTICE_REVIEW_DRAFT.md`는 초안이며, 그대로 고객에게 제공할 수 없다.
6. 리뷰어가 전체 포함 구성요소·명시적 재배포 권한·NOTICE/저작권 충족을 확인하기 전까지 **`RELEASE_BLOCKED`**. unsigned EXE, 임시 CI 산출물이나 미승인 NOTICE를 공개 GitHub·크몽에 업로드하지 않는다.

## 4. 실제 Windows 구매자 수락 체크

깨끗한 **일반 Windows 10/11** 환경(개발 도구/Python 미설치 시나리오 포함)에서 빌드된 **동일 SHA의 EXE**를 사용해 관찰한다. 사용자 PC를 임의로 재설정하거나 Defender/SmartScreen을 끄지 않는다.

| 테스트 | 합격 근거 | 현 상태 |
|---|---|---|
| EXE 단독 구동, UI 렌더링 | Python 별도 설치 없이 시작, 사용자 화면에서 텍스트/조작 가능 | **미검증** |
| 로컬 합성 소스·ZIP·폴더·TXT·붙여넣기 | 미리보기 → 검사 → HTML/Markdown 저장·열기 → 재검사·현 세션 보고서 삭제 | **CI 합성 검증 이력만**, 실기기 미검증 |
| 차단/복구 | 악성 경로 ZIP, 제외 디렉터리, 변조 보고서, 취소·재시도에서 안전한 부분/차단 처리 | **CI 합성 검증 이력만**, 실기기 미검증 |
| SmartScreen/Defender | 실제 경고·탐지 여부와 대응 정책 기록. **보호 기능 비활성화 금지** | **미검증** |
| OS 네트워크 송신 | 고객 파일을 사용하지 않는 고정 합성 사례로 승인된 OS 수준 패킷/프로세스 관찰; 자동 업로드·의도치 않은 외부 연결 없음 확인 | **미검증** |
| Chrome/Edge PDF | 한국어 글꼴, 긴 파일/라인, 줄바꿈, 페이지 나눔을 실제 인쇄/PDF 열어 **육안 확인** | **미검증** |
| 전달 ZIP·고지문·설명 | 실행 파일 SHA/설명서/원본 LICENSE·NOTICE/사용제한/지원·환불 정책 실제 납품본 일치 | **미구성·미승인** |

### 로컬의 기존 안전한 개발 도구

- `powershell -NoProfile -ExecutionPolicy Bypass -File .\verify_local.ps1` — 설치 없이 합성 기능 점검, 임시 비밀 제외 증거 파일; PowerShell 스크립트의 자체 설명을 반드시 확인.
- `./scripts/build_windows_portable.ps1` — 패키징 의존성이 이미 설치된 **개발 PC 전용**, 기존 EXE 덮어쓰기 거부, unsigned 후보 생성.
- `./scripts/windows_acceptance_readonly.ps1 -ExePath 'dist-windows/CodeCheckerOffline.exe' -OutputPath '.build-windows/windows-acceptance-local.json'` — EXE SHA, 서명, Defender 설정의 **읽기 전용 관찰**만 기록. 외부 업로드·로컬 OS 패킷 검증·소비자 수락·라이선스 승인은 **하지 않는다**. 이미 파일이 있으면 다른 파일명 사용.
- `python -m scripts.windows_acceptance_contract --evidence .build-windows/windows-acceptance-local.json --exe dist-windows/CodeCheckerOffline.exe` — 기존 증거 정합성 검증. **판매 가능 판정을 하지 않는다.**

위 명령은 개발 환경에 이미 존재하는 도구를 전제로 한 선택적 절차이다. **실기기 검증을 수행하지 않았으면 PASS로 바꾸지 않는다.** 고객 소스·계정·토큰·원본 라이선스 문서·실제 EXE를 Public GitHub에 업로드하지 않는다.

## 5. 실패·판정·인수인계

- CI 또는 테스트 실패: 해당 **SHA·실제 로그·실패 항목**만 확인하여 가장 좁은 수정 → 회귀 검증. 같은 실패를 반복하는 빈 커밋 금지.
- 실사용 또는 법적 원본 미확보: **BLOCKED/UNVERIFIED** 유지. 비용·권한·공개 배포·범위 변경은 사용자 승인 필요.
- 최종 출시 승인 조건: 정확한 고객 전달 ZIP과 hash, 실제 사용 검증, 라이선스 원문 확인·NOTICE, 상품 안내/환불·지원 규정, 사용자 최종 배포 승인, 크몽 적격 판매 심사.
- 문서 근거 시점: **2026-10-30 KST**. 이 파일의 공식 URL은 공개 라이선스 검수의 시작점이며, 실제 고객 전달물의 권한을 인증하지 않는다.
