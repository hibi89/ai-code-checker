# CODE CHECKER — HANDOFF (10-point)

Updated 2026-10-26 KST. Official triggers: [코드체커 깃헙 확인해] or ㄱ. Source of truth GitHub and current evidence. Start with CODE_CHECKER_RESUME.md → HANDOFF.md → STATUS.md → AGENTS.md → REQUIREMENTS.md → FINAL_PRODUCT_BLUEPRINT.md → MVP_3DAY_ROADMAP.md → actual source/tests, and verify main/branches/PR/CI.

## 1. Goal, confirmed requirements, technology

Owner-approved: MVP in 3 focused development days, then blueprint gap filling, extensive hardening, real Windows QA, finally optional Kmong sale approval. Primary product is repeat-use Windows offline code-risk checker: TXT/ZIP/folder/paste, localized HTML/Markdown, PDF via browser Print, no required API/license server/subscription. Python 3.11+; Tkinter GUI; Pydantic models; legacy Gemini v1 remains separate and untouched.

## 2. Completed features, changes, decision rationale

- Day1 local ingest, TXT reconstruction, source-map and limited AST rules MERGED PR #2.
- Day2 self-contained Korean HTML/Markdown evidence-verified reporting MERGED PR #3.
- Day3 feature/windows-portable adds desktop_core.py, desktop_ui.py, tests/test_desktop_core.py, optional scripts/build_windows_portable.ps1, pinned requirements-offline-build.txt, separate Windows packaging Actions, DAY3_WINDOWS_GUIDE.md. PR #4 started as draft, awaiting final CI and merge at this writing.
- Architecture choice: Tkinter + headless controller instead of local HTTP server avoids extra service/port/dependency and preserves offline privacy. All input passes through existing safe code_input and offline_core; no code execution and no provider imports in GUI.
- GUI: file/ZIP/TXT/folder/paste, language choice, safe preflight count/mapping, threaded scan, output HTML+Markdown, partial notices, local HTML open. No user login or remote calls.

## 3. Tests, commands, success/fail, scope

- Local developer: python -m unittest discover -s tests -v ; python desktop_ui.py --self-test ; python desktop_ui.py (only GUI-capable system).
- Verified Day3 source SHA c6acab56559c22c7545af218d18a67c061e73203: GitHub Actions run 40307804095 16/16 PASS; Linux job reports 85 tests PASS; headless synthetic packaged path test PASS; Windows Python unit matrix also passed.
- Windows EXE smoke Actions run 40307810915 PASS: Windows 2025, Python 3.13.16, PyInstaller 6.22.3. EXE --self-test created offline synthetic HTML/Markdown. SHA256 sample 8387C4A07AB44E2C3F24741410D14BFEBE899EB57D60212EE707FBA743D9E8DE. No binary artifact shared.
- Actual Tk GUI click, browser PDF print, offline network capture, clean device Defender/SmartScreen, commercial customer acceptance UNVERIFIED.

## 4. Completed / active / pending / blocked

Days1–2 done and merged. Day3 code and candidate package CI tested; PR #4 IN PROGRESS/pending final merge and main CI when written. GUI UX and customer EXE NOT verified. Phase2 blueprint gap, Phase3 hardening, Phase4 sales not started.

## 5. Errors, causes, tries, alternatives, avoid repeats

Prior Day1/Day2 malformed test expectations were fixed in prior commits, no repeating needed. Current Day3 source and Windows packaged smoke PASS on checks listed, no unresolved failures at evidence cutoff. Local GitHub clone previously blocked by DNS; use GitHub connector and remote CI as source. If package test fails later inspect exact runner logs, make one targeted correction, never call paid Gemini automatically or weaken fail-closed behavior.

## 6. Repo, branch, SHA and paths

Repo https://github.com/hibi89/ai-code-checker, Public MIT, default main. Day3 started from main b88bf15f49d83a5caf41e79d56f5ecad64621d72 into feature/windows-portable. PR #4 https://github.com/hibi89/ai-code-checker/pull/4. Important code desktop_core.py / desktop_ui.py / offline_core.py / offline_report.py / tests/test_desktop_core.py. Latest branch SHA changes with docs commits; FETCH actual HEAD. Restore through Git history/feature branch, no force push.

## 7. Production/deployment/environment/commands

No Vercel, cloud service, domain or production URL; NOT APPLICABLE. Development GUI: python desktop_ui.py after installing requirements.txt. Windows candidate: install requirements-offline-build.txt on build PC and execute scripts/build_windows_portable.ps1. Output dist-windows/CodeCheckerOffline.exe, SHA256 printed; not uploaded to public CI artifact store. build prerequisites require optional developer package downloads, customer runtime needs no cloud AI.

## 8. Originals, backup, secrets, forbidden edits

GitHub original v1 preserved in history; no customer input modified. Public repository must NOT contain keys, .env, real customer source/ZIP, confidential reports, proprietary licensing or unreleased paid modules. GUI reports local masked excerpts, with retention/cleanup by user. No hidden telemetry, external fonts/scripts/CDN, code execution or provider fallback; actual outbound network absence needs packet capture verification.

## 9. Next priority, procedure, acceptance, approvals

First check latest PR #4/head and standard matrix 16/16 plus Windows EXE smoke. Merge when clean; confirm main SHA and post-merge CI. Then create final blueprint gap matrix, address high-risk correctness gaps before polishing; verify actual Windows GUI/SmartScreen/network/PDF before any sale. Additional costs, API calls, customer data upload, repo permission changes, private repo creation or public listing require explicit owner approval. User ㄱ means advance next approved unit without repeated questions.

## 10. Updated timestamp, verification evidence and doc base

2026-10-26 KST; precise time not recorded. Evidence was latest verified Day3 code SHA c6acab56559c22c7545af218d18a67c061e73203 + CI 40307804095 + Windows candidate build 40307810915, not physical customer test. Documentation writes/merge create new SHA; refresh before announcing completion. Day3 product is a developer candidate, not sale-ready.
