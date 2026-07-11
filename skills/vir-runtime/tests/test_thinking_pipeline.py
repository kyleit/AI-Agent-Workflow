# File path: tests/unit/test_thinking_pipeline.py
import unittest
import asyncio
from vir_runtime.core.bus import AsyncEventBus
from vir_runtime.cognitive.pipeline import ThinkingPipeline, PipelineTimeoutError

class TestThinkingPipeline(unittest.IsolatedAsyncioTestCase):
    async def test_successful_run(self):
        bus = AsyncEventBus(worker_count=1)
        bus.start()
        
        pipeline = ThinkingPipeline(session_id="session_123", bus=bus)
        status = await pipeline.start_pipeline()
        
        await bus.stop()
        self.assertEqual(status, "PASS")
        self.assertEqual(pipeline.active_stage_index, 10) # Improve stage

    async def test_stage_timeout(self):
        bus = AsyncEventBus(worker_count=1)
        bus.start()
        
        # Instantiate with a super small timeout to force failure
        pipeline = ThinkingPipeline(session_id="session_456", bus=bus, stage_timeout=0.001)
        
        with self.assertRaises(PipelineTimeoutError):
            await pipeline.start_pipeline()
            
        await bus.stop()
        self.assertEqual(pipeline.status, "BLOCKED")

if __name__ == "__main__":
    unittest.main()
