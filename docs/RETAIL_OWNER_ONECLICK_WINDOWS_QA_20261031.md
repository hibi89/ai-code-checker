# Code Checker — 실제 Windows PC 일괄 검수 도구 (개발자/소유자 전용)

**판정:** GitHub CI와 구매자 Windows 수락은 다르다. 이 도구를 성공적으로 실행해도 **크몽 출시 불가**이며 소유자/저작권·NOTICE와 사람의 실사용 검증은 별도다.

## 설계 선택

- A — 기존 PowerShell/Python 검증기 4개를 매번 개별 수동 실행: 코드 변경이 적지만 파일명·EXE SHA 혼동, 누락·덮어쓰기 위험이 크다. Python이 없는 PC에서는 전체 경로가 닫힌다.
- **B — 이미 검증한 Windows EXE 테스트와 OS 읽기 전용 스크립트를 PowerShell 7 한 명령으로 실행**: 기존 코드 재사용, Python·API·유료 호출·관리자 권한 불필요, 동일 EXE SHA 확인. 프로그램 자체는 Python/PowerShell 설치가 불필요하지만 **이 개발자 검수 도구에는 PowerShell 7이 필요**하다. 이 방식 선택.

## 사전 준비

실제 구매자 환경에 가까운 별도 일반 Windows 10/11에서 **이미 빌드한 EXE**와 소스 저장소의 `scripts` 디렉터리를 로컬 복사한다. Python, VS Code 및 개발 도구는 EXE 실행에 필요하지 않다. 검수 스크립트 실행에는 `pwsh`(PowerShell 7)가 이미 설치되어 있어야 한다. 별도의 설치·정책/Defender/SmartScreen 변경·원본 파일 수정·네트워크 패킷 캡처를 자동으로 수행하지 않는다.

**사용자 PC의 실제 화면은 AI가 직접 검증할 수 없다.** SmartScreen이나 Defender가 실행을 차단하면 우회하기보다 차단 결과를 기록하고 해당 항목을 BLOCKED 처리한다. 미승인 EXE를 외부에 배포하지 않는다.

## 개발자 Windows PC에서 EXE와 검수 영수증을 함께 만드는 경우

고객 PC가 아니라 **소유자 개발 PC**에서 아직 EXE 후보가 없는 경우, 다음 선택형 명령을 사용할 수 있다. 사전에 Windows, `pwsh`(PowerShell 7), Python, `tkinter`, 고정된 `requirements-offline-build.txt`의 PyInstaller가 설치되어 있어야 한다. 이 명령은 패키지 설치·다운로드·API·고객 소스 전송·Defender 설정 변경을 수행하지 않는다.

```powershell
pwsh -NoProfile -File .\scripts\build_windows_portable.ps1 `
  -OwnerAcceptance `
  -EvidenceDir .\owner-acceptance-private-NEW
```

기존 `dist-windows/CodeCheckerOffline.exe`가 존재하거나 출력 폴더가 이미 있으면 **덮어쓰지 않고 중단**한다. 빌드/합성 스모크 뒤 같은 로컬 EXE에 대해 기존 원클릭 검수를 자동 실행하고 SHA-256과 미완료 수동 게이트 10개를 대조한다. 실패 시 생성된 로컬 EXE/증거를 자동 삭제하지 않으며, 결과는 출시 승인이 아니다. 실제 일반 Windows 검수에는 EXE를 별도 소유자 통제 환경에서 수동 확인해야 한다. EXE나 원문 LICENSE를 공개 GitHub artifact에 업로드하지 않는다.

`-OwnerAcceptance`를 빼면 기존 빌드 명령이 그대로 작동한다. `-EvidenceDir`만 단독 지정하면 오류로 중단한다. 이미 만들어진 후보가 있다면 아래의 기존 한 번에 실행을 사용한다.

## 한 번에 실행

저장소 루트 또는 로컬 검수용 복사본에서:

```powershell
pwsh -NoProfile -File .\scripts\windows_owner_oneclick_qa.ps1 `
  -ExePath .\dist-windows\CodeCheckerOffline.exe `
  -EvidenceDir .\owner-acceptance-20261031
```

매 실행마다 **새로운 폴더**를 지정한다. 기존 폴더는 덮어쓰지 않는다. 스크립트는 아래 파일을 해당 폴더에만 생성한다.

- `readonly-os-observation.json`: EXE SHA, 서명 관찰, Defender 설정 읽기 결과. Defender 서비스가 늦으면 10초 후 `UNVERIFIED`.
- `exe-synthetic-gui.json`: 기존 EXE의 합성 GUI 시작/미리보기→스캔→보고서 완료 기록, Python 불필요. 실제 고객 소스는 사용하지 않는다.
- `owner-preflight.json`: **동일 EXE SHA-256/바이트**와 기존 영수증을 대조한 결과. 수동 체크 항목 10개는 전부 `UNVERIFIED`, 출시 플래그는 `false`.
- `owner-manual-checklist.md`: 실제 Windows GUI 조작, SmartScreen, 네트워크 관찰, Edge/Chrome 한글 PDF, 정확한 8.6.15 Tcl/Tk 원본, 71개 DLL/리소스 권리·NOTICE, 최종 고객 ZIP/지원·환불/사용자 출시 승인 등의 **빈 체크리스트**.

**선택적 Defender 검사**는 명시적으로 `-IncludeDefenderFileScan`을 추가해야 하며, 설치된 Defender의 기존 명령을 읽기 전용 옵션과 함께 실행하고 120초 제한을 둔다. 운영체제 설정·실시간 보호·방화벽을 바꾸지 않으며 명령 결과가 0이어도 안전/무해하다는 인증은 아니다.

입력 EXE가 없거나 UNC/공유 드라이브/링크된 경로, 기존 출력 디렉터리, 영수증 EXE SHA 불일치, 기존 기록의 승인 플래그 위조, EXE 변경 등이 확인되면 성공 요약을 생성하지 않는다. 부분 실패한 임시 폴더의 기존 데이터는 삭제하지 않고 소유자가 확인하도록 보존한다.

## 검증의 경계

`OWNER_WINDOWS_ONECLICK_SYNTHETIC_PASS`는 **보안·라이선스 및 구매자 수락 통과가 아니다**. 실제 사람은 EXE를 수동 실행해 GUI 입력·분석·보고서/삭제, Windows 보호 경고, OS 수준 외부 패킷, PDF 페이지·한글 글꼴을 확인해야 한다. 필요한 고객 LICENSE/NOTICE가 최종 ZIP에 모두 포함되고 정확한 재배포 권리가 입증된 뒤에만 별도의 소유자 출시 승인을 요청한다.

GitHub hosted Windows CI에서는 같은 EXE를 사용해 이 스크립트의 합성 경로를 실행하지만, 출력 JSON·EXE·보고서·LICENSE 원문을 artifact로 업로드하지 않는다. 일반 소비자 Windows 10/11의 SmartScreen 평판과 사람의 시각 수락은 **미검증**을 유지한다.
