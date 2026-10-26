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
