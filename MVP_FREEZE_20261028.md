# MVP freeze: 2026-10-28 delivery target

## Decision
**Functionality first**: a minimum working offline Windows Code Checker, not a polished commercial product. Front-end styling, feature expansion, and supplementary legal engineering are postponed until this end-to-end basic user workflow is continuously green. This changes priority, not the established protection against publishing an unapproved binary or exposing customer code.

## Acceptance definition (MVP, not commercial release)
- From local **file / directory / ZIP / pasted text**, display an input preview and exclusions. No model key, hosted backend, login, hidden telemetry or network request.
- Run deterministic Python static checks without running input code. Show genuine candidate rule and path/line; mark non-Python limited and excluded/failed input partial (never say safe just because scan completed).
- Save locally escaped, self-contained **HTML + Markdown** report with previewed scope and non-overwriting file names. Opening a local report is available in GUI.
- Windows executable **developer candidate** launches the Tk GUI and can finish automated synthetic button controls for preview, scan, output and appropriate cancellation; no Python install required on the target runner.
- Build and unit CI green with no new paid dependencies. No customer secrets or synthetic EXEs uploaded.

## Reproduce in a checkout
```powershell
python -m pip install -r requirements-offline.txt
python -m scripts.mvp_acceptance
python desktop_ui.py --self-test
python desktop_ui.py
```
On Windows with approved packaging dependencies:
```powershell
python -m pip install -r requirements-offline-build.txt
./scripts/build_windows_portable.ps1
```
Generated developer-only binary: `dist-windows/CodeCheckerOffline.exe`. No public upload or automated commercial release. Optional packaging dependencies are developer-side only.

## Evidence interpretation
`scripts.mvp_acceptance` tests seven user-critical contracts with disposable synthetic Python, mixed ZIP and invalid ZIP:
1. Preview of Python input.
2. Real scan with supported Python AST risk candidate, verified finding.
3. HTML/Markdown generated with source mapping and self-contained content.
4. Input unchanged.
5. Report overwrite rejected.
6. Mixed language + excluded secret input reported partial, secret not leaked.
7. Unsafe ZIP traversal blocked without report.

The 16-job Python CI matrix and Windows packaged Tk synthetic workflow separately test cross-platform imports and packaged GUI. This acceptance script is **not** a Windows human UI test, complete static/security audit, malware-free declaration, primary license review, provenance certificate or retail customer approval.

## Deferred after MVP
Cosmetic UI improvements, feature counts, extended parser accuracy/coverage, optional AI/independent agents, automated fixes, sophisticated PDF exporter, packaging polish, marketplace assets. Keep eventual release blockers visible: clean independent customer Windows, SmartScreen/Defender observation, network packet capture, real Korean PDF visual review, original third-party legal NOTICE and owner authorization. The deadline is a target, not evidence of checks not performed.

## Result record
Link exact GitHub PR/main commit and matching Windows CI runs **after** they complete. Do not fill unverified PASS.
