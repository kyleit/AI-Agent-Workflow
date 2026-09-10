from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CoverageValidationResult:
    passed: bool
    blocking_findings: list[str] = field(default_factory=list[str])


class FeatureCoverageValidator:
    required_fields = (
        "capability_id",
        "user_intent",
        "acceptance_criteria",
        "phase_id",
        "code_block_ids",
        "test_ids",
        "evidence_paths",
    )

    def validate(self, rows: list[dict[str, object]]) -> CoverageValidationResult:
        findings: list[str] = []
        if not rows:
            return CoverageValidationResult(False, ["feature_coverage_matrix_missing"])
        seen_capabilities: set[str] = set()
        for index, row in enumerate(rows, start=1):
            capability = str(row.get("capability_id", "")).strip()
            if capability:
                seen_capabilities.add(capability)
            for field_name in self.required_fields:
                if row.get(field_name) in (None, "", [], ()):
                    findings.append(f"coverage_row_{index}_missing:{field_name}")
        if len(seen_capabilities) != len(rows):
            findings.append("feature_coverage_duplicate_or_blank_capability")
        return CoverageValidationResult(not findings, findings)


__all__ = ["CoverageValidationResult", "FeatureCoverageValidator"]
