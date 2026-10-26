"""Fixed synthetic labeled smoke corpus for deterministic offline rule accuracy.

A case label is a specific (rule_id, source_line) observation; the metrics are
NOT true precision/recall on arbitrary real projects. JS/TS are explicitly
reported as unsupported for language-specific accuracy, not scored as clean.
Never executes the scanned program, uploads code, or calls an AI API.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from offline_core import scan_text
from offline_report import build_report


@dataclass(frozen=True)
class Case:
    case_id: str
    code: str
    expected: tuple[tuple[str, int], ...]
    filename: str = "synthetic.py"


PYTHON_CASES = (
    Case("dynamic-eval", "eval(value)\n", (("PY-DYNAMIC-EXEC", 1),)),
    Case("dynamic-exec", "exec(source)\n", (("PY-DYNAMIC-EXEC", 1),)),
    Case("subprocess-direct", "import subprocess\nsubprocess.run(cmd, shell=True)\n", (("PY-SHELL", 2),)),
    Case("subprocess-aliased", "import subprocess as sp\nsp.Popen(cmd, shell=True)\n", (("PY-SHELL", 2),)),
    Case("subprocess-from-import", "from subprocess import check_output as capture\ncapture(cmd, shell=True)\n", (("PY-SHELL", 2),)),
    Case("subprocess-other-run", "service.run(cmd, shell=True)\n", ()),
    Case("subprocess-other-call", "service.call(cmd, shell=True)\n", ()),
    Case("subprocess-no-shell", "import subprocess\nsubprocess.run(cmd, shell=False)\n", ()),
    Case("pickle-direct", "import pickle\npickle.loads(data)\n", (("PY-PICKLE", 2),)),
    Case("pickle-aliased", "import pickle as codec\ncodec.load(stream)\n", (("PY-PICKLE", 2),)),
    Case("pickle-from-import", "from pickle import loads as decode\ndecode(data)\n", (("PY-PICKLE", 2),)),
    Case("pickle-unrelated", "converter.loads(data)\n", ()),
    Case("sql-fstring", 'conn.execute(f"SELECT * FROM records WHERE id={uid}")\n', (("PY-SQL-CONCAT", 1),)),
    Case("sql-plus", 'cursor.execute("UPDATE users SET x=" + value)\n', (("PY-SQL-CONCAT", 1),)),
    Case("sql-param", 'conn.execute("SELECT * FROM records WHERE id=?", (uid,))\n', ()),
    Case("sql-nonquery", 'printer.execute(f"render {name}")\n', ()),
    Case("tls-requests", "import requests\nrequests.get(url, verify=False)\n", (("GEN-TLS-VERIFY", 2),)),
    Case("tls-from-import", "from requests import post as send\nsend(url, verify=False)\n", (("GEN-TLS-VERIFY", 2),)),
    Case("tls-comment", "# requests.get(url, verify=False)\n", ()),
    Case("tls-string", 'print("verify=False")\n', ()),
    Case("tls-assignment", "verify = False\n", ()),
    Case("tls-other-client", "client.get(url, verify=False)\n", ()),
    Case("tls-valid", "import requests\nrequests.get(url, verify=True)\n", ()),
    Case("syntax-broken", "def broken(:\n    pass\n", (("PY-SYNTAX", 1),)),
    Case("safe-code", "print('synthetic')\n", ()),
    # Intentional known misses: unsupported dynamic indirection/dataflow.
    Case("dynamic-getattr-known-miss", 'getattr(__import__("builtins"), "eval")(value)\n', (("PY-DYNAMIC-EXEC", 1),)),
    Case("shell-dynamic-import-known-miss", '__import__("subprocess").run(cmd, shell=True)\n', (("PY-SHELL", 1),)),
    Case("sql-composed-variable-known-miss", 'query = f"SELECT * FROM t WHERE x={v}"\nconn.execute(query)\n', (("PY-SQL-CONCAT", 2),)),
)

JS_TS_LIMITED = (
    Case("js-generic-limited", 'console.log("synthetic");\n', (), "synthetic.js"),
    Case("ts-generic-limited", "const count: number = 1;\n", (), "synthetic.ts"),
)


def evaluate() -> dict:
    tp = fp = fn = 0
    per_case = []
    per_rule: dict[str, dict[str, int]] = {}
    for case in PYTHON_CASES:
        scan = scan_text(case.code, filename=case.filename)
        report = build_report(scan)
        actual = {(row.rule_id, row.finding.start_line) for row in report.findings}
        expected = set(case.expected)
        valid = actual & expected
        unexpected = actual - expected
        missed = expected - actual
        tp += len(valid)
        fp += len(unexpected)
        fn += len(missed)
        for field, items in (("tp", valid), ("fp", unexpected), ("fn", missed)):
            for rid, _ in items:
                per_rule.setdefault(rid, {"tp": 0, "fp": 0, "fn": 0})[field] += 1
        per_case.append({
            "id": case.case_id, "tp": len(valid), "fp": len(unexpected),
            "fn": len(missed), "status": scan.status,
        })
        if report.validation_issues:
            raise ValueError("Synthetic source citation validation failed")
    limited_count = 0
    for case in JS_TS_LIMITED:
        scan = scan_text(case.code, filename=case.filename)
        if scan.status != "partial" or scan.counts["limited"] != 1:
            raise AssertionError("JS/TS must stay explicitly limited, not clean")
        limited_count += 1
    return {
        "format": "synthetic_fixed_corpus_rule_level_v1",
        "python_cases": len(PYTHON_CASES),
        "js_ts_limited_cases_excluded_from_metric": limited_count,
        "tp": tp, "fp": fp, "fn": fn,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "by_rule": dict(sorted(per_rule.items())),
        "cases": per_case,
        "real_world_accuracy": "UNVERIFIED",
        "js_ts_parser_coverage": "UNVERIFIED_NOT_IMPLEMENTED",
        "customer_release_ready": False,
    }


def main() -> int:
    result = evaluate()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
