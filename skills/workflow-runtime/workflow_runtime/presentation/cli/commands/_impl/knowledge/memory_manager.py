from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, cast

from workflow_runtime.presentation.cli.commands._impl.shared_helpers import \
    _run_core_cli_handler  # pyright: ignore[reportPrivateUsage]


def do_memory_action(args: Any) -> None:
    subaction = str(getattr(args, 'action', None) or getattr(args, 'subaction', None) or "")
    if subaction == "query":
        args.memory_action = "query"
        _run_core_cli_handler("handle_memory", args)
        return

    _memory_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "infrastructure", "memory"
    )
    _memory_dir = os.path.normpath(_memory_dir)
    if _memory_dir not in sys.path:
        sys.path.insert(0, _memory_dir)

    res: dict[str, Any] = {}
    if subaction == "bootstrap":
        from workflow_runtime.infrastructure.memory.bootstrap import \
            run_bootstrap
        res = run_bootstrap()
    elif subaction == "update":
        from workflow_runtime.infrastructure.memory.update import run_update
        res = run_update()
    elif subaction == "search":
        from workflow_runtime.infrastructure.memory.search import RAGSearcher
        searcher = RAGSearcher()
        query_str = str(getattr(args, "query", "") or "")
        res = searcher.execute_search(query_str)
    elif subaction == "status":
        memory_dir = Path(".agents") / "memory"
        state_file = memory_dir / "memory-state.json"
        walkthrough = memory_dir / "walkthrough.md"
        state: dict[str, Any] = {}
        if state_file.exists():
            try:
                import json as _json
                raw_s = _json.loads(state_file.read_text(encoding="utf-8"))
                if isinstance(raw_s, dict):
                    state = cast(dict[str, Any], raw_s)
            except Exception:
                pass
        res = {
            "status": "success",
            "summary": "Memory system is available.",
            "memory_dir": str(memory_dir),
            "state_file_exists": state_file.exists(),
            "walkthrough_exists": walkthrough.exists(),
            "project": state.get("project", {}),
        }
    elif subaction == "reset":
        res = {"status": "success", "summary": "Memory reset not implemented in CLI (use bootstrap)."}
    elif subaction == "export":
        res = {"status": "success", "summary": "Memory export not implemented in CLI."}
    else:
        res = {"status": "failure", "summary": "Invalid memory subaction."}

    summary_str = str(res.get("message") or res.get("summary") or "Memory operation complete.")
    raw_warnings = res.get("warnings")
    warnings_list: list[Any] = cast(list[Any], raw_warnings) if isinstance(raw_warnings, list) else []
    raw_read = res.get("files_read")
    read_list: list[Any] = cast(list[Any], raw_read) if isinstance(raw_read, list) else []
    raw_written = res.get("files_written")
    written_list: list[Any] = cast(list[Any], raw_written) if isinstance(raw_written, list) else []

    result: dict[str, Any] = {
        "status": str(res.get("status", "success")),
        "command": f"memory {subaction}",
        "summary": summary_str,
        "warnings": warnings_list,
        "files_read": read_list,
        "files_written": written_list,
        "next_skill": res.get("next_skill")
    }
    for key in ("provider_chain", "selected_provider", "provider_health", "results", "results_count", "fallback_reason", "current_source_authority"):
        if key in res:
            result[key] = res[key]
    print(json.dumps(result, indent=2))
    if str(result["status"]) != "success":
        sys.exit(1)


def do_env_action(args: Any) -> None:
    from workflow_runtime.application.system.environment_health import \
        run_health_check
    _ = args
    res = run_health_check()
    print(json.dumps(res, indent=2))
    if str(res.get("status", "")) != "success":
        sys.exit(1)


def do_mail_action(args: Any) -> None:
    _run_core_cli_handler("handle_mail", args)


__all__ = [
    "do_memory_action",
    "do_env_action",
    "do_mail_action",
]
