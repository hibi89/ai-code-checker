# CODE CHECKER — STATUS (2026-10-26 KST)

Repository: https://github.com/hibi89/ai-code-checker (Public/MIT). Production/Vercel: NOT APPLICABLE (offline Windows desktop app).

## Live merged source baseline
- Day1 PR #2: safe ingest/Python AST; Day2 PR #3: Korean HTML/Markdown offline report; Day3 PR #4: Tk desktop GUI + unsigned packaged EXE candidate.
- Verified Day3 main **merge SHA `f0c257058f43298167e6777f315db01ae294fd86`** with [post-merge Actions 16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40309370848).
- Windows PR #4 smoke: EXE built and synthetic scan/report PASS. Python CI baseline: 85 unit tests. **Actual GUI clicking/clean customer Windows, Defender/SmartScreen, printing, packet-capture privacy tests remain UNVERIFIED.** No customer-ready release.
- Prior code + v1 Gemini flow preserved. Offline local scan does not require AI API keys, a server, online account, subscription, customer code execution or external source transfer by design. Real network observation is pending.

## Current Phase2 work — not yet main
- Branch: `feature/blueprint-gap-phase2` based on main `f0c2570`. Feature work is not counted as main delivery before PR merge.
- [BLUEPRINT_GAP_MATRIX_20261026.md](BLUEPRINT_GAP_MATRIX_20261026.md): 25 evidence-based blueprint checks, priorities and acceptance.
- P0-A truthfulness fix: `offline_coverage.py` inventories names of policy-skipped subtrees without reading children or following symlinks. `offline_core.py` reports them separately, makes folder scans partial when any subtree is pruned, and states **child file counts UNKNOWN** rather than inventing exact discovered counts. `desktop_core.py`, `offline_report.py` surface that distinction. Existing legacy `code_input.py` unchanged.
- `tests/test_pruned_coverage.py` covers nested ignored subtrees, clean directories, depth limits and bounded walk refusal. GitHub CI for the feature head must be checked before completion.
- No new third-party runtime dependency, no provider/API calls, no customer data, no EXE artifact upload.

## Work board

| Phase | Verified status |
|---|---|
| MVP Day1 ingest | MERGED / CI PASS |
| MVP Day2 report | MERGED / CI PASS |
| MVP Day3 GUI code + EXE synthetic smoke | MERGED / CI PASS; real Windows interaction UNVERIFIED |
| Phase2 blueprint gap matrix | CREATED on feature branch; PR/main integration pending |
| Phase2 P0-A scan coverage truth | FEATURE CODE IMPLEMENTED; CI/PR integration pending |
| Phase2 P0-B clean Windows GUI/privacy/PDF | PENDING |
| Phase2 P0-C benchmarking, dependency licenses | PENDING |
| Phase2 P1 Python/JS/TS depth and report UX | PENDING |
| Phase3 final stability/privacy/security/accuracy | PENDING |
| Phase4 Kmong approval and sale | PENDING |

## Recovery and next run

- Stable recovery point: `main` f0c2570 (PR #4 merged + CI PASS). Never force push, remove historical Gemini source or expose customer data.
- Next **ㄱ** or **[코드체커 깃헙 확인해]**: check branch current SHA/open PR/CI; if Phase2 P0-A passes, merge PR non-force; verify main post-merge CI; then proceed to Windows E2E and measurable coverage/benchmark. Any unrun GUI, packet, PDF, antivirus checks must stay UNVERIFIED.
- Follow `HANDOFF.md`, `AGENTS.md`, `REQUIREMENTS.md`, final blueprint, and GAP matrix. Update handoff after relevant merge.

## Phase2 P0-A merged and verified (2026-10-26 KST)

- [PR #5 merged](https://github.com/hibi89/ai-code-checker/pull/5) into **main `2ab40c2e06638cac8aca15a2fd50aa7941336f1f`** from feature head `5afd848da250e7b351ace82937b08275139c42f8`.
- Feature final-head [Actions 16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40310261361) with **89 Python unit tests PASS** (85 baseline + 4 new); [Windows packaged EXE smoke PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40310322743).
- Ignore/pruned directories are now listed as **directory metadata only**; their contained files are UNKNOWN, not enumerated. Overall folder scan becomes partial when any subtree pruned. This avoids falsely implying a complete review of all project folders; original read-only input and v1 Gemini CLI preserved.
- The post-merge main CI for 2ab40c2 should be checked separately. Documentation commits later than this merge change HEAD again.
- Next target: P0-B real Windows GUI interactions, offline packet observation, PDF printing, Unicode paths and Defender/SmartScreen, then P0-C measured benchmarks and license inventory. **Do not sell until acceptance.**

## Phase2 P0-B Windows GUI/Edge PDF CI evidence (2026-10-26 KST)

- PR [#6](https://github.com/hibi89/ai-code-checker/pull/6) feature branch `feature/windows-gui-pdf-e2e`: **Windows CI code SHA `d6e4005998edeafc5a1c262281f29a747d3582c7` passed** GitHub Actions [Windows smoke](https://github.com/hibi89/ai-code-checker/actions/runs/40313412431) and standard 16/16 CI at [40313412364](https://github.com/hibi89/ai-code-checker/actions/runs/40313412364). Verify latest docs HEAD, PR merge and post-merge CI separately.
- `desktop_ui.py`: explicit test-only hook to instantiate actual Tk UI, packaged `--gui-smoke`, and fix that clears stale open-report state on source changes/failure. Existing Gemini CLI stays unchanged.
- `scripts/windows_gui_e2e.py`: real Tk event loop + scripted controls for Unicode TXT, mixed ZIP, policy-pruned folder, paste and blocked path traversal; local reports, partial statuses and mocked local HTML opener PASS. Python socket connect attempts during synthetic GUI test: zero under fail-closed monkeypatch.
- `scripts/windows_browser_pdf_smoke.py`: Windows hosted Microsoft Edge headless printed self-contained HTML to a 96,799-byte PDF, `%PDF-` signature PASS; Unicode path tested. PDF NOT uploaded or visually inspected.
- Packaged Tk GUI startup and EXE offline synthetic scan both PASS on Windows CI; EXE remains unsigned, not distributed.
- Distinguish these PASSes from still **UNVERIFIED** independent customer's Windows GUI physical interaction, browser interactive Print, Korean PDF visual glyph rendering, Defender/SmartScreen, Windows packet-capture, and commercial license/release gates.
- Next: validate PR #6 final SHA/CI then merge if green; verify main after merge. Afterwards Phase2 P0-C repeatable benchmark + transitive bundled license audit. Detailed evidence: [WINDOWS_GUI_PDF_EVIDENCE_20261026.md](WINDOWS_GUI_PDF_EVIDENCE_20261026.md).

## P0-B integrated into main (2026-10-26 KST)

- [PR #6](https://github.com/hibi89/ai-code-checker/pull/6) merged at **`2294cfc458c104fbfa20dd452e87009696dcf15c`** from feature head `57486ecd4fbe0a07e75e3e14439deed60c882b08`.
- Final feature head [16/16 standard CI PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40313874119) and [Windows GUI/Edge PDF/EXE smoke PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40313878754). CI of merge commit and later documentation commits requires live verification.
- Verified Windows Server 2025 synthetic UI flow, packaged Tk startup, source/paste/ZIP/folder/blocked states, Unicode paths, local opener mock, synthetic Edge headless PDF signature and 96,799-byte file. Python socket monkeypatch found no attempted connections in this synthetic GUI run; not a network packet capture.
- **Unverified launch gates:** physical clean customer's Windows PC and human GUI, browser interactive Print dialog, PDF glyph/layout visual check, OS network capture, Defender/SmartScreen/reputation, optional packaging code signing, transitive license/SBOM/commercial terms.
- **Next approved work:** Phase2 P0-C automated scale/performance + dependency/license inventory, with separate real-Windows acceptance pending. No public EXE upload, Vercel deployment, paid APIs or commercial sale.
- Resume sources: [WINDOWS_GUI_PDF_EVIDENCE_20261026.md](WINDOWS_GUI_PDF_EVIDENCE_20261026.md), [BLUEPRINT_GAP_MATRIX_20261026.md](BLUEPRINT_GAP_MATRIX_20261026.md).

## Phase2 P0-C synthetic benchmark + installed build dependency inventory (2026-10-26)

- New PR [#7](https://github.com/hibi89/ai-code-checker/pull/7) on `feature/p0c-benchmark-sbom`, branched from last verified main `ec4c03f5670e6a582f46b6c91fbdb9ae90b8da1b` (main Actions 16/16 PASS). Source files `scripts/benchmark_offline.py`, `scripts/offline_dependency_inventory.py`, `tests/test_benchmark_inventory.py`, `.github/workflows/p0c-performance-inventory.yml`, [measured report](P0C_PERFORMANCE_SBOM_20261026.md). **Do not mark PR merged before checking live state.**
- Measured on synthetic LF-identical fixtures, Windows/Linux Python 3.13, [P0-C Actions 40317040322](https://github.com/hibi89/ai-code-checker/actions/runs/40317040322) **3/3 jobs PASS**: TXT 1,200 lines 0.1217/0.0888 s; 12-file ZIP 0.0862/0.0700 s; 200-file 12,000 lines 0.8835/0.6912 s; 200-file ~6.04MB 12,000 lines 1.9216/1.7263 s (Windows/Linux respectively). Every case produced local HTML/Markdown; 201 supported source files blocked.
- Multi-MB tracemalloc peak 11.608 MiB Windows / 11.607 MiB Linux. **Traced Python allocations, NOT full RSS or EXE process footprint.** Runner-only observations, not a performance guarantee.
- Windows build dependency inventory: 12 installed Python package records reachable from pinned Pydantic 2.12.5 and PyInstaller 6.22.3; 0 unresolved roots and 0 missing declared-license metadata. `pip-audit` (online advisory lookup in CI) returned 'No known vulnerabilities found' for pinned build dependencies. **Metadata inventory is not packaged binary SBOM or legal redistribution license approval.**
- The initial synthetic unit fixture had two test-only failures (packaging import absent in legacy matrix and fake dict metadata lacking get_all); tests fixed to use real-style email Message metadata and mocking without extra original CLI dependencies. Source & original v1 Gemini untouched. Baseline 93 tests already PASS after fix, final LF fixture test should increase to 94; verify latest head Actions before merge.
- P0-C remaining to commercial readiness: actual bundled EXE SBOM and license notices/attribution, Defender/SmartScreen/clean Windows, OS-level packet capture, interactive PDF visual inspection, real project throughput/peak RSS. No customer code or secrets used/uploaded and no product artifact published.
- Next `ㄱ`: verify PR #7 latest code HEAD, GitHub regular 16/16 + dedicated benchmark/inventory 3/3; merge only if green and record main post-merge CI. Then prioritize packaged binary inventory/license text and independent Windows acceptance, or Python/JS rules as warranted by blueprint.

## P0-C final verified integration (2026-10-26 KST)

- **MERGED [PR #7](https://github.com/hibi89/ai-code-checker/pull/7)** to main as `625313622c4dcefe055848acab399181dbba9bde`; feature final HEAD `1186e2cd80ddf60350f7e0eb66e1b2263769e8c7`.
- Feature final-head [standard CI 16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40317430334) and [dedicated performance/inventory CI 3/3 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40317437467). The post-merge main run `40317897360` was queued initially; check current HEAD and outcome rather than assuming success.
- Python synthetic unit tests **94 PASS** (89 prior, 5 new), no customer inputs or paid AI/API calls.
- Cross-platform identical LF-input benchmark 200 files and 12,000 lines: Windows 0.8835s / Ubuntu 0.6912s; ~6.04 MB variant Windows 1.9216s / Ubuntu 1.7263s. Tracemalloc Python peak allocation ~11.61 MiB at ~6MB; excludes native RSS and packaged EXE/browser. 201 files blocked (explicit limit). Exact report: [P0C_PERFORMANCE_SBOM_20261026.md](P0C_PERFORMANCE_SBOM_20261026.md).
- Windows installed build dependencies: 12 Python distribution metadata records, Pydantic 2.12.5 + PyInstaller 6.22.3 roots pinned, no unresolved/unknown declared-license metadata; `pip-audit` **no known vulnerabilities at run time**. Actual EXE embedded libraries/licenses and corresponding NOTICE obligations remain **UNVERIFIED**.
- **NEXT:** full PyInstaller EXE bundle/native DLL/Tcl-Tk SBOM and license-text/attribution verification, real clean Windows customer interaction and Defender/SmartScreen, network packet observation and PDF visual quality. Sale/release still forbidden without owner approval; no Vercel.

## Phase2 P0-D actual frozen EXE inventory — VERIFIED CI, MERGED (2026-10-26)

- [PR #8](https://github.com/hibi89/ai-code-checker/pull/8) merged as **`c3ca5df250ea81e0bb523ca3f2da2e7e1eb8bd3f`**. Feature head `1ac85f82845e7d8b90a813d0935e3a47cb6ffed0` [full standard CI 16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40318937393) (98 Python unit tests PASS) and [Windows packaged CI 1/1 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40318937450).
- Actual freshly built Windows onefile EXE inspection via PyInstaller `CArchiveReader`: **1,018 CArchive metadata entries + 544 nested PYZ Python module names**. Runtime native binary and Tcl/Tk marker both detected. The build-environment dependency closure had 12 installed Python distributions and 30 candidate license-text files hashed. **30 is installed license evidence, not 30 proven embedded license notices.**
- Local gitignored JSON evidence `.build-windows/frozen-exe-evidence.json`; EXE SHA-256 per [Windows Action](https://github.com/hibi89/ai-code-checker/actions/runs/40318937450), no binary uploaded. Scan is metadata-only: bundled code not executed/extracted. `NOTICE_REVIEW=REQUIRED`; `COMMERCIAL_RELEASE=NOT_APPROVED` CI gate preserved.
- **This is NOT distribution license approval nor signed release.** Actual component→vendor→exact license text mapping, Python/Tcl/Tk/native DLL obligations, human copyright/NOTICE review, clean customer Windows, SmartScreen/Defender, OS packet capture and PDF visual acceptance remain pending.
- Next `ㄱ`: verify newest main SHA and post-merge CI; move to P0-E complete source/NOTICE mapping, clean-device acceptance plan and deep rule coverage, without publishing EXE or using paid APIs.

## P0-E actual archive owner candidates and installed original license texts — merged (2026-10-26 KST)

- [PR #9](https://github.com/hibi89/ai-code-checker/pull/9) **MERGED main `765ed9d4a9f183e749dfd78d0dc185d73694c609`** (feature final `73341809baf06b30d5472dcb8dfeacaa7a2b03ec`). [Final 16/16 regular CI](https://github.com/hibi89/ai-code-checker/actions/runs/40321463525) PASS, **104/104 unittest PASS**; [Windows EXE GUI/PDF/archive/license mapping CI](https://github.com/hibi89/ai-code-checker/actions/runs/40321463677) PASS. Confirm main post-merge CI separately.
- `scripts/map_frozen_licenses.py` maps **all 1,562 actual observed EXE archive/PYZ names**, conservatively (names only). **7 installed distribution ownership CANDIDATES**, 276 CPython stdlib name candidates, 923 Tcl/Tk filename/resource candidates; **92 unresolved** (67 native/system binary + 25 resource/bootloader). No binary hash provenance or legal owner proof.
- P0-D installed license file hashes checked; **26 original installed license texts staged** in local `.build-windows/NOTICE_REVIEW_DRAFT.md`, **0 missing** on CI. This local draft is NOT a distributable third-party notice. EXE/notice evidence never published. `license_compliance_certified=false` and `customer_release_ready=false` enforced by CI.
- Owner candidates: annotated-types, packaging, pydantic, pydantic-core, setuptools, typing-extensions, typing-inspection. Exact package→embedded binary→license text/NOTICE attribution, CPython/Tcl/Tk/VC redistribution, Windows client/SmartScreen/packet/PDF visuals remain **UNVERIFIED**.
- Next `ㄱ`: verify main/CI, prioritize unresolved 67 native DLL/.pyd and 25 resource/bootloader owner/legal notices with evidence; then end-user clean Windows & safety/product accuracy gates. No commercial release or paid API.
- [P0-E evidence ledger](P0E_OWNER_LICENSE_MAPPING_20261026.md).


## Phase2 P0-F native build file provenance — MERGED (2026-10-26 KST)

- **PR [#10](https://github.com/hibi89/ai-code-checker/pull/10) MERGED**, `main` feature merge commit `c59f3dc807a11f48949f081263877bf4533467c9`. Feature code head `200236091b7b75130bbe010c2478d92b695a0c43` [16/16 regular CI PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40323280004) and [Windows packaged CI PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40323280024); **111 synthetic Python unittest PASS**. Verify post-merge main Actions separately.
- New `scripts/reconcile_native_build.py` reads PyInstaller local `Analysis-00.toc` with bounded `ast.literal_eval`; maps unresolved CArchive entries to the build source file, hashes native binary bytes with `CArchiveReader.extract` *in memory*, no disk extraction. `tests/test_native_build_provenance.py` adds seven tests; workflow checks count integrity and release blocks.
- **Actual Windows evidence:** previous **92 unresolved** archive items → **80** unique Analysis source file records; of these **67 native binaries** exactly SHA-256 matched actual EXE embedded bytes and **13 non-native resources** had unverified unique source paths. **12** archive resources/bootloader entries remain without an Analysis source claim. Byte equality is *not* copyright/license approval.
- Local gitignored result `.build-windows/native-provenance.json`; absolute build source paths not emitted; no customer code/artifacts or paid APIs transmitted. Commercial legal NOTICE and release **BLOCKED**. Detailed methodology & evidence: [P0F_NATIVE_PROVENANCE_20261026.md](P0F_NATIVE_PROVENANCE_20261026.md).
- Next `ㄱ`: verify main HEAD/post-merge CI; investigate the 12 remaining archive/resource/bootloader entries via actual EXE and EXE build TOC, make traceable evidence and identify which are PyInstaller internal archive entries. Then remaining CPython/Tcl/Tk/VC copyright/NOTICE obligations and independent Windows client/SmartScreen/packet/PDF visual acceptance and Python/JS/TS scanner accuracy. No EXE publication, no commercial launch without owner approval.

## Phase2 P0-G EXE-00.toc cross-check — PR #11, feature CI PASS (2026-10-26 KST)

- Base main SHA `abd72767318672f5060a75ebd0da8982c44b0db0`; new feature `feature/p0g-exe-toc-provenance`, [PR #11](https://github.com/hibi89/ai-code-checker/pull/11). Code/doc pre-handoff head `49583688f99e44486c83167fbc5d571c0851fb91` passed [standard 16/16 CI](https://github.com/hibi89/ai-code-checker/actions/runs/40328196934) with **119/119 synthetic tests** and [Windows packaged CI](https://github.com/hibi89/ai-code-checker/actions/runs/40328196858). New handoff-doc commit requires re-check before merge.
- Real CI Windows onefile rebuild P0-D/E/F/P0-G: **12 P0-F non-unique Analysis entries → 11 exact-name EXE-00.toc packaging record candidates, 0 ambiguous, 1 without EXE TOC claim**. This is build metadata only: NO legal source-owner/redistribution/NOTICE certification. 67 previously known native byte matches remain source-build equality only.
- New `scripts/reconcile_exe_toc.py` and `tests/test_exe_toc_provenance.py` (8 tests); `.github/workflows/windows-portable.yml` enforces accounting and release flags. Evidence `.build-windows/exe-toc-evidence.json` stays ignored/local, aggregate counters visible in CI. [P0-G ledger](P0G_EXE_TOC_EVIDENCE_20261026.md).
- NEXT `ㄱ`: confirm PR #11 latest SHA, standard+Windows CI and mergeability; merge normally if green and verify main post-merge CI. Then target final **1** unlinked record for strictly evidence-based investigation, CPython/Tcl/Tk/VC/PyInstaller original-license/NOTICE, independent Windows/Defender/SmartScreen/packet/PDF acceptance, and Python/JS/TS scanner accuracy.
- **No customer release, EXE distribution, paid API or Vercel deployment.** Owner approval needed for commercialization, permissions/repository changes, customer data transfer and new spend. All clean-consumer-Windows and legal obligations still unverified.

## P0-G final merge record (2026-10-26 KST)

- [PR #11](https://github.com/hibi89/ai-code-checker/pull/11) **MERGED main** at `cdf23e171a59258e2659fb72c634a44eea687065`, feature final head `59e79133514e9b4d5b55ce915835c1735acd4317`.
- Verified feature [standard Tests 16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40328799451) with **119/119 synthetic unit tests** and [Windows packaged EXE P0-D/E/F/G PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40328799432). The original merge SHA main CI [40329090414](https://github.com/hibi89/ai-code-checker/actions/runs/40329090414) was queued when recorded; independently re-check main/post-documentation CI.
- **12 nonunique P0-F records → 11 exact-name EXE-00.toc build packaging claims, 0 ambiguous, 1 no claim.** Build metadata only, NOT legal attribution; 67 native byte matches are merely build-file evidence. No customer-facing EXE, signed release or completed notice.
- NEXT `ㄱ`: refresh live main SHA/checks, then investigate the final 1 no-claim record without guessing ownership; verify third-party notice obligations and independent real Windows privacy/Defender/SmartScreen/GUI/PDF visual gates, then scanner Python/JS/TS accuracy. No Vercel; commercial release still BLOCKED.

## P0-H feature work — final EXE TOC unmatched record (2026-10-26 KST)

- Base verified main `491348598da42aba431302712d0c257efa5a7b1b` (16/16 [CI](https://github.com/hibi89/ai-code-checker/actions/runs/40329235800)). P0-G 12 → 11 unique EXE TOC claims, 1 missing. New `feature/p0h-pkg-toc-evidence` compares that 1 against freshly produced `PKG-00.toc` without code execution, upload, or proprietary source publishing. See [P0-H evidence and design](P0H_PKG_TOC_EVIDENCE_20261026.md).
- **Status as of document creation: pending new PR/CI**; do not claim the remaining record, license/NOTICE or customer release resolved until actual Windows CI evidence reviewed. Tests and approval fail-closed required. No external API or Vercel.

## P0-H CI validation / no additional PKG match — 2026-10-26 KST

- [PR #12](https://github.com/hibi89/ai-code-checker/pull/12), branch `feature/p0h-pkg-toc-evidence`, code SHA `1a5dab52c3d5670004ff61a7b9cf4371f5810844`. [Standard 16/16 CI PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40330934255); **126/126 synthetic unit tests PASS**. [Windows EXE/P0-D/E/F/G/H CI PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40330934463), with Tk synthetic GUI, Edge headless PDF and local artifact checks. Verify final docs commit and PR before merge.
- Actual last single EXE TOC unmatched name had **0 unique PKG TOC claims, 0 ambiguous, 1 no claim**. This is a checked **no-evidence state**, NOT evidence of a missing license or a completed vendor attribution. 67 exact native build-source byte comparisons and 11 EXE records remain separate, unapproved metadata evidence.
- **Pivot:** avoid repeatedly traversing the same unchanged build metadata. Proceed next to P1-D synthetic labeled scanner accuracy (especially Python AST precision and JS/TS restricted scope), and customer-clean Windows/privacy/PDF/Defender acceptance plus original CPython/Tcl/Tk/VC/PyInstaller license notices when real environmental evidence is available. Commercial launch explicitly blocked.

## P0-H merged — source evidence maintained, next analyzer quality (2026-10-26 KST)

- [PR #12](https://github.com/hibi89/ai-code-checker/pull/12) **MERGED** into main as `07a358956264ef7488a5912aa3c970f9dd69d16d` from final feature `325d365d2731aaed271b8b6500193fbe4acfdb7b`. Feature final [standard 16/16 CI PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40331433872) (**126 unit tests**) and [Windows EXE P0-D/E/F/G/H CI PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40331434064). Merge main [CI 40331742286](https://github.com/hibi89/ai-code-checker/actions/runs/40331742286) started; verify outcome and subsequent documentation SHA separately.
- P0-G last 1 unmatched entry → **P0-H PKG TOC matched 0; remains 1**. This is not evidence of a malfunction or licensing noncompliance; stop repeating metadata-only attempts. No new security/notice rights verified.
- **NEXT `ㄱ`: P1-D scanner accuracy**: labeled synthetic TP/FP/FN corpus, prioritize Python AST correctness and truthful JS/TS limited status, measure false-positive and false-negative outcomes before adding deterministic rules. Preserve source, offline/no customer execution, no paid APIs, local report behavior. Clean Windows/Defender/SmartScreen/OS traffic/PDF visuals, legal notices and sale approval remain outstanding; no Vercel.

## Phase2 P1-D accuracy corpus (2026-10-26 KST — pending CI)

- Baseline main SHA \`0129395f9ad896f8d947db73d5bca8d59eb0f138\`, 16/16 [CI pass](https://github.com/hibi89/ai-code-checker/actions/runs/40331876779). Branch \`feature/p1d-rule-accuracy\` updates conservative Python AST checks for subprocess/pickle alias imports, requests verify=False and SQL-prefix observations, retaining JS/TS limited-only status. Adds fixed synthetic labeled TP/FP/FN test script and [evidence ledger](P1D_RULE_ACCURACY_20261026.md). New CI not verified at creation.
- All accuracy claims must be limited to explicitly labeled fixtures, never real-world security detection or full JS/TS scan. Next: verify CI+metrics, address failures, PR+merge, then continue broader labeled rule coverage and real Windows/licensing gates. No EXE sale or Vercel.
