"""
workflow_runtime/presentation/cli/knowledge_command_handlers.py

CLI command handlers for AIWF knowledge services, RAG search, memory, telegram notifications, registry, and visual debug.
"""
from __future__ import annotations

import argparse
import sys
from typing import Any, cast


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
    import logging

    from workflow_runtime.application.knowledge.rag_service import RAGService
    from workflow_runtime.application.ports.locator import (
        InfrastructureLocator)
    if getattr(InfrastructureLocator, "RAGStoreAdapter", None) is not None and getattr(InfrastructureLocator, "MemoryStoreAdapter", None) is not None:
        rag_cls: Any = getattr(InfrastructureLocator, "RAGStoreAdapter")
        mem_cls: Any = getattr(InfrastructureLocator, "MemoryStoreAdapter")
        rag_store = rag_cls()
        mem_store = mem_cls()
    else:
        import importlib
        rag_mod = importlib.import_module("workflow_runtime.infrastructure.knowledge.rag_store_adapter")
        mem_mod = importlib.import_module("workflow_runtime.infrastructure.knowledge.memory_store_adapter")
        rag_cls: Any = getattr(rag_mod, "RAGStoreAdapter")
        mem_cls: Any = getattr(mem_mod, "MemoryStoreAdapter")
        rag_store = rag_cls()
        mem_store = mem_cls()
    logging.getLogger("workflow_runtime.infrastructure.knowledge.rag_store_adapter").disabled = True
    service = RAGService(sqlite_store=rag_store, memory_store=mem_store)
    query = str(getattr(args, "query", None) or getattr(args, "query_flag", None) or "")
    top_k = int(cast(int, getattr(args, "limit", None) or getattr(args, "top_k", 5)))
    results = service.query(query=query, top_k=top_k)
    for idx, item in enumerate(results, start=1):
        path_str = item.file_path.path if hasattr(item.file_path, "path") else str(item.file_path)
        print(f"[{idx}] {path_str} (score: {item.score:.4f})\n    {item.snippet}")
    return 0


def handle_memory(args: argparse.Namespace) -> int:
    import os
    import subprocess
    mem_act = getattr(args, "memory_action", None) or getattr(args, "subaction", None) or getattr(args, "action", None)
    if mem_act == "update":
        from workflow_runtime.infrastructure.memory.update import run_update
        res = run_update()
        return 0 if res.get("status") == "success" else 1
    elif mem_act == "bootstrap":
        from workflow_runtime.infrastructure.memory.bootstrap import run_bootstrap
        res = run_bootstrap()
        return 0 if res.get("status") == "success" else 1
    elif mem_act in ("query", "search"):
        from workflow_runtime.infrastructure.memory.search import RAGSearcher
        searcher = RAGSearcher()
        q_val = str(getattr(args, "query", "") or "")
        results = searcher.local_search(q_val)
        if not results:
            print("No memory matches found.")
            return 0
        limit = int(getattr(args, "limit", 10) or 10)
        for idx, entry in enumerate(results[:limit], start=1):
            file_name = entry.get("file", "unknown")
            snippet = entry.get("snippet", entry.get("text", ""))
            print(f"[{idx}] {file_name} (score: {entry.get('score', 0.0)})\n    {snippet}")
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
