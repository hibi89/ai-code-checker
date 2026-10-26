# CODE CHECKER — STATUS

Updated: 2026-10-26 KST. Product: Windows offline MVP developer candidate; not customer release.
Repository: https://github.com/hibi89/ai-code-checker (Public/MIT). Baseline before Day3: main b88bf15f49d83a5caf41e79d56f5ecad64621d72.

## Approved sequence

3-focused-day MVP → final blueprint gap analysis and feature fill → privacy/security/reliability/performance hardening → clean Windows acceptance → Kmong launch only on separate approval.

## Delivery board

| Stage | Result |
|---|---|
| Day1 safe TXT/ZIP/folder/paste scanner and source mapping | MERGED PR #2, CI passed |
| Day2 Korean HTML/Markdown offline report | MERGED PR #3, CI passed |
| Day3 Tk desktop input/preview/scan/report/open | IMPLEMENTED in feature/windows-portable, PR #4; headless CI tested |
| Day3 unsigned Windows portable EXE candidate | BUILT + synthetic packaged self-test PASS on GitHub Windows 2025; no downloadable binary uploaded |
| Real GUI click/visual, browser PDF, clean customer Windows and SmartScreen | UNVERIFIED |
| Final blueprint gap closing, network observation, security and commercialization | NOT STARTED |

## Day3 files and behaviors

- desktop_core.py: metadata-only preview using safe readers; does not run static analysis during preflight. Exposes Python AST/generic-only file counts, exclusions and line/byte totals.
- desktop_ui.py: Tkinter source file, ZIP, folder or paste; conservative language choice; mandatory preview; worker-thread scan; explicit partial/blocked status; open local HTML; refuse window close during active work. The GUI never imports the legacy Gemini provider.
- tests/test_desktop_core.py: 9 synthetic headless tests for preview, 1,200-line TXT, multi-file TXT, ZIP, paste, no code execution, no network mock, no overwrite and import without GUI display.
- requirements-offline-build.txt and scripts/build_windows_portable.ps1: pinned PyInstaller 6.22.3 / Pydantic 2.12.5 for candidate build; Windows-only onefile windowed EXE; prints SHA256; runs bundled synthetic self-test; refuses EXE overwrite.
- .github/workflows/windows-portable.yml: PR-based Windows runner builds and tests unsigned candidate but intentionally does not publish artifact. Standard .github/workflows/tests.yml also compiles the offline modules and runs self-test.
- DAY3_WINDOWS_GUIDE.md and README.md: local usage, packaging, operational and commercialization caveats.

## Verification evidence

- Day3 code PR: https://github.com/hibi89/ai-code-checker/pull/4 .
- Tests at code SHA c6acab56559c22c7545af218d18a67c061e73203: Actions run 40307804095 PASS 16/16; Linux Python run 85 unittest PASS (76 inherited + 9 new) and synthetic desktop_ui.py --self-test PASS. Also Windows variants in matrix.
- Windows packaging job run 40307810915: success on Windows 2025 Python 3.13.16, PyInstaller 6.22.3; executable CodeCheckerOffline.exe generated and self-tested, printed CANDIDATE_BUILT_SMOKE_PASS.
- Sample unsigned EXE SHA256 (run 40307810915): 8387C4A07AB44E2C3F24741410D14BFEBE899EB57D60212EE707FBA743D9E8DE. The artifact is NOT uploaded for customer use; may differ on subsequent runs.
- Following documentation commit(s) and merge should be checked against actual newest branch and main Actions runs; do not assume unchanged SHA.

## Risks and pending acceptance

- GUI window rendering, clicks, paste text persistence, HTML open in real browser, print-to-PDF, Windows path/UTF8, Defender/SmartScreen and clean-device behavior have NOT been run by a human/GUI automation.
- Network capture proving zero source exfiltration has NOT been performed; offline architecture and synthetic socket mocks are evidence but not a network audit.
- Binary is UNSIGNED, packaging is only a candidate, PyInstaller/Windows CI does not guarantee antivirus compatibility.
- Current bounds: max 200 eligible files, max 1 MiB per file, 8 MiB total, 20 MiB ZIP input. Ignored directories may not all be enumerated in coverage; precise discovery count/coverage needs hardening.
- Python static AST checks are shallow rules, JS/TS generic patterns only. Complete status is NOT proof of no defects. Report pair write is no-clobber but a forced process kill is not full two-file atomic transaction.
- Original v1 Gemini CLI unchanged, no paid APIs called. Public repo has no customer sources, keys or sensitive proprietary distribution material.

## Next

1. Confirm PR #4 latest SHA and both standard CI and Windows packaging CI success; merge non-force, verify main SHA and new main CI.
2. Next user ㄱ: phase 2 blueprint gap matrix: inventory implemented / unimplemented / excluded / unverified and prioritize actual end-to-end Windows clean-device QA and functional gaps. If GUI/EXE acceptance cannot run here, label UNVERIFIED, do not claim release.
3. Update STATUS.md and HANDOFF.md after any major implementation or verification; resume automatically with [코드체커 깃헙 확인해].

Vercel/Production: NOT APPLICABLE, local-only application.
