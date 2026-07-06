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
BRAIN_ROOT = r"C:\Users\Kyle\.gemini\antigravity-ide\brain"

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
                if content and "Model Selection" in content:
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
                if source == "MODEL":
                    # This turn's input is the context compiled so far
                    total_input_chars += current_history_chars
                    
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
            cost = (input_tokens * 1.25 / 1000000) + (output_tokens * 3.75 / 1000000)
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
            "accuracy": "estimated",
            "updated_at": datetime.now().astimezone().isoformat()
        }
    except Exception:
        pass
        
    return {}

def estimate_context_usage() -> dict:
    session = load_session()
    conv_id = session.get("conversation_id")
    
    default_provider = "antigravity" if "ANTIGRAVITY_AGENT" in os.environ else "estimate"
    
    if not conv_id:
        return {
            "provider": default_provider,
            "model": "auto",
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_tokens": 0,
            "thinking_tokens": 0,
            "total_tokens": 0,
            "active_tokens": 0,
            "limit_tokens": LIMIT_TOKENS,
            "percentage": 0.0,
            "estimated_cost_usd": 0.0,
            "accuracy": "estimated",
            "updated_at": datetime.now().astimezone().isoformat()
        }
        
    log_file = os.path.join(BRAIN_ROOT, conv_id, ".system_generated", "logs", "transcript.jsonl")
    parsed = parse_transcript(log_file)
    if parsed:
        return parsed
        
    return {
        "provider": default_provider,
        "model": "auto",
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_tokens": 0,
        "thinking_tokens": 0,
        "total_tokens": 0,
        "active_tokens": 0,
        "limit_tokens": LIMIT_TOKENS,
        "percentage": 0.0,
        "estimated_cost_usd": 0.0,
        "accuracy": "estimated",
        "updated_at": datetime.now().astimezone().isoformat()
    }
