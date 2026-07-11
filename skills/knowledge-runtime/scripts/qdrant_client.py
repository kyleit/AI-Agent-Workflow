# qdrant_client.py
import urllib.request
import json
import warnings

class QdrantSearchClient:
    def __init__(self, url: str = "http://localhost:6333", api_key: str = None):
        self.url = url
        self.api_key = api_key
        self._available = False
        try:
            # Check availability
            req = urllib.request.Request(f"{url}/readyz", method="GET")
            if api_key:
                req.add_header("Authorization", f"Bearer {api_key}")
            with urllib.request.urlopen(req, timeout=1.0) as response:
                if response.status == 200:
                    self._available = True
        except Exception:
            warnings.warn("Qdrant service is not reachable.")

    def query_points(self, vector: list[float] = None, limit: int = 10, keywords: list[str] = None) -> list[str]:
        if not self._available:
            return []
        
        try:
            # Simulated or scroll lookup based on filters/payload match
            url = f"{self.url}/collections/ai-skill-framework/points/scroll"
            filter_conditions = []
            if keywords:
                for kw in keywords:
                    filter_conditions.append({
                        "key": "text",
                        "match": {"value": kw}
                    })
            
            payload = {
                "limit": limit,
                "with_payload": True
            }
            if filter_conditions:
                payload["filter"] = {"should": filter_conditions}
                
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            if self.api_key:
                req.add_header("Authorization", f"Bearer {self.api_key}")
                
            with urllib.request.urlopen(req, timeout=1.5) as response:
                resp = json.loads(response.read().decode("utf-8"))
                points = resp.get("result", {}).get("points", [])
                return [p.get("id") for p in points if p.get("id")]
        except Exception as e:
            warnings.warn(f"Qdrant query_points failed: {e}")
            return []

    def is_available(self) -> bool:
        return self._available
