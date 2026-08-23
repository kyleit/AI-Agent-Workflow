from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, cast

from .common import get_project_root, log_info, log_warn, to_posix_path
from .config import get_memory_paths, load_memory_config
from .keyword_index import extract_keywords, search_in_markdown


class RAGSearcher:
    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or load_memory_config()
        self.paths = get_memory_paths(self.config)
        self.qdrant_url = "http://localhost:6333"

    def local_search(self, query: str) -> list[dict[str, Any]]:
        """Tìm kiếm từ khóa thô trên toàn bộ tệp markdown tri thức."""
        keywords = extract_keywords(query)
        if not keywords:
            return []

        results: list[dict[str, Any]] = []
        # Quét các file markdown chính trong memory_root
        mem_dir = str(self.paths.get("memory_root", ""))
        if os.path.exists(mem_dir):
            for root, _, files in os.walk(mem_dir):
                for file in files:
                    if file.endswith(".md"):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, get_project_root())
                        matches = search_in_markdown(full_path, keywords)
                        for m in matches:
                            m_dict = m
                            m_dict["file"] = to_posix_path(rel_path)
                            results.append(m_dict)

        # Sắp xếp kết quả theo score giảm dần
        results.sort(key=lambda x: cast(float, x.get("score", 0.0)), reverse=True)
        return results

    def vector_search(self, query: str) -> list[dict[str, Any]]:
        """Gọi API REST của Qdrant (full-text match hoặc dummy mock nếu không có embedding model)."""
        collection = str(self.config.get("vector_collection", "ai-skill-framework"))
        url = f"{self.qdrant_url}/collections/{collection}/points/scroll"

        keywords = extract_keywords(query)
        if not keywords:
            return []

        filter_conditions: list[dict[str, Any]] = []
        for kw in keywords:
            filter_conditions.append({
                "key": "text",
                "match": {"value": kw}
            })

        payload = {
            "filter": {
                "should": filter_conditions
            },
            "limit": 10,
            "with_payload": True
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode())
                points_list: list[dict[str, Any]] = []
                if isinstance(data, dict):
                    data_dict = cast(dict[str, Any], data)
                    res_obj = data_dict.get("result")
                    if isinstance(res_obj, dict):
                        res_dict = cast(dict[str, Any], res_obj)
                        raw_pts = res_dict.get("points")
                        if isinstance(raw_pts, list):
                            points_list = cast(list[dict[str, Any]], raw_pts)

                results: list[dict[str, Any]] = []
                for pt in points_list:
                    payload_data: dict[str, Any] = cast(dict[str, Any], pt.get("payload", {})) if isinstance(pt.get("payload"), dict) else {}
                    results.append({
                        "file": payload_data.get("file", "unknown.md"),
                        "text": payload_data.get("text", pt.get("id", "")),
                        "score": 10.0,
                        "type": "vector"
                    })
                return results
        except Exception as e:
            log_warn(f"Qdrant vector search failed: {e}. Falling back to local keyword search.")
            return []

    def execute_search(self, query: str) -> dict[str, Any]:
        log_info(f"Searching memory for: '{query}'")

        results = self.vector_search(query)
        retrieval_level = "Level 2 — Vector Search"

        if not results:
            results = self.local_search(query)
            retrieval_level = "Level 1 — Local Keyword Match"

        return {
            "status": "success",
            "query": query,
            "retrieval_level": retrieval_level,
            "results_count": len(results),
            "results": results[:5]
        }


__all__ = ["RAGSearcher"]

if __name__ == "__main__":
    import sys
    query_str = sys.argv[1] if len(sys.argv) > 1 else "session"
    searcher = RAGSearcher()
    res = searcher.execute_search(query_str)
    print(json.dumps(res, indent=2))
