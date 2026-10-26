"""P0-F: reconcile an observed frozen EXE with PyInstaller build Analysis TOC.

Evidence level: build source path claims + optional embedded/native byte SHA matches.
Uses no pickle/eval/exec, no customer code, no network, no files extracted to disk.
Build-time paths never appear in stdout/review reports or uploaded artifacts.
The evidence is NOT a software license or vendor ownership certification.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

SOURCE_TYPES = {"BINARY", "EXTENSION", "DATA", "EXECUTABLE", "ZIPFILE"}
MAX_TOC_BYTES = 16 * 1024 * 1024
MAX_RECORDS = 30000
MAX_NATIVE_BYTES = 32 * 1024 * 1024
NATIVE_SUFFIXES = (".dll", ".pyd", ".exe", ".so", ".dylib")
UNRESOLVED = {"unresolved_native_or_system_binary", "unresolved_archive_resource_or_bootloader"}


def normalize(name: str) -> str:
    if not isinstance(name, str) or len(name) > 768 or "\x00" in name:
        raise ValueError("Unsafe bundle name")
    value = name.replace("\\", "/")
    if not value or value.startswith("/") or ".." in value.split("/"):
        raise ValueError("Invalid bundle path")
    return value.casefold()


def _traverse(value, result: list, visited: list[int]):
    visited[0] += 1
    if visited[0] > MAX_RECORDS * 20:
        raise ValueError("PyInstaller Analysis TOC too complex")
    if isinstance(value, (tuple, list)):
        if (len(value) == 3 and isinstance(value[0], str)
                and isinstance(value[1], str) and isinstance(value[2], str)
                and value[2] in SOURCE_TYPES):
            dest, src, kind = value
            result.append((normalize(dest), Path(src), kind))
            if len(result) > MAX_RECORDS:
                raise ValueError("Too many source records")
        else:
            for child in value:
                _traverse(child, result, visited)
    elif isinstance(value, dict):
        for child in value.values():
            _traverse(child, result, visited)


def parse_analysis_toc(path: Path) -> list[tuple[str, Path, str]]:
    if not path.is_file() or path.stat().st_size > MAX_TOC_BYTES:
        raise ValueError("Missing/oversized Analysis-00.toc")
    content = path.read_text(encoding="utf-8")
    parsed = ast.literal_eval(content)  # data only, not Python evaluation
    records: list = []
    _traverse(parsed, records, [0])
    if not records:
        raise ValueError("Build analysis contains no binary/data source records")
    return records


def source_bucket(src: Path) -> str:
    """No absolute build paths, usernames, temp directories in the result."""
    s = str(src).replace("\\", "/").casefold()
    if "/site-packages/" in s:
        return "python_site_packages"
    if re.search(r"/(?:dlls|lib|libs|tcl|tk)(?:/|$)", s):
        return "python_runtime_or_tcl_tree_candidate"
    if "/windows/" in s or "/system32/" in s:
        return "windows_os_tree_candidate"
    if "/ai-code-checker/" in s:
        return "repository_build_tree"
    return "other_build_source_location"


def sha_file(path: Path, maximum: int) -> str | None:
    if not path.is_file() or path.stat().st_size > maximum:
        return None
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def reconcile(mapping: dict, toc_records: list[tuple[str, Path, str]], *,
              archive_reader=None, max_native_bytes=MAX_NATIVE_BYTES) -> dict:
    """Explicit ambiguity + source-only claims; byte-hash match never licensing."""
    if (mapping.get("customer_release_ready") is not False
            or mapping.get("third_party_notice_ready_to_distribute") is not False
            or mapping.get("license_compliance_certified") is not False):
        raise ValueError("Refuse pre-approved license evidence")
    entries = mapping["entries"]
    lookup: dict[str, list] = {}
    by_basename: dict[str, list] = {}
    for dest, src, kind in toc_records:
        row = (src, kind)
        lookup.setdefault(dest, []).append(row)
        by_basename.setdefault(dest.rsplit("/", 1)[-1], []).append((dest, *row))
    records = []
    counters = Counter()
    unresolved_rows = 0
    resolved_by_build_record = 0
    exact_byte_matches = 0
    build_source_missing = 0
    for row in entries:
        if row["kind"] != "CArchive" or row["mapping"] not in UNRESOLVED:
            continue
        unresolved_rows += 1
        name = row["name"]
        key = normalize(name)
        candidates = lookup.get(key, [])
        method = "exact_archive_relative_path"
        if not candidates:
            # Filename-only similarity does not constitute a secure match.
            suggestions = by_basename.get(key.rsplit("/", 1)[-1], [])
            status = "basename_hypothesis_only" if suggestions else "no_analysis_claim"
            records.append({"name": name, "initial_category": row["mapping"],
                            "build_record_evidence": status,
                            "source_location_category": None,
                            "source_byte_match": "not_tested"})
            counters[status] += 1
            continue
        dedup = {(str(src).casefold(), kind): (src, kind) for src, kind in candidates}
        if len(dedup) != 1:
            records.append({"name": name, "initial_category": row["mapping"],
                            "build_record_evidence": "ambiguous_multiple_source_records",
                            "source_location_category": None,
                            "source_byte_match": "not_tested"})
            counters["ambiguous_multiple_source_records"] += 1
            continue
        (src, kind), = dedup.values()
        resolved_by_build_record += 1
        category = source_bucket(src)
        status = "recorded_build_source_path_candidate"
        match_status = "not_native"
        if key.endswith(NATIVE_SUFFIXES):
            match_status = "not_tested"
            try:
                expected_hash = sha_file(src, max_native_bytes)
                if expected_hash is None:
                    build_source_missing += 1
                    match_status = "source_missing_or_oversized"
                elif archive_reader is None:
                    match_status = "archive_reader_unavailable"
                else:
                    # CArchiveReader.extract returns bytes without loading code.
                    raw = archive_reader.extract(name)
                    if not isinstance(raw, bytes):
                        match_status = "unsupported_embedded_entry_type"
                    elif len(raw) > max_native_bytes:
                        match_status = "embedded_entry_oversized"
                    elif hashlib.sha256(raw).hexdigest() == expected_hash:
                        match_status = "byte_identical_to_recorded_build_source"
                        exact_byte_matches += 1
                    else:
                        match_status = "different_bytes_review_required"
            except (OSError, ValueError, KeyError, RuntimeError, MemoryError):
                match_status = "comparison_error_unverified"
            counters[match_status] += 1
        counters[status] += 1
        records.append({
            "name": name, "initial_category": row["mapping"],
            "build_record_evidence": status,
            "source_location_category": category,
            "recorded_build_type": kind,
            "source_byte_match": match_status,
        })
    if len(records) != unresolved_rows:
        raise AssertionError("Some unresolved archive entries were not reconciled")
    return {
        "format": "code_checker_p0f_native_build_source_evidence_v1",
        "exe_sha256": mapping["exe_sha256"],
        "previous_unresolved_archive_entries": unresolved_rows,
        "recorded_build_source_candidates": resolved_by_build_record,
        "not_uniquely_recorded_in_build_toc": unresolved_rows - resolved_by_build_record,
        "native_archive_exact_byte_matches": exact_byte_matches,
        "candidate_build_files_unavailable_or_oversized": build_source_missing,
        "evidence_counts": dict(sorted(counters.items())),
        "records": records,
        "build_toc_paths_not_exposed": True,
        "native_bytes_only_hashed_in_memory": True,
        "source_path_not_a_license_or_vendor_proof": True,
        "all_entries_counted": len(records) == unresolved_rows,
        "legal_notice_approved": False,
        "customer_release_ready": False,
        "status": "BUILD_PROVENANCE_EVIDENCE_LICENSE_REVIEW_REQUIRED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Frozen EXE native source provenance; local CI only")
    parser.add_argument("--mapping", required=True)
    parser.add_argument("--analysis-toc", required=True)
    parser.add_argument("--exe", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        from PyInstaller.archive.readers import CArchiveReader
        output = Path(args.out)
        if output.exists() or output.is_symlink() or not output.parent.is_dir():
            raise ValueError("Refuse output overwrite/missing directory")
        mapping = json.loads(Path(args.mapping).read_text(encoding="utf-8"))
        records = parse_analysis_toc(Path(args.analysis_toc))
        reader = CArchiveReader(str(Path(args.exe).resolve(strict=True)))
        result = reconcile(mapping, records, archive_reader=reader)
        output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
        print("BUILD_PROVENANCE_AUDIT_PASS")
        print("PREVIOUSLY_UNRESOLVED=" + str(result["previous_unresolved_archive_entries"]))
        print("BUILD_SOURCE_CANDIDATES=" + str(result["recorded_build_source_candidates"]))
        print("NATIVE_EXACT_BYTE_MATCHES=" + str(result["native_archive_exact_byte_matches"]))
        print("NOT_UNIQUELY_RECONCILED=" + str(result["not_uniquely_recorded_in_build_toc"]))
        print("EVIDENCE_CATEGORY_COUNTS=" + json.dumps(result["evidence_counts"], sort_keys=True))
        print("LICENSE_AND_BINARY_OWNER_CERTIFIED=False")
        print("COMMERCIAL_RELEASE=NOT_APPROVED")
        return 0
    except (ValueError, OSError, TypeError, KeyError, SyntaxError, RecursionError) as exc:
        print("BUILD_PROVENANCE_AUDIT_FAILED=" + type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
