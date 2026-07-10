import urllib.request
import json
import warnings
from .base import BaseProvider

class VectorDBProvider(BaseProvider):
    def __init__(self, host: str = "localhost", port: int = 6333, collection_name: str = "knowledge"):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self._url = f"http://{host}:{port}/collections/{collection_name}"
        self._available = False
        try:
            # Quick check if Qdrant is responsive
            req = urllib.request.Request(f"http://{host}:{port}/readyz", method="GET")
            with urllib.request.urlopen(req, timeout=1.0) as response:
                if response.status == 200:
                    self._available = True
        except Exception:
            warnings.warn("Qdrant Vector DB is not available or not running. Semantic search will be disabled.")

    def search(self, query: str, limit: int = 5) -> list[dict]:
        if not self._available:
            return []
        
        results = []
        try:
            # Dummy embedding and query to Qdrant REST API (for demonstration/mocking Qdrant scroll)
            url = f"{self._url}/points/scroll"
            data = json.dumps({"limit": limit}).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=1.5) as response:
                resp = json.loads(response.read().decode("utf-8"))
                for record in resp.get("result", {}).get("points", []):
                    payload = record.get("payload", {})
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
