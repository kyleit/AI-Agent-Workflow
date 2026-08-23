# File path: vir_runtime/multi_agent/consensus.py
from __future__ import annotations

import os
from typing import Any, cast

import yaml

from workflow_runtime.application.visual.core.bus import AsyncEventBus, Event
from workflow_runtime.domain.ports.visual_ports import ConsensusRecord


class ConsensusEngine:
    def __init__(self, bus: AsyncEventBus, config_path: str = "config.yaml") -> None:
        self.bus = bus
        self.config_path = config_path
        self.votes: dict[str, dict[str, Any]] = {}
        self.confidence_threshold = 0.85
        self.domain_weights: dict[str, float] = {"design": 1.0, "network": 0.8, "accessibility": 1.0}
        self._load_config()

    def _load_config(self) -> None:
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                raw_cfg = yaml.safe_load(f)
                config = cast(dict[str, Any], raw_cfg) if isinstance(raw_cfg, dict) else {}
            raw_cons = config.get("consensus")
            consensus_conf = cast(dict[str, Any], raw_cons) if isinstance(raw_cons, dict) else {}
            self.confidence_threshold = float(str(consensus_conf.get("confidence_threshold", 0.85)))
            raw_dw = consensus_conf.get("domain_weights")
            if isinstance(raw_dw, dict):
                self.domain_weights = cast(dict[str, float], raw_dw)

    def register_vote(self, agent_name: str, vote: dict[str, Any]) -> None:
        """Register dynamic agent vote params."""
        self.votes[agent_name] = vote

    async def collect_votes(self) -> ConsensusRecord:
        """Aggregate votes, evaluate vetoes with evidence rules, and return verdict."""
        confidence_breakdowns: dict[str, float] = {}
        vetoes: list[str] = []
        evidence_ids: list[Any] = []
        weighted_sum = 0.0
        weight_total = 0.0

        for agent, vote in list(self.votes.items()):
            domain = str(vote.get("domain", "general"))
            confidence = float(str(vote.get("confidence", 1.0)))
            has_veto = bool(vote.get("veto", False))
            raw_ev = vote.get("evidence_ids")
            linked_ev = cast(list[Any], raw_ev) if isinstance(raw_ev, list) else []

            weight = float(self.domain_weights.get(domain, 1.0))
            weighted_sum += confidence * weight
            weight_total += weight
            confidence_breakdowns[domain] = confidence

            if has_veto:
                if len(linked_ev) >= 1:
                    vetoes.append(f"Veto by {agent}: {vote.get('reason', 'No reason specified')}")
                    evidence_ids.extend(linked_ev)
                else:
                    print(f"[ConsensusEngine] Downgrading veto from {agent} due to missing evidence.")
                    advisory_payload = {"reason": f"Veto from {agent} downgraded: missing evidence details."}
                    self.bus.publish(Event(topic="vir.design.advisory", payload=advisory_payload))

        avg_confidence = (weighted_sum / weight_total) if weight_total > 0 else 1.0

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


__all__ = ["ConsensusEngine"]
