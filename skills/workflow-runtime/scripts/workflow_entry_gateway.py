import os
import sys
import re

# Add parent directory to sys.path to resolve imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from event_logger import emit_event, get_logger
from session import load_session, save_session_atomic

class WorkflowEntryGateway:
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = workspace_root
        self.logger = get_logger(workspace_root)

    def detect_intent(self, request_text: str) -> str:
        """
        Detects if the request is Chat Mode or Engineering Mode.
        """
        # Search for engineering keywords
        eng_keywords = [
            r"\badd\b", r"\bfix\b", r"\bimplement\b", r"\brefactor\b", 
            r"\bcreate\b", r"\bmodify\b", r"\bdelete\b", r"\btest\b", 
            r"\bbuild\b", r"\brelease\b", r"\bpublish\b", r"feat-\d+", r"quick-\d+"
        ]
        
        request_lower = request_text.lower()
        for kw in eng_keywords:
            if re.search(kw, request_lower):
                return "engineering"
        return "chat"

    def generate_request_id(self) -> str:
        """
        Generates a sequential request ID by counting existing workflow.request.received events.
        """
        try:
            events = self.logger.read_all()
            req_count = sum(1 for e in events if e.get("event_type") == "workflow.request.received")
            return f"REQ-{req_count + 1:03d}"
        except Exception:
            import uuid
            return f"REQ-{uuid.uuid4().hex[:6].upper()}"

    def extract_workflow_id(self, request_text: str) -> str:
        """
        Extracts FEAT-xxx or QUICK-xxx from text, or returns FEAT-AUTO.
        """
        m = re.search(r"\b(feat-\d+|quick-\d+)\b", request_text, re.IGNORECASE)
        if m:
            return m.group(1).upper()
        return "FEAT-AUTO"

    def handle_request(self, request_text: str) -> dict:
        """
        Receives an engineering/chat request and routes accordingly.
        """
        intent = self.detect_intent(request_text)
        req_id = self.generate_request_id()
        
        # 1. Emit received event
        emit_event(
            "workflow.request.received",
            {"request_id": req_id, "intent": intent, "request_text": request_text}
        )
        
        if intent == "chat":
            return {
                "status": "BYPASS",
                "request_id": req_id,
                "intent": "chat",
                "message": "Chat request bypassed gateway and resolved directly by LLM."
            }
            
        # 2. Engineering mode workflow initialization
        workflow_id = self.extract_workflow_id(request_text)
        
        # Load and update session context
        session = load_session()
        if not session:
            session = {}
            
        session["workflow_id"] = workflow_id
        session["work_item"] = {
            "id": workflow_id,
            "type": "QUICK" if "QUICK" in workflow_id else "FEAT",
            "title": f"Work Item {workflow_id}"
        }
        session["execution_mode"] = "workflow"
        session["current_phase"] = "brainstorming"
        session["active_request_id"] = req_id
        
        save_session_atomic(session)
        
        # Set environment variables for current and child processes
        os.environ["AIWF_WORKFLOW_ID"] = workflow_id
        os.environ["AIWF_EXECUTION_MODE"] = "workflow"
        os.environ["AIWF_CURRENT_PHASE"] = "brainstorming"
        os.environ["AIWF_ACTIVE_REQUEST_ID"] = req_id
        
        # Emit workflow started events
        emit_event("workflow.started", {"request_id": req_id, "workflow_id": workflow_id})
        emit_event("workflow.phase.started", {"request_id": req_id, "workflow_id": workflow_id, "phase": "brainstorming"})
        emit_event("skill.selected", {"request_id": req_id, "workflow_id": workflow_id, "skill": "brainstorming"})
        
        # Forward request to Workflow Supervisor (simulated by returning next step info)
        return {
            "status": "ROUTED",
            "request_id": req_id,
            "intent": "engineering",
            "workflow_id": workflow_id,
            "execution_mode": "workflow",
            "current_phase": "brainstorming",
            "next_skill": "brainstorming"
        }
