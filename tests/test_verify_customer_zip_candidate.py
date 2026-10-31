"""Inert ZIP fixtures only; no real executables or third-party licenses."""
from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from scripts.verify_customer_zip_candidate import inspect_candidate, main


class PrivateZipCandidateTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="codechecker-retail-zip-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.exe = self.root / "CodeCheckerOffline.exe"
        self.exe.write_bytes(b"MZ INERT SYNTHETIC NOT EXECUTABLE")
        self.archive = self.root / "candidate-private.zip"
        self.files = {
            "CodeCheckerOffline.exe": self.exe.read_bytes(),
            "README.txt": b"Code Checker candidate readme. Review before distribution.\n",
            "LICENSE": b"INERT TEST ONLY. This is not a license or redistribution approval.\n",
            "NOTICE.txt": b"INERT TEST ONLY. This is not a third party notice.\n",
            "LICENSES/Example.txt": b"INERT TEST LICENSE CONTENT - NOT DISTRIBUTABLE.\n",
        }

    def write_zip(self, files=None, *, duplicate=None, symlink=False, corrupt_sum=False):
        payload = dict(files if files is not None else self.files)
        checksum = "".join(
            f"{hashlib.sha256(payload[n]).hexdigest()}  {n}\n"
            for n in sorted(payload)
        ).encode("ascii")
        if corrupt_sum:
            checksum = checksum.replace(b"a", b"b", 1)
        with zipfile.ZipFile(self.archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for name, content in payload.items():
                if symlink and name == "LICENSES/Example.txt":
                    info = zipfile.ZipInfo(name)
                    info.create_system = 3
                    info.external_attr = (0o120777 << 16)
                    z.writestr(info, content)
                else:
                    z.writestr(name, content)
            z.writestr("SHA256SUMS.txt", checksum)
            if duplicate is not None:
                z.writestr(duplicate, b"duplicate")

    def test_structural_receipt_does_not_claim_legal_or_sale_approval(self):
        self.write_zip()
        record = inspect_candidate(self.archive, self.exe)
        self.assertEqual(record["entries_checked"], 6)
        self.assertEqual(record["exact_exe_sha256"], hashlib.sha256(self.exe.read_bytes()).hexdigest())
        self.assertEqual(record["candidate_zip_sha256"], hashlib.sha256(self.archive.read_bytes()).hexdigest())
        self.assertFalse(record["customer_release_ready"])
        self.assertFalse(record["vendor_redistribution_rights_verified"])
        self.assertNotIn(str(self.root), json.dumps(record))
        self.assertNotIn("INERT TEST", json.dumps(record))

    def test_missing_readme_license_or_notice_denied(self):
        for required in ("README.txt", "LICENSE", "NOTICE.txt"):
            with self.subTest(required=required):
                files = dict(self.files)
                files.pop(required)
                self.write_zip(files)
                with self.assertRaises(ValueError):
                    inspect_candidate(self.archive, self.exe)

    def test_same_size_different_exe_denied(self):
        files = dict(self.files)
        files["CodeCheckerOffline.exe"] = self.exe.read_bytes().replace(b"INERT", b"iNERT")
        self.write_zip(files)
        with self.assertRaises(ValueError):
            inspect_candidate(self.archive, self.exe)

    def test_duplicate_case_collision_and_extra_executable_denied(self):
        for extra in ("readme.txt", "other.exe", "../outside.txt", "LICENSES/../README.txt",
                      "/absolute.txt", "LICENSES/CON.txt", "LICENSES/bad\\name.txt"):
            with self.subTest(extra=extra):
                self.write_zip(duplicate=extra)
                with self.assertRaises(ValueError):
                    inspect_candidate(self.archive, self.exe)

    def test_symlink_entry_denied(self):
        self.write_zip(symlink=True)
        with self.assertRaises(ValueError):
            inspect_candidate(self.archive, self.exe)

    def test_tampered_or_missing_checksums_denied(self):
        self.write_zip(corrupt_sum=True)
        with self.assertRaises(ValueError):
            inspect_candidate(self.archive, self.exe)
        self.write_zip()
        with zipfile.ZipFile(self.archive, "a") as z:
            z.writestr("LICENSES/Unexpected.txt", b"outside manifest")
        with self.assertRaises(ValueError):
            inspect_candidate(self.archive, self.exe)

    def test_invalid_utf8_notice_denied(self):
        files = dict(self.files)
        files["NOTICE.txt"] = b"INERT TEXT \xff\xfe\xff"
        self.write_zip(files)
        with self.assertRaises(ValueError):
            inspect_candidate(self.archive, self.exe)

    def test_corrupt_zip_denied(self):
        self.archive.write_bytes(b"PK\x03\x04 NOT A ZIP FILE")
        with self.assertRaises(ValueError):
            inspect_candidate(self.archive, self.exe)

    def test_cli_output_is_new_not_overwritten_and_always_blocked(self):
        self.write_zip()
        out = self.root / "private-summary.json"
        args = ["--zip", str(self.archive), "--exe", str(self.exe), "--out", str(out)]
        self.assertEqual(main(args), 0)
        content = out.read_text(encoding="utf-8")
        self.assertFalse(json.loads(content)["owner_release_approval"])
        self.assertEqual(main(args), 1)
        self.assertEqual(out.read_text(encoding="utf-8"), content)

    def test_zip_local_symlink_denied(self):
        self.write_zip()
        link = self.root / "indirect.zip"
        try:
            link.symlink_to(self.archive)
        except (OSError, NotImplementedError):
            self.skipTest("symlink unavailable")
        with self.assertRaises(Exception):
            inspect_candidate(link, self.exe)


if __name__ == "__main__":
    unittest.main()
