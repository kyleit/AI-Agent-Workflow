# forecaster.py
import json

def make_forecast(events: list, limit=2000000) -> dict:
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
        
    req_events = [e for e in events if e.get("event_type") == "Provider request"]
    if len(req_events) < 2:
        # Fallback if too few requests
        latest_ctx = req_events[0].get("active_context", 10000) if req_events else 10000
        rem_tokens = limit - latest_ctx
        rem_reqs = max(1, int(rem_tokens / 50000))
        
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
        
    # Calculate avg growth from delta of last requests
    deltas = [e.get("context_delta", 0) for e in req_events[-3:]]
    # Filter negative/neutral growth to avoid zero division
    avg_growth = sum(max(0, d) for d in deltas) / len(deltas)
    if avg_growth <= 1000:
        avg_growth = 35000 # default fallback
        
    latest_ctx = req_events[-1].get("active_context", 0)
    remaining_tokens = max(0, limit - latest_ctx)
    
    rem_reqs = max(1, int(remaining_tokens / avg_growth))
    
    # Calculate avg cost
    costs = [e.get("cost", 0.0) for e in req_events[-3:]]
    avg_cost = sum(costs) / len(costs) if costs else 0.015
    if avg_cost <= 0:
        avg_cost = 0.015
        
    # Confidence level depends on history length
    conf = "High" if len(req_events) >= 3 else "Medium"
        
    # Exhaustion probability based on remaining requests
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
