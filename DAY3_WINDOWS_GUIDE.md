# CODE CHECKER — Day 3 Windows portable MVP guide

Status: developer candidate ONLY. No customer distribution, sales, or security-completeness claim.

## Design decision

Two approaches compared: (A) Tkinter standard-library desktop GUI + headless controller versus (B) local HTTP server and browser frontend. Tkinter avoids listening ports, running a background web server, service infrastructure and additional GUI dependencies. Both require platform UX testing. Selected (A) to minimize API/hosting cost and reuse the existing safety boundary.

## Run with Python

On a Windows machine with Python 3.11 or newer, from the repository root:

    python -m pip install -r requirements-offline.txt
    python desktop_ui.py

Choose source file/TXT/ZIP, folder, or paste. For TXT/paste, select a language; if the TXT has explicitly delimited FILE headers, set language to Auto so each section extension applies. Click (1) Input preview to see files, bytes, lines, excluded/unsupported count and expected Python AST vs generic-only coverage. Click (2) Local scan to generate Korean HTML and Markdown. Use Open HTML and browser Print to PDF.

The GUI does not import the legacy Gemini client. No customer project is executed, dependencies are not installed by the application, and no account, model key or cloud backend is required to scan. The GUI uses a worker thread and disables closing while the operation runs. Cancellation is not yet implemented.

Default output directory is under the current user's home folder: CodeCheckerReports. Report names contain current local date/time and microseconds. Existing reports are never overwritten. Reports can include masked excerpts or source paths; keep and delete them locally. Do not use cloud-synced folders without considering the data transfer risk.

## Optional Windows executable candidate

The packaging commands download developer build dependencies only when an authorized developer explicitly runs pip. The customer EXE runtime does not download a model or require an API key.

    python -m pip install -r requirements-offline-build.txt
    powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_portable.ps1

The script checks a Windows environment, builds an unsigned one-file EXE using pinned PyInstaller, declines to overwrite existing output, and runs a synthetic self-test on the generated EXE. It prints SHA256. Output: dist-windows/CodeCheckerOffline.exe. Intermediate files: .build-windows. Never commit EXE, source snippets, real customer reports, tokens or other private assets to this public repository.

GitHub PR validation adds a Windows 2025 runner packaging + synthetic EXE smoke, without publishing an artifact. The CI build and self-test confirm that imports, bundled modules and offline scan/report path work in a Windows runner; they DO NOT validate actual Tk button rendering, Windows Defender/SmartScreen, code signing, network traffic observation, PDF printing, enterprise policy, or a clean user's PC.

PyInstaller has a commercial-use packaging exception, but final licenses/attributions for all redistributed dependencies must be independently audited before sale. Unsigned EXE can trigger SmartScreen/antivirus warnings.

## Test and acceptance

    python -m unittest discover -s tests -v
    python desktop_ui.py --self-test

Expected --self-test exit code 0 means a temporary synthetic paste can be scanned and a verified offline report written. GUI startup/display or actual button interaction remains UNVERIFIED by the automated test.

Required prelaunch checks: source/ZIP/folder/paste actions on clean Windows, limits and exclusions, partial/status error display, unicode paths, package Defender checks, physical offline network capture, browser PDF, report cleanup, performance & memory, licensing and refund/support policy. Do not label the product complete until these are verified.
