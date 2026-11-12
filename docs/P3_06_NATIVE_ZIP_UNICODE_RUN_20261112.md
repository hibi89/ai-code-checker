# P3-06 — native ZIP extraction + Korean path + Python PATH isolation

Checked: 2026-11-12 KST. Target: Code Checker **95% provisional engineering** (not commercial approval).

## Source / decision
- Production reference branch remains `main@adf3f4ac8fab87c72d176011b0b719de39797db4` (unchanged). Product work: `hibi89/ai-code-checker@feature/retail-private-candidate-20261112`.
- Exact functional CI SHA: `3d92c4c0f3886d80e499261b8b6d44b7791713c4`.
- Reused existing native Windows 2025 PyInstaller/Tk/GUI/HTML-to-PDF validation and P3-05 private ZIP/Windows receipts pipeline.
- Choice A: inspect ZIP manifest and checksum only; insufficient to establish executability of an EXE once extracted.
- Choice B (selected): in a disposable Windows CI temp directory with Korean and space characters, extract the **actual freshly built** EXE from the synthetic unapproved private ZIP and run `--self-test`, `--gui-smoke` and `--scenario-smoke` with system-only PATH and Python-related environment variables removed. No customer code, authentic vendor originals, paid API or EXE release. Hash before and after and confirm existing ZIP/JSON cannot be overwritten. The destination is destroyed with the CI workspace.
- A branch- and path-filtered push trigger runs the existing Windows portable workflow for P95 test changes; no workflow auto-publishing, branch merging, Vercel or customer distribution.

## Exact CI evidence
- [Standard Tests #43224297929](https://github.com/hibi89/ai-code-checker/actions/runs/43224297929): **16/16 SUCCESS** at exact SHA `3d92c4c0f3886d80e499261b8b6d44b7791713c4`.
- [Windows portable candidate smoke #43224297880](https://github.com/hibi89/ai-code-checker/actions/runs/43224297880): **1/1 SUCCESS**, including original source EXE build, hosted Windows Tk UI smoke, synthetic Korean PDF, offline receipt chain and the new **extracted Korean-path EXE** smoke. New step logged:
  - `REAL_FROZEN_WINDOWS_EXE_PRIVATE_ZIP_E2E_PASS`
  - `EXTRACTED_KOREAN_PATH_PYTHON_FREE_EXE_SMOKE=PASS`
  - `ZIP_RECEIPT_AND_BUNDLE_HASHES_VERIFIED=True`
  - `CUSTOMER_RELEASE_READY=False`
- Real Windows hosted built EXE SHA-256: `759c543fb7dfd0b85cce95a8e98d42eef1324d5a6d5d3536c6d87acdf48f31c5`. Hash equality checked for original EXE, ZIP-contained bytes, extracted EXE, and extracted EXE again after the three smoke runs. Original EXE not overwritten.
- "Python-free" log means **hosted runner Python directories were removed from child PATH and Python-related environment variables were unset**; the runner itself still has Python installed. Thus clean no-Python buyer PC remains NOT_VERIFIED, not claimed as an observed customer machine.
- The temporary LICENSE/NOTICE is explicitly invalid synthetic test text. Real rights and distribution permission remain NOT_VERIFIED.
- GitHub-hosted Defender evidence is an observation, not a malware-free guarantee; OS-level packet capture / buyer SmartScreen human acceptance not done.

## Stage assessment
- Prior **90% provisional engineering** (actual Windows EXE→candidate ZIP→receipt integration).
- New +5%p **provisional engineering** for the complete extract/reopen/run verification in a Unicode and space path, child Python PATH isolation, GUI/scenario mode, before/after exact bytes and no-overwrite behavior on native Windows: **95% engineering milestone reached**.
- **Not a measured percentage of all requirements; not a 95% commercial-release pass rate.** `customer_release_ready=False`, **RELEASE HOLD**, source PR draft, no public sales upload.
- Human-dependent final 5%: actual Windows10/11 buyer test without Python installed, true Defender/SmartScreen/network/PDF visual evidence, frozen Tcl/Tk/CPython/PyInstaller and remaining binary owner and original LICENSE/NOTICE/redistribution rights, real owner candidate ZIP, support/refund/price and explicit seller release authorization. No owner work is needed for this engineering checkpoint; user participation required to finish release acceptance.

## Continuity / rollback
- Prior `34acee6f28e4b22b9a072ad0e4c31ed2c9727d64` passed P3-05 native EXE/ZIP receipts; P3-06 source SHA `3d92c4c0f3886d80e499261b8b6d44b7791713c4`; existing original `main` unchanged.
- No force push; revert via normal Git commit as needed. Re-run under the existing Windows workflow only when source changes; no repeated empty dispatch. All failed output paths retained on HOLD and never auto-deleted per P3-04.
- **User marker rule:** Keep Code Checker `[작업중]` on central Kmong until verified 95 goal and central score synchronization are completed. Only then can the marker be removed; do not remove during a still-open target attempt.
