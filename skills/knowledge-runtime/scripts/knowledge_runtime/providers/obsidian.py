import urllib.request
import json
import warnings
from .base import BaseProvider

class ObsidianProvider(BaseProvider):
    def __init__(self, port: int = 27124, token: str = ""):
        self.port = port
        self.token = token
        self._url = f"http://127.0.0.1:{port}"
        self._available = False
        try:
            # Check Obsidian REST API availability
            req = urllib.request.Request(f"{self._url}/", method="GET")
            if token:
                req.add_header("Authorization", f"Bearer {token}")
            with urllib.request.urlopen(req, timeout=1.0) as response:
                if response.status == 200:
                    self._available = True
        except Exception:
            warnings.warn("Obsidian Local API is not available or not running. Obsidian sync will be disabled.")

    def search(self, query: str, limit: int = 5) -> list[dict]:
        if not self._available:
            return []
        
        results = []
        try:
            url = f"{self._url}/search"
            data = json.dumps({"query": query}).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            if self.token:
                req.add_header("Authorization", f"Bearer {self.token}")
            with urllib.request.urlopen(req, timeout=1.5) as response:
                resp = json.loads(response.read().decode("utf-8"))
                for item in resp:
                    results.append({
                        "path": item.get("filename", ""),
                        "snippet": item.get("match", ""),
                        "score": 0.85
                    })
        except Exception as e:
            warnings.warn(f"Obsidian search failed: {e}")
            
        return results[:limit]

    def read(self, path: str) -> str:
        if not self._available:
            raise ConnectionError("Obsidian not available.")
        try:
            req = urllib.request.Request(f"{self._url}/vault/{path}", method="GET")
            if self.token:
                req.add_header("Authorization", f"Bearer {self.token}")
            with urllib.request.urlopen(req) as response:
                return response.read().decode("utf-8")
        except Exception as e:
            raise IOError(f"Failed to read Obsidian note: {e}")

    def save(self, path: str, content: str) -> bool:
        if not self._available:
            return False
        try:
            req = urllib.request.Request(f"{self._url}/vault/{path}", data=content.encode("utf-8"), method="PUT")
            if self.token:
                req.add_header("Authorization", f"Bearer {self.token}")
            with urllib.request.urlopen(req) as response:
                return response.status == 200
        except Exception as e:
            warnings.warn(f"Obsidian save failed: {e}")
            return False

    def is_available(self) -> bool:
        return self._available
