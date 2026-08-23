from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, cast


def calculate_efficiency_score(requests: list[dict[str, Any]]) -> int:
    """
    Computes an efficiency score from 10 to 100 based on requests analytics.
    """
    if not requests:
        return 100

    score = 100

    # Calculate avg total tokens
    total_tokens = sum(cast(int, r.get("total_tokens", 0)) for r in requests)
    avg_tokens = total_tokens / max(1, len(requests))

    # Deduct for large average context size (max deduction 30)
    if avg_tokens > 500000:
        deduction = min(30, int((avg_tokens - 500000) / 25000))
        score -= deduction

    # Deduct for expensive requests (cost > $0.15, max deduction 20)
    expensive_count = sum(1 for r in requests if cast(float, r.get("cost_usd", 0.0)) > 0.15)
    score -= min(20, expensive_count * 5)

    # Deduct for repeatedly loaded documents or high tool activities (max deduction 20)
    high_tool_count = sum(1 for r in requests if cast(int, r.get("tool_call_count", 0)) > 15)
    score -= min(20, high_tool_count * 4)

    # Deduct for low context efficiency (high context_usage_percentage, max deduction 20)
    high_pct_count = sum(1 for r in requests if cast(float, r.get("context_usage_percentage", 0.0)) > 80.0)
    score -= min(20, high_pct_count * 5)

    return max(10, min(100, score))


def generate_recommendations(requests: list[dict[str, Any]], conversation_id: str) -> list[dict[str, Any]]:
    if not requests:
        return []

    recs: list[dict[str, Any]] = []

    total_conv_history = 0
    total_rules = 0
    total_tokens = 0

    for r in requests:
        total_tokens += cast(int, r.get("total_tokens", 0))
        cb_json = r.get("context_breakdown_json")
        if cb_json:
            try:
                cb: dict[str, Any] = json.loads(cb_json) if isinstance(cb_json, str) else cast(dict[str, Any], cb_json)
                breakdown: list[dict[str, Any]] = cast(list[dict[str, Any]], cb.get("breakdown", []))
                for item in breakdown:
                    if item.get("category") == "Conversation History":
                        total_conv_history += cast(int, item.get("tokens", 0))
                    elif item.get("category") == "AI_RULES":
                        total_rules += cast(int, item.get("tokens", 0))
            except Exception:
                pass

    req_count = len(requests)
    avg_conv = total_conv_history / req_count if req_count > 0 else 0
    avg_rules = total_rules / req_count if req_count > 0 else 0
    avg_total = total_tokens / req_count if req_count > 0 else 0

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

    if avg_total > 0 and (avg_rules / avg_total) > 0.30:
        desc = "AI_RULES and AGENTS guidelines account for over 30% of active context. Consider trimming verbose instructions."
        token_savings = int(avg_rules * 0.3)
        cost_savings = round(token_savings * 0.000003, 4)
        recs.append({
            "type": "Optimize AI_RULES",
            "description": desc,
            "token_savings": token_savings,
            "cost_savings": cost_savings,
            "priority": "Medium",
            "confidence": 0.85
        })

    if req_count > 5:
        tool_counts = [cast(int, r.get("tool_call_count", 0)) for r in requests]
        avg_tools = sum(tool_counts) / req_count
        if avg_tools > 10:
            desc = f"Average tool calls per step is {round(avg_tools, 1)}. Batching tool executions can reduce overall turn count."
            token_savings = int(avg_total * 0.15)
            cost_savings = round(token_savings * 0.000003, 4)
            recs.append({
                "type": "Batch Tool Executions",
                "description": desc,
                "token_savings": token_savings,
                "cost_savings": cost_savings,
                "priority": "Medium",
                "confidence": 0.80
            })

    formatted_recs: list[dict[str, Any]] = []
    now_iso = datetime.now().astimezone().isoformat()
    for rec in recs:
        rec_id = hashlib.md5(f"{conversation_id}_{rec['type']}".encode("utf-8")).hexdigest()[:12]
        formatted_recs.append({
            "id": rec_id,
            "conversation_id": conversation_id,
            "type": rec["type"],
            "description": rec["description"],
            "token_savings": rec["token_savings"],
            "cost_savings": rec["cost_savings"],
            "priority": rec["priority"],
            "confidence": rec["confidence"],
            "status": "pending",
            "timestamp": now_iso
        })

    return formatted_recs


__all__ = [
    "calculate_efficiency_score",
    "generate_recommendations"
]
