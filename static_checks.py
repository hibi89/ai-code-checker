"""Small deterministic checks that run locally without executing project code."""

from __future__ import annotations

import ast
import re
import string

from code_input import CodeBundle, SourceFile
from offline_models import CodeFinding


def _line_text(source: SourceFile, line_number: int | None) -> str:
    if not line_number or line_number < 1:
        return ""
    lines = source.source_lines
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
        self.events: dict[str, list[tuple[int, int, tuple[str, str] | None, ast.AST]]] = {}
        self.locals: dict[ast.AST, set[str]] = {}
        self.function_events: dict[ast.AST, dict[str, list[tuple[int, int, tuple[str, str] | None, ast.AST]]]] = {}

        def bind(name: str, node: ast.AST, origin: tuple[str, str] | None = None) -> None:
            self.events.setdefault(name, []).append(
                (getattr(node, "lineno", 0), getattr(node, "col_offset", 0), origin, node))

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
                              if direct and alias.name in {"subprocess", "pickle", "requests", "os", "asyncio", "builtins"}
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
                                  if direct and pkg in {"subprocess", "pickle", "requests", "os", "asyncio", "builtins"}
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
                # Keep module-level provenance in guarded suites; the exact
                # branch restriction is enforced later by _control_suites.
                walk(child, direct=direct)

        for statement in tree.body:
            walk(statement, direct=True)
        for events in self.events.values():
            events.sort(key=lambda value: (value[0], value[1]))
        for function in ast.walk(tree):
            if isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.function_events[function] = self._local_import_events(function)

    @staticmethod
    def _local_import_events(scope: ast.FunctionDef | ast.AsyncFunctionDef
                             ) -> dict[str, list[tuple[int, int, tuple[str, str] | None, ast.AST]]]:
        """Lexically scoped import/rebind records, separate from module globals.

        Never traverse inner functions, classes, lambdas or comprehensions.
        Guarded blocks remain conditional: _control_suites verifies the arm.
        """
        result: dict[str, list[tuple[int, int, tuple[str, str] | None, ast.AST]]] = {}
        allowed = {"subprocess", "pickle", "requests", "os", "asyncio", "builtins"}

        def bind(name: str, node: ast.AST, origin: tuple[str, str] | None = None) -> None:
            result.setdefault(name, []).append((
                getattr(node, "lineno", 0), getattr(node, "col_offset", 0), origin, node,
            ))

        def walk(node: ast.AST) -> None:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                bind(node.name, node)
                return
            if isinstance(node, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp,
                                 ast.GeneratorExp)):
                return
            if isinstance(node, ast.Import):
                for alias in node.names:
                    origin = ((alias.name, "__module__")
                              if alias.name in allowed else None)
                    bind(alias.asname or alias.name.split(".")[0], node, origin)
                return
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        for existing in tuple(result):
                            bind(existing, node)
                    else:
                        pkg = node.module if node.level == 0 else None
                        origin = ((pkg, alias.name) if pkg in allowed else None)
                        bind(alias.asname or alias.name, node, origin)
                return
            if isinstance(node, ast.ExceptHandler) and node.name:
                bind(node.name, node)
            if isinstance(node, (ast.MatchAs, ast.MatchStar)) and node.name:
                bind(node.name, node)
            if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                bind(node.id, node)
            for child in ast.iter_child_nodes(node):
                walk(child)

        for statement in scope.body:
            walk(statement)
        for records in result.values():
            records.sort(key=lambda event: (event[0], event[1]))
        return result

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

    _CONDITIONAL_BLOCKS = (
        ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.TryStar,
        ast.With, ast.AsyncWith, ast.Match,
    )

    def _control_suites(self, node: ast.AST) -> set[tuple[ast.AST, str | ast.AST]]:
        """Track exactly which guarded suite contains a syntactic node.

        An import in an if/try/loop/match suite is not guaranteed to have run
        when a later call is outside that same suite. This is purely syntactic
        dominance evidence, not execution of code or full control-flow analysis.
        """
        result: set[tuple[ast.AST, str | ast.AST]] = set()
        child = node
        parent = self.parents.get(child)
        while parent is not None:
            if isinstance(parent, self._CONDITIONAL_BLOCKS):
                key: str | ast.AST | None = None
                for field in ("body", "orelse", "finalbody"):
                    suite = getattr(parent, field, None)
                    if isinstance(suite, list) and child in suite:
                        key = field
                        break
                if key is None and isinstance(parent, (ast.Try, ast.TryStar)):
                    if child in parent.handlers:
                        key = child  # exact except handler, not every handler
                if key is None and isinstance(parent, ast.Match):
                    if child in parent.cases:
                        key = child  # exact match case
                if key is not None:
                    result.add((parent, key))
            child, parent = parent, self.parents.get(parent)
        return result

    def _candidate(self, alias: str, call: ast.Call) -> tuple[str, str] | None:
        nested = False
        closest_scope: ast.AST | None = None
        parent = self.parents.get(call)
        while parent is not None:
            if isinstance(parent, self._SCOPES):
                nested = True
                if closest_scope is None:
                    closest_scope = parent
                if alias in self.local_names(parent):
                    # Inner function imports can be traced; other lexical
                    # scopes/closures stay unknown rather than borrowing a
                    # sibling or class import.
                    if parent is not closest_scope:
                        records = self.function_events.get(parent, {}).get(alias, ())
                        if (not isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef))
                                or len(records) != 1 or records[0][2] is None
                                or records[0][0] >= getattr(closest_scope, "lineno", 0)
                                or self._control_suites(records[0][3])):
                            return None
                        return records[0][2]
                    if not isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        return None
                    records = self.function_events.get(parent, {}).get(alias, ())
                    earlier = [row for row in records
                               if (row[0], row[1]) < (call.lineno, call.col_offset)]
                    if not earlier:
                        return None
                    _, _, origin, bound_at = earlier[-1]
                    if not self._control_suites(bound_at).issubset(self._control_suites(call)):
                        return None
                    return origin
            parent = self.parents.get(parent)
        events = self.events.get(alias, ())
        if nested and any(origin is None for _, _, origin, _ in events):
            return None  # Execution order of later global writes is unknown.
        earlier = [row for row in events
                   if (row[0], row[1]) < (call.lineno, call.col_offset)]
        if not earlier:
            return None
        _, _, origin, bound_at = earlier[-1]
        if not self._control_suites(bound_at).issubset(self._control_suites(call)):
            return None  # Import or shadow may have executed only in another arm.
        return origin

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
               for line, col, _, _ in events):
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
_DIRECT_SHELL_CALLS = {"os": {"system", "popen"}, "asyncio": {"create_subprocess_shell"}}
_REQUESTS_CALLS = {"get", "post", "put", "patch", "delete", "head", "options", "request"}


def _literal_imported_module(node: ast.AST, resolver: _ImportResolver) -> str | None:
    """Only the *builtin* __import__('literal') with no other arguments.

    The original source is never imported or executed. Aliases, dynamically
    computed module names and shadowed __import__ are intentionally skipped.
    """
    if (not isinstance(node, ast.Call) or not resolver.builtin(node, "__import__")
            or len(node.args) != 1 or node.keywords
            or not isinstance(node.args[0], ast.Constant)
            or not isinstance(node.args[0].value, str)):
        return None
    module = node.args[0].value
    return module if module in {"builtins", "subprocess", "os", "asyncio", "pickle", "requests"} else None


def _dynamic_import_target(call: ast.Call, resolver: _ImportResolver) -> tuple[str, str] | None:
    """Recognize direct literal module-function calls, not arbitrary call chains.

    Supports __import__('subprocess').run(...), __import__('pickle').loads(...),
    and __import__('requests').get(...), plus
    getattr(__import__('builtins'), 'eval')(...). Both dynamic lookup
    operators must resolve to unshadowed builtins by lexical inspection.
    The result means a syntactic risk candidate, not actual runtime identity.
    """
    callee = call.func
    if isinstance(callee, ast.Attribute):
        module = _literal_imported_module(callee.value, resolver)
        return (module, callee.attr) if module else None
    if (isinstance(callee, ast.Call) and resolver.builtin(callee, "getattr")
            and len(callee.args) == 2 and not callee.keywords
            and isinstance(callee.args[1], ast.Constant)
            and isinstance(callee.args[1].value, str)):
        module = _literal_imported_module(callee.args[0], resolver)
        return (module, callee.args[1].value) if module else None
    return None


def _sql_literal_prefix(node: ast.AST) -> str:
    """Only identify visible leading SQL text; never guess from dynamic values."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr) and node.values:
        return _sql_literal_prefix(node.values[0])
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        return _sql_literal_prefix(node.left)
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"format", "format_map"}):
        return _sql_literal_prefix(node.func.value)
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


_SQL_PERCENT_SLOT = re.compile(
    r"(?<!%)%(?:\([A-Za-z_]\w*\))?[-+# 0]*(?:\d+|\*)?(?:\.\d+)?[diouxXeEfFgGcrsa]"
)


def _literal_format_argument(node: ast.AST) -> bool:
    """Structural literal check only: DO NOT evaluate code or f-strings."""
    if isinstance(node, ast.Constant):
        return type(node.value) in (str, bytes, int, float, bool, type(None))
    if (isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub))
            and isinstance(node.operand, ast.Constant)
            and type(node.operand.value) in (int, float)):
        return True
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return all(_literal_format_argument(value) for value in node.elts)
    if isinstance(node, ast.Dict):
        return all(key is not None and _literal_format_argument(key)
                   and _literal_format_argument(value)
                   for key, value in zip(node.keys, node.values))
    return False


def _has_real_format_field(pattern: str) -> bool:
    """Distinguish actual interpolation from escaped {{braces}} or plain SQL."""
    try:
        return any(field is not None for _, field, _, _
                   in string.Formatter().parse(pattern))
    except ValueError:
        return False


def _sql_dynamic(node: ast.AST) -> bool:
    """Only direct dynamic interpolation with a visible leading SQL verb.

    Includes Python string %, str.format and str.format_map without
    treating constant-only formatting or parameterized SQL as risky.
    This is pattern evidence, not proof of exploitable SQL injection.
    """
    if not _SQL_START.match(_sql_literal_prefix(node)):
        return False
    if isinstance(node, ast.JoinedStr):
        return not _sql_literal_only(node)
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Add):
            return not _sql_literal_only(node)
        if isinstance(node.op, ast.Mod):
            return (isinstance(node.left, ast.Constant)
                    and isinstance(node.left.value, str)
                    and bool(_SQL_PERCENT_SLOT.search(node.left.value))
                    and not _literal_format_argument(node.right))
        return False
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"format", "format_map"}
            and isinstance(node.func.value, ast.Constant)
            and isinstance(node.func.value.value, str)):
        pattern = node.func.value.value
        if not _has_real_format_field(pattern):
            return False
        expressions = [*node.args, *(key.value for key in node.keywords)]
        return (bool(expressions)
                and not any(key.arg is None for key in node.keywords)
                and any(not _literal_format_argument(item) for item in expressions))
    return False


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


def _static_option_constant(value: ast.AST) -> object:
    """Return only primitive syntax literals; never evaluate source expressions."""
    if isinstance(value, ast.Constant):
        return value.value
    if (
        isinstance(value, ast.UnaryOp)
        and isinstance(value.op, (ast.UAdd, ast.USub))
        and isinstance(value.operand, ast.Constant)
        and type(value.operand.value) in (int, float)
    ):
        literal = value.operand.value
        return literal if isinstance(value.op, ast.UAdd) else -literal
    return None


def _literal_shell_enabled(value: ast.AST) -> bool:
    """Only flag syntactically known truthy built-in literals."""
    candidate = _static_option_constant(value)
    return type(candidate) in (bool, int, float, str, bytes) and bool(candidate)


def _literal_tls_disabled(value: ast.AST) -> bool:
    """None means 'default' in requests, not explicit certificate bypass."""
    candidate = _static_option_constant(value)
    return type(candidate) in (bool, int, float, str, bytes) and not candidate


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
        literal_dynamic_target = _dynamic_import_target(node, resolver)
        if ((function_name in {"eval", "exec"} and resolver.builtin(node, function_name))
                or resolver.imported(node, "builtins", {"eval", "exec"})
                or (literal_dynamic_target is not None
                    and literal_dynamic_target[0] == "builtins"
                    and literal_dynamic_target[1] in {"eval", "exec"})):
            risky_builtin = (
                literal_dynamic_target[1] if literal_dynamic_target is not None
                and literal_dynamic_target[0] == "builtins" else
                function_name or attribute_name or "eval/exec alias"
            )
            findings.append(_finding(
                source, "HIGH", "security", f"동적 코드 실행 호출: {risky_builtin}",
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
        # os.system/os.popen and asyncio.create_subprocess_shell always
        # invoke a shell; unlike subprocess.run/Popen shell=True is not needed.
        # Resolve only known import provenance to avoid unrelated-method FPs.
        direct_shell = any(
            resolver.imported(node, package, names)
            or (literal_dynamic_target is not None
                and literal_dynamic_target[0] == package
                and literal_dynamic_target[1] in names)
            for package, names in _DIRECT_SHELL_CALLS.items()
        )
        if direct_shell or (shell_true and (
            resolver.imported(node, "subprocess", _SUBPROCESS_CALLS)
            or (literal_dynamic_target is not None
                and literal_dynamic_target[0] == "subprocess"
                and literal_dynamic_target[1] in _SUBPROCESS_CALLS)
        )):
            findings.append(_finding(
                source, "HIGH", "security", "셸 명령을 문자열로 실행함",
                line_number,
                "명령 인자에 외부 입력이 섞이면 셸 메타문자 실행 위험이 생길 수 있습니다.",
                "가능하면 shell=False와 인자 배열을 사용하고, 모든 인자를 검증하세요.",
                90,
            ))

        if (resolver.imported(node, "pickle", {"load", "loads"})
                or (literal_dynamic_target is not None
                    and literal_dynamic_target[0] == "pickle"
                    and literal_dynamic_target[1] in {"load", "loads"})):
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
        if (resolver.imported(node, "requests", _REQUESTS_CALLS)
                or (literal_dynamic_target is not None
                    and literal_dynamic_target[0] == "requests"
                    and literal_dynamic_target[1] in _REQUESTS_CALLS)) and any(
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

        # SQL drivers expose direct, batch and SQLite script execution.
        # Match only visible dynamic SQL construction; parameter binding remains safe.
        if attribute_name in {"execute", "executemany", "executescript"} and node.args:
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
