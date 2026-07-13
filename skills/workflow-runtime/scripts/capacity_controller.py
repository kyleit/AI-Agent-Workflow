# capacity_controller.py
import os
import psutil
import time
from typing import Dict, Any, Tuple, Optional

class CapacityController:
    def __init__(self, max_cpu_percent: float = 80.0, max_ram_percent: float = 80.0, max_concurrency: int = 4):
        self.max_cpu_percent = max_cpu_percent
        self.max_ram_percent = max_ram_percent
        self.max_concurrency = max_concurrency
        self.recruited_agents = {}
        self.idle_reclamation_ttl = 10.0 # seconds

    def get_hardware_status(self) -> Dict[str, Any]:
        try:
            cpu = psutil.cpu_percent(interval=None)
            virtual_mem = psutil.virtual_memory()
            ram = virtual_mem.percent
            available_ram_gb = virtual_mem.available / (1024 ** 3)
        except Exception:
            cpu = 0.0
            ram = 0.0
            available_ram_gb = 8.0 # fallback

        # Calculate memory pressure
        memory_pressure = "low"
        if ram > 85.0:
            memory_pressure = "high"
        elif ram > 70.0:
            memory_pressure = "medium"

        return {
            "cpu_utilization": cpu,
            "ram_utilization": ram,
            "available_ram_gb": available_ram_gb,
            "memory_pressure": memory_pressure
        }

    def evaluate_concurrency_limit(self) -> int:
        status = self.get_hardware_status()
        cpu = status["cpu_utilization"]
        ram = status["ram_utilization"]
        pressure = status["memory_pressure"]

        # Dynamic concurrency throttling based on resource utilization
        if cpu > self.max_cpu_percent or ram > self.max_ram_percent or pressure == "high":
            return 1  # Throttle to minimum sequential execution to prevent crash
        elif cpu > 60.0 or ram > 70.0 or pressure == "medium":
            return min(2, self.max_concurrency)
        elif cpu > 40.0:
            return min(3, self.max_concurrency)
        return self.max_concurrency

    def can_recruit(self, agent_role: str, workload_size: int) -> Tuple[bool, str]:
        status = self.get_hardware_status()
        cpu = status["cpu_utilization"]
        ram = status["ram_utilization"]

        # Prevent recruitment under memory pressure or CPU throttle
        if cpu > self.max_cpu_percent:
            return False, f"CPU usage is {cpu}% (limit: {self.max_cpu_percent}%)"
        if ram > self.max_ram_percent:
            return False, f"RAM usage is {ram}% (limit: {self.max_ram_percent}%)"

        # Concurrency & active processes check
        active_recruits = len(self.recruited_agents)
        if active_recruits >= self.max_concurrency:
            return False, f"Maximum concurrency/recruitment limit reached ({self.max_concurrency})"

        return True, "OK"

    def recruit_agent(self, agent_id: str, role: str) -> None:
        self.recruited_agents[agent_id] = {
            "role": role,
            "recruited_at": time.time(),
            "last_active": time.time()
        }

    def release_agent(self, agent_id: str) -> None:
        if agent_id in self.recruited_agents:
            del self.recruited_agents[agent_id]

    def reclaim_idle_agents(self, agents: Dict[str, Any], idle_timeout: Optional[float] = None) -> list[str]:
        now = time.time()
        reclaimed = []
        ttl = idle_timeout if idle_timeout is not None else self.idle_reclamation_ttl
        for aid, a in list(agents.items()):
            # Do not reclaim core agents (PM, ARCH, ORCH)
            if "PM" in aid or "ARCH" in aid or "ORCH" in aid:
                continue
            if a.get("status") == "IDLE" and (now - a.get("last_active", now)) > ttl:
                reclaimed.append(aid)
        return reclaimed
