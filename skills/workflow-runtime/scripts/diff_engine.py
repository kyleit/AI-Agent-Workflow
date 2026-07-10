# diff_engine.py
import json

def calculate_diff(breakdown_a: dict, breakdown_b: dict) -> dict:
    """
    Compares two context breakdown JSON dicts and calculates the differences.
    breakdown_a: previous breakdown dict (or empty)
    breakdown_b: current breakdown dict (or empty)
    """
    if not breakdown_a:
        breakdown_a = {}
    if not breakdown_b:
        breakdown_b = {}
        
    cats_a = {item["category"]: item["tokens"] for item in breakdown_a.get("breakdown", [])}
    cats_b = {item["category"]: item["tokens"] for item in breakdown_b.get("breakdown", [])}
    
    all_categories = set(cats_a.keys()).union(set(cats_b.keys()))
    
    diff_cats = {}
    added = 0
    removed = 0
    
    for cat in all_categories:
        prev = cats_a.get(cat, 0)
        curr = cats_b.get(cat, 0)
        delta = curr - prev
        
        if delta > 0:
            added += delta
        else:
            removed += abs(delta)
            
        pct = round((delta / max(1, prev)) * 100, 2)
        diff_cats[cat] = {
            "previous": prev,
            "current": curr,
            "delta": delta,
            "percentage": pct
        }
        
    net = added - removed
    prev_total = sum(cats_a.values())
    net_pct = round((net / max(1, prev_total)) * 100, 2)
    
    # Sort categories by absolute delta descending
    sorted_categories = dict(sorted(diff_cats.items(), key=lambda x: abs(x[1]["delta"]), reverse=True))
    
    return {
        "previous_request_id": breakdown_a.get("request_id") or breakdown_a.get("conversation_id") or "unknown",
        "current_request_id": breakdown_b.get("request_id") or breakdown_b.get("conversation_id") or "unknown",
        "net_change_tokens": net,
        "percentage_change": net_pct,
        "added_tokens": added,
        "removed_tokens": removed,
        "categories": sorted_categories
    }
