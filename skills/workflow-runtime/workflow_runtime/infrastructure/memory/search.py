from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any, cast

from .common import log_info, log_warn, read_text_safe, to_posix_path
from .config import get_memory_paths, load_memory_config
from .context_manifest import load_context_manifest, manifest_freshness
from .keyword_index import extract_keywords, search_in_markdown


class RAGSearcher:
    """Project-scoped retrieval router with truthful provider health and evidence."""

    def __init__(self, config: dict[str, Any] | None = None, root_dir: str | os.PathLike[str] | None = None):
        self.root_dir = Path(root_dir or os.getcwd()).resolve()
        self.config = config or load_memory_config(root_dir=str(self.root_dir))
        self.paths = get_memory_paths(self.config, root_dir=str(self.root_dir))
        self.qdrant_url = str(self.config.get("qdrant_url", "http://localhost:6333")).rstrip("/")
        self.collection = str(self.config.get("vector_collection", self.config.get("project_id", "ai-skill-framework")))
        self.qmd_timeout = max(1, int(self.config.get("qmd_timeout_seconds", 3)))
        self._cached_revision: str | None = None
        self._cached_freshness: str | None = None

    def _revision(self) -> str:
        if self._cached_revision is not None:
            return self._cached_revision
        from .context_manifest import current_revision
        self._cached_revision = current_revision(self.root_dir)
        return self._cached_revision

    def _freshness(self) -> str:
        if self._cached_freshness is not None:
            return self._cached_freshness
        self._cached_freshness = manifest_freshness(
            self.root_dir,
            load_context_manifest(self.root_dir / ".agents" / "memory" / "project-context.json"),
        )
        return self._cached_freshness

    def _health(self, provider: str, state: str, reason: str, *, index_path: str = "", collection: str = "", document_count: int = 0, chunk_count: int = 0, embedding_status: str = "not_required") -> dict[str, Any]:
        return {
            "provider": provider, "state": state, "index_path": index_path,
            "collection": collection, "document_count": document_count,
            "chunk_count": chunk_count, "embedding_status": embedding_status,
            "reason": reason,
        }

    def _run_qmd_cli(self, arguments: list[str]) -> tuple[int, str, str]:
        """Run qmd without leaving its Python child behind on timeout."""
        executable = shutil.which("qmd")
        if not executable:
            return (127, "", "qmd executable is not installed")
        process: subprocess.Popen[str] | None = None
        try:
            process = subprocess.Popen(
                [executable, "--db-path", str(self.paths.get("qmd_index", "")), *arguments],
                cwd=self.root_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace",
            )
            stdout, stderr = process.communicate(timeout=self.qmd_timeout)
            return (int(process.returncode or 0), stdout, stderr)
        except subprocess.TimeoutExpired:
            if process is not None:
                try:
                    if os.name == "nt":
                        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, timeout=2)
                    else:
                        process.kill()
                except (OSError, subprocess.TimeoutExpired):
                    pass
            return (124, "", "qmd command timed out")
        except OSError as exc:
            return (1, "", str(exc))

    def _qmd_runtime_reason(self) -> str | None:
        """Return a deterministic compatibility reason before spawning qmd."""
        if sys.version_info >= (3, 14) and os.environ.get("AIWF_QMD_FORCE", "").lower() not in {"1", "true", "yes"}:
            return "qmd embedding runtime is not compatible with Python 3.14; SQLite fallback is active"
        return None

    def _qmd_health(self) -> dict[str, Any]:
        index_path = str(self.paths.get("qmd_index", ""))
        if not shutil.which("qmd"):
            return self._health("qmd", "UNAVAILABLE", "qmd executable is not installed", index_path=index_path, collection=self.collection)
        compatibility_reason = self._qmd_runtime_reason()
        if compatibility_reason:
            return self._health("qmd", "UNAVAILABLE", compatibility_reason, index_path=index_path, collection=self.collection)
        if not os.path.isfile(index_path):
            return self._health("qmd", "DEGRADED", "project-scoped qmd index is missing", index_path=index_path, collection=self.collection)
        try:
            code, stdout, stderr = self._run_qmd_cli(["collection", "list"])
            if code != 0:
                return self._health("qmd", "DEGRADED", stderr.strip() or "qmd health check failed", index_path=index_path, collection=self.collection)
            collections: Any = json.loads(stdout or "[]")
            info = next((item for item in collections if isinstance(item, dict) and item.get("name") == self.collection), None)
            if info is None:
                return self._health("qmd", "DEGRADED", "project collection is missing", index_path=index_path, collection=self.collection)
            document_count = int(info.get("document_count", 0) or 0)
            chunk_count = int(info.get("chunk_count", 0) or 0)
            if not document_count or not chunk_count:
                return self._health(
                    "qmd", "DEGRADED", "QMD is installed but the project collection is empty; SQLite fallback is active",
                    index_path=index_path, collection=self.collection,
                    document_count=document_count, chunk_count=chunk_count,
                    embedding_status="empty",
                )
            return self._health(
                "qmd", "READY", "validated project collection and embeddings",
                index_path=index_path, collection=self.collection,
                document_count=document_count, chunk_count=chunk_count,
                embedding_status="ready",
            )
        except (OSError, TypeError, ValueError) as exc:
            return self._health("qmd", "DEGRADED", str(exc), index_path=index_path, collection=self.collection)

    def _index_signature(self) -> str:
        digest = hashlib.sha256()
        for path in self._index_files():
            stat = path.stat()
            digest.update(f"{path.relative_to(self.root_dir).as_posix()}:{stat.st_mtime_ns}:{stat.st_size}".encode())
        return digest.hexdigest()

    def _index_files(self) -> list[Path]:
        """Return generated memory plus current source files for local RAG."""
        memory_root = Path(str(self.paths["memory_root"]))
        index_path = Path(str(self.paths.get("qmd_index", ""))).resolve()
        index_key = os.path.normcase(os.path.abspath(str(index_path)))
        volatile_memory_files = {"memory-state.json"}
        extensions = {
            ".c", ".cc", ".cpp", ".cs", ".css", ".dart", ".go", ".h",
            ".hpp", ".html", ".java", ".js", ".json", ".jsx", ".kt",
            ".md", ".php", ".py", ".rb", ".rs", ".sql", ".svelte",
            ".swift", ".toml", ".ts", ".tsx", ".txt", ".xml", ".yaml",
            ".yml",
        }
        excluded = {
            ".git", ".hg", ".svn", ".venv", "__pycache__", ".pytest_cache",
            ".mypy_cache", ".ruff_cache", "node_modules", "dist", "build",
            "target", "artifacts", "scratch", "_to_delete", "public_export",
        }
        max_bytes = max(16_000, int(self.config.get("max_index_file_bytes", 1_000_000)))
        files: set[Path] = set()
        for path in memory_root.rglob("*"):
            if (
                path.is_file()
                and path.resolve() != index_path
                and path.suffix.lower() in {".md", ".json", ".txt"}
                and path.name not in volatile_memory_files
                and not path.name.startswith("qmd.index")
                and path.stat().st_size <= max_bytes
            ):
                files.add(path)
        candidates: list[Path]
        # Git already knows the project boundary and ignore rules. Using its
        # file list avoids a full recursive filesystem walk on every AI entry
        # request, while still including untracked source files.
        if (self.root_dir / ".git").exists() or (self.root_dir / ".git" ).is_file():
            try:
                listed = subprocess.run(
                    ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                    cwd=self.root_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, encoding="utf-8", errors="replace", check=False,
                )
                candidates = [self.root_dir / line.strip() for line in listed.stdout.splitlines() if line.strip()]
            except OSError:
                candidates = list(self.root_dir.rglob("*"))
        else:
            try:
                listed = subprocess.run(
                    ["rg", "--files", "--hidden", "--glob", "!.git/**", "--glob", "!node_modules/**"],
                    cwd=self.root_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                    timeout=5,
                )
                candidates = [self.root_dir / line.strip() for line in listed.stdout.splitlines() if line.strip()]
            except (OSError, subprocess.TimeoutExpired):
                candidates = list(self.root_dir.rglob("*"))
        for path in candidates:
            try:
                stat = path.stat()
            except OSError:
                continue
            if path.suffix.lower() not in extensions:
                continue
            if (
                os.path.normcase(os.path.abspath(str(path))) == index_key
                or stat.st_size > max_bytes
                or any(part in excluded for part in path.parts)
            ):
                continue
            files.add(path)
        return sorted(files)

    def _query_source_files(self, files: list[Path], query: str) -> set[Path]:
        """Find source files relevant to a first query without reading every file."""
        keywords = extract_keywords(query)
        if not keywords:
            return set()
        candidate_map = {
            os.path.normcase(os.path.abspath(str(path))): path
            for path in files
            if ".agents" not in path.parts
        }
        if not candidate_map:
            return set()
        pattern = "|".join(re.escape(term) for term in keywords[:8])
        try:
            result = subprocess.run(
                ["rg", "-l", "-i", "--hidden", "--glob", "!.git/**", "--glob", "!node_modules/**", pattern, "."],
                cwd=self.root_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired):
            return {
                path for path in files
                if path.name.lower() in {f"{term.lower()}.py" for term in keywords}
            }
        matches: set[Path] = set()
        for raw_path in result.stdout.splitlines():
            candidate = self.root_dir / raw_path.strip()
            mapped = candidate_map.get(os.path.normcase(os.path.abspath(str(candidate))))
            if mapped is not None:
                matches.add(mapped)
        return matches

    def _current_index_metadata(self, files: list[Path]) -> dict[str, tuple[int, int]]:
        """Capture cheap file fingerprints used for incremental index updates."""
        metadata: dict[str, tuple[int, int]] = {}
        for path in files:
            try:
                stat = path.stat()
            except OSError:
                continue
            relative = to_posix_path(os.path.relpath(path, self.root_dir))
            metadata[relative] = (int(stat.st_mtime_ns), int(stat.st_size))
        return metadata

    def _index_file(
        self,
        conn: sqlite3.Connection,
        path: Path,
        revision: str,
        freshness: str,
    ) -> None:
        """Replace one file's chunks while keeping all other indexed source intact."""
        relative = to_posix_path(os.path.relpath(path, self.root_dir))
        conn.execute("DELETE FROM memory_chunks_fts WHERE file = ?", (relative,))
        content = read_text_safe(path)
        if not content:
            return
        source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        lines = content.splitlines()
        for offset in range(0, len(lines), 60):
            chunk = "\n".join(lines[offset:offset + 60]).strip()
            if not chunk:
                continue
            anchor = f"{relative}:{offset + 1}"
            chunk_id = hashlib.sha256(f"{anchor}:{source_hash}".encode()).hexdigest()[:24]
            conn.execute(
                "INSERT INTO memory_chunks_fts(chunk_id,file,anchor,text,source_hash,source_revision,freshness) VALUES(?,?,?,?,?,?,?)",
                (chunk_id, relative, anchor, chunk, source_hash, revision, freshness),
            )

    def _ensure_sqlite_index(self, query: str = "") -> dict[str, Any]:
        index_path = Path(str(self.paths.get("qmd_index")))
        index_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(index_path)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("CREATE TABLE IF NOT EXISTS memory_index_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            files = self._index_files()
            current_metadata = self._current_index_metadata(files)
            signature = hashlib.sha256(
                "".join(f"{name}:{mtime}:{size}" for name, (mtime, size) in sorted(current_metadata.items())).encode()
            ).hexdigest()
            existing = conn.execute("SELECT value FROM memory_index_meta WHERE key = 'signature'").fetchone()
            root_identity = os.path.normcase(str(self.root_dir.resolve()))
            existing_root = conn.execute("SELECT value FROM memory_index_meta WHERE key = 'root_identity'").fetchone()
            conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS memory_chunks_fts USING fts5(chunk_id UNINDEXED, file, anchor, text, source_hash, source_revision, freshness)")
            conn.execute("CREATE TABLE IF NOT EXISTS memory_index_files (file TEXT PRIMARY KEY, mtime_ns INTEGER NOT NULL, size INTEGER NOT NULL)")
            stored_rows = conn.execute("SELECT file,mtime_ns,size FROM memory_index_files").fetchall()
            stored_metadata = {
                str(row[0]): (int(row[1]), int(row[2]))
                for row in stored_rows
            }
            if not existing_root or str(existing_root[0]) != root_identity:
                # An index is project-scoped. A copied or legacy index must not
                # trigger a cross-project full rebuild or leak stale chunks.
                conn.execute("DELETE FROM memory_chunks_fts")
                conn.execute("DELETE FROM memory_index_files")
                stored_rows = []
                stored_metadata = {}
                existing = None
            revision = self._revision()
            freshness = self._freshness()
            signature_matches = bool(existing and str(existing[0]) == signature)
            if not stored_rows and signature_matches:
                # Older indexes have a global signature but no file manifest.
                # Adopt them without the expensive full source re-read.
                for name, (mtime, size) in current_metadata.items():
                    conn.execute("INSERT OR REPLACE INTO memory_index_files(file,mtime_ns,size) VALUES(?,?,?)", (name, mtime, size))
            elif not signature_matches:
                if not stored_rows:
                    # One-time migration for indexes created before the per-file
                    # manifest existed. Future calls update only changed files.
                    conn.execute("DELETE FROM memory_chunks_fts")
                    stored_metadata = {}
                changed_files = {
                    name for name, fingerprint in current_metadata.items()
                    if stored_metadata.get(name) != fingerprint
                }
                removed_files = set(stored_metadata) - set(current_metadata)
                for name in removed_files:
                    conn.execute("DELETE FROM memory_chunks_fts WHERE file = ?", (name,))
                    conn.execute("DELETE FROM memory_index_files WHERE file = ?", (name,))
                path_by_name = {
                    to_posix_path(os.path.relpath(path, self.root_dir)): path
                    for path in files
                }
                indexed_files = {
                    str(row[0])
                    for row in conn.execute("SELECT DISTINCT file FROM memory_chunks_fts").fetchall()
                }
                query_files = self._query_source_files(files, query) if not stored_rows else set()
                query_file_names = {
                    to_posix_path(os.path.relpath(path, self.root_dir))
                    for path in query_files
                }
                memory_prefix = to_posix_path(
                    os.path.relpath(Path(str(self.paths["memory_root"])), self.root_dir)
                ).rstrip("/") + "/"
                files_to_index = {
                    name for name in changed_files
                    if name in indexed_files
                    or name in query_file_names
                    or name.startswith(memory_prefix)
                }
                for name in sorted(files_to_index):
                    path = path_by_name.get(name)
                    if path is None:
                        continue
                    self._index_file(conn, path, revision, freshness)
                    mtime, size = current_metadata[name]
                    conn.execute("INSERT OR REPLACE INTO memory_index_files(file,mtime_ns,size) VALUES(?,?,?)", (name, mtime, size))
                if not stored_rows:
                    for name, (mtime, size) in current_metadata.items():
                        conn.execute("INSERT OR REPLACE INTO memory_index_files(file,mtime_ns,size) VALUES(?,?,?)", (name, mtime, size))
                conn.execute("UPDATE memory_chunks_fts SET source_revision = ?, freshness = ?", (revision, freshness))
                conn.execute("INSERT OR REPLACE INTO memory_index_meta(key,value) VALUES('last_indexed_at',datetime('now'))")
            conn.execute("INSERT OR REPLACE INTO memory_index_meta(key,value) VALUES('signature',?)", (signature,))
            conn.execute("INSERT OR REPLACE INTO memory_index_meta(key,value) VALUES('root_identity',?)", (root_identity,))
            count = int(conn.execute("SELECT count(*) FROM memory_chunks_fts").fetchone()[0])
            documents = int(conn.execute("SELECT count(DISTINCT file) FROM memory_chunks_fts").fetchone()[0])
            conn.commit()
            return self._health("sqlite-fts5", "READY", "embedded local project index", index_path=str(index_path), document_count=documents, chunk_count=count)
        except sqlite3.OperationalError as exc:
            conn.rollback()
            return self._health("sqlite-fts5", "UNAVAILABLE", f"SQLite FTS5 unavailable: {exc}", index_path=str(index_path))
        finally:
            conn.close()

    def _sqlite_search(self, query: str, limit: int = 10, health: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        health = health or self._ensure_sqlite_index()
        if health["state"] != "READY":
            return []
        conn = sqlite3.connect(str(self.paths["qmd_index"]))
        conn.row_factory = sqlite3.Row
        try:
            terms = [term.replace('"', "") for term in extract_keywords(query)]
            if not terms:
                return []
            match_query = " OR ".join(f'"{term}"' for term in terms)
            rows = conn.execute(
                "SELECT file,anchor,text,source_hash,source_revision,freshness,bm25(memory_chunks_fts) AS rank FROM memory_chunks_fts WHERE memory_chunks_fts MATCH ? ORDER BY rank LIMIT ?",
                (match_query, limit),
            ).fetchall()
            return [self._evidence("sqlite-fts5", dict(row), score=1.0 / (1.0 + abs(float(row["rank"] or 0.0)))) for row in rows]
        except sqlite3.OperationalError:
            return []
        finally:
            conn.close()

    def _qmd_search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        index_path = str(self.paths.get("qmd_index", ""))
        if not shutil.which("qmd") or self._qmd_runtime_reason() or not os.path.isfile(index_path):
            return []
        try:
            code, stdout, _ = self._run_qmd_cli(
                ["search", "--collection", self.collection, "--query", query, "--top-k", str(limit), "--rerank"]
            )
            if code != 0 or not stdout.strip():
                return []
            parsed: Any = json.loads(stdout)
            rows = parsed if isinstance(parsed, list) else parsed.get("results", []) if isinstance(parsed, dict) else []
            return [self._evidence("qmd", cast(dict[str, Any], row), score=float(row.get("score", 0.0))) for row in rows if isinstance(row, dict)]
        except (OSError, ValueError):
            return []

    def _evidence(self, provider: str, row: dict[str, Any], score: float) -> dict[str, Any]:
        raw_text = str(row.get("text", row.get("content", "")))
        max_text = max(1000, int(self.config.get("max_evidence_chars", 8000)))
        return {
            "provider": provider,
            "file": row.get("file", row.get("path", "unknown")),
            "anchor": row.get("anchor", row.get("source_anchor", "")),
            "text": raw_text[:max_text],
            "text_truncated": len(raw_text) > max_text,
            "score": score,
            "confidence": "high" if score >= 0.5 else "medium" if score > 0 else "low",
            "source_hash": row.get("source_hash"),
            "source_revision": row.get("source_revision", self._revision()),
            "freshness": row.get("freshness", self._freshness()),
        }

    def local_search(self, query: str) -> list[dict[str, Any]]:
        return self._sqlite_search(query)

    def _qdrant_health(self) -> dict[str, Any]:
        url = f"{self.qdrant_url}/collections/{self.collection}"
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                data = json.loads(response.read().decode("utf-8"))
            result = data.get("result", {}) if isinstance(data, dict) else {}
            vectors = result.get("config", {}).get("params", {}).get("vectors", {}) if isinstance(result, dict) else {}
            points = result.get("points_count", result.get("vectors_count", 0)) if isinstance(result, dict) else 0
            if not isinstance(vectors, dict) or not points:
                return self._health("qdrant", "DEGRADED", "Qdrant is reachable but collection or vectors are not ready", collection=self.collection, document_count=int(points or 0), chunk_count=int(points or 0), embedding_status="invalid")
            return self._health("qdrant", "READY", "validated collection and vector count", collection=self.collection, document_count=int(points), chunk_count=int(points), embedding_status="ready")
        except Exception as exc:
            return self._health("qdrant", "UNAVAILABLE", f"Qdrant unavailable: {exc}", collection=self.collection)

    def vector_search(self, query: str) -> list[dict[str, Any]]:
        health = self._qdrant_health()
        if health["state"] != "READY":
            return []
        keywords = extract_keywords(query)
        if not keywords:
            return []
        try:
            request = urllib.request.Request(
                f"{self.qdrant_url}/collections/{self.collection}/points/scroll",
                data=json.dumps({"limit": 20, "with_payload": True}).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(request, timeout=2) as response:
                data = json.loads(response.read().decode("utf-8"))
            points = data.get("result", {}).get("points", []) if isinstance(data, dict) else []
            results: list[dict[str, Any]] = []
            for point in points if isinstance(points, list) else []:
                payload = point.get("payload", {}) if isinstance(point, dict) else {}
                text = str(payload.get("text", payload.get("content", ""))) if isinstance(payload, dict) else ""
                hits = sum(1 for keyword in keywords if keyword.lower() in text.lower())
                if hits:
                    results.append(self._evidence("qdrant", {
                        "file": payload.get("file", payload.get("path", "unknown")),
                        "anchor": payload.get("anchor", ""), "text": text,
                        "source_hash": payload.get("source_hash"),
                        "source_revision": payload.get("source_revision"),
                        "freshness": payload.get("freshness", "UNVERIFIED"),
                    }, score=hits / len(keywords)))
            return sorted(results, key=lambda item: cast(float, item["score"]), reverse=True)
        except Exception as exc:
            log_warn(f"Qdrant collection query failed: {exc}")
            return []

    def local_provider_health(self, query: str = "") -> list[dict[str, Any]]:
        return [self._qmd_health(), self._ensure_sqlite_index(query), self._qdrant_health()]

    def execute_search(self, query: str) -> dict[str, Any]:
        log_info(f"Searching memory for: '{query}'")
        chain = list(self.config.get("provider_chain", ["qmd", "sqlite-fts5", "qdrant", "markdown"]))
        reasons: list[str] = []
        health_by_provider = {item["provider"]: item for item in self.local_provider_health(query)}
        for provider in chain:
            health = health_by_provider.get(provider)
            if provider == "qmd" and health and health["state"] == "READY":
                results = self._qmd_search(query)
            elif provider == "sqlite-fts5" and health and health["state"] == "READY":
                results = self._sqlite_search(query, health=health)
            elif provider == "qdrant" and health and health["state"] == "READY":
                results = self.vector_search(query)
            elif provider == "markdown":
                results = self._markdown_search(query)
            else:
                results = []
            if results:
                return {
                    "status": "success", "query": query, "provider_chain": chain,
                    "selected_provider": provider, "provider_health": list(health_by_provider.values()),
                    "results": results[:5], "results_count": len(results),
                    "fallback_reason": "; ".join(reasons),
                    "current_source_authority": "source files; generated memory is an index and navigation layer",
                }
            if health and health.get("state") != "READY":
                reasons.append(f"{provider}: {health.get('reason')}")
        return {
            "status": "success", "query": query, "provider_chain": chain,
            "selected_provider": "none", "provider_health": list(health_by_provider.values()),
            "results": [], "results_count": 0, "fallback_reason": "; ".join(reasons),
            "current_source_authority": "source files; generated memory is an index and navigation layer",
        }

    def _markdown_search(self, query: str) -> list[dict[str, Any]]:
        keywords = extract_keywords(query)
        results: list[dict[str, Any]] = []
        if not keywords:
            return results
        mem_dir = str(self.paths.get("memory_root", ""))
        for root, _, files in os.walk(mem_dir):
            for file in files:
                if not file.endswith(".md"):
                    continue
                full_path = os.path.join(root, file)
                rel_path = to_posix_path(os.path.relpath(full_path, self.root_dir))
                for match in search_in_markdown(full_path, keywords):
                    row = dict(match)
                    row.update({"file": rel_path, "anchor": f"{rel_path}:{int(row.get('line', 0))}", "source_hash": hashlib.sha256(Path(full_path).read_bytes()).hexdigest(), "source_revision": self._revision(), "freshness": self._freshness()})
                    results.append(self._evidence("markdown", row, float(row.get("score", 0.0))))
        return sorted(results, key=lambda item: cast(float, item.get("score", 0.0)), reverse=True)


__all__ = ["RAGSearcher"]

if __name__ == "__main__":
    import sys
    print(json.dumps(RAGSearcher().execute_search(sys.argv[1] if len(sys.argv) > 1 else "architecture"), indent=2))
