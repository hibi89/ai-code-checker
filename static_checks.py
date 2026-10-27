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


class _ImportResolver:
    """Conservative module binding chronology plus lexical shadow checks.

    Only direct module imports identify sensitive APIs. Uncertain rebinding
    invalidates identity instead of guessing the runtime value of an alias.
    """

    _SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef,
               ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)

    def __init__(self, tree: ast.Module) -> None:
        self.parents = {child: parent for parent in ast.walk(tree)
                        for child in ast.iter_child_nodes(parent)}
        self.events: dict[str, list[tuple[int, int, tuple[str, str] | None]]] = {}
        self.locals: dict[ast.AST, set[str]] = {}

        def bind(name: str, node: ast.AST, origin: tuple[str, str] | None = None) -> None:
            self.events.setdefault(name, []).append(
                (getattr(node, "lineno", 0), getattr(node, "col_offset", 0), origin))

        def walk(node: ast.AST, *, direct: bool = False) -> None:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                bind(node.name, node)
                return
            if isinstance(node, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp,
                                 ast.GeneratorExp)):
                return
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = alias.asname or alias.name.split(".")[0]
                    origin = ((alias.name, "__module__")
                              if direct and alias.name in {"subprocess", "pickle", "requests"}
                              else None)
                    bind(local, node, origin)
                return
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        for existing in tuple(self.events):
                            bind(existing, node)
                    else:
                        local = alias.asname or alias.name
                        pkg = node.module if node.level == 0 else None
                        origin = ((pkg, alias.name)
                                  if direct and pkg in {"subprocess", "pickle", "requests"}
                                  else None)
                        bind(local, node, origin)
                return
            if isinstance(node, ast.ExceptHandler) and node.name:
                bind(node.name, node)
            if isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
                bind(node.name, node)
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                bind(node.id, node)
            for child in ast.iter_child_nodes(node):
                walk(child)

        for statement in tree.body:
            walk(statement, direct=True)
        for events in self.events.values():
            events.sort(key=lambda value: (value[0], value[1]))

    def local_names(self, scope: ast.AST) -> set[str]:
        if scope in self.locals:
            return self.locals[scope]
        names: set[str] = set()

        def visit(node: ast.AST) -> None:
            if node is not scope and isinstance(node, self._SCOPES):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    names.add(node.name)
                return
            if isinstance(node, ast.arg):
                names.add(node.arg)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                names.add(node.id)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if alias.name != "*":
                        names.add(alias.asname or alias.name.split(".")[0])
            elif isinstance(node, ast.ExceptHandler) and node.name:
                names.add(node.name)
            elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
                names.add(node.name)
            elif isinstance(node, (ast.Global, ast.Nonlocal)):
                names.update(node.names)
            for child in ast.iter_child_nodes(node):
                visit(child)

        visit(scope)
        self.locals[scope] = names
        return names

    def _candidate(self, alias: str, call: ast.Call) -> tuple[str, str] | None:
        nested = False
        parent = self.parents.get(call)
        while parent is not None:
            if isinstance(parent, self._SCOPES):
                nested = True
                if alias in self.local_names(parent):
                    return None
            parent = self.parents.get(parent)
        events = self.events.get(alias, ())
        if nested and any(origin is None for _, _, origin in events):
            return None  # Execution order of later global writes is unknown.
        earlier = [row for row in events
                   if (row[0], row[1]) < (call.lineno, call.col_offset)]
        return earlier[-1][2] if earlier else None

    def imported(self, call: ast.Call, package: str, names: set[str]) -> bool:
        target = call.func
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
            return (target.attr in names and
                    self._candidate(target.value.id, call) == (package, "__module__"))
        if isinstance(target, ast.Name):
            return self._candidate(target.id, call) in {
                (package, original) for original in names
            }
        return False

    def builtin(self, call: ast.Call, name: str) -> bool:
        if not isinstance(call.func, ast.Name) or call.func.id != name:
            return False
        events = self.events.get(name, ())
        if any((line, col) < (call.lineno, call.col_offset)
               for line, col, _ in events):
            return False
        parent = self.parents.get(call)
        while parent is not None:
            if isinstance(parent, self._SCOPES):
                if name in self.local_names(parent) or events:
                    return False
            parent = self.parents.get(parent)
        return True


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


def _sql_literal_only(node: ast.AST) -> bool:
    """Recognize string-only combinations without evaluating project code."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str)
    if isinstance(node, ast.JoinedStr):
        return all(
            (isinstance(item, ast.Constant) and isinstance(item.value, str))
            or (
                isinstance(item, ast.FormattedValue)
                and isinstance(item.value, ast.Constant)
                and (item.format_spec is None or _sql_literal_only(item.format_spec))
            )
            for item in node.values
        )
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _sql_literal_only(node.left) and _sql_literal_only(node.right)
    return False


def _sql_dynamic(node: ast.AST) -> bool:
    """An SQL prefix is not enough: require a nonliteral expression."""
    return (
        isinstance(node, (ast.JoinedStr, ast.BinOp))
        and (not isinstance(node, ast.BinOp) or isinstance(node.op, ast.Add))
        and not _sql_literal_only(node)
        and bool(_SQL_START.match(_sql_literal_prefix(node)))
    )


def _sql_direct_local(query: ast.AST, call: ast.Call, resolver: _ImportResolver) -> bool:
    """Track only direct statements/returns and assignments in one ordered block.

    For conditionals, candidate assignment and execution must be within the
    same if/else arm. Values inherited from outside the arm are not inferred.
    Nested writes invalidate the candidate rather than claiming dataflow.
    """
    if not isinstance(query, ast.Name):
        return False
    statement = resolver.parents.get(call)
    if not isinstance(statement, (ast.Expr, ast.Return)) or statement.value is not call:
        return False
    scope = resolver.parents.get(statement)
    if isinstance(scope, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef)):
        block = scope.body
    elif isinstance(scope, ast.If):
        if statement in scope.body:
            block = scope.body
        elif statement in scope.orelse:
            block = scope.orelse
        else:
            return False
    else:
        return False

    candidate = False
    for earlier in block:
        if earlier is statement:
            return candidate
        if (isinstance(earlier, ast.Assign) and len(earlier.targets) == 1
                and isinstance(earlier.targets[0], ast.Name)
                and earlier.targets[0].id == query.id):
            candidate = _sql_dynamic(earlier.value)
            continue
        if (isinstance(earlier, ast.AnnAssign)
                and isinstance(earlier.target, ast.Name)
                and earlier.target.id == query.id):
            candidate = earlier.value is not None and _sql_dynamic(earlier.value)
            continue
        if any(isinstance(n, ast.Name) and n.id == query.id and
               isinstance(n.ctx, (ast.Store, ast.Del)) for n in ast.walk(earlier)):
            candidate = False
        if isinstance(earlier, (ast.Import, ast.ImportFrom)) and any(
            (a.asname or a.name.split(".")[0]) == query.id for a in earlier.names
        ):
            candidate = False
        if isinstance(earlier, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if earlier.name == query.id:
                candidate = False
    return False


def _literal_shell_enabled(value: ast.AST) -> bool:
    """Only flag syntactically known truthy built-in literals."""
    return isinstance(value, ast.Constant) and isinstance(
        value.value, (bool, int, float, str, bytes)
    ) and bool(value.value)


def _literal_tls_disabled(value: ast.AST) -> bool:
    """None means 'default' in requests, not explicit certificate bypass."""
    return isinstance(value, ast.Constant) and (
        value.value is False
        or (
            type(value.value) in (int, float, str, bytes)
            and not value.value
        )
    )


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

    resolver = _ImportResolver(tree)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        line_number = getattr(node, "lineno", None)
        function_name = node.func.id if isinstance(node.func, ast.Name) else None
        attribute_name = node.func.attr if isinstance(node.func, ast.Attribute) else None
        if function_name in {"eval", "exec"} and resolver.builtin(node, function_name):
            findings.append(_finding(
                source, "HIGH", "security", f"동적 코드 실행 호출: {function_name}",
                line_number,
                "외부 입력이 전달되면 임의 코드 실행으로 이어질 수 있습니다.",
                "동적 실행이 꼭 필요한지 확인하고, 가능하면 명시적 파서나 허용 목록 기반 로직으로 대체하세요.",
                90,
            ))

        shell_true = any(
            keyword.arg == "shell"
            and _literal_shell_enabled(keyword.value)
            for keyword in node.keywords
        )
        if shell_true and resolver.imported(node, "subprocess", _SUBPROCESS_CALLS):
            findings.append(_finding(
                source, "HIGH", "security", "셸 명령을 문자열로 실행함",
                line_number,
                "명령 인자에 외부 입력이 섞이면 셸 메타문자 실행 위험이 생길 수 있습니다.",
                "가능하면 shell=False와 인자 배열을 사용하고, 모든 인자를 검증하세요.",
                90,
            ))

        if resolver.imported(node, "pickle", {"load", "loads"}):
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
        if resolver.imported(node, "requests", _REQUESTS_CALLS) and any(
            kw.arg == "verify" and _literal_tls_disabled(kw.value)
            for kw in node.keywords
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
            if _sql_dynamic(query) or _sql_direct_local(query, node, resolver):
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
