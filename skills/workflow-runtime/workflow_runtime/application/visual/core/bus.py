from __future__ import annotations

import asyncio
import inspect
from typing import Any, Callable

# File path: vir_runtime/core/bus.py
"""
Purpose: Asynchronous Event Bus with wildcard pattern support.
Owner: Infrastructure Developer
Related FEAT: FEAT-056
Related Blueprint: bp_vir_core_event_bus
"""

EventHandler = Callable[..., Any]


class Event:
    def __init__(self, topic: str, payload: dict[str, Any]):
        self.topic = topic
        self.payload = payload


class AsyncEventBus:
    def __init__(self, worker_count: int = 1):
        self.worker_count = worker_count
        self.subscribers: dict[str, list[EventHandler]] = {}
        self.queue: asyncio.Queue[Event | None] = asyncio.Queue()
        self.workers: list[asyncio.Task[None]] = []
        self.running = False

    def subscribe(self, topic_pattern: str, handler: EventHandler) -> None:
        """Subscribe to dynamic topic pattern changes."""
        if topic_pattern not in self.subscribers:
            self.subscribers[topic_pattern] = []
        self.subscribers[topic_pattern].append(handler)

    def publish(self, event: Event) -> None:
        """Publish event matching payload specifications."""
        self.queue.put_nowait(event)

    def start(self) -> None:
        """Start async workers loop."""
        if not self.running:
            self.running = True
            for _ in range(self.worker_count):
                task = asyncio.create_task(self._worker_loop())
                self.workers.append(task)

    async def stop(self) -> None:
        """Stop and gracefully wait for workers processing queues."""
        self.running = False
        for _ in range(self.worker_count):
            self.queue.put_nowait(None)
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
            self.workers.clear()

    async def _worker_loop(self) -> None:
        while self.running or not self.queue.empty():
            event = await self.queue.get()
            if event is None:
                self.queue.task_done()
                break
            for pattern, handlers in self.subscribers.items():
                if self._match(pattern, event.topic):
                    for handler in handlers:
                        try:
                            if inspect.iscoroutinefunction(handler):
                                await handler(event)
                            else:
                                handler(event)
                        except Exception as e:
                            print(f"[AsyncEventBus] Handler exception: {e}")
            self.queue.task_done()

    def _match(self, pattern: str, topic: str) -> bool:
        if pattern == "*" or pattern == topic:
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return topic.startswith(prefix)
        return False


# Sprint 0 Skeleton Layer 5 Wildcard Event Bus
class WildcardEventBus:
    def __init__(self) -> None:
        self.subscribers: dict[str, list[EventHandler]] = {}

    def subscribe(self, topic: str, callback: EventHandler) -> None:
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        print(f"[WildcardEventBus] Publishing topic: {topic}")
        for sub_topic, callbacks in self.subscribers.items():
            if sub_topic == "*" or sub_topic == topic:
                for cb in callbacks:
                    cb(topic, payload)


__all__ = [
    "Event",
    "AsyncEventBus",
    "WildcardEventBus",
]
