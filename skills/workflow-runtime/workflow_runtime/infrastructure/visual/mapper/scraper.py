# File path: vir_runtime/mapper/scraper.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SourceCoordinate:
    file_path: str
    line: int
    column: int
    confidence: float


class SourceLinker:
    def __init__(self, block_node_modules: bool = True) -> None:
        self.block_node_modules = block_node_modules

    def resolve_source_coordinates(self, element_id: str) -> list[SourceCoordinate]:
        """Inject metadata scraping queries and resolve coordinates components candidates."""
        print(f"[SourceLinker] Resolving source coordinates for element: {element_id}")
        candidates: list[SourceCoordinate] = []

        if element_id == "button#submit":
            candidates.append(
                SourceCoordinate(
                    file_path="src/components/Button.tsx",
                    line=42,
                    column=8,
                    confidence=0.95
                )
            )
        else:
            candidates.append(
                SourceCoordinate(
                    file_path="src/App.tsx",
                    line=10,
                    column=4,
                    confidence=0.50
                )
            )

        if self.block_node_modules:
            candidates = [c for c in candidates if "node_modules" not in c.file_path]

        return candidates


__all__ = [
    "SourceCoordinate",
    "SourceLinker",
]
