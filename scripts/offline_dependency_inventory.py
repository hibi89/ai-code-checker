"""Preliminary build-env dependency inventory, NOT a legal license certificate.

Enumerates reachable installed Python distributions from offline build roots.
Does not install packages, read source/customer code, invoke networks, or claim
the list exactly matches PyInstaller-bundled binaries, Tk/Tcl, system libraries.
"""
from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
import platform
import re
import sys

try:
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name
except ImportError:
    Requirement = None
    def canonicalize_name(name: str):
        return re.sub(r"[-_.]+", "-", name).lower()


DEFAULT_ROOTS = {"pyinstaller": "6.22.3"}


def _license_field(dist):
    m = dist.metadata
    expression = m.get("License-Expression", "").strip()
    if expression:
        return expression, "License-Expression"
    classifier = [item.rsplit(" :: ", 1)[-1]
                  for item in m.get_all("Classifier", []) if item.startswith("License ::")]
    if classifier:
        return " | ".join(sorted(set(classifier))), "Classifier"
    description = (m.get("License", "") or "").strip()
    if description:
        if len(description) > 160:
            return description[:160] + "…", "Legacy-License-Truncated"
        return description, "Legacy-License"
    return "UNKNOWN", "Metadata-Missing"


def inventory(roots=None):
    if Requirement is None:
        raise RuntimeError("packaging metadata parser is missing")
    roots = roots or DEFAULT_ROOTS
    pending = list(roots)
    seen = set()
    records = []
    unresolved = []
    while pending:
        raw = pending.pop()
        key = canonicalize_name(raw)
        if key in seen:
            continue
        seen.add(key)
        try:
            dist = metadata.distribution(raw)
        except metadata.PackageNotFoundError:
            unresolved.append(raw)
            continue
        license_label, origin = _license_field(dist)
        requires = []
        for entry in dist.requires or []:
            try:
                req = Requirement(entry)
                # Ignore optional extras; include only installed current-platform
                # requirements. A packaging hook might still bring hidden imports.
                if req.marker and not req.marker.evaluate({"extra": ""}):
                    continue
                name = canonicalize_name(req.name)
            except Exception:
                unresolved.append("unparsed requirement for " + key)
                continue
            requires.append(name)
            if name not in seen:
                pending.append(name)
        records.append({
            "name": canonicalize_name(dist.metadata.get("Name", raw)),
            "version": dist.version,
            "license_declared": license_label,
            "license_metadata_source": origin,
            "requires_in_current_environment": sorted(set(requires)),
        })
    records.sort(key=lambda x: x["name"])
    wrong_roots = [
        {"name": key, "expected_version": value,
         "observed_version": next((r["version"] for r in records if r["name"] == key), "MISSING")}
        for key, value in roots.items()
        if not any(r["name"] == key and r["version"] == value for r in records)
    ]
    return {
        "kind": "installed_python_offline_build_dependency_inventory",
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "roots": roots,
        "components": records,
        "components_count": len(records),
        "unknown_license_metadata_count": sum(c["license_declared"] == "UNKNOWN" for c in records),
        "unresolved": sorted(set(unresolved)),
        "wrong_root_versions": wrong_roots,
        "needs_full_bundled_binary_manifest": True,
        "needs_full_LICENSE_NOTICE_review": True,
        "includes_python_stdlib_tcl_tk": False,
        "status": "INVENTORY_ONLY_REVIEW_REQUIRED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Installed offline build deps, no downloads")
    parser.add_argument("--strict", action="store_true", help="Fail when missing/root mismatched dependencies")
    args = parser.parse_args()
    try:
        report = inventory()
    except Exception as exc:
        print(json.dumps({"status": "INVENTORY_FAILED", "error": type(exc).__name__}))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 1 if args.strict and (report["unresolved"] or report["wrong_root_versions"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
