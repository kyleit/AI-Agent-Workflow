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
from workflow_runtime.application.workflow.blueprint_authoring_policy_validator import (
    BlueprintAuthoringPolicyValidator,
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
    section_aliases = {
        "Document Control And Upstream Traceability": "document control and upstream traceability",
        "Executive Architecture And 4-Layer DDD Topology": "executive architecture and 4-layer ddd topology",
        "Data Flow And Sequence Diagram": "data flow and sequence diagram",
        "File-By-File Change Matrix": "file by file change matrix",
        "QA Verification Matrix": "qa verification matrix",
        "Internal Review Evidence": "internal review evidence",
    }

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
        findings.extend(self._approval_claim_findings(relative_blueprint, text, work_item_id))
        authoring_policy = BlueprintAuthoringPolicyValidator().validate(
            self.workspace_root,
            self.workspace_root / relative_blueprint,
        )
        findings.extend(authoring_policy.blocking_findings)
        effective_scope_metrics = self._scope_metrics(scope_metrics or {}, text)
        artifact_set = BlueprintArtifactSetValidator().validate(
            self.workspace_root / relative_blueprint,
            self._discover_phase_paths(relative_blueprint),
            effective_scope_metrics,
        )
        findings.extend(artifact_set.blocking_findings)
        if not post_implementation:
            findings.extend(
                self._preimplementation_runtime_pass_findings(
                    text,
                    "master",
                )
            )
            for phase_path in self._discover_phase_paths(relative_blueprint):
                findings.extend(
                    self._preimplementation_runtime_pass_findings(
                        phase_path.read_text(encoding="utf-8"),
                        phase_path.stem,
                    )
                )
        if self._looks_like_project_initialization(text):
            findings.extend(self._greenfield_contract_findings(text, "master"))
            for phase_path in self._discover_phase_paths(relative_blueprint):
                findings.extend(
                    self._greenfield_contract_findings(
                        phase_path.read_text(encoding="utf-8"),
                        phase_path.stem,
                        phase=True,
                    )
                )
            findings.extend(self._surface_completeness_findings(text))
        findings.extend(
            self._upstream_delivery_coverage_findings(
                text,
                relative_blueprint,
                self._discover_phase_paths(relative_blueprint),
            )
        )
        findings.extend(self._requirement_surface_findings(text))
        findings.extend(self._scope_findings(text, effective_scope_metrics, coverage_rows))
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

    def _approval_claim_findings(
        self,
        relative_blueprint: Path,
        blueprint_text: str,
        work_item_id: str,
    ) -> list[str]:
        """Reject agent-authored approval metadata on every verification route."""
        status = re.search(r"^status:\s*([^\s#]+)", blueprint_text, re.IGNORECASE | re.MULTILINE)
        if status is None or status.group(1).upper() not in {"APPROVED", "FROZEN"}:
            return []
        candidates = [
            self.workspace_root / ".agents" / "state" / "work-items" / work_item_id / "approvals.json",
            self.workspace_root / ".agents" / "state" / "approvals.json",
        ]
        for candidate in candidates:
            try:
                payload = json.loads(candidate.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError, TypeError):
                continue
            approval = payload.get("blueprint") if isinstance(payload, dict) else None
            if not isinstance(approval, dict) or not approval.get("approved"):
                continue
            approved_path = str(approval.get("path", "")).replace("\\", "/").lstrip("./")
            approved_work_item = str(
                approval.get("work_item_id") or approval.get("work_item") or work_item_id
            )
            if approved_path == relative_blueprint.as_posix() and approved_work_item == work_item_id:
                return []
        return ["unbound_blueprint_approval_claim"]

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
        decomposer = BlueprintScopeDecomposer()
        inferred = decomposer.infer_from_blueprint(blueprint_text)
        if scope_metrics:
            # Structured handoff metrics are useful hints, but the written
            # Blueprint is authoritative. Stale or under-counted metadata must
            # never make a large artifact look small enough for one phase.
            for key in ("capability_count", "file_family_count", "task_count"):
                if key in scope_metrics:
                    inferred[key] = max(
                        int(inferred.get(key, 0)),
                        int(scope_metrics.get(key, 0)),
                    )
            inferred["cross_layer"] = bool(
                inferred.get("cross_layer", False)
                or scope_metrics.get("cross_layer", False)
            )
            if scope_metrics.get("boundary_kinds"):
                inferred["boundary_kinds"] = scope_metrics["boundary_kinds"]
        assessment = decomposer.assess(
            int(inferred.get("capability_count", 0)),
            int(inferred.get("file_family_count", 0)),
            int(inferred.get("task_count", 0)),
            bool(inferred.get("cross_layer", False)),
            inferred.get("boundary_kinds"),
        )
        declared = re.search(r"declared_phase_count:\s*(\d+)", blueprint_text)
        declared_count = int(declared.group(1)) if declared else 1
        # An explicit declaration may request additional delivery slices, but
        # it can never reduce the count derived from the artifact itself.
        inferred["recommended_phase_count"] = max(assessment.recommended_phase_count, declared_count)
        inferred["requires_phase_split"] = assessment.requires_phase_split or inferred["recommended_phase_count"] > 1
        inferred["scope_reasons"] = assessment.reasons
        return inferred

    def _discover_phase_paths(self, master_path: Path) -> list[Path]:
        resolved_master = master_path
        if not resolved_master.is_absolute():
            resolved_master = self.workspace_root / resolved_master
        prefix = resolved_master.name.split("_", 1)[0]
        phase_paths: list[Path] = []
        for candidate in resolved_master.parent.rglob("*.md"):
            if candidate.resolve() == resolved_master.resolve():
                continue
            try:
                candidate_text = candidate.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            if re.search(r"^artifact_type:\s*phase_blueprint\s*$", candidate_text, re.IGNORECASE | re.MULTILINE) and re.search(
                r"^phase_id:\s*P\d+\s*$", candidate_text, re.IGNORECASE | re.MULTILINE
            ):
                phase_paths.append(candidate)
                continue
            if re.search(rf"(?:^|[-_]){re.escape(prefix)}-P\d+(?:[-_])", candidate.stem, re.IGNORECASE):
                phase_paths.append(candidate)
        return sorted(set(phase_paths))

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
        if assessment.requires_phase_split or int(scope_metrics.get("recommended_phase_count", 1)) > 1:
            headings = self._heading_text(blueprint_text)
            has_feature_coverage_heading = any(
                self._normalize("Feature Coverage Matrix") in heading
                for heading in headings
            )
            # Phase Blueprints are separate physical artifacts. Their presence
            # and contracts are validated recursively by the artifact-set
            # validator; the Master only needs to index and cover them.
            for marker in ("Master Blueprint", "Feature Coverage Matrix"):
                if not any(self._normalize(marker) in heading for heading in headings):
                    findings.append(f"large_feature_missing:{marker}")
            if has_feature_coverage_heading:
                if not self._section_has_table(
                    blueprint_text,
                    "feature coverage matrix",
                    (
                        "capability id", "acceptance criteria", "phase", "files",
                        "code blocks", "test ids", "evidence paths",
                    ),
                ):
                    findings.append("feature_coverage_matrix_incomplete")
                else:
                    coverage_body = self._section_body(blueprint_text, "feature coverage matrix")
                    coverage_text = "\n".join(coverage_body or [])
                    requirement_ids = sorted(
                        {
                            match.group(0).upper()
                            for match in re.finditer(
                                r"\b(?:FR|NFR|AC|G|US)-\d+\b",
                                blueprint_text,
                                re.IGNORECASE,
                            )
                        }
                    )
                    for requirement_id in requirement_ids:
                        if not re.search(rf"\b{re.escape(requirement_id)}\b", coverage_text, re.IGNORECASE):
                            findings.append(f"feature_coverage_missing:{requirement_id}")
        if coverage_rows is not None:
            findings.extend(FeatureCoverageValidator().validate(coverage_rows).blocking_findings)
        elif assessment.requires_phase_split or int(scope_metrics.get("recommended_phase_count", 1)) > 1:
            if not any(
                self._normalize("Feature Coverage Matrix") in heading
                for heading in self._heading_text(blueprint_text)
            ):
                findings.append("feature_coverage_matrix_missing")
        return findings

    def _requirement_surface_findings(self, master_text: str) -> list[str]:
        """Keep generated scope bound to the original requirement artifact."""
        linked = self._linked_artifact_paths(master_text)
        requirement_text = self._read_linked_artifact(
            linked.get("specification") or linked.get("requirements")
        )
        if not requirement_text:
            return []
        lower_requirement = requirement_text.lower()
        findings: list[str] = []
        screen_body = "\n".join(
            self._section_body(master_text, "screen and route coverage matrix") or []
        )
        if screen_body:
            routes = list(dict.fromkeys(re.findall(r"#/[^\s`,)]+", requirement_text)))
            for route in routes:
                if route not in screen_body:
                    findings.append(f"requirement_route_unmapped:{route}")
                    continue
                matching = [line for line in screen_body.splitlines() if route in line]
                row_text = "\n".join(matching).lower()
                if route not in {"#/dialog", "#/navigation"} and not re.search(
                    r"(?:views?|routes?|pages?|screens?)[\\/][^|` ]+\.(?:svelte|tsx|jsx|vue|html)",
                    row_text,
                    re.IGNORECASE,
                ):
                    findings.append(f"requirement_route_missing_screen_file:{route}")

        backend_body = "\n".join(
            self._section_body(master_text, "backend capability coverage matrix") or []
        ).lower()
        if backend_body:
            table_names = list(dict.fromkeys(re.findall(
                r"(?:table|create table(?: if not exists)?)\s+[`'\[]?([a-z][a-z0-9_]*)",
                lower_requirement,
                re.IGNORECASE,
            )))
            for table_name in table_names:
                if table_name not in backend_body:
                    findings.append(f"requirement_table_unmapped:{table_name}")
            if any(token in lower_requirement for token in ("worker", "scheduler", "probe")):
                if not any(token in backend_body for token in ("worker", "scheduler", "probe")):
                    findings.append("requirement_capability_unmapped:execution")
            if any(token in lower_requirement for token in ("incident", "history", "metric")):
                if not any(token in backend_body for token in ("incident", "history", "metric")):
                    findings.append("requirement_capability_unmapped:observability")
        return findings

    def _surface_completeness_findings(self, blueprint_text: str) -> list[str]:
        """Reject greenfield blueprints that satisfy block syntax but omit whole product surfaces.

        This deliberately validates contracts, not a particular product. The
        generator must derive the rows from the upstream requirements and then
        prove that each UI/backend surface has concrete files, blocks, and
        runtime tests. A file count or a few representative snippets cannot
        satisfy this check.
        """
        lower = blueprint_text.lower()
        headings = self._heading_text(blueprint_text)
        findings: list[str] = []

        ui_signal_count = sum(
            token in lower
            for token in ("frontend", "svelte", "spa", "route", "screen", "view", "web ui")
        )
        backend_signal_count = sum(
            token in lower
            for token in ("backend", "go", "api", "service", "repository", "database", "worker")
        )
        if ui_signal_count >= 3:
            section = "screen and route coverage matrix"
            if not any(self._normalize(section) in heading for heading in headings):
                findings.append("surface_completeness_missing:screen_and_route_coverage_matrix")
            elif not self._section_has_table(
                blueprint_text,
                section,
                (
                    "route", "screen", "concrete files", "code blocks",
                    "api", "state", "test", "evidence",
                ),
            ):
                findings.append("surface_completeness_incomplete:screen_and_route_coverage_matrix")
            else:
                body = "\n".join(self._section_body(blueprint_text, section) or [])
                rows = [line for line in body.splitlines() if line.strip().startswith("|")]
                data_rows = [line for line in rows if not re.search(r"^\s*\|\s*:?-+", line)]
                if len(data_rows) < 4:
                    findings.append("surface_completeness_too_few:screen_and_route_rows")
                if len(set(re.findall(r"[`']([^`']+\.(?:svelte|tsx|jsx|vue|html|css|js|ts))[`']", body, re.IGNORECASE))) < 4:
                    findings.append("surface_completeness_too_few:screen_concrete_files")

        if backend_signal_count >= 4:
            section = "backend capability coverage matrix"
            if not any(self._normalize(section) in heading for heading in headings):
                findings.append("surface_completeness_missing:backend_capability_coverage_matrix")
            elif not self._section_has_table(
                blueprint_text,
                section,
                (
                    "capability", "concrete files", "code blocks", "api",
                    "data", "test", "evidence",
                ),
            ):
                findings.append("surface_completeness_incomplete:backend_capability_coverage_matrix")
            else:
                body = "\n".join(self._section_body(blueprint_text, section) or [])
                rows = [line for line in body.splitlines() if line.strip().startswith("|")]
                data_rows = [line for line in rows if not re.search(r"^\s*\|\s*:?-+", line)]
                if len(data_rows) < 4:
                    findings.append("surface_completeness_too_few:backend_capability_rows")
                required_surfaces = {
                    "persistence": ("repository", "database", "sqlite", "migration", "storage"),
                    "application": ("application", "use case", "service", "orchestration"),
                    "delivery": ("api", "http", "rest", "fiber", "handler", "route"),
                    "verification": ("test", "fixture", "integration", "e2e"),
                }
                for surface, aliases in required_surfaces.items():
                    if not any(alias in body.lower() for alias in aliases):
                        findings.append(f"surface_completeness_missing:backend_{surface}")
                if any(token in lower for token in ("probe", "scheduler", "worker", "incident", "metric")):
                    for surface, aliases in {
                        "execution": ("probe", "worker", "scheduler", "queue"),
                        "observability": ("metric", "history", "incident", "event", "realtime"),
                    }.items():
                        if not any(alias in body.lower() for alias in aliases):
                            findings.append(f"surface_completeness_missing:backend_{surface}")

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
        headings = self._heading_text(text)
        for marker, normalized_marker in self.section_aliases.items():
            required_heading = self._normalize(normalized_marker)
            if not any(required_heading in heading for heading in headings):
                findings.append(f"missing_required_marker:{marker}")
        if "CODE_BLOCK_GATE" not in text:
            findings.append("missing_required_marker:CODE_BLOCK_GATE")
        if any("data flow sequence diagram" in heading for heading in headings):
            diagram_text = text.lower()
            has_mermaid = "```mermaid" in diagram_text
            has_sequence_shape = "sequencediagram" in diagram_text or "flowchart" in diagram_text
            if not (has_mermaid and has_sequence_shape):
                findings.append("data_flow_sequence_diagram_missing")
        if self._looks_like_project_initialization(text) and not any(
            "project initialization coverage matrix" in heading for heading in headings
        ):
            findings.append("project_initialization_coverage_matrix_missing")
        elif self._looks_like_project_initialization(text) and not self._section_has_table(
            text,
            "project initialization coverage matrix",
            ("obligation id", "scaffold files", "code blocks", "tests", "commands", "evidence"),
        ):
            findings.append("project_initialization_coverage_matrix_incomplete")
        elif self._looks_like_project_initialization(text):
            init_body = self._section_body(text, "project initialization coverage matrix")
            init_text = "\n".join(init_body or []).lower()
            obligations = {
                "backend": ("backend", "go fiber", "fiber"),
                "frontend": ("frontend", "svelte", "spa", "tailwind"),
                "database": ("database", "sqlite", "persistence", "migration"),
                "desktop_shell": ("desktop", "wails", "systray", "tray"),
                "assets": ("assets", "font", "lucide", "local"),
                "controls_and_dialogs": ("controls", "input", "textarea", "select", "dialog", "alert", "prompt", "confirm"),
                "loading": ("loading", "skeleton", "spinner"),
                "tooling": ("tooling", "go.mod", "wails.json", "package.json", "npm", "go test"),
            }
            for obligation_id, aliases in obligations.items():
                if not any(alias in init_text for alias in aliases):
                    findings.append(f"project_initialization_obligation_missing:{obligation_id}")
        prose_lines: list[str] = []
        in_fence = False
        for line in text.splitlines():
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if not in_fence:
                prose_lines.append(line)
        prose_text = "\n".join(prose_lines)
        # Require a path boundary so URL schemes such as ``https://`` are not
        # mistaken for Windows drive-letter paths.
        drive_path_pattern = r"(?<![A-Za-z0-9])[A-Za-z]" + ":" + r"[\\/]"
        if re.search(r"file:///|" + drive_path_pattern + r"|/(Users|Volumes|home)/", prose_text):
            findings.append("relative_path_scan_failed")
        return findings

    def _greenfield_contract_findings(
        self,
        text: str,
        artifact_label: str,
        phase: bool = False,
    ) -> list[str]:
        """Require a buildable repository contract for empty-project work."""
        headings = self._heading_text(text)
        required = (
            (
                "empty repository baseline",
                "target repository tree",
                "bootstrap command sequence",
                "initial dependency manifest",
                "hierarchical delivery decomposition",
            )
            if not phase
            else (
                "phase entry and exit contract",
                "owned directory tree",
                "full file delivery contract",
            )
        )
        findings = []
        for marker in required:
            if not any(self._normalize(marker) in heading for heading in headings):
                findings.append(f"{artifact_label}_missing_greenfield_contract:{marker}")
        if phase:
            frontmatter = text.split("---", 2)[1] if text.startswith("---") else ""
            if not re.search(r"^family_id:\s*\S+", frontmatter, re.IGNORECASE | re.MULTILINE):
                findings.append(f"{artifact_label}_missing_family_id")
            if not re.search(r"^small_feature_id:\s*\S+", frontmatter, re.IGNORECASE | re.MULTILINE):
                findings.append(f"{artifact_label}_missing_small_feature_id")
        return findings

    def _upstream_delivery_coverage_findings(
        self,
        master_text: str,
        master_path: Path,
        phase_paths: list[Path],
    ) -> list[str]:
        """Ensure a Blueprint materializes the upstream plan, not just its theme."""
        linked = self._linked_artifact_paths(master_text)
        roadmap_text = self._read_linked_artifact(linked.get("roadmap"))
        plan_text = self._read_linked_artifact(linked.get("plan"))
        if not roadmap_text and not plan_text:
            return []

        findings: list[str] = []
        all_phase_text = "\n".join(
            [master_text]
            + [path.read_text(encoding="utf-8") for path in phase_paths if path.is_file()]
        )
        matrix_body = self._section_body(master_text, "upstream delivery unit coverage")
        phase_ids = self._upstream_phase_ids(roadmap_text)
        if phase_ids:
            if matrix_body is None:
                findings.append("upstream_delivery_unit_coverage_matrix_missing")
            else:
                discovered = {path.resolve() for path in phase_paths}
                mapped_paths: set[Path] = set()
                for phase_id in phase_ids:
                    matching_rows = [
                        line for line in matrix_body
                        if phase_id.lower() in line.lower()
                    ]
                    if not matching_rows:
                        findings.append(f"upstream_phase_unmapped:{phase_id}")
                        continue
                    artifact_refs = re.findall(
                        r"`([^`]+\.md)`",
                        "\n".join(matching_rows),
                        re.IGNORECASE,
                    )
                    if not artifact_refs:
                        findings.append(f"upstream_phase_artifact_missing:{phase_id}")
                        continue
                    for ref in artifact_refs:
                        candidate = (self.workspace_root / ref).resolve()
                        if candidate not in discovered:
                            findings.append(
                                f"upstream_phase_artifact_not_discovered:{phase_id}:{ref}"
                            )
                        else:
                            mapped_paths.add(candidate)
                if len(mapped_paths) < len(phase_ids):
                    findings.append(
                        "upstream_phase_artifact_count_mismatch:"
                        f"required={len(phase_ids)}:mapped={len(mapped_paths)}"
                    )

        planned_files = self._planned_implementation_files(plan_text)
        if planned_files:
            normalized_scope = all_phase_text.replace("\\", "/").lower()
            for path in planned_files:
                if path.lower().replace("\\", "/") not in normalized_scope:
                    findings.append(f"upstream_plan_file_unmaterialized:{path}")
        return findings

    @staticmethod
    def _linked_artifact_paths(text: str) -> dict[str, Path]:
        return {
            key.lower(): Path(value)
            for key, value in re.findall(
                r"^\s{2,}(specification|roadmap|plan|brainstorming):\s*([^\s]+)\s*$",
                text,
                re.IGNORECASE | re.MULTILINE,
            )
        }

    def _read_linked_artifact(self, path: Path | None) -> str:
        if path is None:
            return ""
        candidate = path if path.is_absolute() else self.workspace_root / path
        try:
            return candidate.resolve().read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return ""

    @staticmethod
    def _upstream_phase_ids(roadmap_text: str) -> list[str]:
        ids = re.findall(
            r"`(P\d+(?:-[A-Z0-9]+)+)`",
            roadmap_text,
            re.IGNORECASE,
        )
        return list(dict.fromkeys(item.upper() for item in ids))

    @staticmethod
    def _planned_implementation_files(plan_text: str) -> list[str]:
        if not plan_text:
            return []
        candidates = re.findall(r"`([^`]+)`", plan_text)
        source_extensions = {
            ".go", ".sum", ".mod", ".sql", ".svelte", ".ts", ".js", ".css",
            ".json", ".html", ".woff", ".woff2", ".ttf", ".svg", ".png",
        }
        ignored_prefixes = ("docs/", "http:", "https:", "file:")
        planned: list[str] = []
        for candidate in candidates:
            normalized = candidate.replace("\\", "/").strip()
            if not normalized or normalized.lower().startswith(ignored_prefixes):
                continue
            if Path(normalized).suffix.lower() not in source_extensions:
                continue
            if normalized not in planned:
                planned.append(normalized)
        return planned

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    def _heading_text(self, text: str) -> list[str]:
        return [
            self._normalize(line.lstrip("#").strip())
            for line in text.splitlines()
            if line.lstrip().startswith("#")
        ]

    def _section_has_table(
        self,
        text: str,
        heading_fragment: str,
        required_columns: tuple[str, ...],
    ) -> bool:
        body = self._section_body(text, heading_fragment)
        if body is None:
            return False
        normalized_body = self._normalize("\n".join(body))
        if any(self._normalize(column) not in normalized_body for column in required_columns):
            return False
        data_rows = self._table_rows(body)
        return len(data_rows) >= 2

    def _section_body(self, text: str, heading_fragment: str) -> list[str] | None:
        lines = text.splitlines()
        target = self._normalize(heading_fragment)
        start = next(
            (
                index
                for index, line in enumerate(lines)
                if line.lstrip().startswith("#") and target in self._normalize(line)
            ),
            None,
        )
        if start is None:
            return None
        body: list[str] = []
        for line in lines[start + 1:]:
            if line.lstrip().startswith("#"):
                break
            body.append(line)
        return body

    @staticmethod
    def _table_rows(body: list[str]) -> list[str]:
        return [
            line for line in body
            if line.strip().startswith("|")
            and "{{" not in line
            and not re.fullmatch(r"\s*\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)+\|?\s*", line)
        ]

    @staticmethod
    def _preimplementation_runtime_pass_findings(text: str, artifact_label: str) -> list[str]:
        """Reject unsubstantiated runtime PASS claims before implementation.

        Blueprint readiness may prove that a test *will* be run, but it cannot
        claim that a product runtime, browser, desktop shell, or visual E2E
        already passed when the product has not been implemented. Static code
        block and architecture review PASS rows remain valid.
        """
        findings: list[str] = []
        runtime_markers = (
            "e2e", "runtime", "browser", "desktop", "visual", "systray",
            "fiber rest", "wails", "font offline", "custom control",
            "schema migration", "probe engine", "api readiness",
        )
        in_fence = False
        headings = [line.strip().lower() for line in text.splitlines() if line.lstrip().startswith("#")]
        scoped_validation = any(
            any(marker in heading for marker in ("qa verification matrix", "runtime evidence", "e2e evidence"))
            for heading in headings
        )
        current_heading = ""
        for line in text.splitlines():
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if line.lstrip().startswith("#"):
                current_heading = line.strip().lower()
                continue
            if in_fence or not line.strip().startswith("|"):
                continue
            if scoped_validation and not any(
                marker in current_heading
                for marker in ("qa verification matrix", "runtime evidence", "e2e evidence")
            ):
                continue
            lower = line.lower()
            if "pass" not in lower or not any(marker in lower for marker in runtime_markers):
                continue
            findings.append(f"preimplementation_runtime_pass_claim:{artifact_label}")
        return findings

    @staticmethod
    def _looks_like_project_initialization(text: str) -> bool:
        lower = text.lower()
        if re.search(r"project_initialization\s*:\s*true", lower):
            return True
        scaffold_markers = sum(
            marker in lower
            for marker in ("go.mod", "wails.json", "frontend/package.json", "project scaffold")
        )
        return scaffold_markers >= 2 and any(
            marker in lower
            for marker in ("new", "greenfield", "from scratch", "empty repository", "khởi tạo dự án")
        )

    def _run_code_block_gate(self, relative_blueprint: Path, work_item_id: str, output: Path) -> dict[str, object]:
        candidates = (
            self.workspace_root / "skills" / "strict-code-block-gate" / "scripts" / "run_strict_code_block_gate.py",
            self.workspace_root / ".agents" / "skills" / "strict-code-block-gate" / "scripts" / "run_strict_code_block_gate.py",
        )
        runner = next((candidate for candidate in candidates if candidate.is_file()), None)
        if runner is None:
            return {
                "decision": "BLOCKED",
                "blueprint_full_sha256": "",
                "per_code_block": [],
                "blocking_findings": ["strict_code_block_gate_runner_missing"],
            }
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
        for phase_path in self._discover_phase_paths(relative_blueprint):
            command.extend(["--phase-blueprint", phase_path.as_posix()])
        subprocess.run(command, cwd=self.workspace_root, check=False, capture_output=True, text=True, timeout=30)
        return json.loads((self.workspace_root / output).read_text(encoding="utf-8"))


__all__ = ["BlueprintAutoValidationService", "BlueprintValidationResult"]
