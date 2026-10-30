"""Validate a local Windows frozen-EXE synthetic GUI smoke receipt.

A valid receipt proves only that the packaged binary completed two built-in,
synthetic modes and that its bytes matched the receipt. It does NOT establish
independent consumer Windows/OS-packet/SmartScreen/PDF/legal acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
from pathlib import Path

FORMAT = "code_checker_windows_local_exe_smoke_v1"
MAX_RECEIPT_BYTES = 16 * 1024
MAX_EXE_BYTES = 256 * 1024 * 1024
FIELDS = frozenset({
    "format", "collection_method", "scope", "exe_sha256", "exe_bytes",
    "observed_synthetic", "pending_gates", "actual_customer_code_used",
    "actual_customer_release_ready", "legal_notice_approved",
})
OBSERVED = frozenset({
    "packaged_tk_gui_startup", "packaged_preview_scan_report",
    "executable_hash_stable",
})
PENDING = frozenset({
    "clean_consumer_windows", "interactive_human_gui", "smartscreen_reputation",
    "defender_customer_acceptance", "os_packet_capture", "korean_pdf_visual",
    "third_party_license_notice",
})


def validate_receipt(data: dict, exe: Path) -> dict:
    if not isinstance(data, dict) or set(data) != FIELDS:
        raise ValueError("Unexpected local EXE smoke evidence schema")
    if (data["format"] != FORMAT
            or data["collection_method"] != "two_synthetic_exe_modes_no_python_required"
            or data["scope"] != "existing_local_exe_only"):
        raise ValueError("Invalid EXE smoke provenance")
    if (data["actual_customer_code_used"] is not False
            or data["actual_customer_release_ready"] is not False
            or data["legal_notice_approved"] is not False):
        raise ValueError("Local EXE smoke cannot certify commercial release")
    observed = data["observed_synthetic"]
    if (not isinstance(observed, dict) or set(observed) != OBSERVED
            or observed["packaged_tk_gui_startup"] != "PASS"
            or observed["packaged_preview_scan_report"] != "PASS"
            or observed["executable_hash_stable"] is not True):
        raise ValueError("Synthetic GUI outcome unproven")
    gates = data["pending_gates"]
    if not isinstance(gates, dict) or set(gates) != PENDING:
        raise ValueError("Missing or unexpected pending retail gate")
    if any(v != "UNVERIFIED" for v in gates.values()):
        raise ValueError("Synthetic smoke may not promote retail acceptance")

    sha = data["exe_sha256"]
    size = data["exe_bytes"]
    if (not isinstance(sha, str) or re.fullmatch(r"[0-9a-f]{64}", sha) is None
            or type(size) is not int or not 0 < size <= MAX_EXE_BYTES):
        raise ValueError("Invalid EXE identity")
    if exe.is_symlink() or not exe.is_file():
        raise ValueError("Missing or linked EXE")
    st_before = exe.stat()
    if not stat.S_ISREG(st_before.st_mode) or st_before.st_size != size:
        raise ValueError("EXE size or type changed")
    digest = hashlib.sha256()
    with exe.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    st_after = exe.stat()
    if (st_after.st_ino, st_after.st_size, st_after.st_mtime_ns) != (
            st_before.st_ino, st_before.st_size, st_before.st_mtime_ns):
        raise ValueError("EXE changed during evidence validation")
    if digest.hexdigest() != sha:
        raise ValueError("EXE content differs from receipt")
    return {
        "exe_hash_verified": True,
        "packaged_tk_and_synthetic_workflow": "PASS",
        "pending_manual_gates": len(PENDING),
        "customer_release_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Windows EXE synthetic smoke evidence (not release approval)")
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--exe", required=True, type=Path)
    args = parser.parse_args()
    try:
        if (args.evidence.is_symlink() or not args.evidence.is_file()
                or not 0 < args.evidence.stat().st_size <= MAX_RECEIPT_BYTES):
            raise ValueError("Missing, linked or oversized smoke receipt")
        record = json.loads(args.evidence.read_text(encoding="utf-8-sig"))
        result = validate_receipt(record, args.exe)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        print("WINDOWS_EXE_SYNTHETIC_RECEIPT_INVALID")
        return 1
    print("WINDOWS_EXE_SYNTHETIC_RECEIPT_PASS")
    print("EXE_HASH_VERIFIED=" + str(result["exe_hash_verified"]))
    print("MANUAL_GATES_UNVERIFIED=" + str(result["pending_manual_gates"]))
    print("CUSTOMER_RELEASE_READY=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
