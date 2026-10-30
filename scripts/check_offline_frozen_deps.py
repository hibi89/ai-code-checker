"""Fail closed if Gemini/Pydantic code leaks into the offline frozen executable.

Read only the existing bounded CArchive/PYZ metadata manifest; never extract,
execute or upload packaged files. Does not certify any license or retail release.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

MAX_EVIDENCE = 16 * 1024 * 1024


def check_boundary(audit: dict) -> dict:
    if not isinstance(audit, dict):
        raise ValueError("Expected EXE audit object")
    if (audit.get("format") != "code_checker_p0d_frozen_archive_audit_v1"
            or audit.get("license_compliance_certified") is not False
            or audit.get("third_party_notice_ready_to_distribute") is not False
            or audit.get("customer_release_ready") is not False):
        raise ValueError("Untrusted or falsely approved EXE audit")
    archive = audit["archive"]
    if (archive.get("metadata_only") is not True
            or archive.get("no_bundle_entry_extracted_or_executed") is not True
            or archive.get("archive_read_errors")):
        raise ValueError("Unverified packaged inventory")
    top, nested = archive["top_level"], archive["pyz_modules"]
    if (not top or not nested
            or len(top) != archive["top_level_count"]
            or len(nested) != archive["pyz_module_count"]):
        raise ValueError("Incomplete CArchive or PYZ metadata")
    for row in top:
        name = row["name"]
        if not isinstance(name, str):
            raise ValueError("Invalid archive name")
        name = name.lower().replace("\\", "/")
        if (name.startswith(("pydantic/", "pydantic_core/", "pydantic.", "pydantic_core."))
                or "/pydantic/" in name or "/pydantic_core/" in name):
            raise ValueError("Pydantic files still bundled in offline executable")
    seen_local_model = False
    for row in nested:
        module = row["module"]
        if not isinstance(module, str):
            raise ValueError("Invalid PYZ module")
        root = module.partition(".")[0]
        if root in {"pydantic", "pydantic_core", "review_models"}:
            raise ValueError("Gemini/Pydantic model bundled in offline executable")
        if module == "offline_models":
            seen_local_model = True
    if not seen_local_model:
        raise ValueError("Pure standard-library offline models missing")
    return {
        "top_level_count": len(top),
        "pyz_module_count": len(nested),
        "stdlib_model_present": seen_local_model,
        "gemini_pydantic_bundled": False,
        "customer_release_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Guard offline Windows EXE against Gemini/Pydantic bundling")
    parser.add_argument("--audit", required=True, type=Path)
    args = parser.parse_args()
    try:
        p = args.audit
        if p.is_symlink() or not p.is_file() or not 0 < p.stat().st_size <= MAX_EVIDENCE:
            raise ValueError("Missing, linked or oversized archive audit")
        result = check_boundary(json.loads(p.read_text(encoding="utf-8")))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        print("OFFLINE_FROZEN_DEPENDENCY_BOUNDARY_INVALID")
        return 1
    print("OFFLINE_FROZEN_DEPENDENCY_BOUNDARY_PASS")
    print("CARCHIVE_ENTRIES=" + str(result["top_level_count"]))
    print("PYZ_MODULES=" + str(result["pyz_module_count"]))
    print("GEMINI_PYDANTIC_BUNDLED=False")
    print("LICENSE_NOTICE_REVIEW_STILL_REQUIRED=True")
    print("CUSTOMER_RELEASE_READY=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
