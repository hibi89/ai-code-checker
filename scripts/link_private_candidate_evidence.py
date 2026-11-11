"""Cross-check a private ZIP and existing same-EXE Windows receipts; NEVER release."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from input_safety import validate_offline_input_path
from scripts.verify_customer_zip_candidate import FORMAT as ZIP_FORMAT, inspect_candidate
from scripts.consolidate_windows_retail_evidence import (
    MAX_ACCEPTANCE, MAX_SMOKE, MAX_RUNTIME, MAX_DEFENDER,
    _load, consolidate,
)

FORMAT = "code_checker_candidate_receipt_binding_v1"


def link_candidate_evidence(exe: Path, archive: Path, readonly: dict,
                            smoke: dict, *, runtime: dict | None = None,
                            defender: dict | None = None) -> dict:
    """Only already collected receipts. Never launches a binary or tests an OS."""
    first = inspect_candidate(archive, exe)
    if (first.get("format") != ZIP_FORMAT
            or first.get("status") != "PACKAGE_STRUCTURE_ONLY_RELEASE_BLOCKED"
            or first.get("customer_release_ready") is not False
            or first.get("owner_release_approval") is not False):
        raise ValueError("UNTRUSTED_ZIP_EVIDENCE")
    windows = consolidate(exe, readonly, smoke, runtime=runtime, defender=defender)
    if (windows.get("status") != "EXACT_BINARY_RECEIPTS_VALID_RELEASE_BLOCKED"
            or windows.get("customer_release_ready") is not False
            or windows.get("legal_notice_approved") is not False
            or windows.get("real_buyer_pc_test_certified") is not False
            or first["exact_exe_sha256"] != windows["exe_sha256"]
            or first["exact_exe_bytes"] != windows["exe_bytes"]):
        raise ValueError("CROSS_BINARY_EVIDENCE_MISMATCH")
    gates = windows.get("human_release_gates")
    if (not isinstance(gates, dict) or len(gates) < 6
            or any(value != "UNVERIFIED" for value in gates.values())):
        raise ValueError("RETAIL_GATES_CANNOT_BE_AUTO_APPROVED")
    # Revalidate physical ZIP after reading receipts, not only before them.
    second = inspect_candidate(archive, exe)
    if second != first:
        raise ValueError("CANDIDATE_CHANGED_DURING_REVIEW")
    return {
        "format": FORMAT,
        "status": "PRIVATE_ZIP_AND_WINDOWS_RECEIPTS_LINKED_RELEASE_BLOCKED",
        "exact_exe_sha256": first["exact_exe_sha256"],
        "exact_exe_bytes": first["exact_exe_bytes"],
        "candidate_zip_sha256": first["candidate_zip_sha256"],
        "candidate_zip_bytes": first["candidate_zip_bytes"],
        "entries_checked": first["entries_checked"],
        "synthetic_packaged_gui_receipt_verified": True,
        "windows_readonly_receipt_verified": True,
        "optional_runtime_receipt_provided": runtime is not None,
        "optional_defender_receipt_provided": defender is not None,
        "human_release_gates": dict(gates),
        "vendor_redistribution_rights_verified": False,
        "actual_buyer_windows_10_11_accepted": False,
        "malware_free_certified": False,
        "owner_release_approval": False,
        "customer_release_ready": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Bind unapproved private ZIP to exact Windows EXE receipts")
    p.add_argument("--exe", required=True, type=Path)
    p.add_argument("--zip", required=True, type=Path)
    p.add_argument("--readonly", required=True, type=Path)
    p.add_argument("--smoke", required=True, type=Path)
    p.add_argument("--runtime", type=Path)
    p.add_argument("--defender", type=Path)
    p.add_argument("--out", type=Path, help="Optional fresh private JSON path")
    args = p.parse_args(argv)
    paths = [args.exe, args.zip, args.readonly, args.smoke] + [
        x for x in (args.runtime, args.defender) if x is not None]
    try:
        if any(not x.is_absolute() for x in paths) or len(set(paths)) != len(paths):
            raise ValueError("INPUT_PATHS_MUST_BE_DISTINCT")
        if args.out is not None:
            if (not args.out.is_absolute() or args.out.suffix.lower() != ".json"
                    or args.out in paths or args.out.exists() or args.out.is_symlink()):
                raise ValueError("OUTPUT_MUST_BE_NEW")
            valid_out = validate_offline_input_path(args.out)
            if not valid_out.parent.is_dir():
                raise ValueError("OUTPUT_PARENT_NOT_FOUND")
        result = link_candidate_evidence(
            args.exe, args.zip, _load(args.readonly, MAX_ACCEPTANCE),
            _load(args.smoke, MAX_SMOKE),
            runtime=_load(args.runtime, MAX_RUNTIME) if args.runtime else None,
            defender=_load(args.defender, MAX_DEFENDER) if args.defender else None,
        )
        if args.out is not None:
            fd = os.open(valid_out, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as out:
                    json.dump(result, out, sort_keys=True, ensure_ascii=True, indent=2)
                    out.write("\n")
            except Exception:
                valid_out.unlink(missing_ok=True)
                raise
        print("PRIVATE_ZIP_AND_WINDOWS_RECEIPTS_LINKED_RELEASE_BLOCKED")
        print("EXE_SHA256=" + result["exact_exe_sha256"])
        print("ZIP_SHA256=" + result["candidate_zip_sha256"])
        print("CUSTOMER_RELEASE_READY=False")
        return 0
    except (ValueError, OSError, KeyError, TypeError, UnicodeError, json.JSONDecodeError):
        print("PRIVATE_ZIP_WINDOWS_RECEIPT_BINDING_BLOCKED")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
