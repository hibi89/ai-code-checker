"""Stage ORIGINAL local build-environment runtime license candidates for human review.

One exact, SHA-256 verified EXE -> installed CPython/Tcl/Tk/PyInstaller source
candidate bytes and hashes. Candidate bytes are never put into GitHub, a CI
artifact, the packaged EXE, or a customer NOTICE by this tool. License terms
and binary owners MUST still be reviewed by a human before redistribution.

No network, package install, untrusted code execution or arbitrary-file input.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
import os
import re
import stat
import sys
from pathlib import Path

from scripts.build_notice_review_queue import _verify_exe
from scripts.runtime_version_receipt import MAX_RECEIPT_BYTES, verify_receipt

FORMAT = "code_checker_runtime_original_license_candidates_v1"
MAX_ORIGINAL_BYTES = 1024 * 1024
MAX_PYINSTALLER_CANDIDATES = 16
_REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_KNOWN_LICENSE_NAMES = re.compile(
    r"(?i)^(?:license|licence|copying|copyright|notice)(?:[._-].*)?$"
)
_TCL_DIR = re.compile(r"^(?:tcl|tk)\d+(?:\.\d+)*$", re.IGNORECASE)


def _safe_regular_file(path: Path, root: Path) -> bytes | None:
    """Bounded byte read from a non-linked installed source under exact root."""
    try:
        if root.is_symlink() or not root.is_dir():
            return None
        relative = path.relative_to(root)
        if not relative.parts or any(part in (".", "..") for part in relative.parts):
            return None
        current = root
        for component in relative.parts[:-1]:
            current = current / component
            stat_info = current.lstat()
            if (not stat.S_ISDIR(stat_info.st_mode)
                    or getattr(stat_info, "st_file_attributes", 0) & _REPARSE):
                return None
        observed = path.lstat()
        if (not stat.S_ISREG(observed.st_mode)
                or getattr(observed, "st_file_attributes", 0) & _REPARSE
                or not 0 < observed.st_size <= MAX_ORIGINAL_BYTES):
            return None
        before = (observed.st_dev, observed.st_ino, observed.st_size, observed.st_mtime_ns)
        # Open the inspected file itself, not a newly resolved path. The
        # second identity check rejects a replace-between-lstat-and-open race.
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        try:
            opened = os.fstat(fd)
            opened_id = (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
            if (not stat.S_ISREG(opened.st_mode)
                    or getattr(opened, "st_file_attributes", 0) & _REPARSE
                    or path.is_symlink() or opened_id != before):
                return None
            with os.fdopen(fd, "rb", closefd=False) as stream:
                raw = stream.read(MAX_ORIGINAL_BYTES + 1)
            after = os.fstat(fd)
            on_disk = path.lstat()
            after_id = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            disk_id = (on_disk.st_dev, on_disk.st_ino, on_disk.st_size, on_disk.st_mtime_ns)
            if (len(raw) != observed.st_size or len(raw) > MAX_ORIGINAL_BYTES
                    or path.is_symlink() or after_id != before or disk_id != before):
                return None
            return raw
        finally:
            os.close(fd)
    except (OSError, ValueError):
        return None


def _runtime_candidates(root: Path) -> tuple[dict[str, tuple[str, bytes]], list[str]]:
    """Inspect only bounded standard Python/Tcl/Tk install layouts.

    Some Windows distributions put tcl8.x in Lib/, not the top-level tcl/
    tree. Distinct installed source contents are AMBIGUOUS, not silently
    picked by whichever path is enumerated first.
    """
    found: dict[str, tuple[str, bytes]] = {}
    for name in ("LICENSE.txt", "LICENSE"):
        raw = _safe_regular_file(root / name, root)
        if raw is not None:
            found["cpython"] = (name, raw)
            break
    candidate_roots = (
        root / "tcl", root / "Lib", root / "Lib" / "tcl", root,
    )
    alternatives: dict[str, list[tuple[str, bytes]]] = {"tcl": [], "tk": []}
    for location in candidate_roots:
        try:
            children = list(location.iterdir())
        except OSError:
            children = []
        if len(children) > 256:
            # An expected installation directory is not necessarily small;
            # skip it rather than scanning a large unrelated tree.
            continue
        for directory in sorted(children, key=lambda p: p.name.casefold()):
            if not _TCL_DIR.fullmatch(directory.name):
                continue
            prefix = "tcl" if directory.name.lower().startswith("tcl") else "tk"
            raw = _safe_regular_file(directory / "license.terms", root)
            if raw is not None:
                relative = (directory / "license.terms").relative_to(root).as_posix()
                alternatives[prefix].append((relative, raw))
            # Some installed Tcl library trees include the matching Tk
            # directory beneath Tcl; inspect only a fixed sibling pattern.
            if prefix == "tcl":
                try:
                    tk_dirs = list(directory.iterdir())
                except OSError:
                    tk_dirs = []
                if len(tk_dirs) > 128:
                    continue
                for subdir in sorted(tk_dirs, key=lambda p: p.name.casefold()):
                    if not _TCL_DIR.fullmatch(subdir.name) or not subdir.name.lower().startswith("tk"):
                        continue
                    raw = _safe_regular_file(subdir / "license.terms", root)
                    if raw is not None:
                        relative = (subdir / "license.terms").relative_to(root).as_posix()
                        alternatives["tk"].append((relative, raw))
    ambiguities = []
    for role in ("tcl", "tk"):
        matches = alternatives[role]
        if not matches:
            continue
        by_digest = {hashlib.sha256(raw).hexdigest() for _, raw in matches}
        if len(by_digest) != 1:
            ambiguities.append(role)
            continue
        found[role] = min(matches, key=lambda item: (len(item[0]), item[0].casefold()))
    return found, ambiguities


def _pyinstaller_candidates(dist) -> list[tuple[str, bytes]]:
    if dist is None or str(dist.version) != "6.22.3":
        return []
    records = []
    for value in dist.files or ():
        path = Path(str(value).replace("\\", "/"))
        if (path.is_absolute() or ".." in path.parts
                or len(path.parts) > 12 or len(str(path)) > 512
                or not _KNOWN_LICENSE_NAMES.fullmatch(path.name)):
            continue
        found = Path(dist.locate_file(value))
        # Only read members listed in this exact installed RECORD, never scan
        # the whole build machine or follow linked source locations.
        base = Path(dist.locate_file(""))
        raw = _safe_regular_file(found, base)
        if raw is not None:
            records.append((path.name, raw))
        if len(records) > MAX_PYINSTALLER_CANDIDATES:
            raise ValueError("Excessive PyInstaller original LICENSE candidates")
    return records


def stage_candidates(exe: Path, audit: dict, python_root: Path, dist, out_dir: Path,
                     runtime_receipt: dict | None = None) -> dict:
    """Stage originals as exact bytes, metadata only for downstream reviewers."""
    if (not isinstance(audit, dict)
            or audit.get("format") != "code_checker_p0d_frozen_archive_audit_v1"
            or audit.get("customer_release_ready") is not False
            or audit.get("license_compliance_certified") is not False
            or audit.get("third_party_notice_ready_to_distribute") is not False):
        raise ValueError("Invalid or preapproved EXE manifest")
    if (not isinstance(audit.get("exe_sha256"), str)
            or re.fullmatch("[0-9a-f]{64}", audit["exe_sha256"]) is None):
        raise ValueError("Missing exact EXE identity")
    exe_size = _verify_exe(exe, audit["exe_sha256"])
    if (out_dir.exists() or out_dir.is_symlink() or not out_dir.parent.is_dir()
            or out_dir.parent.is_symlink() or not python_root.is_dir()
            or python_root.is_symlink()):
        raise ValueError("New local output and non-linked runtime root required")
    if (out_dir.parent.resolve() == python_root.resolve()
            or python_root.resolve() in out_dir.parent.resolve().parents):
        raise ValueError("Output may not modify installed runtime tree")

    # Bind version evidence observed from the actual frozen Tk interpreter to
    # this exact EXE before creating or writing any license candidate files.
    if runtime_receipt is not None:
        verify_receipt(runtime_receipt, exe)
    root_sources, ambiguous_source_roles = _runtime_candidates(python_root)
    py_sources = _pyinstaller_candidates(dist)
    # The exact build distribution may have no RECORD listed license text.
    # Leave missing entries unresolved instead of generating substitute words.
    source_groups: dict[str, list[tuple[str, bytes]]] = {
        role: ([root_sources[role]] if role in root_sources else [])
        for role in ("cpython", "tcl", "tk")
    }
    source_groups["pyinstaller"] = py_sources
    out_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
    rows = []
    for role in ("cpython", "tcl", "tk", "pyinstaller"):
        for idx, (safe_name, raw) in enumerate(source_groups[role], start=1):
            suffix = f"{role}-{idx:02d}.original"
            target = out_dir / suffix
            with target.open("xb") as fp:
                fp.write(raw)
            if hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(raw).digest():
                raise ValueError("Staged source bytes failed integrity comparison")
            rows.append({
                "role": role,
                "candidate_file": suffix,
                "installed_source_basename": Path(safe_name).name,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "source_kind": ("installed_pyinstaller_record" if role == "pyinstaller"
                                else "installed_python_runtime_tree"),
                "corresponding_frozen_entry_or_copyright_owner_verified": False,
                "human_review_required": True,
            })
    _verify_exe(exe, audit["exe_sha256"])
    counts = {role: sum(row["role"] == role for row in rows)
              for role in source_groups}
    missing = [role for role, count in counts.items() if count == 0]
    report = {
        "format": FORMAT,
        "exe_sha256": audit["exe_sha256"],
        "exe_bytes": exe_size,
        "runtime_python_version": ".".join(map(str, sys.version_info[:3])),
        "build_pyinstaller_version": (str(dist.version) if dist is not None else None),
        "frozen_tcl_tk_runtime_receipt_verified": runtime_receipt is not None,
        "frozen_tcl_patchlevel": (runtime_receipt["tcl_runtime_patchlevel"]
                                  if runtime_receipt is not None else None),
        "frozen_tk_patchlevel": (runtime_receipt["tk_runtime_patchlevel"]
                                 if runtime_receipt is not None else None),
        "exact_runtime_version_is_not_license_source_or_owner_proof": True,
        "original_candidate_file_count": len(rows),
        "source_role_counts": counts,
        "missing_source_roles": missing,
        "ambiguous_source_roles": ambiguous_source_roles,
        "originals": rows,
        "candidate_files_stored_only_in_local_build_folder": True,
        "actual_exe_sha256_confirmed": True,
        "build_runtime_source_cannot_prove_frozen_binary_ownership": True,
        "third_party_license_notice_human_review_required": True,
        "copyright_and_redistribution_rights_verified": False,
        "customer_notice_ready": False,
        "customer_release_ready": False,
        "status": "BUILD_RUNTIME_ORIGINALS_STAGED_RETAIL_BLOCKED",
    }
    with (out_dir / "manifest.json").open("x", encoding="utf-8") as fp:
        json.dump(report, fp, ensure_ascii=False, indent=2, sort_keys=True)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage original local Windows runtime licenses (review only)")
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--python-root", type=Path, default=Path(sys.base_prefix))
    parser.add_argument("--runtime-receipt", type=Path, default=None)
    args = parser.parse_args()
    try:
        source = args.audit
        if (source.is_symlink() or not source.is_file()
                or not 0 < source.stat().st_size <= 16 * 1024 * 1024):
            raise ValueError("Missing, linked or oversized frozen EXE audit")
        audit = json.loads(source.read_text(encoding="utf-8"))
        receipt = None
        if args.runtime_receipt is not None:
            evidence = args.runtime_receipt
            if (evidence.is_symlink() or not evidence.is_file()
                    or not 0 < evidence.stat().st_size <= MAX_RECEIPT_BYTES):
                raise ValueError("Missing, linked or oversized runtime receipt")
            receipt = json.loads(evidence.read_text(encoding="utf-8"))
        dist = metadata.distribution("pyinstaller")
        report = stage_candidates(
            args.exe, audit, args.python_root, dist, args.out_dir, receipt)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError,
            metadata.PackageNotFoundError):
        print("LOCAL_RUNTIME_ORIGINAL_LICENSE_STAGE_INVALID")
        return 1
    print("LOCAL_RUNTIME_ORIGINAL_LICENSE_STAGE_PASS")
    print("ORIGINAL_LOCAL_FILE_CANDIDATES=" + str(report["original_candidate_file_count"]))
    print("FROZEN_RUNTIME_VERSION_HASH_BOUND=" +
          str(report["frozen_tcl_tk_runtime_receipt_verified"]))
    print("CPYTHON_SOURCE_FILES=" + str(report["source_role_counts"]["cpython"]))
    print("TCL_SOURCE_FILES=" + str(report["source_role_counts"]["tcl"]))
    print("TK_SOURCE_FILES=" + str(report["source_role_counts"]["tk"]))
    print("PYINSTALLER_SOURCE_FILES=" + str(report["source_role_counts"]["pyinstaller"]))
    print("MISSING_SOURCE_ROLE_COUNT=" + str(len(report["missing_source_roles"])))
    print("AMBIGUOUS_SOURCE_ROLE_COUNT=" + str(len(report["ambiguous_source_roles"])))
    print("COPYRIGHT_AND_REDISTRIBUTION_APPROVED=False")
    print("CUSTOMER_NOTICE_READY=False")
    print("CUSTOMER_RELEASE_READY=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
