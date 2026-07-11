# File path: vir_runtime/multi_agent/consensus.py
import yaml
import os
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from vir_runtime.core.bus import AsyncEventBus, Event

@dataclass
class ConsensusRecord:
    verdict: str # PASS or FAIL
    confidence_breakdowns: Dict[str, float]
    vetoes: List[str]
    evidence_ids: List[str]

class ConsensusEngine:
    def __init__(self, bus: AsyncEventBus, config_path: str = "config.yaml"):
        self.bus = bus
        self.config_path = config_path
        self.votes: Dict[str, Dict[str, Any]] = {}
        self.confidence_threshold = 0.85
        self.domain_weights = {"design": 1.0, "network": 0.8, "accessibility": 1.0}
        self._load_config()

    def _load_config(self) -> None:
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            consensus_conf = config.get("consensus", {})
            self.confidence_threshold = consensus_conf.get("confidence_threshold", 0.85)
            self.domain_weights = consensus_conf.get("domain_weights", self.domain_weights)

    def register_vote(self, agent_name: str, vote: Dict[str, Any]) -> None:
        """Register dynamic agent vote params."""
        self.votes[agent_name] = vote

    async def collect_votes(self) -> ConsensusRecord:
        """Aggregate votes, evaluate vetoes with evidence rules, and return verdict."""
        confidence_breakdowns = {}
        vetoes = []
        evidence_ids = []
        weighted_sum = 0.0
        weight_total = 0.0

        for agent, vote in self.votes.items():
            domain = vote.get("domain", "general")
            confidence = vote.get("confidence", 1.0)
            has_veto = vote.get("veto", False)
            linked_ev = vote.get("evidence_ids", [])

            # Apply domain weight multiplier
            weight = self.domain_weights.get(domain, 1.0)
            weighted_sum += confidence * weight
            weight_total += weight
            confidence_breakdowns[domain] = confidence

            # Veto evidence verification rule (requires >= 1 evidence object)
            if has_veto:
                if len(linked_ev) >= 1:
                    vetoes.append(f"Veto by {agent}: {vote.get('reason', 'No reason specified')}")
                    evidence_ids.extend(linked_ev)
                else:
                    # Downgrade veto to advisory warning
                    print(f"[ConsensusEngine] Downgrading veto from {agent} due to missing evidence.")
                    advisory_payload = {"reason": f"Veto from {agent} downgraded: missing evidence details."}
                    self.bus.publish(Event(topic="vir.design.advisory", payload=advisory_payload))

        # Calculate final verdict parameters
        avg_confidence = (weighted_sum / weight_total) if weight_total > 0 else 1.0
        
        # PASS conditions: no vetoes, high average confidence
        if len(vetoes) == 0 and avg_confidence >= self.confidence_threshold:
            verdict = "PASS"
        else:
            verdict = "FAIL"

        record = ConsensusRecord(
            verdict=verdict,
            confidence_breakdowns=confidence_breakdowns,
            vetoes=vetoes,
            evidence_ids=list(set(evidence_ids))
        )

        # Publish final verdict
        verdict_event = Event(
            topic="vir.consensus.verdict",
            payload={
                "verdict": verdict,
                "avg_confidence": avg_confidence,
                "veto_count": len(vetoes)
            }
        )
        self.bus.publish(verdict_event)
        
        return record
