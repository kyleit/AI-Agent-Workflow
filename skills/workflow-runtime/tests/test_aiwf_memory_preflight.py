from __future__ import annotations

import hashlib
import json

from workflow_runtime.application.workflow.workflow_entry_gateway import build_context_preflight
from workflow_runtime.infrastructure.memory.search import RAGSearcher
from workflow_runtime.presentation.cli.bootstrap import bootstrap_di


def test_context_preflight_persists_bounded_memory_and_rag_receipt(tmp_path, monkeypatch) -> None:
    bootstrap_di()
    memory = tmp_path / ".agents" / "memory"
    state = tmp_path / ".agents" / "state"
    memory.mkdir(parents=True)
    state.mkdir(parents=True)
    summary = memory / "project-summary.md"
    summary.write_text("# Project\n\nRuntime architecture and workflow routing.\n", encoding="utf-8")
    digest = hashlib.sha256(summary.read_bytes()).hexdigest()
    (memory / "project-context.json").write_text(json.dumps({
        "schema_version": "aiwf.project-context.v1",
        "project_id": "fixture",
        "source_revision": "WORKTREE",
        "source_hashes": [f".agents/memory/project-summary.md={digest}"],
        "summary_path": ".agents/memory/project-summary.md",
        "architecture_paths": [],
        "entrypoints": [],
        "active_constraints": [],
        "known_blockers": [],
        "index_revision": "WORKTREE",
        "freshness": "CURRENT",
        "retrieval_hints": [],
        "catalog_paths": [],
    }), encoding="utf-8")

    def fake_search(self, query: str):
        return {
            "status": "success",
            "selected_provider": "sqlite-fts5",
            "results": [{
                "file": ".agents/memory/project-summary.md",
                "anchor": ".agents/memory/project-summary.md:1",
                "text": "Runtime architecture",
                "score": 0.9,
            }],
            "provider_health": [
                {"provider": "qmd", "state": "UNAVAILABLE", "reason": "not installed"},
                {"provider": "sqlite-fts5", "state": "READY", "reason": "embedded"},
            ],
        }

    monkeypatch.setattr(
        "workflow_runtime.infrastructure.memory.search.RAGSearcher.execute_search",
        fake_search,
    )
    result = build_context_preflight("workflow architecture", tmp_path)

    assert result["memory_action"] == "cache"
    assert result["rag_status"] == "fallback"
    assert result["retrieval_count"] == 1
    receipt = state / "memory-preflight.json"
    assert receipt.is_file()
    persisted = json.loads(receipt.read_text(encoding="utf-8"))
    assert persisted["source_authority"] == "current_worktree"
    assert persisted["rag_provider"] == "sqlite-fts5"


def test_local_rag_indexes_current_source_anchors(tmp_path) -> None:
    memory = tmp_path / ".agents" / "memory"
    memory.mkdir(parents=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "lane_runtime.py").write_text(
        "def unique_lane_scheduler_contract():\n    return 'current-source'\n",
        encoding="utf-8",
    )
    (memory / "project-summary.md").write_text("# Cached summary\n", encoding="utf-8")

    searcher = RAGSearcher(
        root_dir=tmp_path,
        config={
            "project_id": "fixture",
            "provider_chain": ["sqlite-fts5"],
            "qmd_index": ".agents/memory/qmd.index",
        },
    )
    result = searcher.execute_search("unique lane scheduler contract")

    assert result["selected_provider"] == "sqlite-fts5"
    assert any(item["file"] == "src/lane_runtime.py" for item in result["results"])


def test_local_rag_updates_only_changed_source_file(tmp_path) -> None:
    memory = tmp_path / ".agents" / "memory"
    memory.mkdir(parents=True)
    source = tmp_path / "runtime.py"
    sibling = tmp_path / "sibling.py"
    source.write_text("def old_runtime_contract():\n    return 'old'\n", encoding="utf-8")
    sibling.write_text("def stable_sibling_contract():\n    return 'stable'\n", encoding="utf-8")

    config = {
        "project_id": "fixture",
        "provider_chain": ["sqlite-fts5"],
        "qmd_index": ".agents/memory/qmd.index",
    }
    searcher = RAGSearcher(root_dir=tmp_path, config=config)
    assert searcher.execute_search("old_runtime_contract")["results"]

    source.write_text("def new_runtime_contract():\n    return 'new'\n", encoding="utf-8")
    refreshed = RAGSearcher(root_dir=tmp_path, config=config).execute_search("new_runtime_contract")

    assert refreshed["selected_provider"] == "sqlite-fts5"
    assert any(item["file"] == "runtime.py" for item in refreshed["results"])
    assert not RAGSearcher(root_dir=tmp_path, config=config).execute_search("old_runtime_contract")["results"]
