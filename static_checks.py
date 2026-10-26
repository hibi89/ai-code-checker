"""Small deterministic checks that run locally without executing project code."""

from __future__ import annotations

import ast
import re

from code_input import CodeBundle, SourceFile
from review_models import CodeFinding


def _line_text(source: SourceFile, line_number: int | None) -> str:
    if not line_number or line_number < 1:
        return ""
    lines = source.text.splitlines()
    if line_number > len(lines):
        return ""
    return lines[line_number - 1].strip()[:300]


def _finding(
    source: SourceFile,
    severity: str,
    perspective: str,
    title: str,
    line_number: int | None,
    impact: str,
    recommendation: str,
    confidence: int = 95,
) -> CodeFinding:
    line = _line_text(source, line_number)
    return CodeFinding(
        severity=severity,  # type: ignore[arg-type]
        perspective=perspective,  # type: ignore[arg-type]
        title=title,
        file_path=source.path,
        start_line=line_number,
        end_line=line_number,
        evidence=line,
        impact=impact,
        recommendation=recommendation,
        confidence=confidence,
        source="static",
        citation_verified=bool(line and line_number and line_number <= source.line_count),
    )


def _module_imports(tree: ast.Module) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Module-level import names only: do not infer arbitrary objects' provenance."""
    modules = {"subprocess": set(), "pickle": set(), "requests": set()}
    functions = {"subprocess": set(), "pickle": set(), "requests": set()}
    for stmt in tree.body:
        if isinstance(stmt, ast.Import):
            for alias in stmt.names:
                if alias.name in modules:
                    modules[alias.name].add(alias.asname or alias.name)
        elif isinstance(stmt, ast.ImportFrom) and stmt.level == 0:
            if stmt.module in functions:
                for alias in stmt.names:
                    functions[stmt.module].add((alias.name, alias.asname or alias.name))
    return modules, functions


_SQL_START = re.compile(
    r"^\s*(?:SELECT|INSERT|UPDATE|DELETE|REPLACE|WITH|CREATE|ALTER|DROP|PRAGMA)\b",
    re.IGNORECASE,
)
_SUBPROCESS_CALLS = {"run", "Popen", "call", "check_call", "check_output"}
_REQUESTS_CALLS = {"get", "post", "put", "patch", "delete", "head", "options", "request"}


def _sql_literal_prefix(node: ast.AST) -> str:
    """Only identify visible leading SQL text; never guess from dynamic values."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr) and node.values:
        return _sql_literal_prefix(node.values[0])
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _sql_literal_prefix(node.left)
    return ""


def _python_findings(source: SourceFile) -> list[CodeFinding]:
    findings: list[CodeFinding] = []
    try:
        tree = ast.parse(source.text, filename=source.path)
    except SyntaxError as error:
        findings.append(_finding(
            source, "HIGH", "reliability", "Python 구문 오류",
            error.lineno or 1,
            f"Python 파서가 이 파일을 읽지 못했습니다: {error.msg}",
            "오류 위치의 문법과 들여쓰기를 수정한 뒤 다시 검토하세요.",
        ))
        return findings

    modules, functions = _module_imports(tree)

    def imported_call(node: ast.AST, package: str, names: set[str]) -> bool:
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            return node.value.id in modules[package] and node.attr in names
        if isinstance(node, ast.Name):
            return any(original in names and local == node.id for original, local in functions[package])
        return False

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        line_number = getattr(node, "lineno", None)
        function_name = node.func.id if isinstance(node.func, ast.Name) else None
        attribute_name = node.func.attr if isinstance(node.func, ast.Attribute) else None
        if function_name in {"eval", "exec"}:
            findings.append(_finding(
                source, "HIGH", "security", f"동적 코드 실행 호출: {function_name}",
                line_number,
                "외부 입력이 전달되면 임의 코드 실행으로 이어질 수 있습니다.",
                "동적 실행이 꼭 필요한지 확인하고, 가능하면 명시적 파서나 허용 목록 기반 로직으로 대체하세요.",
                90,
            ))

        shell_true = any(
            keyword.arg == "shell"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
            for keyword in node.keywords
        )
        if shell_true and imported_call(node.func, "subprocess", _SUBPROCESS_CALLS):
            findings.append(_finding(
                source, "HIGH", "security", "셸 명령을 문자열로 실행함",
                line_number,
                "명령 인자에 외부 입력이 섞이면 셸 메타문자 실행 위험이 생길 수 있습니다.",
                "가능하면 shell=False와 인자 배열을 사용하고, 모든 인자를 검증하세요.",
                90,
            ))

        if imported_call(node.func, "pickle", {"load", "loads"}):
            findings.append(_finding(
                source, "HIGH", "security",
                "신뢰할 수 없는 데이터의 pickle 역직렬화 가능성",
                line_number,
                "조작된 pickle 입력은 역직렬화 과정에서 임의 동작을 유발할 수 있습니다.",
                "신뢰 경계를 확인하고, 외부 데이터에는 JSON 등 안전한 직렬화 형식을 사용하세요.",
                85,
            ))

        # Generic verify=False text matching on Python caused string/comment FPs.
        # Only recognize explicit requests module/from-import HTTP calls.
        if imported_call(node.func, "requests", _REQUESTS_CALLS) and any(
            kw.arg == "verify" and isinstance(kw.value, ast.Constant)
            and kw.value.value is False for kw in node.keywords
        ):
            findings.append(_finding(
                source, "HIGH", "security", "TLS 인증서 검증을 비활성화함",
                line_number,
                "서버 인증서 확인을 끄면 중간자 공격에 노출될 수 있습니다.",
                "인증서 검증을 다시 켜고, 개발용 예외가 운영 설정에 포함되지 않게 분리하세요.",
                85,
            ))

        if attribute_name == "execute" and node.args:
            query = node.args[0]
            if isinstance(query, ast.JoinedStr) or (
                isinstance(query, ast.BinOp) and isinstance(query.op, ast.Add)
            ):
                if _SQL_START.match(_sql_literal_prefix(query)):
                    findings.append(_finding(
                        source, "HIGH", "security",
                        "SQL 질의 문자열을 동적으로 조합함",
                        line_number,
                        "외부 입력이 질의 문자열에 직접 결합되면 SQL 인젝션 위험이 생길 수 있습니다.",
                        "값은 플레이스홀더 바인딩으로 전달하고, 질의 구조와 데이터 값을 분리하세요.",
                        80,
                    ))
    return findings


def run_static_checks(bundle: CodeBundle) -> list[CodeFinding]:
    findings: list[CodeFinding] = []
    for source in bundle.files:
        for redaction in source.redactions:
            is_credential = redaction.kind not in {
                "email address", "Korean phone number", "Korean resident number"
            }
            findings.append(_finding(
                source,
                "HIGH",
                "security",
                (
                    "비밀정보 형태의 값이 전송 전에 마스킹됨"
                    if is_credential
                    else "개인정보 형태의 값이 전송 전에 마스킹됨"
                ),
                redaction.line_number,
                (
                    f"{redaction.kind} 형태의 문자열이 감지되었습니다. 실제 자격증명이라면 노출된 것으로 간주해야 합니다."
                    if is_credential
                    else f"{redaction.kind} 형태의 값이 감지되어 AI 전송 전에 가려졌습니다."
                ),
                (
                    "해당 키나 비밀번호를 폐기·교체하고, 저장소와 배포 환경에 실제 비밀값이 남지 않았는지 확인하세요."
                    if is_credential
                    else "실제 개인정보라면 저장 위치와 처리 근거를 확인하고, 필요하지 않은 개인정보는 테스트 데이터에서도 제거하세요."
                ),
                85,
            ))

        if source.path.lower().endswith((".py", ".pyi")):
            findings.extend(_python_findings(source))
        else:
            # Non-Python inputs remain GENERIC PATTERN ONLY, not parsed JS/TS.
            for line_number, line in enumerate(source.text.splitlines(), start=1):
                if re.search(r"(?i)\bverify\s*=\s*False\b", line):
                    findings.append(_finding(
                        source, "HIGH", "security",
                        "TLS 인증서 검증을 비활성화함",
                        line_number,
                        "서버 인증서 확인을 끄면 중간자 공격에 노출될 수 있습니다.",
                        "인증서 검증을 다시 켜고, 개발용 예외가 운영 설정에 포함되지 않게 분리하세요.",
                        85,
                    ))

    return findings
