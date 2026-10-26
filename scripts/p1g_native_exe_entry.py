"""CI-only frozen executable smoke: never open customer files or network."""
from __future__ import annotations
import importlib
import json
import sys


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    if sys.argv[1] == "--baseline":
        print(json.dumps({"status": "P1G_BASELINE_NO_JS_TS", "customer_release_ready": False}))
        return 0
    if sys.argv[1] == "--synthetic":
        module = importlib.import_module("scripts.prototype_js_ts_adapter")
        cases = [
            ("js", "eval(value);\n", "JS-DIRECT-EVAL-PATTERN"),
            ("ts", "const x: string = 'value';\neval(x);\n", "JS-DIRECT-EVAL-PATTERN"),
            ("tsx", "const X = () => <div>{eval(value)}</div>;\n", "JS-DIRECT-EVAL-PATTERN"),
            ("js", "new Function('return 1');\n", "JS-NEW-FUNCTION-PATTERN"),
        ]
        for language, code, rule in cases:
            outcome = module.inspect(code, language)
            if (outcome.status != "syntax_checked" or
                    not any(candidate.rule == rule for candidate in outcome.candidates) or
                    outcome.shipped or outcome.approved_for_sale):
                raise AssertionError("Frozen grammar probe mismatch: " + language)
        print(json.dumps({
            "status": "P1G_PACKAGED_GRAMMAR_SYNTHETIC_PASS",
            "cases": len(cases),
            "customer_release_ready": False,
            "real_world_security_accuracy": "UNVERIFIED",
        }))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
