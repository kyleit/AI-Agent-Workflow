# forecaster.py
from __future__ import annotations

from typing import Any, cast


def make_forecast(events: list[dict[str, Any]], limit: int = 2000000) -> dict[str, Any]:
    """
    Computes regression forecasting for remaining context, requests, and cost.
    """
    if not events:
        return {
            "exhaustion_probability": "Low",
            "confidence_level": "Low",
            "remaining_requests": 99,
            "predicted_next_context": 0,
            "estimated_cost_to_complete": 0.0
        }

    req_events = [e for e in events if str(e.get("event_type", "")) == "Provider request"]
    if len(req_events) < 2:
        latest_ctx = int(cast(int, req_events[0].get("active_context", 10000))) if req_events else 10000
        rem_tokens = limit - latest_ctx
        rem_reqs = max(1, int(rem_tokens / 50000.0))

        prob = "Low"
        if rem_tokens < 200000 or rem_reqs <= 3:
            prob = "Critical"
        elif rem_tokens < 500000 or rem_reqs <= 6:
            prob = "High"

        return {
            "exhaustion_probability": prob,
            "confidence_level": "Low",
            "remaining_requests": rem_reqs,
            "predicted_next_context": latest_ctx + 50000,
            "estimated_cost_to_complete": round(rem_reqs * 0.045, 4)
        }

    deltas = [int(cast(int, e.get("context_delta", 0))) for e in req_events[-3:]]
    avg_growth = float(sum(max(0, d) for d in deltas) / float(len(deltas))) if deltas else 35000.0
    if avg_growth <= 1000.0:
        avg_growth = 35000.0

    latest_ctx = int(cast(int, req_events[-1].get("active_context", 0)))
    remaining_tokens = max(0, limit - latest_ctx)

    rem_reqs = max(1, int(remaining_tokens / avg_growth))

    costs = [float(cast(float, e.get("cost", 0.0))) for e in req_events[-3:]]
    avg_cost = float(sum(costs) / float(len(costs))) if costs else 0.015
    if avg_cost <= 0.0:
        avg_cost = 0.015

    conf = "High" if len(req_events) >= 3 else "Medium"

    if remaining_tokens < 200000 or rem_reqs <= 3:
        prob = "Critical"
    elif remaining_tokens < 500000 or rem_reqs <= 6:
        prob = "High"
    elif remaining_tokens < 1000000 or rem_reqs <= 12:
        prob = "Medium"
    else:
        prob = "Low"

    return {
        "exhaustion_probability": prob,
        "confidence_level": conf,
        "remaining_requests": rem_reqs,
        "predicted_next_context": min(limit, latest_ctx + int(avg_growth)),
        "estimated_cost_to_complete": round(rem_reqs * avg_cost, 4)
    }


__all__ = ["make_forecast"]
