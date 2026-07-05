# context.py
import os
import sys

# Ensure sibling imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from session import load_session

LIMIT_TOKENS = 2000000
BRAIN_ROOT = r"C:\Users\Kyle\.gemini\antigravity-ide\brain"

def estimate_context_usage() -> dict:
    session = load_session()
    conv_id = session.get("conversation_id")
    
    if not conv_id:
        return {"total_tokens": 0, "limit_tokens": LIMIT_TOKENS, "percentage": 0.0}
        
    log_file = os.path.join(BRAIN_ROOT, conv_id, ".system_generated", "logs", "transcript.jsonl")
    
    if not os.path.exists(log_file):
        return {"total_tokens": 0, "limit_tokens": LIMIT_TOKENS, "percentage": 0.0}
        
    try:
        size = os.path.getsize(log_file)
        # 1 token is roughly 3 bytes on average
        tokens = int(size / 3)
        percentage = round((tokens / LIMIT_TOKENS) * 100, 2)
        return {
            "total_tokens": tokens,
            "limit_tokens": LIMIT_TOKENS,
            "percentage": percentage
        }
    except OSError:
        return {"total_tokens": 0, "limit_tokens": LIMIT_TOKENS, "percentage": 0.0}
