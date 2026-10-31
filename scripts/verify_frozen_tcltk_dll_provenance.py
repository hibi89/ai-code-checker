"""Hash exact frozen Tcl/Tk DLLs against unique Analysis TOC build source.

No executable/code execution, extraction to disk, network, or legal approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from scripts.build_notice_review_queue import _verify_exe
from scripts.reconcile_native_build import MAX_NATIVE_BYTES, normalize, parse_analysis_toc, sha_file
from scripts.runtime_version_receipt import MAX_RECEIPT_BYTES, verify_receipt
from scripts.verify_upstream_tcl_tk_license import _safe_read

FORMAT = "code_checker_frozen_tcltk_dll_provenance_v1"
DLL_NAME = re.compile(r"^(tcl|tk)[0-9]{2,3}t?\.dll$", re.IGNORECASE)
MAX_AUDIT = 16 * 1024 * 1024


def verify_dlls(exe: Path, audit: dict, receipt: dict,
                toc: list[tuple[str, Path, str]], reader) -> dict:
    if not isinstance(audit, dict) or any(audit.get(k) is not False for k in (
        "customer_release_ready", "license_compliance_certified",
        "third_party_notice_ready_to_distribute",
    )):
        raise ValueError("Unexpected or prematurely approved EXE audit")
    sha = audit.get("exe_sha256")
    if not isinstance(sha, str) or not re.fullmatch(r"[a-f0-9]{64}", sha):
        raise ValueError("Invalid EXE fingerprint")
    size = _verify_exe(exe, sha)
    if audit.get("exe_bytes") != size:
        raise ValueError("EXE bytes differ from CArchive audit")
    verify_receipt(receipt, exe)
    if receipt["exe_sha256"] != sha or receipt["exe_bytes"] != size:
        raise ValueError("Live Tcl/Tk receipt belongs to another EXE")
    entries = audit.get("archive", {}).get("top_level")
    if not isinstance(entries, list) or not hasattr(reader, "toc"):
        raise ValueError("Missing archive manifest")
    names = [row["name"] for row in entries]
    if len(set(names)) != len(names) or set(names) != set(reader.toc):
        raise ValueError("Actual CArchive entries differ from audit")
    dlls = []
    for role in ("tcl", "tk"):
        matches = [name for name in names if DLL_NAME.fullmatch(name)
                   and DLL_NAME.fullmatch(name).group(1).lower() == role]
        if len(matches) != 1:
            raise ValueError("Missing/ambiguous frozen " + role + " DLL")
        name = matches[0]
        sources = [(src, kind) for dest, src, kind in toc if dest == normalize(name)]
        if len(sources) != 1 or sources[0][1] != "BINARY":
            raise ValueError("Missing/ambiguous exact build source for frozen DLL")
        src = sources[0][0]
        if src.is_symlink() or not src.is_file():
            raise ValueError("Linked or unavailable build source")
        src_sha = sha_file(src, MAX_NATIVE_BYTES)
        if src_sha is None:
            raise ValueError("Unhashable source DLL")
        binary = reader.extract(name)
        if not isinstance(binary, bytes) or not 0 < len(binary) <= MAX_NATIVE_BYTES:
            raise ValueError("No bounded DLL bytes in the EXE")
        embed_sha = hashlib.sha256(binary).hexdigest()
        if embed_sha != src_sha:
            raise ValueError("Actual EXE DLL bytes differ from build source")
        dlls.append({
            "role": role, "archive_entry": name,
            "embedded_bytes": len(binary), "sha256": embed_sha,
            "exact_build_source_bytes_match": True,
            "vendor_and_redistribution_rights_verified": False,
        })
    _verify_exe(exe, sha)
    return {
        "format": FORMAT, "exe_sha256": sha, "exe_bytes": size,
        "frozen_tcl_patchlevel": receipt["tcl_runtime_patchlevel"],
        "frozen_tk_patchlevel": receipt["tk_runtime_patchlevel"],
        "dlls": dlls, "exact_embedded_build_source_bytes_match": True,
        "installed_original_license_text_verified": False,
        "vendor_binary_ownership_verified": False, "third_party_notice_ready": False,
        "license_compliance_certified": False, "customer_release_ready": False,
        "status": "DLL_BYTES_ONLY_RETAIL_RELEASE_BLOCKED",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Actual DLL bytes vs local Windows build source; not legal approval")
    for key in ("exe", "audit", "runtime-receipt", "analysis-toc", "out"):
        p.add_argument("--" + key, type=Path, required=True)
    args = p.parse_args(argv)
    inputs = [args.exe, args.audit, args.runtime_receipt, args.analysis_toc]
    try:
        if (args.out.exists() or args.out.is_symlink() or not args.out.parent.is_dir()
                or args.out.parent.is_symlink() or args.out in inputs or len(set(inputs)) != 4):
            raise ValueError("Fresh private distinct output required")
        from PyInstaller.archive.readers import CArchiveReader
        audit = json.loads(_safe_read(args.audit, MAX_AUDIT))
        receipt = json.loads(_safe_read(args.runtime_receipt, MAX_RECEIPT_BYTES))
        toc = parse_analysis_toc(args.analysis_toc)
        result = verify_dlls(args.exe, audit, receipt, toc, CArchiveReader(str(args.exe)))
        with args.out.open("x", encoding="utf-8", newline="\n") as f:
            json.dump(result, f, sort_keys=True, indent=2)
        print("EXACT_TCL_TK_FROZEN_DLL_BYTES_MATCH_BUILD_SOURCES")
        print("EXE_SHA256=" + result["exe_sha256"])
        print("TCL_TK_DLL_COUNT=2")
        print("COPYRIGHT_NOTICE_AND_RELEASE_APPROVED=False")
        return 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError,
            RuntimeError, ImportError, json.JSONDecodeError):
        print("EXACT_TCL_TK_FROZEN_DLL_PROVENANCE_INVALID")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
