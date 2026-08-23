"""
workflow_runtime/presentation/cli/commands/_impl/usage/usage_report.py

Usage detail reporter and entrypoint for AIWF CLI usage stats.
"""
from __future__ import annotations

import os
from typing import Any

from workflow_runtime.infrastructure.session.session_io import load_session


def get_usage_detail_summary() -> dict[str, str]:
    return {"status": "ok", "module": "usage_report"}


from workflow_runtime.infrastructure.persistence.metadata_insight_records import (
    get_project_summary, get_workflow_summary, save_usage_to_dbs)


def do_usage(args: Any) -> int:
    session = load_session()
    subaction = getattr(args, "subaction", None)
    if subaction:
        try:
            from workflow_runtime.presentation.cli.commands._impl.usage.usage_insights import (
                do_usage_extended)
            do_usage_extended(args)
            return 0
        except Exception:
            pass

    print("--- Usage Summary ---")
    print(f"Conversation ID: {session.get('conversation_id', 'unknown')}")
    print(f"Checkpoint: {session.get('checkpoint', 1)}")
    print(f"Tokens Used: {session.get('total_tokens', 0)}")
    return 0


__all__ = [
    "get_usage_detail_summary",
    "get_project_summary",
    "get_workflow_summary",
    "save_usage_to_dbs",
    "do_usage",
]
