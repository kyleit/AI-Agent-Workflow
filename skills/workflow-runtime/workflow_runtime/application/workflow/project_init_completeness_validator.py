from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProjectInitCompletenessResult:
    passed: bool
    blocking_findings: list[str] = field(default_factory=list[str])


class ProjectInitCompletenessValidator:
    required_row_fields = (
        "obligation_id",
        "scaffold_files",
        "code_block_ids",
        "test_ids",
        "evidence_paths",
    )

    def validate(
        self,
        required_obligations: list[str],
        coverage_rows: list[dict[str, object]],
    ) -> ProjectInitCompletenessResult:
        findings: list[str] = []
        rows_by_obligation = {
            str(row.get("obligation_id", "")).strip(): row
            for row in coverage_rows
            if str(row.get("obligation_id", "")).strip()
        }
        for obligation in required_obligations:
            key = obligation.strip()
            row = rows_by_obligation.get(key)
            if row is None:
                findings.append(f"project_init_obligation_missing:{key}")
                continue
            for field_name in self.required_row_fields:
                if row.get(field_name) in (None, "", [], ()):
                    findings.append(f"project_init_obligation_incomplete:{key}:{field_name}")
        return ProjectInitCompletenessResult(not findings, findings)


__all__ = ["ProjectInitCompletenessResult", "ProjectInitCompletenessValidator"]
