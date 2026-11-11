"""P3-03: one-command, owner-opted-in OFFLINE private candidate + exact EXE receipt review.

Never distribute, execute a customer EXE, generate legal texts or grant release.
On any error, only newly created candidate outputs owned by this invocation are removed.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from input_safety import validate_offline_input_path
from scripts.build_private_customer_candidate import create_private_candidate
from scripts.consolidate_windows_retail_evidence import (
    MAX_ACCEPTANCE, MAX_SMOKE, MAX_DEFENDER, MAX_RUNTIME, _load,
)
from scripts.link_private_candidate_evidence import link_candidate_evidence
from scripts.verify_customer_zip_candidate import inspect_candidate

FORMAT = "code_checker_owner_private_retail_review_v1"


def _fail() -> ValueError:
    return ValueError("PRIVATE_RETAIL_REVIEW_BLOCKED")


def _input_path(value: Path) -> Path:
    if not isinstance(value, Path) or not value.is_absolute():
        raise _fail()
    checked = validate_offline_input_path(value)
    if not checked.is_file() or checked.is_symlink():
        raise _fail()
    return checked


def _new_output(value: Path, suffix: str) -> Path:
    if (not isinstance(value, Path) or not value.is_absolute()
            or value.suffix.lower() != suffix or value.exists() or value.is_symlink()):
        raise _fail()
    checked = validate_offline_input_path(value)
    if not checked.parent.is_dir() or checked.parent.is_symlink():
        raise _fail()
    return checked


def prepare_private_review(*, exe: Path, readme: Path, license_file: Path,
                           notice: Path, component_licenses: dict[str, Path],
                           readonly: Path, smoke: Path,
                           output_zip: Path, output_receipt: Path,
                           runtime: Path | None = None, defender: Path | None = None) -> dict:
    if not isinstance(component_licenses, dict) or not component_licenses:
        raise _fail()
    inputs = [exe, readme, license_file, notice, readonly, smoke,
              *component_licenses.values()]
    inputs.extend(x for x in (runtime, defender) if x is not None)
    if (len(set(inputs)) != len(inputs) or any(not isinstance(x, Path) for x in inputs)
            ):
        raise _fail()
    checked = {_input_path(x) for x in inputs}
    output_zip = _new_output(output_zip, ".zip")
    output_receipt = _new_output(output_receipt, ".json")
    if output_zip == output_receipt or output_zip in checked or output_receipt in checked:
        raise _fail()
    # Load original actual Windows/EXE receipts *before* writing any output.
    ro = _load(readonly, MAX_ACCEPTANCE)
    sm = _load(smoke, MAX_SMOKE)
    rt = _load(runtime, MAX_RUNTIME) if runtime is not None else None
    df = _load(defender, MAX_DEFENDER) if defender is not None else None
    created_zip = False
    created_receipt = False
    try:
        made = create_private_candidate(exe=exe, readme=readme,
            license_file=license_file, notice=notice, component_licenses=component_licenses,
            output=output_zip)
        created_zip = True
        bound = link_candidate_evidence(exe, output_zip, ro, sm, runtime=rt, defender=df)
        if (bound["customer_release_ready"] is not False
                or made["status"] != "PRIVATE_CANDIDATE_CREATED_RELEASE_BLOCKED"
                or bound["status"] != "PRIVATE_ZIP_AND_WINDOWS_RECEIPTS_LINKED_RELEASE_BLOCKED"
                or bound["exact_exe_sha256"] != made["exact_exe_sha256"]
                or bound["candidate_zip_sha256"] != made["candidate_zip_sha256"]):
            raise _fail()
        report = {
            "format": FORMAT, "status": "PRIVATE_RETAIL_REVIEW_CANDIDATE_RELEASE_BLOCKED",
            "exact_exe_sha256": bound["exact_exe_sha256"],
            "candidate_zip_sha256": bound["candidate_zip_sha256"],
            "entries_checked": bound["entries_checked"],
            "human_release_gates": bound["human_release_gates"],
            "synthetic_packaged_gui_receipt_verified": True,
            "windows_readonly_receipt_verified": True,
            "optional_runtime_receipt_provided": rt is not None,
            "optional_defender_receipt_provided": df is not None,
            "original_license_texts_verified": False,
            "vendor_redistribution_rights_verified": False,
            "real_buyer_pc_test_certified": False,
            "legal_notice_approved": False,
            "owner_release_approval": False,
            "customer_release_ready": False,
        }
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        fd = os.open(output_receipt, flags, 0o600)
        created_receipt = True
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(report, stream, ensure_ascii=True, sort_keys=True, indent=2)
            stream.write("\n")
        # Verify that neither the private ZIP nor its independent EXE changed.
        final = inspect_candidate(output_zip, exe)
        if (final["exact_exe_sha256"] != report["exact_exe_sha256"]
                or final["candidate_zip_sha256"] != report["candidate_zip_sha256"]):
            raise _fail()
        return report
    except Exception:
        if created_receipt:
            output_receipt.unlink(missing_ok=True)
        if created_zip:
            output_zip.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Owner-only offline private ZIP + Windows receipt review (no sale)")
    for required in ("exe", "readme", "license", "notice", "readonly", "smoke", "out-zip", "out-report"):
        parser.add_argument("--" + required, type=Path, required=True)
    for optional in ("runtime", "defender"):
        parser.add_argument("--" + optional, type=Path)
    parser.add_argument("--component-license", action="append", default=[], metavar="NAME=PATH")
    a = parser.parse_args(argv)
    try:
        components = {}
        for item in a.component_license:
            if "=" not in item:
                raise _fail()
            name, file = item.split("=", 1)
            if name in components:
                raise _fail()
            components[name] = Path(file)
        result = prepare_private_review(exe=a.exe, readme=a.readme,
            license_file=a.license, notice=a.notice, component_licenses=components,
            readonly=a.readonly, smoke=a.smoke,
            output_zip=a.out_zip, output_receipt=a.out_report,
            runtime=a.runtime, defender=a.defender)
        print(result["status"])
        print("EXE_SHA256=" + result["exact_exe_sha256"])
        print("ZIP_SHA256=" + result["candidate_zip_sha256"])
        print("CUSTOMER_RELEASE_READY=False")
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, json.JSONDecodeError):
        print("PRIVATE_RETAIL_REVIEW_BLOCKED")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
