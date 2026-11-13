"""Synthetic graph contract tests: no external dependency or customer source."""
from __future__ import annotations

import hashlib
import unittest

from code_input import InputError
from proofqa_p70 import correlate_findings, validate_graph

SHA = hashlib.sha256(b"fixture").hexdigest()
SOURCES = {"app.py": SHA, "widget.js": SHA, "schema.sql": SHA}
GRAPH = {
    "graph": {"graphify_version": "0.9.108", "schema_version": "1"},
    "nodes": [
        {"id": "p0", "label": "app.py", "file_type": "code", "source_file": "app.py", "source_location": "L1"},
        {"id": "p1", "label": "risk_one()", "file_type": "code", "source_file": "app.py", "source_location": "L2"},
        {"id": "p2", "label": "risk_two()", "file_type": "code", "source_file": "app.py", "source_location": "L4"},
        {"id": "j", "label": "handle()", "file_type": "code", "source_file": "widget.js", "source_location": "L1"},
        {"id": "s", "label": "audit", "file_type": "code", "source_file": "schema.sql", "source_location": "L1"},
    ],
    "links": [
        {"source": "p0", "target": "p1", "relation": "contains", "confidence": "EXTRACTED"},
        {"source": "p0", "target": "p2", "relation": "contains", "confidence": "EXTRACTED"},
    ],
}
CASE = {
    "contract": "proofqa.p50.v1",
    "source": {"sha256": "a" * 64},
    "findings": [
        {"rule_id": "PY-DYNAMIC-EXEC", "source_path": "app.py", "line": 3,
         "status": "NEEDS_VALIDATION", "confirmed_vulnerability": False},
        {"rule_id": "PY-DYNAMIC-EXEC", "source_path": "app.py", "line": 5,
         "status": "NEEDS_VALIDATION", "confirmed_vulnerability": False},
    ],
}


class ProofQaGraphTests(unittest.TestCase):
    def test_three_languages_and_two_static_findings_correlated_without_confirmation(self):
        nodes, links, langs = validate_graph(GRAPH, SOURCES)
        self.assertEqual(set(langs), {".py", ".js", ".sql"})
        self.assertTrue(all(langs.values()))
        self.assertEqual(len(links), 2)
        result = correlate_findings(CASE, GRAPH, SOURCES)
        self.assertEqual(result["summary"]["source_linked"], 2)
        self.assertEqual(result["summary"]["impact_linked"], 2)
        self.assertEqual(result["summary"]["confirmed_security_findings"], 0)
        self.assertTrue(all(row["confidence"] == "FILE_SCOPE_APPROXIMATE"
                            for row in result["findings_correlated"]))

    def test_missing_graph_filename_not_invented(self):
        graph = {**GRAPH, "nodes": [n for n in GRAPH["nodes"] if n["source_file"] != "widget.js"]}
        _, _, langs = validate_graph(graph, SOURCES)
        self.assertEqual(langs[".js"], 0)

    def test_graph_duplicate_node_rejected(self):
        graph = {**GRAPH, "nodes": GRAPH["nodes"] + [GRAPH["nodes"][0]]}
        with self.assertRaises(InputError):
            validate_graph(graph, SOURCES)

    def test_dangling_link_rejected(self):
        graph = {**GRAPH, "links": [{"source": "p0", "target": "fake"}]}
        with self.assertRaises(InputError):
            validate_graph(graph, SOURCES)

    def test_wrong_pinned_version_rejected(self):
        graph = {**GRAPH, "graph": {"graphify_version": "0.9.111"}}
        with self.assertRaises(InputError):
            validate_graph(graph, SOURCES)

    def test_fake_confirmed_findings_rejected(self):
        case = {**CASE, "findings": [{**CASE["findings"][0], "confirmed_vulnerability": True}]}
        with self.assertRaises(InputError):
            correlate_findings(case, GRAPH, SOURCES)

    def test_forged_unverified_source_ref_fails_closed(self):
        graph = {**GRAPH, "nodes": [
            {**n, "source_file": "../customer/app.py"} if n["id"] == "p1" else n
            for n in GRAPH["nodes"]
        ]}
        nodes, _, _ = validate_graph(graph, SOURCES)
        self.assertFalse(any(n["id"] == "p1" for n in nodes))

    def test_outside_zip_filename_is_not_accepted(self):
        case = {**CASE, "findings": [{**CASE["findings"][0], "source_path": "other.py"}]}
        with self.assertRaises(InputError):
            correlate_findings(case, GRAPH, SOURCES)


if __name__ == "__main__":
    unittest.main()
