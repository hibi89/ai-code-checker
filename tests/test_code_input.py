from __future__ import annotations

import os
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from code_input import InputError, InputLimits, bundle_from_text, load_directory, load_single_file, load_zip


class CodeInputTests(unittest.TestCase):
    def test_credentials_are_redacted_before_bundle_is_rendered(self) -> None:
        secret = "sk_live_" + "1234567890abcdefghij"
        bundle = bundle_from_text(f'API_KEY = "{secret}"\nprint("ready")')

        rendered = bundle.render()
        self.assertNotIn(secret, rendered)
        self.assertIn("<REDACTED>", rendered)
        self.assertEqual(bundle.redaction_count, 1)
        self.assertEqual(bundle.files[0].redactions[0].line_number, 1)

    def test_unquoted_secret_assignment_is_redacted_without_hiding_env_lookup(self) -> None:
        secret = "prod_secret_value_123456789"
        bundle = bundle_from_text(
            f"API_TOKEN = {secret}\n"
            'password = os.getenv("PASSWORD")\n'
        )

        rendered = bundle.render()
        self.assertNotIn(secret, rendered)
        self.assertIn("API_TOKEN = <REDACTED>", rendered)
        self.assertIn('password = os.getenv("PASSWORD")', rendered)
        self.assertEqual(bundle.redaction_count, 1)

    def test_attribute_reference_is_preserved_while_real_token_is_redacted(self) -> None:
        google_key = "AIza" + "A" * 40
        bundle = bundle_from_text(
            "client = Client(api_key=settings.api_key)\n"
            f"API_KEY = {google_key}\n"
        )

        rendered = bundle.render()
        self.assertIn("api_key=settings.api_key", rendered)
        self.assertNotIn(google_key, rendered)
        self.assertIn("API_KEY = <REDACTED>", rendered)
        self.assertEqual(bundle.redaction_count, 1)

    def test_aws_secret_access_key_is_redacted(self) -> None:
        secret = "synthetic-aws-secret-value-123456"
        bundle = bundle_from_text(f'AWS_SECRET_ACCESS_KEY = "{secret}"\n')

        rendered = bundle.render()
        self.assertNotIn(secret, rendered)
        self.assertIn('AWS_SECRET_ACCESS_KEY = "<REDACTED>"', rendered)
        self.assertEqual(bundle.redaction_count, 1)

    def test_common_korean_personal_data_is_redacted_but_example_email_is_kept(self) -> None:
        source_text = (
            'owner = "owner@' + 'mycompany.co.kr"\n'
            + 'mobile = "010-' + '1234-5678"\n'
            + 'rrn = "900101-' + '1234567"\n'
            + 'fixture = "user@example.com"\n'
        )
        bundle = bundle_from_text(source_text)

        rendered = bundle.render()
        self.assertNotIn("owner@" + "mycompany.co.kr", rendered)
        self.assertNotIn("010-" + "1234-5678", rendered)
        self.assertNotIn("900101-" + "1234567", rendered)
        self.assertIn("user@example.com", rendered)
        self.assertEqual(bundle.redaction_count, 3)

    def test_env_file_is_excluded_without_reading_its_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".env").write_text("API_KEY=example-secret-value\n", encoding="utf-8")
            (root / "main.py").write_text("print('ok')\n", encoding="utf-8")

            bundle = load_directory(root)

        self.assertEqual([source.path for source in bundle.files], ["main.py"])
        self.assertIn(".env", bundle.excluded_paths)
        self.assertNotIn("example-secret-value", bundle.render())

    def test_env_example_credentials_are_masked_and_utf8_bom_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            google_key = "AIza" + "123456789012345678901234567890123456789"
            (root / ".env.example").write_text(
                f"GEMINI_API_KEY={google_key}\n",
                encoding="utf-8-sig",
            )
            (root / "main.py").write_bytes(b"\xef\xbb\xbfprint('ok')\r\n")

            bundle = load_directory(root)

        self.assertEqual(len(bundle.files), 2)
        self.assertNotIn(google_key, bundle.render())
        self.assertIn("<REDACTED>", bundle.render())
        self.assertNotIn("\r", bundle.render())

    def test_ignored_directories_are_not_collected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "node_modules").mkdir()
            (root / "src" / "main.py").write_text("print('ok')", encoding="utf-8")
            (root / "node_modules" / "bad.py").write_text("eval(x)", encoding="utf-8")

            bundle = load_directory(root)

        self.assertEqual([source.path for source in bundle.files], ["src/main.py"])

    def test_directory_source_replaced_after_lstat_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "main.py"
            source.write_bytes(b"pass")
            # Windows creation timestamps may share a filesystem tick.
            # Separate the physical files so the path-to-path identity
            # check has a real, observable replacement signal.
            time.sleep(0.08)
            replacement = root / "replacement.tmp"
            replacement.write_bytes(b"eval")
            actual_open = os.open
            swapped = False

            def swap_before_open(path, flags, *args, **kwargs):
                nonlocal swapped
                if Path(path) == source and not swapped:
                    os.replace(replacement, source)
                    swapped = True
                return actual_open(path, flags, *args, **kwargs)

            with patch("code_input.os.open", side_effect=swap_before_open):
                with self.assertRaisesRegex(InputError, "변경되었습니다"):
                    load_directory(root)
            self.assertTrue(swapped)

    def test_single_source_replaced_after_lstat_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "main.py"
            source.write_bytes(b"pass")
            # Windows creation timestamps may share a filesystem tick.
            # Separate the physical files so the path-to-path identity
            # check has a real, observable replacement signal.
            time.sleep(0.08)
            replacement = root / "replacement.tmp"
            replacement.write_bytes(b"eval")
            actual_open = os.open
            swapped = False

            def swap_before_open(path, flags, *args, **kwargs):
                nonlocal swapped
                if Path(path) == source and not swapped:
                    os.replace(replacement, source)
                    swapped = True
                return actual_open(path, flags, *args, **kwargs)

            with patch("code_input.os.open", side_effect=swap_before_open):
                with self.assertRaisesRegex(InputError, "변경되었습니다"):
                    load_single_file(source)
            self.assertTrue(swapped)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "named pipes require POSIX")
    def test_named_pipe_is_excluded_without_opening(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "main.py").write_text("print('ok')", encoding="utf-8")
            os.mkfifo(root / "pipe.py")

            bundle = load_directory(root)

        self.assertEqual([source.path for source in bundle.files], ["main.py"])
        self.assertIn("pipe.py", bundle.excluded_paths)
        self.assertTrue(any("일반 파일이 아니어서" in warning for warning in bundle.warnings))

    def test_zip_traversal_is_rejected_without_extracting(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive_path = root / "unsafe.zip"
            outside = root.parent / "escaped_ai_checker_test.py"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("../escaped_ai_checker_test.py", "print('bad')")

            with self.assertRaises(InputError):
                load_zip(archive_path)
            self.assertFalse(outside.exists())

    def test_zip_reads_supported_text_without_extracting(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive_path = root / "project.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("src/main.py", "print('safe')\r\n")
                archive.writestr(".env", "API_KEY=do-not-read\n")

            bundle = load_zip(archive_path)

        self.assertEqual([source.path for source in bundle.files], ["src/main.py"])
        self.assertIn(".env", bundle.excluded_paths)
        self.assertNotIn("do-not-read", bundle.render())
        self.assertNotIn("\r", bundle.render())

    def test_zip_path_with_windows_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            archive_path = Path(temp) / "unsafe.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(r"..\outside.py", "print('bad')")
            with self.assertRaises(InputError):
                load_zip(archive_path)

    def test_limits_reject_oversized_file_and_project(self) -> None:
        limits = InputLimits(max_file_bytes=8, max_total_bytes=12)
        with self.assertRaises(InputError):
            bundle_from_text("print('too long')", limits=limits)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.py").write_text("123456789", encoding="utf-8")
            with self.assertRaises(InputError):
                load_directory(root, limits)

    def test_invalid_utf8_file_is_skipped_and_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "main.py").write_text("print('ok')", encoding="utf-8")
            (root / "broken.py").write_bytes(b"\xff\xfe\xfa")
            bundle = load_directory(root)

        self.assertEqual([source.path for source in bundle.files], ["main.py"])
        self.assertTrue(any("not UTF-8 text" in warning for warning in bundle.warnings))

    def test_korean_filename_is_preserved_and_parent_path_is_rejected(self) -> None:
        bundle = bundle_from_text("print('ok')", filename="한글 파일.py")
        self.assertEqual(bundle.files[0].path, "한글 파일.py")
        with self.assertRaises(InputError):
            bundle_from_text("print('bad')", filename="../escape.py")


if __name__ == "__main__":
    unittest.main()
