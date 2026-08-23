# vector_manifest.py
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any

from .common import to_posix_path


def chunk_markdown_file(file_path: str, content: str) -> list[dict[str, Any]]:
    """Phân mảnh tệp markdown theo các tiêu đề ## để lưu trữ vector."""
    chunks: list[dict[str, Any]] = []
    basename = os.path.basename(file_path)
    file_id = os.path.splitext(basename)[0]

    sections = re.split(r"\n##\s+", content)

    intro = sections[0].strip()
    if intro:
        chunks.append({
            "id": f"{file_id}-intro",
            "text": intro,
            "metadata": {
                "type": "documentation",
                "file": to_posix_path(file_path),
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
            "id": f"{file_id}-{title_slug or idx}",
            "text": f"{title}\n{body}",
            "metadata": {
                "type": "documentation",
                "file": to_posix_path(file_path),
                "tags": [title_slug, "section"]
            }
        })

    return chunks


def write_vector_sync_plan(dest_path: str, collection: str, upserts: list[dict[str, Any]], deletes: list[str] | None = None) -> None:
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    plan: dict[str, Any] = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "collection": collection,
        "upsert": upserts,
        "delete": [{"id": d_id} for d_id in (deletes or [])]
    }
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)


__all__ = ["chunk_markdown_file", "write_vector_sync_plan"]
