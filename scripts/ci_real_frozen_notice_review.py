"""CI-only real frozen EXE -> exact-owner NOTICE review-progress exercise.

Does not mark redistribution permission, legal compliance or sales as approved.
All files remain on the local ephemeral runner; no artifact publishing.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

from scripts.track_notice_review import create_progress, summarize_progress, _read_json, MAX_QUEUE_BYTES


def check(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def main() -> int:
    if os.name != "nt":
        print("ACTUAL_BINARY_NOTICE_REVIEW_REQUIRES_WINDOWS")
        return 2
    repo = Path(__file__).resolve().parents[1]
    exe = repo / "dist-windows" / "CodeCheckerOffline.exe"
    root = repo / ".build-windows"
    queue_path = root / "notice-review-queue.json"
    template_path = root / "notice-review-progress-template.json"
    summary_path = root / "notice-review-progress-summary.json"
    for path in (exe, queue_path):
        check(path.is_file() and not path.is_symlink(), "MISSING_REAL_BINARY_OR_QUEUE")
    for path in (template_path, summary_path):
        check(not path.exists() and not path.is_symlink(),
              "REFUSE_EXISTING_PRIVATE_PROGRESS")

    queue = _read_json(queue_path, MAX_QUEUE_BYTES)
    progress = create_progress(queue, exe)
    summary = summarize_progress(queue, exe, progress)
    expected_rows = queue["unresolved_entry_count"]
    check(type(expected_rows) is int and expected_rows > 0,
          "NO_UNRESOLVED_VENDOR_RECORDS")
    check(progress["entry_count"] == expected_rows
          and summary["unresolved_entry_count"] == expected_rows,
          "INCOMPLETE_UNRESOLVED_VENDOR_ROSTER")
    check(all(row["review_stage"] == "UNREVIEWED" for row in progress["entries"]),
          "UNEXPECTED_HUMAN_REVIEW_STAGE")
    check(summary["investigation_stage_counts"]["UNREVIEWED"] == expected_rows
          and sum(summary["investigation_stage_counts"].values()) == expected_rows,
          "INCOMPLETE_PROGRESS_COUNTS")
    check(progress["exe_sha256"] == queue["exe_sha256"]
          and summary["exe_sha256"] == queue["exe_sha256"]
          and progress["queue_sha256"] == summary["queue_sha256"],
          "FOREIGN_BINARY_OR_QUEUE_PROGRESS")
    for key in ("customer_release_ready", "license_compliance_certified",
                "third_party_notice_ready", "vendor_or_binary_ownership_certified"):
        check(progress[key] is False, "PREMATURE_OWNER_APPROVAL:" + key)
    check(summary["customer_release_ready"] is False
          and summary["human_review_still_required"] is True
          and summary["original_license_and_redistribution_rights_not_certified"] is True,
          "PREMATURE_HUMAN_RELEASE")
    # A forged progress update must fail even if only one gate changes.
    forged = copy.deepcopy(progress)
    forged["customer_release_ready"] = True
    try:
        summarize_progress(queue, exe, forged)
    except ValueError:
        pass
    else:
        raise AssertionError("FORGED_RETAIL_APPROVAL_NOT_REJECTED")
    # A progress file tied to a different exact queue must fail closed.
    forged = copy.deepcopy(progress)
    forged["queue_sha256"] = "0" * 64
    try:
        summarize_progress(queue, exe, forged)
    except ValueError:
        pass
    else:
        raise AssertionError("STALENESS_NOT_REJECTED")

    for path, record in ((template_path, progress), (summary_path, summary)):
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(record, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
        check(json.loads(path.read_text(encoding="utf-8")) == record,
              "PRIVATE_PROGRESS_WRITTEN_RECORD_DIFFERENT")
    check("UNREVIEWED" in summary["investigation_stage_counts"],
          "REVIEW_COUNT_NOT_PRESENT")
    print("REAL_EXE_NOTICE_REVIEW_QUEUE_PROGRESS_PASS")
    print("EXE_SHA256=" + progress["exe_sha256"])
    print("UNRESOLVED_REVIEW_ROWS=" + str(expected_rows))
    print("HUMAN_RIGHTS_AND_BUYER_ACCEPTANCE=UNVERIFIED")
    print("CUSTOMER_RELEASE_READY=False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
