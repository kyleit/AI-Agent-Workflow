# File path: vir_runtime/cognitive/pipeline.py
import asyncio
import time
from typing import Dict, Any, List
from vir_runtime.core.bus import AsyncEventBus, Event

class PipelineTimeoutError(Exception):
    pass

class ThinkingPipeline:
    def __init__(self, session_id: str, bus: AsyncEventBus, max_rethink_loops: int = 3, stage_timeout: float = 30.0):
        self.session_id = session_id
        self.bus = bus
        self.max_rethink_loops = max_rethink_loops
        self.stage_timeout = stage_timeout
        self.rethink_count = 0
        self.active_stage_index = 0
        self.status = "OPEN"
        self.stages = [
            "Observe", "Understand", "Reason", "Investigate", 
            "Hypothesize", "Test", "Doubt", "Refine", 
            "Verify", "Learn", "Improve"
        ]

    async def start_pipeline(self) -> str:
        """Execute the 11 pipeline stages sequentially with timeouts."""
        print(f"[ThinkingPipeline] Starting pipeline for session {self.session_id}")
        self.status = "OPEN"
        
        while self.rethink_count <= self.max_rethink_loops:
            try:
                for idx in range(self.active_stage_index, len(self.stages)):
                    self.active_stage_index = idx
                    stage = self.stages[idx]
                    
                    # Notify stage transition
                    transition_event = Event(
                        topic="vir.cognitive.stage_transition",
                        payload={"session_id": self.session_id, "from_stage": self.stages[idx-1] if idx > 0 else None, "to_stage": stage}
                    )
                    self.bus.publish(transition_event)

                    # Execute stage actions under timeout
                    await asyncio.wait_for(self._execute_stage(stage), timeout=self.stage_timeout)

                self.status = "PASS"
                return "PASS"
            except asyncio.TimeoutError:
                reason = f"Stage '{self.stages[self.active_stage_index]}' timed out after {self.stage_timeout}s."
                await self.transition_to_blocked(reason)
                raise PipelineTimeoutError(reason)
            except Exception as e:
                # Check if rethink is triggered (e.g. self-doubt engine reduced confidence)
                if self.status == "RETHINK":
                    self.rethink_count += 1
                    print(f"[ThinkingPipeline] Rethink triggered. Loop {self.rethink_count}/{self.max_rethink_loops}")
                    self.active_stage_index = 0 # reset to Observe
                    self.status = "OPEN"
                    continue
                else:
                    await self.transition_to_blocked(str(e))
                    return "FAIL"
        
        await self.transition_to_blocked("Max rethink loops limit exceeded.")
        return "BLOCKED"

    async def _execute_stage(self, stage: str) -> None:
        """Simulate stage processing coordinates logic."""
        print(f"[ThinkingPipeline] Executing Stage: {stage}")
        # A tiny delay to simulate work
        await asyncio.sleep(0.01)

    async def transition_to_blocked(self, reason: str) -> None:
        """Transition target session status parameters to BLOCKED."""
        self.status = "BLOCKED"
        print(f"[ThinkingPipeline] Session BLOCKED! Reason: {reason}")
        blocked_event = Event(
            topic="vir.cognitive.blocked",
            payload={"session_id": self.session_id, "reason": reason}
        )
        self.bus.publish(blocked_event)
