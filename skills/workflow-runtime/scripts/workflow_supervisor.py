# workflow_supervisor.py
import os
import json
import time
from typing import Any, Dict, List, Optional
from workflow_state_machine import WorkflowStateMachine
from evidence_gate_engine import EvidenceGateEngine
from agent_dispatcher import AgentDispatcher

class WorkflowSupervisor:
    def __init__(
        self,
        workspace_root: str = ".",
        registry_path: Optional[str] = None
    ) -> None:
        self.workspace_root = workspace_root
        self.state_machine = WorkflowStateMachine(workspace_root=self.workspace_root)
        self.gate_engine = EvidenceGateEngine(workspace_root=self.workspace_root)
        self.dispatcher = AgentDispatcher(max_workers=3)
        
        # Load registry config
        if not registry_path:
            registry_path = os.path.join(self.workspace_root, ".agents", "config", "phase_registry.json")
        self.registry: Dict[str, Any] = {}
        if os.path.exists(registry_path):
            with open(registry_path, "r", encoding="utf-8") as f:
                self.registry = json.load(f)
                
        self.notifications: List[str] = []
        self.running = False
        self.completed = False

    def emit_notification(self, level: str, message: str) -> None:
        payload = f"[{level.upper()}] {message}"
        self.notifications.append(payload)
        self.state_machine.append_event("supervisor.notification", {"level": level, "message": message})

    def run_supervisor_step(self, evidence: Dict[str, Any]) -> str:
        current = self.state_machine.current_state
        
        # If workflow has advanced beyond continuous improvement, set completed
        if current == "ContinuousImprovement":
            self.completed = True
            self.emit_notification("info", "Workflow Execution Completed.")
            return current
            
        # Map current state key to registry (case-insensitive key parsing)
        registry_key = current.lower()
        if registry_key not in self.registry:
            # Check if this is a gate checkpoint
            if current.startswith("Gate"):
                # Evaluate approval evidence
                decision = self.gate_engine.evaluate_gate(current, evidence)
                if decision == "PASS":
                    # Transition to next stage depending on gate type
                    if current == "Gate1_PlanApproval":
                        self.state_machine.transition_to("ArchitectureReview")
                    elif current == "Gate2_BlueprintApproval":
                        self.state_machine.transition_to("Implementation")
                    elif current == "Gate3_ReleaseApproval":
                        self.state_machine.transition_to("ReleaseExecution")
                    self.emit_notification("info", f"Gate {current} approved. Advancing to next phase.")
                elif decision == "FAIL":
                    self.emit_notification("approval_required", f"Waiting Approval. Gate: {current}. Action required.")
                else:
                    self.emit_notification("info", f"Gate {current} blocked. Missing required files.")
                return self.state_machine.current_state
            return current

        phase_config = self.registry[registry_key]
        agent_name = phase_config.get("agent", "worker-agent")
        next_phase = phase_config.get("next", "ContinuousImprovement")
        
        # Dispatch the agent to execute
        def dummy_agent_task():
            time.sleep(0.01)
            
        dispatched = self.dispatcher.dispatch_agent(agent_name, dummy_agent_task)
        if not dispatched:
            self.emit_notification("info", f"Throttling agent {agent_name} spawn due to worker pool limit.")
            return current
            
        # If compilation/tests or checks are failed in evidence (retry logic)
        if registry_key == "implementation" and not evidence.get("compilation_success", True):
            self.emit_notification("info", f"Phase {current} execution failed compilation. Triggering retries.")
            return current
            
        # Auto advance intermediate phases
        self.state_machine.transition_to(next_phase)
        self.emit_notification("info", f"Phase {current} execution completed. Next phase: {next_phase}. No action required.")
        return self.state_machine.current_state
