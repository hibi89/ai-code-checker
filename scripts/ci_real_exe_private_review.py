"""CI-only real Windows frozen EXE -> synthetic private customer ZIP integration.

Tests the *actual* fresh EXE and separately collected Windows receipts in a
throwaway directory. Embedded documentation is inert, intentionally invalid
as legal notices; it must never be distributed or used to claim release.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from scripts.prepare_private_retail_review import prepare_private_review
from scripts.verify_customer_zip_candidate import inspect_candidate


def _digest(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    count = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
            count += len(chunk)
    return h.hexdigest(), count


def _checked(value: bool, label: str) -> None:
    if not value:
        raise AssertionError(label)


def main() -> int:
    if os.name != "nt":
        print("REAL_EXE_PRIVATE_ZIP_NOT_RUN_REQUIRES_WINDOWS")
        return 2

    repo = Path(__file__).resolve().parents[1]
    exe = (repo / "dist-windows" / "CodeCheckerOffline.exe").absolute()
    evidence = repo / ".build-windows"
    readonly = (evidence / "windows-acceptance-readonly.json").absolute()
    smoke = (evidence / "windows-local-exe-smoke.json").absolute()
    runtime = (evidence / "runtime-version-receipt.json").absolute()
    defender = (evidence / "defender-custom-scan.json").absolute()
    for path in (exe, readonly, smoke, runtime, defender):
        _checked(path.is_file() and not path.is_symlink(), "SOURCE_OR_RECEIPT_NOT_FOUND")

    original_hash, original_bytes = _digest(exe)
    _checked(original_bytes > 1024 * 1024, "REAL_EXE_EXPECTED_NOT_INERT_FIXTURE")

    # Synthetic license strings are test data, not actual vendor permissions.
    # No real owner/vendor EXE, customer report or legal text is uploaded.
    with tempfile.TemporaryDirectory(prefix="codechecker-ci-real-exe-") as scratch:
        folder = Path(scratch)
        documents = {
            "readme": "README-ci-source.txt",
            "license": "LICENSE-ci-not-valid.txt",
            "notice": "NOTICE-ci-not-valid.txt",
            "component": "component-ci-not-valid.terms",
        }
        files: dict[str, Path] = {}
        for role, filename in documents.items():
            path = folder / filename
            path.write_text(
                "SYNTHETIC TEST FIXTURE ONLY. NOT A COPYRIGHT LICENSE. "
                "NOT FOR SALES OR DISTRIBUTION. " + role + "\n",
                encoding="utf-8",
            )
            files[role] = path

        candidate = folder / "fresh-private-review.zip"
        report_path = folder / "fresh-review-receipt.json"
        arguments = dict(
            exe=exe,
            readme=files["readme"],
            license_file=files["license"],
            notice=files["notice"],
            component_licenses={"SyntheticComponent.terms": files["component"]},
            readonly=readonly,
            smoke=smoke,
            runtime=runtime,
            defender=defender,
            output_zip=candidate,
            output_receipt=report_path,
        )

        result = prepare_private_review(**arguments)
        confirmed = json.loads(report_path.read_text(encoding="utf-8"))
        independently_checked = inspect_candidate(candidate, exe)
        _checked(result == confirmed, "WRITTEN_RECEIPT_MISMATCH")
        _checked(result["status"] == "PRIVATE_RETAIL_REVIEW_CANDIDATE_RELEASE_BLOCKED",
                 "UNEXPECTED_PRIVATE_REVIEW_STATUS")
        _checked(result["customer_release_ready"] is False
                 and result["legal_notice_approved"] is False
                 and result["original_license_texts_verified"] is False
                 and result["vendor_redistribution_rights_verified"] is False
                 and result["real_buyer_pc_test_certified"] is False
                 and result["owner_release_approval"] is False,
                 "FALSE_RETAIL_APPROVAL")
        _checked(len(result["human_release_gates"]) >= 8
                 and set(result["human_release_gates"].values()) == {"UNVERIFIED"},
                 "MANUAL_GATES_CANNOT_BE_AUTO_PASSED")
        _checked(result["optional_runtime_receipt_provided"] is True
                 and result["optional_defender_receipt_provided"] is True,
                 "EXACT_WINDOWS_RECEIPTS_MISSING")
        _checked(result["exact_exe_sha256"] == independently_checked["exact_exe_sha256"]
                 == original_hash
                 and independently_checked["exact_exe_bytes"] == original_bytes,
                 "EXE_BINARY_IDENTITY_MISMATCH")
        _checked(result["candidate_zip_sha256"] == independently_checked["candidate_zip_sha256"]
                 == _digest(candidate)[0],
                 "CANDIDATE_IDENTITY_MISMATCH")

        # Read the actual EXE out of the ZIP, not only the manifest metadata.
        h = hashlib.sha256()
        total = 0
        with zipfile.ZipFile(candidate) as z:
            _checked(set(z.namelist()) == {
                "CodeCheckerOffline.exe", "README.txt", "LICENSE", "NOTICE.txt",
                "LICENSES/SyntheticComponent.terms", "SHA256SUMS.txt",
            }, "EXACT_ZIP_CONTENTS_MISMATCH")
            with z.open("CodeCheckerOffline.exe") as packaged:
                for chunk in iter(lambda: packaged.read(1024 * 1024), b""):
                    h.update(chunk)
                    total += len(chunk)
        _checked(h.hexdigest() == original_hash and total == original_bytes,
                 "PHYSICAL_ZIP_EXE_CHANGED")

        # Materialize the *packaged* EXE in a Korean/space-containing directory,
        # then execute it with system binaries on PATH but no Python installation.
        # The EXE is our own freshly built GitHub candidate, never customer code.
        consumer_folder = folder / "고객 점검 folder with spaces"
        consumer_folder.mkdir()
        extracted = consumer_folder / "CodeCheckerOffline.exe"
        with zipfile.ZipFile(candidate, "r") as z:
            with z.open("CodeCheckerOffline.exe") as source:
                with extracted.open("xb") as target:
                    shutil.copyfileobj(source, target, length=1024 * 1024)
        _checked(_digest(extracted) == (original_hash, original_bytes),
                 "EXTRACTED_EXE_IDENTITY_MISMATCH")

        clean_env = {k: v for k, v in os.environ.items()
                     if not k.upper().startswith(("PYTHON", "PYINSTALLER", "_MEIPASS"))}
        system_root = Path(clean_env.get("SystemRoot") or r"C:\Windows")
        clean_env["PATH"] = os.pathsep.join(
            (str(system_root / "System32"), str(system_root)))
        for mode in ("--self-test", "--gui-smoke", "--scenario-smoke"):
            try:
                completed = subprocess.run(
                    [str(extracted), mode], cwd=consumer_folder,
                    env=clean_env, timeout=120, check=False,
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except subprocess.TimeoutExpired as exc:
                raise AssertionError("EXTRACTED_EXE_MODE_TIMEOUT:" + mode) from exc
            _checked(completed.returncode == 0,
                     "EXTRACTED_EXE_MODE_FAILED:" + mode)
        _checked(_digest(extracted) == (original_hash, original_bytes),
                 "PACKAGED_EXE_MODIFIED_AFTER_RUN")

        before = (_digest(candidate), _digest(report_path))
        try:
            prepare_private_review(**arguments)
        except (ValueError, OSError):
            pass
        else:
            raise AssertionError("MUST_REJECT_REUSED_CUSTOMER_ZIP_PATH")
        _checked((_digest(candidate), _digest(report_path)) == before,
                 "EXISTING_PRIVATE_OUTPUT_OVERWRITTEN")
        _checked(_digest(exe) == (original_hash, original_bytes),
                 "ORIGINAL_WINDOWS_EXE_MODIFIED")

    print("REAL_FROZEN_WINDOWS_EXE_PRIVATE_ZIP_E2E_PASS")
    print("EXACT_EXE_SHA256=" + original_hash)
    print("ZIP_RECEIPT_AND_BUNDLE_HASHES_VERIFIED=True")
    print("EXTRACTED_KOREAN_PATH_PYTHON_FREE_EXE_SMOKE=PASS")
    print("CUSTOMER_RELEASE_READY=False")
    print("LICENSE_AND_ACTUAL_BUYER_PC_ACCEPTANCE=UNVERIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
