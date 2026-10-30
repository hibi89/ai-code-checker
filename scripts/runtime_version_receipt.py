"""Local exact-frozen EXE Tcl/Tk version receipt; NOT a license certificate.

Only the already-running frozen application reads its own executable and Tk
interpreter versions. No network, code scan, customer input, notice or EXE
upload. Receipt stays in an explicit fresh developer-local file.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path

FORMAT = "code_checker_frozen_tcl_tk_version_receipt_v1"
MAX_EXE_BYTES = 256 * 1024 * 1024
MAX_RECEIPT_BYTES = 4096
VERSION = re.compile(r"[0-9]{1,2}\.[0-9]{1,2}(?:\.[0-9]{1,3})?(?:[ab][0-9]{1,3})?\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
FLAGS = (
    "installed_license_text_or_exact_binary_origin_proven",
    "copyright_and_redistribution_rights_verified",
    "customer_notice_ready",
    "customer_release_ready",
)


def _exe_fingerprint(exe: Path) -> tuple[int, str]:
    if exe.is_symlink():
        raise ValueError("linked executable is not evidence")
    with exe.open("rb") as stream:
        initial = os.fstat(stream.fileno())
        if not stat.S_ISREG(initial.st_mode) or not 0 < initial.st_size <= MAX_EXE_BYTES:
            raise ValueError("missing or oversized executable")
        digest = hashlib.sha256()
        length = 0
        while chunk := stream.read(1024 * 1024):
            length += len(chunk)
            if length > MAX_EXE_BYTES:
                raise ValueError("oversized executable")
            digest.update(chunk)
        after = os.fstat(stream.fileno())
    if (length != initial.st_size or initial.st_size != after.st_size
            or initial.st_mtime_ns != after.st_mtime_ns
            or exe.is_symlink() or exe.stat().st_size != length):
        raise ValueError("executable changed during receipt")
    return length, digest.hexdigest()


def capture_receipt(exe: Path, tk_factory, *, frozen: bool, python_version: str) -> dict:
    """Read actual Tcl/Tk patchlevels from live Tk interpreter in frozen EXE."""
    if not frozen or not exe.is_file() or not VERSION.fullmatch(python_version):
        raise ValueError("an actual frozen Windows runtime is required")
    root = tk_factory()
    try:
        root.withdraw()
        tcl_version = str(root.tk.call("info", "patchlevel"))
        tk_version = str(root.tk.call("set", "tk_patchLevel"))
    finally:
        root.destroy()
    if not VERSION.fullmatch(tcl_version) or not VERSION.fullmatch(tk_version):
        raise ValueError("invalid runtime Tcl/Tk patchlevel")
    size, sha = _exe_fingerprint(exe)
    return {
        "format": FORMAT,
        "exe_sha256": sha,
        "exe_bytes": size,
        "frozen_process_runtime_observed": True,
        "python_runtime_version": python_version,
        "tcl_runtime_patchlevel": tcl_version,
        "tk_runtime_patchlevel": tk_version,
        **{name: False for name in FLAGS},
    }


def verify_receipt(receipt: dict, exe: Path) -> None:
    required = {
        "format", "exe_sha256", "exe_bytes", "frozen_process_runtime_observed",
        "python_runtime_version", "tcl_runtime_patchlevel", "tk_runtime_patchlevel",
        *FLAGS,
    }
    if (not isinstance(receipt, dict) or set(receipt) != required
            or receipt["format"] != FORMAT
            or receipt["frozen_process_runtime_observed"] is not True
            or any(receipt.get(name) is not False for name in FLAGS)
            or not isinstance(receipt["exe_sha256"], str)
            or SHA256.fullmatch(receipt["exe_sha256"]) is None
            or type(receipt["exe_bytes"]) is not int
            or any(not isinstance(receipt[key], str) or VERSION.fullmatch(receipt[key]) is None
                   for key in ("python_runtime_version",
                               "tcl_runtime_patchlevel", "tk_runtime_patchlevel"))):
        raise ValueError("incomplete, invalid or prematurely approved receipt")
    size, sha = _exe_fingerprint(exe)
    if size != receipt["exe_bytes"] or sha != receipt["exe_sha256"]:
        raise ValueError("receipt does not match exact executable")


def write_frozen_receipt(output: Path) -> None:
    if not getattr(sys, "frozen", False) or not hasattr(sys, "_MEIPASS"):
        raise ValueError("only the frozen application may write this receipt")
    if (output.exists() or output.is_symlink()
            or output.parent == Path(".") or not output.parent.is_dir()
            or output.parent.is_symlink()):
        raise ValueError("output must be a fresh developer-local file")
    import tkinter as tk
    exe = Path(sys.executable)
    receipt = capture_receipt(
        exe, tk.Tk, frozen=True,
        python_version=".".join(map(str, sys.version_info[:3])))
    verify_receipt(receipt, exe)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, ensure_ascii=True, sort_keys=True, indent=2)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if len(args) == 2 and args[0] == "--write-frozen":
            write_frozen_receipt(Path(args[1]))
            return 0
        if len(args) == 3 and args[0] == "--verify":
            path = Path(args[1])
            if (path.is_symlink() or not path.is_file()
                    or not 0 < path.stat().st_size <= MAX_RECEIPT_BYTES):
                raise ValueError("unsafe receipt")
            receipt = json.loads(path.read_text(encoding="utf-8"))
            verify_receipt(receipt, Path(args[2]))
            print("EXACT_FROZEN_RUNTIME_VERSION_RECEIPT_PASS")
            print("FROZEN_TCL_PATCHLEVEL=" + receipt["tcl_runtime_patchlevel"])
            print("FROZEN_TK_PATCHLEVEL=" + receipt["tk_runtime_patchlevel"])
            print("ORIGINAL_TCL_TK_LICENSE_AND_OWNER=UNVERIFIED")
            print("CUSTOMER_RELEASE_READY=False")
            return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
