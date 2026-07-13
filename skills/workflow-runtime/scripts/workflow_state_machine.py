# workflow_state_machine.py
import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

class WorkflowStateError(Exception):
    pass

class WorkflowStateMachine:
    def __init__(self, workspace_root: str = ".") -> None:
        self.workspace_root = workspace_root
        self.state_dir = os.path.join(workspace_root, ".agents", "state")
        self.checkpoints_dir = os.path.join(self.state_dir, "checkpoints")
        os.makedirs(self.checkpoints_dir, exist_ok=True)
        
        self.events_file = os.path.join(self.state_dir, "workflow_events.jsonl")
        self.snapshot_file = os.path.join(self.state_dir, "workflow_snapshot.json")
        
        self.current_state = "Brainstorming"
        self.history: List[str] = []
        self.rollback_approved = False
        
        # Load existing snapshot if exists, otherwise save initial state
        if os.path.exists(self.snapshot_file):
            self.load_snapshot()
        else:
            self.save_snapshot()

    def load_snapshot(self) -> None:
        if os.path.exists(self.snapshot_file):
            try:
                with open(self.snapshot_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.current_state = data.get("current_state", "Brainstorming")
                    self.history = data.get("history", [])
                    self.rollback_approved = data.get("rollback_approved", False)
            except Exception:
                pass

    def save_snapshot(self) -> None:
        data = {
            "current_state": self.current_state,
            "history": self.history,
            "rollback_approved": self.rollback_approved,
            "updated_at": datetime.now().astimezone().isoformat()
        }
        with open(self.snapshot_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
        # Also write to checkpoint
        cp_file = os.path.join(self.checkpoints_dir, f"checkpoint_{self.current_state.lower()}.json")
        with open(cp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def append_event(self, topic: str, payload: Dict[str, Any]) -> None:
        event = {
            "topic": topic,
            "payload": payload,
            "timestamp": datetime.now().astimezone().isoformat()
        }
        with open(self.events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def transition_to(self, target_state: str) -> None:
        VALID_LIFECYCLE = [
            "Brainstorming", "Planning", "Gate1_PlanApproval", "ArchitectureReview", 
            "Blueprint", "Gate2_BlueprintApproval", "Implementation", "Debug", 
            "Verification", "Certification", "FinalReview", "ReleasePreparation", 
            "Gate3_ReleaseApproval", "ReleaseExecution", "PostReleaseValidation", 
            "ProductionMonitoring", "ProductionMaintenance", "RuntimeGovernance", 
            "ContinuousImprovement"
        ]
        
        if target_state not in VALID_LIFECYCLE:
            raise WorkflowStateError(f"Target state '{target_state}' is not a valid AIWF lifecycle state.")
            
        self.history.append(self.current_state)
        self.current_state = target_state
        self.save_snapshot()
        self.append_event("state.transition", {"from": self.history[-1], "to": self.current_state})

    def request_rollback(self, incident_details: str) -> str:
        # Create incident report
        report_content = f"""# Incident Report
- **Incident**: {incident_details}
- **Timestamp**: {datetime.now().astimezone().isoformat()}
- **Recommended Action**: ROLLBACK REQUIRED.
- **Rollback Status**: WAITING_FOR_APPROVAL
"""
        # Save incident details
        self.append_event("incident.detected", {"details": incident_details})
        return report_content

    def execute_rollback(self) -> bool:
        if not self.rollback_approved:
            raise WorkflowStateError("Rollback aborted. Explicit human Rollback Approval Gate is required.")
            
        self.append_event("rollback.executed", {"previous_state": self.current_state})
        self.current_state = "Implementation"  # Rollback transitions back to Implementation safe zone
        self.save_snapshot()
        return True
