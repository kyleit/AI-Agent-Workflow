import os
import json
from typing import Optional
from vir_runtime.varbc.domain.report import VARReport
from vir_runtime.varbc.application.ports import ReportRepositoryPort
from vir_runtime.varbc.domain.errors import RepositoryIOError


class FileReportRepo(ReportRepositoryPort):
    """File-system based storage adapter for VARReport records and assets."""

    def __init__(
        self,
        reports_dir: str = "docs/reports",
        assets_dir: str = "docs/reports/assets",
    ) -> None:
        """Initializes report repository paths."""
        self._reports_dir = reports_dir
        self._assets_dir = assets_dir
        os.makedirs(self._reports_dir, exist_ok=True)
        os.makedirs(self._assets_dir, exist_ok=True)

    async def save_report(self, report: VARReport) -> None:
        """Saves report JSON and Markdown summary to reports_dir.

        1. Path json_path = os.path.join(self._reports_dir, f"VAR_REPORT_{report.id}.json")
        2. Path md_path = os.path.join(self._reports_dir, f"VAR_REPORT_{report.id}.md")
        3. Write report.model_dump_json(indent=2) to json_path.
        4. Format Markdown content with status, score, diff summary table, and write to md_path.
        """
        try:
            json_path = os.path.join(
                self._reports_dir, f"VAR_REPORT_{report.id}.json"
            )
            md_path = os.path.join(
                self._reports_dir, f"VAR_REPORT_{report.id}.md"
            )

            with open(json_path, "w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))

            # Format Markdown table
            diff_rows = ""
            for diff in report.diffs:
                issues_str = "; ".join(diff.issues) if diff.issues else "None"
                diff_rows += f"| {diff.baseline_id} | {diff.observation_id} | {diff.diff_score} | {issues_str} |\n"
            if not diff_rows:
                diff_rows = "| - | - | - | No diffs performed |\n"

            md_content = f"""# Visual Agentic Runtime Verification Report

- **Report ID**: `{report.id}`
- **Generated At**: `{report.generated_at.isoformat()}`
- **Overall Status**: **{report.status.value}**
- **Passed**: `{report.passed}`
- **Compliance Score**: `{report.score}/100.0`

## Visual Diffs Summary

| Baseline ID | Observation ID | Diff Score | Issues |
| :--- | :--- | :--- | :--- |
{diff_rows}
"""
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content)

        except Exception as e:
            raise RepositoryIOError(
                f"Failed to save report '{report.id}': {e}"
            ) from e

    async def get_report(self, report_id: str) -> Optional[VARReport]:
        """Retrieves VARReport by report_id."""
        json_path = os.path.join(
            self._reports_dir, f"VAR_REPORT_{report_id}.json"
        )
        if not os.path.exists(json_path):
            return None
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                content = f.read()
            return VARReport.model_validate_json(content)
        except Exception as e:
            raise RepositoryIOError(
                f"Failed to read report '{report_id}': {e}"
            ) from e
