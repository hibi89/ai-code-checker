"""CI-only feasibility probe for offline JS/TS/TSX syntax parsers.

Never runs target JavaScript/TypeScript, fetches code, enables user plugins or
changes the shipped Windows executable. All samples are hand-authored.
Package metadata and parse behavior are observations, not redistribution
clearance or real-world vulnerability detection accuracy.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from importlib import metadata
from typing import Any


PINNED = {
    "tree-sitter": "0.26.0",
    "tree-sitter-javascript": "0.25.0",
    "tree-sitter-typescript": "0.23.2",
}


@dataclass(frozen=True)
class Fixture:
    name: str
    language: str
    text: str
    valid: bool


SAMPLES = (
    Fixture("javascript-const", "js", "const value = 10;\nconsole.log(value);\n", True),
    Fixture("javascript-arrow", "js", "const fn = (x) => x?.name ?? 'n/a';\n", True),
    Fixture("javascript-jsx", "js", "const view = <div>{name}</div>;\n", True),
    Fixture("javascript-utf8-offset", "js", "const 한글 = 1;\nlet next = 한글;\n", True),
    Fixture("javascript-comment-not-executed", "js", "// process.exit(1)\nconst x = 1;\n", True),
    Fixture("javascript-broken", "js", "const value = ;\n", False),
    Fixture("typescript-interface", "ts", "interface Item { id: number }\nconst item: Item = {id: 1};\n", True),
    Fixture("typescript-generic", "ts", "function identity<T>(input: T): T { return input; }\n", True),
    Fixture("typescript-optional", "ts", "type Name = string | null;\nconst name: Name = null;\n", True),
    Fixture("typescript-broken", "ts", "const value: = 1;\n", False),
    Fixture("tsx-component", "tsx", "const Element = (props: {name: string}) => <span>{props.name}</span>;\n", True),
    Fixture("tsx-broken", "tsx", "const item = <div>;\n", False),
)


def _assert_metadata() -> dict[str, dict[str, object]]:
    observed = {}
    for package, version in PINNED.items():
        dist = metadata.distribution(package)
        installed = dist.version
        if installed != version:
            raise AssertionError("Parser probe version drift: " + package)
        declared = (dist.metadata.get("License-Expression")
                    or dist.metadata.get("License") or "").strip()
        classifiers = dist.metadata.get_all("Classifier", []) or []
        # Packaging METADATA may use a full MIT license body rather than the
        # short SPDX string. Check only advertised license identifiers, never
        # treat wheel metadata as legal redistribution clearance.
        evidence = (
            "spdx-or-license-field" if re.search(r"(?i)\bMIT\b", declared[:350])
            else "classifier" if any(
                "License :: OSI Approved :: MIT License" in value
                for value in classifiers
            ) else None
        )
        if evidence is None:
            raise AssertionError("No MIT license claim found in parser metadata: " + package)
        files = list(dist.files or [])
        # A wheel metadata flag does not prove all legal notices are shipped.
        license_candidates = sum(
            any(segment.upper().startswith(("LICENSE", "COPYING", "NOTICE"))
                for segment in entry.parts)
            for entry in files
        )
        observed[package] = {
            "version": installed,
            "declared_license": "MIT (packaging claim only)",
            "license_metadata_evidence": evidence,
            "installed_license_named_paths": license_candidates,
            "notice_approval": False,
            "customer_exe_included": False,
        }
    return observed


def _parsers() -> dict[str, Any]:
    # Imports happen ONLY inside the separate CI-only feasibility job.
    from tree_sitter import Language, Parser
    import tree_sitter_javascript
    import tree_sitter_typescript

    return {
        "js": Parser(Language(tree_sitter_javascript.language())),
        "ts": Parser(Language(tree_sitter_typescript.language_typescript())),
        "tsx": Parser(Language(tree_sitter_typescript.language_tsx())),
    }


def probe() -> dict[str, object]:
    packages = _assert_metadata()
    parsers = _parsers()
    checked = 0
    valid = 0
    invalid = 0
    for sample in SAMPLES:
        source = sample.text.encode("utf-8")
        tree = parsers[sample.language].parse(source)
        accepted = not tree.root_node.has_error and not tree.root_node.is_missing
        if accepted != sample.valid:
            raise AssertionError("Unexpected grammar parse outcome: " + sample.name)
        if tree.root_node.end_byte != len(source):
            raise AssertionError("UTF-8 byte-span mismatch: " + sample.name)
        checked += 1
        valid += int(sample.valid)
        invalid += int(not sample.valid)
    return {
        "format": "code_checker_js_ts_parser_ci_feasibility_v1",
        "test_fixtures": checked,
        "valid_syntax_accepted": valid,
        "malformed_syntax_rejected": invalid,
        "tested_grammars": sorted(parsers),
        "pinned_packages": packages,
        "runs_scanned_program": False,
        "source_uploaded": False,
        "required_ai_api_calls": 0,
        "shipped_exe_modified": False,
        "commercial_release_ready": False,
        "legal_notice_approved": False,
        "real_world_security_accuracy": "UNVERIFIED",
        "status": "SYNTAX_PARSER_FEASIBILITY_ONLY",
    }


def main() -> int:
    print(json.dumps(probe(), sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
