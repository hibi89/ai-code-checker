# CODE CHECKER v2 — Windows GUI + Browser PDF Synthetic QA

Updated 2026-10-26 KST. Scope: GitHub Actions hosted Windows Server 2025 (Python 3.13) with generated synthetic sources only. **NOT a clean consumer PC acceptance certificate.**

## Decision and evidence

- [PR #6](https://github.com/hibi89/ai-code-checker/pull/6): Windows Tk GUI widget integration, packaged Tk startup, Edge browser PDF print. Prior stable main: `fe03de7bfd12587a8c57a39aed922c715ae8863e` (Actions 16/16 PASS).
- **Code commit:** `d6e4005998edeafc5a1c262281f29a747d3582c7` — [Windows CI success](https://github.com/hibi89/ai-code-checker/actions/runs/40313412431); [full CI success](https://github.com/hibi89/ai-code-checker/actions/runs/40313412364) 16/16 and additional [push CI success](https://github.com/hibi89/ai-code-checker/actions/runs/40313404319).
- The packaged executable `CodeCheckerOffline.exe --gui-smoke` instantiated, updated and destroyed a real Tk window; `--self-test` scanned synthetic code and wrote HTML and Markdown. **No binary uploaded** and the EXE remains UNSIGNED.
- `scripts/windows_gui_e2e.py` launched a real Tk mainloop on Windows and invoked Tk widget callbacks for chosen Unicode-path TXT, ZIP, ignored-folder, pasted Python, and rejected unsafe ZIP. It checked complete/partial states, blocked input, invalidating stale HTML, local output, HTML open via mocked OS call and unchanged input contents.
- In that synthetic GUI process, Python `socket.socket.connect` and `socket.create_connection` were patched to raise, and completed without attempted Python socket calls. This is NOT an OS packet capture or guarantee about all bundled/system/browser network activity.
- `scripts/windows_browser_pdf_smoke.py` opened only locally generated, escaped Korean HTML with installed Microsoft Edge (`msedge.exe`) headless, with background networking disabled; it produced a **96,799-byte PDF** beginning `%PDF-`, in a Unicode-path output folder. PDF was not uploaded or visually examined. This proves headless local HTML→PDF works in that CI runner, not that a customer's UI Print dialog was used.

## Actual regression and corrections (not hidden)

1. Initial Windows script `python scripts/windows_gui_e2e.py` failed to import root modules. Fixed GitHub workflow to run `python -m scripts.windows_gui_e2e` / `...windows_browser_pdf_smoke` from repository root.
2. Tk test compared the `ttk.Button` configuration string rather than widget state. Corrected to `button.instate(['disabled'])`. This allowed the full scripted GUI flow to pass. Kept GUI source fix to invalidate stale results on changed input/error.
3. Initial PDF fixture used a Korean report filename where report writer only allows ASCII safe slugs. Changed **test filename** to `synthetic-print`, keeping Unicode folder and Unicode PDF filename. Final head code test succeeded.

## Verification levels

| Gate | Result | Evidence/scope |
|---|---|---|
| Windows packaged Python scanner + HTML/Markdown | PASS | Unsigned EXE `--self-test` on Windows runner |
| Packaged Tk root startup | PASS | `--gui-smoke` synthetic init/refresh/destroy |
| Real Tk window + scripted widget controls | PASS | TXT/ZIP/folder/paste/blocked, local report, mocked external opener |
| Unicode path | PASS | Synthetic TXT/folder and browser PDF paths |
| Headless Edge browser PDF render/export | PASS | PDF signature and file size; **visual text/page QA not yet done** |
| Source mutation | PASS synthetic | Synthetic source bytes unchanged |
| Basic in-process Python socket guard | PASS synthetic | No socket connection attempts; packet-level **UNVERIFIED** |
| Independent clean Windows GUI, mouse/keyboard, installer | UNVERIFIED | No consumer-machine session/device and no physical user interaction |
| Defender/SmartScreen, signing, enterprise controls | UNVERIFIED | Unsigned EXE may be blocked or warned |
| Browser Print dialog, PDF page visual quality, Korean glyphs | UNVERIFIED | Headless output PDF was not visually inspected |
| OS-level network/telemetry packet observation | UNVERIFIED | Must measure system/browser process traffic separately |
| Commercial redistribution license/SBOM, performance, sales | UNVERIFIED | Later Phase2 P0-C and Phase3/4 |

## Reproduction (authorized developer)

`python -m pip install -r requirements-offline-build.txt` (build machine network/pip only; not consumer scanning).

`python -m scripts.windows_gui_e2e` (Windows with Tk display).

`python -m scripts.windows_browser_pdf_smoke` (Windows with installed Edge or Chrome).

`powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_portable.ps1` (Windows unsigned candidate build, synthetic `--self-test` and `--gui-smoke`).

`python -m unittest discover -s tests -v` (all-platform headless tests).

The probes use temporary generated sources/reports; leave customer data, actual API keys, private code and binary artifacts out of the Public/MIT repository and GitHub artifacts.

## Next gates

1. Merge PR #6 only on final-head green Windows smoke and standard 16-job CI; verify new main CI.
2. Phase2 P0-C benchmark measured 200 files / 12,000 lines / multi-MB and human review of dependency licenses, packaging notices and pinned transitive versions.
3. User/clean PC acceptance: actual GUI interaction, Defender/SmartScreen, offline traffic capture, browser Print dialogue, Unicode rendering and PDF visual inspection. If not available, keep UNVERIFIED; do not manufacture screenshots or passing outcomes.
