> **[CODE_CHECKER_P95_WORK_MARKER_LOCK_20261112 — 사용자 최신 직접 지시]** AI Code Checker의 현재 목표는 **검증된 95%**. 중앙 크몽 브랜치 완성률표에서 해당 제품명 옆 `**[작업중]**`를 목표 달성 전 절대 지우지 않는다. 미달(90% 잠정)이나 채팅 종료·일시 보류 자체는 표시 제거 사유가 아니며, HOLD·실기기/권리 미검증을 별도 명시한다. 95% 도달과 실제 근거를 검증한 뒤에만 표시를 해제한다. 기존 ‘작업 전환/종료 시 즉시 해제’ 일반 규칙에 대한 **이 제품 P95 목표의 최신 사용자 예외**다. 타 제품 표식은 보존한다.

> **[KMONG_WORK_IN_PROGRESS_20261112 — 크몽 필수 지침 / 소유자 승인]** 이 저장소에서 크몽 상품 또는 육성 후보 작업을 담당하면 새 채팅·`ㄱ` 재개 시 이 `AGENTS.md`를 반드시 읽는다.
> - **실제 상품 개발·수정·테스트/검증 착수 시 즉시:** 중앙 `hibi89/hackathon-command-center-2026`의 `kmong-productization` 브랜치 [최종완성률 및 작업 현황 표](https://github.com/hibi89/hackathon-command-center-2026/blob/kmong-productization/docs/audits/KMONG_16_CURRENT_20261111.md)에서 **담당 제품명 바로 옆에 `**[작업중]**`**을 작성하고 실제 GitHub 커밋을 확인한다. 같은 저장소에 상품이 여럿이면 현재 담당 상품만 표시. 활성 16종 외 PREP·FFAX·Factory AX 등의 후보는 같은 문서의 별도 후보 작업 상태 표에서 표시한다.
> - **검증된 목표 완성률 달성 / 종료 / 중단 / 보류 / 다른 상품으로 작업 전환 시 즉시:** 자신의 `[작업중]`만 제거해 GitHub 커밋을 확인한다. 다른 채팅이 작업 중인 표식은 임의 변경하지 않는다. 중앙 최신 HEAD를 먼저 읽고 동시 갱신을 보존한다.
> - 중앙 기록 쓰기 실패 시 제품 `STATUS.md`·`HANDOFF.md`와 답변에 **`KMONG_HUB_SYNC_PENDING`**을 기록한다. 자동 실시간 동기화가 없고, 표식은 완성률 상향·판매/배포 승인이나 작업 자동 실행을 의미하지 않는다. 실제 검증 근거 없이는 숫자를 변경하지 않는다.

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
