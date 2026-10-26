# Code Checker v2 — Requirements / Owner-Approved Product Direction

Date: 2026-10-26 KST. Status: OWNER-APPROVED GOAL AND MVP-FIRST PROCESS. New v2 implementation, GUI, binaries and launch remain incomplete; commercial release and paid/permission/security changes require separate approval.

## Product decision
- Principal product: portable customer-operated **offline Windows code-risk checker**, one-time purchase, unlimited local runs, no recurring per-run vendor fee, no API key required for core features.
- Deliverable: executable application and locally generated self-contained HTML report (save as PDF using system/browser Print to PDF); Markdown optional.
- Secondary product: seller-run verified diagnostic report, optional, explicitly scoped and priced separately.
- Keep existing CLI and Gemini integration as a separate optional mode, **off by default**. BYOK Gemini usage may incur model charges and is NOT zero-cost. No implicit remote fallback.
- Do not advertise independent 8-agent review: existing repository has one model call plus local pattern checks.
- Preserve the existing report-only plan as historical baseline. v2 offline software becomes the approved primary product design; historical Gemini CLI must not be represented as the new completed product.

## Required behaviors for first release
1. Select directory, individual source file, or ZIP. Display what was analyzed and excluded before scanning. Protect against symlinks, ZIP escape/bombs, oversized files and secrets.
2. Default offline: no customer source execution, no dependency install, no external network requests, no telemetry. Do not trust project-provided configuration/scripts/plugins.
3. Deterministic checks: start with existing Python AST/safe pattern engine; use Python Ruff and Bandit only as separately validated optional integrations. JS/TS syntax or security checks must never be presented as thorough before a verified adapter exists.
4. Output evidence: file/path/line and observed fact, recommendation, rule ID, severity and coverage; separate confirmed deterministic findings from candidate risks and unknowns.
5. Report missing coverage, parsing failures, skipped files, unsupported languages, timeouts and result quality without declaring clean when incomplete.
6. Unlimited repeat execution for purchaser; no activation server, login, API quota or forced subscription.
7. Generate HTML report in a local output directory, self-contained, escaped content, no tracking/image CDNs, no external font dependencies; Markdown retained. PDF via local system print initially. No automatic code changes.
8. Human-review add-on must be clearly identified as a different product. High-risk severity needs actual contextual verification; a matching line excerpt is not proof.
9. Windows-friendly portable distribution is desired. First customer-ready distribution requires Windows Defender/SmartScreen, package scan, startup/UTF-8 paths, browser printing and clean-device checks. Unsigned EXE may produce warnings or be blocked; free packaging does not guarantee smooth installation.
10. Preserve privacy and complete deletion paths; optional log may record counts and durations only, without original code/response.

## Scale/coverage policy
- REMOVE old 500-line cap as a software product licensing/usage restriction.
- Benchmark target only: at least 200 supported source files and multi-megabyte synthetic folders for a responsive offline scan; number and size limits remain unpromised until measured. Existing CLI remains limited to 50 files / 512 KiB until changed and tested.
- Traversal != analysis. Every run reports (discovered/scanned/skipped/unsupported/failed), languages, analyzers and coverage. No claim of full repository audit based on file traversal.
- Large inputs: bounded resources, progress reporting, explicit partial output or fail closed as required; cancellation must not corrupt originals.
- Python analysis quality first; JS/TS support as separately verified P1 milestone for target buyer needs.

## Acceptance gates
A. Current CLI and 46 documented unit tests retained; no regression.
B. Local offline E2E can scan both vulnerable and safe synthetic fixtures without API key/network; expected findings present; key false positives documented and controlled.
C. Distinguish completed vs partial scan, successful process vs verified deliverable approval.
D. Windows packaged application works without local Python installation; tests include clean Windows or equivalent evidence; otherwise status unverified.
E. HTML/Markdown report checks source mapping, escaping, printing and offline behavior.
F. Licensing/attribution audited for any bundled dependencies/rules. Do not bundle Semgrep registry rules without explicit redistribution/service-right verification.
G. Customer source isn't uploaded during default run, verified via network observation/test, not just documentation.
H. Pricing/launch requires validated time-to-deliver and realistic support/return-policy review.

## Explicit non-goals in offline MVP
- Independent 8-agent CODE COUNCIL, code auto-fix, comprehensive vulnerability certification, real-runtime analysis, SaaS backend, customer login, online license server, automatic remote updates, proprietary DRM.
- A guaranteed permanent zero operating cost including developer labor, payment fees, Windows code signing or user computer usage.

## TXT, ZIP, and multi-file ingest (design revision 2026-10-26)

- Official first-class inputs: ZIP, raw TXT, explicitly delimited multi-file TXT, folder, and paste. All feed ONE offline-safe normalized file manifest.
- Raw TXT is a single source; v2 asks for/infers language cautiously, retaining original line positions. Current CLI already accepts TXT and ZIP, but local Python AST only executes for `.py`/`.pyi`, **not** generic TXT. Multi-file TXT reconstruction is not implemented.
- Multi-file TXT uses `===== FILE: relative/path.ext =====` section markers and strict path/line mapping, malformed content fails visibly. ZIP retains relative paths, blocks dangerous entries and never executes code.
- Every result lists detected, eligible, scanned, skipped, unsupported and failed entries; neither TXT nor ZIP may silently truncate or report a partial scan as complete.
- 500-line limit remains removed as v2 product policy; >=1,200 and >=12,000-line synthetic fixtures are mandatory before publishing scale guarantees. Operational file/byte limits remain until benchmarked.
- Details and synthetic acceptance cases: [INPUT_SPEC_V2.md](INPUT_SPEC_V2.md).

## Approved staged delivery sequence
- [FINAL_PRODUCT_BLUEPRINT.md](FINAL_PRODUCT_BLUEPRINT.md) is the target; [MVP_3DAY_ROADMAP.md](MVP_3DAY_ROADMAP.md) controls implementation order and acceptance gates.
- Phase 1: 3 focused development days for the working, offline, source-safe MVP with TXT/ZIP → static rules → local report and basic Windows interaction. Not all final-product features must be complete within 3 days.
- Phase 2: perform explicit gap review against the final blueprint and fill missing product functionality.
- Phase 3: comprehensive stability/security/performance/licensing/privacy and accuracy verification, preserving baseline safety in all phases.
- Phase 4: Windows packaging/customer-acceptance verification and Kmong commercialization. No release before gates.
