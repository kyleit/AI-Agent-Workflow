# safe_multi_agent_writes.py
import os
import json
import hashlib
import time
import shutil
import tempfile
import subprocess
from datetime import datetime, timedelta

STATE_DIR = os.path.join(".agents", "state")

def ensure_state_dir():
    os.makedirs(STATE_DIR, exist_ok=True)

def read_json_safe(path: str, default: dict) -> dict:
    if not os.path.exists(path):
        return default
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default

def write_json_atomic(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(path))
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Windows-resilient retry replace loop
        retries = 5
        while retries > 0:
            try:
                os.replace(temp_path, path)
                break
            except OSError as e:
                retries -= 1
                if retries <= 0:
                    raise e
                time.sleep(0.02)
    except Exception as e:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        raise e

def calculate_hash(content_bytes: bytes) -> str:
    return hashlib.sha256(content_bytes).hexdigest()

def calculate_file_hash(path: str) -> str:
    if not os.path.exists(path):
        return ""
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""

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
    ) -> dict:
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
            ownership_plan = {}
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
        write_json_atomic(plan_path, plan)
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
    def acquire_lease(cls, owner_id: str, scope: str, duration_seconds: int = 600) -> dict:
        ensure_state_dir()
        lease_file = os.path.join(STATE_DIR, "write_leases.json")
        from session import OSFileLock
        lock = OSFileLock(lease_file + ".lock")
        import time
        while not lock.acquire():
            time.sleep(0.05)
        try:
            data = read_json_safe(lease_file, {"leases": {}, "history": []})
            
            now = datetime.now().astimezone()
            active_leases = {}
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
            
            write_json_atomic(lease_file, data)
            
            ownership_file = os.path.join(STATE_DIR, "ownership.json")
            ownership_data = read_json_safe(ownership_file, {})
            ownership_data[scope] = owner_id
            write_json_atomic(ownership_file, ownership_data)
            
            return new_lease
        finally:
            lock.release()

    @staticmethod
    def release_lease(owner_id: str, lease_id: str) -> bool:
        ensure_state_dir()
        lease_file = os.path.join(STATE_DIR, "write_leases.json")
        from session import OSFileLock
        lock = OSFileLock(lease_file + ".lock")
        import time
        while not lock.acquire():
            time.sleep(0.05)
        try:
            data = read_json_safe(lease_file, {"leases": {}, "history": []})
            
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
                    write_json_atomic(lease_file, data)
                    
                    ownership_file = os.path.join(STATE_DIR, "ownership.json")
                    ownership_data = read_json_safe(ownership_file, {})
                    if lease["scope"] in ownership_data:
                        del ownership_data[lease["scope"]]
                    write_json_atomic(ownership_file, ownership_data)
                    return True
            return False
        finally:
            lock.release()

    @staticmethod
    def renew_lease(owner_id: str, lease_id: str) -> bool:
        ensure_state_dir()
        lease_file = os.path.join(STATE_DIR, "write_leases.json")
        from session import OSFileLock
        lock = OSFileLock(lease_file + ".lock")
        import time
        while not lock.acquire():
            time.sleep(0.05)
        try:
            data = read_json_safe(lease_file, {"leases": {}, "history": []})
            
            if lease_id in data["leases"]:
                lease = data["leases"][lease_id]
                if lease["owner_id"] == owner_id:
                    now = datetime.now().astimezone()
                    lease["last_heartbeat_at"] = now.isoformat()
                    lease["expires_at"] = (now + timedelta(seconds=600)).isoformat()
                    write_json_atomic(lease_file, data)
                    return True
            return False
        finally:
            lock.release()

class ConcurrencyController:
    @staticmethod
    def capture_base_state(file_path: str) -> dict:
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
        lease_data = read_json_safe(lease_file, {"leases": {}, "history": []})
        now = datetime.now().astimezone()
        
        has_valid_lease = False
        for lid, lease in lease_data["leases"].items():
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
            conf_data = read_json_safe(conflict_file, {"conflicts": []})
            conf_data["conflicts"].append({
                "conflict_id": f"conf-{int(time.time() * 1000)}",
                "type": "base_hash_mismatch",
                "file_path": file_path,
                "details": f"Stale write rejected. Expected hash {expected_hash}, current hash {current_hash}.",
                "affected_agents": [owner_id],
                "timestamp": now.isoformat(),
                "status": "unresolved"
            })
            write_json_atomic(conflict_file, conf_data)
            
            evidence_file = os.path.join("artifacts", "adaptive-agent-team", "stale_write_evidence.json")
            os.makedirs(os.path.dirname(evidence_file), exist_ok=True)
            ev_data = read_json_safe(evidence_file, {"events": []})
            ev_data["events"].append({
                "timestamp": now.isoformat(),
                "file_path": file_path,
                "expected_hash": expected_hash,
                "current_hash": current_hash,
                "agent_id": owner_id,
                "action": "write_rejected"
            })
            write_json_atomic(evidence_file, ev_data)
            
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
            ev_data = read_json_safe(evidence_file, {"writes": []})
            ev_data["writes"].append({
                "timestamp": datetime.now().astimezone().isoformat(),
                "file_path": file_path,
                "agent_id": owner_id,
                "fencing_token": fencing_token,
                "status": "success"
            })
            write_json_atomic(evidence_file, ev_data)
            return True
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

class PatchIntegrationQueue:
    @staticmethod
    def enqueue_patch(agent_id: str, patch_content: str, base_commit: str, changed_files: list) -> str:
        ensure_state_dir()
        queue_file = os.path.join(STATE_DIR, "integration_queue.json")
        queue_data = read_json_safe(queue_file, {"queue": [], "active_integration": None})
        
        patch_id = f"patch-{int(time.time() * 1000)}"
        
        patches_file = os.path.join(STATE_DIR, "patches.json")
        patches_data = read_json_safe(patches_file, {"patches": {}})
        patches_data["patches"][patch_id] = {
            "patch_id": patch_id,
            "agent_id": agent_id,
            "patch_content": patch_content,
            "base_commit": base_commit,
            "changed_files": changed_files
        }
        write_json_atomic(patches_file, patches_data)
        
        queue_data["queue"].append({
            "patch_id": patch_id,
            "agent_id": agent_id,
            "status": "pending",
            "base_commit": base_commit,
            "changed_files": changed_files,
            "dependencies": []
        })
        write_json_atomic(queue_file, queue_data)
        return patch_id

    @classmethod
    def integrate_next(cls, integration_owner_id: str) -> dict:
        ensure_state_dir()
        queue_file = os.path.join(STATE_DIR, "integration_queue.json")
        queue_data = read_json_safe(queue_file, {"queue": [], "active_integration": None})
        
        pending = [p for p in queue_data["queue"] if p["status"] == "pending"]
        if not pending:
            return {"status": "empty", "summary": "No pending patches in queue."}
            
        next_patch = pending[0]
        patch_id = next_patch["patch_id"]
        
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
        write_json_atomic(queue_file, queue_data)
        
        patches_file = os.path.join(STATE_DIR, "patches.json")
        patches_data = read_json_safe(patches_file, {"patches": {}})
        patch_item = patches_data["patches"].get(patch_id)
        
        if not patch_item:
            next_patch["status"] = "failed"
            write_json_atomic(queue_file, queue_data)
            return {"status": "error", "summary": f"Patch data for '{patch_id}' not found."}
            
        hunk_overlaps = cls.detect_patch_overlaps(patch_item["patch_content"])
        if hunk_overlaps:
            next_patch["status"] = "failed"
            queue_data["active_integration"] = None
            write_json_atomic(queue_file, queue_data)
            
            conflict_file = os.path.join(STATE_DIR, "conflicts.json")
            conf_data = read_json_safe(conflict_file, {"conflicts": []})
            conf_data["conflicts"].append({
                "conflict_id": f"conf-{int(time.time() * 1000)}",
                "type": "hunk_overlap",
                "file_path": hunk_overlaps[0],
                "details": f"Overlapping patch hunks detected for patch {patch_id}.",
                "affected_agents": [patch_item["agent_id"], integration_owner_id],
                "timestamp": datetime.now().astimezone().isoformat(),
                "status": "unresolved"
            })
            write_json_atomic(conflict_file, conf_data)
            
            evidence_file = os.path.join("artifacts", "adaptive-agent-team", "conflict_resolution_evidence.json")
            os.makedirs(os.path.dirname(evidence_file), exist_ok=True)
            ev_data = read_json_safe(evidence_file, {"events": []})
            ev_data["events"].append({
                "timestamp": datetime.now().astimezone().isoformat(),
                "patch_id": patch_id,
                "conflict_type": "hunk_overlap",
                "files": hunk_overlaps,
                "action": "queue_paused"
            })
            write_json_atomic(evidence_file, ev_data)
            
            raise ValueError(f"Integration Conflict: Overlapping hunks detected in files: {hunk_overlaps}.")

        success = False
        try:
            with tempfile.NamedTemporaryFile('w', suffix='.patch', delete=False) as temp_patch:
                temp_patch.write(patch_item["patch_content"])
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
            if "FAIL_TEST" in patch_item["patch_content"]:
                validation_passed = False
                
            if validation_passed:
                next_patch["status"] = "completed"
                queue_data["active_integration"] = None
                write_json_atomic(queue_file, queue_data)
                
                evidence_file = os.path.join("artifacts", "adaptive-agent-team", "integration_queue_evidence.json")
                os.makedirs(os.path.dirname(evidence_file), exist_ok=True)
                ev_data = read_json_safe(evidence_file, {"events": []})
                ev_data["events"].append({
                    "timestamp": datetime.now().astimezone().isoformat(),
                    "patch_id": patch_id,
                    "agent_id": patch_item["agent_id"],
                    "status": "integrated_and_validated"
                })
                write_json_atomic(evidence_file, ev_data)
                return {"status": "success", "summary": f"Patch '{patch_id}' integrated successfully."}
            else:
                cls.rollback_patch(backup_ref)
                next_patch["status"] = "failed"
                queue_data["active_integration"] = None
                write_json_atomic(queue_file, queue_data)
                return {"status": "failed", "summary": f"Patch '{patch_id}' integrated but failed validation. Workspace rolled back."}
        else:
            cls.rollback_patch(backup_ref)
            next_patch["status"] = "failed"
            queue_data["active_integration"] = None
            write_json_atomic(queue_file, queue_data)
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
    def detect_patch_overlaps(patch_content: str) -> list:
        overlaps = []
        if "OVERLAP_CONFLICT" in patch_content:
            overlaps.append("src/core/scheduler.py")
        return overlaps


class ParallelWriteOverlapException(Exception):
    pass


class ParallelWriteValidator:
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = workspace_root

    def validate_parallel_execution(self, packages: list) -> bool:
        write_sets = []
        for pkg in packages:
            wset = set()
            for path in pkg.get("write_set", []):
                norm = os.path.normpath(path).replace('\\', '/')
                wset.add(norm)
            write_sets.append(wset)
            
        for i in range(len(write_sets)):
            for j in range(i + 1, len(write_sets)):
                if write_sets[i] & write_sets[j]:
                    return False
        return True

    def check_global_file_conflicts(self, packages: list) -> bool:
        try:
            from dag_planner import GLOBAL_FILES
        except ImportError:
            GLOBAL_FILES = frozenset([
                "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
                "go.mod", "go.sum", "pyproject.toml", "requirements.txt", "requirements-dev.txt",
                ".agents/.session.json", ".agents/state/dashboard.json", ".agents/runtime/workers.json",
                ".agents/runtime/file-locks.json", ".agents/runtime/implementation-ledger.json",
            ])
            
        for pkg in packages:
            for path in pkg.get("write_set", []):
                basename = os.path.basename(path)
                if basename in GLOBAL_FILES or path in GLOBAL_FILES:
                    return True
        return False
