from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from workflow_runtime.application.workflow.blueprint_artifact_set_validator import (
    BlueprintArtifactSetValidator,
)
from workflow_runtime.application.workflow.blueprint_scope_decomposer import (
    BlueprintScopeDecomposer,
)
from workflow_runtime.application.workflow.feature_coverage_validator import (
    FeatureCoverageValidator,
)
from workflow_runtime.application.workflow.project_init_completeness_validator import (
    ProjectInitCompletenessValidator,
)
from workflow_runtime.application.workflow.source_context_validator import (
    SourceContextValidator,
)


@dataclass(frozen=True)
class BlueprintValidationResult:
    status: str
    score: int
    evidence: list[str] = field(default_factory=list[str])
    blocking_findings: list[str] = field(default_factory=list[str])
    next_action: str = "repair_blueprint"
    result_id: str = ""
    blueprint_sha256: str = ""
    source_snapshot: str = ""


class BlueprintAutoValidationService:
    required_markers = (
        "Document Control And Upstream Traceability",
        "Executive Architecture And 4-Layer DDD Topology",
        "Data Flow And Sequence Diagram",
        "File-By-File Change Matrix",
        "QA Verification Matrix",
        "Internal Review Evidence",
        "CODE_BLOCK_GATE",
    )

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()

    def validate_for_approval(
        self,
        blueprint_path: Path,
        work_item_id: str,
        scope_metrics: dict[str, object] | None = None,
        coverage_rows: list[dict[str, object]] | None = None,
        init_obligations: list[str] | None = None,
        init_coverage_rows: list[dict[str, object]] | None = None,
        allow_existing_creates: bool = False,
        post_implementation: bool = False,
    ) -> BlueprintValidationResult:
        relative_blueprint = self._relative_blueprint(blueprint_path)
        findings = self._document_findings(relative_blueprint)
        text = (self.workspace_root / relative_blueprint).read_text(encoding="utf-8")
        artifact_set = BlueprintArtifactSetValidator().validate(
            self.workspace_root / relative_blueprint,
            self._discover_phase_paths(relative_blueprint),
            self._scope_metrics(scope_metrics or {}, text),
        )
        findings.extend(artifact_set.blocking_findings)
        findings.extend(self._scope_findings(text, scope_metrics or {}, coverage_rows))
        if init_obligations is not None:
            init_coverage = ProjectInitCompletenessValidator().validate(
                init_obligations,
                init_coverage_rows or [],
            )
            findings.extend(init_coverage.blocking_findings)
        gate_output = Path("docs") / "aiwf-runs" / work_item_id / "05-blueprint" / "code-block-gate.json"
        gate_result = self._run_code_block_gate(relative_blueprint, work_item_id, gate_output)
        blueprint_sha256 = str(gate_result.get("blueprint_full_sha256", ""))
        source_snapshot = self._source_snapshot()
        result_id = f"{work_item_id}:{blueprint_sha256}"
        decision = str(gate_result.get("decision", "BLOCKED"))
        if decision != "PASS":
            findings.append(f"CODE_BLOCK_GATE:{decision}")
        for block in gate_result.get("per_code_block", []):
            if isinstance(block, dict) and block.get("status") in {"FAIL", "BLOCKED"}:
                findings.append(f"code_block_failed:{block.get('id', 'unknown')}")
        findings.extend(str(item) for item in gate_result.get("blocking_findings", []))
        code_blocks = [block for block in gate_result.get("per_code_block", []) if isinstance(block, dict)]
        source_context = SourceContextValidator(self.workspace_root).validate_blocks(
            code_blocks,
            allow_existing_creates=allow_existing_creates,
        )
        findings.extend(source_context.blocking_findings)
        if findings:
            return BlueprintValidationResult(
                status="BLOCKED",
                score=max(0, 100 - (10 * len(findings))),
                evidence=[gate_output.as_posix()],
                blocking_findings=findings,
                result_id=result_id,
                blueprint_sha256=blueprint_sha256,
                source_snapshot=source_snapshot,
            )
        return BlueprintValidationResult(
            status="VERIFIED" if post_implementation else "APPROVAL_READY",
            score=100,
            evidence=[gate_output.as_posix()],
            next_action="debug-to-verify" if post_implementation else "request_owner_blueprint_approval",
            result_id=result_id,
            blueprint_sha256=blueprint_sha256,
            source_snapshot=source_snapshot,
        )

    def _source_snapshot(self) -> str:
        try:
            return subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.workspace_root,
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return "working-tree"

    def _scope_metrics(self, scope_metrics: dict[str, object], blueprint_text: str) -> dict[str, object]:
        if scope_metrics:
            assessment = BlueprintScopeDecomposer().assess(
                int(scope_metrics.get("capability_count", 0)),
                int(scope_metrics.get("file_family_count", 0)),
                int(scope_metrics.get("task_count", 0)),
                bool(scope_metrics.get("cross_layer", False)),
                scope_metrics.get("boundary_kinds"),
            )
            return {"recommended_phase_count": assessment.recommended_phase_count}
        declared = re.search(r"declared_phase_count:\s*(\d+)", blueprint_text)
        return {"recommended_phase_count": int(declared.group(1)) if declared else 1}

    def _discover_phase_paths(self, master_path: Path) -> list[Path]:
        resolved_master = master_path
        if not resolved_master.is_absolute():
            resolved_master = self.workspace_root / resolved_master
        prefix = resolved_master.name.split("_", 1)[0]
        return sorted(resolved_master.parent.glob(f"{prefix}-P??_*.md"))

    def _scope_findings(
        self,
        blueprint_text: str,
        scope_metrics: dict[str, object],
        coverage_rows: list[dict[str, object]] | None,
    ) -> list[str]:
        findings: list[str] = []
        assessment = BlueprintScopeDecomposer().assess(
            int(scope_metrics.get("capability_count", 0)),
            int(scope_metrics.get("file_family_count", 0)),
            int(scope_metrics.get("task_count", 0)),
            bool(scope_metrics.get("cross_layer", False)),
        )
        if assessment.requires_phase_split:
            for marker in ("Master Blueprint", "Phase Blueprint", "Feature Coverage Matrix"):
                if marker not in blueprint_text:
                    findings.append(f"large_feature_missing:{marker}")
        if coverage_rows is not None:
            findings.extend(FeatureCoverageValidator().validate(coverage_rows).blocking_findings)
        elif assessment.requires_phase_split:
            findings.append("feature_coverage_matrix_missing")
        return findings

    def _relative_blueprint(self, blueprint_path: Path) -> Path:
        candidate = blueprint_path if blueprint_path.is_absolute() else self.workspace_root / blueprint_path
        resolved = candidate.resolve()
        relative = resolved.relative_to(self.workspace_root)
        if not relative.parts or relative.parts[0] != "docs":
            raise ValueError("blueprint_must_be_under_docs")
        return relative

    def _document_findings(self, relative_blueprint: Path) -> list[str]:
        text = (self.workspace_root / relative_blueprint).read_text(encoding="utf-8")
        findings: list[str] = []
        for marker in self.required_markers:
            if marker not in text:
                findings.append(f"missing_required_marker:{marker}")
        prose_lines: list[str] = []
        in_fence = False
        for line in text.splitlines():
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if not in_fence:
                prose_lines.append(line)
        prose_text = "\n".join(prose_lines)
        drive_path_pattern = r"[A-Za-z]" + ":" + r"[\\/]"
        if re.search(r"file:///|" + drive_path_pattern + r"|/(Users|Volumes|home)/", prose_text):
            findings.append("relative_path_scan_failed")
        return findings

    def _run_code_block_gate(self, relative_blueprint: Path, work_item_id: str, output: Path) -> dict[str, object]:
        runner = self.workspace_root / "skills" / "strict-code-block-gate" / "scripts" / "run_strict_code_block_gate.py"
        command = [
            sys.executable,
            str(runner),
            "--blueprint",
            relative_blueprint.as_posix(),
            "--workflow-id",
            work_item_id,
            "--output",
            output.as_posix(),
            "--no-execute",
        ]
        subprocess.run(command, cwd=self.workspace_root, check=False, capture_output=True, text=True, timeout=30)
        return json.loads((self.workspace_root / output).read_text(encoding="utf-8"))


__all__ = ["BlueprintAutoValidationService", "BlueprintValidationResult"]
