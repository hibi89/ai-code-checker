from __future__ import annotations

import argparse
import math
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from code_input import CodeBundle, InputError, InputLimits, bundle_from_text, load_path
from reporting import convert_ai_findings, render_report
from reviewer import ReviewError, analyze_bundle, build_prompt, estimate_request_cost
from static_checks import run_static_checks


DEFAULT_MODEL = "gemini-3.1-flash-lite"
DEFAULT_INPUT_PRICE = 0.25
DEFAULT_OUTPUT_PRICE = 1.50


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
    input_price: float
    output_price: float
    max_output_tokens: int
    max_estimated_cost_usd: float


def _float_setting(name: str, default: float) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as error:
        raise ValueError(f"{name}은 숫자여야 합니다.") from error
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name}은 유한한 0 이상 숫자여야 합니다.")
    return value


def _int_setting(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"{name}은 정수여야 합니다.") from error
    return value


def load_settings() -> Settings:
    load_dotenv()
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    max_output_tokens = _int_setting("MAX_OUTPUT_TOKENS", 2048)
    max_estimated_cost_usd = _float_setting("MAX_ESTIMATED_COST_USD", 0.05)
    if not 256 <= max_output_tokens <= 8192:
        raise ValueError("MAX_OUTPUT_TOKENS는 256~8192 범위여야 합니다.")
    if max_estimated_cost_usd <= 0:
        raise ValueError("MAX_ESTIMATED_COST_USD는 0보다 커야 합니다.")
    return Settings(
        api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        model=model,
        input_price=_float_setting("GEMINI_INPUT_USD_PER_MILLION", DEFAULT_INPUT_PRICE),
        output_price=_float_setting("GEMINI_OUTPUT_USD_PER_MILLION", DEFAULT_OUTPUT_PRICE),
        max_output_tokens=max_output_tokens,
        max_estimated_cost_usd=max_estimated_cost_usd,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="소스 코드를 실행하지 않고 정적 검사와 Gemini 단일 호출로 검수합니다."
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="검수할 폴더, ZIP 또는 단일 코드 파일. 생략하면 표준 입력을 사용합니다.",
    )
    parser.add_argument(
        "--filename",
        default="stdin.py",
        help="표준 입력 코드의 파일명/확장자 (기본값: stdin.py)",
    )
    parser.add_argument(
        "--output",
        help="Markdown 리포트 경로. 기존 파일은 덮어쓰지 않습니다.",
    )
    parser.add_argument(
        "--order-ref",
        default="",
        help="사용량 로그에 남길 비식별 주문 참조(영문·숫자·._-만, 최대 64자).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="파일 필터·비밀정보 마스킹·정적 검사만 수행하고 외부 API를 호출하지 않습니다.",
    )
    parser.add_argument(
        "--confirm-upload",
        action="store_true",
        help="검수 대상 코드를 Google Gemini API로 보내는 것에 동의합니다.",
    )
    return parser


def _configure_console_encoding() -> None:
    """Keep Korean CLI output usable on Windows consoles with legacy code pages."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="backslashreplace")
            except (OSError, ValueError):
                pass


def _read_stdin_bundle(filename: str, limits: InputLimits) -> CodeBundle:
    try:
        if sys.stdin.isatty():
            print("코드를 붙여 넣고 입력을 마치면 새 줄에 END를 입력하세요.")
            lines: list[str] = []
            total_bytes = 0
            while True:
                line = sys.stdin.readline(limits.max_total_bytes + 2)
                if not line:
                    break
                if len(line) > limits.max_total_bytes + 1:
                    raise InputError("붙여넣은 입력이 프로젝트 크기 제한을 초과했습니다.")
                line = line.rstrip("\n")
                if line.endswith("\r"):
                    line = line[:-1]
                if line.strip() == "END":
                    break
                line_bytes = len(line.encode("utf-8")) + (1 if lines else 0)
                total_bytes += line_bytes
                if total_bytes > min(limits.max_file_bytes, limits.max_total_bytes):
                    raise InputError("붙여넣은 입력이 파일 크기 제한을 초과했습니다.")
                lines.append(line)
            text = "\n".join(lines)
        else:
            text = sys.stdin.read(limits.max_total_bytes + 1)
    except UnicodeError as error:
        raise InputError("표준 입력을 UTF-8 텍스트로 읽지 못했습니다.") from error
    return bundle_from_text(text, filename=filename, limits=limits)


def _confirm_cloud_upload(args: argparse.Namespace) -> bool:
    print()
    print("외부 AI 전송 안내")
    print("- 선택한 코드 파일과 비밀정보 마스킹 결과가 Google Gemini API로 전송됩니다.")
    print("- 실제 .env·키 파일과 지원하지 않는 파일은 읽거나 전송하지 않습니다.")
    print("- 코드는 실행하거나 의존성을 설치하지 않습니다.")
    print("- 외부 전송을 허용할 권한이 있는 코드인지, Google 계정의 데이터 처리 조건을 확인하세요.")
    if args.confirm_upload:
        return True
    if not sys.stdin.isatty():
        print("비대화형 실행은 --confirm-upload를 지정해야 전송할 수 있습니다.")
        return False
    answer = input("전송을 허용하면 YES를 입력하세요: ").strip()
    return answer == "YES"


def _print_input_summary(bundle: CodeBundle, static_count: int) -> None:
    print(f"분석 대상으로 준비한 파일: {len(bundle.files)}개 ({bundle.source_bytes:,} bytes)")
    print(f"전송 전 마스킹한 비밀정보 형태 값: {bundle.redaction_count}개")
    print(f"지원하지 않거나 제외한 파일: {len(bundle.excluded_paths)}개")
    print(f"로컬 정적 검사에서 발견한 항목: {static_count}개")
    if bundle.warnings:
        for warning in bundle.warnings:
            print(f"- {warning}")
    for source in bundle.files:
        print(f"  - {source.path}")


def _save_report(report: str, requested_path: str | None) -> Path:
    if requested_path:
        destination = Path(requested_path).expanduser()
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            with destination.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(report)
        except FileExistsError as error:
            raise ValueError("리포트 경로의 파일이 이미 있습니다. 다른 경로를 지정하세요.") from error
        return destination

    directory = Path.home() / ".ai-code-checker" / "reports"
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    for suffix in range(100):
        name = f"review-{stamp}-{suffix:02d}.md"
        destination = directory / name
        try:
            with destination.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(report)
            return destination
        except FileExistsError:
            continue
    raise OSError("새 리포트 파일 이름을 만들지 못했습니다.")


def _usage_log_path() -> Path:
    return Path.home() / ".ai-code-checker" / "usage.jsonl"


def run_cli(argv: list[str] | None = None) -> int:
    _configure_console_encoding()
    parser = build_parser()
    args = parser.parse_args(argv)
    limits = InputLimits()

    try:
        settings = load_settings()
        if args.source:
            bundle = load_path(args.source, limits)
        else:
            bundle = _read_stdin_bundle(args.filename, limits)
        static_findings = run_static_checks(bundle)
        _print_input_summary(bundle, len(static_findings))

        prompt = build_prompt(bundle)
        estimate = estimate_request_cost(
            prompt,
            settings.input_price,
            settings.output_price,
            settings.max_output_tokens,
        )
        print(
            f"예상 최대 API 원가: USD {estimate.max_estimated_cost_usd:.6f} "
            f"(입력 추정 {estimate.estimated_input_tokens:,} tokens, "
            f"출력 상한 {estimate.max_output_tokens:,} tokens)"
        )
        over_budget = estimate.max_estimated_cost_usd > settings.max_estimated_cost_usd
        if over_budget:
            print(
                "예상 원가가 설정 상한을 넘습니다. 실제 분석은 입력 범위를 줄이거나 "
                "MAX_ESTIMATED_COST_USD를 검토하기 전까지 API를 호출하지 않습니다.",
                file=sys.stderr,
            )

        if args.dry_run:
            print("드라이런 완료: 외부 전송과 AI 호출은 하지 않았습니다.")
            return 0

        if over_budget:
            return 2

        if not settings.api_key:
            print("GEMINI_API_KEY가 없습니다. .env를 설정한 뒤 다시 실행하세요.", file=sys.stderr)
            return 2
        if args.order_ref and not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", args.order_ref):
            print("--order-ref는 영문·숫자·점·밑줄·하이픈으로 된 1~64자만 허용합니다.", file=sys.stderr)
            return 2

        if not _confirm_cloud_upload(args):
            print("외부 전송 동의가 없어 AI 분석을 시작하지 않았습니다.")
            return 2

        ai_review, usage, estimate, usage_warnings = analyze_bundle(
            bundle,
            api_key=settings.api_key,
            model=settings.model,
            input_usd_per_million=settings.input_price,
            output_usd_per_million=settings.output_price,
            max_output_tokens=settings.max_output_tokens,
            max_estimated_cost_usd=settings.max_estimated_cost_usd,
        )
        ai_findings = convert_ai_findings(ai_review, bundle)

        try:
            from reviewer import append_usage_log

            append_usage_log(
                usage,
                path=_usage_log_path(),
                order_ref=args.order_ref,
            )
        except (OSError, ValueError):
            usage_warnings.append(
                "로컬 사용량 로그를 기록하지 못했습니다. 소스 코드는 로그에 기록하지 않습니다."
            )

        report = render_report(
            bundle=bundle,
            static_findings=static_findings,
            ai_review=ai_review,
            ai_findings=ai_findings,
            usage=usage,
            preflight_cost_usd=estimate.max_estimated_cost_usd,
            cost_limit_usd=settings.max_estimated_cost_usd,
            usage_warnings=usage_warnings,
        )
        report_path = _save_report(report, args.output)
        print(f"검수가 끝났습니다. 한국어 리포트: {report_path}")
        if any(not finding.citation_verified for finding in ai_findings):
            print("AI 발견 항목 중 원본 경로·줄·발췌가 맞지 않는 항목이 있습니다. 리포트에서 사람 확인 표시를 확인하세요.")
        return 0

    except (InputError, ReviewError, ValueError, OSError) as error:
        print(f"검수를 완료하지 못했습니다: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("사용자가 실행을 취소했습니다.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(run_cli())
