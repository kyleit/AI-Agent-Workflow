# vector_manifest.py
from __future__ import annotations

import json
import hashlib
import os
import re
from datetime import datetime
from typing import Any

from .common import to_posix_path


def chunk_markdown_file(file_path: str, content: str, source_revision: str = "WORKTREE") -> list[dict[str, Any]]:
    """Phân mảnh tệp markdown theo các tiêu đề ## để lưu trữ vector."""
    chunks: list[dict[str, Any]] = []
    source_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    sections = re.split(r"\n##\s+", content)

    intro = sections[0].strip()
    if intro:
        chunks.append({
            "id": stable_chunk_id(file_path, "intro", intro),
            "text": intro,
            "metadata": {
                "type": "documentation",
                "file": to_posix_path(file_path),
                "source_hash": source_hash,
                "source_revision": source_revision,
                "anchor": f"{to_posix_path(file_path)}:1",
                "tags": ["intro", "overview"]
            }
        })

    for idx, sec in enumerate(sections[1:]):
        lines = sec.splitlines()
        if not lines:
            continue
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()

        title_slug = re.sub(r"[^a-z0-9_-]", "", title.lower().replace(" ", "-"))

        chunks.append({
            "id": stable_chunk_id(file_path, title_slug or str(idx), body),
            "text": f"{title}\n{body}",
            "metadata": {
                "type": "documentation",
                "file": to_posix_path(file_path),
                "source_hash": source_hash,
                "source_revision": source_revision,
                "anchor": f"{to_posix_path(file_path)}:{content.find(body) + 1}",
                "tags": [title_slug, "section"]
            }
        })

    return chunks


def stable_chunk_id(source_path: str, section: str, content: str) -> str:
    normalized_path = to_posix_path(source_path).lstrip("./")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    return f"{normalized_path}:{section}:{digest}"


def write_vector_sync_plan(dest_path: str, collection: str, upserts: list[dict[str, Any]], deletes: list[str] | None = None) -> None:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    plan: dict[str, Any] = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "collection": collection,
        "upsert": upserts,
        "delete": [{"id": d_id} for d_id in (deletes or [])],
        "provider_contract": {
            "source_authority": "source files",
            "generated_index": True,
            "embedding_required": False,
        },
    }
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)


__all__ = ["chunk_markdown_file", "stable_chunk_id", "write_vector_sync_plan"]
