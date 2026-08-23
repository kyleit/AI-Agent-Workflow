from workflow_runtime.domain.knowledge.entities import (KnowledgeGraph,
                                                        MemoryEntry)
from workflow_runtime.shared.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class KnowledgeGraphAdapter:
    """Adapter building relational knowledge graph network from memory entries."""

    def build_graph(self, entries: list[MemoryEntry]) -> KnowledgeGraph:
        """Constructs KnowledgeGraph instance populated with nodes and relational edges."""
        graph = KnowledgeGraph()

        # Step 1: Add all entries as graph nodes
        for entry in entries:
            graph.add_node(entry)

        # Step 2: Connect nodes sharing matching tags or cross-referencing IDs
        n = len(entries)
        for i in range(n):
            for j in range(i + 1, n):
                e1 = entries[i]
                e2 = entries[j]

                # Check tag overlap
                shared_tags = set(e1.tags).intersection(set(e2.tags))
                if shared_tags:
                    graph.connect(e1.entry_id, e2.entry_id, f"SHARES_TAGS({','.join(shared_tags)})")

                # Check cross references in content or title
                if e1.entry_id in e2.content or e1.title in e2.content:
                    graph.connect(e2.entry_id, e1.entry_id, "REFERENCES")
                elif e2.entry_id in e1.content or e2.title in e1.content:
                    graph.connect(e1.entry_id, e2.entry_id, "REFERENCES")

        logger.info(
            f"Built KnowledgeGraph with {len(graph.nodes)} nodes and {len(graph.edges)} edges."
        )
        return graph
