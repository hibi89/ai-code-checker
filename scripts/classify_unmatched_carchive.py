"""Classify an EXE archive row absent from both PyInstaller build TOCs.

No source code execution or bundle extraction. A PyInstaller CArchive 'o'
typecode is a bootloader runtime OPTION, not a packaged source/binary file.
The exact installed file or legal rights of any other type remain unverified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from scripts.build_notice_review_queue import _verify_exe
from scripts.reconcile_native_build import normalize

FORMAT = "code_checker_last_unmatched_carchive_classification_v1"
MAX_INPUT_BYTES = 16 * 1024 * 1024
MAX_UNMATCHED_ROWS = 32
OPTION_NAME = re.compile(r"^pyi-[a-z][a-z0-9-]*(?: [A-Za-z0-9_./:-]{1,120})?$")
_LEGACY_OPTIONS = {"v", "u", "s", "O", "W"}


def classify_unmatched(audit: dict, pkg: dict, exe: Path) -> dict:
    """An exact-EXE-bound *metadata* classification, not NOTICE signoff."""
    if (audit.get("format") != "code_checker_p0d_frozen_archive_audit_v1"
            or pkg.get("format") != "code_checker_p0h_pkg_toc_metadata_v1"):
        raise ValueError("Unexpected original audit or PKG TOC evidence")
    if (any(audit.get(flag) is not False for flag in (
            "customer_release_ready", "third_party_notice_ready_to_distribute",
            "license_compliance_certified"))
            or any(pkg.get(flag) is not False for flag in (
                "customer_release_ready", "legal_notice_approved",
                "license_compliance_certified"))):
        raise ValueError("Preapproved binary/license evidence is invalid")
    expected_sha = audit.get("exe_sha256")
    if (not isinstance(expected_sha, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected_sha) is None
            or pkg.get("exe_sha256") != expected_sha):
        raise ValueError("EXE evidence identity mismatch")
    exe_bytes = _verify_exe(exe, expected_sha)
    rows = pkg["records"]
    if (not isinstance(rows, list)
            or len(rows) != pkg["previously_unmatched_exe_toc"]
            or len(rows) > MAX_UNMATCHED_ROWS
            or pkg.get("pkg_unique_record_claims", -1)
            + pkg.get("pkg_ambiguous_record_claims", -1)
            + pkg.get("pkg_no_record_claims", -1) != len(rows)
            or pkg.get("all_prior_unmatched_accounted_for") is not True):
        raise ValueError("Inconsistent prior PKG accounting")
    archive = audit["archive"]
    top = {}
    for raw in archive["top_level"]:
        name = normalize(raw["name"])
        if name in top:
            raise ValueError("Duplicate original archive names")
        top[name] = str(raw["typecode"])
    outcomes = []
    seen = set()
    for row in rows:
        if row["pkg_toc_evidence"] != "no_pkg_toc_record":
            continue
        name = normalize(row["name"])
        kind = str(row["carchive_typecode"])
        if (name in seen or top.get(name) != kind
                or row.get("copyright_owner_verified") is not False
                or row.get("license_approved") is not False):
            raise ValueError("Untrusted or duplicate unmatched entry")
        seen.add(name)
        # PyInstaller's own CArchive/bootloader code specifies type 'o'
        # for an OPTION whose TOC entry name encodes the runtime setting.
        if kind == "o":
            category = "PYINSTALLER_RUNTIME_OPTION_METADATA"
            recognized = bool(OPTION_NAME.fullmatch(name) or name in _LEGACY_OPTIONS)
        else:
            category = "UNRESOLVED_ARCHIVE_PAYLOAD_OR_RESOURCE"
            recognized = False
        outcomes.append({
            # The logical TOC name is hashed to avoid exposing file paths in
            # public CI logs or persisted review summaries.
            "logical_archive_name_sha256": hashlib.sha256(name.encode("utf-8")).hexdigest(),
            "carchive_typecode": kind,
            "classification": category,
            "option_name_matches_known_syntax": recognized,
            "runtime_option_not_a_separate_embedded_file": kind == "o",
            "actual_archive_source_or_vendor_verified": False,
            "third_party_copyright_notice_review_still_required": True,
        })
    if len(outcomes) != pkg["pkg_no_record_claims"]:
        raise ValueError("Some unmatched metadata entries were dropped")
    return {
        "format": FORMAT,
        "exe_sha256": expected_sha,
        "exe_bytes": exe_bytes,
        "previously_no_pkg_toc_claims": pkg["pkg_no_record_claims"],
        "runtime_option_metadata_count": sum(
            row["classification"] == "PYINSTALLER_RUNTIME_OPTION_METADATA"
            for row in outcomes),
        "unresolved_payload_count": sum(
            row["classification"] == "UNRESOLVED_ARCHIVE_PAYLOAD_OR_RESOURCE"
            for row in outcomes),
        "recognized_option_name_count": sum(
            row["option_name_matches_known_syntax"] for row in outcomes),
        "records": outcomes,
        "actual_exe_hash_verified": True,
        "metadata_not_evidence_of_license_permission": True,
        "customer_notice_ready": False,
        "customer_release_ready": False,
        "license_compliance_certified": False,
        "status": "FROZEN_OPTION_METADATA_ONLY_RETAIL_BLOCKED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify last frozen TOC row from exact EXE")
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--pkg", required=True, type=Path)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        paths = (args.audit, args.pkg)
        for path in paths:
            if (path.is_symlink() or not path.is_file()
                    or not 0 < path.stat().st_size <= MAX_INPUT_BYTES):
                raise ValueError("Missing, linked or oversized source evidence")
        out = args.out
        if (out.exists() or out.is_symlink() or not out.parent.is_dir()
                or out.parent.is_symlink() or out in (*paths, args.exe)):
            raise ValueError("Output must be a new local file")
        audit, pkg = (json.loads(p.read_text(encoding="utf-8")) for p in paths)
        classified = classify_unmatched(audit, pkg, args.exe)
        with out.open("x", encoding="utf-8") as stream:
            json.dump(classified, stream, ensure_ascii=False, indent=2, sort_keys=True)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        print("LAST_UNMATCHED_CARCHIVE_EVIDENCE_INVALID")
        return 1
    print("LAST_UNMATCHED_CARCHIVE_METADATA_PASS")
    print("EXE_HASH_VERIFIED=True")
    print("RUNTIME_OPTION_METADATA=" + str(classified["runtime_option_metadata_count"]))
    print("RECOGNIZED_OPTION_NAME=" + str(classified["recognized_option_name_count"]))
    print("UNRESOLVED_PAYLOAD=" + str(classified["unresolved_payload_count"]))
    print("CUSTOMER_NOTICE_READY=False")
    print("CUSTOMER_RELEASE_READY=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
