from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ASTNode:
    id: str
    type: str
    properties: Dict[str, Any]
    children: List['ASTNode']
    parent_id: Optional[str] = None
