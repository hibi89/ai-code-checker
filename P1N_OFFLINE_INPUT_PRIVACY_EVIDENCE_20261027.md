# P1-N Offline v2 remote-input locality — 2026-10-27 KST

## Verified GitHub evidence
- [PR #25](https://github.com/hibi89/ai-code-checker/pull/25) **MERGED** to `main` source SHA `7fcb2ca3e665773f1464d5636ca0a8fcf1d493a9` from verified feature `89d9823955f0817ef0e03e96d69effc16ae24943`. Baseline main `f09de9a7af879a4ddf7f75686d91efa163c8cdbd`.
- [Tests Actions 40501255327](https://github.com/hibi89/ai-code-checker/actions/runs/40501255327): **16/16 successful**, Windows Python 3.11 **200 unit tests PASS**, including local Win32 GetDriveTypeW acceptance and synthetic mapped-input denial before project ingestion.
- [Windows EXE/Tk/PDF/receipt/provenance Actions 40501255271](https://github.com/hibi89/ai-code-checker/actions/runs/40501255271): **1/1 successful**, with packaged synthetic Tk workflow, binary SHA/local Windows receipt and original third-party NOTICE release gates preserved.
- [Phase2 synthetic performance/dependency Actions 40501255370](https://github.com/hibi89/ai-code-checker/actions/runs/40501255370): **3/3 successful**.

## Gap, alternative designs and chosen implementation
- Earlier P1-M protected output drives, but `desktop_core._base_bundle`, `desktop_core.run_scan` and `offline_core.scan_path` could still touch an input path's metadata and content if it belonged to a drive-letter-mapped Windows network share. This can cause SMB traffic without Python socket calls.
- Alternative A: change the original `code_input.load_path` and all original Gemini v1 source loader behavior; rejected to preserve original mode.
- Alternative B: new `input_safety.validate_offline_input_path` guard at **offline v2** entrypoints only; selected. UNC/device path and symlink/reparse ancestors are blocked; Windows mapped drives are queried with standard-library Win32 `GetDriveTypeW` before folder/file metadata access. Fixed/removable/RAM local drive types allowed, remote/unknown/optical or failed drive queries fail closed. No new dependency, host/OS settings change, cloud feature or paid API.
- `desktop_core.inspect_input` via `_base_bundle` and `run_scan` validate source locality before is_dir or bounded loader; `offline_core.scan_path` validates for direct offline CLI users. `desktop_ui.py` discloses local-only input and file-picker boundary. `scripts/map_frozen_licenses.py` tracks new first-party module; no legal redistribution approval implied.
- `tests/test_input_safety.py` adds 10 synthetic/Windows-platform cases: UNC/device, mapped drive, preview, scan, direct CLI, unknown/failed query, local types, symlink ancestor, valid local scan, unchanged original loader, real Windows drive type. No customer data or network shares were accessed.

## Remaining limitations / release gates
- **Not an OS packet-capture proof.** The user's OS file chooser can browse remote paths prior to final selection/validation, and cloud-synchronized *local* folders are not fully detected. Privileged adversarial reparse-point races/TOCTOU and remote source access from the unchanged legacy loader are not covered by this v2 input guard. No guarantee of no network traffic for arbitrary OS configuration.
- Actual clean retail Windows/SmartScreen/Defender EXE malware scan/OS packet observation, human Korean PDF visual review, original third-party bundled LICENSE/NOTICE redistribution signoff, signing and owner commercial approval remain **UNVERIFIED/BLOCKED**.
- The original legacy Gemini v1 `code_input.load_path` was not edited. No EXE artifact uploaded, released, sold, signed or deployed. No Vercel/production URL applicable.
- Recovery: revert PR #25; never force push. Docs commits following source merge advance `main` SHA and do not automatically prove new CI.
