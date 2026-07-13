import os
import sys
import re
import json
from datetime import datetime

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
        Detects the intent of the request.
        Returns one of: 'chat', 'feature_request', 'bug_fix', 'refactoring', 'migrations', 'architecture_changes', 'implementation_tasks'.
        """
        request_lower = request_text.lower()
        
        # 1. Check for bug fix keywords first
        bug_keywords = [r"\bfix\b", r"\bbug\b", r"\berror\b", r"\bissue\b", r"\btypo\b", r"\bmismatch\b", r"\bbroken\b", r"\bregression\b"]
        for kw in bug_keywords:
            if re.search(kw, request_lower):
                return "bug_fix"
                
        # 2. Check for migrations
        migration_keywords = [r"\bmigration\b", r"\bmigrate\b", r"\bdb schema\b", r"\bupgrade database\b"]
        for kw in migration_keywords:
            if re.search(kw, request_lower):
                return "migrations"
                
        # 3. Check for architecture changes
        arch_keywords = [r"\barchitecture\b", r"\barchitect\b", r"\badr\b", r"\bdesign pattern\b"]
        for kw in arch_keywords:
            if re.search(kw, request_lower):
                return "architecture_changes"
                
        # 4. Check for refactoring
        refactor_keywords = [r"\brefactor\b", r"\bclean\b", r"\bsimplify\b", r"\brewrite\b"]
        for kw in refactor_keywords:
            if re.search(kw, request_lower):
                return "refactoring"
                
        # 5. Check for implementation tasks
        task_keywords = [r"\btask\b", r"\bimplement code\b", r"\bwrite code\b", r"\bcoding\b"]
        for kw in task_keywords:
            if re.search(kw, request_lower):
                return "implementation_tasks"

        # 6. Check for feature request
        feat_keywords = [
            r"\badd\b", r"\bfeature\b", r"\bnew\b", r"\bimplement\b", 
            r"\bcreate\b", r"\bmodify\b", r"\bdelete\b", r"\btest\b", 
            r"\bbuild\b", r"\brelease\b", r"\bpublish\b", r"feat-\d+", r"quick-\d+"
        ]
        for kw in feat_keywords:
            if re.search(kw, request_lower):
                return "feature_request"
                
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

    def handle_request(self, request_text: str, source: str = None, session_id: str = None) -> dict:
        """
        Receives an engineering/chat request and routes accordingly.
        """
        intent = self.detect_intent(request_text)
        req_id = self.generate_request_id()
        
        # 1. Emit received event
        emit_event(
            "workflow.request.received",
            {"request_id": req_id, "intent": intent, "request_text": request_text, "source": source or "system", "session_id": session_id or "default_session"}
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
        if workflow_id == "FEAT-AUTO":
            # Auto-assign next FEAT ID
            max_num = 0
            for d in ["docs/brainstorming", "docs/designs", "docs/plans", "docs/verification"]:
                d_path = os.path.join(self.workspace_root, d)
                if os.path.exists(d_path):
                    for f in os.listdir(d_path):
                        match = re.search(r"FEAT-(\d+)", f)
                        if match:
                            num = int(match.group(1))
                            if num > max_num:
                                max_num = num
            feat_id = max_num + 1 if max_num > 0 else 313
            workflow_id = f"FEAT-{feat_id:03d}"

        # Load and update session context
        session = load_session()
        if not session:
            session = {}
            
        session["workflow_id"] = workflow_id
        session["work_item"] = {
            "id": workflow_id,
            "type": "QUICK" if "QUICK" in workflow_id else "FEAT",
            "title": request_text
        }
        session["execution_mode"] = "workflow"
        session["current_phase"] = "brainstorming"
        session["active_request_id"] = req_id
        if source:
            session["source"] = source
        if session_id:
            session["session_id"] = session_id
        
        save_session_atomic(session)
        
        # Set environment variables for current and child processes
        os.environ["AIWF_WORKFLOW_ID"] = workflow_id
        os.environ["AIWF_EXECUTION_MODE"] = "workflow"
        os.environ["AIWF_CURRENT_PHASE"] = "brainstorming"
        os.environ["AIWF_ACTIVE_REQUEST_ID"] = req_id
        if source:
            os.environ["AIWF_SOURCE"] = source
        if session_id:
            os.environ["AIWF_SESSION_ID"] = session_id

        # Update workflow.json
        state_dir = os.path.join(self.workspace_root, ".agents", "state")
        os.makedirs(state_dir, exist_ok=True)
        wf_path = os.path.join(state_dir, "workflow.json")
        wf_data = {
            "active_workflow": "standard-development",
            "active_phase": "brainstorming",
            "checkpoint": 1,
            "waiting_for": None,
            "work_item": {
                "id": workflow_id,
                "type": "FEAT",
                "title": request_text
            },
            "workflow_type": "standard-development",
            "parent_workflow_id": None,
            "suggested_next_skill": "brainstorming",
            "suggested_next_command": "brainstorm",
            "resume_state": {},
            "_metadata": {
                "generation": 1,
                "revision": 1,
                "writer_id": "system",
                "updated_at": datetime.now().astimezone().isoformat()
            }
        }
        with open(wf_path, "w", encoding="utf-8") as f:
            json.dump(wf_data, f, indent=2, ensure_ascii=False)

        # Update context.json
        ctx_path = os.path.join(state_dir, "context.json")
        ctx_data = {}
        if os.path.exists(ctx_path):
            try:
                with open(ctx_path, "r", encoding="utf-8") as f:
                    ctx_data = json.load(f)
            except Exception:
                pass
        ctx_data.update({
            "project_id": "ai-skill-framework",
            "workspace_path": ".",
            "permission_mode": "sandbox",
            "checkpoint": 1,
            "work_item_id": workflow_id,
            "workflow_id": workflow_id,
            "phase": "brainstorming",
            "execution_mode": "workflow",
            "autonomous_delivery": False,
            "progress_percentage": 0,
            "project_version": ctx_data.get("project_version", "6.15.1"),
            "source": source or ctx_data.get("source", "system"),
            "session_id": session_id or ctx_data.get("session_id", "default_session"),
            "authorization": {
                "authorization_id": f"AUTH-{workflow_id}",
                "project_id": "ai-skill-framework",
                "workspace_id": "workspace-id",
                "work_item_id": workflow_id,
                "workflow_id": f"WF-{workflow_id}",
                "permission_mode": "sandbox",
                "authorization_status": "active",
                "source": "system_default",
                "allowed_phases": ["brainstorming", "planning", "blueprint", "implementation", "debug", "verification", "release"],
                "allow_document_create": True,
                "allow_document_modify": True,
                "allow_source_create": True,
                "allow_source_modify": True,
                "allow_test_create": True,
                "allow_test_modify": True,
                "allow_runtime_state_modify": True,
                "allow_agent_spawn": True,
                "allow_agent_reassignment": True,
                "allow_parallel_execution": True,
                "allow_retry": True,
                "allow_replan": True,
                "allow_commit": True,
                "allow_merge": True,
                "allow_rebase": True,
                "allow_tag": True,
                "allow_push": True,
                "allow_release": True,
                "allow_publish": True,
                "allow_deploy": True,
                "stop_at": "release_approval",
                "expires_when": "release_approved_or_work_item_cancelled",
                "created_at": datetime.now().astimezone().isoformat(),
                "terminated_at": None,
                "max_retries_per_task": 3,
                "max_replans_per_work_item": 2,
                "max_agent_reassignments_per_task": 2
            }
        })
        with open(ctx_path, "w", encoding="utf-8") as f:
            json.dump(ctx_data, f, indent=2, ensure_ascii=False)

        # Update runtime.json
        rt_path = os.path.join(state_dir, "runtime.json")
        rt_data = {}
        if os.path.exists(rt_path):
            try:
                with open(rt_path, "r", encoding="utf-8") as f:
                    rt_data = json.load(f)
            except Exception:
                pass
        rt_data.update({
            "status": "in_progress",
            "current_skill": "brainstorming",
            "current_command": "brainstorm",
            "current_step": "Starting brainstorming...",
            "checkpoint": 1,
            "updated_at": datetime.now().astimezone().isoformat(),
            "suggestion_gate": {
                "active": True,
                "raw_request": request_text,
                "classification": intent,
                "recommended_skill": "brainstorming",
                "options": [],
                "status": "status"
            }
        })
        with open(rt_path, "w", encoding="utf-8") as f:
            json.dump(rt_data, f, indent=2, ensure_ascii=False)
        
        # Emit workflow started events
        emit_event("workflow.created", {"request_id": req_id, "workflow_id": workflow_id, "intent": intent, "status": "CREATED", "next_phase": "brainstorming", "source": source or "system", "session_id": session_id or "default_session"})
        emit_event("workflow.started", {"request_id": req_id, "workflow_id": workflow_id})
        emit_event("workflow.phase.started", {"request_id": req_id, "workflow_id": workflow_id, "phase": "brainstorming"})
        emit_event("skill.selected", {"request_id": req_id, "workflow_id": workflow_id, "skill": "brainstorming"})
        emit_event("skill.started", {"request_id": req_id, "workflow_id": workflow_id, "skill": "brainstorming"})
        
        # Forward request to Workflow Supervisor (simulated by returning next step info)
        return {
            "status": "ROUTED",
            "request_id": req_id,
            "intent": intent,
            "workflow_id": workflow_id,
            "workflow": "standard-development",
            "execution_mode": "workflow",
            "current_phase": "brainstorming",
            "next_skill": "brainstorming",
            "source": source or "system",
            "session_id": session_id or "default_session"
        }
