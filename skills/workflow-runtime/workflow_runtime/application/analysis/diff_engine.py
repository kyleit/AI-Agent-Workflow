# diff_engine.py
from __future__ import annotations

from typing import Any, cast


def _sort_key(item: tuple[str, dict[str, Any]]) -> int:
    val = item[1].get("delta", 0)
    return abs(int(cast(int, val)))


def calculate_diff(breakdown_a: dict[str, Any] | None = None, breakdown_b: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Compares two context breakdown JSON dicts and calculates the differences.
    breakdown_a: previous breakdown dict (or empty)
    breakdown_b: current breakdown dict (or empty)
    """
    bd_a = breakdown_a or {}
    bd_b = breakdown_b or {}

    bd_a_items = bd_a.get("breakdown")
    items_a = cast(list[Any], bd_a_items) if isinstance(bd_a_items, list) else []
    cats_a: dict[str, int] = {}
    for item in items_a:
        if isinstance(item, dict):
            item_dict = cast(dict[str, Any], item)
            cat_name = str(item_dict.get("category", ""))
            tokens_val = int(cast(int, item_dict.get("tokens", 0)))
            cats_a[cat_name] = tokens_val

    bd_b_items = bd_b.get("breakdown")
    items_b = cast(list[Any], bd_b_items) if isinstance(bd_b_items, list) else []
    cats_b: dict[str, int] = {}
    for item in items_b:
        if isinstance(item, dict):
            item_dict = cast(dict[str, Any], item)
            cat_name = str(item_dict.get("category", ""))
            tokens_val = int(cast(int, item_dict.get("tokens", 0)))
            cats_b[cat_name] = tokens_val

    all_categories = set(cats_a.keys()).union(set(cats_b.keys()))

    diff_cats: dict[str, dict[str, Any]] = {}
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

    sorted_categories = dict(sorted(diff_cats.items(), key=_sort_key, reverse=True))

    return {
        "previous_request_id": bd_a.get("request_id") or bd_a.get("conversation_id") or "unknown",
        "current_request_id": bd_b.get("request_id") or bd_b.get("conversation_id") or "unknown",
        "net_change_tokens": net,
        "percentage_change": net_pct,
        "added_tokens": added,
        "removed_tokens": removed,
        "categories": sorted_categories
    }


__all__ = ["calculate_diff"]
