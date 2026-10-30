"""Consolidate *existing* exact-EXE Windows receipts without approving a release.

Offline developer/owner review helper, not a customer-facing acceptance
certificate. Does not launch the EXE, Defender, a browser, or customer code,
and never uploads files or copies original licenses into the output.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.runtime_version_receipt import verify_receipt
from scripts.verify_upstream_tcl_tk_license import _safe_read
from scripts.windows_acceptance_contract import (
    MAX_EVIDENCE_BYTES as MAX_ACCEPTANCE,
    validate_evidence,
)
from scripts.windows_local_exe_smoke_contract import (
    MAX_RECEIPT_BYTES as MAX_SMOKE, validate_receipt,
)
from scripts.windows_defender_scan_contract import (
    MAX_EVIDENCE_BYTES as MAX_DEFENDER, validate_scan_receipt,
)
from scripts.runtime_version_receipt import MAX_RECEIPT_BYTES as MAX_RUNTIME

FORMAT = "code_checker_exact_exe_release_preflight_evidence_v1"
GATES = (
    "interactive_buyer_gui",
    "clean_consumer_windows_10_11",
    "smartscreen_reputation_on_buyer_pc",
    "defender_on_buyer_pc",
    "os_level_network_capture",
    "korean_pdf_visual_inspection",
    "actual_binary_owner_and_original_license_notice",
    "final_customer_zip_and_owner_release_approval",
)


def _load(path: Path, bound: int) -> dict:
    raw = _safe_read(path, bound)
    data = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Receipt must be a JSON object")
    return data


def consolidate(exe: Path, readonly: dict, smoke: dict, *,
                runtime: dict | None = None, defender: dict | None = None) -> dict:
    """Validate every supplied source independently against this exact EXE."""
    accepted = validate_evidence(readonly, exe)
    synthetic = validate_receipt(smoke, exe)
    sha, size = readonly["exe_sha256"], readonly["exe_bytes"]
    if (sha != smoke["exe_sha256"] or size != smoke["exe_bytes"]):
        raise ValueError("Read-only and synthetic evidence describe different files")
    results = {
        "read_only_os_and_signature_metadata": "RECEIPT_INTEGRITY_VERIFIED",
        "packaged_gui_and_preview_scan_synthetic": "SYNTHETIC_PASS",
        "frozen_tcl_tk_patchlevels": "NOT_PROVIDED",
        "defender_custom_scan_command": "NOT_PROVIDED",
    }
    observations = {
        "windows_signature_status": accepted["signature_observed"],
        "defender_settings_observed": accepted["defender_settings_observed"],
        "frozen_tcl_patchlevel": None,
        "frozen_tk_patchlevel": None,
        "defender_custom_scan_command_status": None,
    }
    if (not accepted["local_exe_hash_verified"]
            or not synthetic["exe_hash_verified"]
            or synthetic["packaged_tk_and_synthetic_workflow"] != "PASS"):
        raise ValueError("Required EXE receipt integrity not verified")

    if runtime is not None:
        verify_receipt(runtime, exe)
        if runtime["exe_sha256"] != sha or runtime["exe_bytes"] != size:
            raise ValueError("Frozen EXE runtime and other receipts differ")
        results["frozen_tcl_tk_patchlevels"] = "FROZEN_RECEIPT_HASH_VERIFIED"
        observations["frozen_tcl_patchlevel"] = runtime["tcl_runtime_patchlevel"]
        observations["frozen_tk_patchlevel"] = runtime["tk_runtime_patchlevel"]
    if defender is not None:
        evidence = validate_scan_receipt(defender, exe)
        if defender["exe_sha256"] != sha or defender["exe_bytes"] != size:
            raise ValueError("Defender and GUI/readonly receipts differ")
        results["defender_custom_scan_command"] = "RECEIPT_INTEGRITY_VERIFIED"
        observations["defender_custom_scan_command_status"] = defender["scan_command_status"]
        if evidence["malware_free_certified"] is not False:
            raise ValueError("Defender cannot certify a malware-free binary")

    return {
        "format": FORMAT,
        "exe_sha256": sha,
        "exe_bytes": size,
        "receipt_evidence": results,
        "observations_not_acceptance": observations,
        "human_release_gates": {gate: "UNVERIFIED" for gate in GATES},
        "receipt_files_and_binary_in_output": False,
        "original_license_texts_in_output": False,
        "customer_source_or_local_paths_in_output": False,
        "real_buyer_pc_test_certified": False,
        "malware_free_certified": False,
        "legal_notice_approved": False,
        "customer_release_ready": False,
        "status": "EXACT_BINARY_RECEIPTS_VALID_RELEASE_BLOCKED",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline exact-EXE Windows evidence summary (not release approval)")
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--readonly", required=True, type=Path)
    parser.add_argument("--smoke", required=True, type=Path)
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--defender", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    a = parser.parse_args(argv)
    inputs = [a.exe, a.readonly, a.smoke] + [p for p in (a.runtime, a.defender) if p is not None]
    try:
        if (a.out.exists() or a.out.is_symlink() or not a.out.parent.is_dir()
                or a.out.parent.is_symlink() or a.out.suffix.lower() != ".json"
                or a.out in inputs or len(set(inputs)) != len(inputs)):
            raise ValueError("Refuse overwrite, linked output directory or duplicate inputs")
        result = consolidate(
            a.exe, _load(a.readonly, MAX_ACCEPTANCE), _load(a.smoke, MAX_SMOKE),
            runtime=_load(a.runtime, MAX_RUNTIME) if a.runtime is not None else None,
            defender=_load(a.defender, MAX_DEFENDER) if a.defender is not None else None,
        )
        with a.out.open("x", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=True, sort_keys=True, indent=2)
        print("EXACT_EXE_WINDOWS_RECEIPT_CONSOLIDATION_PASS")
        print("EXE_HASH_VERIFIED=True")
        print("CONSUMER_OS_AND_LAWFUL_CUSTOMER_RELEASE=UNVERIFIED")
        print("CUSTOMER_RELEASE_READY=False")
        return 0
    except (OSError, ValueError, KeyError, TypeError, UnicodeError,
            json.JSONDecodeError):
        print("EXACT_EXE_WINDOWS_RECEIPT_CONSOLIDATION_INVALID")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
