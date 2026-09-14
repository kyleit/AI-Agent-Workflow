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
        for path in [master_path, *phase_paths]:
            if not path.is_file():
                continue
            # Blueprint document length is intentionally not a gate. Splitting
            # remains an Agent decision based on executable ownership and
            # context, while completeness is enforced by matrix/block checks.
        expected_count = max(1, int(scope_metrics.get("recommended_phase_count", 0)))
        master_text = master_path.read_text(encoding="utf-8") if master_path.is_file() else ""
        project_initialization = bool(scope_metrics.get("project_initialization")) or bool(
            re.search(r"^project_initialization:\s*true\s*$", master_text, re.IGNORECASE | re.MULTILINE)
        )
        cross_layer = bool(scope_metrics.get("cross_layer")) or self._has_cross_layer_families(master_text)
        phase_split_required = expected_count > 1 or (project_initialization and cross_layer)
        family_paths: dict[tuple[str, str], list[Path]] = {}
        for path in phase_paths:
            relative_parts = path.relative_to(master_path.parent).parts
            family = relative_parts[0] if relative_parts else ""
            subfeature = relative_parts[1] if len(relative_parts) > 2 else ""
            family_paths.setdefault((family, subfeature), []).append(path)
        if phase_split_required and len(phase_paths) < expected_count:
            findings.append(f"phase_blueprint_count_mismatch:minimum={expected_count}:actual={len(phase_paths)}")
        if project_initialization and cross_layer and not phase_paths:
            findings.append("greenfield_cross_layer_phase_artifacts_missing:master_only_blueprint_is_invalid")
        if phase_split_required and any(not family for family, _ in family_paths):
            findings.append("phase_family_layout_required:phases_must_live_under_family_directories")
        if phase_split_required:
            if not self._has_implementation_task_contract(master_text):
                findings.append("master_implementation_task_contract_missing_or_incomplete")
            required_families = {
                family
                for family, markers in {
                    "backend": ("backend", "fiber", "sqlite", "go"),
                    "frontend": ("frontend", "svelte", "tailwind", "spa"),
                    "wails": ("wails", "desktop", "systray", "tray"),
            }.items()
                if all(marker in master_text.lower() for marker in markers[:2])
            }
            for family in sorted(required_families):
                if not any(name.lower() == family for name, _ in family_paths if name):
                    findings.append(f"phase_family_missing:{family}")
        for family in sorted({name for name, _ in family_paths if name}):
            family_phase_paths = [path for (name, _), paths in family_paths.items() if name == family for path in paths]
            family_text = "\n".join(path.read_text(encoding="utf-8") for path in family_phase_paths)
            family_file_count = len(
                re.findall(
                    r"^\|\s*[^|]+\|[^|]+\|\s*(?:NEW|MODIFY|DELETE|REPLACE|CREATE|ADD)",
                    family_text,
                    re.IGNORECASE | re.MULTILINE,
                )
            )
            has_subfeatures = any(name == family and subfeature for name, subfeature in family_paths)
            if family_file_count > 8 and not has_subfeatures:
                findings.append(f"phase_subfeature_layout_required:{family}:files={family_file_count}")
        for (family, subfeature), paths in sorted(family_paths.items()):
            phase_by_id: dict[str, Path] = {}
            for path in paths:
                text = path.read_text(encoding="utf-8")
                match = re.search(r"^phase_id:\s*(P\d+)\s*$", text, re.IGNORECASE | re.MULTILINE)
                if match is None:
                    match = re.search(r"(?:^|[-_])(P\d+)(?:[-_]|$)", path.stem, re.IGNORECASE)
                if match is None:
                    findings.append(f"phase_blueprint_missing_id:{path}")
                    continue
                phase_id = match.group(1).upper()
                if phase_id in phase_by_id:
                    findings.append(f"phase_blueprint_duplicate:{family or 'root'}:{phase_id}")
                phase_by_id[phase_id] = path
                normalized_text = self._normalize(text)
                for marker in self.required_phase_markers:
                    if self._normalize(marker) not in normalized_text:
                        findings.append(f"phase_blueprint_incomplete:{family or 'root'}/{subfeature or 'direct'}:{phase_id}:{marker}")
                if phase_split_required and not self._has_implementation_task_contract(text):
                    findings.append(
                        f"phase_implementation_task_contract_missing_or_incomplete:{family or 'root'}/{subfeature or 'direct'}:{phase_id}"
                    )
            if family and phase_by_id:
                numbers = sorted(int(re.search(r"\d+", phase_id).group(0)) for phase_id in phase_by_id)
                expected_numbers = list(range(1, max(numbers) + 1))
                if numbers != expected_numbers:
                    findings.append(f"phase_sequence_gap:{family}/{subfeature or 'direct'}:{numbers}")
        return ArtifactSetValidationResult(not findings, findings)

    @staticmethod
    def _has_cross_layer_families(text: str) -> bool:
        lowered = text.lower()
        families = (
            ("backend", ("backend", "fiber", "sqlite", "go")),
            ("frontend", ("frontend", "svelte", "tailwind", "spa")),
            ("wails", ("wails", "desktop", "systray", "tray")),
        )
        return sum(all(token in lowered for token in tokens[:2]) for _, tokens in families) >= 2

    @staticmethod
    def _has_implementation_task_contract(text: str) -> bool:
        """Require a fresh-agent executable task table for large deliveries."""
        lines = text.splitlines()
        heading_index = next(
            (
                index for index, line in enumerate(lines)
                if line.lstrip().startswith("#")
                and "implementation task contract" in re.sub(r"[^a-z0-9]+", " ", line.lower())
            ),
            None,
        )
        if heading_index is None:
            return False
        body: list[str] = []
        for line in lines[heading_index + 1:]:
            if line.lstrip().startswith("#"):
                break
            body.append(line)
        tables = [line for line in body if line.strip().startswith("|")]
        if len(tables) < 3:
            return False
        header = tables[0].lower()
        required = (
            "task", "responsibility", "exact", "depends", "consumes", "produces",
            "red", "implementation", "green", "evidence", "rollback",
        )
        if any(token not in header for token in required):
            return False
        data_rows = [line for line in tables[2:] if "{{" not in line]
        if not data_rows:
            return False
        forbidden = re.compile(
            r"\b(?:tbd|todo|implement later|write tests|as appropriate|as needed|similar to)\b",
            re.IGNORECASE,
        )
        return not any(forbidden.search(row) for row in data_rows)

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


__all__ = ["ArtifactSetValidationResult", "BlueprintArtifactSetValidator"]
