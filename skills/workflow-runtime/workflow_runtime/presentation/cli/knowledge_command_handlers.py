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
    mem_act = getattr(args, "memory_action", None)
    if mem_act == "update":
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "infrastructure", "memory", "update.py"))
        cmd = [sys.executable, script_path]
        if getattr(args, "full", False):
            cmd.append("--full")
        res = subprocess.run(cmd)
        return res.returncode
    elif mem_act == "bootstrap":
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "infrastructure", "memory", "bootstrap.py"))
        cmd = [sys.executable, script_path]
        res = subprocess.run(cmd)
        return res.returncode
    elif mem_act == "query":
        from workflow_runtime.application.knowledge.memory_service import (
            MemoryService)
        from workflow_runtime.application.ports.locator import (
            InfrastructureLocator)
        if getattr(InfrastructureLocator, "MemoryStoreAdapter", None) is not None:
            mem_cls: Any = getattr(InfrastructureLocator, "MemoryStoreAdapter")
            mem_store = mem_cls()
        else:
            import importlib
            mod = importlib.import_module("workflow_runtime.infrastructure.knowledge.memory_store_adapter")
            mem_cls: Any = getattr(mod, "MemoryStoreAdapter")
            mem_store = mem_cls()
        service = MemoryService(memory_store=mem_store)
        q_val = str(getattr(args, "query", ""))
        cat_val = str(getattr(args, "category", ""))
        results = service.query(query=q_val, category=cat_val)
        for entry in results:
            print(f"[{entry.scope.value}] {entry.entry_id} ({entry.title}): {entry.content}")
        return 0
    return 1


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
    if getattr(args, "proxy", None):
        extra.extend(["--proxy", str(args.proxy)])
    sub_val = str(getattr(args, "subcommand", ""))
    return svc.run(sub_val, extra)


def handle_registry(args: argparse.Namespace) -> int:
    from workflow_runtime.application.ports.locator import (
        InfrastructureLocator)
    if getattr(InfrastructureLocator, "RegistryAdapter", None) is not None:
        reg_cls: Any = getattr(InfrastructureLocator, "RegistryAdapter")
        reg: Any = reg_cls()
    else:
        import importlib
        mod = importlib.import_module("workflow_runtime.infrastructure.registry.registry_adapter")
        reg_cls: Any = getattr(mod, "RegistryAdapter")
        reg: Any = reg_cls()
    sub = getattr(args, "subcommand", None)

    if sub == "list":
        raw_projects = reg.list_projects()
        projects = cast(list[dict[str, Any]], raw_projects) if isinstance(raw_projects, list) else []
        if not projects:
            print("No projects registered.")
            return 0
        for p in projects:
            print(f"  [{p.get('id', '?')}] {p.get('name', '?')} — {p.get('path', '?')}")
        return 0

    elif sub == "register":
        path_val = getattr(args, "path", None)
        if not path_val:
            print("--path is required for register", file=sys.stderr)
            return 2
        raw_result = reg.register(str(path_val), force=bool(getattr(args, "force", False)))
        result = cast(dict[str, Any], raw_result) if isinstance(raw_result, dict) else {}
        print(f"Registered: {result.get('name')} (id={result.get('id')})")
        return 0

    elif sub == "unregister":
        path_val = getattr(args, "path", None)
        if not path_val:
            print("--path is required for unregister", file=sys.stderr)
            return 2
        ok = bool(reg.unregister(str(path_val)))
        print("Unregistered." if ok else "Project not found.")
        return 0 if ok else 1

    elif sub == "doctor":
        raw_report = reg.doctor()
        report = cast(dict[str, Any], raw_report) if isinstance(raw_report, dict) else {}
        for k, v in report.items():
            print(f"  {k}: {v}")
        return 0

    elif sub == "cleanup":
        raw_report = reg.cleanup()
        report = cast(dict[str, Any], raw_report) if isinstance(raw_report, dict) else {}
        removed = report.get("removed", 0)
        print(f"Cleanup complete: {removed} stale entries removed.")
        return 0

    elif sub == "update-all":
        raw_report = reg.update_all()
        report = cast(dict[str, Any], raw_report) if isinstance(raw_report, dict) else {}
        print(f"Updated {report.get('updated', 0)} projects.")
        return 0

    return 0


def handle_provider(args: argparse.Namespace) -> int:
    from workflow_runtime.application.knowledge.knowledge_api import sync
    sub = getattr(args, "subcommand", None)
    if sub == "list":
        print("Providers managed by new API (Markdown is default).")
        return 0
    elif sub == "sync":
        name = str(getattr(args, "name", None) or "obsidian")
        res = sync(name)
        print(f"Sync result for {name}: {res}")
        return 0 if res.get("status") == "success" else 1
    elif sub in ["config", "status"]:
        print(f"Provider {sub} not yet fully ported to DDD API. Check memory.config.json directly.")
        return 0
    return 1


def handle_visual(args: argparse.Namespace) -> int:
    """Route to ported VIR CLI."""
    try:
        from workflow_runtime.application.visual.core.cli import CLIRunner
        runner = CLIRunner()
        argv: list[str] = []
        mode_val = getattr(args, "mode", None)
        if mode_val:
            argv.extend(["--mode", str(mode_val)])
        feat_val = getattr(args, "feature_id", None)
        if feat_val:
            argv.extend(["--feature-id", str(feat_val)])
        if getattr(args, "ci", False):
            argv.append("--ci")

        subcmd_val = getattr(args, "subcommand", "")
        argv.append(str(subcmd_val))

        url_val = getattr(args, "url", None)
        if url_val:
            argv.extend(["--url", str(url_val)])
        goal_val = getattr(args, "goal", None)
        if goal_val:
            argv.extend(["--goal", str(goal_val)])
        iter_val = getattr(args, "max_iter", None)
        if iter_val:
            argv.extend(["--max-iter", str(iter_val)])
        return runner.main(argv)
    except Exception as e:
        print(f"[ERROR] visual: {e}", file=sys.stderr)
        return 1


__all__ = [
    "handle_notify",
    "handle_cleanup",
    "handle_verify",
    "handle_search",
    "handle_memory",
    "handle_state",
    "handle_telegram",
    "handle_registry",
    "handle_provider",
    "handle_visual",
]
