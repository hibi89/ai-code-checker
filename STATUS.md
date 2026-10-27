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

## P1-D synthetic rule accuracy — verified feature CI (2026-10-26 KST)

- [PR #13](https://github.com/hibi89/ai-code-checker/pull/13), pre-document feature SHA `a4e25b8f9992f9a6e4f703f32e2b25b4a372b82b`. GitHub [Tests 40333097683](https://github.com/hibi89/ai-code-checker/actions/runs/40333097683) **16/16 PASS, 132 unittest PASS**; [Windows EXE GUI/PDF/build smoke 40333096415](https://github.com/hibi89/ai-code-checker/actions/runs/40333096415) PASS; [P0-C performance/SBOM CI 40333096368](https://github.com/hibi89/ai-code-checker/actions/runs/40333096368) **3/3 PASS**. Reverify final docs SHA before merge and main.
- Fixed synthetic labeled Python corpus: **28 code cases, TP=13 FP=0 FN=3**, labeled precision **100%**, labeled recall **81.25%**. 2 JS/TS partial coverage checks excluded, no JS/TS parser. Three FNs intentionally included for Python indirect dynamic eval, imported subprocess and cross-line SQL flow. These ratios CANNOT be generalized to customer programs or complete vulnerability scanning.
- Changes: `static_checks.py`, `scripts/evaluate_rule_accuracy.py`, `tests/test_rule_accuracy.py`, standard workflow; no extra runtime/build deps, no paid AI and no remote customer source transfer.
- NEXT: after normal green PR merge, use independent larger labeled cases and legal review for optional JS/TS AST parser, verify actual clean Windows/Defender/SmartScreen/OS packet/interactive PDF visuals and third-party NOTICE before commercialization. Not customer-release ready. Vercel N/A.

## P1-D final merge — 2026-10-26 KST

- [PR #13](https://github.com/hibi89/ai-code-checker/pull/13) **MERGED main** SHA `aef34df705bde1d6458449f237a98bcce83a8535` from feature head `23977690e5485bd76e32dbfc6e39b5b9cbce2982`. Final feature [Tests 16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40333563658), **132 unit tests PASS**; [Windows packaged CI PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40333563565); [synthetic performance/inventory 3/3 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40333563602). Original main merge and follow-up documentation CI require live re-check.
- 28 labeled synthetic Python cases produced **TP=13, FP=0, FN=3**: fixed-fixture precision 100%, recall 81.25%, **real-world correctness UNVERIFIED**. Two JS/TS status fixtures intentionally remain `limited` and excluded. Existing local HTML/Markdown, v1 Gemini and no customer source execution preserved in CI checks. No customer-ready EXE or Vercel.
- Next `ㄱ`: strengthen Python import/scope alias-shadow regression and increase independent labeled vulnerability corpus, plan optional vetted JS/TS parser with licensing/packaging cost review, and address actual end-user Windows Defender/SmartScreen/network/PDF visual and third-party NOTICE. No sale/release without explicit owner approval.


## P1-D2 conservative Python import matching (2026-10-26 KST)
- Base main c5df010b7b52643cab214989f50f2948795cb6cd, successful 16/16 previous main CI. Feature branch feature/p1d2-import-binding-accuracy fixes Python alias-shadow false positives without expanding runtime API/deps.
- 20 new fixed synthetic Python cases, 3 regression methods. First completed CI test job: 135/135 PASS; fixture metrics (not real-world): 48 cases, TP17 FP0 FN3, precision 100%, recall 85%. Whole 16-job matrix and new PR Windows CI PENDING at this authored moment.
- Ledger: P1D2_IMPORT_BINDING_20261026.md. JavaScript/TypeScript remain explicitly limited. Local user Windows/Defender/SmartScreen/packet/PDF and third-party NOTICE still unverified. No EXE commercial release.

## P1-D2 final integration (2026-10-26 KST)
- PR #14 https://github.com/hibi89/ai-code-checker/pull/14 MERGED to main as 545b751871b377cf52f245abb8efc6e602bd2682 from feature ef5038f25f98514c931f7bd524b669ce1d4721cf.
- Final feature standard Tests https://github.com/hibi89/ai-code-checker/actions/runs/40336933987 16/16 PASS, 135 Python unit tests PASS, packaged Windows EXE GUI/PDF/P0-D-E-F-G-H https://github.com/hibi89/ai-code-checker/actions/runs/40336934413 PASS, performance/dependency 3/3 https://github.com/hibi89/ai-code-checker/actions/runs/40336933977 PASS. Post-merge main CI and follow-up docs-SHA need fresh check.
- P1-D2 fixed 48 synthetic Python cases: TP17, FP0, FN3; synthetic precision 100%, recall 85%; JS/TS 2 limited only. NOT a security certification nor representative real-world accuracy. Legal NOTICE, clean consumer Windows Defender/SmartScreen/OS traffic/Korean PDF visual and sales gates remain NOT APPROVED.
- Next ㄱ: Evaluate vetted JS/TS parser options (license size config/trust/Windows compatibility, offline no-new-cost); add independently selected Python labeled corpus, then real clean-Windows/privacy and third-party redistribution notices. No EXE release, paid API, Vercel or customer code transfer without explicit approval.
## Phase2 P1-E JS/TS feasibility branch (2026-10-26 KST)

- Last verified main `bd4e7041a813fc599aa7cf51ae6d68158c64466c`; [main Tests 16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40337436335). New `feature/p1e-parser-probe` compares regex/Node TypeScript/Tree-sitter; implements **CI-only** pinned syntax parser test for JS/TS/TSX and checks package metadata, never runs customer code. Documentation: [P1-E parser feasibility](P1E_JS_TS_PARSER_FEASIBILITY_20261026.md). Outcomes pending real two-OS CI. Product `requirements-offline-build.txt` and JS/TS `limited` status unchanged. Customer EXE release unapproved.

## P1-E verified JS/TS grammar feasibility — CI-only (2026-10-26 KST)

- [PR #15](https://github.com/hibi89/ai-code-checker/pull/15), parser code SHA `4e4cd29bd511a7811098251fedceaaec16004db5`. [Separate parser workflow 40341166881](https://github.com/hibi89/ai-code-checker/actions/runs/40341166881) **Windows 2025 1/1 + Ubuntu 24.04 1/1 PASS**: fixed wheels Tree-sitter 0.26.0/JS 0.25.0/TS 0.23.2, **12 syntax fixtures** (9 valid, 3 malformed), 3 adapter-boundary tests each. Installed license-named paths 1/package, MIT declared in package metadata only, NOT approved commercial NOTICE/distribution. Main product dependency and EXE unchanged; JS/TS still `limited`.
- Initial workflow invalid YAML and overly strict license-string checks were corrected and actual 2-OS CI now pass. Final feature PR/head regular Tests CI requires independent verification before merge; physical clean Windows/privacy/PDF and notices remain blocked. Vercel N/A.

## P1-E integrated parser research (2026-10-26 KST)

- [PR #15](https://github.com/hibi89/ai-code-checker/pull/15) merged into main at `33d20ee5ffc94e72ee4f81d6b6c76ea5a60b46b9`; feature `fdae1c6463da606e0377a277992081c12a4d9173`. Final feature [standard Tests 16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40341532660), [JS/TS/TSX CI Windows+Ubuntu 2/2 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40341532563); 12 synthetic syntax fixtures passed (9 valid, 3 invalid). No JS/TS rule engine shipped; product still limited, no EXE dependency addition. Package MIT metadata and 1 license-named file per package do not establish NOTICE compliance.
- Next GO: optional parser-backed rule adapter prototype, syntax-error fail-closed and independent fixtures, then original notice and real Windows EXE size/privacy/Defender/PDF visual reviews. No commercial release or paid AI API/Vercel.

## P1-F JS/TS syntax pattern prototype (2026-10-26 KST)
- PR [#16](https://github.com/hibi89/ai-code-checker/pull/16) research-only Tree-sitter opt-in grammar-backed adapter; base main `65a30e968cd6a329124cd696720ebe156ef7ae6f`. Runs inert JS/TS/TSX parse, observes direct eval and new Function syntactic candidates; max input 512 KiB/25k nodes, explicit blocked/syntax_failed/missing-parser states. Product `offline_core`/EXE unchanged, JS/TS coverage stays limited.
- [Windows+Ubuntu research 40343388339](https://github.com/hibi89/ai-code-checker/actions/runs/40343388339) 2/2 PASS, 17 curated cases TP8 FP0 FN0 (synthetic pattern labels only). Real-world accuracy, third-party original notices, Windows packaged adapter and customer AV/network/PDF acceptance unverified. [Evidence](P1F_JS_TS_ADAPTER_20261026.md). Final PR code+docs CI pending.

## P1-F final verified integration — 2026-10-26 KST
- [PR #16](https://github.com/hibi89/ai-code-checker/pull/16) MERGED to main `9188a2a3f2df9780e546f5508d26564471caae0d` from feature `4429ae9c798950b3d13769d1dac85aaf696ff321`. Final feature [standard CI 16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40343693225), 142 Python unit tests PASS (previous code feature [40343454967](https://github.com/hibi89/ai-code-checker/actions/runs/40343454967)); [Windows+Ubuntu research parser 2/2 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40343693332). Fixed syntactic research corpus 17 cases, candidate TP8 FP0 FN0 (NOT a real-world security metric).
- Product is unchanged: JS/TS remains limited, native grammars not bundled into customer EXE. Next GO third-party LICENSE/NOTICE + native parser Windows EXE size/security and opt-in actual integration only after gates; real retail Windows/SmartScreen/Defender/OS packet/PDF visual checks outstanding. No release approval, Vercel or paid AI.

## Phase2 P1-G frozen research Windows native package & actual license text (2026-10-26 KST)

- Base main `d4cc67eafc21edcef83b2eadc63595e7298e7010` CI 16/16 PASS. Feature `feature/p1g-native-package-notice-audit`, code SHA `317777b874166e5e5e62c3678436d40a630e667c`. [New native package & license CI 40345534242](https://github.com/hibi89/ai-code-checker/actions/runs/40345534242) **3/3 PASS**; [standard Tests CI 40345533817](https://github.com/hibi89/ai-code-checker/actions/runs/40345533817) **16/16 PASS, 147 unittest PASS**. Windows research EXE baseline 8,563,435 bytes; native Tree-sitter grammar 9,053,820 bytes, delta +490,385 bytes (not actual customer EXE delta). Pinned packages' ORIGINAL installed LICENSE files physically read/hashed on Ubuntu+Windows; Python core Tree-sitter 0.26.0 Windows/Linux license hashes differ; no original full text uploaded or legal approval claimed. 4/4 frozen synthetic probes PASS. [Full evidence](P1G_NATIVE_NOTICE_EVIDENCE_20261026.md). Product GUI/EXE untouched, JS/TS still limited, release blocked.


## P1-G final merged evidence — 2026-10-26 KST
- PR #17 https://github.com/hibi89/ai-code-checker/pull/17 MERGED at main 3a94feb607aea7908094f6adb24318ad6220bffa from feature ac23a7c00fcd8fef54679fad18640c0211b4e0bc.
- Final feature standard Tests https://github.com/hibi89/ai-code-checker/actions/runs/40346261310 16/16 PASS, 147 Python unittests; Windows+Ubuntu original-wheel LICENSE / native research packaging https://github.com/hibi89/ai-code-checker/actions/runs/40346261152 3/3 PASS.
- Research unsigned Windows standalone baseline 8,563,435 B, parser candidate 9,053,820 B, delta +490,385 B; four frozen synthetic grammar cases PASS. THIS IS NOT REAL CodeCheckerOffline.exe DELTA. Installed three pinned wheel original LICENSE files physically read and hashed; Tree-sitter 0.26.0 Windows/Linux LICENSE bytes and SHA differ.
- Full evidence: P1G_NATIVE_NOTICE_EVIDENCE_20261026.md. Original GUI EXE/product JS/TS limited coverage unchanged, no customer EXE shipment; no legal NOTICE/commercial license approval, independent retail Windows Defender/SmartScreen/network/PDF acceptance outstanding. Main documentation CI must be checked separately.


## P1-H summary tables — merged 2026-10-27 KST

- **Latest verified code merge:** [PR #18](https://github.com/hibi89/ai-code-checker/pull/18) merged into main `b101245295ff8ccd55e1330c3e3f60c1520173d1`, feature code `3e58e9d0373a817e7a3f5774b60a3db40a38d62b`; rollback baseline before this work `144564698de820189f2683946e3e1b8000250272`. Later documentation commits move main HEAD and must be checked separately.
- **Functionality:** `offline_report.py` now adds severity-based candidate counts, rule-ID candidate counts and extension-inferred language/file counts to both self-contained local HTML and Markdown. Path entries that were excluded or unsupported are included in the language count; pruned directory contents are unknown and omitted. Candidate statistics include unverifiable citations and are never called confirmed defects. The Python scan, v1 Gemini, offline GUI/EXE build and network design remain unchanged.
- **New test suite:** `tests/test_report_summary.py` adds four synthetic checks for summary total consistency, empty findings, forged citation, and offline/CSP markup. Before merge, [regular CI](https://github.com/hibi89/ai-code-checker/actions/runs/40488934355) **16/16 SUCCESS**, [Windows smoke](https://github.com/hibi89/ai-code-checker/actions/runs/40488934266) **1/1 SUCCESS**, and [synthetic performance/dependency inventory](https://github.com/hibi89/ai-code-checker/actions/runs/40488934291) **3/3 SUCCESS**, all at feature SHA `3e58e9d`. Source code itself was not executed against real customer data. Post-merge/docs main CI must be verified separately before final release.
- **Remaining gates:** actual clean customer Windows click/Defender/SmartScreen/OS packet capture/HTML Korean PDF visual proof, complete binary native license/NOTICE approval, independent rule accuracy, optional JS/TS integration, progress/cancel and explicit user-controlled cleanup. No Vercel production and NO commercialization approval.
- **Next `ㄱ`:** first re-check latest main SHA/docs and CI, then implement a narrowly scoped P1-E progress/cancellation UX with fail-closed partial status and tests (or another proven highest-priority gap). Use feature branch/PR, avoid customer code execution/network/data upload, preserve original v1 CLI, and update docs after verified work.


## P1-E cooperative progress/cancel — merged 2026-10-27 KST

- [PR #19](https://github.com/hibi89/ai-code-checker/pull/19) **MERGED** into main at `12c51540e646bc088aa24faa96aaf48f5fb843dd`, verified feature SHA `5790939162b790c87542a37017130ca35a13d19d`. Prior rollback main `aec40dfa23f54aa99d13aec295553a2d76b4ee1a`. Documentation commits following this merge change main HEAD.
- **Implemented:** cooperative `ScanControl` cancellation and `ProgressUpdate` phases in `desktop_core.py`; optional per-file progress/checkpoints in `offline_core.py`; actual Tk progress indicator and cancel button plus main-thread queue events in `desktop_ui.py`. No new package/API/service, no customer code execution, no changes to legacy Gemini mode. Default uninstrumented scan path retains old static-check behavior.
- **Cancellation contract:** read/normalize is bounded but cannot stop within an individual file/ZIP read; scan checks between files, and report verification/atomic publication has a final checkpoint. Cancellation before publication raises `ScanCancelled` and does not create a new report pair; once publication starts, it is not interrupted and the UI disables cancel, preserving atomic no-clobber writer guarantees.
- **Tests:** new `tests/test_desktop_progress_cancel.py` 7 synthetic regressions; `scripts/windows_gui_e2e.py` adds scripted Tk cancel button and stale result check. [General tests Actions 40490662936](https://github.com/hibi89/ai-code-checker/actions/runs/40490662936) **16/16 PASS**, Windows Python 3.11 **158 unit tests PASS**; [Windows EXE/Tk/PDF synthetic Actions 40490662926](https://github.com/hibi89/ai-code-checker/actions/runs/40490662926) **1/1 PASS**; [synthetic performance/inventory Actions 40490662990](https://github.com/hibi89/ai-code-checker/actions/runs/40490662990) **3/3 PASS**. Observations are on feature SHA, NOT proof of post-doc main CI/customer PC.
- **Incomplete:** true intra-read cancellation, actual clean Windows human GUI/Defender/SmartScreen/OS network capture/visual Korean PDF, full packaged NOTICE/license approval, user-controlled report cleanup, measured independent product rule accuracy and JS/TS parser product integration. No Vercel (N/A), no EXE commercial release.
- **Next `ㄱ`:** verify live latest main SHA/CI and `HANDOFF.md`; prioritize P1-E local user-controlled cleanup/report integrity or fail-closed JS/TS integration only after required licensing/Windows proof. Keep product/source safety and upfront permission gates.


## P1-I current-session report cleanup — merged 2026-10-27 KST

- **Main source:** [PR #20](https://github.com/hibi89/ai-code-checker/pull/20) merged at `779b611bf2f932fa219631c32f810fa3253111c4` from feature SHA `78d5ad675ee0bf7d2502fc91e8d72db4fe5b9825`. Prior main rollback `a5ab0ab0745ca1b6b3cc31e1af0a009dbf6a7a79`; newer documentation commits advance main.
- **Implemented:** `report_cleanup.py` exact currently generated HTML+Markdown two-file receipt (hash, stat identity, parent directory) with explicit user confirmation and strict fail-closed checks. `desktop_core.py` attaches optional receipt after successful report write; `desktop_ui.py` provides opt-in "현재 보고서 삭제" and invalidates stale controls. No deleting original code, directory walking, previous reports or automatic retention. `scripts/map_frozen_licenses.py` recognizes the new first-party module without certifying legal redistribution.
- **CI evidence:** [Tests 40493402697](https://github.com/hibi89/ai-code-checker/actions/runs/40493402697) **16/16 PASS**, Windows Python 3.11 **167 unit tests PASS**. [Windows EXE/Tk 40493399705](https://github.com/hibi89/ai-code-checker/actions/runs/40493399705) **1/1 PASS**, incl. synthetic confirm/decline GUI and freeze manifest/provenance gates. Report-specific 8 new synthetic contract cases + component mapper regression. Initial missing-file errors and initial provenance counter/test expectation mismatch were resolved with actual CI traces; do not repeat unsuccessful approaches.
- **Known limits:** No true atomic paired deletion; if second unlink fails, remaining file is reported and manual inspection needed. Receipt does not persist across app restarts; files above 32 MiB per report lack in-app deletion eligibility. Actual clean retail Windows, Defender/SmartScreen, OS network packet capture, visual Korean PDF and original bundled legal NOTICE still **UNVERIFIED**. Sales/release BLOCKED. Vercel/Production **N/A**.
- **Next `ㄱ`:** verify newest main SHA and CI; prioritize next real gap (explicit output-path safeguards/recovery tests or independent Windows/privacy/license acceptance), while avoiding new cloud dependency, source execution, unapproved spending or release. See `P1I_REPORT_CLEANUP_EVIDENCE_20261027.md`.


## P1-J path isolation and offline output safety — merged 2026-10-27 KST

- **Verified source:** [PR #21](https://github.com/hibi89/ai-code-checker/pull/21) merged main `8485413205007366ffa683ec272a198f1f47f394`, branch `feature/p1j-output-path-privacy-guards`, final feature `27d7825a51575fdd9ed82d0774811df48d4699d4`, baseline `d58f1f2459c7964586019b3da889a28b2b2006cb`. Docs commits after source merge move main HEAD.
- **Implemented:** `output_safety.py` refuses UNC/device-looking outputs, existing symlink/reparse-point components, non-directory targets and output equal to/inside a folder being scanned. `desktop_core.py` checks before ingesting input; `offline_report.write_report` applies guard to all local reports. `scripts/map_frozen_licenses.py` classifies newly packaged first-party module with no third-party legal approval changes. 8 synthetic tests and Windows scripted path-containment case.
- **Evidence:** [Tests 40494794235](https://github.com/hibi89/ai-code-checker/actions/runs/40494794235) 16/16 success, Windows Python3.11 **175 unittest PASS**; [Windows candidate/Tk/PDF 40494794185](https://github.com/hibi89/ai-code-checker/actions/runs/40494794185) 1/1 success; [synthetic performance/dependencies 40494794230](https://github.com/hibi89/ai-code-checker/actions/runs/40494794230) 3/3 success.
- **Limits:** filesystem TOCTOU races not proven safe, mapped/synchronized folders may still transmit reports; no OS-level packet capture or retail Windows/Defender/SmartScreen/PDF visual/complete original EXE NOTICE acceptance. **NO customer release**, no paid API or Vercel. See `P1J_OUTPUT_SAFETY_EVIDENCE_20261027.md`.
- **Next `ㄱ`:** recheck latest main SHA/workflows and advance independent privacy/Windows acceptance and licensing gates, or narrowly scoped fail-closed improvement based on reproduced evidence; maintain source privacy and explicit human release approval.


## P1-K verified frozen Windows full Tk workflow — merged 2026-10-27 KST

- Source [PR #22](https://github.com/hibi89/ai-code-checker/pull/22) merged as `39d5db20ac3db3294bd45ce76f6d32c4f9fab65d` from feature head `523679d26dc6e7d3a8756bd8a2652cb19a25450f`. Prior main rollback `2d7bfd30a0bb50547c86841abc2fbb673339dcb1`; docs later advance main HEAD.
- Actual Windows PyInstaller **frozen EXE** runs developer-only `--scenario-smoke`: synthetic Tk paste → input preview → offline static scan → Korean HTML/Markdown pair → receipt/GUI controls. This closes source-scripted GUI vs packaged EXE functionality gap without changing normal GUI or Gemini v1. `scripts/build_windows_portable.ps1` now rejects EXE if frozen workflow smoke fails.
- [General Tests CI 40496583577](https://github.com/hibi89/ai-code-checker/actions/runs/40496583577) **16/16 PASS**, [Windows candidate 40496583605](https://github.com/hibi89/ai-code-checker/actions/runs/40496583605) **1/1 PASS** including `PACKAGED_TK_FULL_WORKFLOW_PASS`. All runs at feature SHA; post-document main Actions not separately established.
- **Still UNVERIFIED:** clean consumer Windows PC, human GUI click, Defender/SmartScreen, actual OS packet capture, manual Korean PDF visual inspection, third-party binary NOTICE/licensing, signed EXE/retail deliverability. These block commercialization. OS-level privacy cannot be inferred from GUI synthetic smoke. See `P1K_FROZEN_GUI_ACCEPTANCE_20261027.md`.
- **Next `ㄱ`:** verify live latest main/PR/Actions; implement bounded automated customer-device acceptance procedure or targeted stability bugfix, preserving no-source-upload and no-release boundaries.


## P1-L Windows read-only retail acceptance evidence — MERGED 2026-10-27 KST

- Source [PR #23](https://github.com/hibi89/ai-code-checker/pull/23) merged main `f7fccd8f1440b1ca562c341ca4a21f2dd124b363`; feature `19496ba18e3b213d2589118407543b029dab6763`; baseline `17b9eb9d4ff66a803df9e2ac5593a746f96d8d29`. Documentation commits after merge change main SHA.
- **Implemented:** optional explicit `scripts/windows_acceptance_readonly.ps1` collects a no-clobber local-only binary SHA, length, Authenticode observation and Defender settings, without changing OS security/firewall/registry or scanning customer files. `scripts/windows_acceptance_contract.py` checks current EXE bytes against receipt, rejects forged release claims/extra private metadata and leaves SmartScreen, packet, actual AV file scan, human PDF visual, retail Windows and legal NOTICE gates UNVERIFIED. CI attached in `.github/workflows/windows-portable.yml`, 10 synthetic unit tests added.
- **Verified:** [general Tests 40498518599](https://github.com/hibi89/ai-code-checker/actions/runs/40498518599) 16/16 PASS, Windows Python3.11 185 tests PASS. [Windows EXE/Tk/receipt 40498518640](https://github.com/hibi89/ai-code-checker/actions/runs/40498518640) 1/1 PASS: frozen Tk scenario, local Defender settings observation and current-EXE SHA comparison pass. Defender settings are **not** an actual antivirus EXE scan. No user device accessed or modified; no remote reports/artifacts uploaded.
- **Release still BLOCKED**: clean retail Windows/SmartScreen/Defender scan/OS packet/PDF manual visuals, original redistribution NOTICE and explicit owner approval not performed. See `P1L_WINDOWS_READONLY_ACCEPTANCE_20261027.md`; normal offline GUI/Gemini v1 unchanged, Vercel N/A.
- **Next `ㄱ`:** verify current main SHA and docs; prioritize actual verifiable Windows privacy/reliability gap (without modifying user's OS or exposing customer code), then legal source/license acceptance. Do not infer certification or sell/download EXE from hosted CI.


## P1-M Windows mapped network drive output safety — 2026-10-27 KST

- [PR #24](https://github.com/hibi89/ai-code-checker/pull/24) **MERGED** source main `72c89d36828267ffb44edb1d9dd1ee47e65dc5b2`, verified feature `1eba94597ed6074d10db7feec41bf81f54fe55a4`, baseline `d73b2f71eabce091de22dc6f4f42f324f23dc6a6`. New docs commits move `main` further.
- **Implemented:** `output_safety.py` checks `GetDriveTypeW` on Windows *before* output folder filesystem traversal, denies mapped remote drive type 4 and unclassified/non-writable drives (0, 1, 5), permits local fixed/removable/RAM (3, 2, 6). Existing no-clobber output and UNC/reparse/source-root protections preserved. GUI informs users that local cloud-sync folders remain a user-managed risk.
- **Verified CI:** [general 40499792387](https://github.com/hibi89/ai-code-checker/actions/runs/40499792387) 16/16 SUCCESS, Windows Python3.11 **190 unit tests PASS**, incl. mocked remote denial and real Windows GetDriveTypeW test; [Windows candidate 40499792348](https://github.com/hibi89/ai-code-checker/actions/runs/40499792348) 1/1 SUCCESS. No customer data, external API or OS setting changes.
- **Limits:** remote **input** paths, OneDrive/other local-sync folders, TOCTOU races and external traffic not fully excluded. No actual OS packet capture, clean consumer Windows, real AV scan/SmartScreen, human PDF visual, bundled original legal NOTICE; customer EXE release remains BLOCKED. See `P1M_WINDOWS_MAPPED_DRIVE_SAFETY_20261027.md`.
- **Next `ㄱ`:** inspect live `main` and CI, select remaining verifiable input privacy or accuracy gap, use minimal dependency-free feature PR. Human device and legal release gates remain outstanding.


## P1-N offline v2 remote-input locality hardened — 2026-10-27 KST

- [PR #25](https://github.com/hibi89/ai-code-checker/pull/25) **MERGED** source SHA `7fcb2ca3e665773f1464d5636ca0a8fcf1d493a9`, verified feature head `89d9823955f0817ef0e03e96d69effc16ae24943`, prior main `f09de9a7af879a4ddf7f75686d91efa163c8cdbd`. Docs advance main afterward.
- **Implemented:** new `input_safety.py` blocks offline v2 UNC/device paths, Windows mapped remote/unknown drive types and symlink/reparse ancestors *before* source metadata and code reads. `desktop_core.py` applies in preview and run; `offline_core.scan_path` applies to direct offline CLI. Old Gemini v1 `code_input.load_path` remains unchanged. GUI discloses local-only input and native picker limitations. First-party frozen license map updated without legal signoff.
- **Tests:** [standard 40501255327](https://github.com/hibi89/ai-code-checker/actions/runs/40501255327) **16/16 PASS**, Windows 3.11 **200 Python tests PASS**, incl. 10 new input privacy cases; [Windows EXE 40501255271](https://github.com/hibi89/ai-code-checker/actions/runs/40501255271) **1/1 PASS**; [Phase2 performance/inventory 40501255370](https://github.com/hibi89/ai-code-checker/actions/runs/40501255370) **3/3 PASS**.
- **Limitations and release:** Native file picker may enumerate remote paths, local-sync directories still exist, legacy Gemini mode not modified, hostile filesystem TOCTOU and real OS packet capture not verified. Retail Windows/Defender EXE scan/SmartScreen/Korean PDF human visuals/original NOTICE and owner approval still BLOCK commercial release. Evidence: `P1N_OFFLINE_INPUT_PRIVACY_EVIDENCE_20261027.md`.
- **Next `ㄱ`:** check live `main` SHA/CI; address next measurable scanner rule-accuracy, source/manifest risk or output integrity gap without client uploads, paid APIs or retail release.

## P1-O SQL local-binding accuracy — 2026-10-27 KST

- [PR #26](https://github.com/hibi89/ai-code-checker/pull/26) **MERGED** into main source commit `f4ae5e4cd164aa74ca1e41861d2c9cac43544101`; final feature code/test SHA `b3a10d835a0f27b8b85a0db6772acb3973bb51b9`, baseline main `29e27f6e055d4726b77f7e4debfb854aa2d20c53`.
- **Implemented:** `static_checks.py` now flags direct local/module/function statement `query = f"SELECT..."` or SQL string concatenation followed by `cursor.execute(query)`. Typed direct assignment supported. Reassignment, nested/conditional writes, imports, and scope shifts are conservatively invalidated. No general taint/dataflow, indirect aliases or return-expression inference.
- **Observed feature-head CI:** [Tests 40504757775](https://github.com/hibi89/ai-code-checker/actions/runs/40504757775) **16/16 PASS**, hosted Windows Python3.11 `Ran 207 tests`, `OK (skipped=1)`; [Windows packaged 40504757873](https://github.com/hibi89/ai-code-checker/actions/runs/40504757873) **PASS**; [performance/dependency 40504757925](https://github.com/hibi89/ai-code-checker/actions/runs/40504757925) **3/3 PASS**.
- **Labeled synthetic corpus:** 52 Python cases, TP20/FP0/FN2, precision 100% and recall ~90.91% only within hand-authored labels; remaining misses are dynamic builtin/import indirection. JS/TS still limited. Real-world precision/recall and client app security UNVERIFIED.
- **Files:** `static_checks.py`, `scripts/evaluate_rule_accuracy.py`, `tests/test_rule_accuracy.py`, `tests/test_sql_local_binding.py`. No new dependency, internet API, code execution, original v1 modification or commercial EXE publication.
- **Outstanding:** independent customer-code accuracy, return/nested expression limitations, clean consumer Windows/Defender/SmartScreen, OS packet capture, PDF visual and original third-party NOTICE/license review. Retail release blocked; no Vercel.
- **Next `ㄱ`:** verify latest main SHA and source test state, then select another evidenced scanner accuracy bug or product usability gap; use a small source-preserving branch/PR, test before merge. Post-document main Actions are not inferred from feature-head CI.

## P1-P SQL return/if-arm coverage and static-only precision — 2026-10-27 KST

- **Source MERGED:** [PR #27](https://github.com/hibi89/ai-code-checker/pull/27) main merge commit `3591838789f1d56f8508cd696b647949fb45c2a1`; feature head `734dc498b4d33961fd8746c79c52312b0dd30e2b` on baseline main `7894488a4719f75ea2dde9a30c973e2417463ba6`. Revert PR #27 to restore baseline without force push.
- **Actual change:** `static_checks.py` now detects direct `return cursor.execute(query)` and `if/else` arms where direct variable assignment and execute share the same straight-line arm; branch-crossing/outer-scope values and nested wrapped returns remain unsupported. Literal-only SQL addition and f-strings with no substitution are no longer labeled as dynamic SQL.
- **Validated:** [Tests 40506589531](https://github.com/hibi89/ai-code-checker/actions/runs/40506589531) **16/16 PASS**; hosted Windows 3.11 214 unittest cases, `OK (skipped=1)`. [Windows portable candidate 40506589522](https://github.com/hibi89/ai-code-checker/actions/runs/40506589522) **1/1 PASS** and [synthetic performance/dependency 40506589542](https://github.com/hibi89/ai-code-checker/actions/runs/40506589542) **3/3 PASS** on final feature head.
- **Frozen labeled corpus:** 61 Python cases, TP24/FP0/FN2, synthetic precision 100%/recall 92.31%; 2 JS/TS limited excluded, actual customer-code accuracy UNVERIFIED. Only synthetic self-generated fixtures exercised, not real projects.
- **Files changed:** `static_checks.py`, `tests/test_sql_local_binding.py`, `scripts/evaluate_rule_accuracy.py`. Original Gemini v1, offline input/output protections and Windows packaging remain unchanged, no new dependency or API/service cost.
- **Release blockers unchanged:** real clean retail Windows GUI/Defender executable scan/SmartScreen, OS-level packet evidence, human Korean PDF visual review, original third-party NOTICE/license certification and owner authorization. No Vercel, no commercial EXE distribution.
- **Next `ㄱ`:** verify actual current main SHA/docs and evidence, then prioritize independently provable accuracy/coverage issues and product usability; do not expand speculative broad dataflow without labeled adversarial tests. Latest post-doc main CI may not be visible in PR-run-only lookup.

## P1-Q literal option precision and static SQL f-strings — 2026-10-27 KST

- **Implemented/merged:** [PR #28](https://github.com/hibi89/ai-code-checker/pull/28), source merge `47e60a3be76c99b0bc640b4cb1f3dc5889626cc4`; final feature head `75b779c988c349514b7da63549e9922c5277558d`; prior main `8babbd9804db957d527f6c28bd55fdafc7403b1e`.
- **Actual behavior:** `static_checks.py` recognizes explicit truthy syntax-literal `subprocess.run(shell=1/-1/'yes')` and explicit falsey `requests.get(verify=0/0.0/'')` for known imported APIs, not uncertain dynamic variables. `verify=None` remains unflagged because it delegates to the default. SQL constant-only f-string formatting no longer creates dynamic-SQL false positives; dynamic variables still reported as candidates. No eval/source execution.
- **Verification:** [Tests 40507666937](https://github.com/hibi89/ai-code-checker/actions/runs/40507666937) 16/16 PASS; hosted Windows Python 3.11 `Ran 222 tests`, `OK (skipped=1)`; [Windows portable EXE 40507667081](https://github.com/hibi89/ai-code-checker/actions/runs/40507667081) 1/1 PASS; [performance & dependency inventory 40507666955](https://github.com/hibi89/ai-code-checker/actions/runs/40507666955) 3/3 PASS, on final feature HEAD.
- **Synthetic cases only:** fixed corpus expanded to 72 Python labels: TP29 FP0 FN2; synthetic precision 100%, recall 93.55%. 2 JS/TS limited samples excluded; real-world accuracy UNKNOWN. Eleven new synthetic cases and eight unittest methods in this phase.
- **Changed files:** `static_checks.py`, `tests/test_option_literal_accuracy.py`, `scripts/evaluate_rule_accuracy.py`; original Gemini v1 intact, no new dependencies, no paid API, no customer source upload.
- **Release blocked:** no independent clean customer Windows/real SmartScreen/Defender EXE scanning, OS network trace, human Korean PDF visual, complete original third-party NOTICE/license obligations or explicit commercial approval. No Vercel/Production URL.
- **Next `ㄱ`:** verify current main SHA/CI/feature evidence and select a concrete analyzer accuracy/product workflow gap with tests first. Do not infer customer code quality from fixed synthetic labels, or post-document main CI from PR workflow checks.
