# CODE CHECKER v2 — Phase 2 Final Blueprint Gap Matrix

Updated 2026-10-26 KST. Baseline **main merge `f0c257058f43298167e6777f315db01ae294fd86`**, Day 3 PR #4 merged. This is an evidence-based engineering gap audit, NOT certification of a production product. Reference: FINAL_PRODUCT_BLUEPRINT.md, REQUIREMENTS.md, INPUT_SPEC_V2.md, ARCHITECTURE_V2.md, current code and GitHub Actions. Check live SHA/CI again when resuming.

## Status meanings

- **IMPLEMENTED / CI TESTED**: code and synthetic/runner tests exist. Not equivalent to clean consumer Windows behavior.
- **PARTIAL**: some technical path exists, with a known contract/verification gap.
- **UNVERIFIED**: plausible implementation but missing direct test or operational evidence.
- **MISSING**: code/feature not yet provided.
- **EXCLUDED / DEFERRED**: intentionally out of scope for initial offline local product.

## Acceptance-oriented audit

| # | Blueprint requirement | Current implementation / concrete evidence | Gap/state | Priority & proof needed |
|---|---|---|---|---|
| 1 | ZIP, TXT, delimited TXT, folder, paste, source file | offline_core.scan_path / scan_text; desktop_core; desktop_ui | IMPLEMENTED / CI TESTED | P0: actual GUI click on Windows and corrupt input QA |
| 2 | Safe ingress, redaction, no source execution | code_input safe readers, static_checks Python AST; 85 synthetic CI tests | PARTIAL | P0: adversarial ZIP/path/binary/large input and Windows filesystem edge cases |
| 3 | Full discovered/eligible/analyzed/excluded manifest | OfflineScan.coverage; desktop_core preflight | **PARTIAL: ignored directories are pruned by loader; contained items not enumerated** | **P0: explicit subtree-pruned markers and counts vs unknown child count; never claim full repo** |
| 4 | Scan states complete, partial, blocked, cancelled | complete/partial object; blocked CLI error code; GUI exceptions | PARTIAL; cancellation absent, blocked not persisted as report object | P1: explicit cancel, timeout and fail-closed outcome |
| 5 | Single TXT Python choice and exact origin mapping | _language_virtual_path, SourceOrigin, synthetic 1,200 lines | IMPLEMENTED / CI TESTED | P1: UTF-8 BOM, huge texts and Unicode real Windows QA |
| 6 | Delimited TXT strict grammar and source map | _split_delimited_txt, duplicate/path escape tests | IMPLEMENTED / CI TESTED | P1: malformed headers, lines and secret-redaction boundary QA |
| 7 | Python AST risk rules incl. exec, SQL, pickle, shell | static_checks.py | PARTIAL: small rule set, no dataflow or project analysis | P1: measure false negatives/positives with labeled synthetic corpus |
| 8 | JS/TS syntax and risk adapter | generic-patterns-only marked limited | MISSING: language-specific adapter | P1: select verified parser/tool with safe config, licensing and zero code exec |
| 9 | Analyzer/rule IDs and severity | offline_report.py fixed known-title map, severity sort | PARTIAL: rules identified by title, not stable engine IDs; basic severity only | P1: use engine-level stable IDs and tests through report |
| 10 | Finding evidence cross-check and redacted excerpts | build_report validates path/line/excerpt against masked bundle | IMPLEMENTED / CI TESTED | P1: adversarial citation and multiline tests; a matched excerpt is not proof of defect |
| 11 | Human required / pattern-only certainty differentiation | Report disclaimer, invalid citation partial | PARTIAL: no contextual verification workflow | P2: evidence status and human reviewer add-on tracked separately |
| 12 | Dedup and severity priorities | offline_report.build_report | IMPLEMENTED / CI TESTED | P2: rule-level conflict handling and false-positive suppression |
| 13 | Korean standalone HTML and Markdown | self-contained HTML/CSP, Markdown sanitizer, local filenames | IMPLEMENTED / CI TESTED | P0: browser render and print/PDF actual Windows verification |
| 14 | Dashboard breakdown (language, rule, severity) | per-file coverage and finding cards/counts | PARTIAL: no proper rule/language/severity summary KPI visualization | P1: Korean report summary charts/tables, no JS/CDN, accessible print |
| 15 | Re-run/compare results | unlimited local sequential scans and distinct reports | PARTIAL: no explicit comparison of historical runs | P2: local user-chosen report comparisons without retention/telemetry |
| 16 | Desktop workflow | Tk source picker, paste, preview, worker scan, HTML open | IMPLEMENTED / headless CI TESTED | **P0: actual GUI click/render, Unicode, failed/partial paths on clean Windows** |
| 17 | Progress and cancellation | status changes before/after task, no live progress/cancel | MISSING detailed progress/cancel | P1: bounded queue, progress events, cancellation preserving inputs |
| 18 | Portable Windows EXE | PyInstaller onefile unsigned candidate; Windows 2025 Actions packaged --self-test PASS | PARTIAL | **P0: clean offline Windows/Defender/SmartScreen, start/run/uninstall** |
| 19 | Offline/network privacy guarantee | no remote analyzer in offline path; socket mock unit tests; no telemetry/assets | UNVERIFIED actual network capture | **P0: isolated-network packet/endpoint observation on Windows customer flow** |
| 20 | Source data handling, retention/delete | no overwrite, local report only, documented deletion | PARTIAL: no in-app report erase control, synced-folder risk | P1: explicit local cleanup and user-controlled output path guardrails |
| 21 | Scale + memory/latency bounds | v2 limits 200 eligible files / 1 MiB per file / 8 MiB total; synthetic 12k-line test | PARTIAL: no repeatable Windows multi-MB throughput/memory benchmark | P0: benchmark and publish only measured throughput/limits |
| 22 | Source-file protection and write errors | input read-only; write_report temporary + hard-link no-clobber | PARTIAL: forced exit can leave one of pair; cloud paths not blocked | P1: output integrity/recovery and path error matrix |
| 23 | Dependencies, licenses, provenance | Windows candidate pinned Pydantic/PyInstaller, pip-audit for legacy requirements | PARTIAL | P0: transitive component SBOM, notices, CVE audit and bundling licenses before sale |
| 24 | Commercial offer/pricing 49k/99k/40k | owner-approved hypotheses in blueprint | UNVERIFIED demand/support costs; NO sales yet | P2: clean product QA, documented service terms, seller approval |
| 25 | 8 independent AI council / guaranteed auto fixes / SaaS | explicitly excluded | EXCLUDED | No work in core product |

## Critical baseline limitations (MUST remain visible)

- **Day 3 CI proof:** 16/16 standard workflow matrix, 85 synthetic unit tests, Windows candidate EXE built with synthetic --self-test. This is not a GUI visual test, packet-capture privacy proof, or market-quality certification.
- **No tested paid service:** software can be run repeatedly without AI API, but development labor, signing, hardware, packaging and transaction fees are not zero.
- **Misleading coverage risk:** loader may prune ignored directories without enumerating their contents. Do not treat covered path count as a count of every filesystem item.
- **Not a comprehensive security review:** small Python AST rules; JS/TS generic patterns only, no runtime, no independent AI council.
- **Public MIT repo:** existing source not proprietary and no user customer data/real keys/paid commercial secrets permitted in commits.

## Prioritized implementation blocks

| Order | Work package | Acceptance check (synthetic, CI, then Windows) |
|---|---|---|
| P0-A | **Coverage truthfulness:** expose ignored/pruned subtree metadata without recursive reads, revise report/preview counts, fail partial rather than full-code false confidence | ignored directory fixture, symlink subtree, ZIP non-readable entries, partial flag, no customer code leaked |
| P0-B | **Actual Windows UI E2E and offline observation** | automated or human actual GUI launch/click, file selection, report HTML print, Windows Defender + network capture; record unsupported gates |
| P0-C | **Benchmark and dependency/license gates** | measured file/byte/runtime/memory and hashes/SBOM; only tested limits advertised |
| P1-D | **Rule depth + JS/TS adapter** | fixed rule IDs, parser selection and no untrusted config execution; labeled precision/recall |
| P1-E | **Report/dashboard UX, progress and cancellation** | severity/rule/language summaries, per-file progress, clear cancel/partial and safe report deletion |

## Design evaluation for Phase2 immediate action

| Option | Performance | Direct API/build cost | Maintainability/risk |
|---|---|---|---|
| A. Expand third-party analyzers immediately (Ruff/Bandit/JS) | More rules once integrated, heavier install/start | API=0 but more bundle/download/build work | Higher licensing/config/execution boundary risk; current coverage truth problem persists |
| **B. Fix scan manifest/coverage and instrument synthetic Windows QA first** | Preserves lightweight core and establishes performance evidence | No AI calls or new runtime library required | Minimal source impact, directly reduces misleading complete/partial claims; recommended now |

**Decision:** option B first; no material feature reduction. Phase2 starts with coverage truthful accounting on a new feature branch, then follows P0-B/C. New external dependencies, paid APIs, user data upload and repository access changes still require separate explicit owner approval.

## Rollback / boundaries / next handoff

Source baseline for this audit: main merge `f0c257058f43298167e6777f315db01ae294fd86`; preserve it. No force push; all fixes feature branch → tests → PR → main and STATUS/HANDOFF refresh. Product not Vercel deployed. Real customer delivery remains NOT READY.


## 2026-10-27 verified P1-H / P1-E addendum (baseline table above is historical)

- **#14 summaries:** P1-H [PR #18](https://github.com/hibi89/ai-code-checker/pull/18) merged; Korean HTML/Markdown severity/rule/language summary tables are implemented/CI tested. Statistics are candidates/file suffixes only; they are not confirmed vulnerabilities or a complete language-coverage guarantee.
- **#17 progress/cancellation:** P1-E [PR #19](https://github.com/hibi89/ai-code-checker/pull/19) merged source SHA `12c51540e646bc088aa24faa96aaf48f5fb843dd`; cooperative per-file progress and GUI cancel implemented with 7 headless tests + Windows scripted Tk E2E, all feature CI PASS. Cannot interrupt one bounded input read or atomic publication mid-stage; not a total wall-clock completion percentage. `cancelled` is an exception/UI result and NOT yet a persisted `OfflineScan` report state.
- **#4 blocked/cancelled persisted outcomes** remain PARTIAL: blocked CLI and cancelled GUI are visibly differentiated, but they are not persisted reports.
- **#20 report management:** local automatic stored report deletion remains MISSING. Prioritize explicit user-controlled selection and safe deletion with no unprompted source/report removal.
- **#18/#19/#23 customer Windows, packet/privacy, signing and legal clearance** remain UNVERIFIED/BLOCKED despite synthetic hosted Windows tests. No Vercel and no commercial release.


## 2026-10-27 P1-I verified update (prior table remains historical)

- **#20 (retention/delete):** user-initiated, latest in-session report HTML+Markdown deletion implemented/CI tested under [PR #20](https://github.com/hibi89/ai-code-checker/pull/20). SHA/stat proof, exact path/single-owner file checks, confirmation defaults to No, no directory scans/removal. Deletion after app restart or of historical files is not available. No claim of recoverable or atomic 2-file deletion; manual handling of partial I/O error remains.
- **#22 output integrity:** prior atomic no-overwrite **creation** retained; new paired *deletion* is non-atomic with fail-closed preflight and truthful partial-error disclosure. Customer Windows edge cases remain unverified.
- **#23 binary provenance:** new first-party module identified explicitly in frozen package candidate map. This is **not legal attribution, license clearance, or permission to distribute**.
- **#18/#19 actual Windows/device/privacy:** synthetic hosted CI and UI invoke tests passed, but real customer Windows, OS packets, antivirus, SmartScreen, PDF visual remain unverified.
- **#4 blocked/cancelled persisted reports:** unchanged; GUI status separated but not persisted report state.
- Detailed evidence: [P1-I report cleanup ledger](P1I_REPORT_CLEANUP_EVIDENCE_20261027.md); source merge `779b611bf2f932fa219631c32f810fa3253111c4`, verified feature `78d5ad675ee0bf7d2502fc91e8d72db4fe5b9825`.


## 2026-10-27 P1-J verified output path guard addendum

- **#22 output integrity / source isolation:** `output_safety.validate_output_location` now blocks reports inside the folder being scanned before source reads; prevents writing via currently detected symlink, junction/reparse components, UNC-style paths, or file-as-folder outputs. Original paired no-overwrite hardlink publication retained. Eight Python synthetic regressions and one Windows scripted scenario PASS. This is preflight only, not atomic against hostile filesystem races.
- **#19 and #20 storage privacy:** UNC-style path blocking does not prove absence of OS network traffic; user-selected cloud sync/mapped drives may leak reports. No automated network/captive test establishes privacy, and no operating system packet capture yet. **Remain UNVERIFIED on customer hardware.**
- **#23 packaging notices:** first-party module `output_safety` identified in frozen archive mapping, does not establish third-party redistribution rights or legal signoff.
- Source merge [PR #21](https://github.com/hibi89/ai-code-checker/pull/21) `8485413205007366ffa683ec272a198f1f47f394`, CI general 16/16 / 175 unittest, Windows candidate 1/1, synthetic inventory 3/3 PASS at feature head `27d7825`. See `P1J_OUTPUT_SAFETY_EVIDENCE_20261027.md`. Product release BLOCKED.


## P1-K 2026-10-27 acceptance evidence addendum

- **#16 desktop, #18 Windows EXE:** full synthetic Tk workflow now executes from actual frozen Windows onefile process as `--scenario-smoke`, not merely hosted source Python + packaged GUI startup. Verified on feature SHA via [Windows Actions 40496583605](https://github.com/hibi89/ai-code-checker/actions/runs/40496583605), with source [PR #22](https://github.com/hibi89/ai-code-checker/pull/22) merged `39d5db20ac3db3294bd45ce76f6d32c4f9fab65d`.
- **#13 PDF:** Windows browser synthetic PDF smoke still PASS, actual visual page verification and real user browser print **UNVERIFIED**.
- **#19 OS/network and #23 notice:** physical Windows Defender/SmartScreen/OS packet capture/actual binary rights and original NOTICE compliance remain UNVERIFIED/BLOCKED; CI GUI smoke provides no evidence for those.
- New proof document: `P1K_FROZEN_GUI_ACCEPTANCE_20261027.md`. No Vercel or product release.


## 2026-10-27 P1-L release-gate observation addendum

- **#18/#19 Windows/privacy:** P1-L [PR #23](https://github.com/hibi89/ai-code-checker/pull/23) added an explicit local-only, read-only Windows EXE SHA/signature/Defender settings receipt, independently checked against the actual EXE bytes. CI hosted Windows logs confirm `WINDOWS_ACCEPTANCE_READONLY_EVIDENCE_PASS` and Defender *settings* observable, **not** a Defender EXE malware scan, SmartScreen acceptance or actual network packet capture. Actual retail clean Windows remains UNVERIFIED.
- **#13 visual PDF:** Existing headless browser print remains synthetic only, human visual inspection UNVERIFIED.
- **#23 binary licenses:** original third-party NOTICE and redistribution approval remain BLOCKED; signature status observation alone does not approve distribution.
- **Release gates:** evidence schema hardcodes retail user acceptance, SmartScreen, OS packets, Defender file scan, human Korean PDF visual and third-party legal NOTICE as UNVERIFIED. No user OS changes; CI Tests 16/16 / 185 Python cases and Windows EXE + read-only receipt 1/1 PASS on feature `19496ba1`, merged source `f7fccd8`. See `P1L_WINDOWS_READONLY_ACCEPTANCE_20261027.md`.


## P1-M 2026-10-27 mapped Windows network-drive output update

- **Storage privacy #19/#22:** previous UNC, symlink/junction and in-source output protections expanded to Windows mapped drive letters with Win32 GetDriveTypeW; remote type 4, missing/unknown and optical denied before output traversal, local type 2/3/6 accepted. [PR #24](https://github.com/hibi89/ai-code-checker/pull/24) merged main source `72c89d36828267ffb44edb1d9dd1ee47e65dc5b2`.
- **Tests:** CI Tests [40499792387](https://github.com/hibi89/ai-code-checker/actions/runs/40499792387) 16/16 SUCCESS, 190 Windows Python3.11 unit tests; Windows EXE [40499792348](https://github.com/hibi89/ai-code-checker/actions/runs/40499792348) 1/1 SUCCESS. Mocked remote drive and real Windows local drive observation PASS.
- **Not closed:** network-mapped **input** source path may still read from network, cloud-synchronized local folders, filesystem TOCTOU, real OS packet capture, customer retail Defender/SmartScreen, Korean PDF visual, native third-party legal NOTICE and manual commercial release approval. See `P1M_WINDOWS_MAPPED_DRIVE_SAFETY_20261027.md`.


## P1-N 2026-10-27 input privacy delta

- **Offline v2 local-input privacy:** P1-M protected only output drives; P1-N rejects UNC/device and Windows remote mapped input source drives and symlink/reparse ancestors before preview/scan direct source reads. `code_input.load_path` (original v1 legacy loader) unchanged. [PR #25](https://github.com/hibi89/ai-code-checker/pull/25) source merge `7fcb2ca3e665773f1464d5636ca0a8fcf1d493a9`.
- **Verified:** Actions general [40501255327](https://github.com/hibi89/ai-code-checker/actions/runs/40501255327) 16/16, Windows Python3.11 200 tests, Windows candidate [40501255271](https://github.com/hibi89/ai-code-checker/actions/runs/40501255271) 1/1, synthetic performance [40501255370](https://github.com/hibi89/ai-code-checker/actions/runs/40501255370) 3/3.
- **Remaining:** OS picker itself can browse remote sources before validation; cloud-sync local folders, hostile filesystem races, real packet capture, physical clean retail Windows Defender/SmartScreen/PDF visual and complete bundled LICENSE/NOTICE legal clearance all remain unverified. See `P1N_OFFLINE_INPUT_PRIVACY_EVIDENCE_20261027.md`; no commercial release.

## P1-R 2026-10-27: actual preview freshness added

- Final [PR #29](https://github.com/hibi89/ai-code-checker/pull/29) source merge `510db6cc790d34e69e7763d419cbea7c2f5f43da`, feature `b8d83924e9d4d0dc1fc6d1ff01ecf5134f7cdb59`. GUI preflight now includes a session-only digest of the masked normalized manifest and compares it at scan start. Changes require a fresh preview; unchanged sources continue to report. Headless/legacy callers do not require a fingerprint.
- Scope: versioned ZIP/TXT, same-size source changes, project file additions/removals, metadata-visible pruned subtrees. Not an atomic read snapshot and cannot detect equivalent redacted content or subsequent races. No raw ignored subtree reads.
- [General Tests 40509498853](https://github.com/hibi89/ai-code-checker/actions/runs/40509498853) 16/16 PASS (Windows3.11 230 tests/1 skipped); [Windows candidate Tk 40509498591](https://github.com/hibi89/ai-code-checker/actions/runs/40509498591) 1/1 PASS. Initial Tk cancel mock incompatibility was fixed in a follow-up source commit before final CI. No real customer desktop, AV, SmartScreen, OS packets, PDF visual, full licenses or commercial authorization.

## P1-S historical report discovery — 2026-10-27

- [PR #30](https://github.com/hibi89/ai-code-checker/pull/30) merged source `90ca2eb98e96b497c6b1f2d8029dfdbeb80505ad`, branch `e3d8e0ac10f8ec9fb12d185412929f20a1b91fb4`. On a later desktop session, a user may explicitly select an existing HTML report in the configured local output directory, check a paired MD and restrictive CSP header, and open it read-only. No automatic report indexing/persistence/cleanup, and existing session deletion capability is not transferred to historical reports. The selection is local and bounded; safety indicators are a document *format* check, not cryptographic origin attestation or malware validation.
- Verified final feature [Tests 40511844744](https://github.com/hibi89/ai-code-checker/actions/runs/40511844744) 16/16 jobs PASS including Windows3.11 242 tests (1 skipped), [Windows GUI/EXE 40511844793](https://github.com/hibi89/ai-code-checker/actions/runs/40511844793) PASS. Fixed initial provenance mapping mismatch for new first-party `report_history` module in `scripts/map_frozen_licenses.py`, with regression; no license gate weakened.
- Product gaps that still block release: full historic report management/search beyond explicit picker, real-user Windows, executable malware scan/SmartScreen, OS egress capture, manual Korean print-to-PDF visual, original third-party NOTICE/legal clearance and explicit owner approval. Other earlier matrix rows remain historical unless explicitly marked superseded.
