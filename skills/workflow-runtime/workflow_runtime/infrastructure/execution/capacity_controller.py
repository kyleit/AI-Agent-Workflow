# capacity_controller.py
from __future__ import annotations

import time
from typing import Any, cast

import psutil


class CapacityController:
    def __init__(self, max_cpu_percent: float = 80.0, max_ram_percent: float = 80.0, max_concurrency: int = 4) -> None:
        self.max_cpu_percent = max_cpu_percent
        self.max_ram_percent = max_ram_percent
        self.max_concurrency = max_concurrency
        self.recruited_agents: dict[str, dict[str, Any]] = {}
        self.idle_reclamation_ttl = 10.0

    def get_hardware_status(self) -> dict[str, Any]:
        try:
            cpu = float(psutil.cpu_percent(interval=None))
            virtual_mem = psutil.virtual_memory()
            ram = float(virtual_mem.percent)
            available_ram_gb = float(virtual_mem.available / (1024 ** 3))
        except Exception:
            cpu = 0.0
            ram = 0.0
            available_ram_gb = 8.0

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
        cpu = float(cast(float, status["cpu_utilization"]))
        ram = float(cast(float, status["ram_utilization"]))
        pressure = str(status["memory_pressure"])

        if cpu > self.max_cpu_percent or ram > self.max_ram_percent or pressure == "high":
            return 1
        elif cpu > 60.0 or ram > 70.0 or pressure == "medium":
            return min(2, self.max_concurrency)
        elif cpu > 40.0:
            return min(3, self.max_concurrency)
        return self.max_concurrency

    def can_recruit(self, agent_role: str, workload_size: int) -> tuple[bool, str]:
        status = self.get_hardware_status()
        cpu = float(cast(float, status["cpu_utilization"]))
        ram = float(cast(float, status["ram_utilization"]))

        if cpu > self.max_cpu_percent:
            return False, f"CPU usage is {cpu}% (limit: {self.max_cpu_percent}%)"
        if ram > self.max_ram_percent:
            return False, f"RAM usage is {ram}% (limit: {self.max_ram_percent}%)"

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

    def reclaim_idle_agents(self, agents: dict[str, Any], idle_timeout: float | None = None) -> list[str]:
        now = time.time()
        reclaimed: list[str] = []
        ttl = idle_timeout if idle_timeout is not None else self.idle_reclamation_ttl
        for aid, a_raw in list(agents.items()):
            if "PM" in aid or "ARCH" in aid or "ORCH" in aid:
                continue
            a = cast(dict[str, Any], a_raw) if isinstance(a_raw, dict) else {}
            last_active = float(cast(float, a.get("last_active", now)))
            if a.get("status") == "IDLE" and (now - last_active) > ttl:
                reclaimed.append(aid)
        return reclaimed


__all__ = ["CapacityController"]
