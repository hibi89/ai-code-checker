"""P0-E: infer CArchive/PYZ ownership candidates and stage ORIGINAL license files.

Inputs: local P0-D JSON and installed pinned build environment.
Outputs: local, UNAPPROVED evidence/NOTICE draft; NEVER a compliance certificate.
No network, customer source, bundled source extraction or code execution.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
import re
import sys
from collections import Counter
from pathlib import Path

try:
    from packaging.utils import canonicalize_name
except ImportError:
    def canonicalize_name(name: str) -> str:
        # Standard CI also runs legacy Python installations without packaging.
        return re.sub(r"[-_.]+", "-", name).lower()


MAX_LICENSE_TEXT_BYTES = 1024 * 1024
MAX_MAPPINGS = 30000
FIRST_PARTY = frozenset({
    "desktop_core", "desktop_ui", "offline_core", "offline_coverage",
    "offline_report", "code_input", "static_checks", "review_models",
    "reporting", "reviewer", "main",
})


def _safe_name(name: str) -> str:
    if not isinstance(name, str) or len(name) > 512 or "\x00" in name:
        raise ValueError("Invalid embedded entry name")
    return name.replace("\\", "/")


def _native_candidates(archive_name: str, installed_files: dict[str, set[str]]) -> list[str]:
    """Exact (relative path) filename claim only, not binary provenance."""
    key = archive_name.casefold()
    full = sorted(k for k, names in installed_files.items() if key in names)
    return full


def _installed_file_claims(records: list[dict]) -> dict[str, set[str]]:
    matches = {}
    for dist_info in records:
        name = canonicalize_name(dist_info["name"])
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            continue
        names = set()
        for file in dist.files or ():
            path = _safe_name(str(file)).casefold()
            if path.endswith((".pyd", ".dll", ".so", ".dylib")):
                names.add(path)
        matches[name] = names
    return matches


def make_mapping(audit: dict, *, package_claims=None, installed_files=None) -> dict:
    """Map every observed embedded name; ambiguous/unknown never silently dropped.

    Name matching, metadata claims and stdlib classification are hypotheses,
    NOT hashes of the original embedded uncompressed binaries.
    """
    if (audit.get("license_compliance_certified") is not False
            or audit.get("third_party_notice_ready_to_distribute") is not False
            or audit.get("customer_release_ready") is not False):
        raise ValueError("Cannot accept falsely approved source manifest")
    archive = audit["archive"]
    top = archive["top_level"]
    pyz = archive["pyz_modules"]
    if not top or not pyz or len(top) + len(pyz) > MAX_MAPPINGS:
        raise ValueError("Invalid or oversized archive contents")
    installed = {
        canonicalize_name(item["name"]): item
        for item in audit["python_build_distributions"]
    }
    package_claims = package_claims if package_claims is not None else metadata.packages_distributions()
    installed_files = installed_files if installed_files is not None else _installed_file_claims(
        audit["python_build_distributions"]
    )
    stdlib = sys.stdlib_module_names
    output = []
    counts = Counter()
    candidate_dists = set()
    unique = set()
    for row in pyz:
        module = _safe_name(row["module"])
        pathkey = ("pyz", module)
        if pathkey in unique:
            raise ValueError("Duplicate embedded module")
        unique.add(pathkey)
        root = module.partition(".")[0]
        declared = sorted({
            canonicalize_name(pkg)
            for pkg in package_claims.get(root, [])
            if canonicalize_name(pkg) in installed
        })
        if root in FIRST_PARTY:
            kind, owners = "first_party_candidate", ["repository"]
        elif declared:
            kind = "installed_dist_unique_name_claim" if len(declared) == 1 else "ambiguous_dist_name_claim"
            owners = declared
            candidate_dists.update(declared)
        elif root in stdlib:
            kind, owners = "cpython_stdlib_name_candidate", ["CPython"]
        else:
            kind, owners = "unresolved", []
        counts[kind] += 1
        output.append({"kind": "PYZ", "name": module, "mapping": kind, "owner_candidates": owners,
                       "match_basis": "module prefix/name only"})
    for row in top:
        name = _safe_name(row["name"])
        pathkey = ("archive", name)
        if pathkey in unique:
            raise ValueError("Duplicate CArchive entry")
        unique.add(pathkey)
        lower = name.lower()
        if re.search(r"(?:^|/)python3\d+\.dll$", lower):
            kind, owners = "cpython_runtime_filename_candidate", ["CPython"]
        elif (re.search(r"(?:^|/)(?:tcl|tk)\d+.*\.dll$", lower)
              or lower.startswith(("_tcl_data/", "_tk_data/"))):
            kind, owners = "tcl_tk_filename_candidate", ["Tcl/Tk"]
        elif name.rsplit("/", 1)[-1] in FIRST_PARTY and str(row.get("typecode")) in ("s", "m"):
            kind, owners = "first_party_candidate", ["repository"]
        else:
            declared = _native_candidates(name, installed_files) if lower.endswith(
                (".pyd", ".dll", ".so", ".dylib")) else []
            if declared:
                kind = ("installed_native_exact_relative_filename_candidate"
                        if len(declared) == 1 else "ambiguous_native_filename")
                owners = declared
                candidate_dists.update(declared)
            elif lower.endswith((".dll", ".pyd", ".exe", ".so", ".dylib")):
                kind, owners = "unresolved_native_or_system_binary", []
            else:
                kind, owners = "unresolved_archive_resource_or_bootloader", []
        counts[kind] += 1
        output.append({"kind": "CArchive", "name": name, "mapping": kind,
                       "owner_candidates": owners, "match_basis": "metadata/path only"})
    summary = {
        "format": "code_checker_p0e_ownership_claims_v1",
        "exe_sha256": audit["exe_sha256"],
        "archive_entries": len(top),
        "pyz_modules": len(pyz),
        "total_rows": len(output),
        "mapping_counts": dict(sorted(counts.items())),
        "installed_dist_candidates": sorted(candidate_dists),
        "candidate_dist_count": len(candidate_dists),
        "unresolved_count": sum(value for key, value in counts.items() if key.startswith("unresolved")),
        "all_items_accounted_for_in_metadata": len(output) == len(top) + len(pyz),
        "mapping_is_name_based_hypothesis": True,
        "embedded_binary_hash_matches_checked": False,
        "manual_component_version_and_license_review_required": True,
        "license_compliance_certified": False,
        "third_party_notice_ready_to_distribute": False,
        "customer_release_ready": False,
        "status": "CANDIDATE_MAPPING_ONLY_NOTICE_REVIEW_REQUIRED",
        "entries": output,
    }
    return summary


def gather_original_license_texts(audit: dict, mapping: dict) -> tuple[str, dict]:
    """Read only installed-package license paths verified by P0-D SHA-256.

    Full original text is staged LOCALLY in the draft, never pushed to GitHub.
    These files are NOT necessarily shipped in the EXE.
    """
    selected = set(mapping["installed_dist_candidates"])
    # PyInstaller bootloader license exception requires separate examination
    # whether or not the *build tool* is bundled in the PYZ.
    selected.add("pyinstaller")
    pieces = [
        "# THIRD-PARTY NOTICE REVIEW CANDIDATE — NOT FOR DISTRIBUTION",
        "",
        "This document contains installed build-environment license text candidates.",
        "It has not established the actual binary owners, redistribution obligations,",
        "copyright attribution completeness, or legal permission to distribute.",
        "Do not attach as an approved NOTICE or send to customers.",
        "",
    ]
    reviewed_files = 0
    missing = []
    for item in sorted(audit["python_build_distributions"], key=lambda d: d["name"]):
        name = canonicalize_name(item["name"])
        if name not in selected:
            continue
        pieces.extend([f"## {name} {item['version']} — INSTALLED LICENSE EVIDENCE ONLY",
                       "", f"Metadata label: {item['license_metadata']}", ""])
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            missing.append(name + ": installed distribution unavailable")
            continue
        licenses = item["license_files_in_installed_distribution"]
        if not licenses:
            missing.append(name + ": no listed license original")
        for record in licenses:
            relative = _safe_name(record["installed_relative_path"])
            # Make source path originate from enumerated distribution RECORD.
            declared_paths = {str(p).replace("\\", "/") for p in dist.files or ()}
            if relative not in declared_paths:
                raise ValueError("Evidence license file missing from installed RECORD")
            absolute = Path(dist.locate_file(relative))
            try:
                if not absolute.is_file() or absolute.stat().st_size > MAX_LICENSE_TEXT_BYTES:
                    missing.append(name + ": unreadable/oversized " + relative)
                    continue
                data = absolute.read_bytes()
            except OSError:
                missing.append(name + ": unreadable " + relative)
                continue
            if hashlib.sha256(data).hexdigest() != record["sha256"]:
                raise ValueError("License original changed since P0-D hash")
            try:
                original = data.decode("utf-8-sig")
            except UnicodeDecodeError:
                try:
                    original = data.decode("cp1252")
                except UnicodeDecodeError:
                    missing.append(name + ": cannot decode " + relative)
                    continue
            pieces.extend([f"### Original installed file: {relative}",
                           f"SHA256: {record['sha256']}", "", original, ""])
            reviewed_files += 1
    return "\n".join(pieces), {
        "selected_installed_distributions": sorted(selected),
        "staged_original_license_files": reviewed_files,
        "unavailable_or_missing_texts": sorted(missing),
        "selected_dists_without_claim_of_exe_inclusion": True,
        "draft_for_distribution": False,
        "human_legal_review_pending": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline component claim and license-original draft")
    parser.add_argument("--audit", required=True)
    parser.add_argument("--mapping-out", required=True)
    parser.add_argument("--notice-draft-out", required=True)
    args = parser.parse_args()
    try:
        source = Path(args.audit)
        mapping_path = Path(args.mapping_out)
        draft_path = Path(args.notice_draft_out)
        if any(p.exists() or p.is_symlink() for p in (mapping_path, draft_path)):
            raise FileExistsError("Refuse overwrite of mapping/notice files")
        if mapping_path == draft_path or not all(
                p.parent.is_dir() for p in (mapping_path, draft_path)):
            raise ValueError("Output destinations must be distinct existing directories")
        audit = json.loads(source.read_text(encoding="utf-8"))
        mapping = make_mapping(audit)
        draft, draft_status = gather_original_license_texts(audit, mapping)
        mapping["license_text_draft"] = draft_status
        mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        draft_path.write_text(draft, encoding="utf-8")
        print("COMPONENT_NAME_CANDIDATE_MAPPING_PASS")
        print("TOTAL_ARCHIVE_AND_PYZ_ROWS=" + str(mapping["total_rows"]))
        print("CANDIDATE_PACKAGES=" + str(mapping["candidate_dist_count"]))
        # Package names are public package metadata, not customer code or paths.
        print("CANDIDATE_PACKAGE_NAMES=" + ",".join(mapping["installed_dist_candidates"]))
        print("MAPPING_CATEGORY_COUNTS=" + json.dumps(mapping["mapping_counts"], sort_keys=True))
        print("UNRESOLVED_ENTRIES=" + str(mapping["unresolved_count"]))
        print("STAGED_ORIGINAL_LICENSE_FILES=" + str(draft_status["staged_original_license_files"]))
        print("MISSING_ORIGINAL_LICENSE_FILES=" + str(len(draft_status["unavailable_or_missing_texts"])))
        print("LEGAL_NOTICE_REVIEW=REQUIRED")
        print("BINARY_OWNERSHIP_VERIFIED=False")
        print("CUSTOMER_RELEASE_ALLOWED=False")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("COMPONENT_MAPPING_FAILED=" + type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
