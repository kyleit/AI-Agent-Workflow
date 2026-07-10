# heartbeat.py
import os
import sys

# Ensure sibling imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from checkpoint import get_checkpoint_name

def generate_heartbeat_string(session: dict) -> str:
    conv_id = session.get("conversation_id", "unknown")
    
    work_item = session.get("work_item", {})
    wi_str = "None"
    if work_item:
        wi_str = f"{work_item.get('id', 'N/A')} ({work_item.get('title', 'N/A')})"
        
    chk = session.get("checkpoint", 1)
    if isinstance(chk, str) and "Phase" in chk:
        phase_str = chk
    else:
        try:
            phase_str = f"Checkpoint {chk} ({get_checkpoint_name(int(chk))})"
        except (ValueError, TypeError):
            phase_str = str(chk)
            
    status = session.get("status", "unknown")
    updated = session.get("updated_at", "N/A")
    
    ctx = session.get("context_usage", {})
    pct = ctx.get("percentage", 0.0)
    tok = ctx.get("total_tokens", 0)
    lim = ctx.get("limit_tokens", 2000000)
    ctx_str = f"{pct}% ({tok:,} / {lim:,} tokens)"
    
    health = session.get("context_health", "healthy")
    
    lines = [
        "==================================================",
        "        AI Engineering Workflow Heartbeat        ",
        "==================================================",
        f"Conversation ID:   {conv_id}",
        f"Active Work Item:  {wi_str}",
        f"Current Phase:     {phase_str}",
        f"Execution Status:  {status}",
        f"Last Update:       {updated}",
        "--------------------------------------------------",
        f"Context Usage:     {ctx_str}",
        f"Context Health:    {health}",
        "=================================================="
    ]
    return "\n".join(lines)

def print_heartbeat(session: dict) -> None:
    print(generate_heartbeat_string(session))
