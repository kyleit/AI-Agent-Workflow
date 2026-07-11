# File path: vir_runtime/sensory/touch.py
import asyncio
import random
import json
from typing import Dict, Any, List

class TouchEngine:
    def __init__(self):
        self.action_history: List[Dict[str, Any]] = []

    async def execute_action(self, action: Dict[str, Any], mode: str = "A") -> None:
        """Dispatch target page clicks and key entry sequences with delays."""
        action_type = action.get("type", "click")
        selector = action.get("selector", "")
        value = action.get("value", "")

        # Simulate micro-delays for human interaction (Mode B)
        if mode == "B":
            # Heuristic human timing: micro-delay between 100ms and 500ms
            delay = random.uniform(0.1, 0.5)
            print(f"[TouchEngine] Mode B: Simulating human timing delay of {delay:.2f}s before {action_type}")
            await asyncio.sleep(delay)
        else:
            # Mode A: Standard fast execution
            await asyncio.sleep(0.01)

        print(f"[TouchEngine] Executed {action_type} on '{selector}'" + (f" with value '{value}'" if value else ""))
        
        # Log to history
        self.action_history.append({
            "action": action,
            "mode": mode,
            "timestamp": random.random() # dummy timestamp
        })

    def export_replay_log(self, path: str) -> None:
        """Export replay log file containing details of all click interactions."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.action_history, f, indent=2)
        print(f"[TouchEngine] Replay logs exported to: {path}")
