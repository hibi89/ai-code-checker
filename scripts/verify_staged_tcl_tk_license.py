"""Bind locally STAGED Tcl/Tk original bytes to upstream tags and actual EXE.

Only developer-local, already staged source candidates are read. Do not expose
license texts in logs, artifacts, public repos or automatically approve NOTICE.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import stat
from pathlib import Path

from scripts.verify_upstream_tcl_tk_license import (
    MAX_LICENSE, MAX_RECEIPT, _safe_read, compare_originals,
)
from scripts.runtime_version_receipt import verify_receipt
from scripts import verify_upstream_tcl_tk_license as upstream

FORMAT = "code_checker_runtime_original_license_candidates_v1"
MAX_MANIFEST = 128 * 1024
_REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def verify_staged(exe: Path, receipt: dict, staged: Path) -> dict:
    info = staged.lstat()
    if (not stat.S_ISDIR(info.st_mode) or staged.is_symlink()
            or getattr(info, "st_file_attributes", 0) & _REPARSE):
        raise ValueError("Staged folder must be a real local directory")
    raw_manifest = _safe_read(staged / "manifest.json", MAX_MANIFEST)
    manifest = json.loads(raw_manifest)
    if (not isinstance(manifest, dict) or manifest.get("format") != FORMAT
            or manifest.get("actual_exe_sha256_confirmed") is not True
            or manifest.get("frozen_tcl_tk_runtime_receipt_verified") is not True
            or manifest.get("customer_release_ready") is not False
            or manifest.get("customer_notice_ready") is not False
            or manifest.get("copyright_and_redistribution_rights_verified") is not False
            or not isinstance(manifest.get("originals"), list)
            or manifest.get("original_candidate_file_count") != len(manifest["originals"])
            or not isinstance(manifest.get("source_role_counts"), dict)
            or set(manifest["source_role_counts"]) != {"cpython", "tcl", "tk", "pyinstaller"}
            or sum(manifest["source_role_counts"].values()) != len(manifest["originals"])
            or not isinstance(manifest.get("missing_source_roles"), list)
            or not isinstance(manifest.get("ambiguous_source_roles"), list)
            or manifest.get("exe_sha256") != receipt.get("exe_sha256")
            or manifest.get("exe_bytes") != receipt.get("exe_bytes")
            or manifest.get("frozen_tcl_patchlevel") != receipt.get("tcl_runtime_patchlevel")
            or manifest.get("frozen_tk_patchlevel") != receipt.get("tk_runtime_patchlevel")):
        raise ValueError("Incomplete/mismatched frozen runtime original manifest")

    counts = manifest["source_role_counts"]
    missing = manifest["missing_source_roles"]
    ambiguous = manifest["ambiguous_source_roles"]
    if (any(not isinstance(role, str) or role not in counts for role in missing + ambiguous)
            or len(missing) != len(set(missing))
            or len(ambiguous) != len(set(ambiguous))
            or set(missing) != {role for role in counts if counts[role] == 0}
            or not set(ambiguous).issubset(set(missing))
            or any(type(count) is not int or count < 0 or count > 16 for count in counts.values())):
        raise ValueError("Invalid missing/ambiguous installed source accounting")

    unavailable = sorted(role for role in ("tcl", "tk")
                         if role in missing or role in ambiguous)
    if unavailable:
        # Missing installed source is an explicit, EXE-hash-bound unresolved
        # compliance gap, NOT a CI green source-byte match or release approval.
        # Check any present Tcl/Tk candidate against its own upstream tagged
        # blob before recording the OTHER role as unavailable. An available Tk
        # file is not made unverifiable just because Tcl was absent from the
        # installed Python runtime tree.
        checked_present: list[dict] = []
        for role in ("tcl", "tk"):
            role_rows = [row for row in manifest["originals"]
                         if isinstance(row, dict) and row.get("role") == role]
            if role in unavailable:
                if role_rows or counts[role] != 0:
                    raise ValueError("Claimed missing source exists in manifest")
                continue
            if counts[role] != 1 or len(role_rows) != 1:
                raise ValueError("Unexpected existing source candidate count")
            item = role_rows[0]
            if (item.get("candidate_file") != role + "-01.original"
                    or item.get("installed_source_basename") != "license.terms"
                    or item.get("source_kind") != "installed_python_runtime_tree"
                    or item.get("human_review_required") is not True
                    or item.get("corresponding_frozen_entry_or_copyright_owner_verified") is not False
                    or type(item.get("bytes")) is not int
                    or not isinstance(item.get("sha256"), str)):
                raise ValueError("Unexpected staged candidate metadata")
            raw = _safe_read(staged / item["candidate_file"], MAX_LICENSE)
            if len(raw) != item["bytes"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
                raise ValueError("Present staged source candidate was modified")
            version = receipt[role + "_runtime_patchlevel"]
            if not isinstance(version, str):
                raise ValueError("Missing frozen Tcl/Tk runtime version")
            pinned = upstream.PINNED.get(role, {}).get(version)
            actual_blob = upstream.git_blob_id(raw)
            checked_present.append({
                "component": role,
                "runtime_patchlevel": version,
                "official_git_tag": pinned[0] if pinned else None,
                "upstream_license_git_blob_sha1": pinned[1] if pinned else None,
                "installed_license_git_blob_sha1": actual_blob,
                "upstream_original_bytes_match": bool(pinned and actual_blob == pinned[1]),
                "exact_bundled_binary_owner_verified": False,
            })
        verify_receipt(receipt, exe)
        return {
            "format": "code_checker_staged_tcl_tk_upstream_review_v1",
            "status": "MISSING_INSTALLED_SOURCE_REVIEW_REQUIRED",
            "exe_sha256": receipt["exe_sha256"],
            "exe_bytes": receipt["exe_bytes"],
            "missing_or_ambiguous_roles": unavailable,
            "available_installed_source_originals": checked_present,
            "available_source_count": len(checked_present),
            "available_upstream_original_bytes_match": (
                bool(checked_present) and all(
                    row["upstream_original_bytes_match"] for row in checked_present
                )
            ),
            "staged_manifest_sha256": hashlib.sha256(raw_manifest).hexdigest(),
            "source_equality_verified": False,
            "installed_source_binary_copyright_owner_verified": False,
            "third_party_notice_ready": False,
            "license_compliance_certified": False,
            "customer_release_ready": False,
        }

    originals = {}
    for role in ("tcl", "tk"):
        rows = [row for row in manifest["originals"]
                if isinstance(row, dict) and row.get("role") == role]
        if len(rows) != 1:
            raise ValueError("Ambiguous installed source original")
        row = rows[0]
        name = role + "-01.original"
        if (row.get("candidate_file") != name
                or row.get("installed_source_basename") != "license.terms"
                or row.get("source_kind") != "installed_python_runtime_tree"
                or row.get("human_review_required") is not True
                or row.get("corresponding_frozen_entry_or_copyright_owner_verified") is not False
                or not isinstance(row.get("sha256"), str)
                or not isinstance(row.get("bytes"), int)
                or isinstance(row.get("bytes"), bool)):
            raise ValueError("Unexpected or preapproved source candidate")
        raw = _safe_read(staged / name, MAX_LICENSE)
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("Installed original differs from staged manifest")
        originals[role] = raw

    result = compare_originals(receipt, exe, originals["tcl"], originals["tk"])
    result["staged_installed_source_hashes_verified"] = True
    result["staged_manifest_sha256"] = hashlib.sha256(raw_manifest).hexdigest()
    result["installed_source_binary_copyright_owner_verified"] = False
    result["note"] = "Original source text equality, not binary origin/NOTICE permission."
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local staged runtime Tcl/Tk original comparison")
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--runtime-receipt", required=True, type=Path)
    parser.add_argument("--staged-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if (args.out.exists() or args.out.is_symlink()
                or not args.out.parent.is_dir() or args.out.parent.is_symlink()
                or args.out.parent == args.staged_dir):
            raise ValueError("Output must be new and separate from originals")
        receipt = json.loads(_safe_read(args.runtime_receipt, MAX_RECEIPT))
        report = verify_staged(args.exe, receipt, args.staged_dir)
        with args.out.open("x", encoding="utf-8") as target:
            json.dump(report, target, sort_keys=True, indent=2, ensure_ascii=True)
        if report["status"] == "MISSING_INSTALLED_SOURCE_REVIEW_REQUIRED":
            print("EXACT_EXE_TCLTK_INSTALLED_SOURCE_MISSING_UPSTREAM_MATCH_UNVERIFIED")
            for row in report["available_installed_source_originals"]:
                print(
                    row["component"].upper() + "_INSTALLED_LICENSE_OFFICIAL_BYTES_MATCH="
                    + str(row["upstream_original_bytes_match"])
                )
        else:
            print("ACTUAL_EXE_STAGED_TCLTK_UPSTREAM_SOURCE_MATCH_PASS")
        print("ORIGINAL_LICENSE_TEXT_OUTPUT=False")
        print("BINARY_OWNER_AND_REDISTRIBUTION_REVIEW=REQUIRED")
        print("CUSTOMER_RELEASE_READY=False")
        return 0
    except (OSError, ValueError, TypeError, KeyError, OverflowError, json.JSONDecodeError):
        print("ACTUAL_EXE_STAGED_TCLTK_UPSTREAM_SOURCE_MATCH_INVALID")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
