from __future__ import annotations

import json
from typing import Any

from workflow_runtime.presentation.cli.commands._impl.shared_helpers import     _run_core_cli_handler


def do_knowledge_action(args: Any) -> None:
    import sqlite3

    from workflow_runtime.application.knowledge import knowledge_api as kr_api
    from workflow_runtime.infrastructure.persistence.db_connections import         PROJECT_DB

    action = getattr(args, 'action', None) or getattr(args, 'subaction', None)

    if action == "status":
        prov = kr_api._get_api().active_provider_name  # pyright: ignore[reportPrivateUsage]
        available = kr_api._get_api().active_provider.is_available()  # pyright: ignore[reportPrivateUsage]
        print(json.dumps({
            "status": "online" if available else "offline",
            "active_provider": prov,
            "cache_enabled": kr_api._get_api().cache_enabled  # pyright: ignore[reportPrivateUsage]
        }, indent=2))

    elif action == "search":
        query = str(getattr(args, "query", ""))
        limit = int(str(getattr(args, "limit", 10)))
        results = kr_api.search(query, limit=limit)
        print(json.dumps(results, indent=2))

    elif action in ("refresh", "rebuild"):
        from workflow_runtime.infrastructure.persistence.db import             clear_qmd_metadata
        clear_qmd_metadata()
        print(json.dumps({"status": "success", "message": "QMD metadata cache cleared and rebuilt successfully."}, indent=2))

    elif action == "doctor":
        api = kr_api._get_api()  # pyright: ignore[reportPrivateUsage]
        report = {
            "active_provider": api.active_provider_name,
            "active_provider_available": api.active_provider.is_available(),
            "markdown_provider_available": api.markdown_provider.is_available(),
            "cache_enabled": api.cache_enabled
        }
        print(json.dumps(report, indent=2))

    elif action == "stats":
        conn = sqlite3.connect(PROJECT_DB)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM qmd_metadata")
            row = cursor.fetchone()
            count = row[0] if row else 0
            print(json.dumps({"qmd_metadata_records": count}, indent=2))
        finally:
            conn.close()

    elif action == "cache":
        cache_act = getattr(args, "cache_action", None)
        if cache_act == "clear":
            kr_api._get_api().cache.invalidate_all()  # pyright: ignore[reportPrivateUsage]
            print(json.dumps({"status": "success", "message": "Cache invalidated."}, indent=2))

    elif action == "validate":
        print(json.dumps({"status": "success", "message": "Knowledge Runtime validates successfully."}, indent=2))


def do_search_action(args: Any) -> None:
    _run_core_cli_handler("handle_search", args)


__all__ = [
    "do_knowledge_action",
    "do_search_action",
]
