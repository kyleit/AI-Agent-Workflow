import os
import tempfile
import time
from datetime import datetime, timedelta
from typing import Any, cast

from workflow_runtime.infrastructure.session.session_lock import OSFileLock
from workflow_runtime.infrastructure.session.state_sync import \
    read_json_safe as _read_json_safe
from workflow_runtime.infrastructure.session.state_sync import \
    write_json_atomic as _write_json_atomic

STATE_DIR = os.path.join(".agents", "state")

from workflow_runtime.domain.security.safe_writes_io import (
    calculate_file_hash, ensure_state_dir)


class AdaptiveTeamPlanner:
    @staticmethod
    def plan_team(
        task_complexity: str,
        dependency_depth: int,
        independent_workstreams: int,
        shared_write_scope_count: int,
        estimated_coordination_cost: float,
        estimated_parallel_benefit: float,
        risk_level: str,
        specialized_roles: list[str],
        context_description: str
    ) -> dict[str, Any]:
        ensure_state_dir()

        is_release = "release" in context_description.lower() or "version" in context_description.lower() or "changelog" in context_description.lower()

        if is_release:
            if risk_level.lower() == "high":
                plan = {
                    "execution_pattern": "single_agent_with_verifier",
                    "recommended_agent_count": 2,
                    "writer_count": 1,
                    "reviewer_count": 1,
                    "reasoning_summary": "High-risk release workflow requires exactly one Release Agent and one read-only Verification Agent.",
                    "ownership_plan": {
                        ".": "RELEASE-AGENT-01"
                    },
                    "integration_strategy": "sequential_release"
                }
            else:
                plan = {
                    "execution_pattern": "single_agent",
                    "recommended_agent_count": 1,
                    "writer_count": 1,
                    "reviewer_count": 0,
                    "reasoning_summary": "Standard release workflow requires exactly one Release Agent for sequential coordination.",
                    "ownership_plan": {
                        ".": "RELEASE-AGENT-01"
                    },
                    "integration_strategy": "sequential_release"
                }
        elif task_complexity.lower() in ["trivial", "small"] and independent_workstreams <= 1:
            plan = {
                "execution_pattern": "single_agent",
                "recommended_agent_count": 1,
                "writer_count": 1,
                "reviewer_count": 0,
                "reasoning_summary": f"Trivial/Small task ('{task_complexity}') with sequential steps. No parallel benefit exists.",
                "ownership_plan": {
                    ".": "CODER-AGENT-01"
                },
                "integration_strategy": "direct"
            }
        elif task_complexity.lower() == "medium" and shared_write_scope_count > 1 and independent_workstreams <= 1:
            plan = {
                "execution_pattern": "multi_agent_research_single_writer",
                "recommended_agent_count": 3,
                "writer_count": 1,
                "reviewer_count": 2,
                "reasoning_summary": "Task involves multiple research domains but sequential writes are safer to prevent collisions. Assigning one Writer.",
                "ownership_plan": {
                    ".": "WRITER-AGENT-01"
                },
                "integration_strategy": "analyst_handoff"
            }
        elif independent_workstreams > 1 and shared_write_scope_count == 0:
            ownership_plan: dict[str, str] = {}
            for i in range(min(independent_workstreams, 3)):
                ownership_plan[f"module_{i + 1}/"] = f"WRITER-AGENT-0{i + 1}"

            plan = {
                "execution_pattern": "multi_writer_isolated",
                "recommended_agent_count": independent_workstreams + 1,
                "writer_count": independent_workstreams,
                "reviewer_count": 0,
                "reasoning_summary": "Task has disjoint workstreams with independent, non-overlapping directory scopes.",
                "ownership_plan": ownership_plan,
                "integration_strategy": "serialized_patch_queue"
            }
        else:
            plan = {
                "execution_pattern": "multi_agent_research_single_writer",
                "recommended_agent_count": 2,
                "writer_count": 1,
                "reviewer_count": 1,
                "reasoning_summary": "Overlapping write scopes or high risk detected. Multi-Writer execution is rejected. Falling back to Mode B.",
                "ownership_plan": {
                    ".": "WRITER-AGENT-01"
                },
                "integration_strategy": "analyst_handoff"
            }

        plan_path = os.path.join(STATE_DIR, "team_plan.json")
        _write_json_atomic(plan_path, plan)
        return plan

class LeaseManager:
    @staticmethod
    def check_overlap(scope_a: str, scope_b: str) -> bool:
        if scope_a == "." or scope_b == ".":
            return True
        abs_a = os.path.abspath(scope_a)
        abs_b = os.path.abspath(scope_b)

        repo_root = os.path.abspath(".")
        rel_a = os.path.relpath(abs_a, repo_root).replace('\\', '/').strip('/')
        rel_b = os.path.relpath(abs_b, repo_root).replace('\\', '/').strip('/')

        if rel_a == "." or rel_b == ".":
            return True

        parts_a = rel_a.split('/')
        parts_b = rel_b.split('/')

        if parts_a == parts_b:
            return True
        if rel_a.startswith(rel_b + "/"):
            return True
        if rel_b.startswith(rel_a + "/"):
            return True
        return False

    @classmethod
    def acquire_lease(cls, owner_id: str, scope: str, duration_seconds: int = 600) -> dict[str, Any]:
        ensure_state_dir()
        lease_file = os.path.join(STATE_DIR, "write_leases.json")
#         from workflow_runtime.infrastructure.session.session import OSFileLock
        lock = cast(Any, OSFileLock(lease_file + ".lock"))
        import time
        while not lock.acquire():
            time.sleep(0.05)
        try:
            data = _read_json_safe(lease_file) or {"leases": {}, "history": []}

            now = datetime.now().astimezone()
            active_leases: dict[str, dict[str, Any]] = {}
            for lid, lease in data["leases"].items():
                expires_at = datetime.fromisoformat(lease["expires_at"])
                if expires_at > now and lease["status"] == "active":
                    active_leases[lid] = lease
                else:
                    data["history"].append({
                        "timestamp": datetime.now().astimezone().isoformat(),
                        "event": "expired",
                        "lease_id": lid,
                        "owner_id": lease["owner_id"],
                        "scope": lease["scope"]
                    })

            data["leases"] = active_leases

            for lid, lease in active_leases.items():
                if cls.check_overlap(lease["scope"], scope):
                    raise ValueError(f"Lease acquisition blocked: scope '{scope}' overlaps with active lease '{lease['scope']}' owned by {lease['owner_id']}.")

            fencing_token = 1
            for old_event in reversed(data["history"]):
                if old_event["scope"] == scope and "fencing_token" in old_event:
                    fencing_token = old_event["fencing_token"] + 1
                    break

            lease_id = f"lease-{int(time.time() * 1000)}"
            new_lease = {
              "lease_id": lease_id,
              "owner_id": owner_id,
              "scope": scope,
              "fencing_token": fencing_token,
              "acquired_at": now.isoformat(),
              "expires_at": (now + timedelta(seconds=duration_seconds)).isoformat(),
              "last_heartbeat_at": now.isoformat(),
              "status": "active"
            }

            data["leases"][lease_id] = new_lease
            data["history"].append({
                "timestamp": now.isoformat(),
                "event": "acquired",
                "lease_id": lease_id,
                "owner_id": owner_id,
                "scope": scope,
                "fencing_token": fencing_token
            })

            _write_json_atomic(lease_file, data)

            ownership_file = os.path.join(STATE_DIR, "ownership.json")
            ownership_data = _read_json_safe(ownership_file) or {}
            ownership_data[scope] = owner_id
            _write_json_atomic(ownership_file, ownership_data)

            return new_lease
        finally:
            lock.release()

    @staticmethod
    def release_lease(owner_id: str, lease_id: str) -> bool:
        ensure_state_dir()
        lease_file = os.path.join(STATE_DIR, "write_leases.json")
#         from workflow_runtime.infrastructure.session.session import OSFileLock
        lock = cast(Any, OSFileLock(lease_file + ".lock"))
        import time
        while not lock.acquire():
            time.sleep(0.05)
        try:
            data = _read_json_safe(lease_file) or {"leases": {}, "history": []}

            if lease_id in data["leases"]:
                lease = data["leases"][lease_id]
                if lease["owner_id"] == owner_id:
                    del data["leases"][lease_id]
                    data["history"].append({
                        "timestamp": datetime.now().astimezone().isoformat(),
                        "event": "released",
                        "lease_id": lease_id,
                        "owner_id": owner_id,
                        "scope": lease["scope"]
                    })
                    _write_json_atomic(lease_file, data)

                    ownership_file = os.path.join(STATE_DIR, "ownership.json")
                    ownership_data = _read_json_safe(ownership_file) or {}
                    if lease["scope"] in ownership_data:
                        del ownership_data[lease["scope"]]
                    _write_json_atomic(ownership_file, ownership_data)
                    return True
            return False
        finally:
            lock.release()

    @staticmethod
    def renew_lease(owner_id: str, lease_id: str) -> bool:
        ensure_state_dir()
        lease_file = os.path.join(STATE_DIR, "write_leases.json")
#         from workflow_runtime.infrastructure.session.session import OSFileLock
        lock = cast(Any, OSFileLock(lease_file + ".lock"))
        import time
        while not lock.acquire():
            time.sleep(0.05)
        try:
            data = _read_json_safe(lease_file) or {"leases": {}, "history": []}

            if lease_id in data["leases"]:
                lease = data["leases"][lease_id]
                if lease["owner_id"] == owner_id:
                    now = datetime.now().astimezone()
                    lease["last_heartbeat_at"] = now.isoformat()
                    lease["expires_at"] = (now + timedelta(seconds=600)).isoformat()
                    _write_json_atomic(lease_file, data)
                    return True
            return False
        finally:
            lock.release()

class ConcurrencyController:
    @staticmethod
    def capture_base_state(file_path: str) -> dict[str, Any]:
        file_hash = calculate_file_hash(file_path)
        mtime = os.path.getmtime(file_path) if os.path.exists(file_path) else 0.0
        return {
            "file_path": file_path,
            "base_hash": file_hash,
            "base_mtime": mtime
        }

    @staticmethod
    def validate_write(file_path: str, expected_hash: str, owner_id: str, fencing_token: int) -> bool:
        abs_target = os.path.abspath(file_path)
        abs_repo = os.path.abspath(".")
        if not abs_target.startswith(abs_repo):
            raise PermissionError(f"Security Rejection: path traversal detected for file '{file_path}' outside workspace root.")
        if os.path.islink(file_path):
            real_path = os.path.realpath(file_path)
            if not real_path.startswith(abs_repo):
                raise PermissionError("Security Rejection: symbolic link resolves outside workspace root.")

        lease_file = os.path.join(STATE_DIR, "write_leases.json")
        lease_data = _read_json_safe(lease_file) or {"leases": {}, "history": []}
        now = datetime.now().astimezone()

        has_valid_lease = False
        for _lid, lease in cast(dict[str, dict[str, Any]], lease_data["leases"]).items():
            expires_at = datetime.fromisoformat(lease["expires_at"])
            if expires_at > now and lease["status"] == "active":
                if LeaseManager.check_overlap(lease["scope"], file_path):
                    if lease["owner_id"] == owner_id:
                        if lease["fencing_token"] == fencing_token:
                            has_valid_lease = True
                            break
                        else:
                            raise ValueError(f"Fencing Token Mismatch: write rejected. Provided token {fencing_token}, active lease token is {lease['fencing_token']}.")
                    else:
                        raise ValueError(f"Lease Violation: write rejected. Path is leased by {lease['owner_id']}.")

        if not has_valid_lease:
            raise ValueError(f"Lease Rejection: write rejected. Agent '{owner_id}' does not have a valid active lease for path '{file_path}'.")

        current_hash = calculate_file_hash(file_path)
        if current_hash != expected_hash:
            conflict_file = os.path.join(STATE_DIR, "conflicts.json")
            conf_data = _read_json_safe(conflict_file) or {"conflicts": []}
            conf_data["conflicts"].append({
                "conflict_id": f"conf-{int(time.time() * 1000)}",
                "type": "base_hash_mismatch",
                "file_path": file_path,
                "details": f"Stale write rejected. Expected hash {expected_hash}, current hash {current_hash}.",
                "affected_agents": [owner_id],
                "timestamp": now.isoformat(),
                "status": "unresolved"
            })
            _write_json_atomic(conflict_file, conf_data)

            evidence_file = os.path.join("artifacts", "adaptive-agent-team", "stale_write_evidence.json")
            os.makedirs(os.path.dirname(evidence_file), exist_ok=True)
            ev_data = _read_json_safe(evidence_file) or {"events": []}
            ev_data["events"].append({
                "timestamp": now.isoformat(),
                "file_path": file_path,
                "expected_hash": expected_hash,
                "current_hash": current_hash,
                "agent_id": owner_id,
                "action": "write_rejected"
            })
            _write_json_atomic(evidence_file, ev_data)

            raise ValueError(f"Stale Write Collision: Base hash mismatch for file '{file_path}'. File changed on disk since read.")

        return True

class AtomicWriter:
    @classmethod
    def atomic_replace(cls, file_path: str, content: str, expected_hash: str, owner_id: str, fencing_token: int) -> bool:
        ConcurrencyController.validate_write(file_path, expected_hash, owner_id, fencing_token)

        target_dir = os.path.dirname(os.path.abspath(file_path))
        os.makedirs(target_dir, exist_ok=True)

        permissions = 0o644
        if os.path.exists(file_path):
            permissions = os.stat(file_path).st_mode

        temp_fd, temp_path = tempfile.mkstemp(dir=target_dir)
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                f.write(content)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass

            os.chmod(temp_path, permissions)
            os.replace(temp_path, file_path)

            evidence_file = os.path.join("artifacts", "adaptive-agent-team", "ownership_evidence.json")
            os.makedirs(os.path.dirname(evidence_file), exist_ok=True)
            ev_data = _read_json_safe(evidence_file) or {"writes": []}
            ev_data["writes"].append({
                "timestamp": datetime.now().astimezone().isoformat(),
                "file_path": file_path,
                "agent_id": owner_id,
                "fencing_token": fencing_token,
                "status": "success"
            })
            _write_json_atomic(evidence_file, ev_data)
            return True
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e



# -- re-exports from split parts (backward compat) --
from workflow_runtime.application.security.patch_integration_queue import (
    PatchIntegrationQueue)

__all__ = ['AdaptiveTeamPlanner', 'ConcurrencyController', 'AtomicWriter', 'PatchIntegrationQueue']
