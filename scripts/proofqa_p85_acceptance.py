"""P85 exact real-source synthetic end-to-end report generator and verifier.

No customer input accepted. Real Graphify 0.9.108 and agent-browser 0.43.0
are called using their P70 synthetic fixtures; reports stay local ephemeral.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from proofqa_p85 import compose
from proofqa_p85_verify import verify_package
from scripts.proofqa_p70_graph_acceptance import evaluate as evaluate_graph
from scripts.proofqa_p70_browser_acceptance import evaluate as evaluate_browser

SCHEMA = "schemas/proofqa_p85_report.schema.json"


def evaluate() -> dict[str, object]:
    graph = evaluate_graph()
    browser = evaluate_browser()
    with tempfile.TemporaryDirectory(prefix="proofqa-p85-live-synthetic-") as scratch:
        output = compose(graph, browser, scratch)
        command = [
            sys.executable, "-m", "proofqa_p85_verify", str(output),
            "--schema", SCHEMA,
        ]
        # Independent OS process: only hashed artifacts + own schema, without
        # access to the in-memory P85 producer's findings or decisions.
        result = subprocess.run(
            command, cwd=Path.cwd(), env=dict(os.environ), capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=60, check=False,
        )
        if result.returncode:
            raise RuntimeError(
                "P85 SEPARATE-PROCESS VERIFY FAIL: "
                + result.stdout[-2000:] + "\n" + result.stderr[-2000:]
            )
        verified = json.loads(result.stdout.strip())
        second_pass = verify_package(output, SCHEMA)
        if verified != second_pass:
            raise AssertionError("Local verifier and fresh read-only verifier process disagree")
        if verified["findings"]["needs_validation"] < 2 or verified["findings"]["confirmed"] != 0:
            raise AssertionError("Synthetic static findings cannot become security CONFIRMED")
        if verified["coverage"]["not_covered"] < 6:
            raise AssertionError("Unassessed real-world scope was concealed")
        pdf_file = output / "report.pdf"
        if pdf_file.stat().st_size < 800 or pdf_file.stat().st_size > 1024 * 1024:
            raise AssertionError("Real PDF file size is invalid")
        # Programmatically render the page, not only parse text.
        import fitz
        with fitz.open(pdf_file) as pdf:
            page = pdf.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
            if pix.width < 800 or pix.height < 1000 or not pix.samples:
                raise AssertionError("PDF visual raster generation failed")
            raster = {
                "width": pix.width, "height": pix.height,
                "pixels": pix.width * pix.height,
                "render": "PASS_AUTOMATED_ONLY",
            }
        return {
            "contract": "proofqa.p85.synthetic.acceptance.v1",
            "status": "PASS",
            "tools": {"graphify": "0.9.108", "agent_browser": "0.43.0",
                      "pypdf": "real_pdf_parse", "fitz": "real_pdf_raster"},
            "real_graphify_ast": graph["ast_nodes"],
            "static_graph_linked_findings": graph["finding_correlation"]["source_linked"],
            "real_chromium_http": browser["http_requests_checked"],
            "verified_report": verified,
            "pdf_raster": raster,
            "fresh_independent_security_agent": "NOT_RUN",
            "human_pdf_visual_review": "NOT_RUN",
            "authorized_customer_website": "NOT_RUN",
            "release_state": "HOLD",
        }


if __name__ == "__main__":
    try:
        result = evaluate()
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    except Exception as exc:
        print("P85_SYNTHETIC_ACCEPTANCE_FAIL:", exc, file=sys.stderr)
        raise
