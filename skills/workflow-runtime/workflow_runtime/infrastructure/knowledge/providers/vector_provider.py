import json
import urllib.request
import warnings
from typing import Any, cast

from workflow_runtime.domain.knowledge.interfaces import IKnowledgeProvider


class VectorDBProvider(IKnowledgeProvider):
    def __init__(self, host: str = "localhost", port: int = 6333, collection_name: str = "knowledge"):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self._url = f"http://{host}:{port}/collections/{collection_name}"
        self._available = False
        self._health: dict[str, Any] = {
            "provider": "qdrant", "state": "UNAVAILABLE", "index_path": "",
            "collection": collection_name, "document_count": 0, "chunk_count": 0,
            "embedding_status": "unknown", "reason": "not checked",
        }
        try:
            req = urllib.request.Request(self._url, method="GET")
            with urllib.request.urlopen(req, timeout=1.0) as response:
                data = json.loads(response.read().decode("utf-8"))
            result = data.get("result", {}) if isinstance(data, dict) else {}
            vectors = result.get("config", {}).get("params", {}).get("vectors", {}) if isinstance(result, dict) else {}
            points = result.get("points_count", result.get("vectors_count", 0)) if isinstance(result, dict) else 0
            if isinstance(vectors, dict) and int(points or 0) > 0:
                self._available = True
                self._health.update({"state": "READY", "document_count": int(points), "chunk_count": int(points), "embedding_status": "ready", "reason": "validated collection and vector count"})
            else:
                self._health.update({"state": "DEGRADED", "embedding_status": "invalid", "reason": "collection exists but has no validated vectors"})
        except Exception as exc:
            self._health["reason"] = str(exc)
            warnings.warn("Qdrant Vector DB is not available or not running. Semantic search will be disabled.")

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if not self._available:
            return []

        results: list[dict[str, Any]] = []
        try:
            # Dummy embedding and query to Qdrant REST API (for demonstration/mocking Qdrant scroll)
            url = f"{self._url}/points/scroll"
            data = json.dumps({"limit": limit}).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=1.5) as response:
                resp = json.loads(response.read().decode("utf-8"))
                for record in resp.get("result", {}).get("points", []):
                    payload: dict[str, Any] = cast(dict[str, Any], record.get("payload", {})) if isinstance(record.get("payload"), dict) else {}
                    results.append({
                        "path": payload.get("path", ""),
                        "snippet": payload.get("content", "")[:120],
                        "score": 0.9
                    })
        except Exception as e:
            warnings.warn(f"Vector search failed: {e}")

        return results

    def read(self, path: str) -> str:
        raise NotImplementedError("Use MarkdownProvider for file reading.")

    def save(self, path: str, content: str) -> bool:
        return False

    def is_available(self) -> bool:
        return self._available

    def health(self) -> dict[str, Any]:
        return dict(self._health)
