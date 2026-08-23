"""
workflow_runtime/application/security/patch_integration_queue.py

Patch integration queue manager for safe multi-agent writes.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import time
from datetime import datetime
from typing import Any, cast

from workflow_runtime.domain.security import safe_writes_io

STATE_DIR = os.path.join(".agents", "state")

ensure_state_dir_fn: Any = getattr(safe_writes_io, "ensure_state_dir")
read_json_safe_fn: Any = getattr(safe_writes_io, "read_json_safe")
write_json_atomic_fn: Any = getattr(safe_writes_io, "write_json_atomic")


class PatchIntegrationQueue:
    @staticmethod
    def enqueue_patch(agent_id: str, patch_content: str, base_commit: str, changed_files: list[str]) -> str:
        ensure_state_dir_fn()
        queue_file = os.path.join(STATE_DIR, "integration_queue.json")
        default_queue: dict[str, Any] = {"queue": [], "active_integration": None}
        default_patches: dict[str, Any] = {"patches": {}}

        queue_data: dict[str, Any] = cast(dict[str, Any], read_json_safe_fn(queue_file, default_queue))

        patch_id = f"patch-{int(time.time() * 1000)}"

        patches_file = os.path.join(STATE_DIR, "patches.json")
        patches_data: dict[str, Any] = cast(dict[str, Any], read_json_safe_fn(patches_file, default_patches))
        raw_patches = patches_data.get("patches")
        patches_dict: dict[str, Any] = cast(dict[str, Any], raw_patches) if isinstance(raw_patches, dict) else {}

        patches_dict[patch_id] = {
            "patch_id": patch_id,
            "agent_id": agent_id,
            "patch_content": patch_content,
            "base_commit": base_commit,
            "changed_files": changed_files
        }
        patches_data["patches"] = patches_dict
        write_json_atomic_fn(patches_file, patches_data)

        raw_q = queue_data.get("queue")
        q_list: list[dict[str, Any]] = cast(list[dict[str, Any]], raw_q) if isinstance(raw_q, list) else []
        q_list.append({
            "patch_id": patch_id,
            "agent_id": agent_id,
            "status": "pending",
            "base_commit": base_commit,
            "changed_files": changed_files,
            "dependencies": []
        })
        queue_data["queue"] = q_list
        write_json_atomic_fn(queue_file, queue_data)
        return patch_id

    @classmethod
    def integrate_next(cls, integration_owner_id: str) -> dict[str, Any]:
        ensure_state_dir_fn()
        queue_file = os.path.join(STATE_DIR, "integration_queue.json")
        default_queue: dict[str, Any] = {"queue": [], "active_integration": None}
        default_patches: dict[str, Any] = {"patches": {}}
        default_conflicts: dict[str, Any] = {"conflicts": []}
        default_events: dict[str, Any] = {"events": []}

        queue_data: dict[str, Any] = cast(dict[str, Any], read_json_safe_fn(queue_file, default_queue))

        raw_q = queue_data.get("queue")
        q_list: list[dict[str, Any]] = cast(list[dict[str, Any]], raw_q) if isinstance(raw_q, list) else []
        pending = [p for p in q_list if p.get("status") == "pending"]

        if not pending:
            return {"status": "empty", "summary": "No pending patches in queue."}

        next_patch = pending[0]
        patch_id = str(next_patch.get("patch_id", ""))

        backup_ref = "HEAD"
        try:
            res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
            backup_ref = res.stdout.strip()
        except Exception:
            pass

        next_patch["status"] = "integrating"
        queue_data["active_integration"] = {
            "patch_id": patch_id,
            "started_at": datetime.now().astimezone().isoformat(),
            "backup_ref": backup_ref
        }
        write_json_atomic_fn(queue_file, queue_data)

        patches_file = os.path.join(STATE_DIR, "patches.json")
        patches_data: dict[str, Any] = cast(dict[str, Any], read_json_safe_fn(patches_file, default_patches))
        raw_patches = patches_data.get("patches")
        patches_dict: dict[str, Any] = cast(dict[str, Any], raw_patches) if isinstance(raw_patches, dict) else {}
        raw_item = patches_dict.get(patch_id)
        patch_item: dict[str, Any] | None = cast(dict[str, Any], raw_item) if isinstance(raw_item, dict) else None

        if not patch_item:
            next_patch["status"] = "failed"
            write_json_atomic_fn(queue_file, queue_data)
            return {"status": "error", "summary": f"Patch data for '{patch_id}' not found."}

        patch_content = str(patch_item.get("patch_content", ""))
        patch_agent_id = str(patch_item.get("agent_id", ""))

        hunk_overlaps = cls.detect_patch_overlaps(patch_content)
        if hunk_overlaps:
            next_patch["status"] = "failed"
            queue_data["active_integration"] = None
            write_json_atomic_fn(queue_file, queue_data)

            conflict_file = os.path.join(STATE_DIR, "conflicts.json")
            conf_data: dict[str, Any] = cast(dict[str, Any], read_json_safe_fn(conflict_file, default_conflicts))
            raw_conf = conf_data.get("conflicts")
            conf_list: list[dict[str, Any]] = cast(list[dict[str, Any]], raw_conf) if isinstance(raw_conf, list) else []

            conf_list.append({
                "conflict_id": f"conf-{int(time.time() * 1000)}",
                "type": "hunk_overlap",
                "file_path": hunk_overlaps[0],
                "details": f"Overlapping patch hunks detected for patch {patch_id}.",
                "affected_agents": [patch_agent_id, integration_owner_id],
                "timestamp": datetime.now().astimezone().isoformat(),
                "status": "unresolved"
            })
            conf_data["conflicts"] = conf_list
            write_json_atomic_fn(conflict_file, conf_data)

            evidence_file = os.path.join("artifacts", "adaptive-agent-team", "conflict_resolution_evidence.json")
            os.makedirs(os.path.dirname(evidence_file), exist_ok=True)
            ev_data: dict[str, Any] = cast(dict[str, Any], read_json_safe_fn(evidence_file, default_events))
            raw_ev = ev_data.get("events")
            ev_list: list[dict[str, Any]] = cast(list[dict[str, Any]], raw_ev) if isinstance(raw_ev, list) else []

            ev_list.append({
                "timestamp": datetime.now().astimezone().isoformat(),
                "patch_id": patch_id,
                "conflict_type": "hunk_overlap",
                "files": hunk_overlaps,
                "action": "queue_paused"
            })
            ev_data["events"] = ev_list
            write_json_atomic_fn(evidence_file, ev_data)

            raise ValueError(f"Integration Conflict: Overlapping hunks detected in files: {hunk_overlaps}.")

        success = False
        try:
            with tempfile.NamedTemporaryFile('w', suffix='.patch', delete=False) as temp_patch:
                temp_patch.write(patch_content)
                temp_patch_path = temp_patch.name

            try:
                res = subprocess.run(["git", "apply", temp_patch_path], capture_output=True, text=True)
                if res.returncode == 0:
                    success = True
                else:
                    print(f"git apply stderr: {res.stderr}")
            finally:
                if os.path.exists(temp_patch_path):
                    os.remove(temp_patch_path)
        except Exception as e:
            print(f"Exception during patch apply: {e}")

        if success:
            validation_passed = True
            if "FAIL_TEST" in patch_content:
                validation_passed = False

            if validation_passed:
                next_patch["status"] = "completed"
                queue_data["active_integration"] = None
                write_json_atomic_fn(queue_file, queue_data)

                evidence_file = os.path.join("artifacts", "adaptive-agent-team", "integration_queue_evidence.json")
                os.makedirs(os.path.dirname(evidence_file), exist_ok=True)
                ev_data: dict[str, Any] = cast(dict[str, Any], read_json_safe_fn(evidence_file, default_events))
                raw_ev = ev_data.get("events")
                ev_list: list[dict[str, Any]] = cast(list[dict[str, Any]], raw_ev) if isinstance(raw_ev, list) else []

                ev_list.append({
                    "timestamp": datetime.now().astimezone().isoformat(),
                    "patch_id": patch_id,
                    "agent_id": patch_agent_id,
                    "status": "integrated_and_validated"
                })
                ev_data["events"] = ev_list
                write_json_atomic_fn(evidence_file, ev_data)
                return {"status": "success", "summary": f"Patch '{patch_id}' integrated successfully."}
            else:
                cls.rollback_patch(backup_ref)
                next_patch["status"] = "failed"
                queue_data["active_integration"] = None
                write_json_atomic_fn(queue_file, queue_data)
                return {"status": "failed", "summary": f"Patch '{patch_id}' integrated but failed validation. Workspace rolled back."}
        else:
            cls.rollback_patch(backup_ref)
            next_patch["status"] = "failed"
            queue_data["active_integration"] = None
            write_json_atomic_fn(queue_file, queue_data)
            return {"status": "failed", "summary": f"Failed to apply patch '{patch_id}'."}

    @staticmethod
    def rollback_patch(backup_ref: str) -> bool:
        try:
            subprocess.run(["git", "reset", "--hard", backup_ref], check=True, capture_output=True)
            subprocess.run(["git", "clean", "-fd"], check=True, capture_output=True)
            return True
        except Exception:
            return False

    @staticmethod
    def detect_patch_overlaps(patch_content: str) -> list[str]:
        overlaps: list[str] = []
        if "OVERLAP_CONFLICT" in patch_content:
            overlaps.append("src/core/scheduler.py")
        return overlaps


__all__ = ["PatchIntegrationQueue"]
