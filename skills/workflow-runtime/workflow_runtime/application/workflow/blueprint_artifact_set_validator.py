from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ArtifactSetValidationResult:
    passed: bool
    blocking_findings: list[str] = field(default_factory=list[str])


class BlueprintArtifactSetValidator:
    required_phase_markers = (
        "Phase Scope",
        "File-By-File Change Matrix",
        "Implementation-Ready Code-Block Inventory",
        "QA Verification Matrix",
        "NO-GO Conditions",
    )

    def validate(
        self,
        master_path: Path,
        phase_paths: list[Path],
        scope_metrics: dict[str, object],
    ) -> ArtifactSetValidationResult:
        findings: list[str] = []
        if not master_path.is_file():
            findings.append("master_blueprint_missing")
        expected_count = max(1, int(scope_metrics.get("recommended_phase_count", 0)))
        if len(phase_paths) != expected_count:
            findings.append(f"phase_blueprint_count_mismatch:expected={expected_count}:actual={len(phase_paths)}")
        paths_by_phase: dict[str, Path] = {}
        for path in phase_paths:
            match = re.search(r"(P\d+)", path.stem)
            if match:
                paths_by_phase[match.group(1)] = path
        for index in range(1, expected_count + 1):
            phase_id = f"P{index:02d}"
            path = paths_by_phase.get(phase_id)
            if path is None or not path.is_file():
                findings.append(f"phase_blueprint_missing:{phase_id}")
                continue
            text = path.read_text(encoding="utf-8")
            if f"phase_id: {phase_id}" not in text:
                findings.append(f"phase_blueprint_wrong_id:{phase_id}")
            for marker in self.required_phase_markers:
                if marker not in text:
                    findings.append(f"phase_blueprint_incomplete:{phase_id}:{marker}")
        return ArtifactSetValidationResult(not findings, findings)


__all__ = ["ArtifactSetValidationResult", "BlueprintArtifactSetValidator"]
