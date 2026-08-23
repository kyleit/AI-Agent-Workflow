# context.py
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any, cast

LIMIT_TOKENS = 2000000
BRAIN_ROOT = os.path.expanduser("~/.gemini/antigravity-ide/brain")

def get_workflow_metadata(project_path: str) -> dict[str, Any] | None:
    """Best-effort AIWF metadata lookup; never raises for non-AIWF projects."""
    try:
        root = project_path.strip()
        if not root or not os.path.isdir(root):
            return None
        session_path = os.path.join(root, ".agents", ".session.json")
        if os.path.exists(session_path):
            with open(session_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cast(dict[str, Any], data) if isinstance(data, dict) else None
        state_root = os.path.join(root, ".agents", "state")
        metadata: dict[str, Any] = {}
        for key, path in [
            ("context", os.path.join(state_root, "context.json")),
            ("workflow", os.path.join(state_root, "workflow.json")),
        ]:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                if isinstance(payload, dict):
                    metadata[key] = payload
        return metadata or None
    except Exception:
        return None

def parse_transcript(log_file: str) -> dict[str, Any]:
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
    request_count = 0

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
                if line.get("type") == "USER_INPUT" and content and "Model Selection" in content:
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
                type_ = line.get("type")
                if source == "MODEL" and type_ in ["PLANNER_RESPONSE", "ASK_QUESTION"]:
                    # This turn's input is the context compiled so far
                    total_input_chars += current_history_chars
                    request_count += 1

                    # Calculate this turn's output characters
                    thinking = line.get("thinking", "")
                    if thinking:
                        thinking_chars += len(thinking)

                    output_len = len(content) + len(thinking)
                    tool_calls: list[Any] = cast(list[Any], line.get("tool_calls", [])) if isinstance(line.get("tool_calls"), list) else []
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
            uncached = max(0, input_tokens - cache_tokens)
            cost = (uncached * 1.25 / 1000000) + (cache_tokens * 0.3125 / 1000000) + (output_tokens * 3.75 / 1000000)
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
            "request_count": request_count,
            "accuracy": "estimated",
            "updated_at": datetime.now().astimezone().isoformat()
        }
    except Exception:
        pass

    return {}
