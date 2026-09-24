"""``aiwf provider test``: configuration and reachability checks per provider."""

from __future__ import annotations

import os
import socket
import urllib.request
from typing import Any

from workflow_runtime.infrastructure.knowledge.provider_manager.config import \
    resolve_provider_config
from workflow_runtime.infrastructure.knowledge.provider_manager.obsidian_folder import \
    resolve_obsidian_project_folder

_FILE_MODES: tuple[str, ...] = ("file-sync", "readonly", "bidirectional")


def _result(ok: bool, message: str) -> dict[str, Any]:
    return {"status": "success" if ok else "failure", "message": message}


def _check_obsidian(cfg: dict[str, Any], project_root: str) -> dict[str, Any]:
    try:
        path = resolve_obsidian_project_folder(project_root)
    except Exception as e:
        return _result(False, f"Obsidian folder resolution failed: {e}")

    mode = cfg.get("mode", "file-sync")
    if mode in _FILE_MODES:
        if os.path.isdir(path):
            return _result(True, f"Obsidian {mode} mode verified: vault exists at {path}.")
        return _result(False, f"Obsidian vault folder does not exist: {path}.")
    if mode == "rest":
        url = f"http://{cfg.get('host', '127.0.0.1')}:{cfg.get('port', 27124)}/"
        req = urllib.request.Request(url, method="GET")
        token = cfg.get("api_key", "")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if response.status == 200:
                    return _result(True, "Obsidian REST API verified successfully.")
                return _result(False, f"Obsidian REST API returned HTTP {response.status}.")
        except Exception as e:
            return _result(False, f"Failed to connect to Obsidian REST API: {e}")
    return _result(False, f"Unsupported Obsidian mode: {mode}.")


def _check_qdrant(cfg: dict[str, Any]) -> dict[str, Any]:
    host = cfg.get("host", "127.0.0.1")
    port = cfg.get("port", 6333)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)
            if sock.connect_ex((host, int(port))) == 0:
                return _result(True, f"Connected to Qdrant successfully at {host}:{port}.")
        return _result(False, f"Failed to connect to Qdrant at {host}:{port}.")
    except Exception as e:
        return _result(False, f"Qdrant connection error: {e}")


def _check_openai(cfg: dict[str, Any]) -> dict[str, Any]:
    if cfg.get("api_key", ""):
        return _result(True, "OpenAI provider API Key configured.")
    return _result(False, "OpenAI provider API Key is missing.")


def test_provider(name: str, project_root: str | None = ".") -> dict[str, Any]:
    """Return ``{"status": "success"|"failure", "message": ...}`` for provider ``name``."""
    project_root = project_root or "."
    cfg = resolve_provider_config(name, project_root)
    if not cfg:
        return _result(False, f"Provider {name} is not configured.")
    if not cfg.get("enabled", False):
        return _result(False, f"Provider {name} is disabled.")
    if name == "obsidian":
        return _check_obsidian(cfg, project_root)
    if name == "qdrant":
        return _check_qdrant(cfg)
    if name == "openai":
        return _check_openai(cfg)
    return _result(True, f"Provider {name} configuration checked.")


# Keep pytest from collecting this if a test module imports it by name.
test_provider.__test__ = False  # type: ignore[attr-defined]

__all__ = ["test_provider"]
