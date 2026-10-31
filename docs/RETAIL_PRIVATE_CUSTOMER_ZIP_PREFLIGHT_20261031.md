# Code Checker — 고객 전달 후보 ZIP 구조/무결성 로컬 검증

**상태: 판매 승인 아님 / EXE 공개 배포 금지.** 실제 고객용 압축파일을 완성하기 전에 필수 구성 누락, 잘못된 EXE와 체크섬, 압축 경로 위험을 로컬에서 점검하는 **읽기 전용 사전 검증기**다. 고객 ZIP을 생성하거나 공개하지 않는다.

## 설계 비교

- A. Windows 탐색기로 수동 압축/해시·파일명 대조: 비용 0이지만 누락·섞인 EXE·ZIP 변조를 놓치기 쉽다.
- **B. 로컬 Python 표준 zipfile 기반 고정 계약 검사**: 별도 의존성/네트워크/유료 API 비용 0, 파일 크기에 따른 로컬 순차 해시·오염 ZIP 거부. 선택한 방식.

## 사용 전제 및 ZIP 경로 계약

사용자가 통제하는 비동기화 로컬 폴더의 **미공개 후보 ZIP**과 정확한 후보 EXE를 별도로 지정한다. 이 명령은 ZIP을 생성하거나 EXE를 실행하지 않는다.

ZIP 루트에 반드시 필요한 파일:

- `CodeCheckerOffline.exe` — 이미 별도로 검증한 후보 EXE와 **정확한 바이트 일치**
- `README.txt` — 실제 UI·제한사항·지원 범위에 맞춘 사용자 설명서
- `LICENSE` — 기존 제품 코드의 정확한 배포 조건과 고지. Public/MIT 및 다른 권리자의 원래 라이선스 무시 금지
- `NOTICE.txt` — 실제 포함 구성요소의 소유권·필수 고지문을 반영한 **사람 검토 후 원문**
- `SHA256SUMS.txt` — 자신을 제외한 **모든 파일**을 ASCII 소문자 SHA-256 + 공백 2개 + ZIP 상대경로 + 줄바꿈 형태로 정렬한 목록

제3자 라이선스 전문 파일은 `LICENSES/<component>.txt` 또는 `.md`, `.terms`, `.license` 이름만 허용한다. 이름이 Windows에서 위험하거나 중복될 수 있는 경로, 대소문자 충돌, 악성 링크, 알려지지 않은 실행 파일·스테이지 출력이나 비밀파일은 거부한다. 텍스트 파일은 UTF-8로 판독 가능해야 한다. ZIP 크기·압축 해제 총량에 상한을 두고, **디스크에 압축을 풀지 않는다**.

로컬 원본에서 직접 검토한 정식 LICENSE/NOTICE 파일만 사용한다. 아직 실제 Tcl/Tk 또는 71개 항목의 배포 권리가 확인되지 않았으므로, **빈 파일이나 합성 텍스트로 실제 고객 전달 ZIP을 만들지 않는다**. 테스트는 별도의 무해한 합성 바이트만 사용한다.

```powershell
python -m scripts.verify_customer_zip_candidate --zip .build-windows/private-candidate.zip --exe dist-windows/CodeCheckerOffline.exe --out .build-windows/private-zip-structure-receipt.json
```

기존 출력은 덮어쓰지 않는다. JSON에는 파일 내용·원본 라이선스·전체 경로를 복사하지 않고 정확한 ZIP/EXE SHA-256, 크기, 확인한 파일 수만 기록한다.

## 범위와 여전히 차단된 사항

- 구조/해시 일치 ≠ 저작권 소유권, 라이선스 원본·재배포 권리/NOTICE 완비, 악성코드 없음, 설치/SmartScreen, 사람의 GUI 조작, OS 네트워크 송신 또는 한글 PDF 수락.
- 결과 `customer_release_ready=false`, `owner_release_approval=false`, `status=PACKAGE_STRUCTURE_ONLY_RELEASE_BLOCKED`는 항상 유지한다.
- 정확한 EXE의 Tcl/Tk 설치 원본·DLL 및 71개 구성요소 권리/NOTICE **인간 검수** → 실제 Windows 10/11 실사용·Defender/SmartScreen·패킷·PDF 검증 → 최종 ZIP/지원·환불·가격/판매자 승인 후에만 실제 배포 가능 여부를 별도 판단한다.
- ZIP/EXE/실 라이선스/검증 JSON/고객 자료를 공개 GitHub, CI artifact, 크몽에 자동 업로드하지 않는다.
