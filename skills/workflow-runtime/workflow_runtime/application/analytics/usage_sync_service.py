from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from typing import Any, cast

from workflow_runtime.application.analysis.diff_engine import calculate_diff
from workflow_runtime.application.analytics.insights_engine import (
    calculate_efficiency_score, generate_recommendations)
from workflow_runtime.domain.core.context_metadata import (BRAIN_ROOT,
                                                           LIMIT_TOKENS)
from workflow_runtime.infrastructure.persistence.db_connections import \
    PROJECT_DB
from workflow_runtime.infrastructure.persistence.db_records import (
    get_provider_requests, save_insight_snapshot, save_provider_request,
    save_recommendations, save_timeline_event, save_token_diff)


def sync_request_history(conversation_id: str, project_id: str, workspace_root: str = ".", session: dict[str, Any] | None = None) -> None:
    if not conversation_id or os.environ.get("AIWF_RUNTIME_MODE") == "test-isolated" or "PYTEST_CURRENT_TEST" in os.environ:
        return

    log_file = os.path.join(BRAIN_ROOT, conversation_id, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(log_file):
        return

    file_size = os.path.getsize(log_file)
    last_bytes = 0
    current_history_chars = 0
    tool_call_count = 0
    workspace_read_count = 0
    memory_hit_count = 0
    rag_hit_count = 0
    conn: sqlite3.Connection | None = None

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
            last_bytes = cast(int, row[0])
            current_history_chars = cast(int, row[1])
            tool_call_count = cast(int, row[2])
            workspace_read_count = cast(int, row[3])
            memory_hit_count = cast(int, row[4])
            rag_hit_count = cast(int, row[5])

    except Exception:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
            conn = None

    if file_size == last_bytes:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
        return

    prev_breakdown: dict[str, Any] | None = None
    prev_request_id: str | None = None
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT request_id, context_breakdown_json
                FROM provider_requests
                WHERE conversation_id = ?
                ORDER BY rowid DESC LIMIT 1
            """, (conversation_id,))
            row = cursor.fetchone()
            if row:
                prev_request_id = str(row[0])
                cb_json_str = str(row[1])
                try:
                    loaded_cb = json.loads(cb_json_str)
                    if isinstance(loaded_cb, dict):
                        prev_breakdown = cast(dict[str, Any], loaded_cb)
                except Exception:
                    prev_breakdown = None
        except Exception:
            pass

    sess = session or {}
    checkpoint = int(sess.get("checkpoint", 1)) if isinstance(sess.get("checkpoint"), int) else 1
    skill = str(sess.get("current_skill", "unknown"))

    status = "success"
    error_summary: str | None = None
    provider = "antigravity"
    model = "auto"

    try:
        new_bytes_processed = 0
        with open(log_file, "r", encoding="utf-8", errors="replace") as f_text:
            if last_bytes > 0:
                f_text.seek(last_bytes)

            for line_str in f_text:
                new_bytes_processed += len(line_str.encode("utf-8", errors="replace"))
                if not line_str.strip():
                    continue
                try:
                    line_obj = json.loads(line_str)
                    if not isinstance(line_obj, dict):
                        continue
                    line = cast(dict[str, Any], line_obj)
                except json.JSONDecodeError:
                    continue

                content = str(line.get("content", ""))
                source = str(line.get("source", ""))
                type_ = str(line.get("type", ""))
                step_idx = int(line.get("step_index", 0)) if isinstance(line.get("step_index"), int) else 0

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

                if source in ["SYSTEM", "USER"]:
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

                    thinking = str(line.get("thinking", ""))
                    output_len = len(content) + len(thinking)
                    tool_calls_raw = line.get("tool_calls")
                    if isinstance(tool_calls_raw, list):
                        tool_calls = cast(list[Any], tool_calls_raw)
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

                    cb_data: dict[str, Any] = {
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

                    request_record: dict[str, Any] = {
                        "request_id": request_id,
                        "workflow_id": conversation_id,
                        "conversation_id": conversation_id,
                        "project_id": project_id,
                        "skill_name": skill,
                        "command_name": str(sess.get("current_command", "unknown")),
                        "model": model,
                        "provider": provider,
                        "timestamp": str(line.get("created_at")) if line.get("created_at") else datetime.now().astimezone().isoformat(),
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

                    save_provider_request(request_record)

                    diff_val = total_tokens
                    if prev_breakdown is not None:
                        diff_data: dict[str, Any] = calculate_diff(prev_breakdown, cb_data)
                        diff_data["request_id"] = request_id
                        diff_data["prev_request_id"] = prev_request_id
                        diff_data["conversation_id"] = conversation_id
                        diff_data["timestamp"] = request_record["timestamp"]
                        save_token_diff(diff_data)
                        diff_val = cast(int, diff_data.get("net_change_tokens", total_tokens))

                    timeline_record: dict[str, Any] = {
                        "timestamp": request_record["timestamp"],
                        "conversation_id": conversation_id,
                        "event_type": "Provider request",
                        "checkpoint": checkpoint,
                        "skill": skill,
                        "request_id": request_id,
                        "active_context": request_record["total_tokens"],
                        "context_delta": diff_val,
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

        if conn:
            try:
                cursor = conn.cursor()
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

        reqs: list[dict[str, Any]] = get_provider_requests({"conversation_id": conversation_id}, sort_by="timestamp", desc=False)
        if reqs:
            eff_score: int = calculate_efficiency_score(reqs)

            avg_tokens = int(sum(cast(int, r.get("total_tokens", 0)) for r in reqs) / max(1, len(reqs)))
            avg_cost = sum(cast(float, r.get("cost_usd", 0.0)) for r in reqs) / max(1, len(reqs))

            growth_trend = "stable"
            if len(reqs) > 1:
                first = cast(int, reqs[0].get("total_tokens", 0))
                last = cast(int, reqs[-1].get("total_tokens", 0))
                diff = last - first
                if diff > LIMIT_TOKENS * 0.1:
                    growth_trend = "growing"
                elif diff < -LIMIT_TOKENS * 0.1:
                    growth_trend = "shrinking"

            insight_data = {
                "request_count": len(reqs),
                "total_cost": round(sum(cast(float, r.get("cost_usd", 0.0)) for r in reqs), 4),
                "total_tokens": sum(cast(int, r.get("total_tokens", 0)) for r in reqs)
            }
            snapshot: dict[str, Any] = {
                "timestamp": datetime.now().astimezone().isoformat(),
                "conversation_id": conversation_id,
                "efficiency_score": eff_score,
                "avg_tokens": avg_tokens,
                "avg_cost": round(avg_cost, 6),
                "growth_trend": growth_trend,
                "insight_data_json": json.dumps(insight_data)
            }
            save_insight_snapshot(snapshot)

            recs: list[dict[str, Any]] = generate_recommendations(reqs, conversation_id)
            if recs:
                save_recommendations(recs)
    except Exception as e:
        print(f"Error parsing request history: {e}", file=sys.stderr)
        if conn:
            try:
                conn.close()
            except Exception:
                pass


__all__ = ["sync_request_history"]
