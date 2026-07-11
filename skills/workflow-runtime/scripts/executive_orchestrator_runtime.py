# executive_orchestrator_runtime.py
import os
import json
import time

class ExecutiveOrchestratorRuntimeModule:
    """
    FEAT-086: Executive Loop Controller
    Tracks session execution state machine and snapshot synchronization.
    Supports Continuous Sequential Execution with 4 modes: STEP, SPRINT, PROGRAM, OBJECTIVE.
    """
    def __init__(self, session_path: str = ".agents/runtime/context_snapshot.json"):
        self.session_path = session_path
        self.state = "STANDBY"
        self.max_iterations = 30
        self.iteration_count = 0
        self.active_goal = None
        self.history = []
        self.execution_mode = "PROGRAM"  # STEP | SPRINT | PROGRAM | OBJECTIVE

    def initialize(self) -> None:
        self.state = "INITIALIZING"
        self.load_snapshot()
        self.state = "ACTIVE"
        print(f"ExecutiveOrchestratorRuntimeModule initialized in active state. Session: {self.session_path}")

    def load_snapshot(self) -> bool:
        if os.path.exists(self.session_path):
            try:
                with open(self.session_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.state = data.get("state", "STANDBY")
                    self.iteration_count = data.get("iteration_count", 0)
                    self.active_goal = data.get("active_goal")
                    self.history = data.get("history", [])
                    self.execution_mode = data.get("execution_mode", "PROGRAM")
                return True
            except (json.JSONDecodeError, IOError):
                pass
        return False

    def save_snapshot(self) -> bool:
        os.makedirs(os.path.dirname(self.session_path), exist_ok=True)
        temp_path = self.session_path + ".tmp"
        try:
            snapshot = {
                "state": self.state,
                "iteration_count": self.iteration_count,
                "active_goal": self.active_goal,
                "history": self.history,
                "execution_mode": self.execution_mode,
                "timestamp": time.time()
            }
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, self.session_path)
            return True
        except IOError:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        return False

    def transition_to(self, new_state: str) -> None:
        valid_transitions = {
            "STANDBY": ["INITIALIZING"],
            "INITIALIZING": ["ACTIVE", "FAILED"],
            "ACTIVE": ["SUSPENDED", "COMPLETED", "FAILED"],
            "SUSPENDED": ["ACTIVE", "FAILED"],
            "COMPLETED": ["STANDBY"],
            "FAILED": ["STANDBY"]
        }
        if new_state in valid_transitions.get(self.state, []):
            self.state = new_state
            self.save_snapshot()
        else:
            raise ValueError(f"Invalid state transition from {self.state} to {new_state}")

    def should_continue_automatically(self, last_feat_status: str) -> bool:
        if last_feat_status != "PASS":
            return False
        if self.execution_mode in ["SPRINT", "PROGRAM", "OBJECTIVE"]:
            return True
        return False

