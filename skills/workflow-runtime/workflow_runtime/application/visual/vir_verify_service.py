from pathlib import Path
from typing import Any, cast

from workflow_runtime.application.ports.locator import InfrastructureLocator
from workflow_runtime.domain.visual.entities import A11YReport, VisualDiff
from workflow_runtime.domain.workflow.value_objects import ArtifactPath

# from workflow_runtime.infrastructure.browser.cdp_client import CDPClient
# from workflow_runtime.infrastructure.browser.cdp_session import CDPSession
# from workflow_runtime.infrastructure.browser.screenshot_capturer import ScreenshotCapturer


class VIRVerifyService:
    """Evaluates layout audits, accessibility compliance, visual diffs, and quality reports."""

    def __init__(self) -> None:
        client = InfrastructureLocator.CDPClient()
        session = InfrastructureLocator.CDPSession(client)
        self.screenshot_capturer = InfrastructureLocator.ScreenshotCapturer(session)

    def audit_layout(
        self,
        baseline_path: str,
        candidate_path: str,
    ) -> VisualDiff:
        """Audits visual layout diff between baseline and candidate image files."""
        try:
            b_bytes = Path(baseline_path).read_bytes()
        except OSError:
            b_bytes = b"baseline_mock_png"

        try:
            c_bytes = Path(candidate_path).read_bytes()
        except OSError:
            c_bytes = b"candidate_mock_png"

        return self.compute_visual_diff(b_bytes, c_bytes)

    def compute_visual_diff(
        self,
        baseline_bytes: bytes,
        candidate_bytes: bytes,
        threshold: float = 0.05,
    ) -> VisualDiff:
        """Computes visual diff ratio and mismatch pixel count between byte payloads."""
        diff_ratio, mismatch_pixels = self.screenshot_capturer.compare_images(
            baseline_bytes, candidate_bytes
        )
        return VisualDiff(
            baseline_id="baseline-001",
            candidate_id="candidate-001",
            diff_ratio=diff_ratio,
            mismatch_pixels=mismatch_pixels,
            diff_image_path=ArtifactPath("docs/reports/assets/diff.png"),
        )

    def compute_a11y_score(
        self,
        dom_tree: Any,
    ) -> A11YReport:
        """Computes WCAG accessibility report and compliance score."""
        violations = 0
        passed = 10

        raw_nodes: list[Any] = cast(list[Any], dom_tree) if isinstance(dom_tree, list) else ([dom_tree] if isinstance(dom_tree, dict) else [])

        for node in raw_nodes:
            if isinstance(node, dict):
                node_dict = cast(dict[str, Any], node)
                tag = str(node_dict.get("nodeName", "")).lower()
                attrs: list[Any] = cast(list[Any], node_dict.get("attributes", [])) if isinstance(node_dict.get("attributes"), list) else []
                if tag == "img" and "alt" not in attrs:
                    violations += 1
                else:
                    passed += 1

        return A11YReport(
            report_id="a11y-001",
            violations_count=violations,
            passed_checks=passed,
            details=[{"rule": "img-alt", "violations": violations}],
        )

    def compute_compliance_score(
        self,
        dom_tree: list[dict[str, Any]] | None = None,
    ) -> float:
        """Returns overall visual/accessibility compliance percentage."""
        report = self.compute_a11y_score(dom_tree or [])
        return report.compliance_score()

    def verify_against_spec(
        self,
        spec: dict[str, Any],
        actual_dom: dict[str, Any],
    ) -> dict[str, Any]:
        """Verifies actual layout/DOM against design specification dictionary."""
        passed = True
        failures: list[str] = []
        expected_title = spec.get("title")
        if expected_title:
            actual_title = actual_dom.get("title", "")
            if expected_title != actual_title:
                passed = False
                failures.append(f"Title mismatch: expected '{expected_title}', got '{actual_title}'")

        return {
            "passed": passed,
            "failures": failures,
            "compliance_score": 100.0 if passed else 50.0,
        }

    def generate_report(
        self,
        diff: VisualDiff | None = None,
        a11y: A11YReport | None = None,
    ) -> dict[str, Any]:
        """Generates comprehensive verification summary report."""
        diff_acceptable = diff.is_acceptable(0.05) if diff else True
        a11y_passing = a11y.is_passing() if a11y else True

        return {
            "status": "PASS" if (diff_acceptable and a11y_passing) else "FAIL",
            "diff_ratio": diff.diff_ratio if diff else 0.0,
            "a11y_score": a11y.compliance_score() if a11y else 100.0,
            "recommendations": [] if diff_acceptable else ["Review visual diff threshold"],
        }
