# agent_dispatcher.py
import threading
import time
from typing import Dict, Any, List

class AgentDispatcher:
    def __init__(self, max_workers: int = 3) -> None:
        self.max_workers = max_workers
        self.active_agents: Dict[str, threading.Thread] = {}
        self.lock = threading.Lock()

    def dispatch_agent(self, agent_name: str, task_fn) -> bool:
        with self.lock:
            # Enforce concurrency boundary limits
            if len(self.active_agents) >= self.max_workers:
                return False  # Blocked by concurrency backpressure
                
            if agent_name in self.active_agents:
                # Agent thread already running
                return True
                
            t = threading.Thread(target=self._run_wrapper, args=(agent_name, task_fn), name=f"Agent-{agent_name}")
            self.active_agents[agent_name] = t
            t.start()
            return True

    def _run_wrapper(self, agent_name: str, task_fn) -> None:
        try:
            task_fn()
        finally:
            with self.lock:
                if agent_name in self.active_agents:
                    del self.active_agents[agent_name]

    def get_active_count(self) -> int:
        with self.lock:
            return len(self.active_agents)
