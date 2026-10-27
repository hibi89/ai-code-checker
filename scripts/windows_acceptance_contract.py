"""Validate the local-only Windows acceptance receipt.

This module never runs customer code, modifies operating-system settings, uses
the network or treats a hosted Windows runner as a retail PC. A valid evidence
receipt is NOT product approval; the unobserved release gates stay blocked.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

FORMAT = "code_checker_readonly_windows_acceptance_v1"
PENDING = (
    "retail_windows_user_acceptance",
    "smartscreen_reputation",
    "os_packet_capture",
    "defender_exe_scan",
    "korean_pdf_visual",
    "third_party_legal_notice",
)
FIELDS = {
    "format", "collection_method", "scope", "exe_sha256", "exe_bytes",
    "signature_observation", "defender", "pending_gates",
    "customer_release_ready", "legal_notice_approved",
}
MAX_EVIDENCE_BYTES = 16 * 1024


def validate_evidence(record: dict, executable: Path) -> dict:
    """Check receipt against current EXE bytes and fail closed on any release claim."""
    if not isinstance(record, dict) or set(record) != FIELDS:
        raise ValueError("Evidence schema is not exact")
    if (record["format"] != FORMAT
            or record["collection_method"] != "win32_readonly_powershell"
            or record["scope"] != "local_binary_only"):
        raise ValueError("Evidence source or scope is unverified")
    if record["customer_release_ready"] is not False or record["legal_notice_approved"] is not False:
        raise ValueError("A read-only receipt may not approve commercial release")
    if record["signature_observation"] not in {
        "Valid", "NotSigned", "Other", "Unavailable",
    }:
        raise ValueError("Invalid signature observation")
    defender = record["defender"]
    if not isinstance(defender, dict) or set(defender) != {
        "availability", "antivirus_enabled", "real_time_protection_enabled"
    }:
        raise ValueError("Invalid Defender observation")
    if defender["availability"] not in {"OBSERVED", "UNVERIFIED"}:
        raise ValueError("Invalid Defender availability")
    for name in ("antivirus_enabled", "real_time_protection_enabled"):
        val = defender[name]
        if val is not None and type(val) is not bool:
            raise ValueError("Invalid Defender boolean")
        if defender["availability"] == "UNVERIFIED" and val is not None:
            raise ValueError("Unavailable Defender data must not be inferred")
    gates = record["pending_gates"]
    if not isinstance(gates, dict) or set(gates) != set(PENDING):
        raise ValueError("Missing or unexpected product acceptance gate")
    if any(gates[key] != "UNVERIFIED" for key in PENDING):
        raise ValueError("Host evidence cannot certify pending retail or legal gates")
    sha = record["exe_sha256"]
    if not isinstance(sha, str) or re.fullmatch(r"[a-f0-9]{64}", sha) is None:
        raise ValueError("Invalid binary SHA-256")
    size = record["exe_bytes"]
    if type(size) is not int or not 0 < size <= 256 * 1024 * 1024:
        raise ValueError("Invalid binary size")
    if not executable.is_file() or executable.is_symlink():
        raise ValueError("Executable missing or symlinked")
    if executable.stat().st_size != size:
        raise ValueError("EXE changed size since receipt capture")
    hasher = hashlib.sha256()
    with executable.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    if hasher.hexdigest() != sha:
        raise ValueError("EXE SHA-256 differs from locally recorded evidence")
    return {
        "local_exe_hash_verified": True,
        "defender_settings_observed": defender["availability"] == "OBSERVED",
        "signature_observed": record["signature_observation"],
        "pending_gate_count": len(PENDING),
        "customer_release_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Local Windows evidence integrity and release-gate validator")
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--exe", type=Path, required=True)
    args = parser.parse_args()
    try:
        if not args.evidence.is_file() or args.evidence.stat().st_size > MAX_EVIDENCE_BYTES:
            raise ValueError("Evidence missing or oversized")
        record = json.loads(args.evidence.read_text(encoding="utf-8-sig"))
        result = validate_evidence(record, args.exe)
    except (ValueError, OSError, TypeError, KeyError, json.JSONDecodeError):
        print("WINDOWS_ACCEPTANCE_RECEIPT_INVALID")
        return 1
    print("WINDOWS_ACCEPTANCE_READONLY_EVIDENCE_PASS")
    print("BINARY_HASH_MATCH=" + str(result["local_exe_hash_verified"]))
    print("DEFENDER_SETTINGS_OBSERVED=" + str(result["defender_settings_observed"]))
    print("RETAIL_OS_PACKET_SMARTSCREEN_PDF_NOTICE=UNVERIFIED")
    print("CUSTOMER_RELEASE_READY=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
