# File path: tests/unit/test_consensus_engine.py
import unittest
import asyncio
from vir_runtime.core.bus import AsyncEventBus, Event
from vir_runtime.multi_agent.consensus import ConsensusEngine

class TestConsensusEngine(unittest.IsolatedAsyncioTestCase):
    async def test_consensus_veto_downgrade(self):
        bus = AsyncEventBus(worker_count=1)
        bus.start()
        
        engine = ConsensusEngine(bus=bus)
        
        # Agent votes VETO but evidence_ids is empty
        engine.register_vote("visual_agent", {
            "domain": "design",
            "confidence": 0.9,
            "veto": True,
            "evidence_ids": [], # Empty -> should downgrade
            "reason": "Color error"
        })
        
        record = await engine.collect_votes()
        await bus.stop()
        
        # Veto downgraded -> verdict is PASS because average confidence >= 0.85 and no valid vetoes
        self.assertEqual(record.verdict, "PASS")
        self.assertEqual(len(record.vetoes), 0)

    async def test_consensus_veto_confirmed(self):
        bus = AsyncEventBus(worker_count=1)
        bus.start()
        
        engine = ConsensusEngine(bus=bus)
        
        # Agent votes VETO with 1 evidence
        engine.register_vote("visual_agent", {
            "domain": "design",
            "confidence": 0.9,
            "veto": True,
            "evidence_ids": ["ev_123"], # Non-empty -> valid veto
            "reason": "Severe layout shift"
        })
        
        record = await engine.collect_votes()
        await bus.stop()
        
        # Verdict is FAIL
        self.assertEqual(record.verdict, "FAIL")
        self.assertEqual(len(record.vetoes), 1)

if __name__ == "__main__":
    unittest.main()
