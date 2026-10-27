"""P1-V: reconcile Windows frozen-EXE NOTICE review gaps from local build evidence.

This is a *review queue*, not a redistribution or legal certification. It joins
P0-D through P0-H by actual EXE SHA and metadata accounting, never guesses
binary copyright ownership from a file name. No code execution or network IO.
The detailed original LICENSE draft remains local and is not copied here.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from scripts.map_frozen_licenses import canonicalize_name

FORMAT = "code_checker_p1v_notice_gap_ledger_v1"
MAX_INPUT_BYTES = 16 * 1024 * 1024
MAX_ROWS = 30000
_CLAIM_MAPPINGS = {
    "installed_dist_unique_name_claim",
    "ambiguous_dist_name_claim",
    "installed_native_exact_relative_filename_candidate",
    "ambiguous_native_filename",
}


def _blocked(obj: dict, keys: tuple[str, ...]) -> None:
    if not isinstance(obj, dict) or any(obj.get(key) is not False for key in keys):
        raise ValueError("Previous evidence has invalid release/certification flags")


def reconcile_notice_gaps(audit: dict, mapping: dict, native: dict,
                          exe_toc: dict, pkg_toc: dict) -> dict:
    """Check evidence identity and exhaustive accounting before listing tasks."""
    _blocked(audit, ("customer_release_ready", "license_compliance_certified",
                     "third_party_notice_ready_to_distribute"))
    _blocked(mapping, ("customer_release_ready", "license_compliance_certified",
                       "third_party_notice_ready_to_distribute",
                       "embedded_binary_hash_matches_checked"))
    _blocked(native, ("customer_release_ready", "legal_notice_approved"))
    _blocked(exe_toc, ("customer_release_ready", "legal_notice_approved",
                       "license_compliance_certified"))
    _blocked(pkg_toc, ("customer_release_ready", "legal_notice_approved",
                       "license_compliance_certified"))
    sha = audit.get("exe_sha256")
    if (not isinstance(sha, str) or re.fullmatch(r"[a-f0-9]{64}", sha) is None
            or any(doc.get("exe_sha256") != sha
                   for doc in (mapping, native, exe_toc, pkg_toc))):
        raise ValueError("Five evidence stages do not refer to one EXE")

    archive = audit["archive"]
    # P0-E normalizes Windows archive separators in _safe_name; compare
    # canonical archive-relative entry names, never OS absolute paths.
    actual = ([("CArchive", row["name"].replace("\\", "/"))
               for row in archive["top_level"]]
              + [("PYZ", row["module"].replace("\\", "/"))
                 for row in archive["pyz_modules"]])
    rows = mapping["entries"]
    if not 0 < len(actual) <= MAX_ROWS or len(rows) != len(actual):
        raise ValueError("Missing archive ownership-candidate rows")
    actual_set = set(actual)
    mapped_set = {(row["kind"], row["name"]) for row in rows}
    if (len(actual_set) != len(actual) or len(mapped_set) != len(rows)
            or actual_set != mapped_set or mapping["total_rows"] != len(rows)
            or mapping["archive_entries"] != len(archive["top_level"])
            or mapping["pyz_modules"] != len(archive["pyz_modules"])
            or mapping["all_items_accounted_for_in_metadata"] is not True):
        raise ValueError("Ownership mapping does not cover exact observed EXE names")
    counts = Counter(row["mapping"] for row in rows)
    if (dict(sorted(counts.items())) != mapping["mapping_counts"]
            or sum(num for category, num in counts.items()
                   if category.startswith("unresolved")) != mapping["unresolved_count"]):
        raise ValueError("Ownership category accounting differs from actual rows")

    candidates = mapping["installed_dist_candidates"]
    if (not isinstance(candidates, list) or len(candidates) != len(set(candidates))
            or len(candidates) != mapping["candidate_dist_count"]
            or any(not isinstance(name, str) or name != canonicalize_name(name)
                   for name in candidates)):
        raise ValueError("Invalid installed distribution candidate names")
    identified = {canonicalize_name(x)
                  for row in rows if row["mapping"] in _CLAIM_MAPPINGS
                  for x in row["owner_candidates"]}
    if identified != set(candidates):
        raise ValueError("Distribution candidates differ from mapped entries")

    distributions = audit["python_build_distributions"]
    index = {canonicalize_name(d["name"]): d for d in distributions}
    if len(index) != len(distributions):
        raise ValueError("Duplicate installed distribution")
    expected_selection = set(candidates) | {"pyinstaller"}
    draft = mapping["license_text_draft"]
    selected = draft["selected_installed_distributions"]
    if (not isinstance(selected, list) or len(selected) != len(set(selected))
            or set(selected) != expected_selection or not set(selected) <= set(index)
            or draft["draft_for_distribution"] is not False
            or draft["human_legal_review_pending"] is not True
            or draft["selected_dists_without_claim_of_exe_inclusion"] is not True):
        raise ValueError("Original license draft did not cover expected build candidates")
    missing = draft["unavailable_or_missing_texts"]
    staged = draft["staged_original_license_files"]
    if (not isinstance(missing, list) or not all(isinstance(x, str) for x in missing)
            or type(staged) is not int or staged < 0):
        raise ValueError("License draft observation invalid")

    dist_tasks = []
    total_declared = 0
    for name in sorted(selected):
        record = index[name]
        licenses = record["license_files_in_installed_distribution"]
        if not isinstance(licenses, list):
            raise ValueError("Installed original license rows invalid")
        for item in licenses:
            digest = item["sha256"]
            if (not isinstance(digest, str) or re.fullmatch(r"[a-f0-9]{64}", digest) is None
                    or type(item["bytes"]) is not int
                    or not 0 < item["bytes"] <= 1024 * 1024):
                raise ValueError("Original license metadata malformed or duplicate")
        total_declared += len(licenses)
        dist_tasks.append({
            "candidate_distribution": name,
            "installed_version": str(record["version"]),
            "metadata_license_label": str(record["license_metadata"]),
            "original_license_file_metadata_count": len(licenses),
            "human_original_text_and_notice_review": "REQUIRED",
            "binary_owner_and_inclusion_proven": False,
        })
    if staged > total_declared:
        raise ValueError("More staged originals than installed metadata recorded")

    unknown = [row for row in rows if row["mapping"].startswith("unresolved")]
    native_rows = native["records"]
    if (len(native_rows) != native["previous_unresolved_archive_entries"]
            or native["previous_unresolved_archive_entries"] != len(unknown)
            or {row["name"] for row in native_rows} != {row["name"] for row in unknown}
            or len({row["name"] for row in native_rows}) != len(native_rows)
            or native["all_entries_counted"] is not True
            or native["source_path_not_a_license_or_vendor_proof"] is not True):
        raise ValueError("Native provenance must account for exactly the unresolved names")

    not_unique = [row for row in native_rows
                  if row["build_record_evidence"] != "recorded_build_source_path_candidate"]
    if (len(not_unique) != native["not_uniquely_recorded_in_build_toc"]
            or len(exe_toc["records"]) != len(not_unique)
            or exe_toc["previously_not_unique_analysis_claims"] != len(not_unique)
            or (exe_toc["exe_toc_entry_claims"]
                + exe_toc["ambiguous_exe_toc_claims"]
                + exe_toc["without_exe_toc_claims"]) != len(not_unique)
            or {row["name"] for row in exe_toc["records"]}
               != {row["name"] for row in not_unique}
            or exe_toc["all_pending_entries_accounted_for"] is not True):
        raise ValueError("EXE-TOC accounting breaks build provenance chain")
    still_missing = [row for row in exe_toc["records"]
                     if row["exe_toc_evidence"] == "no_exe_toc_entry_claim"]
    if (len(still_missing) != exe_toc["without_exe_toc_claims"]
            or pkg_toc["previously_unmatched_exe_toc"] != len(still_missing)
            or len(pkg_toc["records"]) != len(still_missing)
            or {row["name"] for row in pkg_toc["records"]}
               != {row["name"] for row in still_missing}
            or (pkg_toc["pkg_unique_record_claims"]
                + pkg_toc["pkg_ambiguous_record_claims"]
                + pkg_toc["pkg_no_record_claims"]) != len(still_missing)
            or pkg_toc["all_prior_unmatched_accounted_for"] is not True):
        raise ValueError("PKG-TOC accounting breaks EXE provenance chain")

    tasks = [
        {"id": "installed_python_dist_licenses",
         "evidence_count": len(dist_tasks),
         "note": "Review original installed licenses and actual runtime inclusion/NOTICE rights"},
        {"id": "cpython_runtime_and_stdlib",
         "evidence_count": counts["cpython_stdlib_name_candidate"]
                          + counts["cpython_runtime_filename_candidate"],
         "note": "Confirm exact CPython binary, PSF attribution and distribution requirements"},
        {"id": "tcl_tk_scripts_and_native",
         "evidence_count": counts["tcl_tk_filename_candidate"],
         "note": "Confirm exact Tcl/Tk original rights, Tcl script resources and notices"},
        {"id": "unknown_native_resources_bootloader",
         "evidence_count": len(unknown),
         "note": "Review native/system DLL, bootloader, unresolved resource ownership and licenses"},
        {"id": "pyinstaller_bootloader_exception",
         "evidence_count": 1,
         "note": "Verify PyInstaller installed license and actual bootloader exception/obligations"},
        {"id": "microsoft_windows_vc_runtime",
         "evidence_count": counts["unresolved_native_or_system_binary"],
         "note": "Distinguish Windows system files versus redistributed Microsoft/VC components"},
        {"id": "end_user_notice_and_redistribution_signoff",
         "evidence_count": 1,
         "note": "Manually approve customer distribution NOTICE with version/copyright coverage"},
    ]
    return {
        "format": FORMAT,
        "exe_sha256": sha,
        "mapped_exe_entries": len(actual),
        "metadata_complete": True,
        "candidate_distribution_count": len(candidates),
        "selected_installed_distribution_count": len(dist_tasks),
        "declared_original_license_file_count": total_declared,
        "staged_original_license_file_count": staged,
        "missing_original_license_observation_count": len(missing),
        "distribution_review": dist_tasks,
        "unresolved_archive_entry_count": len(unknown),
        "remaining_pkg_toc_without_claim_count": pkg_toc["pkg_no_record_claims"],
        "manual_review_tasks": tasks,
        "original_license_texts_embedded_in_output": False,
        "copyright_and_binary_owners_verified": False,
        "notice_ready_to_distribute": False,
        "license_compliance_certified": False,
        "customer_release_ready": False,
        "status": "LOCAL_NOTICE_GAP_LEDGER_ONLY_HUMAN_REVIEW_REQUIRED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconcile local Windows EXE license gaps")
    for name in ("audit", "mapping", "native", "exe_toc", "pkg_toc", "out"):
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    args = parser.parse_args()
    try:
        output = args.out
        if (output.exists() or output.is_symlink() or not output.parent.is_dir()
                or any(output == getattr(args, key)
                       for key in ("audit", "mapping", "native", "exe_toc", "pkg_toc"))):
            raise ValueError("Output must be a distinct fresh local file")
        inputs = []
        for key in ("audit", "mapping", "native", "exe_toc", "pkg_toc"):
            path = getattr(args, key)
            if (not path.is_file() or path.is_symlink()
                    or not 0 < path.stat().st_size <= MAX_INPUT_BYTES):
                raise ValueError("Missing, linked or oversized evidence input")
            inputs.append(json.loads(path.read_text(encoding="utf-8")))
        result = reconcile_notice_gaps(*inputs)
        with output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, sort_keys=True, indent=2)
        print("NOTICE_REVIEW_GAP_LEDGER_PASS")
        print("EXE_METADATA_ALL_ROWS_RECONCILED=True")
        print("INSTALLED_DISTRIBUTION_CANDIDATES=" + str(result["candidate_distribution_count"]))
        print("ORIGINAL_LICENSE_FILES_STAGED=" + str(result["staged_original_license_file_count"]))
        print("ORIGINAL_LICENSE_FILE_GAPS=" + str(result["missing_original_license_observation_count"]))
        print("UNRESOLVED_ARCHIVE_NAMES=" + str(result["unresolved_archive_entry_count"]))
        print("PKG_TOC_NO_CLAIMS=" + str(result["remaining_pkg_toc_without_claim_count"]))
        print("NOTICE_READY_TO_DISTRIBUTE=False")
        print("CUSTOMER_RELEASE_READY=False")
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError, json.JSONDecodeError) as exc:
        print("NOTICE_REVIEW_GAP_LEDGER_INVALID")
        if isinstance(exc, ValueError):
            print("REVIEW_GAP_VALIDATION_REASON=" + str(exc)[:160])
        else:
            print("REVIEW_GAP_VALIDATION_ERROR_TYPE=" + type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
