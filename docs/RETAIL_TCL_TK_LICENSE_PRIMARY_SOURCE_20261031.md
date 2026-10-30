# Code Checker — Tcl/Tk official original license provenance (2026-10-31 KST)

> **증거 범위:** Tcl/Tk 공식 upstream Git 소스 `license.terms`의 **원문 위치와 Git blob SHA**를 직접 확인. 본 문서는 Code Checker 실제 frozen EXE에 들어간 바이너리/원본 일치, 법률 준수 또는 고객 NOTICE 승인이 아니다. 원문 전체나 실행파일은 Public GitHub에 복사하지 않았다.

> **2026-10-31 KST 추가 실제 frozen EXE 증거 (과거 '런타임 버전 미확인' 서술보다 최신):** [PR #60 Windows CI 41103150482](https://github.com/hibi89/ai-code-checker/actions/runs/41103150482) head `a000d82bb5e95898300762036a59307cbb875a8e`, GitHub Windows hosted 빌드 EXE SHA-256 `a980db59bfa1093e461914d937f08d26255af1b6a7c2890c57cced340ca5e5ce`에서 실제 interpreter Tcl `8.6.15`, Tk `8.6.15`, `EXACT_FROZEN_RUNTIME_VERSION_RECEIPT_PASS`가 확인됐다. **이 버전은 아래 공식 8.6.15 tagged-source 원문과 검토대상 버전이 대응한다는 사실만 입증**하며, 정확 installed original bytes를 로컬에 가져와 PR61 도구로 대조하거나 DLL owner·동봉 ZIP NOTICE와 라이선스 법적 조건 검토를 통과했다는 뜻은 아니다. 해당 CI는 후속 구성물 분류 assertion 실패로 전체 FAIL, 수정 feature [PR #60](https://github.com/hibi89/ai-code-checker/pull/60) head `b8c43e1` CI 대기. 공식 license byte verifier [PR #61](https://github.com/hibi89/ai-code-checker/pull/61)은 `main`에 merge SHA `00fcfd1`로 반영됐지만 해당 EXE와 실제 원본 2개를 넣어 수행한 실검증은 **미실시**.

> **2026-10-31 KST 새 정확 EXE 실증 근거:** [PR #60 Windows CI 41104103291](https://github.com/hibi89/ai-code-checker/actions/runs/41104103291), source feature `b8c43e1e0210af245b9fd6768544c9aab82925b5`, Windows candidate `CodeCheckerOffline.exe` SHA256 `f516686d2f6d9220260c1e2f0f175fda3ef80ea0d2887aac5f21d6da234a2d5f`. 실제 Tk interpreter Tcl patchlevel=8.6.15, Tk patchlevel=8.6.15, runtime receipt & EXE hash validator **PASS**, Python build installed Tcl original=0/Tk original=1, archive metadata 분류 CArchive 997+PYZ 143, 미분류 71개, 원본/NOTICE review queue **PASS(계상만)**. 실제 EXE+공식 tagged Tcl/Tk 두 원본을 로컬 검사기에 함께 입력한 byte comparison/권한·NOTICE 법적 확인은 **하지 않음**; 공급자 제공 DLL provenance·customer Win10/11 실기기·판매 승인도 BLOCKED. [PR #61](https://github.com/hibi89/ai-code-checker/pull/61) checker + [PR #60](https://github.com/hibi89/ai-code-checker/pull/60) frozen receipt 모두 main 병합 완료; 출시는 여전히 차단.

## 1. 확인된 공식 라이선스 원본

| 공식 프로젝트/태그 | 고정 소스 | Git blob SHA (SHA-1) | 공식 태그 commit |
|---|---|---|---|
| [Tcl 8.6.15](https://github.com/tcltk/tcl/blob/core-8-6-15/license.terms) | `tcltk/tcl@core-8-6-15:license.terms` | `d8049cd9e7ca055f7e584a76f88861a294b30c9c` | `1a98213e55128c8a2136379fedfaef0c8e15320b` |
| [Tk 8.6.15](https://github.com/tcltk/tk/blob/core-8-6-15/license.terms) | `tcltk/tk@core-8-6-15:license.terms` | `01264352c87ca7e34771bd1ee18bed5201ef139f` | `3c4a7176319e29a790ff82c80e3c3ff74f523ffb` |
| [Tcl 8.6.18](https://github.com/tcltk/tcl/blob/core-8-6-18/license.terms) | `tcltk/tcl@core-8-6-18:license.terms` | `d8049cd9e7ca055f7e584a76f88861a294b30c9c` | `515167c897a7c8066abfbd71e8fe7bd8bf3569de` |
| [Tk 8.6.18](https://github.com/tcltk/tk/blob/core-8-6-18/license.terms) | `tcltk/tk@core-8-6-18:license.terms` | `01264352c87ca7e34771bd1ee18bed5201ef139f` | `6dbe68819aac4a22f6f7a143133ce26c5e8d2b05` |

공식 Tcl과 Tk는 **서로 다른 원문**(SHA 상이)이다. 직접 확인한 **두 릴리스의 Tcl끼리 및 Tk끼리**는 원문 Git blob이 각각 동일했다. 중간 버전이나 타 배포판까지 동일하다고 추론하지 않는다. Git blob SHA는 **Git 객체의 SHA-1이며 SHA-256이 아니다**. 원문 파일 그대로 재검증할 때 `git hash-object --no-filters -- <license.terms>`를 사용하되 바이트·개행 변형이 없어야 한다.

- [공식 Tcl/Tk Licensing Terms](https://www.tcl-lang.org/software/tcltk/license.html): 핵심 Tcl/Tk 버전에 적용되는 상업적 사용·복사·수정·배포 허가. 기존 저작권 고지를 유지하고 통지문을 **원문 그대로** 배포에 포함해야 한다.
- [공식 Tcl/Tk 배포 설명](https://www.tcl-lang.org/software/tcltk/): **특정 배포판에 포함된 개별 확장/네이티브 구성요소는 각각 확인**해야 한다.
- 별도의 설치 원본 후보: 이전 Windows CI [41098482393](https://github.com/hibi89/ai-code-checker/actions/runs/41098482393)에서 CPython 1/Tcl 0/Tk 1/PyInstaller 1. **Tcl 원본을 설치 경로에서 발견하지 못했다는 뜻**이지 공식 1차 소스가 존재하지 않거나 Tcl의 상업 사용이 불허된다는 뜻은 아니다.

## 2. 실제 EXE에 적용하는 수동 판단 절차

1. **동일 EXE 고정:** 소스 commit SHA, 빌드한 EXE 자체 SHA-256, Python 및 Tcl/Tk 런타임 버전을 하나의 영수증으로 묶는다. 이 부분은 [PR #60](https://github.com/hibi89/ai-code-checker/pull/60)의 pending Windows EXE version receipt가 완료돼야 실행 검증된다.
2. 버전이 확인되면 **해당 정확한 upstream 릴리스 태그**의 Tcl과 Tk `license.terms`를 각각 원문으로 확보한다. 여기서 확인한 8.6.15/8.6.18만을 무조건 현재 번들 원본으로 간주하지 않는다.
3. 각 원문의 바이트, 태그·commit, Git blob SHA, 대상 바이너리와 버전, 수정·추가 라이선스 및 NOTICE 조건을 **인간 검수**한다. 릴리스 라이선스와 설치 벤더 바이너리가 정확히 대응하지 않는다면 '미검증' 유지.
4. 실제 납품 ZIP의 원문 LICENSE/NOTICE와 바이너리 SHA를 확인한다. **Tcl 원본만 있다고 나머지 71건을 허용 처리하지 않는다.** 과거 명칭 미분류 71개는 불법 구성품을 의미하는 숫자도 아니다.
5. 소비자 Windows GUI 실사용, SmartScreen/Defender, OS 패킷, 한글 PDF 육안, 환불·지원 안내 및 판매 승인까지 충족해야만 판매 판단.

## 3. 확인/미확인

- **확인:** 공식 Tcl/Tk 태그·원문 파일·Git blob SHA 4개, 상업 이용 허가와 통지 의무.
- **미확인:** 현재 bundled Tcl/Tk 버전·원본 DLL 출처·배포판 수정·실제 고객 NOTICE·미분류 71개 검수.
- **CI:** [PR #60 일반 41100173018](https://github.com/hibi89/ai-code-checker/actions/runs/41100173018)과 [Windows 41100173161](https://github.com/hibi89/ai-code-checker/actions/runs/41100173161)는 문서 기준 시점 **queued**, 기능 병합 불가.
- **출시:** `CUSTOMER_RELEASE_READY=False`; 고객 EXE·LICENSE 원문 공개 배포 미승인.

이 원본 위치 확인은 기존 `docs/RETAIL_RELEASE_GATE_CHECKLIST_20261030.md`의 원본 위치 조사에 대한 구체적 증거다. 새 라이선스 판정이나 제품 범위 변경이 아니다.
