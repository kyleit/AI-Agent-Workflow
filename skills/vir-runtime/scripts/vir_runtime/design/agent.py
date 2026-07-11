# File path: vir_runtime/design/agent.py
from typing import Optional, Dict, Any
from vir_runtime.core.bus import AsyncEventBus, Event
from vir_runtime.domain.evidence import Evidence
from vir_runtime.design.kb import DesignKnowledgeBase

class DesignAuthorityAgent:
    def __init__(self, bus: AsyncEventBus, kb: Optional[DesignKnowledgeBase] = None):
        self.bus = bus
        self.kb = kb or DesignKnowledgeBase()

    async def on_evidence_received(self, event: Event) -> None:
        """Evaluate visual evidence details against guidelines."""
        # Inspect visual regression or DOM style evidence
        if event.topic != "vir.evidence.new":
            return

        payload = event.payload
        classification = payload.get("classification")
        
        # We only check layout or style audits
        if classification != "style_audit":
            return

        element_styles = payload.get("styles", {})
        
        # Check primary color compliance
        primary_color = element_styles.get("color")
        if primary_color:
            is_compliant = self.kb.check_token_compliance("color", primary_color)
            if not is_compliant:
                rule = self.kb.lookup_rule("colors", "primary")
                severity = rule.get("severity", "MUST")
                
                # Create associated evidence
                evidence = Evidence(
                    source_agent="DesignAuthorityAgent",
                    classification="design_violation",
                    payload={"element": payload.get("selector"), "invalid_color": primary_color}
                )
                
                reason = f"Primary color '{primary_color}' is not in allowed design tokens."
                if severity == "MUST":
                    await self.issue_veto(reason, evidence)
                else:
                    # Publish ADVISORY warning event
                    advisory_event = Event(
                        topic="vir.design.advisory",
                        payload={"reason": reason, "evidence_id": evidence.evidence_id}
                    )
                    self.bus.publish(advisory_event)

    async def issue_veto(self, reason: str, evidence: Evidence) -> None:
        """Issue a veto event blocking downstream quality gates."""
        print(f"[DesignAuthorityAgent] VETO Issued! Reason: {reason}")
        veto_event = Event(
            topic="vir.design.veto",
            payload={
                "reason": reason,
                "evidence_id": evidence.evidence_id,
                "classification": "VETO"
            }
        )
        self.bus.publish(veto_event)
