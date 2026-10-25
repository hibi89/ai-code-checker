import asyncio
import json
import os
import re
import sys
from typing import Literal, Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# ============================================================
# Config
# ============================================================

load_dotenv()


def get_int_env(name: str, default: int) -> int:
    value = os.getenv(name, str(default))

    try:
        return int(value)
    except ValueError as error:
        raise ValueError(
            f"{name}은 정수여야 합니다. 현재 값: {value}"
        ) from error


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
).strip()

AGENT_MODEL = os.getenv(
    "AGENT_MODEL",
    "",
).strip() or GEMINI_MODEL

JUDGE_MODEL = os.getenv(
    "JUDGE_MODEL",
    "",
).strip() or GEMINI_MODEL

IMPLEMENTATION_MODEL = os.getenv(
    "IMPLEMENTATION_MODEL",
    "",
).strip() or GEMINI_MODEL

MAX_REVIEW_ROUNDS = get_int_env(
    "MAX_REVIEW_ROUNDS",
    3,
)

MAX_RETRIES = get_int_env(
    "MAX_RETRIES",
    3,
)

MAX_CONCURRENT_AGENTS = get_int_env(
    "MAX_CONCURRENT_AGENTS",
    8,
)


def validate_config() -> None:
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요."
        )

    if not GEMINI_MODEL:
        raise RuntimeError("GEMINI_MODEL이 비어 있습니다.")

    if not AGENT_MODEL:
        raise RuntimeError("AGENT_MODEL이 비어 있습니다.")

    if not JUDGE_MODEL:
        raise RuntimeError("JUDGE_MODEL이 비어 있습니다.")

    if not IMPLEMENTATION_MODEL:
        raise RuntimeError("IMPLEMENTATION_MODEL이 비어 있습니다.")

    if MAX_REVIEW_ROUNDS < 1:
        raise ValueError("MAX_REVIEW_ROUNDS는 1 이상이어야 합니다.")

    if MAX_RETRIES < 1:
        raise ValueError("MAX_RETRIES는 1 이상이어야 합니다.")

    if MAX_CONCURRENT_AGENTS < 1:
        raise ValueError("MAX_CONCURRENT_AGENTS는 1 이상이어야 합니다.")

    if MAX_CONCURRENT_AGENTS > 8:
        raise ValueError("MAX_CONCURRENT_AGENTS는 8 이하이어야 합니다.")


# ============================================================
# Structured Output Schemas
# IMPORTANT:
# Pydantic field names and descriptions are ASCII/English
# to avoid SDK schema encoding issues.
# ============================================================

Severity = Literal[
    "CRITICAL",
    "HIGH",
    "MEDIUM",
    "LOW",
    "INFO",
]

Decision = Literal[
    "FINALIZE",
    "REVIEW",
]


class Finding(BaseModel):
    title: str = Field(description="Short title of the finding")
    severity: Severity = Field(description="Severity level")
    location: str = Field(description="File, function, class, snippet, or location")
    evidence: str = Field(description="Code-based evidence")
    impact: str = Field(description="Possible impact")
    suggestion: str = Field(description="Concrete suggestion")


class AgentReview(BaseModel):
    department: str = Field(description="Department name")
    round_number: int = Field(ge=1, description="Review round number")
    score: int = Field(ge=0, le=10, description="Quality score from 0 to 10")
    confidence: int = Field(ge=0, le=100, description="Confidence from 0 to 100")
    summary: str = Field(description="Overall summary")
    strengths: list[str] = Field(description="Strengths")
    findings: list[Finding] = Field(description="Findings")
    open_questions: list[str] = Field(description="Open questions")


class AgentInstruction(BaseModel):
    department: str = Field(description="Department to receive instructions")
    instructions: list[str] = Field(description="Instructions for next review")


class JudgeDecision(BaseModel):
    decision: Decision = Field(description="FINALIZE or REVIEW")
    overall_score: int = Field(ge=0, le=10, description="Overall score from 0 to 10")
    confidence: int = Field(ge=0, le=100, description="Confidence from 0 to 100")
    key_issues: list[str] = Field(description="Key issues")
    agreements: list[str] = Field(description="Agreements")
    conflicts: list[str] = Field(description="Conflicts")
    approved_changes: list[str] = Field(description="Approved changes for implementation")
    review_instructions: list[AgentInstruction] = Field(description="Instructions for review")
    rationale: str = Field(description="Decision rationale")


class FinalCode(BaseModel):
    final_score: int = Field(ge=0, le=10, description="Final score from 0 to 10")
    summary: str = Field(description="Implementation summary")
    changes: list[str] = Field(description="Applied changes")
    remaining_risks: list[str] = Field(description="Remaining risks")
    final_code: str = Field(description="Final code or code bundle")


class TestResponse(BaseModel):
    answer: str = Field(description="Answer text")
    numeric_result: int = Field(description="Numeric result")


# ============================================================
# Prompts
# ============================================================

AGENT_RUBRICS = {
    "보안": """
너는 보안 부처장이다.

다음 관점에서 코드를 검토하라.

- 입력값 검증
- 인증과 권한 문제
- 민감정보 노출
- 인젝션 가능성
- 파일, 네트워크, OS 명령 사용 위험
- 암호화와 토큰 처리
- 예외 메시지를 통한 정보 노출
- 외부 라이브러리 사용 위험
- .env 또는 설정 파일에 실제 비밀값이 포함되었는지 여부

중요 원칙:

- 실제 코드에 근거한 문제만 지적한다.
- 가능성만으로 CRITICAL 또는 HIGH를 남발하지 않는다.
- 보안 문제가 아니면 억지로 보안 문제로 만들지 않는다.
""",

    "성능": """
너는 성능 부처장이다.

다음 관점에서 코드를 검토하라.

- 시간 복잡도
- 불필요한 반복
- 대량 데이터 처리 가능성
- I/O 병목
- 네트워크 호출 병목
- 캐싱 필요성
- 비동기 처리 적절성
- 메모리 사용량
- 병렬 호출과 Rate Limit 간 균형

중요 원칙:

- 실제 병목 가능성이 있는 부분만 지적한다.
- 가독성을 해치는 미세 최적화는 권장하지 않는다.
- 입력 규모가 작다면 과도한 최적화를 요구하지 않는다.
""",

    "아키텍처": """
너는 아키텍처 부처장이다.

다음 관점에서 코드를 검토하라.

- 모듈 분리
- 책임 분리
- 의존성 방향
- 확장 가능성
- 변경 용이성
- 인터페이스 설계
- 전역 상태 사용
- 레이어 간 결합도
- 여러 파일 간 import 관계

중요 원칙:

- 작은 코드에 과도한 엔터프라이즈 구조를 요구하지 않는다.
- 현재 규모에 맞는 구조인지 판단한다.
- 요구사항에 없는 대규모 재설계를 제안하지 않는다.
""",

    "테스트": """
너는 테스트 부처장이다.

다음 관점에서 코드를 검토하라.

- 테스트 가능성
- 단위 테스트 작성 용이성
- 경계값 처리
- 실패 케이스 처리
- 결정적 동작 여부
- 외부 의존성 분리 가능성
- 테스트 누락 시 위험한 부분
- Gemini API 호출을 실제 호출 없이 테스트할 수 있는 구조인지 여부

중요 원칙:

- 코드 자체의 결함과 테스트 부족을 구분한다.
- 단순히 테스트가 없다는 이유만으로 심각도를 과도하게 높이지 않는다.
- 반드시 테스트해야 할 핵심 경로를 구체적으로 제시한다.
""",

    "신뢰성": """
너는 신뢰성 부처장이다.

다음 관점에서 코드를 검토하라.

- 예외 처리
- 장애 복구
- 재시도 정책
- 부분 실패 처리
- 데이터 손상 가능성
- 일관성 유지
- 실패 시 사용자에게 전달되는 정보
- 운영 중 발생 가능한 오류
- 일부 Agent 실패 시 불완전한 검증을 정상 검증으로 처리하지 않는지 여부

중요 원칙:

- 실제 실패 가능성이 있는 흐름을 중심으로 검토한다.
- 모든 예외를 무조건 삼키는 방식을 권장하지 않는다.
- 실패를 정상 성공처럼 처리하는 문제를 특히 주의한다.
""",

    "유지보수": """
너는 유지보수 부처장이다.

다음 관점에서 코드를 검토하라.

- 가독성
- 중복 코드
- 명명
- 함수 크기
- 주석의 적절성
- 변경 시 영향 범위
- 설정값 분리
- 코드 일관성
- 단일 파일과 멀티 파일 구조 간 유지보수 trade-off

중요 원칙:

- 개인 취향 수준의 스타일 지적은 낮은 심각도로 둔다.
- 실제 유지보수 비용을 높이는 문제를 중심으로 지적한다.
- 작동하는 코드를 불필요하게 복잡하게 만들지 않는다.
""",

    "자원관리": """
너는 자원관리 부처장이다.

다음 관점에서 코드를 검토하라.

- 파일 핸들 관리
- 네트워크 연결 관리
- 데이터베이스 연결 관리
- 메모리 누수 가능성
- 동시성 자원 충돌
- 타임아웃 설정
- 백그라운드 작업 정리
- 외부 API 호출 비용
- 병렬 Gemini 호출 수 관리

중요 원칙:

- 실제 자원 누수나 고갈 가능성이 있는지 검토한다.
- 작은 스크립트와 장기 실행 서버를 구분해서 판단한다.
- 자원 정리가 필요한 부분을 구체적으로 제시한다.
""",

    "복잡도비용": """
너는 복잡도와 비용 부처장이다.

다음 관점에서 코드를 검토하라.

- 불필요한 복잡성
- 과도한 추상화
- 운영 비용
- 외부 API 호출 비용
- 모델 호출 비용
- 유지 비용 대비 효과
- 단순한 해결책 존재 여부
- 개발자가 이해하기 쉬운 구조인지 여부
- 8개 Agent 병렬 호출, Judge, Implementation 호출로 인한 비용

중요 원칙:

- 복잡한 해결책보다 단순하고 명확한 해결책을 선호한다.
- 비용 증가 요인이 실제로 있는 경우에만 지적한다.
- 요구사항을 만족하는 가장 작은 변경을 우선한다.
""",
}


JUDGE_PROMPT = """
너는 AI 코드 사전 검증회의 최고 Judge다.

너에게는 8개 전문 부처장이 독립적으로 분석한 보고서가 전달된다.

중요한 구조적 사실:

Gemini가 실제로 9개의 인격을 가지는 것이 아니다.
하나의 모델에 8개의 전문 역할, Judge 역할, 구현 역할을 각각 독립 호출하는 구조다.
따라서 너는 지금 Judge 역할로만 판단해야 한다.

너의 역할은 단순 평균 점수 계산이 아니다.

반드시 다음을 수행하라.

1. 8개 보고서를 모두 비교한다.
2. 중복 지적을 통합한다.
3. 서로 충돌하는 의견을 찾는다.
4. 코드에 근거하지 않은 주장을 걸러낸다.
5. 문제의 심각도를 다시 판단한다.
6. 실제 결함과 단순한 취향을 구분한다.
7. 전체 코드의 품질을 판단한다.
8. 현재 상태로 확정 가능한지 판단한다.
9. 재검증이 필요하다면 부처장별로 구체적인 검증 지시사항을 작성한다.
10. 최종 구현 단계에서 실제 수정해야 할 사항만 승인한다.

중요 원칙:

- CRITICAL 문제가 해결되지 않았다면 일반적으로 재검증한다.
- 중요한 HIGH 문제가 해결되지 않았다면 일반적으로 재검증한다.
- 단순히 평균점수가 낮다는 이유만으로 재검증하지 않는다.
- 사소한 스타일 문제만 남았다면 재검증하지 않는다.
- 근거가 약한 문제는 확신도를 낮춘다.
- 보고서가 먼저 등장했다고 해서 더 중요하게 취급하지 않는다.
- 모든 부처장의 의견을 동등하게 검토한다.
- 부처장이 틀렸다고 판단하면 그 의견을 기각할 수 있다.
- approved_changes에는 실제로 해결할 가치가 있는 문제만 넣는다.
- approved_changes에는 추상적 조언이 아니라 구현 가능한 수정 항목을 적는다.

현재 회차가 최대 검증 회차라면:

이것은 최종 검증이다.
더 이상의 REVIEW를 요구하지 말고 반드시 FINALIZE를 반환한다.

FINALIZE는 현재 검증 결과를 확정한다는 의미다.
REVIEW는 다음 검증 회차가 필요하다는 의미다.
"""


IMPLEMENTATION_PROMPT = """
너는 AI 코드 사전 검증회의 최종 구현 담당자다.

너는 심사위원이 아니다.

Judge가 승인한 수정사항만 실제 코드에 반영한다.

중요한 구조적 사실:

Gemini가 실제로 여러 인격을 가지는 것이 아니다.
하나의 모델을 역할별로 독립 호출하는 구조이며,
너는 지금 Implementation Agent 역할로만 동작해야 한다.

반드시 다음 원칙을 지켜라.

1. Judge가 승인한 문제만 수정한다.
2. 단순한 취향 차이는 수정하지 않는다.
3. 근거 없이 기능을 추가하지 않는다.
4. 기존의 정상적인 기능을 불필요하게 제거하지 않는다.
5. 요구사항에 없는 기능을 임의로 추가하지 않는다.
6. 가장 단순하고 유지보수하기 좋은 해결책을 우선한다.
7. 최종 코드는 실행 가능한 완전한 코드여야 한다.
8. 생략 기호를 사용하지 않는다.
9. 의사코드를 사용하지 않는다.
10. 수정된 전체 코드를 출력한다.
11. Judge가 승인하지 않은 부처장의 제안은 코드에 반영하지 않는다.
12. 원본 코드의 프로그래밍 언어와 구조를 최대한 유지한다.

최종 코드는 사용자가 그대로 복사해서 사용할 수 있어야 한다.
"""


CODE_BUNDLE_NOTICE = """
검증 대상은 단일 파일 코드일 수도 있고,
여러 파일로 구성된 프로젝트 코드 묶음일 수도 있다.

사용자는 아직 실제 파일을 만들기 전에,
전체 프로젝트 코드를 하나의 입력으로 붙여넣었을 수 있다.

입력에는 다음이 섞여 있을 수 있다.

- requirements.txt
- .env.example
- .env 예시
- .gitignore
- 여러 Python 파일
- 번호가 붙은 설명
- 파일 생성 안내 문장
- 짧은 한국어 설명
- 마크다운 형식의 구분선

따라서 다음 원칙을 지켜라.

1. 입력 전체를 하나의 코드 번들로 취급한다.
2. 파일명이 보이면 파일별로 구분해서 판단한다.
3. 파일 경계가 명확하지 않으면 코드 구조와 import 문맥을 근거로 가능한 범위에서 추정한다.
4. 여러 파일 간 import 관계, 스키마 의존성, 실행 진입점, 환경변수 사용, 패키지 의존성을 함께 검토한다.
5. 단일 파일 코드처럼 보이면 단일 파일 기준으로 검토한다.
6. 파일 경계가 불명확하다는 이유만으로 검증을 포기하지 않는다.
7. 파일 경계가 불명확해서 확정할 수 없는 사항은 open_questions 또는 remaining_risks로 분리한다.
8. 코드 번들을 실제로 실행했다고 가정하지 말고, 정적 분석 관점에서 판단한다.
9. .env에 실제 API 키나 비밀값이 포함된 경우에는 보안 위험으로 판단한다.
10. 코드와 설명이 섞여 있으면 코드 검증에는 코드 부분을 우선한다.
"""


# ============================================================
# Input Normalizer
# ============================================================

KNOWN_FILENAMES = {
    "requirements.txt",
    ".env",
    ".env.example",
    ".gitignore",
    "config.py",
    "schemas.py",
    "prompts.py",
    "gemini_client.py",
    "agents.py",
    "agent.py",
    "council.py",
    "main.py",
    "check_gemini.py",
    "README.md",
    "pyproject.toml",
    "setup.py",
    "Dockerfile",
}

SENSITIVE_ENV_KEYWORDS = [
    "KEY",
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "PASS",
    "CREDENTIAL",
    "AUTH",
    "PRIVATE",
    "CERT",
    "DATABASE_URL",
    "DB_URL",
    "REDIS_URL",
    "MONGO_URL",
    "CONNECTION_STRING",
    "DSN",
    "WEBHOOK",
]


def detect_file_header(line: str) -> Optional[str]:
    original = line.strip()

    if not original:
        return None

    if original.startswith("```"):
        return None

    candidate = original.strip("=*-#` \t")

    candidate = re.sub(
        r"^\d+\.\s*",
        "",
        candidate,
    ).strip()

    candidate = re.sub(
        r"^(파일명|file|filename)\s*[:：]\s*",
        "",
        candidate,
        flags=re.IGNORECASE,
    ).strip()

    if candidate in KNOWN_FILENAMES:
        return candidate

    if candidate in [
        ".env",
        ".env.example",
        ".gitignore",
    ]:
        return candidate

    if re.fullmatch(
        r"[A-Za-z0-9_\-./]+\.(py|txt|md|json|toml|yaml|yml|ini|cfg)",
        candidate,
    ):
        return candidate

    return None


def trim_blank_lines(lines: list[str]) -> list[str]:
    start = 0
    end = len(lines)

    while start < end and not lines[start].strip():
        start += 1

    while end > start and not lines[end - 1].strip():
        end -= 1

    return lines[start:end]


def contains_korean(text: str) -> bool:
    return re.search(r"[가-힣]", text) is not None


def remove_markdown_fences(lines: list[str]) -> list[str]:
    result: list[str] = []

    for line in lines:
        if line.strip().startswith("```"):
            continue

        result.append(line)

    return result


def should_mask_env_value(key: str, value: str) -> bool:
    upper_key = key.upper()
    upper_value = value.upper()

    if any(
        keyword in upper_key
        for keyword in SENSITIVE_ENV_KEYWORDS
    ):
        return True

    if "://" in value and "@" in value:
        return True

    if "BEGIN PRIVATE KEY" in upper_value:
        return True

    return False


def sanitize_env_lines(lines: list[str]) -> list[str]:
    result: list[str] = []

    for line in remove_markdown_fences(lines):
        stripped = line.strip()

        if not stripped:
            result.append("")
            continue

        if stripped.startswith("#"):
            result.append(line)
            continue

        if "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*",
            key,
        ):
            continue

        if should_mask_env_value(key, value):
            result.append(f"{key}=<REDACTED>")
        else:
            result.append(f"{key}={value}")

    return trim_blank_lines(result)


def sanitize_requirements_lines(lines: list[str]) -> list[str]:
    result: list[str] = []

    requirement_pattern = re.compile(
        r"^[A-Za-z0-9_.-]+(\[[A-Za-z0-9_,.-]+\])?\s*"
        r"(==|>=|<=|~=|>|<|!=)\s*.+$"
    )

    simple_package_pattern = re.compile(
        r"^[A-Za-z0-9_.-]+$"
    )

    for line in remove_markdown_fences(lines):
        stripped = line.strip()

        if not stripped:
            result.append("")
            continue

        if stripped.startswith("#"):
            result.append(line)
            continue

        if contains_korean(stripped):
            continue

        if requirement_pattern.match(stripped):
            result.append(stripped)
            continue

        if simple_package_pattern.match(stripped):
            result.append(stripped)
            continue

        if stripped.startswith("-r "):
            result.append(stripped)
            continue

        if stripped.startswith("git+"):
            result.append(stripped)
            continue

        if stripped.startswith("http://") or stripped.startswith("https://"):
            result.append(stripped)
            continue

    return trim_blank_lines(result)


def sanitize_gitignore_lines(lines: list[str]) -> list[str]:
    return trim_blank_lines(
        remove_markdown_fences(lines)
    )


def sanitize_python_lines(lines: list[str]) -> list[str]:
    return trim_blank_lines(
        remove_markdown_fences(lines)
    )


def sanitize_generic_lines(lines: list[str]) -> list[str]:
    return trim_blank_lines(
        remove_markdown_fences(lines)
    )


def sanitize_file_content(filename: str, lines: list[str]) -> list[str]:
    if filename == "requirements.txt":
        return sanitize_requirements_lines(lines)

    if filename in [
        ".env",
        ".env.example",
    ]:
        return sanitize_env_lines(lines)

    if filename == ".gitignore":
        return sanitize_gitignore_lines(lines)

    if filename.endswith(".py"):
        return sanitize_python_lines(lines)

    return sanitize_generic_lines(lines)


def normalize_code_bundle(raw_text: str) -> tuple[str, list[str]]:
    lines = raw_text.splitlines()

    files: list[tuple[str, list[str]]] = []
    current_filename: Optional[str] = None
    current_lines: list[str] = []
    preamble_lines: list[str] = []

    for line in lines:
        detected_filename = detect_file_header(line)

        if detected_filename:
            if current_filename is not None:
                sanitized = sanitize_file_content(
                    current_filename,
                    current_lines,
                )

                if sanitized:
                    files.append(
                        (
                            current_filename,
                            sanitized,
                        )
                    )

            current_filename = detected_filename
            current_lines = []
            continue

        if current_filename is not None:
            current_lines.append(line)
        else:
            preamble_lines.append(line)

    if current_filename is not None:
        sanitized = sanitize_file_content(
            current_filename,
            current_lines,
        )

        if sanitized:
            files.append(
                (
                    current_filename,
                    sanitized,
                )
            )

    if not files:
        return (
            raw_text.strip(),
            [],
        )

    normalized_parts: list[str] = [
        "다음은 사용자가 붙여넣은 입력을 파일별 공통 양식으로 정규화한 코드 번들이다.",
        "각 부처장은 아래 전체 코드 번들을 동일하게 검토해야 한다.",
        "Python 코드는 원문 보존을 우선했으며, 마크다운 코드 fence만 제거되었을 수 있다.",
        "실제 비밀값으로 보이는 환경변수 값은 <REDACTED>로 마스킹되었을 수 있다.",
        "",
    ]

    cleaned_preamble = trim_blank_lines(
        remove_markdown_fences(preamble_lines)
    )

    if cleaned_preamble:
        normalized_parts.append("===== _입력_설명.txt =====")
        normalized_parts.extend(cleaned_preamble)
        normalized_parts.append("")

    detected_files: list[str] = []

    for filename, file_lines in files:
        detected_files.append(filename)
        normalized_parts.append(f"===== {filename} =====")
        normalized_parts.extend(file_lines)
        normalized_parts.append("")

    return (
        "\n".join(normalized_parts).strip(),
        detected_files,
    )


# ============================================================
# Gemini Client
# JSON 모드 + 로컬 Pydantic 검증 방식
# response_schema 직접 전달 안 함
# ============================================================

def make_schema_instruction(response_schema) -> str:
    schema = response_schema.model_json_schema()

    schema_json = json.dumps(
        schema,
        ensure_ascii=True,
        indent=2,
    )

    return (
        "Return exactly one JSON object that satisfies the following JSON Schema.\n"
        "Rules:\n"
        "1. Do not use markdown code blocks.\n"
        "2. Do not write any text outside the JSON object.\n"
        "3. Include all required fields.\n"
        "4. Use the exact field names from the schema.\n"
        "5. String values may be written in Korean.\n"
        "6. If there are no items for an array field, return an empty array.\n\n"
        f"JSON Schema:\n{schema_json}\n"
    )


def extract_json_object(text: str) -> str:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(
            r"^```[a-zA-Z0-9_-]*\s*",
            "",
            cleaned,
        )
        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned,
        ).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise RuntimeError(
            "Gemini 응답에서 JSON 객체를 찾지 못했습니다."
        )

    return cleaned[start:end + 1]


class GeminiClient:
    def __init__(self, model: str, role_name: str):
        self.client = genai.Client(
            api_key=GEMINI_API_KEY
        )
        self.model = model
        self.role_name = role_name

    async def generate(self, prompt: str, response_schema):
        last_error = None

        final_prompt = (
            prompt
            + "\n\n"
            + make_schema_instruction(response_schema)
        )

        for attempt in range(1, MAX_RETRIES + 1):
            try:

                def request():
                    response = self.client.models.generate_content(
                        model=self.model,
                        contents=final_prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.2,
                            max_output_tokens=8192,
                        ),
                    )

                    if not response.text:
                        raise RuntimeError(
                            "Gemini가 빈 응답을 반환했습니다."
                        )

                    json_text = extract_json_object(
                        response.text
                    )

                    data = json.loads(
                        json_text
                    )

                    return response_schema.model_validate(
                        data
                    )

                return await asyncio.to_thread(
                    request
                )

            except Exception as error:
                last_error = error

                if attempt < MAX_RETRIES:
                    wait_seconds = 2 ** (attempt - 1)

                    print(f"    Gemini 호출 실패 ({attempt}/{MAX_RETRIES})")
                    print(f"    역할: {self.role_name}")
                    print(f"    사용 모델: {self.model}")
                    print(f"    오류 내용: {error}")
                    print(f"    {wait_seconds}초 후 재시도합니다.")

                    await asyncio.sleep(
                        wait_seconds
                    )

        raise RuntimeError(
            f"Gemini 호출이 {MAX_RETRIES}회 실패했습니다. "
            f"역할: {self.role_name}, "
            f"사용 모델: {self.model}, "
            f"마지막 오류: {last_error}"
        )

# ============================================================
# Agent Layer
# ============================================================

class CodeCouncilAgents:
    def __init__(self):
        self.agent_gemini = GeminiClient(
            model=AGENT_MODEL,
            role_name="부처장 Agent",
        )
        self.judge_gemini = GeminiClient(
            model=JUDGE_MODEL,
            role_name="Judge",
        )
        self.implementation_gemini = GeminiClient(
            model=IMPLEMENTATION_MODEL,
            role_name="Implementation Agent",
        )

    @staticmethod
    def json_dump_model(model) -> str:
        return json.dumps(
            model.model_dump(),
            ensure_ascii=False,
            indent=2,
        )

    async def review_agent(
        self,
        name: str,
        code: str,
        round_number: int,
        previous_review: Optional[str] = None,
        judge_feedback: Optional[str] = None,
    ) -> AgentReview:
        rubric = AGENT_RUBRICS[name]

        previous_review_text = (
            previous_review
            if previous_review
            else "이전 자기 보고서 없음. 이번이 1차 검증이다."
        )

        judge_feedback_text = (
            judge_feedback
            if judge_feedback
            else "Judge가 이 부처에 전달한 별도 피드백 없음."
        )

        prompt = f"""
너는 AI 코드 사전 검증회의 "{name}" 부처장이다.

중요한 구조적 사실:

Gemini가 실제로 여러 인격을 가지는 것이 아니다.
하나의 모델을 역할별로 독립 호출하는 구조이며,
너는 지금 "{name}" 부처장 역할로만 동작해야 한다.

너는 다른 부처장의 의견을 볼 수 없다.
너에게 제공되는 정보는 다음뿐이다.

1. 정규화된 검증 대상 코드 또는 코드 번들
2. 현재 회차
3. 너 자신의 이전 회차 보고서
4. Judge가 너에게만 전달한 피드백

다른 부처장의 의견을 추측하거나 인용하지 마라.

========== 현재 회차 ==========

{round_number}차

========== 너의 전문 검토 기준 ==========

{rubric}

========== 검증 대상 코드 또는 코드 번들 ==========

{CODE_BUNDLE_NOTICE}

{code}

========== 너 자신의 이전 회차 보고서 ==========

{previous_review_text}

========== Judge가 너에게만 전달한 피드백 ==========

{judge_feedback_text}

========== 지시사항 ==========

다음 원칙을 반드시 지켜라.

1. 코드에 근거한 내용만 지적한다.
2. 불확실하면 confidence를 낮춘다.
3. Judge 피드백이 있다면 해당 항목을 우선적으로 재검토한다.
4. 다른 부처장 의견은 제공받지 않았으므로 언급하지 않는다.
5. 단순 취향과 실제 결함을 구분한다.
6. severity는 신중하게 부여한다.
7. findings가 없으면 억지로 만들지 않는다.
8. 모든 설명은 한국어로 작성한다.
9. department 필드에는 반드시 "{name}"을 입력한다.
10. round_number 필드에는 반드시 {round_number}을 입력한다.
11. 여러 파일 코드 번들이면 파일 간 의존성도 너의 전문 관점에서 검토한다.

반드시 지정된 구조화 출력 형식에 맞춰 응답하라.
"""

        return await self.agent_gemini.generate(
            prompt,
            AgentReview,
        )

    async def judge(
        self,
        code: str,
        reports: dict[str, AgentReview],
        round_number: int,
    ) -> JudgeDecision:
        reports_text = "\n\n".join(
            f"""
========== {name} 부처장 보고서 ==========

{self.json_dump_model(report)}
"""
            for name, report in reports.items()
        )

        prompt = f"""
{JUDGE_PROMPT}

========== 현재 회차 ==========

{round_number}차

========== 최대 검증 회차 ==========

{MAX_REVIEW_ROUNDS}차

========== 검증 대상 코드 또는 코드 번들 ==========

{CODE_BUNDLE_NOTICE}

{code}

========== 8개 부처장 보고서 ==========

{reports_text}

========== 지시사항 ==========

현재 회차가 최대 검증 회차와 같거나 크다면 반드시 FINALIZE를 반환하라.

재검증이 필요하다고 판단하는 경우,
review_instructions에는 각 부처장에게 전달할 개별 지시만 작성하라.

approved_changes에는 Implementation Agent가 실제 코드에 반영해야 할 항목만 작성하라.

approved_changes에 단순 취향, 근거 약한 제안, 과도한 리팩터링을 넣지 마라.

여러 파일 코드 번들이면 import 관계, 파일 누락, 설정 파일, requirements.txt, 실행 진입점을 함께 판단하라.

모든 판단은 한국어로 작성하라.
반드시 지정된 구조화 출력 형식에 맞춰 응답하라.
"""

        return await self.judge_gemini.generate(
            prompt,
            JudgeDecision,
        )

    async def implementation(
        self,
        original_code: str,
        reports: dict[str, AgentReview],
        judge_decision: JudgeDecision,
    ) -> FinalCode:
        approved_changes = "\n".join(
            f"- {item}"
            for item in judge_decision.approved_changes
        )

        if not approved_changes:
            approved_changes = (
                "Judge가 승인한 수정사항이 없습니다. "
                "원본 코드를 불필요하게 변경하지 마세요."
            )

        reports_text = "\n\n".join(
            f"""
========== {name} 부처장 ==========

{self.json_dump_model(report)}
"""
            for name, report in reports.items()
        )

        judge_text = self.json_dump_model(judge_decision)

        prompt = f"""
{IMPLEMENTATION_PROMPT}

========== 원본 코드 또는 코드 번들 ==========

{CODE_BUNDLE_NOTICE}

{original_code}

========== Judge가 승인한 수정사항 ==========

{approved_changes}

========== Judge 최종 판정 ==========

{judge_text}

========== 전문 부처장 보고서 ==========

{reports_text}

========== 모든 자료 끝 ==========

이제 최종 코드를 작성하라.

가장 중요한 규칙:

Judge가 승인한 수정사항만 코드에 반영한다.

부처장이 제안했지만 Judge가 승인하지 않은 사항은
임의로 반영하지 마라.

Judge가 승인한 수정사항이 없다면,
원본 코드를 그대로 유지하는 것이 원칙이다.

final_code 필드에는 마크다운 코드블록을 넣지 말고,
실제 코드 문자열만 넣어라.

원본이 여러 파일로 구성된 코드 번들이라면,
final_code 필드에는 수정된 전체 코드 번들을 파일별 구분과 함께 출력하라.

권장 출력 형식:

===== 파일명 =====
수정된 코드

===== 파일명 =====
수정된 코드

파일 경계가 불명확하면 원본의 구분 방식을 최대한 유지하라.

모든 설명은 한국어로 작성하라.
반드시 지정된 구조화 출력 형식에 맞춰 응답하라.
"""

        return await self.implementation_gemini.generate(
            prompt,
            FinalCode,
        )


# ============================================================
# Council Engine
# ============================================================

class CodeCouncil:
    def __init__(self):
        self.agents = CodeCouncilAgents()

    @staticmethod
    def json_dump_model(model) -> str:
        return json.dumps(
            model.model_dump(),
            ensure_ascii=False,
            indent=2,
        )

    def build_feedback(self, judge: JudgeDecision) -> dict[str, str]:
        feedback: dict[str, list[str]] = {
            name: []
            for name in AGENT_RUBRICS.keys()
        }

        for instruction in judge.review_instructions:
            if instruction.department in feedback:
                feedback[instruction.department].extend(
                    instruction.instructions
                )

        result: dict[str, str] = {}

        for name in AGENT_RUBRICS.keys():
            items = feedback[name]

            if items:
                result[name] = "\n".join(
                    f"- {item}"
                    for item in items
                )
            else:
                result[name] = (
                    "Judge가 이 부처에 별도 재검증 지시사항을 내리지 않았습니다. "
                    "이전 자기 의견 중 불확실한 부분이 있다면 다시 검토하세요."
                )

        return result

    async def run_agent_reviews(
        self,
        code: str,
        round_number: int,
        previous_reviews: Optional[dict[str, str]],
        judge_feedback: Optional[dict[str, str]],
    ) -> dict[str, AgentReview]:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_AGENTS)

        async def run_one_agent(name: str):
            async with semaphore:
                return await self.agents.review_agent(
                    name=name,
                    code=code,
                    round_number=round_number,
                    previous_review=(
                        previous_reviews.get(name)
                        if previous_reviews
                        else None
                    ),
                    judge_feedback=(
                        judge_feedback.get(name)
                        if judge_feedback
                        else None
                    ),
                )

        tasks = {
            name: asyncio.create_task(
                run_one_agent(name)
            )
            for name in AGENT_RUBRICS.keys()
        }

        results = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True,
        )

        reports: dict[str, AgentReview] = {}
        failures: list[str] = []

        for name, result in zip(
            tasks.keys(),
            results,
        ):
            if isinstance(result, Exception):
                failures.append(
                    f"{name} 부처장 호출 실패: {result}"
                )
            else:
                reports[name] = result

        if failures:
            failure_text = "\n".join(
                f"- {item}"
                for item in failures
            )

            raise RuntimeError(
                "일부 부처장 호출이 실패했습니다.\n"
                "불완전한 검증을 정상 검증으로 취급하지 않기 위해 "
                "Judge 단계로 진행하지 않습니다.\n\n"
                f"{failure_text}"
            )

        expected_count = len(AGENT_RUBRICS)

        if len(reports) != expected_count:
            raise RuntimeError(
                "부처장 보고서 수가 예상과 다릅니다.\n"
                f"예상: {expected_count}개, 실제: {len(reports)}개\n"
                "불완전한 검증을 정상 검증으로 취급하지 않습니다."
            )

        return reports

    async def run_review(
        self,
        code: str,
    ) -> tuple[
        dict[str, AgentReview],
        JudgeDecision,
        int,
    ]:
        previous_reviews: Optional[dict[str, str]] = None
        judge_feedback: Optional[dict[str, str]] = None

        for round_number in range(1, MAX_REVIEW_ROUNDS + 1):
            print()
            print("=" * 70)
            print(f"{round_number}차 코드 검증 시작")
            print("=" * 70)

            print()
            print(">>> 8개 부처장 병렬 검증을 시작합니다.")
            print(f">>> 현재 병렬 호출 수: {MAX_CONCURRENT_AGENTS}")

            reports = await self.run_agent_reviews(
                code=code,
                round_number=round_number,
                previous_reviews=previous_reviews,
                judge_feedback=judge_feedback,
            )

            print()
            print(">>> 8개 부처장 검증이 모두 완료되었습니다.")

            print()
            print(">>> Judge 판정을 시작합니다.")

            judge = await self.agents.judge(
                code=code,
                reports=reports,
                round_number=round_number,
            )

            print()
            print(f">>> Judge 결정: {judge.decision}")
            print(f">>> Judge 종합점수: {judge.overall_score}/10")
            print(f">>> Judge 확신도: {judge.confidence}/100")

            if (
                round_number >= MAX_REVIEW_ROUNDS
                and judge.decision == "REVIEW"
            ):
                print()
                print(">>> 최대 검증 횟수에 도달했습니다.")
                print(
                    ">>> Judge가 REVIEW를 반환했지만 "
                    "시스템 규칙에 따라 FINALIZE로 확정합니다."
                )

                judge.decision = "FINALIZE"
                judge.rationale = (
                    judge.rationale
                    + "\n\n시스템 규칙: 최대 검증 횟수에 도달하여 "
                    "REVIEW를 FINALIZE로 확정했습니다."
                )

            if judge.decision == "FINALIZE":
                print()
                print(">>> 코드 검증 확정")

                return (
                    reports,
                    judge,
                    round_number,
                )

            previous_reviews = {
                name: self.json_dump_model(report)
                for name, report in reports.items()
            }

            judge_feedback = self.build_feedback(judge)

            print()
            print(">>> Judge가 재검증을 결정했습니다.")
            print(
                ">>> 다음 회차에서 각 부처장은 "
                "자기 이전 의견과 Judge의 자기 부처 피드백만 받습니다."
            )

        raise RuntimeError(
            "검증 엔진이 예상치 못하게 종료되었습니다."
        )

    async def run_implementation(
        self,
        code: str,
        reports: dict[str, AgentReview],
        judge: JudgeDecision,
    ) -> FinalCode:
        print()
        print("=" * 70)
        print("Implementation Agent 수정 단계")
        print("=" * 70)

        print()
        print(">>> Judge가 승인한 수정사항만 반영합니다.")

        return await self.agents.implementation(
            original_code=code,
            reports=reports,
            judge_decision=judge,
        )


# ============================================================
# CLI
# ============================================================

def read_code_input() -> str:
    print("=" * 70)
    print("AI 코드 사전 검증회")
    print("=" * 70)
    print()
    print("프로젝트에 넣기 전에 검증받고 싶은 코드를 붙여넣으세요.")
    print("단일 파일 코드도 가능하고, 여러 파일 전체 코드 묶음도 가능합니다.")
    print("번호, 설명, 파일명, 코드가 섞여 있어도 가능한 범위에서 정리합니다.")
    print("파일 구분이 있으면 더 정확합니다.")
    print("입력이 끝나면 새로운 줄에 END 또는 <<<END>>>를 입력하세요.")
    print()

    lines: list[str] = []

    while True:
        try:
            line = input()
        except EOFError:
            break

        if line.strip() in [
            "END",
            "<<<END>>>",
        ]:
            break

        lines.append(line)

    raw_code = "\n".join(lines).strip()

    if not raw_code:
        raise ValueError("입력된 코드가 없습니다.")

    normalized_code, detected_files = normalize_code_bundle(raw_code)

    print()
    print("=" * 70)
    print("입력 정규화 결과")
    print("=" * 70)

    if detected_files:
        print("다음 파일들을 감지했습니다.")
        print()

        for filename in detected_files:
            print(f"- {filename}")

        print()
        print(
            "위 파일들을 공통 코드 번들 형식으로 정리한 뒤 "
            "8개 부처장에게 동일하게 전달합니다."
        )

    else:
        print("명확한 파일 경계를 감지하지 못했습니다.")
        print(
            "입력 전체를 단일 코드 또는 텍스트 코드 번들로 간주하고 검증합니다."
        )

    return normalized_code


def ask_should_implement() -> bool:
    print()
    print("=" * 70)
    print("선택")
    print("=" * 70)
    print()
    print("Judge가 승인한 수정사항만 반영한 코드를 생성할까요?")
    print("기본 목적이 사전 검증이라면 n을 선택해도 됩니다.")
    print()
    print("y: 수정 코드 생성")
    print("n: 검증 결과만 보고 종료")
    print()

    while True:
        answer = input("선택하세요 [y/n]: ").strip().lower()

        if answer in [
            "y",
            "yes",
        ]:
            return True

        if answer in [
            "n",
            "no",
        ]:
            return False

        print("y 또는 n으로 입력하세요.")


def print_review_result(
    reports: dict[str, AgentReview],
    judge: JudgeDecision,
    round_number: int,
) -> None:
    print()
    print("=" * 70)
    print("코드 사전 검증 결과")
    print("=" * 70)

    print()
    print(f"종료 회차: {round_number}차")
    print(f"Judge 결정: {judge.decision}")
    print(f"Judge 종합점수: {judge.overall_score}/10")
    print(f"Judge 확신도: {judge.confidence}/100")

    print()
    print("-" * 70)
    print("Judge 판단 근거")
    print("-" * 70)
    print(judge.rationale)

    print()
    print("-" * 70)
    print("핵심 문제")
    print("-" * 70)

    if judge.key_issues:
        for item in judge.key_issues:
            print(f"- {item}")
    else:
        print("현재 검증에서 확인된 핵심 문제가 없습니다.")

    print()
    print("-" * 70)
    print("합의 사항")
    print("-" * 70)

    if judge.agreements:
        for item in judge.agreements:
            print(f"- {item}")
    else:
        print("명시적인 합의 사항이 없습니다.")

    print()
    print("-" * 70)
    print("의견 충돌")
    print("-" * 70)

    if judge.conflicts:
        for item in judge.conflicts:
            print(f"- {item}")
    else:
        print("중요한 의견 충돌이 확인되지 않았습니다.")

    print()
    print("-" * 70)
    print("Judge가 승인한 수정 권고")
    print("-" * 70)

    if judge.approved_changes:
        for item in judge.approved_changes:
            print(f"- {item}")
    else:
        print("Judge가 승인한 수정사항이 없습니다.")

    print()
    print("-" * 70)
    print("부처장별 요약")
    print("-" * 70)

    for name, report in reports.items():
        print()
        print(f"[{name} 부처장]")
        print(f"- 점수: {report.score}/10")
        print(f"- 확신도: {report.confidence}/100")
        print(f"- 총평: {report.summary}")

        if report.findings:
            print("- 발견사항:")
            for finding in report.findings:
                print(f"  - [{finding.severity}] {finding.title}")
        else:
            print("- 발견사항: 없음")


def print_final_code(final_code: FinalCode) -> None:
    print()
    print("=" * 70)
    print("수정 코드 생성 결과")
    print("=" * 70)

    print()
    print(f"최종점수: {final_code.final_score}/10")

    print()
    print("-" * 70)
    print("요약")
    print("-" * 70)
    print(final_code.summary)

    print()
    print("-" * 70)
    print("실제로 반영된 수정사항")
    print("-" * 70)

    if final_code.changes:
        for item in final_code.changes:
            print(f"- {item}")
    else:
        print("실제로 반영된 수정사항이 없습니다.")

    print()
    print("-" * 70)
    print("남은 위험")
    print("-" * 70)

    if final_code.remaining_risks:
        for risk in final_code.remaining_risks:
            print(f"- {risk}")
    else:
        print("현재 확인된 중대한 남은 위험이 없습니다.")

    print()
    print("=" * 70)
    print("최종 코드")
    print("=" * 70)
    print()
    print(final_code.final_code)


# ============================================================
# Gemini Check
# ============================================================

def check_gemini() -> None:
    validate_config()

    target_models: list[str] = []

    for model in [
        GEMINI_MODEL,
        AGENT_MODEL,
        JUDGE_MODEL,
        IMPLEMENTATION_MODEL,
    ]:
        if model and model not in target_models:
            target_models.append(model)

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    print("=" * 70)
    print("Gemini 모델 JSON 출력 + Pydantic 검증 테스트")
    print("=" * 70)

    for model_name in target_models:
        print()
        print("-" * 70)
        print(f"테스트 모델: {model_name}")
        print("-" * 70)

        try:
            prompt = (
                "Return a JSON object.\n"
                "Question: What is one plus one?\n\n"
                + make_schema_instruction(TestResponse)
            )

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    max_output_tokens=1024,
                ),
            )

            if not response.text:
                raise RuntimeError(
                    "Gemini가 빈 응답을 반환했습니다."
                )

            json_text = extract_json_object(
                response.text
            )

            data = json.loads(
                json_text
            )

            parsed = TestResponse.model_validate(
                data
            )

            print("호출 성공")
            print(
                json.dumps(
                    parsed.model_dump(),
                    ensure_ascii=False,
                    indent=2,
                )
            )

        except Exception as error:
            print("호출 실패")
            print(f"오류 내용: {error}")
            print()
            print("이 모델이 현재 API 키에서 지원되지 않거나,")
            print("모델명 또는 JSON 출력 설정을 확인해야 합니다.")

    print()
    print("=" * 70)
    print("테스트 종료")
    print("=" * 70)

# ============================================================
# Main
# ============================================================

async def run() -> None:
    validate_config()

    code = read_code_input()

    council = CodeCouncil()

    reports, judge, round_number = await council.run_review(code)

    print_review_result(
        reports=reports,
        judge=judge,
        round_number=round_number,
    )

    should_implement = ask_should_implement()

    if should_implement:
        final_code = await council.run_implementation(
            code=code,
            reports=reports,
            judge=judge,
        )

        print_final_code(final_code)

    else:
        print()
        print("=" * 70)
        print("검증 결과만 출력하고 종료합니다.")
        print("=" * 70)


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--check":
            check_gemini()
        else:
            asyncio.run(run())

    except KeyboardInterrupt:
        print()
        print("사용자가 실행을 중단했습니다.")

    except Exception as error:
        print()
        print("=" * 70)
        print("실행 중 오류가 발생했습니다.")
        print(f"오류 내용: {error}")
        print("=" * 70)

