from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .common import to_posix_path, write_json_safe


FRESHNESS_STATES = {"CURRENT", "STALE", "UNVERIFIED"}


def is_non_source_drift(relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/").lstrip("./")
    return normalized.startswith((".agents/memory/", ".agents/runtime/", "docs/"))


@dataclass(frozen=True)
class ProjectContextManifest:
    schema_version: str
    project_id: str
    generated_at: str
    source_revision: str
    source_hashes: tuple[str, ...]
    summary_path: str
    architecture_paths: tuple[str, ...]
    entrypoints: tuple[str, ...]
    active_constraints: tuple[str, ...]
    known_blockers: tuple[str, ...]
    index_revision: str
    freshness: str
    retrieval_hints: tuple[str, ...]
    catalog_paths: tuple[str, ...] = ()
    catalog_counts: dict[str, int] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "generated_at": self.generated_at,
            "source_revision": self.source_revision,
            "source_hashes": list(self.source_hashes),
            "summary_path": self.summary_path,
            "architecture_paths": list(self.architecture_paths),
            "entrypoints": list(self.entrypoints),
            "active_constraints": list(self.active_constraints),
            "known_blockers": list(self.known_blockers),
            "index_revision": self.index_revision,
            "freshness": self.freshness,
            "retrieval_hints": list(self.retrieval_hints),
            "catalog_paths": list(self.catalog_paths),
            "catalog_counts": self.catalog_counts or {},
        }


def _relative_path(root: Path, path: str | os.PathLike[str]) -> str:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    return to_posix_path(str(candidate.resolve().relative_to(root.resolve())))


def _file_hash(root: Path, relative_path: str) -> str | None:
    path = root / Path(relative_path)
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_revision(root: Path) -> str:
    try:
        repository_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if Path(repository_root).resolve() != root.resolve():
            return "WORKTREE"
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "WORKTREE"


def build_context_manifest(
    project_id: str,
    source_revision: str,
    source_hashes: list[str],
    summary_path: str,
    architecture_paths: list[str],
    entrypoints: list[str],
    active_constraints: list[str],
    known_blockers: list[str],
    index_revision: str,
    freshness: str,
    retrieval_hints: list[str],
    generated_at: str,
    catalog_paths: list[str] | None = None,
    catalog_counts: dict[str, int] | None = None,
) -> ProjectContextManifest:
    paths = [summary_path, *architecture_paths, *entrypoints, *(catalog_paths or [])]
    if any(Path(path).is_absolute() or Path(path).drive for path in paths):
        raise ValueError("context paths must be repository-relative")
    if freshness not in FRESHNESS_STATES:
        raise ValueError("invalid context freshness")
    return ProjectContextManifest(
        schema_version="aiwf.project-context.v1",
        project_id=project_id,
        generated_at=generated_at,
        source_revision=source_revision,
        source_hashes=tuple(source_hashes),
        summary_path=summary_path,
        architecture_paths=tuple(architecture_paths),
        entrypoints=tuple(entrypoints),
        active_constraints=tuple(active_constraints),
        known_blockers=tuple(known_blockers),
        index_revision=index_revision,
        freshness=freshness,
        retrieval_hints=tuple(retrieval_hints),
        catalog_paths=tuple(catalog_paths or []),
        catalog_counts=catalog_counts or {},
    )


def build_project_context_manifest(
    root: Path,
    project_id: str,
    summary_path: str,
    architecture_paths: list[str],
    entrypoints: list[str],
    active_constraints: list[str],
    known_blockers: list[str],
    index_revision: str,
    retrieval_hints: list[str],
    generated_at: str,
    catalog_paths: list[str] | None = None,
    catalog_counts: dict[str, int] | None = None,
) -> ProjectContextManifest:
    relative_paths = [summary_path, *architecture_paths, *entrypoints, *(catalog_paths or [])]
    fingerprints: list[str] = []
    freshness = "CURRENT"
    for relative_path in relative_paths:
        digest = _file_hash(root, relative_path)
        if digest is None:
            freshness = "UNVERIFIED"
        else:
            fingerprints.append(f"{relative_path}={digest}")
    return build_context_manifest(
        project_id=project_id,
        source_revision=current_revision(root),
        source_hashes=fingerprints,
        summary_path=summary_path,
        architecture_paths=architecture_paths,
        entrypoints=entrypoints,
        active_constraints=active_constraints,
        known_blockers=known_blockers,
        index_revision=index_revision,
        freshness=freshness,
        retrieval_hints=retrieval_hints,
        generated_at=generated_at,
        catalog_paths=catalog_paths,
        catalog_counts=catalog_counts,
    )


def write_context_manifest(path: str | os.PathLike[str], manifest: ProjectContextManifest) -> None:
    write_json_safe(path, manifest.to_dict())


def load_context_manifest(path: str | os.PathLike[str]) -> dict[str, Any] | None:
    try:
        with open(path, "r", encoding="utf-8-sig") as stream:
            loaded = json.load(stream)
        return loaded if isinstance(loaded, dict) else None
    except (OSError, ValueError):
        return None


def manifest_freshness(root: Path, manifest: dict[str, Any] | None) -> str:
    if not manifest:
        return "UNVERIFIED"
    stored = manifest.get("source_hashes")
    if not isinstance(stored, list) or not stored:
        return "UNVERIFIED"
    if str(manifest.get("source_revision", "")) != current_revision(root):
        return "STALE"
    if str(manifest.get("source_revision", "")) != "WORKTREE":
        try:
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.splitlines()
            relevant_changes = [
                line for line in status
                if line[3:].strip().replace("\\", "/")
                and not is_non_source_drift(line[3:].strip())
            ]
            if relevant_changes:
                return "STALE"
        except (OSError, subprocess.CalledProcessError):
            # A standalone temp workspace can still be validated by file hashes.
            pass
    for item in stored:
        raw = str(item)
        if "=" not in raw:
            return "UNVERIFIED"
        relative_path, expected = raw.split("=", 1)
        current = _file_hash(root, relative_path)
        if current is None or current != expected:
            return "STALE"
    return "CURRENT"


__all__ = [
    "FRESHNESS_STATES",
    "ProjectContextManifest",
    "build_context_manifest",
    "build_project_context_manifest",
    "current_revision",
    "load_context_manifest",
    "manifest_freshness",
    "write_context_manifest",
]
