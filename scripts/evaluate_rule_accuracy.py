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
    Case("shell-shadow-module", "import subprocess as sp\nsp = fake\nsp.run(cmd, shell=True)\n", ()),
    Case("shell-before-shadow", "import subprocess as sp\nsp.run(cmd, shell=True)\nsp = fake\nsp.run(cmd, shell=True)\n", (("PY-SHELL", 2),)),
    Case("shell-from-shadow", "from subprocess import run as invoke\ninvoke = fake\ninvoke(cmd, shell=True)\n", ()),
    Case("shell-late-import", "subprocess.run(cmd, shell=True)\nimport subprocess\n", ()),
    Case("shell-function-param", "import subprocess as sp\ndef f(sp):\n    sp.run(cmd, shell=True)\n", ()),
    Case("shell-function-late-local", "import subprocess as sp\ndef f():\n    sp.run(cmd, shell=True)\n    sp = fake\n", ()),
    Case("shell-function-real", "import subprocess as sp\ndef f():\n    sp.run(cmd, shell=True)\n", (("PY-SHELL", 3),)),
    Case("shell-conditional-shadow", "import subprocess as sp\nif cond:\n    sp = fake\nsp.run(cmd, shell=True)\n", ()),
    Case("shell-class-shadow", "import subprocess as sp\nclass C:\n    sp = fake\n    sp.run(cmd, shell=True)\n", ()),
    Case("shell-comprehension-shadow", "import subprocess as sp\n[sp.run(cmd, shell=True) for sp in services]\n", ()),
    Case("pickle-module-shadow", "import pickle as codec\ncodec = fake\ncodec.loads(data)\n", ()),
    Case("pickle-function-shadow", "from pickle import loads as decode\ndecode = fake\ndecode(data)\n", ()),
    Case("tls-module-shadow", "import requests\nrequests = fake\nrequests.get(url, verify=False)\n", ()),
    Case("tls-function-shadow", "from requests import get as fetch\nfetch = fake\nfetch(url, verify=False)\n", ()),
    Case("tls-nested-param", "import requests as req\ndef f(req):\n    req.get(url, verify=False)\n", ()),
    Case("tls-true-import", "import requests as req\nreq.get(url, verify=False)\n", (("GEN-TLS-VERIFY", 2),)),
    Case("shell-import-overwrite", "import subprocess as sub\nimport os as sub\nsub.run(cmd, shell=True)\n", ()),
    Case("builtin-eval-shadow", "eval = lambda value: value\neval(source)\n", ()),
    Case("builtin-exec-param", "def apply(exec):\n    exec(source)\n", ()),
    Case("builtin-eval-real", "eval(source)\n", (("PY-DYNAMIC-EXEC", 1),)),
    Case("sql-composed-local", 'query = f"SELECT * FROM t WHERE x={v}"\nconn.execute(query)\n', (("PY-SQL-CONCAT", 2),)),
    Case("sql-local-function", 'def f(v):\n    query = f"SELECT * FROM t WHERE x={v}"\n    conn.execute(query)\n', (("PY-SQL-CONCAT", 3),)),
    Case("sql-local-annotated", 'query: str = "SELECT * FROM t WHERE x=" + v\nconn.execute(query)\n', (("PY-SQL-CONCAT", 2),)),
    Case("sql-local-safe-rebind", 'query = f"SELECT * FROM t WHERE x={v}"\nquery = "SELECT * FROM t WHERE x=?"\nconn.execute(query)\n', ()),
    Case("sql-local-conditional-shadow", 'query = f"SELECT * FROM t WHERE x={v}"\nif cond:\n    query = safe_query\nconn.execute(query)\n', ()),
    Case("sql-direct-return", 'def f(v):\n    query = f"SELECT * FROM t WHERE x={v}"\n    return conn.execute(query)\n', (("PY-SQL-CONCAT", 3),)),
    Case("sql-if-arm", 'if enabled:\n    query = f"SELECT * FROM t WHERE x={v}"\n    conn.execute(query)\n', (("PY-SQL-CONCAT", 3),)),
    Case("sql-else-arm", 'if enabled:\n    pass\nelse:\n    query = "DELETE FROM t WHERE id=" + v\n    conn.execute(query)\n', (("PY-SQL-CONCAT", 5),)),
    Case("sql-if-return", 'def f(v):\n    if enabled:\n        query = f"SELECT * FROM t WHERE x={v}"\n        return conn.execute(query)\n', (("PY-SQL-CONCAT", 4),)),
    Case("sql-static-constant-concat", 'conn.execute("SELECT * FROM " + "t WHERE id=?")\n', ()),
    Case("sql-static-local-concat", 'query = "SELECT * FROM " + "t WHERE id=?"\nconn.execute(query)\n', ()),
    Case("sql-fstring-without-interpolation", 'query = f"SELECT * FROM t"\nconn.execute(query)\n', ()),
    Case("sql-outside-if-branch-unsupported", 'query = f"SELECT * FROM t WHERE x={v}"\nif enabled:\n    conn.execute(query)\n', ()),
    Case("sql-return-expression-ambiguous", 'def f(v):\n    query = f"SELECT * FROM t WHERE x={v}"\n    return wrap(conn.execute(query))\n', ()),
    Case("shell-truthy-one", 'import subprocess\nsubprocess.run(cmd, shell=1)\n', (("PY-SHELL", 2),)),
    Case("shell-truthy-string", 'import subprocess\nsubprocess.run(cmd, shell="yes")\n', (("PY-SHELL", 2),)),
    Case("shell-zero-safe", 'import subprocess\nsubprocess.run(cmd, shell=0)\n', ()),
    Case("shell-none-safe", 'import subprocess\nsubprocess.run(cmd, shell=None)\n', ()),
    Case("tls-zero", 'import requests\nrequests.get(url, verify=0)\n', (("GEN-TLS-VERIFY", 2),)),
    Case("tls-empty-string", 'import requests\nrequests.get(url, verify="")\n', (("GEN-TLS-VERIFY", 2),)),
    Case("tls-none-unknown-default", 'import requests\nrequests.get(url, verify=None)\n', ()),
    Case("tls-custom-cert-path", 'import requests\nrequests.get(url, verify="ca.pem")\n', ()),
    Case("sql-constant-formatted", 'cursor.execute(f"SELECT {1} FROM t")\n', ()),
    Case("sql-constant-formatted-spec", 'cursor.execute(f"SELECT {1:02d} FROM t")\n', ()),
    Case("sql-user-formatted", 'cursor.execute(f"SELECT * FROM t WHERE x={value}")\n', (("PY-SQL-CONCAT", 1),)),
    # Intentional remaining known misses: dynamic import / indirect builtin.
    Case("dynamic-getattr-known-miss", 'getattr(__import__("builtins"), "eval")(value)\n', (("PY-DYNAMIC-EXEC", 1),)),
    Case("shell-dynamic-import-known-miss", '__import__("subprocess").run(cmd, shell=True)\n', (("PY-SHELL", 1),)),
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
