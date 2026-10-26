# CODE CHECKER v2 — Phase2 P0-D Frozen EXE Evidence and Notice Review

Updated 2026-10-26 KST. This document defines **engineered evidence**, not a lawyer's approval of distribution. Main baseline before PR: `52dfd71f2999cc910a06f80cc59ea9662d702785`, status latest main 16/16 PASS at [GitHub Actions](https://github.com/hibi89/ai-code-checker/actions/runs/40318012383).

## The gap

Previous P0-C reviewed **12 installed Windows build-environment Python distributions** and package metadata. That is not a manifest of what the PyInstaller `--onefile` EXE physically contains. An installed build package (e.g. PyInstaller) may not be embedded as a runtime package; conversely Python/Tcl/Tk DLLs and transitive resources may be embedded but absent from Python dependency inventory.

## P0-D implemented evidence pipeline

- `scripts/audit_frozen_exe.py` opens the actual `dist-windows/CodeCheckerOffline.exe` via the installed PyInstaller `CArchiveReader`. Enumerates **CArchive metadata entries** with names/type codes and declared compressed/uncompressed sizes. Opens nested PYZ TOC via `open_embedded_archive` and enumerates module names, not code contents. Records EXE SHA-256/size and high-level Python/Tcl/Tk native-binary presence flags. Does not extract archive members or execute the app's source.
- Separately, from the Windows **installed build environment**, inventories pinned build-root (`pydantic==2.12.5`, `pyinstaller==6.22.3`) distribution graph and hashes matching `LICENSE`, `LICENCE`, `COPYING`, `NOTICE`, `COPYRIGHT` text-file names, with recorded size and installed relative paths. **These hashes are installed-wheel evidence, not proof of inclusion in EXE.**
- Writes a full local JSON evidence manifest to `.build-windows/frozen-exe-evidence.json` after building with `scripts/build_windows_portable.ps1`; `.build-windows` is gitignored. CI prints **only metadata counts and hashes** and deliberately does **not** publish/download an unsigned EXE or embedded source manifest.
- Any unreadable nested Python archive, absent embedded PYZ, or absent Python runtime DLL fails the audit gate. A passing gate only establishes that **a real packaged EXE was inventoried**: report fields `license_compliance_certified=false`, `third_party_notice_ready_to_distribute=false`, `customer_release_ready=false` are required and asserted in CI.
- Regression tests use **fake in-memory TOC metadata**, not executable payloads, and ensure audit never flips license/customer release flags true.

## Third-party compliance worklist — mandatory human review

| Item | Evidence P0-D gathers | Mandatory unresolved work |
|---|---|---|
| PyInstaller bootloader | EXE CArchive, binary SHA, installed PyInstaller metadata | Check the exact installed `COPYING` and PyInstaller bootloader license exception, plus if any PyInstaller files themselves shipped. Official [PyInstaller license](https://pyinstaller.org/en/stable/license.html) says generated executable distribution may be licensed separately subject to **dependencies' licenses**; do not infer those are satisfied |
| Pydantic, pydantic-core, typing-extensions, annotated-types | Build dist metadata, possible PYZ/natively bundled component names | Map every embedded component to exact package/version/license, inspect text contents, establish runtime vs build-only and attribution obligations |
| CPython interpreter and standard library | python3xx.dll marker, code archive/module names | Identify exact CPython and native runtime distribution licenses/notices, check requirements for customer package |
| Tcl/Tk, tkinter, resource files | Tcl/Tk DLL marker and CArchive resource names where present | Match exact Tcl/Tk binaries and resource files to distro owners/versions and notice/copyright duties |
| Microsoft/VC runtime, other `.dll` or `.pyd` | Full nested archive/native file names and sizes | Trace exact binary owners, applicable redistribution license/restrictions, validate signed provenance |
| Own public MIT code | Git source and EXE entrypoint | Ensure owner copyright/third-party notices and public MIT distribution commitments are accurate |

## Verification levels and limitations

- **PASS** (only after CI): actual EXE CArchive and PYZ introspected; built-in type/count/native presence guard and pinned installed license metadata hashes recorded. `CArchiveReader` may use host PyInstaller internals: version locked to build tool.
- **NOT proved:** that every observed module maps to a licensed distribution; that every license text is present/read; NOTICE obligations; OS DLL redistribution legality; antivirus/SmartScreen/certificate reputation; OS packet-capture privacy; independent customer PC and physical-click UI, browser Print dialog, PDF text/visual correctness; execution/resource measurements outside CI.
- Never auto-create an `APPROVED_NOTICE` from limited evidence. An eventual `NOTICE` requires full text/legal provenance verification by owner/reviewer before commercial release.
- Source code is public MIT; candidate EXE is **unsigned**, stays on Windows CI runner and is **not uploaded**.

## Commands, without customer data

On authorized development Windows after installing `requirements-offline-build.txt`:

`./scripts/build_windows_portable.ps1` (builds an unsigned EXE, self-test, Tk-start test).

`python -m scripts.audit_frozen_exe --exe dist-windows/CodeCheckerOffline.exe --out .build-windows/frozen-exe-evidence.json`

`python -m unittest discover -s tests -v`

Next: check GitHub CI logs for actual binary manifest count, nested PYZ count, runtime flags and installed license-file count; if successful, mark **inventory gathered / legal NOTICE still pending**. If failing, inspect trace locally without exposing binary/customer contents. No release, no paid API usage or source execution.
