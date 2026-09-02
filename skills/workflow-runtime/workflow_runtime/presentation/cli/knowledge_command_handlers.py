"""
workflow_runtime/presentation/cli/knowledge_command_handlers.py

CLI command handlers for AIWF knowledge services, RAG search, memory, telegram notifications, registry, and visual debug.
"""
from __future__ import annotations

import argparse
import sys
from typing import cast


def handle_notify(args: argparse.Namespace) -> int:
    from workflow_runtime.infrastructure.telegram.telegram_adapter import (
        TelegramAdapter)
    adapter = TelegramAdapter()
    msg_val = str(getattr(args, "message", ""))
    chat_val = str(getattr(args, "chat_id", ""))
    success = adapter.send_message(message=msg_val, chat_id=chat_val)
    if success:
        print("Telegram notification delivered successfully.")
        return 0
    return 1


def handle_cleanup(args: argparse.Namespace) -> int:
    from workflow_runtime.application.docs.cleanup_service import (
        DocsCleanupService)
    service = DocsCleanupService()
    dry_val = bool(getattr(args, "dry_run", False))
    ff_val = getattr(args, "feature_family", None)
    summary = service.run(dry_run=dry_val, feature_family=str(ff_val) if ff_val else None)
    print(
        f"Docs cleanup finished. Dry run={dry_val}, files moved={summary.files_moved}, errors={len(summary.errors)}"
    )
    return 0 if summary.is_success else 1


def handle_verify(args: argparse.Namespace) -> int:
    from workflow_runtime.application.verification.self_verify_service import (
        SelfVerifyService)
    service = SelfVerifyService()
    skill_val = str(getattr(args, "skill", ""))
    target_val = str(getattr(args, "target_dir", "."))
    result = service.run(skill_name=skill_val, target_dir=target_val)
    print(f"Skill verification: skill='{result.skill_name}' passed={result.passed} score={result.score}/100")
    for log_line in result.logs:
        print(f"  {log_line}")
    return 0 if result.passed else 1


def handle_search(args: argparse.Namespace) -> int:
    import json
    import os

    from workflow_runtime.infrastructure.memory.search import RAGSearcher

    query = str(getattr(args, "query", None) or getattr(args, "query_flag", None) or "")
    limit = int(cast(int, getattr(args, "limit", None) or 5))
    previous_json_mode = os.environ.get("AIWF_JSON_OUTPUT")
    if getattr(args, "format", "text") == "json":
        os.environ["AIWF_JSON_OUTPUT"] = "1"
    try:
        response = RAGSearcher(root_dir=os.getcwd()).execute_search(query)
    finally:
        if previous_json_mode is None:
            os.environ.pop("AIWF_JSON_OUTPUT", None)
        else:
            os.environ["AIWF_JSON_OUTPUT"] = previous_json_mode
    response["results"] = response.get("results", [])[:limit]
    if getattr(args, "format", "text") == "json":
        print(json.dumps(response, indent=2, ensure_ascii=True))
        return 0

    for idx, item in enumerate(response["results"], start=1):
        print(
            f"[{idx}] {item.get('file', 'unknown')} "
            f"(score: {float(item.get('score', 0.0)):.4f}, "
            f"freshness: {item.get('freshness', 'UNVERIFIED')})\n"
            f"    {item.get('text', item.get('snippet', ''))}"
        )
    return 0


def handle_memory(args: argparse.Namespace) -> int:
    import json
    import os

    output_format = str(getattr(args, "format", "text") or "text")
    mem_act = getattr(args, "memory_action", None) or getattr(args, "subaction", None) or getattr(args, "action", None)
    if mem_act == "update":
        from workflow_runtime.infrastructure.memory.update import run_update
        previous_json_mode = os.environ.get("AIWF_JSON_OUTPUT")
        if output_format == "json":
            os.environ["AIWF_JSON_OUTPUT"] = "1"
        try:
            res = run_update()
        finally:
            if previous_json_mode is None:
                os.environ.pop("AIWF_JSON_OUTPUT", None)
            else:
                os.environ["AIWF_JSON_OUTPUT"] = previous_json_mode
        print(json.dumps(res, indent=2, ensure_ascii=True) if output_format == "json" else res.get("summary", "Memory update complete."))
        return 0 if res.get("status") == "success" else 1
    elif mem_act == "bootstrap":
        from workflow_runtime.infrastructure.memory.bootstrap import run_bootstrap
        previous_json_mode = os.environ.get("AIWF_JSON_OUTPUT")
        if output_format == "json":
            os.environ["AIWF_JSON_OUTPUT"] = "1"
        try:
            res = run_bootstrap()
        finally:
            if previous_json_mode is None:
                os.environ.pop("AIWF_JSON_OUTPUT", None)
            else:
                os.environ["AIWF_JSON_OUTPUT"] = previous_json_mode
        print(json.dumps(res, indent=2, ensure_ascii=True) if output_format == "json" else res.get("summary", "Memory bootstrap complete."))
        return 0 if res.get("status") == "success" else 1
    elif mem_act in ("query", "search"):
        from workflow_runtime.infrastructure.memory.search import RAGSearcher
        q_val = str(getattr(args, "query", "") or "")
        limit = int(getattr(args, "limit", 10) or 10)
        previous_json_mode = os.environ.get("AIWF_JSON_OUTPUT")
        if output_format == "json":
            os.environ["AIWF_JSON_OUTPUT"] = "1"
        try:
            response = RAGSearcher(root_dir=os.getcwd()).execute_search(q_val)
        finally:
            if previous_json_mode is None:
                os.environ.pop("AIWF_JSON_OUTPUT", None)
            else:
                os.environ["AIWF_JSON_OUTPUT"] = previous_json_mode
        response["results"] = response.get("results", [])[:limit]
        if output_format == "json":
            print(json.dumps(response, indent=2, ensure_ascii=True))
        elif not response["results"]:
            print("No memory matches found.")
        else:
            for idx, entry in enumerate(response["results"], start=1):
                print(
                    f"[{idx}] {entry.get('file', 'unknown')} "
                    f"(score: {entry.get('score', 0.0)}, "
                    f"freshness: {entry.get('freshness', 'UNVERIFIED')})\n"
                    f"    {entry.get('text', entry.get('snippet', ''))}"
                )
        return 0
    return 0


def handle_state(args: argparse.Namespace) -> int:
    from workflow_runtime.infrastructure.persistence.state_store import (
        StateStoreAdapter)
    adapter = StateStoreAdapter()
    act = getattr(args, "action", None)
    key_val = str(getattr(args, "key", ""))
    val_val = getattr(args, "value", None)

    if act == "read":
        content = adapter.read_state(key=key_val)
        print(content)
        return 0
    elif act == "write":
        if not key_val or val_val is None:
            print("Both --key and --value are required for state write action.", file=sys.stderr)
            return 2
        adapter.write_state(key=key_val, value=str(val_val))
        print(f"STATE WRITE SUCCESS: key={key_val}")
        return 0
    return 1


def handle_telegram(args: argparse.Namespace) -> int:
    from workflow_runtime.application.telegram.telegram_service import (
        TelegramService)
    svc = TelegramService()
    extra: list[str] = []
    if getattr(args, "chat_id", None):
        extra.extend(["--chat-id", str(args.chat_id)])
    if getattr(args, "token", None):
        extra.extend(["--token", str(args.token)])
    if getattr(args, "message", None):
        extra.extend(["--message", str(args.message)])
    if getattr(args, "dry_run", False):
        extra.append("--dry-run")
    sub = getattr(args, "subaction", "status")
    result = svc.dispatch(command=str(sub), args=extra)
    print(result.get("message", "Telegram action completed."))
    return 0 if result.get("success", True) else 1


def handle_registry(args: argparse.Namespace) -> int:
    from workflow_runtime.application.registry.registry_service import (
        RegistryService)
    svc = RegistryService()
    sub = str(getattr(args, "subaction", "list") or "list")
    if sub == "list":
        projects = svc.list_projects()
        for p in projects:
            print(f"- {p.get('name')} ({p.get('path')}): status={p.get('status')}")
        return 0
    elif sub == "register":
        path_val = str(getattr(args, "path", ".") or ".")
        name_val = getattr(args, "name", None)
        res = svc.register(path=path_val, name=str(name_val) if name_val else None)
        print(f"Registered project: {res.get('name')} (id={res.get('id')})")
        return 0
    elif sub == "unregister":
        pid = str(getattr(args, "project_id", "") or "")
        ok = svc.unregister(project_id=pid)
        print(f"Unregistered project {pid}: {ok}")
        return 0 if ok else 1
    return 0


def handle_execution(args: argparse.Namespace) -> int:
    from workflow_runtime.application.execution.execution_control_service import (
        ExecutionControlService)
    svc = ExecutionControlService()
    sub = str(getattr(args, "subaction", "status") or "status")
    if sub == "pause":
        svc.pause()
        print("Workflow execution paused.")
    elif sub == "resume":
        svc.resume()
        print("Workflow execution resumed.")
    elif sub == "cancel":
        svc.cancel()
        print("Workflow execution cancelled.")
    else:
        st = svc.status()
        print(f"Execution status: {st}")
    return 0


def handle_provider(args: argparse.Namespace) -> int:
    from workflow_runtime.application.provider.provider_config_service import (
        ProviderConfigService)
    svc = ProviderConfigService()
    sub = str(getattr(args, "subaction", "list") or "list")
    if sub == "list":
        provs = svc.list_providers()
        for p in provs:
            print(f"- {p.get('name')}: enabled={p.get('enabled')}")
        return 0
    return 0


def handle_visual(args: argparse.Namespace) -> int:
    from workflow_runtime.application.visual.visual_debug_service import (
        VisualDebugService)
    svc = VisualDebugService()
    res = svc.run_checks()
    print(f"Visual Debug Status: {res.get('status')}")
    return 0
