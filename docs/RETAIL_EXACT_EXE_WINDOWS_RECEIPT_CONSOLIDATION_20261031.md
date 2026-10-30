# Code Checker — 동일 EXE 증거 통합 검증 (판매 승인 아님)

고객용 Windows 제품 출시 검수의 반복적인 수집/해시 대조 작업을 줄이기 위해, 기존 4종 독립 영수증을 **똑같은 실행 파일 SHA-256/바이트 크기**로 검증한 로컬 JSON 요약을 만드는 단계다.

## 기존 방식과 선택

- **A. 기존 검수 기록을 따로 확인:** 구현 추가 비용 0, 그러나 서로 다른 EXE 빌드·Windows 호스트의 receipt가 섞여도 수동으로 놓칠 위험이 있다.
- **B. 각 단계의 원래 검증 함수들을 재사용해 통합:** 추가 라이브러리/API·계정·원격 호출 0, 반복 해시 계산 비용은 있지만 실제 EXE와 매번 재검증해 데이터 혼합 사고를 차단한다. **B 채택.**

기능은 `scripts/consolidate_windows_retail_evidence.py`다. 신규 증명이나 승인 로직을 만들지 않고 이미 검증한 다음 계약을 다시 적용한다.

1. `scripts/windows_acceptance_contract.py`: OS·Defender 설정·서명 관찰 영수증. **바이너리 신뢰성 승인 아님.**
2. `scripts/windows_local_exe_smoke_contract.py`: 두 내장 합성 모드에서 GUI 시작→미리보기→스캔→보고서가 정상 종료된 기록. **사람이 GUI 버튼을 누른 수락 검증 아님.**
3. `scripts/runtime_version_receipt.py` (선택): 동일 EXE가 작성한 Tcl/Tk 패치레벨 관찰. **정확한 라이선스 파일/원본 DLL 검수 아님.**
4. `scripts/windows_defender_scan_contract.py` (선택): 선택적으로 실행했던 Defender 명령과 EXE 무결성 관찰. **malware-free·SmartScreen·고객 PC 보호 통과 아님.**

## 실행

검증 PC에 Python이 있을 때, **이미 독립적으로 수집한 같은 EXE의 receipts**로 실행한다. 이 명령은 EXE/백신 스캔을 새로 실행하지 않으며 외부 API나 원본 코드를 읽지 않는다.

```powershell
python -m scripts.consolidate_windows_retail_evidence `
  --exe dist-windows/CodeCheckerOffline.exe `
  --readonly .build-windows/windows-acceptance-readonly.json `
  --smoke .build-windows/windows-local-exe-smoke.json `
  --runtime .build-windows/runtime-version-receipt.json `
  --defender .build-windows/defender-custom-scan.json `
  --out .build-windows/exact-exe-retail-preflight-summary.json
```

`--runtime` 및 `--defender`는 해당 수집본이 없으면 생략 가능하다. 생략 시 각각 `NOT_PROVIDED`로 기록하고 **검증하지 않았다고 표시**한다. 기존 파일을 덮어쓰거나 링크 파일을 신뢰하지 않는다. 결과에는 EXE 경로·PC 사용자명·고객 코드·토큰·원본 LICENSE 전문·Defender 검색 내역을 보관하지 않는다.

출력의 `receipt_evidence`는 원래 영수증 형식·현재 EXE 해시 정합성 및 합성 기능 기록만 요약한다. 8개 `human_release_gates`는 **모두 `UNVERIFIED`**, `real_buyer_pc_test_certified`, `malware_free_certified`, `legal_notice_approved`, `customer_release_ready` 모두 `false`다.

## CI와 사용자 PC를 구분

GitHub Windows hosted runner에서 앞선 4개 수집 단계와 함께 검증기를 실행하지만, 생성된 JSON과 EXE·LICENSE는 CI artifact로 업로드하지 않는다. CI PASS는 **한 실행 파일에 연결된 로컬 메타데이터가 일치한다는 뜻**이다. 깨끗한 일반 Windows 10/11에서의 사용자 GUI 조작·SmartScreen 평판·OS 패킷·한글 PDF 육안, 71건 구성요소 소유권/NOTICE, 공식 8.6.15 Tcl/Tk 원본 바이트 로컬 대조와 고객 ZIP·지원/환불/가격·실제 배포 승인은 별도로 필요하다.

검증 실패 시 새로운 출력을 남기지 않고 nonzero 종료한다. 동일 EXE가 아니면 기존 JSON의 SHA를 고쳐 맞추지 말고 실제 동일 빌드에서 다시 수집한다.
