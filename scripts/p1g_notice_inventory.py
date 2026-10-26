"""Research-only original installed-wheel license text evidence.

Read original installed license/copyright/NOTICE files locally, hash contents,
and check basic MIT text markers. NEVER publish copied license texts, declare
redistribution compliance, or conflate wheel contents with packed EXE contents.
"""
from __future__ import annotations
import hashlib
import json
from importlib import metadata
from pathlib import PurePosixPath

PINNED = {
    "tree-sitter": "0.26.0",
    "tree-sitter-javascript": "0.25.0",
    "tree-sitter-typescript": "0.23.2",
}
LICENSE_NAMES = ("LICENSE", "LICENCE", "COPYING", "NOTICE", "COPYRIGHT")


def _matching_file(path: object) -> bool:
    name = PurePosixPath(str(path).replace("\\", "/")).name.upper()
    return any(name == base or name.startswith(base + ".") or
               name.startswith(base + "-") for base in LICENSE_NAMES)


def _license_text_ok(raw: bytes) -> bool:
    if not raw or len(raw) > 512 * 1024 or b"\x00" in raw:
        return False
    content = raw.decode("utf-8-sig", errors="replace").casefold()
    return ("permission is hereby granted" in content
            and "copyright" in content
            and "software" in content
            and "without restriction" in content)


def inventory() -> dict:
    packages: dict[str, dict] = {}
    for name, expected in PINNED.items():
        distribution = metadata.distribution(name)
        if distribution.version != expected:
            raise AssertionError("Pinned version drift: " + name)
        files = tuple(distribution.files or ())
        matched = [path for path in files if _matching_file(path)]
        if not matched:
            raise AssertionError("Installed original LICENSE file absent: " + name)
        original_evidence = []
        for path in matched:
            raw = distribution.locate_file(path).read_bytes()
            if not _license_text_ok(raw):
                raise AssertionError("Original installed license text check failed: " + name)
            original_evidence.append({
                "installed_relative_name": PurePosixPath(str(path)).name,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "basic_mit_text_markers_present": True,
                "full_original_text_published": False,
            })
        packages[name] = {
            "version": expected,
            "original_installed_license_files_read": len(original_evidence),
            "evidence": original_evidence,
        }
    return {
        "kind": "p1g_ci_original_wheel_license_text_metadata",
        "packages": packages,
        "packages_evaluated": len(packages),
        "source": "exact installed wheel files on CI runner, not shipped CArchive",
        "license_texts_copied_to_repo_or_artifact": False,
        "original_license_review_for_distribution_completed": False,
        "dependency_chain_notice_approved": False,
        "customer_exe_license_compliance_certified": False,
        "customer_release_ready": False,
    }


if __name__ == "__main__":
    print(json.dumps(inventory(), ensure_ascii=False, sort_keys=True))
