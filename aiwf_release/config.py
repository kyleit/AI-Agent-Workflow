"""Load and validate release.config.json for the release engine.

The config is DECLARATIVE — it describes a project's release process; the engine
executes it. Missing optional sections get safe defaults so a minimal config
(just a pipeline) still works.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_NAME = "release.config.json"

# Step types the engine understands. Anything else is a config error.
KNOWN_STEPS = {
    "bump-version",
    "changelog",
    "run",
    "gate",
    "repo-release",
    "submodule-pointer",
}

DEFAULTS: dict[str, Any] = {
    "default_branch": "main",
    "remote_name": "origin",
    "version": {
        "strategy": "auto-conventional",  # or "manual"
        "source_of_truth": "MANIFEST.json#version",
        "files": ["MANIFEST.json#version"],
    },
    "changelog": {
        "dev": {"path": "CHANGELOG.md", "include": "all"},
        "product": None,  # optional
    },
    "gates": {"preflight": []},
    "pipeline": [],
    "receipt_dir": ".agents/state/release",
}


class ConfigError(Exception):
    pass


def _merge_defaults(cfg: dict[str, Any]) -> dict[str, Any]:
    out = json.loads(json.dumps(DEFAULTS))  # deep copy
    for k, v in cfg.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)
        else:
            out[k] = v
    return out


def load(root: Path) -> dict[str, Any]:
    """Load release.config.json from repo root (or .agents/ fallback)."""
    candidates = [root / CONFIG_NAME, root / ".agents" / CONFIG_NAME]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        raise ConfigError(
            f"{CONFIG_NAME} not found (looked in {', '.join(str(c) for c in candidates)})"
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as e:  # noqa: BLE001
        raise ConfigError(f"invalid {CONFIG_NAME}: {e}") from e
    if not isinstance(raw, dict):
        raise ConfigError(f"{CONFIG_NAME} must be a JSON object")
    cfg = _merge_defaults(raw)
    cfg["_config_path"] = str(path)
    validate(cfg)
    return cfg


def validate(cfg: dict[str, Any]) -> None:
    ver = cfg.get("version", {})
    if ver.get("strategy") not in ("auto-conventional", "manual"):
        raise ConfigError("version.strategy must be 'auto-conventional' or 'manual'")
    if not ver.get("files"):
        raise ConfigError("version.files must list at least one version file")
    if not ver.get("source_of_truth"):
        raise ConfigError("version.source_of_truth is required")

    pipeline = cfg.get("pipeline") or []
    if not isinstance(pipeline, list) or not pipeline:
        raise ConfigError("pipeline must be a non-empty array")
    for i, step in enumerate(pipeline):
        if not isinstance(step, dict) or "step" not in step:
            raise ConfigError(f"pipeline[{i}] must be an object with a 'step' key")
        name = step["step"]
        if name not in KNOWN_STEPS:
            raise ConfigError(
                f"pipeline[{i}] unknown step '{name}' (known: {sorted(KNOWN_STEPS)})"
            )
        if name in ("run", "gate") and not step.get("cmd"):
            raise ConfigError(f"pipeline[{i}] step '{name}' requires 'cmd'")
        if name in ("repo-release", "submodule-pointer") and not step.get("path"):
            raise ConfigError(f"pipeline[{i}] step '{name}' requires 'path'")


def parse_file_ref(ref: str) -> tuple[str, str | None]:
    """'MANIFEST.json#version' -> ('MANIFEST.json', 'version'); 'VERSION' -> ('VERSION', None)."""
    if "#" in ref:
        path, key = ref.split("#", 1)
        return path, key
    return ref, None
