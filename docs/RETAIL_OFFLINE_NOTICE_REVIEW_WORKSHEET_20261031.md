# Code Checker — EXE별 71개 LICENSE/NOTICE 검토표 작성 (오프라인, 승인 아님)

기존 Windows CI에서 관찰된 **미확인 아카이브 항목 71개**를 실제 EXE와 동일한 SHA-256로 묶어 인쇄 가능한 HTML 검토표로 만들기 위한 기능이다. 숫자 71은 최근 후보 빌드의 관찰값일 뿐 모든 버전에 고정되지 않는다.

## 목적과 적용

- 기존 `audit_frozen_exe` → `map_frozen_licenses` → `reconcile_native_build` → EXE TOC/PKG TOC 5단계 증거를 동일 실행 파일과 **다시 검증**한다.
- 미확인 항목을 검토 우선순위별 세 묶음으로 배치한다. ① 분석 TOC의 고유 출처 연결이 없거나 실제 바이트 불일치 ② 소스 후보는 있으나 바이트 동일성 미확인 ③ 기록 소스와 바이트 동일. **③도 라이선스·재배포 권리 확인 전에는 미승인이다.**
- 각 항목에는 EXE 내부 상대 이름, 원래 미분류 상태, 관찰된 경로·바이트·TOC 증거, **소유권/버전/원본 LICENSE/NOTICE/검수자 빈칸**이 있다. 법적 판단·서명은 사람이 한다.
- 결과는 로컬 `.html` 한 파일이고, 네트워크/CDN/스크립트/원본 LICENSE 전문/실행파일/개인정보 저장이나 GitHub 업로드가 없다. CSS는 인쇄용 A4 가로. 브라우저에서 직접 열어 필요하면 인쇄/PDF로 저장한다.

## 생성 (검수 PC에서 기존 EXE가 준비된 경우)

PowerShell에서 저장소 루트 기준 아래 명령을 실행한다. 각 `.json`은 **같은 한 개의 빌드**에서 나온 원래의 로컬 전용 증거여야 한다.

```powershell
python -m scripts.render_notice_review_worksheet `
  --audit .build-windows/frozen-exe-evidence.json `
  --mapping .build-windows/ownership-candidates.json `
  --native .build-windows/native-provenance.json `
  --exe-toc .build-windows/exe-toc-evidence.json `
  --pkg-toc .build-windows/pkg-toc-evidence.json `
  --exe dist-windows/CodeCheckerOffline.exe `
  --out .build-windows/manual-owner-notice-review.html
```

입력 중 누락·링크·변조·너무 큰 파일, EXE 해시 불일치, 분류 회계 불일치, 승인 상태로 조작된 JSON, 기존 출력 파일 덮어쓰기가 발견되면 결과를 쓰지 않고 실패한다. 생성된 HTML도 반드시 `NOT APPROVED` 및 `Release remains blocked`를 표시한다.

## 검수 후 무엇이 남는가

- 미분류 파일의 **정확한 실제 저작권 주체·버전·재배포 의무**와 원본 LICENSE/NOTICE를 확인하고 기록한다. EXE 빌드 소스 경로나 같은 바이트만으로 권리를 인정하지 않는다.
- 앞서 만든 `scripts.verify_upstream_tcl_tk_license`로 해당 EXE의 실제 Tcl/Tk 8.6.15 패치레벨과 Tcl 및 Tk **각각 별도의 공식 원본 파일**이 바이트 단위로 일치하는지 로컬에서 대조한다. 원본 자동 다운로드나 업로드는 하지 않는다.
- 구매자 일반 Windows 10/11 GUI·SmartScreen/Defender·OS 네트워크 패킷·Chrome/Edge 한글 PDF를 실기기에서 별도로 수락 검증한다. 결과와 최종 납품 ZIP을 고정해 사용자에게 출시 승인을 받는다.

검토표 생성은 미분류 71건의 **목록 작성/업무 배분을 개선할 뿐, 수동 권리 검수 건수를 임의로 줄이거나 판매 가능 상태를 만들지 않는다.** GitHub hosted synthetic CI PASS도 일반 고객 PC 통과를 의미하지 않는다.

설계 판단: `A` 원본/권리를 자동 판정하는 방식은 정확성·법적 리스크 때문에 부적절. `B` 기존 다섯 단계 증거를 재사용해 오프라인 인쇄 검토표로 전환하는 방식은 추가 API 비용 0, 기존 구조 재사용, 허위 승인 차단이므로 채택.
