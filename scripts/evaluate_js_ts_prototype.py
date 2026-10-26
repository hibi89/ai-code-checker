"""Fixed artificial corpus. Metrics only describe these syntax labels."""
from __future__ import annotations
import json
from scripts.prototype_js_ts_adapter import inspect

E = "JS-DIRECT-EVAL-PATTERN"
F = "JS-NEW-FUNCTION-PATTERN"
# (id, language, source, expected state, expected rule/line pairs)
CASES = (
    ("eval_js", "js", "eval(input);\n", "syntax_checked", ((E, 1),)),
    ("eval_ts", "ts", "const x: string = 'ok';\neval(x);\n", "syntax_checked", ((E, 2),)),
    ("eval_tsx", "tsx", "const C = () => <div>{eval(x)}</div>;\n", "syntax_checked", ((E, 1),)),
    ("new_function_js", "js", "const f = new Function('return 1');\n", "syntax_checked", ((F, 1),)),
    ("new_function_ts", "ts", "const f: Function = new Function('return 1');\n", "syntax_checked", ((F, 1),)),
    ("comment", "js", "// eval(input)\nconst x = 1;\n", "syntax_checked", ()),
    ("string", "js", "const x = 'eval(1)';\n", "syntax_checked", ()),
    ("member", "js", "client.eval(input);\n", "syntax_checked", ()),
    ("property", "js", "new something.Function('x');\n", "syntax_checked", ()),
    ("name_only", "js", "const FunctionName = 42;\n", "syntax_checked", ()),
    ("tsx_attr", "tsx", "const C = () => <div title='eval(1)'/>;\n", "syntax_checked", ()),
    ("ts_interface", "ts", "interface Item { id: number }\nconst a: Item = {id: 2};\n", "syntax_checked", ()),
    ("js_unicode", "js", "const 한글 = 1;\neval(한글);\n", "syntax_checked", ((E, 2),)),
    ("js_2_candidates", "js", "eval(x);\nnew Function('1');\n", "syntax_checked", ((E, 1), (F, 2))),
    ("malformed_js", "js", "const x = ;\n", "syntax_failed", ()),
    ("malformed_ts", "ts", "const x: = 1;\n", "syntax_failed", ()),
    ("malformed_tsx", "tsx", "const C = <div>;\n", "syntax_failed", ()),
)


def evaluate() -> dict:
    tp = fp = fn = 0
    for case_id, language, code, expected_state, labels in CASES:
        outcome = inspect(code, language)
        if (outcome.status != expected_state or not outcome.syntax_only
                or outcome.shipped or outcome.approved_for_sale):
            raise AssertionError("Synthetic status mismatch: " + case_id)
        found = {(item.rule, item.line) for item in outcome.candidates}
        expected = set(labels)
        tp += len(found & expected)
        fp += len(found - expected)
        fn += len(expected - found)
    if fp or fn:
        raise AssertionError("Synthetic candidate mismatch")
    return {
        "format": "P1F_RESEARCH_SYNTAX_CANDIDATES",
        "cases": len(CASES), "tp": tp, "fp": fp, "fn": fn,
        "syntax_only": True, "product_integrated": False,
        "real_world_accuracy": "UNVERIFIED", "commercial_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), sort_keys=True))
