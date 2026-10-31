# Code Checker — 동일 EXE 라이선스 검토 진행표 (로컬 전용, 출시 승인 아님)

## 목적 및 설계 선택

고객용 EXE의 CArchive 미분류 구성요소는 실제 소유자·버전·원본 LICENSE·NOTICE 및 재배포 권리를 사람이 독립 확인해야 한다. 기존 `render_notice_review_worksheet.py`는 해시가 묶인 인쇄 검토표를 제공하지만, 71건을 며칠에 걸쳐 검토할 때 각 행의 **조사 상태를 이어서 집계**하는 기능은 없다.

- **A: 인쇄 검토표를 수기로 관리** — 코드·API 비용 0. 그러나 중복 조사·원본과 다른 EXE 결과 혼합 및 진행률 누락 가능.
- **B: 동일 EXE SHA-256과 기존 5단계 메타데이터 검토 큐에 묶인 로컬 JSON 진행표** — 새 패키지·유료 API·외부 접속 0, 구현 유지비 소규모. **B 선택**. 관리하는 것은 조사 단계일 뿐, 승인 상태가 아니다.

## 사용법

본 작업은 EXE, 고객 자료가 없는 5단계 메타데이터 및 기존 `build_notice_review_queue.py`가 생성한 **정확한 EXE의 queue JSON**이 로컬 비동기화 폴더에 존재할 때만 실행한다. 유료 도구, 인터넷이나 관리자 권한은 필요 없다.

```powershell
# 이미 준비된 동일 EXE 검토 큐를 사용. 기존 파일 덮어쓰기 없음.
python -m scripts.track_notice_review --queue .build-windows/notice-review-queue.json --exe dist-windows/CodeCheckerOffline.exe --out .build-windows/private-review-progress-v1.json

# 로컬 JSON 사본에서 해당 archive_entry의 review_stage 필드만 수정.
# 허용 상태: UNREVIEWED, INVESTIGATING, REFERENCES_FOUND, NEEDS_HUMAN_DECISION
# REFERENCES_FOUND는 법적으로 재배포 가능하다는 뜻이 아님.

# 이후 같은 EXE와 동일한 큐에 대해 진행 집계만 생성
python -m scripts.track_notice_review --queue .build-windows/notice-review-queue.json --exe dist-windows/CodeCheckerOffline.exe --progress .build-windows/private-review-progress-v1.json --out .build-windows/private-review-summary-v1.json
```

프로그램은 시작 시 실제 EXE의 SHA-256/바이트를 다시 검사하고, 기존 검토 큐의 정확한 행과 정렬 순서, 큐 SHA-256을 대조한다. 빠진 행·중복 행·이름 바꾸기·잘못된 조사 단계·기존 파일 덮어쓰기·판매 승인 플래그 조작은 오류로 처리한다. 다른 EXE로 바뀌면 기존 조사 상태를 **자동 재사용하지 않는다**.

**인쇄 검토표 자체는 계속 `render_notice_review_worksheet.py`로 생성한다.** 원본 라이선스 전문·EXE·고객 소스·PC 경로는 진행표/집계에 포함하지 않는다. 사람이 독립 검증한 법적 판단은 원본 출처·내부 검수 문서로 따로 보존하고, 원문/토큰/고객 자료를 Public GitHub에 올리지 않는다.

## 명시적 제한 및 출시 차단

`REFERENCES_FOUND` 71개가 되더라도 소유권·배포 권리·NOTICE 충족을 검증한 것이 **아니다**. 결과 JSON의 `customer_release_ready=false`, `license_compliance_certified=false`, `third_party_notice_ready=false` 및 `status=...RETAIL_RELEASE_BLOCKED`는 고정된다. Tcl/Tk 실제 설치 원본과 frozen DLL 출처, 실제 사용자 Windows GUI·Defender/SmartScreen·네트워크·PDF 시각, 고객 ZIP·지원/환불·가격 및 소유자 별도 승인도 모두 필요하다.

GitHub CI에 기록하는 테스트는 가상 EXE의 SHA 바뀜/검토 행 조작/중복 키 차단과 진행표 기능을 확인할 뿐 **사람이 71개 구성요소를 검토했거나 출시 가능하다는 뜻이 아니다**.
