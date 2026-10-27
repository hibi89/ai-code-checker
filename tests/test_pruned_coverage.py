"""Phase2 synthetic coverage truthfulness tests; do not read pruned code."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from code_input import InputError, InputLimits
from desktop_core import ScanRequest, inspect_input, run_scan
from offline_core import scan_path
from offline_coverage import list_pruned_subtrees
from offline_report import build_report, render_html, render_markdown


class PrunedSubtreeCoverageTests(unittest.TestCase):
    def test_ignored_nested_subtrees_force_partial_and_are_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            (root / "main.py").write_text("print('safe')\n", encoding="utf-8")
            ignored = root / ".git"
            ignored.mkdir()
            (ignored / "secret.py").write_text("password='synthetic-should-never-appear'\n", encoding="utf-8")
            nested = root / "src" / "node_modules"
            nested.mkdir(parents=True)
            (nested / "file.py").write_text("eval('do-not-evaluate')\n", encoding="utf-8")
            request = ScanRequest("path", source=str(root))
            preview = inspect_input(request)
            scan = scan_path(root)
            report = build_report(scan)
            self.assertEqual(preview.files, 1)
            self.assertEqual(len(preview.pruned_subtrees), 2)
            self.assertIn("하위 탐색 제외 폴더", preview.display())
            self.assertIn("src/node_modules/", preview.display())
            self.assertNotIn("synthetic-should-never-appear", preview.display())
            self.assertEqual(scan.counts["enumerated"], 1)
            self.assertEqual(scan.counts["analyzed"], 1)
            self.assertEqual(scan.counts["excluded"], 0)
            self.assertEqual(scan.counts["pruned_subtrees"], 2)
            self.assertEqual(scan.status, "partial")
            self.assertEqual(report.status, "partial")
            self.assertEqual(set(scan.pruned_subtrees), {".git/", "src/node_modules/"})
            self.assertNotIn("synthetic-should-never-appear", str(scan.summary()))
            html = render_html(report)
            markdown = render_markdown(report)
            self.assertIn("src/node_modules/", html)
            self.assertIn("내부 파일 수 미확인", html)
            self.assertIn("하위 탐색 생략 폴더", markdown)
            self.assertNotIn("synthetic-should-never-appear", html)
            self.assertNotIn("eval('do-not-evaluate')", markdown)
            with tempfile.TemporaryDirectory() as output:
                result = run_scan(request, output, "pruned")
                self.assertEqual(result.status, "partial")
                self.assertEqual(result.pruned_subtrees, 2)
                self.assertIn("내부 파일 수는 미확인", result.display())

    def test_directory_without_pruned_subtrees_can_be_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "src").mkdir()
            (Path(tmp) / "src" / "good.py").write_text("print(1)\n", encoding="utf-8")
            scan = scan_path(tmp)
            self.assertEqual(scan.pruned_subtrees, ())
            self.assertEqual(scan.status, "complete")
            self.assertEqual(scan.counts["analyzed"], 1)

    def test_depth_pruning_is_reported_not_silently_counted_as_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "a"
            nested.mkdir()
            deeper = nested / "b"
            deeper.mkdir()
            (deeper / "file.py").write_text("eval('not-read')\n", encoding="utf-8")
            limited = InputLimits(max_depth=1, max_files=5)
            paths = list_pruned_subtrees(root, limits=limited)
            self.assertEqual(paths, ("a/b/",))

    def test_metadata_walk_limit_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for item in ("a", "b"):
                (root / item).mkdir()
            with self.assertRaises(InputError):
                list_pruned_subtrees(root, limits=InputLimits(), max_visited_directories=1)


if __name__ == "__main__":
    unittest.main()
