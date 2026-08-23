from typing import Any, Optional, cast

from workflow_runtime.domain.ports.visual_ports import (AsyncEventBusPort,
                                                        VisualEvent)
from workflow_runtime.domain.visual.core.evidence import Evidence
from workflow_runtime.domain.visual.design.kb import DesignKnowledgeBase

# File path: vir_runtime/design/agent.py



class DesignAuthorityAgent:
    def __init__(self, bus: AsyncEventBusPort, kb: Optional[DesignKnowledgeBase] = None):
        self.bus = bus
        self.kb = kb or DesignKnowledgeBase()

    async def on_evidence_received(self, event: VisualEvent) -> None:
        """Evaluate visual evidence details against guidelines."""
        # Inspect visual regression or DOM style evidence
        if event.topic != "vir.evidence.new":
            return

        payload = event.payload
        classification = payload.get("classification")

        # We only check layout or style audits
        if classification != "style_audit":
            return

        element_styles: dict[str, Any] = cast(dict[str, Any], payload.get("styles", {})) if isinstance(payload.get("styles"), dict) else {}

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
                    advisory_event = VisualEvent(
                        topic="vir.design.advisory",
                        payload={"reason": reason, "evidence_id": evidence.evidence_id}
                    )
                    await self.bus.publish(advisory_event)

    async def issue_veto(self, reason: str, evidence: Evidence) -> None:
        """Issue a veto event blocking downstream quality gates."""
        print(f"[DesignAuthorityAgent] VETO Issued! Reason: {reason}")
        veto_event = VisualEvent(
            topic="vir.design.veto",
            payload={
                "reason": reason,
                "evidence_id": evidence.evidence_id,
                "classification": "VETO"
            }
        )
        await self.bus.publish(veto_event)
