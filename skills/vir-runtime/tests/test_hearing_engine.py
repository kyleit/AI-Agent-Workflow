# File path: tests/unit/test_hearing_engine.py
import unittest
import asyncio
from vir_runtime.core.bus import AsyncEventBus, Event
from vir_runtime.sensory.hearing import HearingEngine

class TestHearingEngine(unittest.IsolatedAsyncioTestCase):
    async def test_hearing_publish(self):
        bus = AsyncEventBus(worker_count=1)
        received_logs = []

        async def handler(event: Event):
            received_logs.append(event.payload)

        # Wildcard subscribe to hearing logs
        bus.subscribe("vir.hearing.console.*", handler)
        bus.start()

        engine = HearingEngine(bus)
        engine.start_listening()

        # Check console log event is published
        await asyncio.sleep(0.1)
        await bus.stop()

        self.assertEqual(len(received_logs), 1)
        self.assertEqual(received_logs[0]["level"], "error")
        self.assertIn("MIME type", received_logs[0]["message"])

if __name__ == "__main__":
    unittest.main()
