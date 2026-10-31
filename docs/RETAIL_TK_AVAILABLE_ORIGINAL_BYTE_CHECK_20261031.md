# 설치 Tk 라이선스 원본 독립 바이트 검증 (Tcl 원본 누락 보존)

2026-10-31 Windows 빌드에서는 실제 Tcl/Tk 8.6.15/8.6.15가 실행되었으며, 설치 환경에서 수집된 `license.terms`는 Tcl 0개/Tk 1개였다. 기존 검사기는 Tcl 누락 때문에 반환한 `MISSING_INSTALLED_SOURCE_REVIEW_REQUIRED` 결과에서, 확보된 Tk 원본에 대해서도 **공식 업스트림 태그와의 Git blob 바이트 비교를 수행하지 않는 공백**이 있었다.

## 대안 및 선택

- A: Tcl·Tk 원본이 둘 다 있을 때만 비교(기존 방식). 구현비용 0, 그러나 이미 확보된 Tk 1건을 매번 미확인으로 남김.
- **B: 설치 원본이 존재하는 역할별로 공식 태그의 Git blob SHA-1과 원본 바이트를 독립 대조(채택)**. 기존 PINNED/안전한 원본 읽기/EXE SHA 검증 재사용; 신규 네트워크·패키지·API 과금 없음. Tcl이 없으면 전체 상태는 반드시 `MISSING_INSTALLED_SOURCE_REVIEW_REQUIRED`와 `source_equality_verified=false` 유지. 조회한 공식 8.6.15 원문: Tcl blob `d8049cd9e7ca055f7e584a76f88861a294b30c9c`, Tk blob `01264352c87ca7e34771bd1ee18bed5201ef139f`.

## 검증 가능한 결과

`scripts/verify_staged_tcl_tk_license.py`의 기존 CLI 명령/영수증 파일을 그대로 사용한다. 누락 상태에서 `available_installed_source_originals`는 존재한 Tcl/Tk 원문별 역할, 실제 런타임 patchlevel, 검증할 upstream 태그·blob ID, **실제 staged 원문 blob ID 및 일치 여부**를 표시한다. 다른 역할이 없거나 원문 해시가 달라도 영수증은 **개별 사실만** 기록하며 라이선스 준수나 판매 승인은 절대로 참으로 바꾸지 않는다. 설치 원문이 없다면 바이트 비교를 성공 처리하지 않는다.

CI의 기존 Windows EXE 후보 검증에 설치 Tk 바이트 비교 결과를 출력한다. 테스트는 무해한 합성 원문으로 (1) 실제 match (2) 원문과 staged manifest가 서로 일치하지만 공식 원문과 다른 경우 (3) 확인되지 않은 runtime tag를 검증한다. 공식 저작권 소유자/빌드 DLL 공급자·원본 법률 조건·71개 미분류 번들/LICENSE/NOTICE·실 소비자 Windows10/11 사용자 검수는 여전히 대기한다. GitHub에 실제 원본 텍스트/EXE/사용자 코드를 올리지 않는다.
