"""Fail-closed verifier for an optional local Microsoft Defender EXE scan receipt.

The script does not start Defender or claim malware-free/release clearance.
A zero MpCmdRun exit alone is insufficient to prove absence of detections.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

FORMAT = "code_checker_defender_file_scan_v1"
FIELDS = {
    "format", "collection_method", "scope", "exe_sha256", "exe_bytes",
    "defender_availability", "scanner_available", "scan_attempted",
    "scan_command_status", "command_exit_code", "exe_unchanged",
    "malware_free_certified", "retail_defender_acceptance",
    "customer_release_ready",
}
STATUSES = {"UNVERIFIED", "ZERO_EXIT", "NONZERO_EXIT", "TIMEOUT", "SCAN_ERROR", "EXE_CHANGED"}
MAX_EVIDENCE_BYTES = 16 * 1024


def validate_scan_receipt(record: dict, executable: Path) -> dict:
    """Validate internal coherence plus local EXE hash, never security quality."""
    if not isinstance(record, dict) or set(record) != FIELDS:
        raise ValueError("Invalid Defender receipt schema")
    if (record["format"] != FORMAT
            or record["collection_method"] != "local_mpcmdrun_custom_file_scan_no_remediation"
            or record["scope"] != "local_developer_or_hosted_windows_binary_only"):
        raise ValueError("Unrecognized scan evidence source")
    if (record["malware_free_certified"] is not False
            or record["customer_release_ready"] is not False
            or record["retail_defender_acceptance"] != "UNVERIFIED"):
        raise ValueError("Developer scan may not grant a security/release approval")
    if record["defender_availability"] not in {"ENABLED", "DISABLED", "UNVERIFIED"}:
        raise ValueError("Defender availability is unverified")
    if type(record["scanner_available"]) is not bool or type(record["scan_attempted"]) is not bool:
        raise ValueError("Invalid process observation types")
    if type(record["exe_unchanged"]) is not bool or not record["exe_unchanged"]:
        raise ValueError("EXE changed or integrity could not be verified")
    status = record["scan_command_status"]
    if status not in STATUSES or status == "EXE_CHANGED":
        raise ValueError("Scan status is unrecognized or EXE changed")
    attempted = record["scan_attempted"]
    code = record["command_exit_code"]
    if attempted:
        if record["defender_availability"] != "ENABLED" or record["scanner_available"] is not True:
            raise ValueError("Scan cannot be claimed without available enabled Defender")
        if status == "ZERO_EXIT" and (type(code) is not int or code != 0):
            raise ValueError("Zero-exit claim without a zero exit code")
        if status == "NONZERO_EXIT" and (type(code) is not int or code == 0):
            raise ValueError("Nonzero-exit claim without nonzero exit code")
        if status in {"UNVERIFIED", "TIMEOUT", "SCAN_ERROR"} and code is not None:
            raise ValueError("Uncompleted scan cannot invent an exit code")
    elif status != "UNVERIFIED" or code is not None:
        raise ValueError("Non-attempted scan cannot claim execution")
    if code is not None and (type(code) is not int or not -2**31 <= code <= 2**31-1):
        raise ValueError("Invalid process return code")
    sha = record["exe_sha256"]
    size = record["exe_bytes"]
    if not isinstance(sha, str) or re.fullmatch(r"[a-f0-9]{64}", sha) is None:
        raise ValueError("Invalid EXE hash")
    if type(size) is not int or not 0 < size <= 256 * 1024 * 1024:
        raise ValueError("Invalid EXE byte size")
    if executable.is_symlink() or not executable.is_file() or executable.stat().st_size != size:
        raise ValueError("Executable missing, linked or changed")
    digest = hashlib.sha256()
    with executable.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(data)
    if digest.hexdigest() != sha:
        raise ValueError("Executable SHA differs from scan receipt")
    return {
        "command_zero_exit_observed": status == "ZERO_EXIT",
        "scan_attempted": attempted,
        "defender_availability": record["defender_availability"],
        "malware_free_certified": False,
        "retail_defender_acceptance": "UNVERIFIED",
        "customer_release_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate local Defender scan receipt without claiming release")
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--exe", required=True, type=Path)
    args = parser.parse_args()
    try:
        if not args.evidence.is_file() or not 0 < args.evidence.stat().st_size <= MAX_EVIDENCE_BYTES:
            raise ValueError("Missing/oversized evidence file")
        record = json.loads(args.evidence.read_text(encoding="utf-8-sig"))
        result = validate_scan_receipt(record, args.exe)
    except (ValueError, OSError, TypeError, KeyError, json.JSONDecodeError):
        print("DEFENDER_SCAN_RECEIPT_INVALID")
        return 1
    print("DEFENDER_SCAN_RECEIPT_INTEGRITY_PASS")
    print("DEFENDER_SCAN_ATTEMPTED=" + str(result["scan_attempted"]))
    print("DEFENDER_COMMAND_ZERO_EXIT=" + str(result["command_zero_exit_observed"]))
    print("MALWARE_FREE_CERTIFIED=False")
    print("RETAIL_DEFENDER_ACCEPTANCE=UNVERIFIED")
    print("CUSTOMER_RELEASE_READY=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
