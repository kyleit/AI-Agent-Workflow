# File path: vir_runtime/cognitive/rca.py
from dataclasses import dataclass
from typing import List, Dict, Any
from vir_runtime.domain.evidence import Evidence

@dataclass
class RootCause:
    category: str # e.g. "TIMING", "CSS_SPECIFICITY", "ROUTING"
    description: str
    is_confirmed: bool
    evidence_ids: List[str]

class RCAEngine:
    def __init__(self, required_evidence_count: int = 2):
        self.required_evidence_count = required_evidence_count

    def analyze_root_cause(self, category: str, description: str, evidence_list: List[Evidence]) -> RootCause:
        """Classify anomalies and confirm verdicts using evidence requirements counters."""
        evidence_ids = [ev.evidence_id for ev in evidence_list]
        is_confirmed = len(evidence_ids) >= self.required_evidence_count
        
        return RootCause(
            category=category,
            description=description,
            is_confirmed=is_confirmed,
            evidence_ids=evidence_ids
        )
