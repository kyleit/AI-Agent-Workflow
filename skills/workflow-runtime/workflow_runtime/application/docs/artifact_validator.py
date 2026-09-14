# artifact_validator.py
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, cast

import yaml

REQUIRED_BLUEPRINT_HEADERS = [
    "Summary",
    "Scope",
    "Technical Design",
    "Files to Change",
    "Implementation Steps",
    "Validation Plan",
    "Rollback Plan"
]
BLUEPRINT_HEADER_ALIASES = {
    "Summary": ("summary",),
    "Scope": ("scope", "completeness boundary"),
    "Technical Design": (
        "technical design",
        "component boundaries",
        "executive architecture",
    ),
    "Files to Change": ("files to change", "file-by-file change matrix"),
    "Implementation Steps": (
        "implementation steps",
        "implementation sequence",
        "specialist implementation sequence",
    ),
    "Validation Plan": ("validation plan", "qa verification matrix"),
    "Rollback Plan": ("rollback plan", "rollback"),
}


def validate_blueprint_file(filepath: str, workflow_prefix: str | None = None) -> dict[str, Any]:
    if not os.path.exists(filepath):
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": f"Blueprint file does not exist at {filepath}.",
            "warnings": [],
            "files_read": [],
            "files_written": []
        }

    raw_path = Path(filepath)
    workspace_root = _find_workspace_root(raw_path.resolve())
    clarification_state = _clarification_state_findings(workspace_root)
    if clarification_state:
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": "Blueprint validation stopped because clarification state is inconsistent.",
            "warnings": [],
            "blocking_findings": clarification_state,
            "files_read": [filepath],
            "files_written": [],
        }
    if raw_path.is_absolute():
        try:
            normalized = raw_path.resolve().relative_to(workspace_root).as_posix()
        except ValueError:
            normalized = raw_path.as_posix()
    else:
        normalized = filepath.replace("\\", "/")

    is_legacy_blueprint = normalized.startswith("docs/blueprints/")
    is_semantic_blueprint = normalized.startswith("docs/features/") and "/blueprints/" in normalized
    if not (is_legacy_blueprint or is_semantic_blueprint):
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": "Blueprint file must be located under docs/features/<feature-family>/blueprints/ or legacy docs/blueprints/ directory.",
            "warnings": [],
            "files_read": [filepath],
            "files_written": []
        }

    if not (normalized.endswith("_blueprint.md") or normalized.endswith("-blueprint.md")):
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": "Blueprint filename must end with '_blueprint.md' or 'phase-blueprint.md'.",
            "warnings": [],
            "files_read": [filepath],
            "files_written": []
        }

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": f"Failed to read file: {e}",
            "warnings": [],
            "files_read": [filepath],
            "files_written": []
        }

    parts = content.split("---")
    if len(parts) < 3:
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": "Blueprint must contain YAML frontmatter surrounded by '---'.",
            "warnings": [],
            "files_read": [filepath],
            "files_written": []
        }

    frontmatter_raw = parts[1].strip()
    try:
        frontmatter = yaml.safe_load(frontmatter_raw)
    except Exception as e:
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": f"Invalid YAML frontmatter format: {e}",
            "warnings": [],
            "files_read": [filepath],
            "files_written": []
        }

    if not isinstance(frontmatter, dict):
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": "Frontmatter is not a valid YAML dictionary.",
            "warnings": [],
            "files_read": [filepath],
            "files_written": []
        }

    fm_dict = cast(dict[str, Any], frontmatter)
    feat_id = str(fm_dict.get("feature_id", "") or "")
    if workflow_prefix:
        if not feat_id.startswith(workflow_prefix):
            return {
                "status": "failure",
                "command": "validate blueprint",
                "summary": f"Blueprint feature_id '{feat_id}' does not match expected prefix '{workflow_prefix}'.",
                "warnings": [],
                "files_read": [filepath],
                "files_written": []
            }

    # Agent-authored Blueprint metadata is not owner approval. Require a
    # scoped runtime record before accepting APPROVED/FROZEN claims.
    declared_status = str(fm_dict.get("status", "") or "").upper()
    if is_semantic_blueprint and declared_status in {"APPROVED", "FROZEN"}:
        if not _has_scoped_owner_approval(
            _find_workspace_root(raw_path.resolve()),
            normalized,
            feat_id,
        ):
            return {
                "status": "failure",
                "command": "validate blueprint",
                "summary": "Blueprint claims owner approval without a bound runtime approval record.",
                "warnings": [],
                "blocking_findings": ["unbound_blueprint_approval_claim"],
                "files_read": [filepath],
                "files_written": [],
            }

    missing_headers: list[str] = []
    lines = content.splitlines()
    for header in REQUIRED_BLUEPRINT_HEADERS:
        aliases = BLUEPRINT_HEADER_ALIASES.get(header, (header.lower(),))
        found = any(
            line.strip().startswith("#")
            and any(alias in line.strip().lower() for alias in aliases)
            for line in lines
        )
        if not found:
            missing_headers.append(header)

    if missing_headers:
        return {
            "status": "failure",
            "command": "validate blueprint",
            "summary": f"Blueprint is missing required headers: {', '.join(missing_headers)}.",
            "warnings": [],
            "files_read": [filepath],
            "files_written": []
        }

    # Semantic Blueprints are implementation contracts, not just documents.
    # Route them through the same completeness loop used by approval and
    # implementation-entry verification so a thin document cannot report PASS.
    if is_semantic_blueprint:
        from workflow_runtime.application.workflow.blueprint_validation_loop import (
            BlueprintAutoValidationService,
        )

        blueprint = Path(filepath).resolve()
        workspace_root = _find_workspace_root(blueprint)
        feature_match = re.search(
            r"^\s*(?:feature_id|issue_id|quick_id|work_item_id):\s*([A-Za-z0-9_-]+)",
            content,
            re.MULTILINE,
        )
        work_item_id = feature_match.group(1) if feature_match else blueprint.name.split("_", 1)[0]
        try:
            result = BlueprintAutoValidationService(workspace_root).validate_for_approval(
                blueprint,
                work_item_id,
                allow_existing_creates=False,
                post_implementation=False,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return {
                "status": "failure",
                "command": "validate blueprint",
                "summary": f"Strict Blueprint validation could not complete: {exc}",
                "warnings": [],
                "blocking_findings": ["strict_blueprint_validation_error"],
                "files_read": [filepath],
                "files_written": [],
            }
        passed = result.status == "APPROVAL_READY"
        return {
            "status": "success" if passed else "failure",
            "command": "validate blueprint",
            "summary": (
                "Blueprint passed strict approval-readiness validation."
                if passed
                else "Blueprint is too thin or incomplete for approval-readiness validation."
            ),
            "warnings": [],
            "blocking_findings": result.blocking_findings,
            "score": result.score,
            "evidence": result.evidence,
            "files_read": [filepath],
            "files_written": result.evidence,
        }

    requirement_findings = _validate_requirement_decision_ledger(content, normalized)
    if requirement_findings:
        return {
            "status": "failure",
            "command": "validate artifact",
            "summary": "Requirement Specification has unresolved or silently inferred decisions.",
            "warnings": [],
            "blocking_findings": requirement_findings,
            "files_read": [filepath],
            "files_written": [],
        }

    return {
        "status": "success",
        "command": "validate blueprint",
        "summary": "Blueprint file conforms to all standards.",
        "warnings": [],
        "files_read": [filepath],
        "files_written": []
    }


def _find_workspace_root(blueprint: Path) -> Path:
    for candidate in (blueprint.parent, *blueprint.parents):
        if candidate.name.lower() == "docs":
            return candidate.parent.resolve()
        if (
            (candidate / ".agents" / "AI_RULES.md").is_file()
            or (candidate / ".agents").is_dir()
            or (candidate / ".git").exists()
        ):
            return candidate.resolve()
    return Path.cwd().resolve()


def _has_scoped_owner_approval(workspace_root: Path, relative_path: str, work_item_id: str) -> bool:
    """Return true only for approval bound to this exact work-item and path."""
    candidates = [
        workspace_root / ".agents" / "state" / "work-items" / work_item_id / "approvals.json",
        workspace_root / ".agents" / "state" / "approvals.json",
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
        if approved_path == relative_path.lstrip("./") and approved_work_item == work_item_id:
            return True
    return False


def validate_artifact_general(filepath: str) -> dict[str, Any]:
    if not os.path.exists(filepath):
        return {
            "status": "failure",
            "command": "validate artifact",
            "summary": f"Artifact file does not exist at {filepath}.",
            "warnings": [],
            "files_read": [],
            "files_written": []
        }
    try:
        content = Path(filepath).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return {
            "status": "failure",
            "command": "validate artifact",
            "summary": f"Artifact file could not be read: {exc}",
            "warnings": [],
            "files_read": [filepath],
            "files_written": [],
        }
    workspace_root = _find_workspace_root(Path(filepath).resolve())
    findings = _clarification_state_findings(workspace_root)
    findings.extend(_validate_requirement_decision_ledger(content, filepath.replace("\\", "/")))
    if findings:
        return {
            "status": "failure",
            "command": "validate artifact",
            "summary": "Requirement Specification has unresolved or silently inferred decisions.",
            "warnings": [],
            "blocking_findings": findings,
            "files_read": [filepath],
            "files_written": [],
        }
    return {
        "status": "success",
        "command": "validate artifact",
        "summary": f"Artifact file {filepath} verified.",
        "warnings": [],
        "files_read": [filepath],
        "files_written": []
    }


def _clarification_state_findings(workspace_root: Path) -> list[str]:
    """Expose the generic state guard through every artifact validation route."""
    findings: list[str] = []
    try:
        from workflow_runtime.application.workflow.clarification_state import (
            validate_clarification_state,
        )

        result = validate_clarification_state(workspace_root)
        findings.extend(str(item) for item in result.get("blocking_findings", []))
    except (ImportError, OSError, TypeError, ValueError):
        findings.append("clarification_state_validation_unavailable")
    findings.extend(_question_artifact_findings(workspace_root))
    return findings


def _question_artifact_findings(workspace_root: Path) -> list[str]:
    """Reject Markdown questions that claim resolution without owner evidence."""
    findings: list[str] = []
    questions_root = workspace_root / "docs" / "features"
    if not questions_root.is_dir():
        return findings
    owner_evidence = re.compile(
        r"owner[_ -]?response(?:[_ -]?id)?|response\s+receipt|owner'?s?\s+answer|"
        r"exact\s+answer|approval[_ -]?record|owner\s+selected",
        re.IGNORECASE,
    )
    for question_path in sorted(questions_root.rglob("questions/*.md")):
        try:
            content = question_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            findings.append(f"clarification_question_read_failed:{question_path}")
            continue
        status = re.search(
            r"^[- ]*(?:\*\*?)?Status(?:\*\*?)?\s*:\s*[`\"']?([^`\"'\r\n]+)",
            content,
            re.IGNORECASE | re.MULTILINE,
        )
        if status is None or status.group(1).strip().upper() not in {"RESOLVED", "APPROVED"}:
            continue
        if not owner_evidence.search(content):
            relative = question_path.relative_to(workspace_root).as_posix()
            findings.append(f"clarification_resolved_without_owner_response:{relative}")
    return findings


def _validate_requirement_decision_ledger(content: str, normalized_path: str) -> list[str]:
    """Enforce owner clarification before a Requirement Spec can advance."""
    path = normalized_path.lower().replace("\\", "/")
    if not ("/requirements/" in path or "/specifications/" in path):
        return []
    if "requirement specification" not in content.lower():
        return []
    headings = [
        re.sub(r"[^a-z0-9]+", " ", line.lstrip("#").strip().lower()).strip()
        for line in content.splitlines()
        if line.lstrip().startswith("#")
    ]
    if not any("ambiguity and decision ledger" in heading for heading in headings):
        return ["requirement_clarification_ledger_missing"]
    body = _section_body_text(content, "ambiguity and decision ledger")
    findings: list[str] = []
    rows = [line for line in body.splitlines() if line.strip().startswith("|")]
    data_rows = [line for line in rows if not re.match(r"^\s*\|\s*:?-+", line)]
    high_impact = re.compile(
        r"scope|data|schema|api|runtime|backend|persistence|security|route|screen|ux|migration",
        re.IGNORECASE,
    )
    for index, row in enumerate(data_rows, start=1):
        cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
        if not cells or cells[0].lower() == "item":
            continue
        classification = next((cell for cell in cells if cell.upper() in {"BLOCKING", "NON_BLOCKING", "DISCOVERABLE"}), "")
        decision = " ".join(cells).lower()
        if classification == "BLOCKING" and re.search(r"pending|unresolved|tbd|tbc|chưa|awaiting", decision):
            findings.append(f"requirement_blocking_decision_unresolved:row_{index}")
        owner_evidence = re.search(
            r"owner[_ -]?response(?:[_ -]?id)?|response\s+receipt|owner'?s?\s+answer|"
            r"exact\s+answer|approval[_ -]?record|owner\s+selected|explicitly\s+specified",
            decision,
            re.IGNORECASE,
        )
        source = cells[1].lower() if len(cells) > 1 else ""
        if classification == "BLOCKING" and not owner_evidence and "prompt" not in source:
            findings.append(f"requirement_blocking_owner_evidence_missing:row_{index}")
        if classification == "BLOCKING" and re.search(
            r"confirmed\s+by\s+owner|owner\s+confirmed|owner\s+approved|owner\s+selected",
            decision,
        ) and not re.search(
            r"owner[_ -]?response(?:[_ -]?id)?|approval[_ -]?record|prompt[_ -]?response|receipt",
            decision,
        ):
            findings.append(f"requirement_owner_confirmation_evidence_missing:row_{index}")
        if classification == "BLOCKING" and re.search(
            r"owner\s+clarification|interactive\s+clarification|owner[_ -]?response",
            decision,
        ):
            transaction_terms = (
                r"active\s+question|current\s+question|question\s+topic",
                r"selected\s+option|option\s+text|chosen\s+option",
                r"owner\s+answer|exact\s+answer|owner's\s+answer",
            )
            missing = [term for term in transaction_terms if not re.search(term, decision)]
            if missing:
                findings.append(f"requirement_clarification_transaction_capture_missing:row_{index}")
        if classification == "NON_BLOCKING" and high_impact.search(" ".join(cells)):
            source_is_prompt_only = source.strip() == "prompt"
            if not source_is_prompt_only or not re.search(
                r"explicitly\s+specified|hard\s+constraint|discoverable|inspected\s+evidence|approved\s+evidence",
                decision,
            ):
                findings.append(f"requirement_high_impact_inferred_as_non_blocking:row_{index}")
    pending = _pending_clarification_for_artifact(content, normalized_path)
    if pending:
        findings.append("requirement_created_while_owner_clarification_pending")
    return findings


def _pending_clarification_for_artifact(content: str, normalized_path: str) -> bool:
    """Reject specs emitted while the bound workflow is still waiting for owner input."""
    candidate = Path(normalized_path)
    if not candidate.is_absolute():
        candidate = Path(normalized_path)
    workspace_root = _find_workspace_root(Path(normalized_path).resolve()) if candidate.is_absolute() else Path.cwd().resolve()
    pending_path = workspace_root / ".agents" / "runtime" / "pending-clarification.json"
    try:
        pending = json.loads(pending_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return False
    if not isinstance(pending, dict):
        return False
    feature_match = re.search(
        r"(?:Feature/Fix ID|Work Item ID|feature_id|work_item_id)[^A-Za-z0-9_-]{0,20}`?([A-Za-z0-9_-]+)",
        content,
        re.IGNORECASE,
    )
    feature_id = feature_match.group(1) if feature_match else ""
    pending_work_item = str(pending.get("workflow_id") or pending.get("work_item_id") or "")
    return bool(
        pending_work_item
        and feature_id
        and pending_work_item == feature_id
        and str(pending.get("classification", "")).upper() == "BLOCKING"
        and str(pending.get("next_action", "")).lower().endswith("before_requirement_specification")
    )


def _section_body_text(content: str, marker: str) -> str:
    normalized_marker = re.sub(r"[^a-z0-9]+", " ", marker.lower()).strip()
    lines = content.splitlines()
    start = None
    for index, line in enumerate(lines):
        if not line.lstrip().startswith("#"):
            continue
        normalized = re.sub(r"[^a-z0-9]+", " ", line.lstrip("#").strip().lower()).strip()
        if normalized_marker in normalized:
            start = index + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].lstrip().startswith("#"):
            end = index
            break
    return "\n".join(lines[start:end])


__all__ = [
    "REQUIRED_BLUEPRINT_HEADERS",
    "validate_blueprint_file",
    "validate_artifact_general",
]
