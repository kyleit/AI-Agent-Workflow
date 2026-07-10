# insights_engine.py
import json
import hashlib
from datetime import datetime

def calculate_efficiency_score(requests: list) -> int:
    """
    Computes an efficiency score from 10 to 100 based on requests analytics.
    """
    if not requests:
        return 100
        
    score = 100
    
    # Calculate avg total tokens
    total_tokens = sum(r.get("total_tokens", 0) for r in requests)
    avg_tokens = total_tokens / len(requests)
    
    # Deduct for large average context size (max deduction 30)
    if avg_tokens > 500000:
        deduction = min(30, int((avg_tokens - 500000) / 25000))
        score -= deduction
        
    # Deduct for expensive requests (cost > $0.15, max deduction 20)
    expensive_count = sum(1 for r in requests if r.get("cost_usd", 0.0) > 0.15)
    score -= min(20, expensive_count * 5)
    
    # Deduct for repeatedly loaded documents or high tool activities (max deduction 20)
    high_tool_count = sum(1 for r in requests if r.get("tool_call_count", 0) > 15)
    score -= min(20, high_tool_count * 4)
    
    # Ensure minimum score is 10
    return max(10, score)

def generate_recommendations(requests: list, conversation_id: str) -> list[dict]:
    """
    Analyzes historical requests and generates a list of actionable optimization recommendations.
    """
    if not requests:
        return []
        
    recs = []
    
    # Heuristic 1: Conversation History accounts for > 50% context
    total_conv_history = 0
    total_rules = 0
    total_tokens = 0
    
    for r in requests:
        total_tokens += r.get("total_tokens", 0)
        cb_json = r.get("context_breakdown_json")
        if cb_json:
            try:
                cb = json.loads(cb_json) if isinstance(cb_json, str) else cb_json
                for item in cb.get("breakdown", []):
                    if item.get("category") == "Conversation History":
                        total_conv_history += item.get("tokens", 0)
                    elif item.get("category") == "AI_RULES":
                        total_rules += item.get("tokens", 0)
            except Exception:
                pass
                
    req_count = len(requests)
    avg_conv = total_conv_history / req_count if req_count > 0 else 0
    avg_rules = total_rules / req_count if req_count > 0 else 0
    avg_total = total_tokens / req_count if req_count > 0 else 0
    
    # Conversation history recommendation
    if avg_total > 0 and (avg_conv / avg_total) > 0.50:
        desc = "Conversation history accounts for over 50% of the active context. Archiving older messages can clean up the context window."
        token_savings = int(avg_conv * 0.4)
        cost_savings = round(token_savings * 0.000003, 4)
        recs.append({
            "type": "Reduce Conversation History",
            "description": desc,
            "token_savings": token_savings,
            "cost_savings": cost_savings,
            "priority": "High",
            "confidence": 0.90
        })
        
    # Heuristic 2: Workspace reads are high
    total_reads = sum(r.get("workspace_read_count", 0) for r in requests)
    if total_reads > 10:
        desc = f"Detected high workspace file activity ({total_reads} reads). Converting repeated workspace reads into RAG retrieval saves tokens."
        token_savings = int(total_reads * 1500)
        cost_savings = round(token_savings * 0.000003, 4)
        recs.append({
            "type": "Convert repeated workspace reads into RAG",
            "description": desc,
            "token_savings": token_savings,
            "cost_savings": cost_savings,
            "priority": "Medium",
            "confidence": 0.80
        })
        
    # Heuristic 3: Blueprint is too large
    if avg_total > 100000 and avg_rules > 30000:
        desc = "The Technical Design Blueprint or active rules size is over 100K tokens. Splitting oversized Blueprints/ADRs keeps model processing fast."
        token_savings = 40000
        cost_savings = 0.12
        recs.append({
            "type": "Split oversized Blueprint",
            "description": desc,
            "token_savings": token_savings,
            "cost_savings": cost_savings,
            "priority": "High",
            "confidence": 0.95
        })

    # Heuristic 4: Move documents to project memory
    memory_hits = sum(r.get("memory_hit_count", 0) for r in requests)
    if memory_hits > 5:
        desc = "Repeated project config checks detected. Move active reference documents into centralized Project Memory."
        token_savings = 15000
        cost_savings = 0.045
        recs.append({
            "type": "Move document into Project Memory",
            "description": desc,
            "token_savings": token_savings,
            "cost_savings": cost_savings,
            "priority": "Medium",
            "confidence": 0.85
        })

    # Helper: assign IDs
    for r in recs:
        hash_input = f"{conversation_id}:{r['type']}:{r['description']}"
        r["id"] = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:16]
        r["conversation_id"] = conversation_id
        r["status"] = "pending"
        r["timestamp"] = datetime.now().astimezone().isoformat()
        
    return recs
