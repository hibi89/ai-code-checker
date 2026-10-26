# CODE CHECKER — HANDOFF (10 required sections)

Last revision: 2026-10-26 KST. Latest code SHA and CI must be fetched rather than inferred. Resume trigger: **[코드체커 깃헙 확인해]** / **ㄱ**.

## 1. Goal, final product, confirmed technologies
Approved sequence: 3-focused-day MVP → blueprint gap filling → broad performance/privacy/security hardening → clean Windows verification → optional Kmong launch with fresh permission. Product is an offline, repeat-use Windows code-risk checker (TXT, delimited TXT, ZIP, folders, paste) and Korean HTML/Markdown/Print-to-PDF. Python 3.11+, local AST static rules, Tkinter GUI, Pydantic, optional unsigned PyInstaller candidate. No required API key/server/subscription. Gemini v1 remains separate/unchanged.

## 2. Completed capabilities, changes and decisions
- Days1–3 merged through PR #2/#3/#4: input normalization, source mapping, Python AST and generic patterns, candidate evidence gate, Korean self-contained reports, local no-clobber writer, Tk GUI, preflight, Windows unsigned EXE synthetic smoke.
- [Phase2 GAP audit](BLUEPRINT_GAP_MATRIX_20261026.md): 25 blueprint requirements and measured unknowns. Choice of coverage-first over third-party analyzer addition, to avoid a false overall complete status while folders are intentionally pruned.
- Feature branch `feature/blueprint-gap-phase2`: metadata-only ignored/symlink/depth-limited subtree names, bounded traversal, unknown child count, partial scan state, Korean preflight/HTML/Markdown disclosure, new synthetic tests. Original v1 loader not modified.

## 3. Tests, commands, passed/failed and limitations
- Verified main f0c2570 [Actions 16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40309370848); original Day3 85 unit tests; [Windows packaged EXE smoke PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40308464932).
- Feature P0-A tests: `python -m unittest discover -s tests -v`, `python desktop_ui.py --self-test`; expected new cases in `tests/test_pruned_coverage.py`; check live CI for actual PASS/FAIL and exact count.
- No real-customer project run, independent clean Windows GUI click, network capture, Windows SmartScreen/Defender, actual PDF print, licensing audit or performance benchmark. All UNVERIFIED, not passed by inference.

## 4. Done / in progress / pending / blocked
Day1–3 MVP source merge DONE, not commercial release. Phase2 gap matrix + P0-A coverage implementation in feature branch, CI/PR/main integration IN PROGRESS. P0-B Windows GUI/privacy/PDF and P0-C benchmark/licensing PENDING. P1 JS/TS/Python accuracy and report UX PENDING; phases 3/4 PENDING.

## 5. Errors, evidence, causes, avoid retries
Previous Day1 malformed test fixtures and Day2 Markdown expectation mismatch were fixed before merge; do not repeat. Prior direct GitHub clone failed DNS; connected GitHub and Actions provided evidence. Current P0-A tests should be judged from live CI logs; if a failure occurs inspect exact traceback, fix minimum then rerun once after substantive correction. Do not use paid provider requests or execute customer code.

## 6. Repo / branches / SHA / key paths
Public/MIT https://github.com/hibi89/ai-code-checker ; Day3 merged `main` f0c257058f43298167e6777f315db01ae294fd86. Phase2 branch `feature/blueprint-gap-phase2` from that main; HEAD changes with docs and tests, query it. New `offline_coverage.py`, `tests/test_pruned_coverage.py`, modified `offline_core.py`, `desktop_core.py`, `offline_report.py`; `BLUEPRINT_GAP_MATRIX_20261026.md`. Original v1 provider code untouched. Do not force push.

## 7. URL, Vercel, executable, environment
No Production URL/Vercel project — NOT APPLICABLE. GUI dev: `python -m pip install -r requirements-offline.txt` then `python desktop_ui.py`. Windows candidate build in `scripts/build_windows_portable.ps1` after `requirements-offline-build.txt`. Unsigned CI EXE was not published as a downloadable artifact; actual customer EXE UNVERIFIED.

## 8. Originals, backup, sensitive inputs, restrictions
Git history contains original v1 plus merged MVP; rollback by main SHA f0c2570 or PR revert. No raw customer ZIP/source, secrets, .env, actual reports, raw provider output, proprietary sales packages to Public MIT repo. Input source read-only, output local only; masked excerpts still can be sensitive. No default network/telemetry/CDN/unsafe code execution. Network inactivity needs observed proof on actual Windows.

## 9. Next work, steps, acceptance and approvals
1. Check latest feature branch PR/CI. Merge only if tests pass. Verify final main SHA and CI; refresh docs if actual status differs.
2. P0-B actual Windows UI click, selected TXT/ZIP/paste and Unicode paths, HTML browser/PDF, Defender/SmartScreen, packet capture; use actual evidence, else label UNVERIFIED.
3. P0-C measure 200-file/12k line synthetic performance and resource bounds, dependency licenses. Then Python/JS adapter and report features.
4. Any paid spending, external customer code transfer, key/API usage, privacy/permission changes, new private repo or launch requires explicit owner approval.

## 10. Timestamp, code baseline, verification scope
2026-10-26 KST (exact minute not recorded). Main source evidence f0c2570; current Phase2 documents are feature-branch proposed work; do not claim their PR merged until confirmed. Current verification is GitHub CI/synthetic. No live customer acceptance.

## Phase2 P0-A completion addendum (2026-10-26 KST)

- **GitHub:** [PR #5](https://github.com/hibi89/ai-code-checker/pull/5) merged at `2ab40c2e06638cac8aca15a2fd50aa7941336f1f`; feature head `5afd848da250e7b351ace82937b08275139c42f8` CI 16/16 PASS, 89 unit tests PASS. Windows EXE synthetic smoke at the same head PASS.
- **Files:** `BLUEPRINT_GAP_MATRIX_20261026.md`, `offline_coverage.py`, `offline_core.py`, `desktop_core.py`, `offline_report.py`, `tests/test_pruned_coverage.py`. Original v1 loader unchanged. Rollback through PR revert or prior `main` f0c2570.
- **Behavior:** excluded/pruned directory names are inventoried without entering them; child file count UNKNOWN; folder scan `partial`, local GUI preflight and Korean reports show exclusions. No API/paid service/extra runtime dependency.
- **Remaining:** real clean Windows GUI click, PDF print, packet capture, Defender/SmartScreen, performance and licensing are UNVERIFIED, no release. No Vercel.
- **Next `ㄱ`:** confirm current main + post-merge CI and latest docs HEAD; create next feature branch for P0-B Windows GUI/print/privacy verification or P0-C synthetic benchmarks as supported by tools, and keep untested acceptance gates explicitly unverified. Update STATUS and HANDOFF on further substantive progress.

## Phase2 P0-B additional handoff (2026-10-26 KST)

- Parent main SHA before new feature: `fe03de7bfd12587a8c57a39aed922c715ae8863e`, latest main CI 16/16 PASS. New `feature/windows-gui-pdf-e2e` PR [#6](https://github.com/hibi89/ai-code-checker/pull/6). Evidence at code SHA `d6e4005998edeafc5a1c262281f29a747d3582c7`: Windows CI [40313412431](https://github.com/hibi89/ai-code-checker/actions/runs/40313412431) PASS, standard 16/16 [40313412364](https://github.com/hibi89/ai-code-checker/actions/runs/40313412364) PASS. Later docs and merge create different SHA; check newest.
- Files: `desktop_ui.py` (test-only Tk on_ready, EXE `--gui-smoke`, clearing stale output state); `scripts/windows_gui_e2e.py` (real Windows Tk callbacks and safe fixtures); `scripts/windows_browser_pdf_smoke.py` (Edge synthetic local HTML→PDF); Windows workflow and candidate build script; [evidence/limitations ledger](WINDOWS_GUI_PDF_EVIDENCE_20261026.md).
- Pass scope: hosted Windows server Tk window source GUI, scripted TXT/ZIP/folder/paste/blocked, local report and open callback mock, temporary Unicode paths, no Python socket connects in synthetic test, Edge 96,799-byte PDF with `%PDF-`, packaged unsigned Tk startup and packaged synthetic scanner. This is **not** physical customer desktop, actual interactive browser Print dialog, PDF visual glyph/layout verification, packet inspection, SmartScreen, or signing.
- Windows CI had two test-harness issues resolved: script import was changed to `python -m scripts...`; Tk ttk disabled detection uses `.instate()`; PDF fixture uses safe ASCII slug while Unicode folder/PDF path remain. Preserve these fixes.
- Procedure on next `ㄱ`: recheck GitHub PR #6 latest head/actions; merge if clean and confirm new main CI; then prioritize Phase2 P0-C performance/limits/dependency SBOM and schedule separate independent Windows acceptance. Do not infer missing safety acceptance or sell.

## Post-merge handoff — P0-B complete in main source (2026-10-26 KST)

- P0-B PR [#6](https://github.com/hibi89/ai-code-checker/pull/6) **merged main at `2294cfc458c104fbfa20dd452e87009696dcf15c`**. Verified final feature SHA `57486ecd4fbe0a07e75e3e14439deed60c882b08`: standard Actions 16/16 PASS, Windows Actions 1/1 PASS including Tk flow, packaged Tk startup and Edge headless PDF.
- Run `python -m scripts.windows_gui_e2e`, `python -m scripts.windows_browser_pdf_smoke` on developer Windows with local runtime prerequisites. Synthetic fixtures only. GUI tested by scripted widget invocation (not physical clicking). PDF signature/size checked, visual pages and real Print dialog NOT checked. Python socket monkeypatch is NOT OS-level network observation.
- Files now in main: `scripts/windows_gui_e2e.py`, `scripts/windows_browser_pdf_smoke.py`, `WINDOWS_GUI_PDF_EVIDENCE_20261026.md`, updated `desktop_ui.py`, Windows smoke workflow and packaged EXE script. Existing v1 Gemini unchanged; no EXE distributed.
- **Next user `ㄱ`:** verify actual newest main/CI first; then create feature branch Phase2 P0-C measured synthetic benchmark for 200-file/12,000-line/multi-MB and minimal offline dependency licensing/SBOM review. Preserve reporting honesty and no external API calls; if actual clean customer Windows, PDF visuals, packet capture or SmartScreen cannot be tested, explicitly mark UNVERIFIED.

## Phase2 P0-C implementation and CI handoff (2026-10-26)

- Feature `feature/p0c-benchmark-sbom`, [PR #7](https://github.com/hibi89/ai-code-checker/pull/7), based on main `ec4c03f5670e6a582f46b6c91fbdb9ae90b8da1b` (16/16 CI PASS). DO NOT infer merge: verify real branch/PR/main SHA at every resume.
- New files: `scripts/benchmark_offline.py` (synthetic 1,200-line TXT, 12-file ZIP, 200×60 files/12k, 200×60 ~6.04MB, 201-file reject, report writing, `tracemalloc`), `scripts/offline_dependency_inventory.py` (installed Python dist metadata closure; license status always REVIEW_REQUIRED), `tests/test_benchmark_inventory.py` (fixture/unit tests), `.github/workflows/p0c-performance-inventory.yml` (Windows+Ubuntu performance and Windows offline build inventory/CVE lookup), [P0C evidence](P0C_PERFORMANCE_SBOM_20261026.md).
- LF deterministic fixture code SHA `fe71b439d50a1d194f9a50c4e6c4180b07130c8a`: [dedicated CI 40317040322 3/3 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40317040322). Windows 200-file 12k lines 0.8835s and ~6.04 MB 1.9216s, peak traced Python allocation 11.608 MiB; Linux 0.6912s and 1.7263s, peak 11.607 MiB. These are ONE hosted CI observation incl. scanner+report writing, not customer hardware/EXE launch or RSS measurements. 201-files blocked.
- Windows Pydantic==2.12.5 + PyInstaller==6.22.3 pinned install closure: 12 Python dist records, no missing license metadata/unresolved, `pip-audit` reported no known vulnerabilities *at CI lookup time*. Does not cover actual packaged EXE, Python/Tk/Tcl DLLs, copyright notices or unknown CVEs; do not claim complete security/licensing approval.
- Test-harness errors: initial mock metadata was dict lacking `.get_all` and optional `packaging` library absent from original runtime test matrix. Corrected fake to `email.message.Message` and patched Requirement in isolated synthetic test; 93/93 unit tests PASS at code SHA `151f9285223e0c021e4ae51f8f6111655b3be2a7`. New LF byte-regression test means 94 expected; check actual CI.
- Next work: PR #7 final SHA regular 16-job matrix and dedicated 3-job CI; inspect logs and merge non-force if all pass. Update STATUS/HANDOFF to actual main and confirm post-merge Actions; next P0-C detailed packaged binary SBOM+NOTICE and clean-device acceptance (not currently accessible). Current product is NOT customer-ready, Public MIT and Gemini v1 preserved, no paid model API, user data upload or artifact distribution.

## Final P0-C merge and next owner GO (2026-10-26 KST)

- PR [#7](https://github.com/hibi89/ai-code-checker/pull/7) **MERGED** as `625313622c4dcefe055848acab399181dbba9bde`, feature SHA `1186e2cd80ddf60350f7e0eb66e1b2263769e8c7` standard 16/16 [CI PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40317430334) and P0-C dedicated Windows/Ubuntu 3/3 [CI PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40317437467). Re-check post-merge main CI and documentation HEAD.
- Synthetic performance: 1200-line TXT 0.1217s Windows / 0.0888s Linux; ZIP12 0.0862s/0.0700s; 200 files 12k lines 0.8835s/0.6912s; 200 files 12k lines ~6.04MB 1.9216s/1.7263s. Each included offline scan, report verification, HTML+Markdown filesystem save, one CI observation. Traced Python peak ~11.61 MiB on 6MB workload (not RSS). 201-file input rejected. Existing caps 200 eligible files/1MiB per file/8MiB total.
- P0-C inventory: exactly 12 installed Python distribution metadata records for pinned PyInstaller/Pydantic Windows build closure; 0 missing metadata; `pip-audit` known-vulnerability scan negative at lookup. **NOT complete binary SBOM, full license notice audit, code signing/antivirus/enterprise approval.**
- Modified files on main: `scripts/benchmark_offline.py`, `scripts/offline_dependency_inventory.py`, `tests/test_benchmark_inventory.py`, `.github/workflows/p0c-performance-inventory.yml`, `P0C_PERFORMANCE_SBOM_20261026.md`. Preserve original v1 Gemini CLI; no new model API requirement or source transfer.
- Next signal `ㄱ`: validate live main HEAD + CI and start P0-D full bundled component/license and attribution investigation (or core static-analysis coverage improvements afterward). No automatic proprietary sales release or binary distribution. Physical consumer Windows/Defender/SmartScreen, OS packet capture, PDF visual, real customer projects, actual native RAM use remain UNVERIFIED.

## P0-D final merge / next go (2026-10-26 KST)

- [PR #8](https://github.com/hibi89/ai-code-checker/pull/8) merged at main **`c3ca5df250ea81e0bb523ca3f2da2e7e1eb8bd3f`**; feature final head `1ac85f82845e7d8b90a813d0935e3a47cb6ffed0` passed [standard 16/16](https://github.com/hibi89/ai-code-checker/actions/runs/40318937393) with **98/98 unit tests**, and [Windows EXE smoke+manifest 1/1](https://github.com/hibi89/ai-code-checker/actions/runs/40318937450). Refresh main latest SHA/CI because handoff docs push additional commits.
- New `scripts/audit_frozen_exe.py` uses PyInstaller `CArchiveReader` (actual freshly built EXE) to list top-level archive metadata and nested PYZ module names without extraction/execution. `tests/test_frozen_exe_audit.py` synthetic tests ensure report never declares legal/license/release approval. `.github/workflows/windows-portable.yml` generates `.build-windows/frozen-exe-evidence.json` **locally and gitignored**, enforces actual embedded Python DLL + PYZ, does not upload EXE/manifest.
- Windows CI observed **1,018 CArchive entries, 544 nested PYZ modules**, native Python runtime + Tcl/Tk flagged, **12 installed Python build distributions and 30 candidate installed license-text files**. This is *not* actual EXE package license mapping nor a statement that all 30 texts are embedded. See `P0D_FROZEN_EXE_NOTICE_REVIEW_20261026.md` for exact evidence and human review matrix.
- Remaining Phase2/Phase3 gates: map every actual archive entry/native DLL to vendor/version/license (particularly CPython, Tcl/Tk and VC runtime); read/verify full actual license text/NOTICE obligations; no premature author-approved customer notices. Clean independent Windows/real physical GUI, SmartScreen/Defender, true OS network packet capture, PDF visual inspection, actual binary signatures and published signing reputation remain unverified. No product sale/public EXE release.
- Next user `ㄱ`: check main + latest CI/PR and proceed to P0-E license-owner mapping/NOTICE review candidates and further security/accuracy gaps using tests; never claim compliance without full evidence. No cost-bearing AI, customer data upload, or permissions changes.

## Phase2 P0-E merged handoff (2026-10-26 KST)

- PR [#9](https://github.com/hibi89/ai-code-checker/pull/9) **MERGED main `765ed9d4a9f183e749dfd78d0dc185d73694c609`**; feature head `73341809baf06b30d5472dcb8dfeacaa7a2b03ec` standard [CI 16/16 PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40321463525), **104 unittest PASS**; [Windows EXE/GUI/PDF/P0-D/P0-E PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40321463677). Main post-merge CI must be checked.
- New `scripts/map_frozen_licenses.py`, `tests/test_component_license_mapping.py`, expanded `.github/workflows/windows-portable.yml`, `P0E_OWNER_LICENSE_MAPPING_20261026.md`. CLI consumes P0-D JSON, makes `.build-windows/ownership-candidates.json` and **local, unapproved** `.build-windows/NOTICE_REVIEW_DRAFT.md` with 26 SHA-checked original installed license files, never uploads/returns client files. Full mapping includes 1,562 EXE names; 7 installed distribution owner candidates and **92 unresolved** (67 native/system, 25 archive resource/bootloader). Classification NAME ONLY, not certified component ownership.
- Public package name candidates: annotated-types, packaging, pydantic, pydantic-core, setuptools, typing-extensions, typing-inspection. Classified other names as CPython stdlib 276, Tcl/Tk candidate 923, installed Python package module 261, first-party 8, native installed relative filename 1, CPython DLL 1. None constitutes LICENSE/NOTICE compliance approval.
- Initial added tests failed in fixture-only nested `dist-info/licenses` directory creation; corrected with `parents=True`; final CI and physical archived EXE mapping both PASS. Continue fail-closed with zero claim of source execution/remote transmission.
- **Next action `ㄱ`:** query latest main HEAD/actions/PR; work on actual native dependency ownership/license notice mapping and source distribution notices, plus remaining clean Windows physical GUI, Defender/SmartScreen, real packet capture, PDF visual/readability and Python/JS/TS accuracy. No binary distribution, private customer input, owner permission changes or commercial launch without explicit approval.


## P0-F merged — actual native byte provenance (2026-10-26 KST)

- [PR #10](https://github.com/hibi89/ai-code-checker/pull/10) merged to main `c59f3dc807a11f48949f081263877bf4533467c9`. Feature head `200236091b7b75130bbe010c2478d92b695a0c43` passed [standard 16/16 CI](https://github.com/hibi89/ai-code-checker/actions/runs/40323280004), **111 unit tests**, and [Windows real EXE build/P0-F provenance](https://github.com/hibi89/ai-code-checker/actions/runs/40323280024). Refresh newest main/CI after docs.
- P0-E had 92 names unowned by installed distribution rules: 67 native/system + 25 resource/bootloader. P0-F matched 80 with unique build `Analysis-00.toc` records. **All 67 native binary files** were byte-identical SHA-256 matches to recorded local build files. Remaining **13 non-native** entries have only path linkage; **12** resource/bootloader items have no unique Analysis claim. Do not claim software copyright/licensing approval.
- Files: `scripts/reconcile_native_build.py` (bounded `ast.literal_eval`, local PyInstaller build TOC source claims, in-memory CArchive native byte SHA comparison, source-path suppression), `tests/test_native_build_provenance.py` (7 synthetic cases), Windows CI step and [P0F evidence](P0F_NATIVE_PROVENANCE_20261026.md). No EXE or manifest uploaded; no AI API.
- On next `ㄱ`: check actual GitHub repo status/CI, research remaining 12 PyInstaller bootloader/resource archive entries (using `EXE-00.toc` and structure metadata if appropriate) but only classify proven evidence. Prepare human-review ownership/licenses/NOTICE tasks for CPython, Tcl/Tk, VC, PyInstaller; then prioritize real independent Windows/Defender/SmartScreen/packet/PDF acceptance and static analysis depth. Customer-ready release is **NOT approved**.
