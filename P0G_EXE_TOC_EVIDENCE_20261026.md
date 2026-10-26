# Phase2 P0-G — EXE build TOC cross-check (2026-10-26 KST)

## Baseline and objective

- Previous confirmed `main` SHA: `abd72767318672f5060a75ebd0da8982c44b0db0`; its standard Tests workflow completed successfully (Actions run 40323750839).
- P0-F left **12 of 92 previously unresolved CArchive names** without unique Analysis build-file claims; the 67 byte-identical native matches remain build provenance, not owner/license proof.
- P0-G checks these remaining items against **actual, locally built PyInstaller `EXE-00.toc`**, while retaining their observed CArchive typecodes. No EXE, originals, NOTICE text or detailed private build paths are committed.

## Compared approaches

| Option | Evidence | Cost/performance | Risk/maintenance |
|---|---|---|---|
| A. Infer remaining resources from filenames/known PyInstaller conventions | No concrete build record proof | Fast and free | Conflates familiar names with source ownership; prone to false positives |
| **B. Parse exact EXE build TOC as inert, bounded literal metadata** | Can establish whether packaging stage declared a same-name record | Local Python, no API cost or execution of bundled/customer code | More testable; still unable to prove legal ownership or redistribution rights |

Approach B is selected within already-approved offline/source-preserving investigation scope.

## Implementation and verification

- `scripts/reconcile_exe_toc.py`: bounded `ast.literal_eval` for generated `EXE-00.toc`; walk only inert tuple/list/dict data; collect normalized archive names, record types and a boolean indicating source-path presence. Never serialize source paths.
- Require identical EXE SHA-256 across P0-D and P0-F, exact P0-F accounting, actual CArchive name membership and release/license flags remaining false; ambiguous multiple records stay ambiguous.
- Every pending CArchive item is reported as **unique EXE packaging TOC claim**, **ambiguous**, or **no EXE TOC claim**. *None* confers vendor identity, copyright proof or redistributable NOTICE.
- `tests/test_exe_toc_provenance.py`: 8 synthetic tests for safe TOC parsing, exact/missing/ambiguous counts, bad SHA/row accounting, release gates, duplicate names, attempted expression injection, unsafe names, oversized TOC.
- Windows portable CI builds a fresh unsigned EXE, runs P0-D/E/F, then P0-G against `.build-windows/CodeCheckerOffline/EXE-00.toc`. Evidence JSON stays local in ignored `.build-windows/exe-toc-evidence.json`; only aggregate counts are logged.
- Verified feature pre-handoff-doc SHA `49583688f99e44486c83167fbc5d571c0851fb91`: [standard CI 16/16 PASS, 119 unittest](https://github.com/hibi89/ai-code-checker/actions/runs/40328196934) and [Windows packaged CI PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40328196858). Real 12 pending names: **11 unique exact-name EXE TOC record claims; 0 ambiguous; 1 with no EXE TOC record**. No owner/license certification. Re-check final docs SHA and post-merge CI.

## Remaining release gates

Owner/license/NOTICE provenance for CPython, Tcl/Tk, VC and PyInstaller bootloader remain subject to primary-source legal review. Independent clean Windows, human GUI/printing and Korean PDF glyph/layout, SmartScreen/Defender and OS network capture remain **UNVERIFIED**. JS/TS and Python scanner precision/recall still require benchmarked improvements. No EXE distribution, customer code upload, paid AI API use, account/security change, or commercialization approved.

## Reproduction

After the existing P0-D/E/F commands and with the pinned Windows build environment:

```powershell
python -m scripts.reconcile_exe_toc --prior .build-windows/native-provenance.json --audit .build-windows/frozen-exe-evidence.json --exe-toc .build-windows/CodeCheckerOffline/EXE-00.toc --out .build-windows/exe-toc-evidence.json
```

Do not overwrite existing local evidence; use a fresh ignored build directory for each reproduction.

## Verified integration record (2026-10-26 KST)

- P0-G code plus eight tests merged by [PR #11](https://github.com/hibi89/ai-code-checker/pull/11) into main SHA `cdf23e171a59258e2659fb72c634a44eea687065` from feature `59e79133514e9b4d5b55ce915835c1735acd4317`.
- [Final feature Tests 16/16 PASS, 119 unittests](https://github.com/hibi89/ai-code-checker/actions/runs/40328799451) and [Windows EXE E2E/P0G evidence PASS](https://github.com/hibi89/ai-code-checker/actions/runs/40328799432): EXE TOC exact-name unique claims **11**, ambiguous **0**, no claim **1**. No claim means insufficient build metadata, not necessarily missing code or a licensing violation.
- Original merged SHA main Actions run [40329090414](https://github.com/hibi89/ai-code-checker/actions/runs/40329090414) initially queued; check later HEAD and run outcome. No customer release approved.
