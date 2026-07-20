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
        Redirects routing to the new WorkflowCoordinator tick engine.
        """
        # Dynamic import of WorkflowCoordinator
        coord_path = os.path.abspath(os.path.join(self.workspace_root, ".agents", "skills", "workflow-coordinator", "scripts"))
        if coord_path not in sys.path:
            sys.path.append(coord_path)
            
        from coordinator import WorkflowCoordinator
        
        # Detect intent
        intent = self.detect_intent(request_text)
        req_id = self.generate_request_id()
        
        # Emit received event
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
            
        # Get/Assign work_item
        workflow_id = self.extract_workflow_id(request_text)
        if workflow_id == "FEAT-AUTO":
            max_num = 0
            for d in ["docs/brainstorming", "docs/blueprints", "docs/plans", "docs/verification"]:
                d_path = os.path.join(self.workspace_root, d)
                if os.path.exists(d_path):
                    # os.walk (not os.listdir) because a feature may use the multi-phase
                    # folder shape (docs/<stage>/<feature-slug>/master/FEAT-XXX_..._master_*.md),
                    # where the FEAT-XXX number is nested, not in the top-level directory name.
                    for _root, _dirs, files in os.walk(d_path):
                        for f in files:
                            match = re.search(r"FEAT-(\d+)", f)
                            if match:
                                num = int(match.group(1))
                                if num > max_num:
                                    max_num = num
            feat_id = max_num + 1 if max_num > 0 else 312
            workflow_id = f"FEAT-{feat_id:03d}"
            
        # Run coordinator tick
        coord = WorkflowCoordinator(self.workspace_root)
        coord_res = coord.run_tick(request_text, workflow_id)
        entry_phase = "brainstorming"
        
        # If success or safety gate violation, update runtime/context states
        # Emit events for backward compatibility
        emit_event("workflow.created", {"request_id": req_id, "workflow_id": workflow_id, "intent": intent, "status": "CREATED", "next_phase": entry_phase, "source": source or "system", "session_id": session_id or "default_session"})
        emit_event("workflow.started", {"request_id": req_id, "workflow_id": workflow_id})
        emit_event("workflow.phase.started", {"request_id": req_id, "workflow_id": workflow_id, "phase": entry_phase})
        
        # Update context.json & runtime.json for compatibility
        if self.workspace_root in ("", "."):
            state_dir = os.path.join(".agents", "state")
        else:
            state_dir = os.path.join(self.workspace_root, ".agents", "state")
        os.makedirs(state_dir, exist_ok=True)
        next_skill_info = coord_res.get("suggested_next_skill_metadata") or {}
        wf_path = os.path.join(state_dir, "workflow.json")
        wf_data = {}
        if os.path.exists(wf_path):
            try:
                with open(wf_path, "r", encoding="utf-8") as f:
                    wf_data = json.load(f)
            except Exception:
                pass
        wf_data.update({
            "active_workflow": workflow_id,
            "active_phase": entry_phase,
            "checkpoint": coord_res.get("checkpoint") or 1,
            "status": "in_progress",
            "work_item": {
                "type": "FEAT" if workflow_id.startswith("FEAT") else "QUICK",
                "id": workflow_id,
                "title": request_text
            },
            "suggested_next_skill": next_skill_info.get("skill") or "brainstorming",
            "suggested_next_command": next_skill_info.get("command") or "brainstorm"
        })
        with open(wf_path, "w", encoding="utf-8") as f:
            json.dump(wf_data, f, indent=2, ensure_ascii=False)
        
        ctx_path = os.path.join(state_dir, "context.json")
        ctx_data = {}
        if os.path.exists(ctx_path):
            try:
                with open(ctx_path, "r", encoding="utf-8") as f:
                    ctx_data = json.load(f)
            except Exception:
                pass
        ctx_data.update({
            "work_item_id": workflow_id,
            "workflow_id": workflow_id,
            "phase": entry_phase,
            "checkpoint": coord_res.get("checkpoint") or 1,
            "authorization": {
                "allowed_phases": ["discovery", "brainstorming", "planning", "blueprint", "implementation", "debug", "verification"]
            }
        })
        with open(ctx_path, "w", encoding="utf-8") as f:
            json.dump(ctx_data, f, indent=2, ensure_ascii=False)
            
        rt_path = os.path.join(state_dir, "runtime.json")
        rt_data = {}
        if os.path.exists(rt_path):
            try:
                with open(rt_path, "r", encoding="utf-8") as f:
                    rt_data = json.load(f)
            except Exception:
                pass
        rt_data.update({
            "status": "in_progress" if coord_res.get("status") == "success" else "waiting_input",
            "current_skill": next_skill_info.get("skill") or "brainstorming",
            "current_command": next_skill_info.get("command") or "brainstorm",
            "checkpoint": coord_res.get("checkpoint") or 1,
            "updated_at": datetime.now().astimezone().isoformat()
        })
        with open(rt_path, "w", encoding="utf-8") as f:
            json.dump(rt_data, f, indent=2, ensure_ascii=False)
            
        # Return gateway expected output format
        return {
            "status": "ROUTED",
            "request_id": req_id,
            "intent": intent,
            "workflow_id": workflow_id,
            "workflow": "standard-development",
            "execution_mode": "workflow",
            "current_phase": entry_phase,
            "next_skill": next_skill_info.get("skill") or "brainstorming",
            "source": source or "system",
            "session_id": session_id or "default_session"
        }
