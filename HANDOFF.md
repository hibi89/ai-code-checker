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
