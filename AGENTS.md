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
8. Complete a change with tests, branch SHA verification, release check when relevant, and updated STATUS.md and HANDOFF.md. Do not claim a working Windows EXE without Windows testing.
9. Any external analyzer is optional, version-pinned, license-checked, configured without executing project scripts or untrusted plugins. Never execute customer-provided code.
10. Product direction and staged delivery were owner-approved 2026-10-26; publish the approved docs on `main` after checks. Source changes are separate feature branches only. No release until gates pass.

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
