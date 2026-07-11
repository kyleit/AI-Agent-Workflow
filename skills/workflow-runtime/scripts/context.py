# context.py
import os
import sys
import json
import re
from datetime import datetime

# Ensure sibling imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from session import load_session

LIMIT_TOKENS = 2000000
BRAIN_ROOT = os.path.expanduser("~/.gemini/antigravity-ide/brain")

def parse_transcript(log_file: str) -> dict:
    if not os.path.exists(log_file):
        return {}
    
    provider = "estimate"
    model = "auto"
    if "ANTIGRAVITY_AGENT" in os.environ:
        provider = "antigravity"
        model = "auto"
    
    total_input_chars = 0
    total_output_chars = 0
    thinking_chars = 0
    current_history_chars = 0
    request_count = 0
    
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line_str in f:
                if not line_str.strip():
                    continue
                try:
                    line = json.loads(line_str)
                except json.JSONDecodeError:
                    continue
                
                content = line.get("content", "")
                
                # Check for settings changes to auto-detect model/provider
                if line.get("type") == "USER_INPUT" and content and "Model Selection" in content:
                    match = re.search(r"Model Selection` from \S+ to ([^\.]+)", content)
                    if match:
                        model_name = match.group(1).strip()
                        model = model_name
                        if "Gemini" in model_name:
                            provider = "antigravity"
                        elif "Claude" in model_name:
                            provider = "claude-code"
                        elif "GPT" in model_name:
                            provider = "openai"
                
                source = line.get("source")
                type_ = line.get("type")
                if source == "MODEL" and type_ in ["PLANNER_RESPONSE", "ASK_QUESTION"]:
                    # This turn's input is the context compiled so far
                    total_input_chars += current_history_chars
                    request_count += 1
                    
                    # Calculate this turn's output characters
                    thinking = line.get("thinking", "")
                    if thinking:
                        thinking_chars += len(thinking)
                        
                    output_len = len(content) + len(thinking)
                    tool_calls = line.get("tool_calls", [])
                    if tool_calls:
                        output_len += len(json.dumps(tool_calls))
                        
                    total_output_chars += output_len
                    
                    # Accumulate model response to history
                    current_history_chars += output_len
                else:
                    # USER or SYSTEM message
                    current_history_chars += len(content)
                    
        input_tokens = int(total_input_chars / 3)
        output_tokens = int(total_output_chars / 3)
        thinking_tokens = int(thinking_chars / 3)
        cache_tokens = int(input_tokens * 0.15) # 15% cache hits
        total_tokens = input_tokens + output_tokens
        
        # Active context size at the end of the conversation
        active_tokens = int(current_history_chars / 3)
        
        # Calculate cost based on detected provider/model
        if provider == "antigravity":
            uncached = max(0, input_tokens - cache_tokens)
            cost = (uncached * 1.25 / 1000000) + (cache_tokens * 0.3125 / 1000000) + (output_tokens * 3.75 / 1000000)
        elif provider == "claude-code":
            cost = (input_tokens * 3.00 / 1000000) + (output_tokens * 15.00 / 1000000)
        elif provider == "openai":
            cost = (input_tokens * 5.00 / 1000000) + (output_tokens * 15.00 / 1000000)
        else:
            cost = (input_tokens * 1.50 / 1000000) + (output_tokens * 5.00 / 1000000)
            
        return {
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_tokens": cache_tokens,
            "thinking_tokens": thinking_tokens,
            "total_tokens": total_tokens,
            "active_tokens": active_tokens,
            "limit_tokens": LIMIT_TOKENS,
            "percentage": round((active_tokens / LIMIT_TOKENS) * 100, 2),
            "estimated_cost_usd": round(cost, 4),
            "request_count": request_count,
            "accuracy": "estimated",
            "updated_at": datetime.now().astimezone().isoformat()
        }
    except Exception:
        pass
        
    return {}

def get_fallback_usage(session: dict, default_provider: str) -> dict:
    checkpoint = session.get("checkpoint", 1)
    percentage = min(checkpoint * 8.5, 95.0)
    active_tokens = int((percentage / 100) * LIMIT_TOKENS)
    total_tokens = active_tokens
    
    input_tokens = int(total_tokens * 0.98)
    output_tokens = int(total_tokens * 0.02)
    cache_tokens = int(total_tokens * 0.15)
    thinking_tokens = int(total_tokens * 0.005)
    
    return {
        "provider": default_provider,
        "model": "auto",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_tokens": cache_tokens,
        "thinking_tokens": thinking_tokens,
        "active_tokens": active_tokens,
        "total_tokens": total_tokens,
        "limit_tokens": LIMIT_TOKENS,
        "percentage": round(percentage, 2),
        "estimated_cost_usd": round(total_tokens * 1.5 / 1000000, 4),
        "accuracy": "estimated",
        "updated_at": datetime.now().astimezone().isoformat()
    }

def detect_active_conversation_id() -> str:
    metadata_str = os.environ.get("ANTIGRAVITY_SOURCE_METADATA")
    if metadata_str:
        try:
            metadata = json.loads(metadata_str)
            if isinstance(metadata, dict):
                tool_data = metadata.get("tool")
                if isinstance(tool_data, dict):
                    env_conv_id = tool_data.get("conversationId")
                    if isinstance(env_conv_id, str) and env_conv_id:
                        return env_conv_id
        except Exception:
            pass
    return ""

def sync_conversation_id(session: dict) -> bool:
    active_id = detect_active_conversation_id()
    if not active_id:
        return False
    old_id = session.get("conversation_id")
    if old_id != active_id:
        session["conversation_id"] = active_id
        log_msg = f"Conversation changed: {old_id} -> {active_id}. Context usage recalculated."
        if "current_logs" not in session or not isinstance(session["current_logs"], list):
            session["current_logs"] = []
        session["current_logs"].append(log_msg)
        session["updated_at"] = datetime.now().astimezone().isoformat()
        return True
    return False

def refresh_context_usage_for_active_conversation(session: dict) -> dict:
    sync_conversation_id(session)
    conv_id = session.get("conversation_id")
    if conv_id:
        log_file = os.path.join(BRAIN_ROOT, conv_id, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(log_file):
            warn_msg = f"Warning: Transcript file not found for conversation {conv_id}. Falling back to zero context usage."
            if "current_logs" not in session or not isinstance(session["current_logs"], list):
                session["current_logs"] = []
            if warn_msg not in session["current_logs"]:
                session["current_logs"].append(warn_msg)
    usage = estimate_context_usage(conv_id)
    session["context_usage"] = {
        "total_tokens": usage.get("active_tokens", 0),
        "limit_tokens": usage.get("limit_tokens", 2000000),
        "percentage": usage.get("percentage", 0.0)
    }
    return usage

def estimate_context_usage(conversation_id: str = None) -> dict:
    if conversation_id is None:
        session = load_session()
        conv_id = session.get("conversation_id")
    else:
        conv_id = conversation_id
    
    default_provider = "antigravity" if "ANTIGRAVITY_AGENT" in os.environ else "estimate"
    
    if not conv_id:
        return get_fallback_usage({}, default_provider)
        
    log_file = os.path.join(BRAIN_ROOT, conv_id, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(log_file):
        # Case C: Missing transcript. Fall back to safe zero/unknown values.
        return {
            "provider": default_provider,
            "model": "auto",
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_tokens": 0,
            "thinking_tokens": 0,
            "active_tokens": 0,
            "total_tokens": 0,
            "limit_tokens": LIMIT_TOKENS,
            "percentage": 0.0,
            "estimated_cost_usd": 0.0,
            "accuracy": "unknown",
            "updated_at": datetime.now().astimezone().isoformat()
        }
        
    parsed = parse_transcript(log_file)
    if parsed:
        return parsed
        
    session_fallback = load_session() if conversation_id is None else {"conversation_id": conv_id}
    return get_fallback_usage(session_fallback, default_provider)
def sync_request_history(conversation_id: str, project_id: str, workspace_root: str = ".") -> None:
    if not conversation_id or os.environ.get("AIWF_RUNTIME_MODE") == "test-isolated" or "PYTEST_CURRENT_TEST" in os.environ:
        return
        
    log_file = os.path.join(BRAIN_ROOT, conversation_id, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(log_file):
        return
        
    import sqlite3
    from db import PROJECT_DB
    
    # 1. Load sync state
    last_bytes = 0
    current_history_chars = 0
    tool_call_count = 0
    workspace_read_count = 0
    memory_hit_count = 0
    rag_hit_count = 0
    conn = None
    
    try:
        conn = sqlite3.connect(PROJECT_DB)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transcript_sync_state (
                conversation_id TEXT PRIMARY KEY,
                last_bytes INTEGER NOT NULL,
                last_history_chars INTEGER NOT NULL,
                tool_call_count INTEGER NOT NULL,
                workspace_read_count INTEGER NOT NULL,
                memory_hit_count INTEGER NOT NULL,
                rag_hit_count INTEGER NOT NULL
            )
        """)
        cursor.execute("""
            SELECT last_bytes, last_history_chars, tool_call_count, workspace_read_count, memory_hit_count, rag_hit_count
            FROM transcript_sync_state WHERE conversation_id = ?
        """, (conversation_id,))
        row = cursor.fetchone()
        if row:
            last_bytes, current_history_chars, tool_call_count, workspace_read_count, memory_hit_count, rag_hit_count = row
    except Exception:
        pass
        
    try:
        file_size = os.path.getsize(log_file)
    except Exception:
        if conn:
            try: conn.close()
            except Exception: pass
        return
        
    if file_size < last_bytes:
        last_bytes = 0
        current_history_chars = 0
        tool_call_count = 0
        workspace_read_count = 0
        memory_hit_count = 0
        rag_hit_count = 0
        
    if file_size == last_bytes:
        if conn:
            try: conn.close()
            except Exception: pass
        return
        
    # Load last request info from database for delta diffs
    prev_breakdown = None
    prev_request_id = None
    if conn:
        try:
            cursor.execute("""
                SELECT request_id, context_breakdown_json 
                FROM provider_requests 
                WHERE conversation_id = ? 
                ORDER BY rowid DESC LIMIT 1
            """, (conversation_id,))
            row = cursor.fetchone()
            if row:
                prev_request_id, cb_json_str = row
                try:
                    prev_breakdown = json.loads(cb_json_str)
                except Exception:
                    prev_breakdown = None
        except Exception:
            pass
        
    session = load_session()
    checkpoint = session.get("checkpoint", 1) if session else 1
    skill = session.get("current_skill", "unknown") if session else "unknown"
    
    status = "success"
    error_summary = None
    provider = "antigravity"
    model = "auto"
    
    try:
        new_bytes_processed = 0
        with open(log_file, "rb") as f_bin:
            if last_bytes > 0:
                f_bin.seek(last_bytes)
            new_data = f_bin.read()
            new_bytes_processed = len(new_data)
            
        lines = new_data.decode("utf-8", errors="replace").splitlines()
        for line_str in lines:
            if not line_str.strip():
                continue
            try:
                line = json.loads(line_str)
            except json.JSONDecodeError:
                continue
                
            content = line.get("content", "")
            source = line.get("source")
            type_ = line.get("type")
            step_idx = line.get("step_index")
            
            if type_ == "USER_INPUT" and content and "Model Selection" in content:
                match = re.search(r"Model Selection` from \S+ to ([^\.]+)", content)
                if match:
                    model_name = match.group(1).strip()
                    model = model_name
                    if "Gemini" in model_name:
                        provider = "antigravity"
                    elif "Claude" in model_name:
                        provider = "claude-code"
                    elif "GPT" in model_name:
                        provider = "openai"
            
            if line.get("status") == "ERROR":
                status = "failed"
                error_summary = content[:200] if content else "Unknown execution error"
                
            if source == "SYSTEM" or source == "USER":
                if type_ in ["VIEW_FILE", "READ_FILE", "GREP_SEARCH"]:
                    workspace_read_count += 1
                if type_ in ["mcp", "command"]:
                    tool_call_count += 1
                if "rag" in type_.lower() or "qdrant" in content.lower():
                    rag_hit_count += 1
                if "memory" in type_.lower():
                    memory_hit_count += 1
                    
            if source == "MODEL" and type_ in ["PLANNER_RESPONSE", "ASK_QUESTION"]:
                request_id = f"{conversation_id}_{step_idx}"
                input_tokens = int(current_history_chars / 3)
                
                thinking = line.get("thinking", "")
                output_len = len(content) + len(thinking)
                tool_calls = line.get("tool_calls", [])
                if tool_calls:
                    output_len += len(json.dumps(tool_calls))
                    tool_call_count += len(tool_calls)
                    
                output_tokens = int(output_len / 3)
                thinking_tokens = int(len(thinking) / 3)
                cache_tokens = int(input_tokens * 0.15)
                total_tokens = input_tokens + output_tokens
                
                duration = max(2.5, min(60.0, output_tokens * 0.05 + 1.5))
                
                if provider == "antigravity":
                    uncached = max(0, input_tokens - cache_tokens)
                    cost = (uncached * 1.25 / 1000000) + (cache_tokens * 0.3125 / 1000000) + (output_tokens * 3.75 / 1000000)
                elif provider == "claude-code":
                    cost = (input_tokens * 3.00 / 1000000) + (output_tokens * 15.00 / 1000000)
                elif provider == "openai":
                    cost = (input_tokens * 5.00 / 1000000) + (output_tokens * 15.00 / 1000000)
                else:
                    cost = (input_tokens * 1.50 / 1000000) + (output_tokens * 5.00 / 1000000)
                    
                pct = (input_tokens / LIMIT_TOKENS) * 100.0
                
                cb_data = {
                    "request_id": request_id,
                    "conversation_id": conversation_id,
                    "total_tokens": input_tokens,
                    "breakdown": [
                        { "category": "Conversation History", "tokens": int(input_tokens * 0.6), "percentage": 60.0, "details": [] },
                        { "category": "AI_RULES", "tokens": int(input_tokens * 0.25), "percentage": 25.0, "details": [] },
                        { "category": "AGENTS", "tokens": int(input_tokens * 0.1), "percentage": 10.0, "details": [] },
                        { "category": "Other runtime context", "tokens": int(input_tokens * 0.05), "percentage": 5.0, "details": [] }
                    ]
                }
                
                request_record = {
                    "request_id": request_id,
                    "workflow_id": conversation_id,
                    "conversation_id": conversation_id,
                    "project_id": project_id,
                    "skill_name": skill,
                    "command_name": session.get("current_command", "unknown") if session else "unknown",
                    "model": model,
                    "provider": provider,
                    "timestamp": line.get("created_at") or datetime.now().astimezone().isoformat(),
                    "duration": duration,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cache_tokens": cache_tokens,
                    "thinking_tokens": thinking_tokens,
                    "total_tokens": total_tokens,
                    "cost_usd": round(cost, 6),
                    "tool_call_count": tool_call_count,
                    "workspace_read_count": workspace_read_count,
                    "memory_hit_count": memory_hit_count,
                    "rag_hit_count": rag_hit_count,
                    "context_usage_percentage": round(pct, 2),
                    "context_limit_tokens": LIMIT_TOKENS,
                    "context_breakdown_json": cb_data,
                    "status": status,
                    "error_summary": error_summary
                }
                
                from db import save_provider_request
                save_provider_request(request_record)
                
                if prev_breakdown is not None:
                    from diff_engine import calculate_diff
                    from db import save_token_diff
                    diff_data = calculate_diff(prev_breakdown, cb_data)
                    diff_data["request_id"] = request_id
                    diff_data["prev_request_id"] = prev_request_id
                    diff_data["conversation_id"] = conversation_id
                    diff_data["timestamp"] = request_record["timestamp"]
                    save_token_diff(diff_data)
                    
                from db import save_timeline_event
                timeline_record = {
                    "timestamp": request_record["timestamp"],
                    "conversation_id": conversation_id,
                    "event_type": "Provider request",
                    "checkpoint": checkpoint,
                    "skill": skill,
                    "request_id": request_id,
                    "active_context": request_record["total_tokens"],
                    "context_delta": diff_data["net_change_tokens"] if (prev_breakdown is not None) else request_record["total_tokens"],
                    "input_tokens": request_record["input_tokens"],
                    "output_tokens": request_record["output_tokens"],
                    "cost": request_record["cost_usd"],
                    "duration": request_record["duration"],
                    "details": {
                        "tool_calls": tool_call_count,
                        "workspace_reads": workspace_read_count,
                        "memory_hits": memory_hit_count,
                        "rag_hits": rag_hit_count
                    }
                }
                save_timeline_event(timeline_record)
                    
                prev_breakdown = cb_data
                prev_request_id = request_id
                
                tool_call_count = 0
                workspace_read_count = 0
                memory_hit_count = 0
                rag_hit_count = 0
                status = "success"
                error_summary = None
                
                current_history_chars += output_len
            else:
                current_history_chars += len(content)
                
        # 4. Save sync state
        if conn:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO transcript_sync_state 
                    (conversation_id, last_bytes, last_history_chars, tool_call_count, workspace_read_count, memory_hit_count, rag_hit_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (conversation_id, last_bytes + new_bytes_processed, current_history_chars, tool_call_count, workspace_read_count, memory_hit_count, rag_hit_count))
                conn.commit()
                conn.close()
                conn = None
            except Exception:
                pass
                
        # 5. Generate and save insights + recommendations
        from db import get_provider_requests, save_insight_snapshot, save_recommendations
        from insights_engine import calculate_efficiency_score, generate_recommendations
        
        reqs = get_provider_requests({"conversation_id": conversation_id}, sort_by="timestamp", desc=False)
        if reqs:
            eff_score = calculate_efficiency_score(reqs)
            
            avg_tokens = int(sum(r["total_tokens"] for r in reqs) / len(reqs))
            avg_cost = sum(r["cost_usd"] for r in reqs) / len(reqs)
            
            growth_trend = "stable"
            if len(reqs) > 1:
                first = reqs[0]["total_tokens"]
                last = reqs[-1]["total_tokens"]
                diff = last - first
                if diff > LIMIT_TOKENS * 0.1:
                    growth_trend = "growing"
                elif diff < -LIMIT_TOKENS * 0.1:
                    growth_trend = "shrinking"
                    
            insight_data = {
                "request_count": len(reqs),
                "total_cost": round(sum(r["cost_usd"] for r in reqs), 4),
                "total_tokens": sum(r["total_tokens"] for r in reqs)
            }
            snapshot = {
                "timestamp": datetime.now().astimezone().isoformat(),
                "conversation_id": conversation_id,
                "efficiency_score": eff_score,
                "avg_tokens": avg_tokens,
                "avg_cost": round(avg_cost, 6),
                "growth_trend": growth_trend,
                "insight_data_json": json.dumps(insight_data)
            }
            save_insight_snapshot(snapshot)
            
            recs = generate_recommendations(reqs, conversation_id)
            if recs:
                save_recommendations(recs)
    except Exception as e:
        print(f"Error parsing request history: {e}", file=sys.stderr)
        if conn:
            try: conn.close()
            except Exception: pass
