# File path: vir_runtime/mapper/scraper.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SourceCoordinate:
    file_path: str
    line: int
    column: int
    confidence: float

class SourceLinker:
    def __init__(self, block_node_modules: bool = True):
        self.block_node_modules = block_node_modules

    def resolve_source_coordinates(self, element_id: str) -> List[SourceCoordinate]:
        """Inject metadata scraping queries and resolve coordinates components candidates."""
        print(f"[SourceLinker] Resolving source coordinates for element: {element_id}")
        candidates = []

        # Simulating React __source metadata mapping resolution
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
            # Fallback coordinate
            candidates.append(
                SourceCoordinate(
                    file_path="src/App.tsx",
                    line=10,
                    column=4,
                    confidence=0.50
                )
            )

        # Filter out node_modules references if configured
        if self.block_node_modules:
            candidates = [c for c in candidates if "node_modules" not in c.file_path]

        return candidates
