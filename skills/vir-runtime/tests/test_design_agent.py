# File path: tests/unit/test_design_agent.py
import unittest
import asyncio
from vir_runtime.core.bus import AsyncEventBus, Event
from vir_runtime.design.agent import DesignAuthorityAgent

class TestDesignAgent(unittest.IsolatedAsyncioTestCase):
    async def test_design_audit_veto(self):
        bus = AsyncEventBus(worker_count=1)
        received_vetos = []

        async def veto_handler(event: Event):
            received_vetos.append(event.payload)

        bus.subscribe("vir.design.veto", veto_handler)
        bus.start()

        agent = DesignAuthorityAgent(bus=bus)
        
        # Publish an evidence event containing incorrect primary color style
        evidence_event = Event(
            topic="vir.evidence.new",
            payload={
                "classification": "style_audit",
                "selector": "h1.heading",
                "styles": {
                    "color": "#ff00ff" # Non-compliant color
                }
            }
        )
        
        await agent.on_evidence_received(evidence_event)

        # Wait briefly for worker to capture veto event
        await asyncio.sleep(0.1)
        await bus.stop()

        self.assertEqual(len(received_vetos), 1)
        self.assertIn("color", received_vetos[0]["reason"])
        self.assertEqual(received_vetos[0]["classification"], "VETO")

if __name__ == "__main__":
    unittest.main()
