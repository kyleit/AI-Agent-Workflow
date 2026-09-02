from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GlobalInstallationSnapshot:
    available: bool
    source_path: str | None
    skills_path: str | None
    rules_path: str | None
    tools_path: str | None
    version: str | None
    asset_hashes: dict[str, str]
    required_runtime_assets: list[str]


DEFAULT_REQUIRED_RUNTIME_ASSETS = [
    "AI_RULES.md",
    "SKILLS.md",
    "skills/aiwf",
    "skills/initialize-workflow",
    "skills/workflow-coordinator",
    "skills/project-memory-bootstrap",
    "skills/project-memory-update",
    "skills/project-rag-search",
    "runtime",
    "skills/strict-code-block-gate",
    "contracts/engineering-quality-gates.yaml",
    "aiwf-hooks",
    "githooks",
    "aiwf_release",
]


def _hash_path(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.read_bytes())
    elif path.is_dir():
        for child in sorted(item for item in path.rglob("*") if item.is_file()):
            digest.update(child.relative_to(path).as_posix().encode("utf-8"))
            digest.update(child.read_bytes())
    return digest.hexdigest()


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


class GlobalInstallationInventory:
    def __init__(self, root: Path | str | None = None) -> None:
        self.root = Path(root).expanduser() if root else None

    def _resolve_root(self) -> Path | None:
        candidates = [
            self.root,
            Path(os.environ["AIWF_GLOBAL_ROOT"]) if os.environ.get("AIWF_GLOBAL_ROOT") else None,
            Path(os.environ["AIWF_FRAMEWORK_ROOT"]) if os.environ.get("AIWF_FRAMEWORK_ROOT") else None,
        ]
        for candidate in candidates:
            if candidate and candidate.exists():
                return candidate.resolve()
        return None

    def inspect(self) -> GlobalInstallationSnapshot:
        root = self._resolve_root()
        if root is None:
            return GlobalInstallationSnapshot(False, None, None, None, None, None, {}, [])
        skills = Path(os.environ.get("AIWF_GLOBAL_SKILLS_PATH", root / "skills"))
        rules = Path(os.environ.get("AIWF_GLOBAL_RULES_PATH", root / "AI_RULES.md"))
        tools = Path(os.environ.get("AIWF_GLOBAL_TOOLS_PATH", root / "tools"))
        manifest = _read_object(root / "MANIFEST.json")
        if not manifest:
            manifest = _read_object(root / ".agents" / "MANIFEST.json")
        raw_required = manifest.get("required_assets")
        required = [str(item) for item in raw_required if isinstance(item, str)] if isinstance(raw_required, list) else []
        if not required:
            required = list(DEFAULT_REQUIRED_RUNTIME_ASSETS)
        hashes: dict[str, str] = {}
        for label, path in (("skills", skills), ("rules", rules), ("tools", tools)):
            if path.exists():
                hashes[label] = _hash_path(path)
        for asset in required:
            source = self._asset_source(root, asset)
            if source.exists():
                hashes[asset] = _hash_path(source)
        version = manifest.get("version")
        return GlobalInstallationSnapshot(
            available=True,
            source_path=str(root),
            skills_path=str(skills) if skills.exists() else None,
            rules_path=str(rules) if rules.exists() else None,
            tools_path=str(tools) if tools.exists() else None,
            version=str(version) if version is not None else None,
            asset_hashes=hashes,
            required_runtime_assets=required,
        )

    @staticmethod
    def _asset_source(root: Path, asset: str) -> Path:
        direct = root / asset
        if direct.exists():
            return direct
        return root / ".agents" / asset


__all__ = [
    "DEFAULT_REQUIRED_RUNTIME_ASSETS",
    "GlobalInstallationInventory",
    "GlobalInstallationSnapshot",
]
