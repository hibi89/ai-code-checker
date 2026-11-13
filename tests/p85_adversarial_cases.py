"""P85 dedicated adversarial suite: no live customer code, no remote IO.

These are *negative contract tests* and report-generation tests; not 15 actual
attack exploits against a deployed customer system. Run in P85 locked-deps CI.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from code_input import InputError
from proofqa_p85 import compose, _pdf_bytes
from proofqa_p85_verify import verify_package

S = lambda t: hashlib.sha256(t.encode()).hexdigest()
SCHEMA = "schemas/proofqa_p85_report.schema.json"

def good_graph():
    return {
        "contract": "proofqa.p70.graph.acceptance.v1",
        "status": "PASS",
        "release_state": "HOLD",
        "security_claim": "NOT_A_SECURITY_CERTIFICATION",
        "tools": {"graphify_package": "graphifyy", "version": "0.9.108",
                  "backend": "none", "mode": "code-only", "sql_extra": True},
        "sha256": {"source_archive": S("real-synthetic-zip"),
                   "graph_json": S("real-synthetic-graph"),
                   "p50_case": S("real-synthetic-p50-case")},
        "source_files": 3,
        "static_scan_status": "partial",
        "ast_nodes": {".py": 3, ".js": 3, ".sql": 2},
        "finding_correlation": {"findings_total": 2, "source_linked": 2,
                                "impact_linked": 2, "confirmed_security_findings": 0},
        "correlation_evidence": [
            {"finding_index": i, "source_path": "app.py", "line": 2 + i * 3,
             "source_sha256": S("app.py synthetic bytes"),
             "graph_status": "SOURCE_FILE_CORRELATED",
             "confidence": "FILE_SCOPE_APPROXIMATE",
             "impact_edges": [
                 {"source": "app", "target": "app_risky",
                  "relation": "contains", "confidence": "EXTRACTED"}
             ]}
            for i in range(2)
        ],
    }


def good_browser():
    return {
        "contract": "proofqa.p70.browser.acceptance.v1",
        "status": "PASS", "release_state": "HOLD",
        "agent_browser_version": "0.43.0",
        "scope": "synthetic 127.0.0.1 only",
        "customer_site_tested": False,
        "payment_or_destructive_actions": False,
        "snapshot_confirmed": True,
        "persist_and_reopen_verified": True,
        "http_requests_checked": [["GET", "/api/ok", 200],
                                  ["GET", "/api/fail", 500],
                                  ["POST", "/api/save", 200],
                                  ["GET", "/api/reopen", 200]],
    }


class P85ContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="proofqa-p85-negative-")
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.target = compose(good_graph(), good_browser(), self.home)
        self.assertTrue(self.target.exists())

    def verify(self):
        return verify_package(self.target, SCHEMA)

    def assert_blocked(self):
        with self.assertRaises((InputError, ValueError)):
            self.verify()

    def rehash(self, filename):
        manifest_file = self.target / "manifest.json"
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        manifest["files"][filename] = hashlib.sha256((self.target / filename).read_bytes()).hexdigest()
        manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def edit(self, filename, edit_fn):
        path = self.target / filename
        doc = json.loads(path.read_text(encoding="utf-8"))
        edit_fn(doc)
        path.write_text(json.dumps(doc, sort_keys=True, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.rehash(filename)

    def test_00_valid_synthetic_report_contract_verified(self):
        result = self.verify()
        self.assertTrue(result["verified"])
        self.assertEqual(result["findings"]["confirmed"], 0)
        self.assertEqual(result["findings"]["needs_validation"], 2)
        self.assertEqual(result["coverage"]["not_covered"], 6)
        self.assertEqual(result["release_state"], "HOLD")

    def test_01_modified_html_without_new_manifest_denied(self):
        (self.target / "report.html").write_text("forged", encoding="utf-8")
        self.assert_blocked()

    def test_02_signed_fake_release_state_denied(self):
        self.edit("report.json", lambda d: d.update(release_state="GO", customer_accepted=True))
        self.assert_blocked()

    def test_03_changed_source_digest_denied_even_with_rehash(self):
        self.edit("audit.json", lambda d: d.update(subject_sha256=S("new-source")))
        self.assert_blocked()

    def test_04_missing_evidence_ref_denied(self):
        self.edit("findings.json", lambda d: d["findings"][0].update(evidence_refs=["EV-UNKNOWN"]))
        self.assert_blocked()

    def test_05_fake_confirmed_vulnerability_denied(self):
        self.edit("findings.json", lambda d: d["findings"][0].update(status="CONFIRMED", severity="HIGH"))
        self.assert_blocked()

    def test_06_severity_on_unvalidated_candidate_denied(self):
        self.edit("findings.json", lambda d: d["findings"][0].update(severity="CRITICAL"))
        self.assert_blocked()

    def test_07_rejected_without_independent_disproof_denied(self):
        self.edit("findings.json", lambda d: d["findings"][0].update(status="REJECTED"))
        self.assert_blocked()

    def test_08_duplicate_finding_id_denied(self):
        self.edit("findings.json", lambda d: d["findings"][1].update(id="PQ85-001"))
        self.assert_blocked()

    def test_09_finding_wrong_source_line_fingerprint_denied(self):
        self.edit("findings.json", lambda d: d["findings"][0].update(line=999))
        self.assert_blocked()

    def test_10_finding_source_hash_record_mismatch_denied(self):
        self.edit("findings.json", lambda d: d["findings"][0].update(source_sha256=S("changed")))
        self.assert_blocked()

    def test_11_coverage_marked_customer_complete_denied(self):
        self.edit("coverage-ledger.json", lambda d: d["units"][-1].update(status="COMPLETED", reviewed_customer=True))
        self.assert_blocked()

    def test_12_fake_final_counts_denied(self):
        self.edit("report.json", lambda d: d["counts"].update(confirmed=2, needs_validation=0))
        self.assert_blocked()

    def test_13_fake_fresh_agent_verification_denied(self):
        self.edit("audit.json", lambda d: d.update(independent_human_security_verification="PASS"))
        self.assert_blocked()

    def test_14_six_stage_coverage_not_complete_denied(self):
        self.edit("audit.json", lambda d: d["phases"].pop())
        self.assert_blocked()

    def test_15_injected_html_script_denied_even_with_rehash(self):
        page = self.target / "report.html"
        page.write_text(page.read_text(encoding="utf-8") + "<script>alert(1)</script>", encoding="utf-8")
        self.rehash("report.html")
        self.assert_blocked()

    def test_16_html_report_number_mismatch_denied(self):
        page = self.target / "report.html"
        page.write_text(page.read_text(encoding="utf-8").replace("FINDINGS: total=2", "FINDINGS: total=3"), encoding="utf-8")
        self.rehash("report.html")
        self.assert_blocked()

    def test_17_pdf_report_does_not_match_json_denied(self):
        (self.target / "report.pdf").write_bytes(_pdf_bytes(["NOT THE REPORTED FINDINGS"]))
        self.rehash("report.pdf")
        self.assert_blocked()

    def test_18_corrupt_pdf_denied_even_with_sha_update(self):
        (self.target / "report.pdf").write_bytes(b"%PDF-1.7\nfake")
        self.rehash("report.pdf")
        self.assert_blocked()

    def test_19_extra_customer_source_file_denied(self):
        (self.target / "secret.env").write_text("should-not-be-bundled")
        self.assert_blocked()

    def test_20_symlink_report_file_denied(self):
        file = self.target / "report.html"
        file.unlink()
        try:
            file.symlink_to(self.target / "report.json")
        except (OSError, NotImplementedError):
            self.skipTest("Host does not allow symlinks; explicit NOT_TESTED")
        self.assert_blocked()

    def test_21_duplicate_output_directory_denied(self):
        with self.assertRaises(FileExistsError):
            compose(good_graph(), good_browser(), self.home)

    def test_22_graph_inferred_is_not_observed(self):
        graph = good_graph()
        graph["correlation_evidence"][0]["impact_edges"][0]["confidence"] = "INFERRED"
        with self.assertRaises(InputError):
            compose(graph, good_browser(), self.home / "other")

    def test_23_graph_unpinned_version_denied(self):
        graph = good_graph()
        graph["tools"]["version"] = "0.9.0"
        with self.assertRaises(InputError):
            compose(graph, good_browser(), self.home / "other")

    def test_24_browser_unobserved_500_denied(self):
        browser = good_browser()
        browser["http_requests_checked"][1][2] = 200
        with self.assertRaises(InputError):
            compose(good_graph(), browser, self.home / "other")

    def test_25_browser_customer_site_unapproved_denied(self):
        browser = good_browser()
        browser["customer_site_tested"] = True
        with self.assertRaises(InputError):
            compose(good_graph(), browser, self.home / "other")

    def test_26_report_schema_rejects_extra_permission_field(self):
        self.edit("report.json", lambda d: d.update(administrator_approved=True))
        self.assert_blocked()

    def test_27_bogus_trust_boundary_os_sandbox_denied(self):
        self.edit("audit.json", lambda d: d["architecture"].update(os_enforced_egress_sandbox=True))
        self.assert_blocked()

    def test_28_bogus_input_sha_on_manifest_denied(self):
        m = self.target / "manifest.json"
        d = json.loads(m.read_text())
        d["input_sha256"] = S("stale")
        m.write_text(json.dumps(d), encoding="utf-8")
        self.assert_blocked()

    def test_29_evidence_record_duplicate_denied(self):
        self.edit("audit.json", lambda d: d["evidence"].append(d["evidence"][0]))
        self.assert_blocked()

    def test_30_pdf_exceeds_bounded_size_denied(self):
        pdf = self.target / "report.pdf"
        pdf.write_bytes(pdf.read_bytes() + b"0" * (1024 * 1024))
        self.rehash("report.pdf")
        self.assert_blocked()


if __name__ == "__main__":
    unittest.main()
