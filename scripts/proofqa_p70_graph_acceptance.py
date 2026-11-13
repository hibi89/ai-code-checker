"""Real Graphify 0.9.108 P70 synthetic AST execution and source provenance gate.

Only generated sample code is passed to Graphify. No customer inputs, auth,
external LLM backends, Graphify cloud plugins, or customer executable scripts.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from proofqa_p50 import run_p50, verify_delivery
from proofqa_p70 import (
    GRAPHIFY_VERSION, correlate_findings, read_json_bounded, sha256,
)

FIXTURES = {
    "app.py": (
        "def risky_one(value):\n"
        "    return eval(value)\n"
        "\n"
        "def risky_two(value):\n"
        "    return eval(value)\n"
    ),
    "widget.js": (
        "function saveDraft(state) {\n"
        "  return { count: state.count + 1 };\n"
        "}\n"
        "function render() { return saveDraft({ count: 1 }); }\n"
    ),
    "schema.sql": (
        "CREATE TABLE documents (id INTEGER PRIMARY KEY, title TEXT);\n"
        "CREATE TABLE audit (id INTEGER PRIMARY KEY, document_id INTEGER,\n"
        "  FOREIGN KEY (document_id) REFERENCES documents(id));\n"
    ),
}


def evaluate() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="proofqa-graph-p70-") as temp:
        root = Path(temp)
        sources = root / "synthetic-code"
        sources.mkdir()
        expected: dict[str, str] = {}
        for name, content in FIXTURES.items():
            item = sources / name
            item.write_text(content, encoding="utf-8", newline="\n")
            expected[name] = sha256(item.read_bytes())

        archive = root / "synthetic.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
            for name in sorted(FIXTURES):
                output.write(sources / name, arcname=name)
        zip_digest_before = sha256(archive.read_bytes())
        p50_dir, p50_status = run_p50(archive, root / "p50-output")
        assert verify_delivery(p50_dir)
        case = read_json_bounded(p50_dir / "case.json")
        if case["source"]["sha256"] != zip_digest_before:
            raise AssertionError("P50 subject hash is not exact ZIP SHA256")
        findings = [f for f in case["findings"] if f["source_path"] == "app.py"]
        if len(findings) < 2:
            raise AssertionError(f"Two actual Code Checker findings required, got {len(findings)}")

        # Verify the exact archived source bytes equal independently recorded
        # fixture source files before graphifying them (no customer ZIP extraction).
        with zipfile.ZipFile(archive, "r") as z:
            for name, digest in expected.items():
                if sha256(z.read(name)) != digest:
                    raise AssertionError(f"Source mismatch: {name}")
        # No user/API credential variables are forwarded to Graphify.
        env_keys = ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG", "LC_ALL", "LD_LIBRARY_PATH")
        env = {k: os.environ[k] for k in env_keys if k in os.environ}
        env["HOME"] = str(root)
        env["GRAPHIFY_BACKEND"] = "none"
        env["GRAPHIFY_QUERY_LOG_DISABLE"] = "1"
        env["PYTHONUTF8"] = "1"
        graph_output = root / "graph-results"
        command = [
            "graphify", "extract", str(sources), "--code-only",
            "--no-cluster", "--max-workers", "1",
            "--out", str(graph_output),
        ]
        process = subprocess.run(
            command, env=env, cwd=root, text=True, encoding="utf-8",
            errors="replace", capture_output=True, timeout=240, check=False,
        )
        if process.returncode:
            raise RuntimeError(
                "Pinned Graphify extraction failed (synthetic fixture only) rc="
                + str(process.returncode) + "\n"
                + process.stderr[-2600:] + "\n" + process.stdout[-1200:]
            )
        graph_path = graph_output / "graphify-out" / "graph.json"
        if not graph_path.is_file():
            raise AssertionError(
                "Graphify returned no graph.json; outputs="
                + str([p.name for p in graph_output.rglob("*")][:35])
            )
        graph = read_json_bounded(graph_path)
        correlation = correlate_findings(case, graph, expected)
        ast = correlation["covered_ast_nodes"]
        if any(ast.get(lang, 0) < 1 for lang in (".py", ".js", ".sql")):
            raise AssertionError(f"Graphify AST language coverage not reached: {ast}")
        summary = correlation["summary"]
        if summary["source_linked"] < 2 or summary["impact_linked"] < 2:
            raise AssertionError("Two Code Checker candidates must be linked to real Graphify edges.")
        if correlation["release_state"] != "HOLD" or summary["confirmed_security_findings"]:
            raise AssertionError("Unverified security candidates must never become CONFIRMED.")
        if sha256(archive.read_bytes()) != zip_digest_before:
            raise AssertionError("Synthetic source archive changed during Graphify.")
        return {
            "contract": "proofqa.p70.graph.acceptance.v1",
            "status": "PASS",
            "tools": {"graphify_package": "graphifyy", "version": GRAPHIFY_VERSION,
                      "backend": "none", "mode": "code-only", "sql_extra": True},
            "sha256": {"source_archive": zip_digest_before, "graph_json": sha256(graph_path.read_bytes()),
                       "p50_case": sha256((p50_dir / "case.json").read_bytes())},
            "static_scan_status": p50_status,
            "source_files": len(expected),
            "ast_nodes": ast,
            "finding_correlation": summary,
            "correlation_evidence": correlation["findings_correlated"][:4],
            "security_claim": "NOT_A_SECURITY_CERTIFICATION",
            "release_state": "HOLD",
        }


if __name__ == "__main__":
    try:
        result = evaluate()
    except Exception as exc:
        print("PROOFQA_P70_GRAPH_FAIL:", exc, file=sys.stderr)
        raise
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
