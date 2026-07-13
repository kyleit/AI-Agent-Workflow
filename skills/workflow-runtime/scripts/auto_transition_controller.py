# auto_transition_controller.py
from workflow_state_machine import WorkflowStateMachine
from evidence_gate_engine import EvidenceGateEngine
from typing import Any, Dict

class AutoTransitionController:
    def __init__(self, state_machine: WorkflowStateMachine, gate_engine: EvidenceGateEngine) -> None:
        self.state_machine = state_machine
        self.gate_engine = gate_engine

    def run_auto_lifecycle(self, evidence: Dict[str, Any]) -> str:
        """
        Runs the automatic phase transition controller sequentially.
        If in auto phases, transitions to the next phase as long as checks are healthy.
        """
        auto_phases = [
            "Implementation", "Debug", "Verification", "Certification", "FinalReview", "ReleasePreparation"
        ]
        
        current = self.state_machine.current_state
        if current not in auto_phases:
            return current

        # Transition validation steps
        if current == "Implementation":
            # Auto-advance to Debug if code files compiles (no critical compilation errors)
            if evidence.get("compilation_success", True):
                self.state_machine.transition_to("Debug")
                
        elif current == "Debug":
            # Auto-advance to Verification if unit tests pass
            if evidence.get("tests_passed", True):
                self.state_machine.transition_to("Verification")
                
        elif current == "Verification":
            # Auto-advance to Certification if static code checks and rules compliance pass
            if evidence.get("compliance_passed", True):
                self.state_machine.transition_to("Certification")
                
        elif current == "Certification":
            # Auto-advance to FinalReview if stress tests and fault injection checks pass
            if evidence.get("stress_passed", True) and not evidence.get("resource_leaks", False):
                self.state_machine.transition_to("FinalReview")
                
        elif current == "FinalReview":
            # Auto-advance to ReleasePreparation if final completeness review is healthy
            if evidence.get("completeness_passed", True):
                self.state_machine.transition_to("ReleasePreparation")

        return self.state_machine.current_state
