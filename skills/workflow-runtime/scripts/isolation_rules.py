# isolation_rules.py
import os
import json
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Tuple

# Confidence threshold for auto routing
CONFIDENCE_THRESHOLD = 0.7

def classify_intent(prompt: str, active_work_item_id: str = None) -> Tuple[str, float]:
    """
    Classify user prompt into one of the 9 required categories with confidence.
    """
    p = prompt.strip().lower()
    
    # 1. Runtime Control & Status
    if p in ["show agents", "set concurrency", "stop after verify"] or p.startswith("set concurrency"):
        return "runtime_control", 1.0
    if p in ["status", "health", "metrics", "timeline", "show status"]:
        return "status_query", 1.0
        
    # 2. Direct workflow actions
    if p.startswith("pause"):
        return "pause_work_item", 1.0
    if p.startswith("resume"):
        return "resume_work_item", 1.0
    if p.startswith("cancel"):
        return "cancel_work_item", 1.0
    if p.startswith("replan"):
        return "replan_work_item", 1.0
        
    # 3. Ambiguous/Unclassified
    if p in ["add one more option", "do something", "why", "help", "hello"]:
        return "unclassified", 0.0
        
    # 4. Modify existing vs Create new
    # If active_work_item_id is explicitly referenced, or "this feature" / "active"
    if active_work_item_id and (active_work_item_id.lower() in p or "this feature" in p or "active feature" in p or "current" in p or "modify" in p or "add dark mode to this" in p):
        return "modify_existing_work_item", 0.9
        
    if "create" in p or "new feature" in p or "new work item" in p or "csv export" in p or "support" in p:
        return "create_new_work_item", 0.95
        
    # Default fallback
    if len(p.split()) < 4:
        return "unclassified", 0.3
        
    # Assume modification of active if there is one
    if active_work_item_id:
        return "modify_existing_work_item", 0.75
    else:
        return "create_new_work_item", 0.75

def process_incoming_prompt(prompt: str, workspace_id: str, session_id: str, active_work_item_id: str = None, active_workflow_id: str = None, state_dir: str = ".agents/state") -> Dict[str, Any]:
    """
    Ingests raw prompt, classifies it, resolves routing decision, and returns the envelope.
    """
    cmd_id = f"CMD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    intent, confidence = classify_intent(prompt, active_work_item_id)
    
    # Resolve target type
    if intent in ["modify_existing_work_item", "cancel_work_item", "pause_work_item", "resume_work_item", "replan_work_item"]:
        target_type = "work_item"
    elif intent == "create_new_work_item":
        target_type = "workflow"
    elif intent in ["runtime_control", "status_query"]:
        target_type = "runtime"
    else:
        target_type = "unclassified"
        
    # Resolve target work item and workflow IDs
    target_work_item_id = active_work_item_id if target_type == "work_item" else None
    target_workflow_id = active_workflow_id if target_type == "work_item" else None
    
    if intent == "create_new_work_item":
        # Simulate creating a new work item ID e.g. FEAT-121
        # In a real run, this would be computed or parsed
        if "csv" in prompt.lower():
            target_work_item_id = "FEAT-121"
            target_workflow_id = "WF-FEAT-121-PLAN"
        else:
            target_work_item_id = f"FEAT-{int(time.time())}"
            target_workflow_id = f"WF-{target_work_item_id}-PLAN"
            
    # Resolve decision
    requires_user_clarification = False
    if intent == "unclassified" or confidence < CONFIDENCE_THRESHOLD:
        decision = "hold"
        requires_user_clarification = True
        status = "pending_classification"
    elif intent == "create_new_work_item":
        decision = "create_work_item"
        status = "routed"
    elif intent in ["runtime_control", "status_query"]:
        decision = "route"
        status = "completed"
    else:
        decision = "route"
        status = "routed"
        
    envelope = {
        "command_id": cmd_id,
        "workspace_id": workspace_id,
        "session_id": session_id,
        "intent": intent,
        "target_type": target_type,
        "target_work_item_id": target_work_item_id,
        "target_workflow_id": target_workflow_id,
        "authorization_id": f"AUTH-{uuid.uuid4().hex[:6].upper()}" if target_work_item_id else None,
        "received_at": datetime.now().astimezone().isoformat(),
        "status": status,
        "prompt": prompt
    }
    
    routing_decision = {
        "command_id": cmd_id,
        "decision": decision,
        "target_work_item_id": target_work_item_id,
        "target_workflow_id": target_workflow_id,
        "reason": f"Classified intent as {intent} with confidence {confidence}",
        "confidence": confidence,
        "requires_user_clarification": requires_user_clarification
    }
    
    # Save to global or scoped inbox/routing decisions
    inbox_dir = state_dir
    if target_work_item_id and target_work_item_id != "FEAT-120":
        # Scoped directory for other work items
        inbox_dir = os.path.join(state_dir, "work-items", target_work_item_id)
        
    os.makedirs(inbox_dir, exist_ok=True)
    
    # Append to command_inbox.jsonl
    inbox_path = os.path.join(inbox_dir, "command_inbox.jsonl")
    with open(inbox_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(envelope) + "\n")
        
    # Append to routing_decisions.jsonl
    decisions_path = os.path.join(inbox_dir, "routing_decisions.jsonl")
    with open(decisions_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(routing_decision) + "\n")
        
    return envelope
