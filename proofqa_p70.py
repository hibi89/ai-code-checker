"""PROOFQA AX P70 graph evidence adapter.

Parses actual pinned Graphify graph.json. Does not run customer code, grant
permissions, or elevate static detections to confirmed vulnerabilities.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

from code_input import InputError

GRAPHIFY_VERSION = "0.9.108"
AGENT_BROWSER_VERSION = "0.43.0"
GRAPH_MAX_BYTES = 12 * 1024 * 1024
MAX_NODES = 10000
MAX_EDGES = 20000
LINE_RE = re.compile(r"^L([1-9][0-9]*)(?:\\b|$)")
ACCEPTED_CONFIDENCE = {"EXTRACTED", "INFERRED", "AMBIGUOUS", "UNKNOWN"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json_bounded(path: str | Path, *, limit: int = GRAPH_MAX_BYTES) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file() or source.is_symlink() or source.stat().st_size > limit:
        raise InputError("그래프/근거 JSON 파일의 크기 또는 타입이 안전하지 않습니다.")
    try:
        result = json.loads(source.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise InputError("그래프/근거 JSON 파싱 실패.") from exc
    if not isinstance(result, dict):
        raise InputError("JSON 최상위 객체가 아닙니다.")
    return result


def _line(value: Any) -> int | None:
    if not isinstance(value, str):
        return None
    match = LINE_RE.match(value)
    return int(match.group(1)) if match else None


def _source_name(source: Any, allowed: set[str]) -> str | None:
    """Conservatively match only uniquely named synthetic fixture code files.

    Graphify can report root-relative or absolute source_file paths. We check
    the file name against an independently digested fixture manifest, but do
    not pretend the graph token alone verifies source-line provenance.
    """
    if not isinstance(source, str) or not source or "\\x00" in source:
        return None
    clean = source.replace(chr(92), "/")
    parts = PurePosixPath(clean).parts
    if ".." in parts or not parts:
        return None
    name = parts[-1]
    return name if name in allowed else None


def validate_graph(
    graph: dict[str, Any], source_hashes: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    if not source_hashes or len(source_hashes) != len({Path(k).name for k in source_hashes}):
        raise InputError("중복되거나 비어 있는 샘플 소스 식별자.")
    allowed = set(source_hashes)
    if any(Path(k).name != k or not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,79}", k)
           or not re.fullmatch("[a-f0-9]{64}", v) for k, v in source_hashes.items()):
        raise InputError("소스 해시 매니페스트가 허용 형식이 아닙니다.")
    nodes = graph.get("nodes")
    links = graph.get("links")
    if (not isinstance(nodes, list) or not isinstance(links, list)
            or len(nodes) > MAX_NODES or len(links) > MAX_EDGES):
        raise InputError("Graphify graph.json 구조/수량 한도 오류.")
    meta = graph.get("graph") or {}
    if not isinstance(meta, dict):
        raise InputError("Graphify 메타데이터 형식 오류.")
    actual = meta.get("graphify_version")
    if actual is not None and str(actual) != GRAPHIFY_VERSION:
        raise InputError("Graphify 실행 버전과 검증 버전이 일치하지 않습니다.")
    known_ids: set[str] = set()
    checked_nodes: list[dict[str, Any]] = []
    for raw in nodes:
        if not isinstance(raw, dict) or not isinstance(raw.get("id"), (str, int)):
            raise InputError("그래프 노드 ID/형식 오류.")
        key = str(raw["id"])
        if key in known_ids:
            raise InputError("Graphify 중복 노드 ID.")
        known_ids.add(key)
        name = _source_name(raw.get("source_file"), allowed)
        if name is None:
            continue
        row = {
            "id": key, "source_path": name,
            "label": str(raw.get("label", ""))[:160],
            "line": _line(raw.get("source_location")),
            "file_type": str(raw.get("file_type", "unknown")),
        }
        checked_nodes.append(row)
    checked_links = []
    for edge in links:
        if not isinstance(edge, dict) or str(edge.get("source")) not in known_ids or str(edge.get("target")) not in known_ids:
            raise InputError("Graphify 링크가 없는 노드 또는 잘못된 형식을 참조합니다.")
        confidence = str(edge.get("confidence", "UNKNOWN")).upper()
        if confidence not in ACCEPTED_CONFIDENCE:
            confidence = "UNKNOWN"
        checked_links.append({
            "source": str(edge["source"]), "target": str(edge["target"]),
            "relation": str(edge.get("relation", "unclassified"))[:90],
            "confidence": confidence,
        })
    counts = {}
    for suffix in (".py", ".js", ".sql"):
        present = [n for n in checked_nodes if n["source_path"].endswith(suffix)
                   and n["line"] is not None]
        counts[suffix] = len(present)
    return checked_nodes, checked_links, counts


def correlate_findings(
    case: dict[str, Any], graph: dict[str, Any], source_hashes: dict[str, str],
) -> dict[str, Any]:
    if case.get("contract") != "proofqa.p50.v1" or not isinstance(case.get("source"), dict):
        raise InputError("P50 근거/계약 형식 오류.")
    findings = case.get("findings")
    if not isinstance(findings, list) or not findings:
        raise InputError("P50 근거에 정적 후보가 없습니다.")
    nodes, links, languages = validate_graph(graph, source_hashes)
    by_file: dict[str, list[dict[str, Any]]] = {}
    for node in nodes:
        by_file.setdefault(node["source_path"], []).append(node)
    by_id = {n["id"]: n for n in nodes}
    outputs = []
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            raise InputError("P50 후보 항목 오류.")
        name = finding.get("source_path")
        lineno = finding.get("line")
        if (name not in source_hashes or not isinstance(lineno, int) or lineno < 1
                or finding.get("status") != "NEEDS_VALIDATION"
                or finding.get("confirmed_vulnerability") is not False):
            raise InputError("P50 근거 출처 또는 확정 여부가 무결하지 않습니다.")
        options = [n for n in by_file.get(name, []) if n["line"] is not None]
        if not options:
            outputs.append({
                "finding_index": index, "source_path": name, "line": lineno,
                "graph_status": "NOT_COVERED", "graph_node_id": None,
                "impact_edges": [], "confidence": "NONE",
            })
            continue
        lower = [n for n in options if n["line"] <= lineno]
        anchor = max(lower, key=lambda n: n["line"]) if lower else min(options, key=lambda n: n["line"])
        relevant = [edge for edge in links if edge["source"] == anchor["id"]
                    or edge["target"] == anchor["id"]][:12]
        outputs.append({
            "finding_index": index, "source_path": name, "line": lineno,
            "source_sha256": source_hashes[name],
            "graph_status": "SOURCE_FILE_CORRELATED",
            "graph_node_id": anchor["id"], "graph_node_line": anchor["line"],
            "confidence": "SAME_START_LINE" if anchor["line"] == lineno else "FILE_SCOPE_APPROXIMATE",
            "impact_edges": [
                {**edge, "other_node": (
                    by_id.get(edge["target"] if edge["source"] == anchor["id"] else edge["source"], {})
                    .get("label", "unresolved")
                )} for edge in relevant
            ],
        })
    return {
        "contract": "proofqa.p70.graph.v1",
        "graphify_version": GRAPHIFY_VERSION,
        "graphify_graph_schema": (graph.get("graph") or {}).get("schema_version", "UNSPECIFIED"),
        "source_sha256": case["source"].get("sha256"),
        "covered_ast_nodes": languages,
        "findings_correlated": outputs,
        "summary": {
            "findings_total": len(outputs),
            "source_linked": sum(x["graph_status"] == "SOURCE_FILE_CORRELATED" for x in outputs),
            "impact_linked": sum(bool(x["impact_edges"]) for x in outputs),
            "confirmed_security_findings": 0,
        },
        "limitations": [
            "Graphify AST edge is not proof of an executed runtime call.",
            "Nearest start line is approximate; matching file and source hash is not exact statement provenance.",
            "P50 detections stay NEEDS_VALIDATION until independent testing.",
            "No arbitrary customer-source execution or public staging access.",
        ],
        "release_state": "HOLD",
    }
