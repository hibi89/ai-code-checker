"""Synthetic-only PROOFQA AX P50 integration/adversarial tests."""
from __future__ import annotations

import json
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from code_input import InputError
from proofqa_p50 import run_p50, verify_delivery, CONTRACT


def _zip(path: Path, members: dict[str, str], compression=zipfile.ZIP_DEFLATED) -> None:
    with zipfile.ZipFile(path, "w", compression=compression) as archive:
        for name, data in members.items():
            archive.writestr(name, data)


class ProofQaP50Tests(unittest.TestCase):
    def test_real_code_checker_adapter_writes_json_html_and_manifest_without_source_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "project.zip"
            _zip(source, {"src/app.py": "x = 1\neval(input('name'))\n"})
            before = source.read_bytes()
            folder, status = run_p50(source, root / "output")
            self.assertIn(status, ("complete", "partial"))
            self.assertEqual(before, source.read_bytes())
            self.assertTrue(verify_delivery(folder))
            case = json.loads((folder / "case.json").read_text(encoding="utf-8"))
            self.assertEqual(case["contract"], CONTRACT)
            self.assertEqual(case["source"]["type"], "local-zip")
            self.assertFalse(case["adapter"]["network"])
            self.assertFalse(case["adapter"]["source_execution"])
            self.assertEqual(case["adapter"]["graph"], "NOT_RUN")
            self.assertEqual(case["delivery"]["release_state"], "HOLD")
            self.assertTrue(any(f["source_path"] == "src/app.py" for f in case["findings"]))
            self.assertTrue(all(f["status"] == "NEEDS_VALIDATION" for f in case["findings"]))
            html = (folder / "report.html").read_text(encoding="utf-8")
            self.assertIn("Content-Security-Policy", html)
            self.assertIn(case["source"]["sha256"], html)
            with self.assertRaises(FileExistsError):
                run_p50(source, root / "output")
            self.assertEqual(before, source.read_bytes())

    def test_zip_slip_denied_with_no_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "evil.zip"
            _zip(source, {"../escape.py": "print('oops')\n"})
            with self.assertRaises(InputError):
                run_p50(source, root / "output")
            self.assertFalse((root / "output").exists())

    def test_casefold_duplicate_path_denied_with_no_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "dup.zip"
            _zip(source, {"a.py": "print('a')\n", "A.py": "print('b')\n"})
            with self.assertRaises(InputError):
                run_p50(source, root / "output")
            self.assertFalse((root / "output").exists())

    def test_symlink_zip_member_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "link.zip"
            link = zipfile.ZipInfo("link.py")
            link.create_system = 3
            link.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(link, "/etc/passwd")
            with self.assertRaises(InputError):
                run_p50(source, root / "output")

    def test_decompression_ratio_bomb_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "bomb.zip"
            _zip(source, {"bomb.py": "#" * 700000})
            with self.assertRaises(InputError):
                run_p50(source, root / "output")

    def test_original_mutation_during_scan_denied_before_any_publish(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "project.zip"
            _zip(source, {"app.py": "print('ok')\n"})
            import proofqa_p50
            original_scan = proofqa_p50.scan_path

            def mutating_scan(src):
                result = original_scan(src)
                with zipfile.ZipFile(src, "a") as archive:
                    archive.writestr("added.py", "print('bad')\n")
                return result

            with patch("proofqa_p50.scan_path", side_effect=mutating_scan):
                with self.assertRaises(InputError):
                    run_p50(source, root / "output")
            self.assertFalse((root / "output").exists())

    def test_manifest_change_fails_independent_verifier(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "project.zip"
            _zip(source, {"app.py": "print('ok')\n"})
            folder, _ = run_p50(source, root / "output")
            with (folder / "report.html").open("ab") as file:
                file.write(b"modified")
            with self.assertRaises(InputError):
                verify_delivery(folder)

    def test_no_source_upload_and_unknown_scans_never_confirmed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "unknown.zip"
            _zip(source, {"module.rs": "fn main() {}\n"})
            folder, status = run_p50(source, root / "output")
            self.assertEqual(status, "partial")
            case = json.loads((folder / "case.json").read_text(encoding="utf-8"))
            self.assertTrue(all(not f["confirmed_vulnerability"] for f in case["findings"]))
            self.assertNotEqual(case["scope"]["status"], "secure")

    def test_bounded_dev_subprocess_does_not_execute_customer_python(self):
        from scripts.proofqa_p50_dev_runner import run_dev_process
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "customer.zip"
            marker = root / "SHOULD_NOT_RUN"
            malicious = "from pathlib import Path\\nPath(" + repr(str(marker)) + ").write_text('executed')\\n"
            _zip(source, {"app.py": malicious})
            rc = run_dev_process(source, root / "out")
            self.assertIn(rc, (0, 3))
            self.assertFalse(marker.exists(), "scanned code must never execute")
            self.assertEqual(len(list((root / "out").glob("proofqa-*"))), 1)


if __name__ == "__main__":
    unittest.main()
