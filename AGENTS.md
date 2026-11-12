> **[OWNER-FINAL-BLUEPRINT-100 | 2026-11-13 KST | 사용자 확정·전체 저장소 최우선]** 제품 공식 **최종완성률은 사용자 확정 최종설계도 전체 100%**를 분모로 한다. 총괄·작업자는 임의로 설계를 축소하거나, 해커톤용 MVP·합성 테스트·CI PASS·85/95% 내부 마일스톤을 최종완성률로 혼용할 수 없다. 최종설계 요구사항 ID→코드→정확 SHA 실제 검증→미구현/미검증 및 사용자 승인 가중치를 추적해 계산한다. 근거·가중치가 미비하면 **최종설계 기준 UNASSESSED(재산정 대기)**로 표시하고 종전 수치는 **과거 내부 마일스톤**으로 보존한다. 크몽 관련 완성률은 해총 `kmong-productization` 원장에 동기화한다. [작업중]/등록완료/RELEASE HOLD 등 기존 별도 상태는 보존한다. 상충하는 구형 진척률 산정 지시보다 우선. [공통 전체 규칙](https://github.com/hibi89/hackathon-command-center-2026/blob/kmong-productization/docs/strategy/FINAL_BLUEPRINT_COMPLETION_STANDARD_20261113.md). 정책 커밋은 코드 수정·성공 테스트·제품 출시·재산정 완료를 의미하지 않는다.

> **[KMONG_WORK_TARGET_GATE_20261112 | 사용자 최신 확정 | 필수 작업 규칙]** 이 저장소에서 크몽 상품·육성 후보를 작업하는 모든 AI 담당자는 새 채팅·`ㄱ` 시작 시 이 문구를 읽고 적용한다.
> - 실제 개발/수정/테스트 착수 즉시 [해총 크몽 최종완성률·후보 상태표](https://github.com/hibi89/hackathon-command-center-2026/blob/kmong-productization/docs/audits/KMONG_16_CURRENT_20261111.md)의 **해당 상품명 옆에 `**[작업중]**`을 표시하고 GitHub 커밋**한다. 확정 단계 목표(예: 95%)와 검증 기준을 제품 STATUS/HANDOFF에 남긴다.
> - **목표 완성률 달성 전에는 [작업중]을 삭제하지 않는다.** 일시중단·종료·보류·다른 제품 전환·담당 채팅 변경도 삭제 사유가 아니다. 예전 '전환·중단 시 삭제' 지시는 폐기한다.
> - **검증된 목표치에 도달한 뒤에만** 기능 SHA·PASS/FAIL/SKIP·미검증을 기록하고 자기 표시를 제거·커밋한다. 목표 하향/변경으로 표식 제거 시 사용자 명시 승인 필요. 다른 담당자 표시·기존 수치·RELEASE HOLD 보존.
> - 표식은 목표 미달 상태를 의미하며 **실시간 실행 증명은 아니다**. 허브 최신 HEAD 확인 후 안전하게 반영, 실패 시 `KMONG_HUB_SYNC_PENDING` 기록. 자동 동기화 없음. 크몽 외 작업에는 표시 불필요.

> **[CODE_CHECKER_POLICY_20261031 | 2026-10-31 사용자 최상위 개발 가속 지시 | 코드체커 총괄 직접 수신]** 최신 [해총 공통 운영 정본](https://github.com/hibi89/hackathon-command-center-2026/blob/main/docs/strategy/20261031_OWNER_BACKEND_FIRST_48H_EXECUTION_PROTOCOL.md)을 적용. **2026-10-30 사용자 재개 결정이 기존 10/28 '개발 대기' 문구보다 우선**한다. 최종 `FINAL_PRODUCT_BLUEPRINT.md` 제품/기능·스택(Python 3.11+, AST 정적 분석, Tkinter, 로컬 보고서, 선택 PyInstaller)·구성 프로그램/레포·입력→분석→증거→보고서/GUI→오류·개인정보 보호 계약·완료조건을 개발 전 짧은 `PRODUCT_AND_INTEGRATION_BASELINE`으로 대조(이미 승인된 설계 반복 금지). 코드체커는 **오프라인 Windows 제품**으로 '백엔드 우선'은 새 서버/유료 API 도입이 아닌 로컬 검사 엔진·정확성·파일 안전·보고서 생성 코어와 실제 사용자 실행 경로를 먼저 완성한다는 뜻. 한 번의 `ㄱ`에 핵심 기능 여러 개를 묶어 구현→초기 로컬 스모크→독립 feature 브랜치 커밋/PR→CI run/SHA 기록 후 안전한 다음 개발 병행. `main` 릴리스 검증·회귀/실Windows·Privacy·Defender·SmartScreen·원본 LICENSE/NOTICE·소유권 확인은 결코 건너뛰지 않는다. 현재 확정된 Tcl 원본/미분류 번들·실사용 QA 차단은 그대로 유지. 48h 코어 집중 목표 ≠ 판매 승인/검증 완료 주장; 기존 Gemini v1·소스/원본·개인정보·무네트워크 정책 보존. **본 공시는 문서-only: 코드·CI·실기기 테스트·EXE 배포 수행 아님.**

> **2026-10-28 해총 전 저장소 최상위 공통 운영 공지 (소유자 승인):** [개발 가속·로컬검증·병목제거 통합 정본](https://github.com/hibi89/hackathon-command-center-2026/blob/main/docs/DEV_ACCELERATION_AND_VERIFICATION_20261028.md) 확인. 현 시점 활성은 **KIC(+DL)·PayPal·UGREEN·LA 4개**만이다. 이 프로젝트는 **임시 개발 대기**(폐기·기존 기록 삭제 아님)로, 소유자의 재개 지시 없이 `ㄱ`만으로 신규 개발·CI·배포를 진행하지 않는다. 활성 프로젝트 일반 기능 구현은 **GPT-6 Instant**, 최초 설계·난제·해총 독립검수는 높은 추론. 파일 단위 GitHub 반복·다수 상태 문서 갱신·동일 SHA 반복 조회를 줄이고, 기능 단위 검증/정확한 PASS·FAIL·SKIP·커밋 SHA만 보고한다. 기존 제품 설계 동결, 외부 승인, 보안·고객데이터/원본·출시 게이트는 그대로 유지. 이 공지는 운영 통지이며 기능 완성 선언이 아니다.

> **2026-10-30 KST 사용자 재개 지시 (10/28 일시 대기 공지보다 최신):** Code Checker의 **크몽 판매용 오프라인 Windows 제품 개발을 다시 활성화**했다. Codex 사용량을 아끼고 GPT-6 해총이 직접 구현/검증한다. 해커톤과 기존 Gemini v1을 보존하고, 실제 사용자 Windows·라이선스·출시 게이트는 그대로 적용한다. 새 채팅은 최신 main/CI와 [CODE_CHECKER_RESUME.md](CODE_CHECKER_RESUME.md) → HANDOFF/STATUS 순으로 확인하라. `ㄱ` 은 기존 승인 범위의 다음 개발 단위 진행이지 EXE 공개 배포·유료 API·보안 설정 변경·판매 승인 신호가 아니다.


# Code Checker — Agent Operating Rules

## Source of truth and resume order
At the start of each new conversation, read CODE_CHECKER_RESUME.md -> HANDOFF.md -> STATUS.md -> AGENTS.md -> REQUIREMENTS.md -> FINAL_PRODUCT_BLUEPRINT.md -> MVP_3DAY_ROADMAP.md -> architecture and implementation. Compare documentation against code and the checked production state; latest verified evidence wins.

## Ownership
ChatGPT is the design/implementation/test/review lead. The owner approves monetized expenses, external code uploads, permissions/security changes, production release, repository visibility changes, and material scope changes. The owner's one-character signal `ㄱ` means continue the next already approved work package. No implicit API usage is authorized by this signal.

## Priority
1. Preserve original code, customer files, existing behavior, and user time.
2. Offline-first, zero required recurring API/service cost for purchaser and seller (excluding human time, hardware, initial build and optional paid service).
3. Clearly distinguish implemented, mocked/offline-tested, API-verified, user-accepted, and unverified.
4. Keep GitHub as the code/version baseline; no secret keys, .env, raw customer code, original model responses, or identifiable production customer reports in the repository.
5. Before coding, compare at least two designs with costs, quality and operations; the owner has approved the offline product direction and 3-day MVP-first implementation process. Any cost/permissions/security/data exposure and material scope change still requires separate prior approval.
6. Before any risky change: capture branch/SHA, backup/revert route, actual test plan, security risk, licenses. Do not force push.
7. Fail closed for incomplete scans and reports, and avoid fabricated success. No automatic paid API retries.
8. Complete a change with focused tests and exact-head integration verification. Update only materially affected handoff/status documentation, not all docs for every small patch. Do not claim a working Windows EXE without Windows testing.
9. Any external analyzer is optional, version-pinned, license-checked, configured without executing project scripts or untrusted plugins. Never execute customer-provided code.
10. Product direction and staged delivery were owner-approved 2026-10-26; publish the approved docs on `main` after checks. Source changes are separate feature branches only. No release until gates pass.

## Fast-track development protocol (owner directive 2026-10-28)
- Optimize verified working features, not commits/docs/test counts. Batch related source, focused regression and essential handoff in one feature commit. Run focused checks first; run full regression at merge/release checkpoints.
- Inspect HEAD/PR/CI once at the start, reconfirm concurrent updates before non-force merge; do not repeatedly poll the same completed job. Preserve other owners' branches, originals and rollback paths.
- Keep AGENTS for durable policy, STATUS for verified state, HANDOFF for resume steps, README for instructions. Do not update three documents after every tiny patch; record only material changes.
- The local Windows one-command check is: powershell -NoProfile -ExecutionPolicy Bypass -File .\verify_local.ps1. Use -Quick for minimal synthetic smoke; optional -IncludeGuiSmoke exercises GUI/PDF fixtures. JSON evidence is created with a unique temporary filename. No installs, paid APIs, customer-source execution/upload, system security changes or DB mutations.
- Current bottlenecks (QUALITATIVE, no time-share measurements): (1) separate source/docs commits and remote lookups => one atomic feature commit and fewer reads. (2) 3 OS × 5 Python versions plus audit for each push => focused local tests, full matrix once for integration. (3) fragmented owner-PC test commands => reproducible single safe script. Do not remove mandatory CI, source confidentiality, human release gates or approvals.
- Resume by finding the next meaningful blueprint gap, proving a core user workflow, then reporting only changed function, exact SHA PASS/FAIL/SKIP, bottleneck action and next goal. Clean customer Windows, SmartScreen, OS packet capture, Korean PDF visual and original third-party LICENSE/NOTICE/legal + owner release consent remain unverified until actually done.

## Change gates
- Public GitHub branch is *not confidential*. Commercially sensitive future packaging code and customer data must not be committed here.
- Any repository added for proprietary distribution needs prior authorization; never assume a public branch can be private.
- CI is a quality signal, not actual customer operation verification.
- No hidden telemetry, external upload, account, subscription, or hard-coded external URLs in the offline product.
- Real API checks require owner permission, a verified account tier/data policy, clear spend ceiling, and safe synthetic input.

## Project intent
Deliver a customer-operated offline code-risk checker that generates evidence-led local reports, with optional seller-assisted human-reviewed report service. It is not equivalent to an AI council, runtime test, security audit certification or zero-defect warranty.

## Owner-approved delivery sequence (2026-10-26)
1. Build working offline v2 MVP in 3 focused development days (target, not a verified deadline or permission to bypass input safety).
2. Compare implementation to FINAL_PRODUCT_BLUEPRINT.md and complete missing product features incrementally.
3. Run broad security, robustness, privacy, compatibility and accuracy hardening before commercial delivery.
4. Publish on Kmong only after clean-device executable/customer delivery checks and approval.
5. Report each stage using verified SHA and PASS/FAIL/UNVERIFIED; no false claim of finished software.

## Exact chat-resume trigger (owner authorized)
When a user starts a new conversation with **`[코드체커 깃헙 확인해]`**, this means: read [CODE_CHECKER_RESUME.md](CODE_CHECKER_RESUME.md), inspect current GitHub main/branches/PR/CI, then **start the next already-approved implementation unit immediately**. As of 2026-10-26 Days 1 and 2 are merged. Day 3 Windows desktop MVP is implemented on `feature/windows-portable` PR #4, with Windows EXE synthetic smoke CI evidence. Confirm actual PR #4 and final CI; merge if green, then continue blueprint gap analysis and clean-device GUI/security verification as the next approved work unit. Do not stop at a generic status summary or re-request decisions already documented. Re-check reality, use safe source-preserving branches, tests, PR, handoff updates. Never infer permission for paid Gemini calls, customer data upload, creating a private repo, repository rights changes or public commercial release.
