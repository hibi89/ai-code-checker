"""Typed review results used both by Gemini structured output and reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
Perspective = Literal[
    "security",
    "reliability",
    "testing",
    "architecture",
    "maintainability",
    "performance",
    "resource_use",
    "complexity_cost",
]
CheckStatus = Literal["issue_found", "no_clear_issue", "not_enough_context"]


class AIReviewFinding(BaseModel):
    severity: Severity = Field(description="Severity based on concrete impact")
    perspective: Perspective = Field(description="One of the eight review perspectives")
    title: str = Field(description="Short Korean finding title")
    file_path: str = Field(description="Exact relative file path from the supplied bundle, or empty if unknown")
    start_line: int | None = Field(default=None, ge=1, description="One-based start line, or null if unknown")
    end_line: int | None = Field(default=None, ge=1, description="One-based end line, or null if unknown")
    evidence: str = Field(description="A short exact code excerpt from the supplied source, or empty if unavailable")
    impact: str = Field(description="Concrete possible impact, without overstating certainty")
    recommendation: str = Field(description="Actionable mitigation or next check")
    confidence: int = Field(ge=0, le=100, description="Confidence that the source supports this finding")


class PerspectiveCheck(BaseModel):
    perspective: Perspective = Field(description="Review perspective")
    status: CheckStatus = Field(description="Whether a clear issue was found or context was insufficient")
    summary: str = Field(description="Short Korean summary for this perspective")


class AIReview(BaseModel):
    summary: str = Field(description="Overall Korean summary of the reviewed source")
    checks: list[PerspectiveCheck] = Field(description="One status item for each of the eight perspectives")
    findings: list[AIReviewFinding] = Field(description="Concrete source-based findings; empty when none are supported")
    limitations: list[str] = Field(description="Specific limitations caused by missing context or unsupported files")


@dataclass(frozen=True)
class CodeFinding:
    severity: Severity
    perspective: Perspective
    title: str
    file_path: str
    start_line: int | None
    end_line: int | None
    evidence: str
    impact: str
    recommendation: str
    confidence: int
    source: Literal["static", "ai"]
    citation_verified: bool


@dataclass(frozen=True)
class TokenUsage:
    model: str
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    estimated_cost_usd: float | None
    cost_basis: str
    duration_ms: int | None = None
    request_count: int = 1
