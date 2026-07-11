# File path: tests/unit/test_event_bus.py
import unittest
import asyncio
from vir_runtime.core.bus import AsyncEventBus, Event

class TestEventBus(unittest.IsolatedAsyncioTestCase):
    async def test_publish_subscribe(self):
        bus = AsyncEventBus(worker_count=1)
        received_payloads = []

        async def handler(event: Event):
            received_payloads.append(event.payload)

        bus.subscribe("test.topic", handler)
        bus.start()

        event = Event("test.topic", {"msg": "hello"})
        bus.publish(event)

        # Wait briefly for worker to process event
        await asyncio.sleep(0.1)
        await bus.stop()

        self.assertEqual(len(received_payloads), 1)
        self.assertEqual(received_payloads[0]["msg"], "hello")

    async def test_wildcard_subscribe(self):
        bus = AsyncEventBus(worker_count=1)
        received_payloads = []

        async def handler(event: Event):
            received_payloads.append(event.payload)

        bus.subscribe("vir.evidence.*", handler)
        bus.start()

        event1 = Event("vir.evidence.new", {"type": "contradiction"})
        event2 = Event("vir.other.topic", {"type": "none"})
        bus.publish(event1)
        bus.publish(event2)

        await asyncio.sleep(0.1)
        await bus.stop()

        self.assertEqual(len(received_payloads), 1)
        self.assertEqual(received_payloads[0]["type"], "contradiction")

if __name__ == "__main__":
    unittest.main()
