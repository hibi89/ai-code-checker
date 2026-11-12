"""P3-03: executable-shaped inert bytes + source-pinned private ZIP and Windows receipts.

Synthetic Windows receipts are fixtures only; these tests never certify Windows or law.
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.prepare_private_retail_review import prepare_private_review, main
from scripts.runtime_version_receipt import FORMAT as RUNTIME_FORMAT, FLAGS
from scripts.windows_acceptance_contract import FORMAT as READONLY_FORMAT, PENDING as RO_PENDING
from scripts.windows_local_exe_smoke_contract import FORMAT as SMOKE_FORMAT, PENDING as SMOKE_PENDING
from scripts.windows_defender_scan_contract import FORMAT as DEFENDER_FORMAT
from scripts.verify_customer_zip_candidate import inspect_candidate


class OwnerPrivateReviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="codechecker-p303-inert-")
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.exe = self.base / "CodeCheckerOffline.exe"
        self.exe.write_bytes(b"MZ THIS IS INERT, NOT A WINDOWS EXECUTABLE")
        paths = []
        for i, label in enumerate(("README", "LICENSE", "NOTICE", "component")):
            p = self.base / (label + "-original.txt")
            p.write_bytes(("SYNTHETIC ONLY, NOT LEGAL TEXT " + str(i)).encode())
            paths.append(p)
        self.readme, self.license_file, self.notice, self.component = paths
        self.ro = self.base / "readonly.json"
        self.sm = self.base / "smoke.json"
        sha = hashlib.sha256(self.exe.read_bytes()).hexdigest()
        size = self.exe.stat().st_size
        self.readonly = {
            "format": READONLY_FORMAT, "collection_method": "win32_readonly_powershell",
            "scope": "local_binary_only", "exe_sha256": sha, "exe_bytes": size,
            "signature_observation": "Unavailable",
            "defender": {"availability": "UNVERIFIED", "antivirus_enabled": None,
                         "real_time_protection_enabled": None},
            "pending_gates": {g: "UNVERIFIED" for g in RO_PENDING},
            "customer_release_ready": False, "legal_notice_approved": False,
        }
        self.smoke = {
            "format": SMOKE_FORMAT,
            "collection_method": "two_synthetic_exe_modes_no_python_required",
            "scope": "existing_local_exe_only", "exe_sha256": sha, "exe_bytes": size,
            "observed_synthetic": {
                "packaged_tk_gui_startup": "PASS", "packaged_preview_scan_report": "PASS",
                "executable_hash_stable": True},
            "pending_gates": {g: "UNVERIFIED" for g in SMOKE_PENDING},
            "actual_customer_code_used": False,
            "actual_customer_release_ready": False, "legal_notice_approved": False,
        }
        self.save_receipts()
        self.out_zip = self.base / "FRESH-private.zip"
        self.out_json = self.base / "FRESH-review.json"

    def save_receipts(self):
        self.ro.write_text(json.dumps(self.readonly))
        self.sm.write_text(json.dumps(self.smoke))

    def kw(self):
        return dict(exe=self.exe, readme=self.readme, license_file=self.license_file,
                    notice=self.notice, component_licenses={"Component.terms": self.component},
                    readonly=self.ro, smoke=self.sm,
                    output_zip=self.out_zip, output_receipt=self.out_json)

    def test_one_command_end_to_end_creates_only_hold_zip_and_receipt(self):
        receipts = prepare_private_review(**self.kw())
        self.assertEqual(receipts["status"], "PRIVATE_RETAIL_REVIEW_CANDIDATE_RELEASE_BLOCKED")
        self.assertEqual(receipts["entries_checked"], 6)
        self.assertFalse(receipts["customer_release_ready"])
        self.assertFalse(receipts["legal_notice_approved"])
        self.assertFalse(receipts["owner_release_approval"])
        self.assertEqual(len(receipts["human_release_gates"]), 8)
        self.assertTrue(all(v == "UNVERIFIED" for v in receipts["human_release_gates"].values()))
        separate = inspect_candidate(self.out_zip, self.exe)
        self.assertEqual(receipts["candidate_zip_sha256"], separate["candidate_zip_sha256"])
        self.assertEqual(receipts["exact_exe_sha256"], separate["exact_exe_sha256"])
        self.assertEqual(json.loads(self.out_json.read_text()), receipts)

    def test_original_owner_inputs_and_windows_receipts_unmodified(self):
        saved = {p: p.read_bytes() for p in (self.exe,self.readme,self.license_file,
                  self.notice,self.component,self.ro,self.sm)}
        prepare_private_review(**self.kw())
        for p, content in saved.items(): self.assertEqual(p.read_bytes(), content)
        self.assertNotIn(str(self.base), self.out_json.read_text())
        self.assertNotIn("SYNTHETIC ONLY", self.out_json.read_text())

    def test_repeat_run_fails_without_overwriting_generated_zip_or_json(self):
        prepare_private_review(**self.kw())
        old_zip,old_json = self.out_zip.read_bytes(),self.out_json.read_bytes()
        with self.assertRaises((ValueError,OSError)): prepare_private_review(**self.kw())
        self.assertEqual(self.out_zip.read_bytes(),old_zip)
        self.assertEqual(self.out_json.read_bytes(),old_json)

    def test_existing_json_preserved_and_zip_never_created(self):
        self.out_json.write_text("ORIGINAL NONOVERWRITE")
        with self.assertRaises(ValueError): prepare_private_review(**self.kw())
        self.assertEqual(self.out_json.read_text(), "ORIGINAL NONOVERWRITE")
        self.assertFalse(self.out_zip.exists())

    def test_forged_readonly_host_acceptance_fails_with_unapproved_zip_retained(self):
        self.readonly["pending_gates"][next(iter(self.readonly["pending_gates"]))] = "PASS"
        self.save_receipts()
        with self.assertRaises(ValueError):prepare_private_review(**self.kw())
        self.assertTrue(self.out_zip.exists());self.assertFalse(self.out_json.exists())

    def test_mismatched_binary_receipt_same_size_refused(self):
        self.smoke["exe_sha256"] = "0"*64
        self.save_receipts()
        with self.assertRaises(ValueError):prepare_private_review(**self.kw())
        self.assertTrue(self.out_zip.exists());self.assertFalse(self.out_json.exists())

    def test_modified_exe_after_receipts_keeps_hold_zip(self):
        payload=self.exe.read_bytes()
        self.exe.write_bytes(payload.replace(b"MZ", b"Mz"))
        with self.assertRaises(ValueError): prepare_private_review(**self.kw())
        self.assertTrue(self.out_zip.exists());self.assertFalse(self.out_json.exists())

    def test_missing_notice_source_blocks_without_creating_output(self):
        self.notice.unlink()
        with self.assertRaises((ValueError,OSError)):prepare_private_review(**self.kw())
        self.assertFalse(self.out_zip.exists());self.assertFalse(self.out_json.exists())

    def test_duplicate_source_receipt_or_output_path_rejected(self):
        f=self.kw();f["smoke"]=f["readonly"]
        with self.assertRaises(ValueError):prepare_private_review(**f)
        f=self.kw();f["output_receipt"]=self.ro
        with self.assertRaises(ValueError):prepare_private_review(**f)

    def test_symlinked_output_parent_rejected(self):
        if os.name=="nt":self.skipTest("Windows junction acceptance requires native test")
        symlink=self.base/"junction"
        symlink.symlink_to(self.base, target_is_directory=True)
        f=self.kw();f["output_zip"]=symlink/"new.zip"
        with self.assertRaises(ValueError):prepare_private_review(**f)

    def test_corrupt_component_utf8_keeps_unapproved_candidate(self):
        self.component.write_bytes(b"\xff\xfe")
        with self.assertRaises(ValueError):prepare_private_review(**self.kw())
        self.assertTrue(self.out_zip.exists());self.assertFalse(self.out_json.exists())

    def test_optional_real_schema_runtime_defender_accepted_only_as_observation(self):
        sha=self.readonly["exe_sha256"];size=self.readonly["exe_bytes"]
        runtime=self.base/"runtime.json"
        runtime.write_text(json.dumps({"format":RUNTIME_FORMAT,"exe_sha256":sha,"exe_bytes":size,
            "frozen_process_runtime_observed":True,"python_runtime_version":"3.13.5",
            "tcl_runtime_patchlevel":"8.6.15","tk_runtime_patchlevel":"8.6.15",
            **{key:False for key in FLAGS}}))
        defender=self.base/"defender.json"
        defender.write_text(json.dumps({"format":DEFENDER_FORMAT,
            "collection_method":"local_mpcmdrun_custom_file_scan_no_remediation",
            "scope":"local_developer_or_hosted_windows_binary_only",
            "exe_sha256":sha,"exe_bytes":size,"defender_availability":"UNVERIFIED",
            "scanner_available":False,"scan_attempted":False,"scan_command_status":"UNVERIFIED",
            "command_exit_code":None,"exe_unchanged":True,"malware_free_certified":False,
            "retail_defender_acceptance":"UNVERIFIED","customer_release_ready":False}))
        result=prepare_private_review(**self.kw(),runtime=runtime,defender=defender)
        self.assertTrue(result["optional_runtime_receipt_provided"])
        self.assertTrue(result["optional_defender_receipt_provided"])
        self.assertFalse(result["customer_release_ready"])

    def test_forged_runtime_legal_rights_refused_without_approval(self):
        sha=self.readonly["exe_sha256"];size=self.readonly["exe_bytes"]
        runtime=self.base/"runtime.json"
        runtime.write_text(json.dumps({"format":RUNTIME_FORMAT,"exe_sha256":sha,"exe_bytes":size,
            "frozen_process_runtime_observed":True,"python_runtime_version":"3.13.5",
            "tcl_runtime_patchlevel":"8.6.15","tk_runtime_patchlevel":"8.6.15",
            **{key:True for key in FLAGS}}))
        with self.assertRaises(ValueError):prepare_private_review(**self.kw(),runtime=runtime)
        self.assertTrue(self.out_zip.exists());self.assertFalse(self.out_json.exists())

    def test_final_physical_validation_failure_preserves_hold_outputs(self):
        from scripts import prepare_private_retail_review as mod
        original=mod.inspect_candidate
        def corrupt_after(*args,**kwargs):
            raise ValueError("synthetic post-write invalid")
        with patch.object(mod,"inspect_candidate",side_effect=corrupt_after):
            with self.assertRaises(ValueError):prepare_private_review(**self.kw())
        self.assertTrue(self.out_zip.exists());self.assertTrue(self.out_json.exists())
        self.assertTrue(self.exe.exists());self.assertTrue(self.ro.exists())

    def test_replaced_review_outputs_remain_untouched_after_late_failure(self):
        from scripts import prepare_private_retail_review as mod
        def replace_outputs(*_args, **_kwargs):
            self.out_zip.unlink()
            self.out_zip.write_bytes(b"OTHER-WRITER-ZIP")
            self.out_json.unlink()
            self.out_json.write_bytes(b"OTHER-WRITER-JSON")
            raise ValueError("synthetic concurrent replacement")
        with patch.object(mod, "inspect_candidate", side_effect=replace_outputs):
            with self.assertRaises(ValueError):prepare_private_review(**self.kw())
        self.assertEqual(self.out_zip.read_bytes(), b"OTHER-WRITER-ZIP")
        self.assertEqual(self.out_json.read_bytes(), b"OTHER-WRITER-JSON")
        with self.assertRaises(ValueError):prepare_private_review(**self.kw())

    def test_cli_prints_only_hashes_not_private_paths_or_license_text(self):
        argv=["--exe",str(self.exe),"--readme",str(self.readme),
              "--license",str(self.license_file),"--notice",str(self.notice),
              "--readonly",str(self.ro),"--smoke",str(self.sm),
              "--component-license","Component.terms="+str(self.component),
              "--out-zip",str(self.out_zip),"--out-report",str(self.out_json)]
        with patch("sys.stdout",new_callable=io.StringIO) as stream:
            self.assertEqual(main(argv),0)
            output=stream.getvalue()
        self.assertIn("RELEASE_BLOCKED",output)
        self.assertNotIn(str(self.base),output)
        self.assertNotIn("SYNTHETIC",output)
        self.assertFalse(json.loads(self.out_json.read_text())["customer_release_ready"])

    def test_zero_component_license_argument_refused(self):
        f=self.kw();f["component_licenses"]={}
        with self.assertRaises(ValueError):prepare_private_review(**f)
        self.assertFalse(self.out_zip.exists())


if __name__ == "__main__":
    unittest.main()
