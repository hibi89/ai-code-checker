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
    # P2-9: lexical function-local import provenance, fixed synthetic fixtures.
    Case("local-subprocess", "def check(cmd):\n    import subprocess as sp\n    sp.run(cmd, shell=True)\n", (("PY-SHELL", 3),)),
    Case("local-subprocess-from", "def check(cmd):\n    from subprocess import run as launch\n    launch(cmd, shell=True)\n", (("PY-SHELL", 3),)),
    Case("local-os", "def check(cmd):\n    import os as osapi\n    osapi.system(cmd)\n", (("PY-SHELL", 3),)),
    Case("local-asyncio", "async def check(cmd):\n    from asyncio import create_subprocess_shell as launch\n    await launch(cmd)\n", (("PY-SHELL", 3),)),
    Case("local-pickle", "def check(data):\n    import pickle as p\n    p.loads(data)\n", (("PY-PICKLE", 3),)),
    Case("local-requests", "def check(url):\n    from requests import get as fetch\n    fetch(url, verify=False)\n", (("GEN-TLS-VERIFY", 3),)),
    Case("local-builtins", "def check(data):\n    from builtins import eval as e\n    e(data)\n", (("PY-DYNAMIC-EXEC", 3),)),
    Case("local-before-rebind", "def f(cmd):\n    import subprocess as sp\n    sp.run(cmd, shell=True)\n    sp = fake\n    sp.run(cmd, shell=True)\n", (("PY-SHELL", 3),)),
    Case("local-late-import", "def check(cmd):\n    sp.run(cmd, shell=True)\n    import subprocess as sp\n", ()),
    Case("local-argument-shadow", "def check(sp):\n    sp.run(cmd, shell=True)\n", ()),
    Case("local-rebound", "def check(cmd):\n    import subprocess as sp\n    sp = fake\n    sp.run(cmd, shell=True)\n", ()),
    Case("local-branch-outside", "def check(cmd, enabled):\n    if enabled:\n        import subprocess as sp\n    sp.run(cmd, shell=True)\n", ()),
    Case("local-branch-inside", "def check(cmd, enabled):\n    if enabled:\n        import subprocess as sp\n        sp.run(cmd, shell=True)\n", (("PY-SHELL", 4),)),
    Case("local-branch-else", "def check(cmd, enabled):\n    if enabled:\n        import subprocess as sp\n    else:\n        sp.run(cmd, shell=True)\n", ()),
    Case("local-sibling", "def first():\n    import subprocess as sp\ndef second():\n    sp.run(cmd, shell=True)\n", ()),
    # P2-13: a single unguarded outer binding is a real lexical closure,
    # while conditional and rebound names remain unproven.
    Case("local-nested-closure-stable", "def outer():\n    import subprocess as sp\n    def inner():\n        sp.run(cmd, shell=True)\n", (("PY-SHELL", 4),)),
    Case("local-nested-closure-guarded", "def outer():\n    if enabled:\n        import subprocess as sp\n    def inner():\n        sp.run(cmd, shell=True)\n", ()),
    Case("local-nested-closure-rebound", "def outer():\n    import subprocess as sp\n    sp = fake\n    def inner():\n        sp.run(cmd, shell=True)\n", ()),
    Case("local-global-leak", "def check(cmd):\n    import subprocess as sp\nsp.run(cmd, shell=True)\n", ()),
    # Explicit builtins module / symbol aliases are sensitive only when proven.
    Case("builtins-module-eval", "import builtins\nbuiltins.eval(value)\n", (("PY-DYNAMIC-EXEC", 2),)),
    Case("builtins-module-exec-alias", "import builtins as safe_api\nsafe_api.exec(source)\n", (("PY-DYNAMIC-EXEC", 2),)),
    Case("builtins-from-eval-alias", "from builtins import eval as evaluate\nevaluate(value)\n", (("PY-DYNAMIC-EXEC", 2),)),
    Case("builtins-from-exec", "from builtins import exec\nexec(source)\n", (("PY-DYNAMIC-EXEC", 2),)),
    Case("builtins-module-late-import", "builtins.eval(value)\nimport builtins\n", ()),
    Case("builtins-module-shadow", "import builtins as b\nb = other\nb.eval(value)\n", ()),
    Case("builtins-function-argument-shadow", "import builtins as b\ndef f(b):\n    b.exec(source)\n", ()),
    Case("builtins-from-alias-shadow", "from builtins import eval as evaluate\nevaluate = fake\nevaluate(value)\n", ()),
    Case("builtins-not-related-method", "service.eval(value)\n", ()),
    Case("builtins-guarded-import-outside", "if flag:\n    import builtins as b\nb.eval(value)\n", ()),
    Case("builtins-guarded-import-inside", "if flag:\n    import builtins as b\n    b.eval(value)\n", (("PY-DYNAMIC-EXEC", 3),)),
    Case("builtins-guarded-from-outside", "if flag:\n    from builtins import exec as invoke\ninvoke(source)\n", ()),
    Case("builtins-other-module", "from fake import eval as evaluate\nevaluate(value)\n", ()),
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
    Case("sql-executemany-fstring", 'cursor.executemany(f"INSERT INTO users VALUES ({name})", rows)\n', (("PY-SQL-CONCAT", 1),)),
    Case("sql-executemany-parameterized", 'cursor.executemany("INSERT INTO users VALUES (?)", rows)\n', ()),
    Case("sql-executemany-local-dynamic", 'query = "DELETE FROM users WHERE id=" + uid\ncursor.executemany(query, rows)\n', (("PY-SQL-CONCAT", 2),)),
    Case("sql-executemany-local-static", 'query = "DELETE FROM users WHERE id=?"\ncursor.executemany(query, rows)\n', ()),
    Case("sql-executescript-dynamic", 'conn.executescript("DROP TABLE " + name)\n', (("PY-SQL-CONCAT", 1),)),
    Case("sql-executescript-local-dynamic", 'query = f"DELETE FROM users WHERE id={uid}"\nconn.executescript(query)\n', (("PY-SQL-CONCAT", 2),)),
    Case("sql-executescript-constant", 'conn.executescript("CREATE TABLE users(id INTEGER)")\n', ()),
    Case("sql-other-method-fstring", 'client.execute_many(f"DELETE FROM users WHERE id={uid}", rows)\n', ()),
    Case("sql-executemany-non-sql", 'printer.executemany(f"render {name}", rows)\n', ()),
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
    Case("conditional-import-following-outside", 'if enabled:\n    import subprocess as sp\nsp.run(cmd, shell=True)\n', ()),
    Case("conditional-import-call-same-arm", 'if enabled:\n    import subprocess as sp\n    sp.run(cmd, shell=True)\n', (("PY-SHELL", 3),)),
    Case("conditional-import-call-else-arm", 'if enabled:\n    import subprocess as sp\nelse:\n    sp.run(cmd, shell=True)\n', ()),
    Case("nested-conditional-import-leak", 'if outer:\n    if inner:\n        import subprocess as sp\n    sp.run(cmd, shell=True)\n', ()),
    Case("nested-conditional-import-same-arm", 'if outer:\n    if inner:\n        import subprocess as sp\n        sp.run(cmd, shell=True)\n', (("PY-SHELL", 4),)),
    Case("try-import-post-except", 'try:\n    import requests as req\nexcept ImportError:\n    req = fake\nreq.get(url, verify=False)\n', ()),
    Case("try-import-same-suite", 'try:\n    import requests as req\n    req.get(url, verify=False)\nexcept ImportError:\n    pass\n', (("GEN-TLS-VERIFY", 3),)),
    Case("except-import-outside", 'try:\n    pass\nexcept ValueError:\n    from pickle import loads as decode\ndecode(data)\n', ()),
    Case("except-import-same-handler", 'try:\n    pass\nexcept ValueError:\n    from pickle import loads as decode\n    decode(data)\n', (("PY-PICKLE", 5),)),
    Case("with-import-outside", 'with context:\n    import pickle as p\np.loads(data)\n', ()),
    Case("with-import-same-suite", 'with context:\n    import pickle as p\n    p.loads(data)\n', (("PY-PICKLE", 3),)),
    Case("loop-import-after-loop", 'for row in rows:\n    import subprocess as sp\nsp.run(cmd, shell=True)\n', ()),
    Case("loop-import-same-suite", 'for row in rows:\n    import subprocess as sp\n    sp.run(cmd, shell=True)\n', (("PY-SHELL", 3),)),
    Case("match-import-outside", 'match mode:\n    case "on":\n        import subprocess as sp\nsp.run(cmd, shell=True)\n', ()),
    Case("match-import-same-case", 'match mode:\n    case "on":\n        import subprocess as sp\n        sp.run(cmd, shell=True)\n', (("PY-SHELL", 4),)),
    Case("unconditional-import-after-guard", 'if enabled:\n    import os as sp\nimport subprocess as sp\nsp.run(cmd, shell=True)\n', (("PY-SHELL", 4),)),

    # High-impact direct shell APIs: provenance required, no shell=True flag.
    Case("os-shell-system", 'import os\nos.system(command)\n', (("PY-SHELL", 2),)),
    Case("os-shell-popen-alias", 'import os as shell\nshell.popen(command)\n', (("PY-SHELL", 2),)),
    Case("os-shell-import-from", 'from os import system as execute\nexecute(command)\n', (("PY-SHELL", 2),)),
    Case("asyncio-shell-direct", 'import asyncio\nasync def work():\n    await asyncio.create_subprocess_shell(command)\n', (("PY-SHELL", 3),)),
    Case("asyncio-shell-from", 'from asyncio import create_subprocess_shell as launch\nlaunch(command)\n', (("PY-SHELL", 2),)),
    Case("os-shell-literal-import", "__import__('os').system(command)\n", (("PY-SHELL", 1),)),
    Case("asyncio-shell-literal-getattr", "getattr(__import__('asyncio'), 'create_subprocess_shell')(command)\n", (("PY-SHELL", 1),)),
    Case("os-shell-shadow", 'import os as shell\nshell = other\nshell.system(command)\n', ()),
    Case("asyncio-shell-param-shadow", 'import asyncio as a\ndef check(a):\n    a.create_subprocess_shell(command)\n', ()),
    Case("os-shell-conditional-import-leak", 'if enabled:\n    import os as shell\nshell.system(command)\n', ()),
    Case("os-shell-conditional-import-same-arm", 'if enabled:\n    import os as shell\n    shell.system(command)\n', (("PY-SHELL", 3),)),
    Case("os-shell-unrelated-method", 'service.system(command)\n', ()),
    Case("os-shell-dynamic-module-unknown", '__import__(module).system(command)\n', ()),
    Case("asyncio-shell-exec-not-shell", 'import asyncio\nasyncio.create_subprocess_exec("echo", "hello")\n', ()),
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
    Case("sql-percent-variable", 'conn.execute("SELECT * FROM users WHERE id=%s" % uid)\n', (("PY-SQL-CONCAT", 1),)),
    Case("sql-percent-named-variable", 'conn.execute("DELETE FROM users WHERE id=%(uid)s" % {"uid": uid})\n', (("PY-SQL-CONCAT", 1),)),
    Case("sql-format-variable", 'cursor.execute("SELECT * FROM users WHERE id={}".format(uid))\n', (("PY-SQL-CONCAT", 1),)),
    Case("sql-format-keyword-variable", 'cursor.execute("UPDATE users SET name={name}".format(name=user))\n', (("PY-SQL-CONCAT", 1),)),
    Case("sql-format-map-variable", 'cursor.execute("SELECT * FROM users WHERE id={uid}".format_map(data))\n', (("PY-SQL-CONCAT", 1),)),
    Case("sql-percent-local-variable", 'query = "SELECT * FROM users WHERE id=%s" % uid\ncursor.execute(query)\n', (("PY-SQL-CONCAT", 2),)),
    Case("sql-format-local-variable", 'query = "SELECT * FROM users WHERE id={}".format(uid)\ncursor.execute(query)\n', (("PY-SQL-CONCAT", 2),)),
    Case("sql-percent-all-static", 'cursor.execute("SELECT * FROM users WHERE id=%s" % 7)\n', ()),
    Case("sql-percent-static-dict", 'cursor.execute("SELECT * FROM users WHERE id=%(id)s" % {"id": 7})\n', ()),
    Case("sql-format-all-static", 'cursor.execute("SELECT * FROM users WHERE id={}".format(7))\n', ()),
    Case("sql-format-map-static", 'cursor.execute("SELECT * FROM users WHERE id={uid}".format_map({"uid": 7}))\n', ()),
    Case("sql-format-escaped-only", 'cursor.execute("SELECT * FROM {{users}}".format(name))\n', ()),
    Case("sql-format-no-placeholder", 'cursor.execute("SELECT * FROM users".format(uid))\n', ()),
    Case("sql-percent-escaped-only", 'cursor.execute("SELECT %% FROM users" % uid)\n', ()),
    Case("sql-parameterized-unchanged", 'cursor.execute("SELECT * FROM users WHERE id=%s", (uid,))\n', ()),

    # Literal dynamic imports: only named, unshadowed builtin helpers count.
    Case("dynamic-pickle-loads", '__import__("pickle").loads(data)\n', (("PY-PICKLE", 1),)),
    Case("dynamic-pickle-getattr-load", 'getattr(__import__("pickle"), "load")(stream)\n', (("PY-PICKLE", 1),)),
    Case("dynamic-requests-get-noverify", '__import__("requests").get(url, verify=False)\n', (("GEN-TLS-VERIFY", 1),)),
    Case("dynamic-requests-getattr-post", 'getattr(__import__("requests"), "post")(url, verify=0)\n', (("GEN-TLS-VERIFY", 1),)),
    Case("dynamic-requests-verified", '__import__("requests").get(url, verify=True)\n', ()),
    Case("dynamic-pickle-module-unknown", '__import__(module).loads(data)\n', ()),
    Case("dynamic-pickle-shadowed-import", '__import__ = custom\n__import__("pickle").loads(data)\n', ()),
    Case("dynamic-pickle-extra-arg", '__import__("pickle", globals()).loads(data)\n', ()),
    Case("dynamic-requests-dynamic-member", 'getattr(__import__("requests"), method)(url, verify=False)\n', ()),
    # Direct literal dynamic imports are recognized only when their helper
    # builtins have not been shadowed. No source code is executed.
    Case("dynamic-builtins-direct-eval", '__import__("builtins").eval(value)\n', (("PY-DYNAMIC-EXEC", 1),)),
    Case("dynamic-builtins-getattr-exec", 'getattr(__import__("builtins"), "exec")(code)\n', (("PY-DYNAMIC-EXEC", 1),)),
    Case("dynamic-subprocess-getattr", 'getattr(__import__("subprocess"), "Popen")(cmd, shell=True)\n', (("PY-SHELL", 1),)),
    Case("dynamic-subprocess-false", '__import__("subprocess").run(cmd, shell=False)\n', ()),
    Case("dynamic-subprocess-other-module", '__import__("unrelated").run(cmd, shell=True)\n', ()),
    Case("dynamic-subprocess-other-method", '__import__("subprocess").safe_call(cmd, shell=True)\n', ()),
    Case("dynamic-subprocess-computed-module", '__import__(package).run(cmd, shell=True)\n', ()),
    Case("dynamic-subprocess-extra-import-argument", '__import__("subprocess", globals()).run(cmd, shell=True)\n', ()),
    Case("dynamic-builtins-unrelated-attribute", '__import__("builtins").print(value)\n', ()),
    Case("dynamic-builtins-getattr-variable-name", 'getattr(__import__("builtins"), method)(value)\n', ()),
    Case("dynamic-builtins-getattr-extra-argument", 'getattr(__import__("builtins"), "eval", fallback)(value)\n', ()),
    Case("dynamic-subprocess-shadow-import", 'def check(__import__):\n    return __import__("subprocess").run(cmd, shell=True)\n', ()),
    Case("dynamic-builtins-shadow-getattr", 'def check(getattr):\n    return getattr(__import__("builtins"), "eval")(value)\n', ()),
    Case("dynamic-subprocess-module-rebound", '__import__ = fake\n__import__("subprocess").run(cmd, shell=True)\n', ()),
    Case("dynamic-getattr-global-rebound", 'getattr = fake\ngetattr(__import__("builtins"), "eval")(value)\n', ()),
    Case("dynamic-builtins-getattr-value-no-execution", 'getattr(__import__("builtins"), "eval")\n', ()),
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
