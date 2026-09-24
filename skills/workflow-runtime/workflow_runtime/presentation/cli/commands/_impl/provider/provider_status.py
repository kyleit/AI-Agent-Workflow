"""Handlers: ``aiwf provider config`` / ``status`` and the unimplemented parser actions.

``config`` and ``status`` are the knowledge-provider commands documented in
``skills/knowledge-runtime/SKILL.md``; both read the effective (global + project,
``${VAR}``-expanded) configuration of ``.`` and print JSON.
"""
from __future__ import annotations

import json
import sys
from typing import Any

from workflow_runtime.infrastructure.knowledge import provider_manager

# Offered by the parser since the command-registry split (QUICK-039) but never
# implemented or specified anywhere; rejected instead of silently exiting 0.
UNSUPPORTED_ACTIONS: frozenset[str] = frozenset({"select", "usage", "reset"})


def _configured_names(project_root: str) -> list[str]:
    providers = provider_manager.resolve_all_providers(project_root).get("providers", {})
    return sorted(providers)


def show_provider_config(name: str | None, project_root: str = ".") -> int:
    """Print the effective, secret-masked config of ``name`` (or of every provider)."""
    if not name:
        print(json.dumps(provider_manager.list_providers(project_root), indent=2))
        return 0
    cfg = provider_manager.resolve_provider_config(name, project_root)
    if not cfg:
        print(json.dumps({"status": "failure", "message": f"Provider {name} is not configured."}, indent=2))
        return 1
    print(json.dumps(provider_manager.mask_secrets(cfg), indent=2))
    return 0


def _provider_status(name: str, project_root: str) -> dict[str, Any]:
    cfg = provider_manager.resolve_provider_config(name, project_root)
    check = provider_manager.test_provider(name, project_root)
    return {
        "name": name,
        "configured": bool(cfg),
        "enabled": bool(cfg.get("enabled", False)),
        "status": check["status"],
        "message": check["message"],
    }


def _is_unhealthy(entry: dict[str, Any]) -> bool:
    # A disabled provider is a valid, reported state; only a missing config or an
    # enabled provider failing its check is unhealthy.
    return not entry["configured"] or (entry["enabled"] and entry["status"] != "success")


def show_provider_status(name: str | None, project_root: str = ".") -> int:
    """Print health for ``name`` (or every configured provider); exit 1 if any is unhealthy."""
    if name:
        entry = _provider_status(name, project_root)
        print(json.dumps(entry, indent=2))
        return 1 if _is_unhealthy(entry) else 0
    entries = [_provider_status(n, project_root) for n in _configured_names(project_root)]
    print(json.dumps({"providers": entries}, indent=2))
    return 1 if any(_is_unhealthy(e) for e in entries) else 0


def reject_unsupported_action(action: str) -> int:
    print(f"aiwf provider {action}: not supported. `aiwf provider` manages knowledge "
          "providers (list, config, status, test, sync, add, edit, remove, enable, "
          "disable, resolve, path, doctor); for LLM token/cost usage use `aiwf usage`.",
          file=sys.stderr)
    return 2


__all__ = [
    "UNSUPPORTED_ACTIONS",
    "reject_unsupported_action",
    "show_provider_config",
    "show_provider_status",
]
