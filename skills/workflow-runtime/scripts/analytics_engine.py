# analytics_engine.py
import os
import sys
import json
import re
from datetime import datetime

# Ensure sibling imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from context import estimate_context_usage

HISTORY_FILE = os.path.join(".agents", "runtime", "analytics_history.json")

def clean_path(p: str, workspace_root: str) -> str:
    if not p:
        return ""
    p = p.strip('"\'')
    # If it is a file:// URI, strip the prefix
    if p.startswith("file://"):
        p = p[7:]
    abs_ws = os.path.abspath(workspace_root)
    # Check if the path is absolute or relative
    if not os.path.isabs(p):
        p = os.path.join(abs_ws, p)
    abs_p = os.path.abspath(p)
    if abs_p.startswith(abs_ws):
        return os.path.relpath(abs_p, abs_ws)
    return p

def detect_duplicate_reads(conversation_id: str, workspace_root: str = ".") -> tuple[int, float, list]:
    home = os.path.expanduser("~")
    brain_dir = os.path.join(home, ".gemini", "antigravity-ide", "brain")
    if not conversation_id or not os.path.exists(brain_dir):
        return 0, 0.0, []
    
    log_path = os.path.join(brain_dir, conversation_id, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(log_path):
        return 0, 0.0, []
    
    file_counts = {}
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line_str in f:
                if not line_str.strip():
                    continue
                try:
                    line = json.loads(line_str)
                except json.JSONDecodeError:
                    continue
                
                tool_calls = line.get("tool_calls", [])
                # Also check tool_calls nested inside prompt responses if any
                if not tool_calls and isinstance(line.get("content"), dict):
                    tool_calls = line["content"].get("tool_calls", [])
                
                if tool_calls:
                    for tc in tool_calls:
                        name = tc.get("name")
                        args = tc.get("args", {})
                        path_val = None
                        if name == "view_file":
                            path_val = args.get("AbsolutePath")
                        elif name == "read_resource":
                            path_val = args.get("Uri")
                        
                        if path_val:
                            rel_p = clean_path(path_val, workspace_root)
                            if rel_p:
                                file_counts[rel_p] = file_counts.get(rel_p, 0) + 1
    except Exception:
        pass
        
    duplicate_read_count = 0
    estimated_savings_usd = 0.0
    duplicate_reads_list = []
    
    for path_val, count in file_counts.items():
        if count > 1:
            try:
                sz = os.path.getsize(os.path.join(workspace_root, path_val))
            except Exception:
                sz = 0
            duplicate_read_count += (count - 1)
            tokens = int(sz / 3)
            savings = (count - 1) * tokens * 1.25 / 1000000  # standard Gemini token pricing
            estimated_savings_usd += savings
            duplicate_reads_list.append({
                "file": path_val,
                "count": count,
                "size_bytes": sz
            })
            
    return duplicate_read_count, round(estimated_savings_usd, 4), duplicate_reads_list

def load_history() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_history(history: list) -> None:
    dir_name = os.path.dirname(HISTORY_FILE)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    
    tmp_path = HISTORY_FILE + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
        os.replace(tmp_path, HISTORY_FILE)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def update_analytics(session_data: dict, workspace_root: str = ".") -> dict:
    conv_id = session_data.get("conversation_id", "")
    
    # 1. Estimate current usage
    usage = estimate_context_usage()
    
    active_tokens = usage.get("active_tokens", 0)
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cache_tokens = usage.get("cache_tokens", 0)
    thinking_tokens = usage.get("thinking_tokens", 0)
    total_tokens = usage.get("total_tokens", 0)
    limit_tokens = usage.get("limit_tokens", 2000000)
    percentage = usage.get("percentage", 0.0)
    estimated_cost_usd = usage.get("estimated_cost_usd", 0.0)
    
    # 2. Detect duplicate reads
    dup_count, dup_savings, dup_list = detect_duplicate_reads(conv_id, workspace_root)
    
    # 3. History logging
    history = load_history()
    if history:
        req_num = history[-1].get("request_number", len(history)) + 1
    else:
        req_num = usage.get("request_count", 0) or 1
    
    new_entry = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "request_number": req_num,
        "active_tokens": active_tokens,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_tokens": cache_tokens,
        "thinking_tokens": thinking_tokens,
        "estimated_cost_usd": estimated_cost_usd,
        "duplicate_reads_detected": dup_list
    }
    
    history.append(new_entry)
    # cap history at 100 entries to prevent bloat
    if len(history) > 100:
        history = history[-100:]
    save_history(history)
    
    # 4. Compute growth rate and efficiency
    cache_hit_ratio = round(cache_tokens / max(1, input_tokens), 2)
    input_to_output_ratio = round(input_tokens / max(1, output_tokens), 2)
    
    growth_speed = 0.0
    if len(history) > 1:
        total_growth = history[-1]["active_tokens"] - history[0]["active_tokens"]
        growth_speed = round(total_growth / max(1, len(history) - 1), 2)
        
    efficiency = {
        "cache_hit_ratio": cache_hit_ratio,
        "input_to_output_ratio": input_to_output_ratio,
        "growth_speed_tokens_per_request": growth_speed,
        "duplicate_read_count": dup_count,
        "estimated_savings_usd": dup_savings
    }
    
    # 5. Build structured token output
    analytics_payload = {
        "total_tokens": active_tokens,
        "limit_tokens": limit_tokens,
        "percentage": percentage,
        "active_context": {
            "total_tokens": active_tokens,
            "limit_tokens": limit_tokens,
            "percentage": percentage,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_tokens": cache_tokens,
            "thinking_tokens": thinking_tokens
        },
        "accumulated_usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_tokens": cache_tokens,
            "thinking_tokens": thinking_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": estimated_cost_usd,
            "request_count": req_num
        },
        "efficiency": efficiency
    }
    
    return analytics_payload
