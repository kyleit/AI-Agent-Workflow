# search.py
import os
import json
import urllib.request
import urllib.error
from common import log_info, log_warn, get_project_root, to_posix_path
from config import load_memory_config, get_memory_paths
from keyword_index import extract_keywords, search_in_markdown

class RAGSearcher:
    def __init__(self, config: dict = None):
        self.config = config or load_memory_config()
        self.paths = get_memory_paths(self.config)
        self.qdrant_url = "http://localhost:6333"

    def local_search(self, query: str) -> list[dict]:
        """Tìm kiếm từ khóa thô trên toàn bộ tệp markdown tri thức."""
        keywords = extract_keywords(query)
        if not keywords:
            return []
            
        results = []
        # Quét các file markdown chính trong memory_root
        mem_dir = self.paths["memory_root"]
        if os.path.exists(mem_dir):
            for root, _, files in os.walk(mem_dir):
                for file in files:
                    if file.endswith(".md"):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, get_project_root())
                        matches = search_in_markdown(full_path, keywords)
                        for m in matches:
                            m["file"] = to_posix_path(rel_path)
                            results.append(m)
                            
        # Sắp xếp kết quả theo score giảm dần
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def vector_search(self, query: str) -> list[dict]:
        """Gọi API REST của Qdrant (full-text match hoặc dummy mock nếu không có embedding model)."""
        collection = self.config.get("vector_collection", "ai-skill-framework")
        url = f"{self.qdrant_url}/collections/{collection}/points/scroll"
        
        # Vì sinh embedding đòi hỏi API key và mô hình ngoài, ta sử dụng API scroll/search 
        # kết hợp với filter từ khóa để giả lập tìm kiếm trong Qdrant
        keywords = extract_keywords(query)
        if not keywords:
            return []
            
        filter_conditions = []
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
                points = data.get("result", {}).get("points", [])
                
                results = []
                for pt in points:
                    payload_data = pt.get("payload", {})
                    results.append({
                        "file": payload_data.get("file", "unknown.md"),
                        "text": payload_data.get("text", pt.get("id")),
                        "score": 10.0,  # Score mặc định cho matched points
                        "type": "vector"
                    })
                return results
        except Exception as e:
            # Fallback thầm lặng sang local search nếu Qdrant offline hoặc API lỗi
            log_warn(f"Qdrant vector search failed: {e}. Falling back to local keyword search.")
            return []

    def execute_search(self, query: str) -> dict:
        log_info(f"Searching memory for: '{query}'")
        
        # Thử tìm kiếm vector
        results = self.vector_search(query)
        retrieval_level = "Level 2 — Vector Search"
        
        # Nếu không có kết quả từ vector, fallback sang local search
        if not results:
            results = self.local_search(query)
            retrieval_level = "Level 1 — Local Keyword Match"
            
        return {
            "status": "success",
            "query": query,
            "retrieval_level": retrieval_level,
            "results_count": len(results),
            "results": results[:5]  # Giới hạn 5 kết quả hàng đầu
        }

if __name__ == "__main__":
    import sys
    query_str = sys.argv[1] if len(sys.argv) > 1 else "session"
    searcher = RAGSearcher()
    res = searcher.execute_search(query_str)
    print(json.dumps(res, indent=2))
