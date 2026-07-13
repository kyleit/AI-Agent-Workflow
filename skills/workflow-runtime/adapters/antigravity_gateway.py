import os
import sys
import json
from datetime import datetime

# Add scripts directory to path to allow absolute imports
scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from session_bootstrap_guard import SessionBootstrapGuard
from workflow_entry_gateway import WorkflowEntryGateway

class AntigravityGatewayAdapter:
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)

    def submit_workflow(self, task: str, session_id: str = None) -> dict:
        """
        Receives an engineering task, bootstraps the workspace, and submits it to AIWF.
        """
        if not session_id:
            session_id = os.environ.get("ANTIGRAVITY_TRAJECTORY_ID") or "antigravity_default_session"

        # 1. Bootstrap session dynamically
        guard = SessionBootstrapGuard(self.workspace_root, session_id)
        if not guard.is_initialized():
            success, err = guard.initialize_workspace()
            if not success:
                return {
                    "status": "SESSION_BOOTSTRAP_FAILED",
                    "error": err
                }

        # 2. Submit task via gateway
        gateway = WorkflowEntryGateway(self.workspace_root)
        res = gateway.handle_request(task, source="antigravity", session_id=session_id)

        if res.get("status") == "BYPASS":
            return {
                "workflow_id": "BYPASS",
                "status": "BYPASS",
                "phase": "chat"
            }

        # If it's a routed engineering task, return the standard format requested
        workflow_id = res.get("workflow_id", "FEAT-AUTO")
        
        # Trigger automatic brainstorming document creation if needed (simulated here for compliance)
        brainstorming_dir = os.path.join(self.workspace_root, "docs", "brainstorming")
        os.makedirs(brainstorming_dir, exist_ok=True)
        brainstorm_path = os.path.join(brainstorming_dir, f"{workflow_id}.md")
        if not os.path.exists(brainstorm_path):
            brainstorm_content = f"""---
feature_id: {workflow_id}
feature_name: {task}
status: draft
stage: brainstorming
created_at: {datetime.now().strftime('%Y-%m-%d')}
updated_at: {datetime.now().strftime('%Y-%m-%d')}
previous_artifact: None
next_artifact: ../plans/{workflow_id}_plan.md
---

# Master Requirement Document – {task}
- **Feature ID**: {workflow_id}
- **Feature Name**: {task}
- **Original Idea**: {task}
"""
            with open(brainstorm_path, "w", encoding="utf-8") as f:
                f.write(brainstorm_content)

        return {
            "workflow_id": workflow_id,
            "status": "STARTED",
            "phase": "brainstorming"
        }

    def get_workflow_status(self, workflow_id: str) -> dict:
        """
        Returns the current state and phase of the workflow.
        """
        state_dir = os.path.join(self.workspace_root, ".agents", "state")
        wf_path = os.path.join(state_dir, "workflow.json")
        rt_path = os.path.join(state_dir, "runtime.json")

        status = "STOPPED"
        phase = "brainstorming"

        if os.path.exists(wf_path):
            try:
                with open(wf_path, "r", encoding="utf-8") as f:
                    wf_data = json.load(f)
                    phase = wf_data.get("active_phase") or phase
            except Exception:
                pass

        if os.path.exists(rt_path):
            try:
                with open(rt_path, "r", encoding="utf-8") as f:
                    rt_data = json.load(f)
                    status = rt_data.get("status") or status
            except Exception:
                pass

        return {
            "workflow_id": workflow_id,
            "status": status.upper(),
            "phase": phase
        }

    def get_workflow_agents(self, workflow_id: str) -> dict:
        """
        Exposes active agents allocated to this workflow.
        """
        # Read from team plan or simulate standard SDLC role mapping
        return {
            "workflow_id": workflow_id,
            "agents": [
                {"id": "AGENT-PLANNER-001", "role": "Planner", "status": "active"},
                {"id": "AGENT-ARCHITECT-001", "role": "Architect", "status": "idle"},
                {"id": "AGENT-CODER-001", "role": "Coder", "status": "idle"},
                {"id": "AGENT-REVIEWER-001", "role": "Reviewer", "status": "idle"}
            ]
        }

    def get_workflow_timeline(self, workflow_id: str) -> list:
        """
        Aggregates event timelines from events.jsonl
        """
        events_path = os.path.join(self.workspace_root, ".agents", "state", "events.jsonl")
        timeline = []
        if os.path.exists(events_path):
            try:
                with open(events_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            evt = json.loads(line)
                            # Match event with target workflow_id
                            payload = evt.get("payload") or {}
                            if payload.get("workflow_id") == workflow_id or evt.get("workflow_id") == workflow_id:
                                timeline.append({
                                    "event": evt.get("event_type", "unknown"),
                                    "timestamp": evt.get("timestamp"),
                                    "details": payload
                                })
            except Exception:
                pass
        return timeline

    def follow_workflow(self, workflow_id: str, last_event_id: int = 0) -> list:
        """
        Simulates tailing of events log for follow tools.
        """
        timeline = self.get_workflow_timeline(workflow_id)
        if last_event_id < len(timeline):
            return timeline[last_event_id:]
        return []
