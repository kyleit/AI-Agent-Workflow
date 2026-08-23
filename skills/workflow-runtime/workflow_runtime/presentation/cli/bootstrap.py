from __future__ import annotations

from typing import Any, cast

from workflow_runtime.application.knowledge.knowledge_provider_factory import (
    KnowledgeProviderFactory)
from workflow_runtime.application.ports.locator import InfrastructureLocator
from workflow_runtime.infrastructure.agy.agy_adapter import AGYAdapter
from workflow_runtime.infrastructure.execution.execution_manager import (
    ExecutionGateway)
from workflow_runtime.infrastructure.knowledge.memory_store_adapter import (
    MemoryStoreAdapter)
from workflow_runtime.infrastructure.knowledge.providers.markdown_provider import (
    MarkdownProvider)
from workflow_runtime.infrastructure.knowledge.providers.obsidian_provider import (
    ObsidianProvider)
from workflow_runtime.infrastructure.knowledge.providers.sqlite_provider import (
    SQLiteProvider)
from workflow_runtime.infrastructure.knowledge.providers.vector_provider import (
    VectorDBProvider)
from workflow_runtime.infrastructure.knowledge.rag_store_adapter import (
    RAGStoreAdapter)
from workflow_runtime.infrastructure.persistence.db_records import (
    save_insight_snapshot)
from workflow_runtime.infrastructure.registry.registry_adapter import (
    RegistryAdapter)


def _create_sqlite(root: str, cfg: dict[str, Any]) -> Any:
    sqlite_cfg = cast(dict[str, Any], cfg.get("sqlite", {})) if isinstance(cfg.get("sqlite"), dict) else {}
    db_path = str(sqlite_cfg.get("db_path", ".agents/state/knowledge.db"))
    return SQLiteProvider(db_path=db_path, workspace_root=root)


def _create_vector_db(root: str, cfg: dict[str, Any]) -> Any:
    qdrant_cfg = cast(dict[str, Any], cfg.get("qdrant", {})) if isinstance(cfg.get("qdrant"), dict) else {}
    host = str(qdrant_cfg.get("host", "127.0.0.1"))
    port = int(qdrant_cfg.get("port", 6333) or 6333)
    collection_name = str(qdrant_cfg.get("collection", "knowledge"))
    return VectorDBProvider(host=host, port=port, collection_name=collection_name)


def _create_obsidian(root: str, cfg: dict[str, Any]) -> Any:
    obsidian_cfg = cast(dict[str, Any], cfg.get("obsidian", {})) if isinstance(cfg.get("obsidian"), dict) else {}
    port = int(obsidian_cfg.get("port", 27124) or 27124)
    token = str(obsidian_cfg.get("api_key", ""))
    return ObsidianProvider(port=port, token=token)


def _create_markdown(root: str, cfg: dict[str, Any]) -> Any:
    _ = cfg
    return MarkdownProvider(workspace_root=root)


def bootstrap_di() -> None:
    """Wire dependencies for Application layer (Clean Architecture Composition Root)."""
    KnowledgeProviderFactory.register("sqlite", _create_sqlite)
    KnowledgeProviderFactory.register("vector_db", _create_vector_db)
    KnowledgeProviderFactory.register("obsidian", _create_obsidian)
    KnowledgeProviderFactory.register("markdown", _create_markdown)

    setattr(InfrastructureLocator, "AgyAdapter", AGYAdapter)
    setattr(InfrastructureLocator, "save_insight_snapshot", save_insight_snapshot)
    setattr(InfrastructureLocator, "MemoryStoreAdapter", MemoryStoreAdapter)
    setattr(InfrastructureLocator, "RAGStoreAdapter", RAGStoreAdapter)
    setattr(InfrastructureLocator, "RegistryAdapter", RegistryAdapter)
    setattr(InfrastructureLocator, "ExecutionGateway", ExecutionGateway)


__all__ = ["bootstrap_di"]
