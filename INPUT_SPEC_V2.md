# Code Checker v2 — TXT / ZIP Input Contract (Design Only)

Date: 2026-10-26 KST. Branch: `plan/offline-zero-cost-v2`. Status: proposed, NOT implemented in v2.

## Objective
Customer-owned or seller-received TXT, ZIP, folder and pasted-source inputs must use a single safe, offline ingestion pipeline. A project with 1,200 lines is not automatically truncated at 500 lines; an input with 12,000 lines must be either fully analyzed within proved capacity or clearly marked partial. Traversal and parser success are not proof of a complete security audit.

## Supported user flows
| Method | Intended behavior | Current baseline | v2 gap |
|---|---|---|---|
| ZIP project | Select ZIP; preserve paths; enumerate all entries; analyze eligible files | CLI already reads ZIP, no extraction | UI, larger tested limits, comprehensive manifest, per-language coverage |
| Single TXT | Select `.txt`; choose/source-detect language; treat as one virtual source file | CLI accepts .txt; only generic local pattern checks apply (Python AST currently gated to .py/.pyi) | Virtual language attribution with reliable source mapping |
| Combined multi-file TXT | Multiple files in a single readable .txt with strict section markers | NOT supported as reconstruction; CLI currently treats TXT as one file | Strict parser with file+line reconstruction |
| Folder | Select directory; traverse eligible files without following symlinks | Supported in CLI | UX, large input pagination/performance/coverage |
| Paste | Paste code and choose language/filename | CLI stdin supported | UI, explicit language and source name |

## Single TXT
- Without a recognized first-line multi-file header, treat the entire file as ONE source, not a complete project.
- Default language is unknown/basic-only; optional user-selected Python/JS/TS/etc. creates an internal virtual path `input.py` or `input.ts` so matching analyzers can process it while preserving `original_file.txt:line` provenance.
- NEVER claim import dependencies or unprovided project files were analyzed; show `single-file only / dependency context not provided`.
- A raw TXT containing `print("hello")` MUST NOT be labeled as Python AST-reviewed merely because the text looks like Python unless the language was selected or reliably confirmed.

## Combined multi-file TXT contract
An explicit header MUST appear as the first non-blank line for multi-file mode. Every subsequent file starts with the same exact header shape:

```text
===== FILE: src/main.py =====
from auth import check_user
print(check_user())

===== FILE: src/auth.py =====
def check_user():
    return True
```

- Header recognition is line-anchored to the exact `===== FILE: relative/path.ext =====` grammar, with a validated relative path. Section continues until the next header or EOF. Blank lines inside code remain meaningful.
- Do not strip comments, infer missing file boundaries, or silently combine independent sections. For a malformed header, duplicate path, section with no source, or input starting with a malformed candidate marker, return a clear parse error rather than silently dropping code.
- If literal source lines begin with the reserved header sequence, require the user to prefix a backslash or use ZIP; the parser must unescape while maintaining a source line map. A test fixture must cover collision handling.
- Reject absolute paths, `..`, Windows drive names, names containing control characters, case-insensitive/Unicode-normalized duplicates on Windows, symlink-like entries and unsupported extensions. Do not write reconstructed files to the customer project directory.
- Preserve both logical path/line and original TXT source location. Example: `src/main.py:2` (from `combined.txt:3`).
- Mixed-language input uses extension-specific analyzers; unknown extensions are listed in the coverage manifest, not declared clean.
- This is *not* arbitrary natural-language prose parsing. Ambiguous plain TXT remains a single source.

## ZIP contract
- No customer-provided code execution or auto-install, no nested ZIP recursive unpack, no external requests, and no extraction to disk as a default ingest step.
- Validate traversal/absolute paths, path collisions after normalization, archive entries count, compressed/uncompressed bytes, archive bomb behavior, symlinks/special files, encoding and extension policy BEFORE treating a scan as complete.
- Project structure and relative paths should survive ingestion. Ignore `.env`, key material, vendor folders, generated assets and binaries according to explicit policy; indicate every skipped/unsupported file in a local manifest.
- Do not silently keep only the first N files; either scan all eligible files within the measured limit or surface a partial/blocked status with exact counts.
- Metadata/index traversal and actual AST/rule analysis are different stages. The report must enumerate analyzed, skipped, unsupported, failed, unknown and rules run.
- Sensitive file contents never go to the report unless explicitly selected and safely redacted. The default offline scanner sends no inputs anywhere.

## UI and scan status
Initial intake panel: `ZIP` / `TXT` / `Folder` / `Paste`, language selector only when ambiguous, summary preview with file/line/byte counts and exclusions, explicit Start scan.
Scan outputs: `complete` (eligible files analyzed to declared policy), `partial` (eligible files skipped/failed), `blocked` (unsafe/malformed), `cancelled` (user abort). "Complete" is a *coverage* status, not a claim of defect-free code.
Progress indicator must show discovered/eligible/analyzed/skipped/failed; report includes local rule IDs and confidence qualifiers, supported languages and file coverage.

## Bounded resource policy
- Old 500-line cap is removed from new product/licensing plan, NOT from any old human-service labor contract until explicitly changed.
- Existing CLI enforces 50 files, 512 KiB total and 128 KiB/file; current `main` code remains unchanged.
- v2 target benchmark: >=200 supported files and multi-MB synthetic repos, including 1,200 and 12,000-line cases; numbers become a marketed limit ONLY after memory/runtime/Windows validation.
- If resource/time limits are exceeded, no auto-splitting that loses imports, no partial result labeled "all scanned"; opt for deterministic batches with stable file IDs and explicit aggregate coverage.
- No AI token quota, activation server, paid service or telemetry in core local mode.

## Test matrix (offline synthetic only)
1. Single 1,200-line TXT, language Python selected: 1 virtual source, correct original line citations, full eligible content considered.
2. Single TXT with unknown language: basic-only coverage warning; do not run Python AST by guessed extension.
3. Mixed multi-file TXT with imports, blank lines and markers: reconstructed file count + line/source maps; no lost or reordered code.
4. Malformed/ambiguous marker, duplicate normalized paths, reserved marker appearing in code: fail safely or require escaping.
5. 12-file / 1,200-line ZIP and >=200-file and 12,000-line stress fixtures: complete or honest partial with exact count, never silent truncation.
6. ZIP path traversal, symlink, nested ZIP, zip bomb, non-UTF-8, binary, `.env`, oversized and Unicode files: correct block/exclusion statuses; no source execution.
7. Compare same synthetic source provided via directory, ZIP, combined TXT: same eligible rules and findings where logical paths and language align.
8. Network-disabled clean Windows launch and report-open/print checks; source content never sent to remote host, verified, not assumed.

## Acceptance
Product copy may say "unlimited local scans" only if there is no hidden activation/usage quota. It must NEVER claim unlimited project size, universal language coverage, all defects detected, or complete source review when a report is partial.
