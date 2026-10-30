"""Standard-library-only dataclasses for the offline scanner.

The legacy Gemini schemas still live in review_models.py, but the offline
Windows executable must not import their third-party validation libraries.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
Perspective = Literal[
    "security", "reliability", "testing", "architecture",
    "maintainability", "performance", "resource_use", "complexity_cost",
]


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
