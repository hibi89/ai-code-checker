from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from code_input import bundle_from_text
from reporting import convert_ai_findings, render_report, verify_ai_citation
from review_models import AIReview, AIReviewFinding, PerspectiveCheck, TokenUsage
from reviewer import ReviewError, analyze_bundle, append_usage_log, estimate_request_cost


PERSPECTIVES = [
    "security", "reliability", "testing", "architecture",
    "maintainability", "performance", "resource_use", "complexity_cost",
]


def empty_review() -> AIReview:
    return AIReview(
        summary="검수 완료",
        checks=[
            PerspectiveCheck(perspective=perspective, status="no_clear_issue", summary="명확한 항목 없음")
            for perspective in PERSPECTIVES
        ],
        findings=[],
        limitations=[],
    )


class FakeModels:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class ReviewFlowTests(unittest.TestCase):
    def test_citation_requires_matching_path_line_and_exact_excerpt(self) -> None:
        bundle = bundle_from_text("def read_user(user_id):\n    return user_id\n")
        finding = AIReviewFinding(
            severity="MEDIUM",
            perspective="reliability",
            title="결과 확인 필요",
            file_path="stdin.py",
            start_line=2,
            end_line=2,
            evidence="return user_id",
            impact="맥락을 더 확인해야 합니다.",
            recommendation="호출부를 확인하세요.",
            confidence=55,
        )
        self.assertTrue(verify_ai_citation(finding, bundle))

        wrong_line = finding.model_copy(update={"start_line": 1, "end_line": 1})
        wrong_path = finding.model_copy(update={"file_path": "../secret.py"})
        self.assertFalse(verify_ai_citation(wrong_line, bundle))
        self.assertFalse(verify_ai_citation(wrong_path, bundle))

    def test_single_structured_request_records_provider_usage(self) -> None:
        response = SimpleNamespace(
            parsed=empty_review(),
            text=None,
            usage_metadata=SimpleNamespace(
                prompt_token_count=1200,
                candidates_token_count=300,
                thoughts_token_count=50,
                total_token_count=1550,
            ),
        )
        models = FakeModels(response)
        client = SimpleNamespace(models=models)
        bundle = bundle_from_text("print('hello')\n")

        review, usage, estimate, warnings = analyze_bundle(
            bundle,
            api_key="test-only",
            client=client,
        )

        self.assertEqual(len(models.calls), 1)
        self.assertEqual(models.calls[0]["config"].max_output_tokens, 2048)
        self.assertTrue(models.calls[0]["config"].automatic_function_calling.disable)
        self.assertIsInstance(review, AIReview)
        self.assertEqual(usage.model, "gemini-3.1-flash-lite")
        self.assertEqual(usage.input_tokens, 1200)
        self.assertEqual(usage.output_tokens, 350)
        self.assertAlmostEqual(usage.estimated_cost_usd or 0, 0.000825)
        self.assertGreater(estimate.max_estimated_cost_usd, 0)
        self.assertEqual(warnings, [])

    def test_api_failure_does_not_retry_or_echo_request_contents(self) -> None:
        class FailingModels:
            def __init__(self):
                self.calls = 0

            def generate_content(self, **kwargs):
                self.calls += 1
                raise ConnectionError("private provider diagnostic")

        models = FailingModels()
        client = SimpleNamespace(models=models)
        source_secret = "sample-private-source-marker"
        bundle = bundle_from_text(f"print('{source_secret}')\n")

        with self.assertRaises(ReviewError) as error:
            analyze_bundle(bundle, api_key="test-only", client=client)

        self.assertEqual(models.calls, 1)
        self.assertNotIn(source_secret, str(error.exception))
        self.assertNotIn("private provider diagnostic", str(error.exception))

    def test_provider_error_exposes_status_but_not_raw_details(self) -> None:
        class ProviderClientError(RuntimeError):
            code = 400
            status = "INVALID_ARGUMENT"
            message = "private provider diagnostic"

        class FailingModels:
            def generate_content(self, **kwargs):
                raise ProviderClientError()

        client = SimpleNamespace(models=FailingModels())
        with self.assertRaises(ReviewError) as error:
            analyze_bundle(
                bundle_from_text("print('synthetic')\n"),
                api_key="test-only",
                client=client,
            )
        self.assertIn("HTTP 400", str(error.exception))
        self.assertIn("INVALID_ARGUMENT", str(error.exception))
        self.assertNotIn("private provider diagnostic", str(error.exception))

    def test_preflight_budget_stops_before_external_api_call(self) -> None:
        models = FakeModels(None)
        client = SimpleNamespace(models=models)
        bundle = bundle_from_text("print('hello')\n")

        with self.assertRaises(ReviewError):
            analyze_bundle(
                bundle,
                api_key="test-only",
                client=client,
                max_estimated_cost_usd=0.000000001,
            )
        self.assertEqual(models.calls, [])

    def test_preflight_estimate_includes_structured_prompt(self) -> None:
        estimate = estimate_request_cost("hello", 0.25, 1.50, 2048)
        self.assertGreater(estimate.estimated_input_tokens, 100)
        self.assertGreater(estimate.max_estimated_cost_usd, 0)

    def test_usage_log_contains_counts_but_no_source(self) -> None:
        usage = TokenUsage(
            model="gemini-3.1-flash-lite",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            estimated_cost_usd=0.000155,
            cost_basis="test",
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / ".ai-code-checker" / "usage.jsonl"
            append_usage_log(usage, path=path, order_ref="KM-01")
            contents = path.read_text(encoding="utf-8")
            record = json.loads(contents)

        self.assertEqual(record["order_ref"], "KM-01")
        self.assertEqual(record["input_tokens"], 100)
        self.assertNotIn("print(", contents)

    def test_report_labels_unverified_ai_citations(self) -> None:
        bundle = bundle_from_text("print('hello')\n")
        review = empty_review().model_copy(update={
            "findings": [AIReviewFinding(
                severity="HIGH",
                perspective="security",
                title="근거 위치 오류 예시",
                file_path="missing.py",
                start_line=500,
                end_line=500,
                evidence="not present",
                impact="영향 설명",
                recommendation="확인",
                confidence=70,
            )],
        })
        ai_findings = convert_ai_findings(review, bundle)
        report = render_report(
            bundle=bundle,
            static_findings=[],
            ai_review=review,
            ai_findings=ai_findings,
            usage=TokenUsage("gemini-3.1-flash-lite", 10, 10, 20, 0.0000175, "test"),
            preflight_cost_usd=0.001,
            cost_limit_usd=0.05,
        )

        self.assertFalse(ai_findings[0].citation_verified)
        self.assertIn("원본 대조 실패", report)
        self.assertIn("결함 자체를 증명하지는 않습니다", report)


if __name__ == "__main__":
    unittest.main()
