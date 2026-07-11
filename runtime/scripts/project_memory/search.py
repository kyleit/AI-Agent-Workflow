# search.py
import os
import json
import sys
from common import log_info, log_warn, get_project_root, to_posix_path
from config import load_memory_config, get_memory_paths

# Add knowledge-runtime scripts path dynamically to sys.path
scripts_dir = os.path.abspath(os.path.join(get_project_root(), "skills", "knowledge-runtime", "scripts"))
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

class RAGSearcher:
    def __init__(self, config: dict = None):
        self.config = config or load_memory_config()
        self.paths = get_memory_paths(self.config)

    def execute_search(self, query: str) -> dict:
        log_info(f"Searching memory via Knowledge Runtime for: '{query}'")
        
        try:
            from knowledge_runtime import api as kr_api
            raw_results = kr_api.search(query, limit=5)
            results = []
            for r in raw_results:
                results.append({
                    "file": r.get("path", "unknown.md"),
                    "text": r.get("snippet", ""),
                    "score": r.get("score", 1.0)
                })
            retrieval_level = "Level 2 — Vector Search"
        except Exception as e:
            log_warn(f"Knowledge Runtime search failed: {e}. Falling back to workspace markdown scan.")
            try:
                from knowledge_runtime.providers.markdown import MarkdownProvider
                provider = MarkdownProvider(workspace_root=get_project_root())
                raw_results = provider.search(query, limit=5)
                results = []
                for r in raw_results:
                    results.append({
                        "file": r.get("path", "unknown.md"),
                        "text": r.get("snippet", ""),
                        "score": r.get("score", 0.5)
                    })
            except Exception as ex:
                log_warn(f"Fallback workspace search failed: {ex}")
                results = []
            retrieval_level = "Level 1 — Local Keyword Match"
            
        return {
            "status": "success",
            "query": query,
            "retrieval_level": retrieval_level,
            "results_count": len(results),
            "results": results[:5]
        }

if __name__ == "__main__":
    query_str = sys.argv[1] if len(sys.argv) > 1 else "session"
    searcher = RAGSearcher()
    res = searcher.execute_search(query_str)
    print(json.dumps(res, indent=2))
