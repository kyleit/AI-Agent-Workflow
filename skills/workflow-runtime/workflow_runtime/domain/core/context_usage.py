# context.py
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, cast

from workflow_runtime.infrastructure.session.session import load_session

from .context_metadata import parse_transcript

LIMIT_TOKENS = 2000000
BRAIN_ROOT = os.path.expanduser("~/.gemini/antigravity-ide/brain")


def get_fallback_usage(session: dict[str, Any], default_provider: str) -> dict[str, Any]:
    checkpoint = int(str(session.get("checkpoint", 1)))
    percentage = min(checkpoint * 8.5, 95.0)
    active_tokens = int((percentage / 100) * LIMIT_TOKENS)
    total_tokens = active_tokens

    input_tokens = int(total_tokens * 0.98)
    output_tokens = int(total_tokens * 0.02)
    cache_tokens = int(total_tokens * 0.15)
    thinking_tokens = int(total_tokens * 0.005)

    return {
        "provider": default_provider,
        "model": "auto",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_tokens": cache_tokens,
        "thinking_tokens": thinking_tokens,
        "active_tokens": active_tokens,
        "total_tokens": total_tokens,
        "limit_tokens": LIMIT_TOKENS,
        "percentage": round(percentage, 2),
        "estimated_cost_usd": round(total_tokens * 1.5 / 1000000, 4),
        "accuracy": "estimated",
        "updated_at": datetime.now().astimezone().isoformat()
    }


def detect_active_conversation_id() -> str:
    metadata_str = os.environ.get("ANTIGRAVITY_SOURCE_METADATA")
    if metadata_str:
        try:
            metadata = json.loads(metadata_str)
            if isinstance(metadata, dict):
                metadata_dict = cast(dict[str, Any], metadata)
                tool_data = metadata_dict.get("tool")
                if isinstance(tool_data, dict):
                    tool_dict = cast(dict[str, Any], tool_data)
                    env_conv_id = tool_dict.get("conversationId")
                    if isinstance(env_conv_id, str) and env_conv_id:
                        return env_conv_id
        except Exception:
            pass
    return ""


def sync_conversation_id(session: dict[str, Any]) -> bool:
    active_id = detect_active_conversation_id()
    if not active_id:
        return False
    old_id = session.get("conversation_id")
    if old_id != active_id:
        session["conversation_id"] = active_id
        log_msg = f"Conversation changed: {old_id} -> {active_id}. Context usage recalculated."
        if "current_logs" not in session or not isinstance(session["current_logs"], list):
            session["current_logs"] = []
        logs_val = session.get("current_logs")
        logs_list: list[Any] = cast(list[Any], logs_val) if isinstance(logs_val, list) else []
        logs_list.append(log_msg)
        session["current_logs"] = logs_list
        session["updated_at"] = datetime.now().astimezone().isoformat()
        return True
    return False


def refresh_context_usage_for_active_conversation(session: dict[str, Any]) -> dict[str, Any]:
    sync_conversation_id(session)
    raw_conv_id = session.get("conversation_id")
    conv_id = str(raw_conv_id) if raw_conv_id is not None else ""
    if conv_id:
        log_file = os.path.join(BRAIN_ROOT, conv_id, ".system_generated", "logs", "transcript.jsonl")
        if not os.path.exists(log_file):
            warn_msg = f"Warning: Transcript file not found for conversation {conv_id}. Falling back to zero context usage."
            if "current_logs" not in session or not isinstance(session["current_logs"], list):
                session["current_logs"] = []
            logs_val = session.get("current_logs")
            logs_list: list[Any] = cast(list[Any], logs_val) if isinstance(logs_val, list) else []
            if warn_msg not in logs_list:
                logs_list.append(warn_msg)
            session["current_logs"] = logs_list
    usage = estimate_context_usage(conv_id)
    session["context_usage"] = {
        "total_tokens": usage.get("active_tokens", 0),
        "limit_tokens": usage.get("limit_tokens", 2000000),
        "percentage": usage.get("percentage", 0.0)
    }
    return usage


def estimate_context_usage(conversation_id: str | None = None) -> dict[str, Any]:
    conv_id: str = ""
    if conversation_id is None:
        session = load_session()
        raw_conv_id = session.get("conversation_id")
        conv_id = str(raw_conv_id) if raw_conv_id is not None else ""
    else:
        conv_id = conversation_id

    default_provider = "antigravity" if "ANTIGRAVITY_AGENT" in os.environ else "estimate"

    if not conv_id:
        return get_fallback_usage({}, default_provider)

    log_file = os.path.join(BRAIN_ROOT, conv_id, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(log_file):
        return {
            "provider": default_provider,
            "model": "auto",
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_tokens": 0,
            "thinking_tokens": 0,
            "active_tokens": 0,
            "total_tokens": 0,
            "limit_tokens": LIMIT_TOKENS,
            "percentage": 0.0,
            "estimated_cost_usd": 0.0,
            "accuracy": "unknown",
            "updated_at": datetime.now().astimezone().isoformat()
        }

    parsed = parse_transcript(log_file)
    if parsed:
        return parsed

    session_fallback = load_session() if conversation_id is None else {"conversation_id": conv_id}
    return get_fallback_usage(session_fallback, default_provider)


__all__ = [
    "get_fallback_usage",
    "detect_active_conversation_id",
    "sync_conversation_id",
    "refresh_context_usage_for_active_conversation",
    "estimate_context_usage",
]
