# Phase2 P0-F — PyInstaller native build provenance and byte evidence

2026-10-26 KST. Prior P0-E [PR #9](https://github.com/hibi89/ai-code-checker/pull/9) merged, 104 unit tests and 16/16 CI pass. P0-E had **92 initially unresolved archive entries** (67 native/system and 25 resource/bootloader). These are categories in the archive *name mapping*, not 92 proven unlicensed components.

## P0-F method
- Inspect the actual packaged Windows onefile EXE using pinned PyInstaller `CArchiveReader` and its local *build* `.build-windows/CodeCheckerOffline/Analysis-00.toc`. Parse TOC only with bounded `ast.literal_eval`, not `eval`/pickle/exec. Neither customer inputs nor third-party source code is run.
- For each previously unresolved **CArchive** entry, compare exact normalized archive-relative path against the generated Analysis build records (binary/extension/data/zip/executable); explicitly distinguish absent, ambiguous, basename-only and unique source claims.
- For uniquely recorded native binaries only, if local build-source file is available and <=32MiB, compare its SHA-256 against the in-memory bytes returned by `CArchiveReader.extract(name)`; **no archive member is written to disk**. Detect and report unequal data. A byte match means this build source was byte-identical, *not* that its vendor ownership or licensing rights have been verified.
- Output a local, gitignored `.build-windows/native-provenance.json` with destination entry names, categories and evidence, but **no source absolute paths/usernames**, and only summary counts in CI logs. Existing `NOTICE_REVIEW_DRAFT.md` remains unapproved and local.
- Add seven synthetic tests for TOC parsing, refusal of injected code, matching/ambiguous/missing builds, true byte equality, private-path removal, and approval fail-closed.
- Windows PR CI executes P0-D and P0-E before P0-F; fail if counts disagree with prior unresolved mapping or any release flags become true. No EXE, source manifest or license texts are published.

## Acceptance and boundaries
- **PASS (if confirmed)**: build-record source candidates for some/all unresolved archive entries, observed exact native bytes for those whose original files are available; every earlier unresolved name accounted for. Record evidence counts, number of matching native hashes, and remaining cases.
- **UNVERIFIED**: owner/copyright of all native files, system-vs-distributable dependency legal rights, CPython/Tcl/Tk/Microsoft/VC license and NOTICE completeness, artifact signing, real consumer Windows / AV / SmartScreen, network packet capture, actual browser PDF visual validation, and representative project-security rule quality.
- **NOTICE and commercial customer release stay BLOCKED**. Even a byte-identical local build source does not grant redistribution permission. Maintain original public/MIT sources and no paid AI requirement.

## Reproduce on an authorized development Windows
`./scripts/build_windows_portable.ps1` (preinstall pinned build dependencies).

`python -m scripts.audit_frozen_exe --exe dist-windows/CodeCheckerOffline.exe --out .build-windows/frozen-exe-evidence.json`

`python -m scripts.map_frozen_licenses --audit .build-windows/frozen-exe-evidence.json --mapping-out .build-windows/ownership-candidates.json --notice-draft-out .build-windows/NOTICE_REVIEW_DRAFT.md`

`python -m scripts.reconcile_native_build --mapping .build-windows/ownership-candidates.json --analysis-toc .build-windows/CodeCheckerOffline/Analysis-00.toc --exe dist-windows/CodeCheckerOffline.exe --out .build-windows/native-provenance.json`

The commands operate only on a user-authorized, **locally built application** and local package provenance. Do not publish intermediate files; the output is diagnostic.
