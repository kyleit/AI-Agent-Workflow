from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_object(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _question_artifact_findings(workspace: Path) -> list[str]:
    """Reject a blocking question resolved by recommendation without owner evidence."""
    findings: list[str] = []
    question_root = workspace / "docs" / "features"
    if not question_root.is_dir():
        return findings
    for path in sorted(question_root.glob("**/questions/*.md")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        header = text.split("---", 2)[1] if text.startswith("---") and "---" in text[3:] else ""
        classification = "" if "classification:" not in header else header.split("classification:", 1)[1].splitlines()[0].strip().upper()
        status = "" if "status:" not in header else header.split("status:", 1)[1].splitlines()[0].strip().upper()
        if classification != "BLOCKING" or not status.startswith("RESOLVED"):
            continue
        lower = text.lower()
        owner_evidence = any(
            marker in lower
            for marker in (
                "owner response",
                "owner confirmed",
                "owner decision",
                "response receipt",
                "native response",
            )
        )
        if "default" in status or not owner_evidence:
            relative = path.relative_to(workspace).as_posix()
            findings.append(f"blocking_question_resolved_without_owner_evidence:{relative}")
    return findings


def validate_clarification_state(root: Path | str) -> dict[str, Any]:
    """Validate the generic owner-input state binding without choosing a domain option."""
    workspace = Path(root).resolve()
    pending_path = workspace / ".agents" / "runtime" / "pending-clarification.json"
    workflow_path = workspace / ".agents" / "state" / "workflow.json"
    question_findings = _question_artifact_findings(workspace)
    if not pending_path.exists():
        return {
            "status": "BLOCKED" if question_findings else "CLEAR",
            "blocking_findings": question_findings,
        }

    pending = _read_object(pending_path)
    if pending is None:
        return {
            "status": "BLOCKED",
            "blocking_findings": ["pending_clarification_invalid_json"],
        }

    workflow = _read_object(workflow_path) or {}
    pending_workflow = str(pending.get("workflow_id") or pending.get("work_item_id") or "")
    active_workflow = str(workflow.get("active_workflow") or "")
    classification = str(pending.get("classification") or "").upper()
    pending_status = str(pending.get("status") or classification).upper()
    waiting_for = str(workflow.get("waiting_for") or "")
    active_phase = str(workflow.get("active_phase") or "")
    findings: list[str] = list(question_findings)

    if not pending_workflow:
        findings.append("pending_clarification_workflow_binding_missing")
    elif active_workflow != pending_workflow:
        findings.append("pending_clarification_workflow_state_mismatch")

    if pending_status in {"RESOLVED", "ANSWERED", "COMPLETED"}:
        if not active_workflow:
            findings.append("resolved_clarification_without_active_workflow")
        if active_phase.lower() == "clarifying" or waiting_for == "owner_clarification":
            findings.append("resolved_clarification_still_in_waiting_state")
    elif classification == "BLOCKING":
        if active_phase.lower() != "clarifying" or waiting_for != "owner_clarification":
            findings.append("unresolved_clarification_not_in_waiting_state")

    return {
        "status": "BLOCKED" if findings else "VALID",
        "blocking_findings": findings,
        "pending": pending,
        "workflow": workflow,
    }


__all__ = ["validate_clarification_state"]
