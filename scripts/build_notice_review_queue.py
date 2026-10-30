"""Build an actionable local license/NOTICE review queue for ONE actual EXE.

This is metadata-only and never copies LICENSE texts or an EXE, executes
customer code, makes network requests, or approves redistribution. The five
preexisting evidence stages must all reconcile to the same executable SHA.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from collections import Counter
from pathlib import Path

from scripts.reconcile_notice_gaps import (
    MAX_INPUT_BYTES, MAX_ROWS, reconcile_notice_gaps,
)

FORMAT = "code_checker_local_binary_notice_review_queue_v1"
MAX_EXE_BYTES = 256 * 1024 * 1024
_REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _verify_exe(exe: Path, expected_sha: str) -> int:
    """Hash actual candidate bytes without launching or extracting anything."""
    if exe.is_symlink() or not exe.is_file():
        raise ValueError("EXE is missing, linked or not a regular file")
    before = exe.lstat()
    if (not stat.S_ISREG(before.st_mode)
            or getattr(before, "st_file_attributes", 0) & _REPARSE
            or not 0 < before.st_size <= MAX_EXE_BYTES):
        raise ValueError("Unsafe or oversized EXE")
    digest = hashlib.sha256()
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(exe, flags)
    try:
        opened = os.fstat(fd)
        if (not stat.S_ISREG(opened.st_mode)
                or (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
                != (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)):
            raise ValueError("EXE identity changed during open")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            for part in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(part)
        after = os.fstat(fd)
        if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
                before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns):
            raise ValueError("EXE changed while hashing")
    finally:
        os.close(fd)
    if digest.hexdigest() != expected_sha:
        raise ValueError("Actual EXE bytes do not match the five-stage provenance")
    return before.st_size


def build_review_queue(audit: dict, mapping: dict, native: dict,
                       exe_toc: dict, pkg_toc: dict, exe: Path) -> dict:
    """An EXE-anchored human review checklist, never a legal-compliance finding."""
    ledger = reconcile_notice_gaps(audit, mapping, native, exe_toc, pkg_toc)
    exe_size = _verify_exe(exe, ledger["exe_sha256"])

    unresolved = [row for row in mapping["entries"]
                  if row["mapping"].startswith("unresolved")]
    native_by_name = {row["name"]: row for row in native["records"]}
    exe_by_name = {row["name"]: row for row in exe_toc["records"]}
    pkg_by_name = {row["name"]: row for row in pkg_toc["records"]}
    if (len(native_by_name) != len(unresolved)
            or len(exe_by_name) != len(exe_toc["records"])
            or len(pkg_by_name) != len(pkg_toc["records"])
            or len(unresolved) > MAX_ROWS):
        raise ValueError("Evidence row identity is missing or duplicated")

    # Only bundled archive *names* and preexisting categories are copied,
    # never original absolute build paths, customer source, or LICENSE text.
    review = []
    category_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    for row in sorted(unresolved, key=lambda entry: entry["name"].casefold()):
        name = row["name"]
        if (not isinstance(name, str) or not 1 <= len(name) <= 512
                or re.search(r"[\x00-\x1f]", name)
                or re.match(r"^[a-zA-Z]:", name)
                or name.startswith(("/", "\\")) or ".." in name.replace("\\", "/").split("/")):
            raise ValueError("Unsafe archive name in release review")
        native_row = native_by_name[name]
        if (row["kind"] != "CArchive"
                or native_row["initial_category"] != row["mapping"]):
            raise ValueError("Unresolved row disagrees with native provenance")
        evidence = native_row["build_record_evidence"]
        category_counts[row["mapping"]] += 1
        source_counts[evidence] += 1
        # Unknown means no proof, even if build source and embedded bytes match.
        review.append({
            "archive_entry": name,
            "entry_kind": "CArchive",
            "unresolved_category": row["mapping"],
            "build_record_evidence": evidence,
            "source_byte_match": native_row.get("source_byte_match", "not_tested"),
            "source_location_category": native_row.get("source_location_category"),
            "exe_toc_evidence": exe_by_name.get(name, {}).get("exe_toc_evidence"),
            "pkg_toc_evidence": pkg_by_name.get(name, {}).get("pkg_toc_evidence"),
            "human_owner_version_and_license_review": "REQUIRED",
            "redistribution_permission_verified": False,
        })
    if len(review) != ledger["unresolved_archive_entry_count"]:
        raise ValueError("Incomplete local manual-review roster")
    return {
        "format": FORMAT,
        "exe_sha256": ledger["exe_sha256"],
        "exe_bytes": exe_size,
        "five_stage_evidence_reconciled": True,
        "actual_exe_hash_verified": True,
        "unresolved_entry_count": len(review),
        "unresolved_category_counts": dict(sorted(category_counts.items())),
        "build_source_candidate_counts": dict(sorted(source_counts.items())),
        "unresolved_entries_requiring_review": review,
        "distribution_review": ledger["distribution_review"],
        "manual_review_tasks": ledger["manual_review_tasks"],
        "original_license_texts_included": False,
        "vendor_or_binary_ownership_certified": False,
        "third_party_notice_ready": False,
        "license_compliance_certified": False,
        "customer_release_ready": False,
        "status": "LOCAL_EVIDENCE_ONLY_RETAIL_RELEASE_BLOCKED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Review queue for exact local unsigned Windows EXE")
    for flag in ("audit", "mapping", "native", "exe-toc", "pkg-toc", "exe", "out"):
        parser.add_argument("--" + flag, required=True, type=Path)
    args = parser.parse_args()
    inputs = [args.audit, args.mapping, args.native, args.exe_toc, args.pkg_toc]
    try:
        out = args.out
        if (out.exists() or out.is_symlink() or not out.parent.is_dir()
                or out in [*inputs, args.exe]):
            raise ValueError("Review output must be a new distinct local file")
        # Match other EXE evidence tools: reject linked, missing, huge inputs.
        evidence = []
        for path in inputs:
            if (path.is_symlink() or not path.is_file()
                    or not 0 < path.stat().st_size <= MAX_INPUT_BYTES):
                raise ValueError("Missing, linked or oversized stage evidence")
            evidence.append(json.loads(path.read_text(encoding="utf-8")))
        report = build_review_queue(*evidence, args.exe)
        with out.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=False, sort_keys=True, indent=2)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        print("LOCAL_NOTICE_REVIEW_QUEUE_INVALID")
        return 1
    print("LOCAL_NOTICE_REVIEW_QUEUE_PASS")
    print("EXE_BYTES_HASH_MATCH=True")
    print("HUMAN_UNRESOLVED_ROWS=" + str(report["unresolved_entry_count"]))
    print("HUMAN_DISTRIBUTION_ROWS=" + str(len(report["distribution_review"])))
    print("LEGAL_NOTICE_APPROVED=False")
    print("CUSTOMER_RELEASE_READY=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
