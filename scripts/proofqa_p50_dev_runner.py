"""Development-only process boundary for PROOFQA AX P50 (not an OS sandbox).

Only the trusted PROOFQA Python adapter runs; customer ZIP scripts never run.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from input_safety import validate_offline_input_path
from output_safety import validate_output_location

_ALLOWED_ENV = (
    "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "TEMP", "TMP",
    "HOME", "USERPROFILE", "LOCALAPPDATA", "APPDATA",
    "LANG", "LC_ALL", "OneDrive", "OneDriveConsumer",
    "OneDriveCommercial",
)


def run_dev_process(source_zip: str | Path, output_root: str | Path) -> int:
    source = validate_offline_input_path(source_zip)
    destination = validate_output_location(output_root)
    adapter = Path(__file__).resolve().parents[1] / "proofqa_p50.py"
    if not adapter.is_file():
        raise FileNotFoundError("PROOFQA P50 trusted local adapter is missing.")
    env = {key: value for key, value in os.environ.items() if key in _ALLOWED_ENV}
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    with tempfile.TemporaryDirectory(prefix="proofqa-dev-") as workdir:
        try:
            process = subprocess.run(
                [sys.executable, "-E", "-s", "-B", "-X", "utf8", str(adapter),
                 str(source), "--output-dir", str(destination)],
                cwd=workdir, env=env, capture_output=True,
                text=True, encoding="utf-8", timeout=120, check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired:
            print("BLOCKED: P50 개발용 정적 분석 시간 한도 초과.", file=sys.stderr)
            return 2
    if process.stdout:
        print(process.stdout, end="")
    if process.stderr:
        print(process.stderr, end="", file=sys.stderr)
    return process.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="PROOFQA P50 isolated developer PROCESS (not kernel sandbox)")
    parser.add_argument("project_zip")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    try:
        return run_dev_process(args.project_zip, args.output_dir)
    except (ValueError, OSError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
