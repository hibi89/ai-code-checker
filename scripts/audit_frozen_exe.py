"""Inspect the BUILT Windows PyInstaller onefile CArchive and nested PYZ.

No executable invocation, no extraction of bundled code, no network.
The generated files are LOCAL CI evidence, NOT license approval / a final SBOM.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
import os
import re
from collections import Counter
from pathlib import Path

from scripts.offline_dependency_inventory import DEFAULT_ROOTS, inventory


MAX_ENTRY_NAMES = 20000
LICENSE_NAMES = re.compile(r"(?i)^(?:license|licence|copying|notice|copyright)(?:[._-].*)?$")


def sha256_file(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def inspect_archive(reader) -> dict:
    """Unpack only TOC *metadata*; recursive PYZ names, never extract code."""
    top = []
    nested = []
    failures = []
    type_counts: Counter[str] = Counter()
    toc = reader.toc
    if not hasattr(toc, "items") or len(toc) == 0:
        raise ValueError("PyInstaller CArchive TOC is empty or unreadable")
    if len(toc) > MAX_ENTRY_NAMES:
        raise ValueError("Too many CArchive entries for bounded manifest")
    for name, entry in sorted(toc.items()):
        if not isinstance(name, str) or len(entry) != 5:
            raise ValueError("Unexpected CArchive TOC entry shape")
        _position, compressed_size, unpacked_size, compressed, typecode = entry
        if any(not isinstance(value, int) or value < 0 for value in (compressed_size, unpacked_size)):
            raise ValueError("Invalid CArchive size metadata")
        type_counts[str(typecode)] += 1
        top.append({
            "name": name,
            "typecode": str(typecode),
            "compressed_bytes": compressed_size,
            "unpacked_bytes": unpacked_size,
            "compressed": bool(compressed),
        })
        if typecode == "z":
            try:
                pyz = reader.open_embedded_archive(name)
                if not hasattr(pyz.toc, "items"):
                    raise ValueError("Invalid nested PYZ TOC")
                if len(pyz.toc) > MAX_ENTRY_NAMES:
                    raise ValueError("Too many PYZ module entries")
                for module, pyz_entry in sorted(pyz.toc.items()):
                    if not isinstance(module, str) or len(pyz_entry) != 3:
                        raise ValueError("Invalid nested PYZ entry shape")
                    nested.append({"archive": name, "module": module, "typecode": str(pyz_entry[0])})
            except Exception as exc:
                failures.append({"archive": name, "reason": type(exc).__name__})
    if not any(row["typecode"] == "z" for row in top):
        failures.append({"archive": "PYZ", "reason": "missing"})
    if not nested:
        failures.append({"archive": "PYZ", "reason": "no readable Python modules"})
    bundled_dlls = [
        row["name"] for row in top
        if row["name"].lower().endswith((".dll", ".pyd"))
    ]
    framework_markers = {
        "python_runtime": any(re.search(r"(?i)(?:^|[\\/])python3\d+\.dll$", x) for x in bundled_dlls),
        "tcl_or_tk": any(re.search(r"(?i)(?:^|[\\/])(?:tcl|tk)\d+.*\.dll$", x) for x in bundled_dlls),
        "native_binary_present": bool(bundled_dlls),
    }
    return {
        "top_level": top, "pyz_modules": nested,
        "top_level_count": len(top),
        "pyz_module_count": len(nested),
        "type_counts": dict(sorted(type_counts.items())),
        "framework_markers": framework_markers,
        "archive_read_errors": failures,
        "metadata_only": True,
        "no_bundle_entry_extracted_or_executed": True,
    }


def gather_installed_license_evidence(root_versions: dict[str, str] | None = None) -> list[dict]:
    """Record candidate text hashes from *installed* wheels, not embedded EXE."""
    root_versions = root_versions or DEFAULT_ROOTS
    manifest = inventory(root_versions)
    if manifest["wrong_root_versions"] or manifest["unresolved"]:
        raise ValueError("Pinned build requirements not available for review")
    evidence = []
    for item in manifest["components"]:
        dist = metadata.distribution(item["name"])
        licenses = []
        # A package can have .dist-info/LICENSE* or data license files.
        for file in dist.files or ():
            relative = str(file).replace("\\", "/")
            if len(relative) > 512:
                continue
            basename = Path(relative).name
            if not LICENSE_NAMES.match(basename):
                continue
            absolute = Path(dist.locate_file(file))
            try:
                if not absolute.is_file() or absolute.stat().st_size > 2 * 1024 * 1024:
                    continue
                licenses.append({
                    "installed_relative_path": relative,
                    "bytes": absolute.stat().st_size,
                    "sha256": sha256_file(absolute),
                })
            except OSError:
                continue
        evidence.append({
            "name": item["name"], "version": item["version"],
            "license_metadata": item["license_declared"],
            "license_files_in_installed_distribution": sorted(licenses, key=lambda x: x["installed_relative_path"]),
            "embedded_in_exe_not_individually_verified": True,
        })
    return evidence


def build_audit(exe: Path, reader, root_versions=None) -> dict:
    if not exe.is_file() or exe.suffix.lower() != ".exe":
        raise ValueError("Windows portable EXE not found")
    archive = inspect_archive(reader)
    license_evidence = gather_installed_license_evidence(root_versions)
    return {
        "format": "code_checker_p0d_frozen_archive_audit_v1",
        "exe": exe.name,
        "exe_bytes": exe.stat().st_size,
        "exe_sha256": sha256_file(exe),
        "archive": archive,
        "python_build_distributions": license_evidence,
        "license_text_evidence_found": sum(len(x["license_files_in_installed_distribution"]) for x in license_evidence),
        "known_unresolved_review_gates": [
            "Manual mapping of every actual bundled entry to package owner and applicable license text",
            "Bundled Python interpreter and CPython standard library license/NOTICE review",
            "Tcl/Tk interpreter, resources, system/VC runtime DLL provenance and notices",
            "Review PyInstaller bootloader exception and all other dependencies",
            "Generate customer-ready license and attribution notice, inspected by a human",
            "Real clean Windows SmartScreen/Defender, packet capture, PDF visual inspection",
        ],
        "license_compliance_certified": False,
        "third_party_notice_ready_to_distribute": False,
        "customer_release_ready": False,
        "status": "BINARY_MANIFEST_OBSERVED_LICENSE_REVIEW_REQUIRED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only PyInstaller EXE components and license evidence")
    parser.add_argument("--exe", required=True)
    parser.add_argument("--out", required=True, help="Local ignored JSON manifest path")
    args = parser.parse_args()
    try:
        from PyInstaller.archive.readers import CArchiveReader
        exe = Path(args.exe).expanduser().resolve(strict=True)
        output = Path(args.out).expanduser()
        if output.exists() or output.is_symlink():
            raise FileExistsError("Audit output will not be overwritten")
        if not output.parent.is_dir():
            raise ValueError("Create a local audit output folder first")
        evidence = build_audit(exe, CArchiveReader(str(exe)))
        if evidence["archive"]["archive_read_errors"]:
            raise ValueError("Embedded Python archive incomplete, refusing audit PASS")
        if not evidence["archive"]["framework_markers"]["python_runtime"]:
            raise ValueError("Python runtime DLL is missing from embedded manifest")
        output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        print("FROZEN_EXE_ARCHIVE_AUDIT_PASS")
        print("EXE_SHA256=" + evidence["exe_sha256"])
        print("CARCHIVE_ENTRIES=" + str(evidence["archive"]["top_level_count"]))
        print("PYZ_MODULES=" + str(evidence["archive"]["pyz_module_count"]))
        print("NATIVE_RUNTIME_PRESENT=" + str(evidence["archive"]["framework_markers"]["native_binary_present"]))
        print("TCL_TK_BINARY_MARKER=" + str(evidence["archive"]["framework_markers"]["tcl_or_tk"]))
        print("INSTALLED_BUILD_DISTRIBUTIONS=" + str(len(evidence["python_build_distributions"])))
        print("INSTALLED_LICENSE_TEXT_FILES=" + str(evidence["license_text_evidence_found"]))
        print("NOTICE_REVIEW=REQUIRED")
        print("COMMERCIAL_RELEASE=NOT_APPROVED")
        return 0
    except (ValueError, OSError, ImportError, FileExistsError) as exc:
        print("FROZEN_EXE_ARCHIVE_AUDIT_FAILED=" + type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
