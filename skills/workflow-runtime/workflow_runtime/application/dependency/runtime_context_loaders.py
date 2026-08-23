"""
workflow_runtime/application/dependency/runtime_context_loaders.py

Cached and lazy context loaders for memory, RAG, version, provider, and usage state.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Optional, cast

from workflow_runtime.application.dependency.dependency_models import (
    DependencyResult)

_STATE_DIR = os.path.join(".agents", "state")
CONTEXT_PATH = os.path.join(_STATE_DIR, "context.json")
DASHBOARD_PATH = os.path.join(_STATE_DIR, "dashboard.json")


def _read_json_safe(file_path: str) -> dict[str, Any]:
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cast(dict[str, Any], data) if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_memory_cached() -> DependencyResult:
    state_file = os.path.join(".agents", "memory", "memory-state.json")
    config_file = os.path.join(".agents", "memory.config.json")

    if os.path.exists(state_file) or os.path.exists(config_file):
        data: dict[str, Any] = {}
        if os.path.exists(state_file):
            data["state"] = _read_json_safe(state_file)
        if os.path.exists(config_file):
            data["config"] = _read_json_safe(config_file)
        return DependencyResult(name="memory", mode="cached", status="cached", source="memory-state.json", action="ok", data=data)

    return DependencyResult(name="memory", mode="cached", status="missing", source="memory-state.json not found", action="warn_only")


def load_memory_lazy(query: Optional[str] = None) -> DependencyResult:
    if query is None:
        return DependencyResult(name="memory", mode="lazy", status="deferred", source="no-query", action="defer")
    return DependencyResult(name="memory", mode="lazy", status="deferred", source=f"query={query[:50]}", action="defer")


def load_rag_cached() -> DependencyResult:
    rag_metadata = os.path.join(".agents", "rag", "rag-state.json")
    if os.path.exists(rag_metadata):
        data = _read_json_safe(rag_metadata)
        return DependencyResult(name="rag", mode="cached", status="cached", source=rag_metadata, action="ok", data=data)
    return DependencyResult(name="rag", mode="cached", status="missing", source="rag-state.json not found", action="warn_only")


def load_rag_lazy(query: Optional[str] = None) -> DependencyResult:
    if query is None:
        return DependencyResult(name="rag", mode="lazy", status="deferred", source="no-query", action="defer")
    return DependencyResult(name="rag", mode="lazy", status="deferred", source=f"query={query[:50]}", action="defer")


def load_version_cached() -> DependencyResult:
    context = _read_json_safe(CONTEXT_PATH)
    version = context.get("project_version") or context.get("version")
    if version:
        return DependencyResult(name="version", mode="cached", status="cached", source=CONTEXT_PATH, action="ok", data={"version": version})
    return DependencyResult(name="version", mode="cached", status="missing", source="project_version not in context.json", action="warn_only")


def load_provider_cached() -> DependencyResult:
    context = _read_json_safe(CONTEXT_PATH)
    provider = context.get("provider") or context.get("ai_provider")
    if provider:
        return DependencyResult(name="provider", mode="cached", status="cached", source=CONTEXT_PATH, action="ok", data={"provider": provider})

    dashboard = _read_json_safe(DASHBOARD_PATH)
    provider = dashboard.get("provider") or dashboard.get("ai_provider")
    if provider:
        return DependencyResult(name="provider", mode="cached", status="cached", source=DASHBOARD_PATH, action="ok", data={"provider": provider})

    return DependencyResult(name="provider", mode="optional", status="missing", source="provider not in context/dashboard", action="warn_only")


def load_usage_cached() -> DependencyResult:
    usage_file = os.path.join(_STATE_DIR, "context", "usage.json")
    if os.path.exists(usage_file):
        data = _read_json_safe(usage_file)
        if data:
            return DependencyResult(name="usage", mode="cached", status="cached", source=usage_file, action="ok", data=data)

    usage_root = os.path.join(_STATE_DIR, "usage.json")
    if os.path.exists(usage_root):
        data = _read_json_safe(usage_root)
        if data:
            return DependencyResult(name="usage", mode="cached", status="cached", source=usage_root, action="ok", data=data)

    dashboard = _read_json_safe(DASHBOARD_PATH)
    usage_in_dash = dashboard.get("usage") or dashboard.get("context_usage")
    if usage_in_dash:
        return DependencyResult(name="usage", mode="cached", status="cached", source=DASHBOARD_PATH, action="ok", data=cast(dict[str, Any], usage_in_dash))

    return DependencyResult(name="usage", mode="cached", status="missing", source="usage not found in state", action="warn_only")


def _resolve_version_cached(skill_name: str, mode: str) -> DependencyResult:
    _ = skill_name
    context = _read_json_safe(CONTEXT_PATH)
    version_data: dict[str, Any] = cast(dict[str, Any], context.get("version", {})) if isinstance(context.get("version"), dict) else {}
    if version_data:
        return DependencyResult(name="version", mode=mode, status="cached", source=CONTEXT_PATH, action="ok", data=version_data)
    return DependencyResult(name="version", mode=mode, status="missing", source=CONTEXT_PATH, action="warn_only" if mode != "required" else "fail")


def _resolve_provider_cached(skill_name: str, mode: str) -> DependencyResult:
    _ = skill_name
    context = _read_json_safe(CONTEXT_PATH)
    provider_data: dict[str, Any] = cast(dict[str, Any], context.get("provider", {})) if isinstance(context.get("provider"), dict) else {}
    if provider_data:
        return DependencyResult(name="provider", mode=mode, status="cached", source=CONTEXT_PATH, action="ok", data=provider_data)
    return DependencyResult(name="provider", mode=mode, status="missing", source=CONTEXT_PATH, action="warn_only" if mode != "required" else "fail")


def _resolve_usage_cached(skill_name: str, mode: str) -> DependencyResult:
    _ = skill_name
    context = _read_json_safe(CONTEXT_PATH)
    usage_data: dict[str, Any] = cast(dict[str, Any], context.get("usage", {})) if isinstance(context.get("usage"), dict) else {}
    if usage_data:
        return DependencyResult(name="usage", mode=mode, status="cached", source=CONTEXT_PATH, action="ok", data=usage_data)
    return DependencyResult(name="usage", mode=mode, status="missing", source=CONTEXT_PATH, action="warn_only" if mode != "required" else "fail")


__all__ = [
    "load_memory_cached",
    "load_memory_lazy",
    "load_rag_cached",
    "load_rag_lazy",
    "load_version_cached",
    "load_provider_cached",
    "load_usage_cached",
    "_resolve_version_cached",
    "_resolve_provider_cached",
    "_resolve_usage_cached",
]
