# multi_agent_runtime.py
class AgentRegistry:
    """
    FEAT-088: Multi-Agent Runtime & Agent Registry SDK
    Registers agents and routes handoffs.
    """
    def __init__(self):
        self.registry = {}

    def register_agent(self, agent_name: str, capabilities: list) -> None:
        self.registry[agent_name] = {
            "capabilities": capabilities,
            "status": "IDLE"
        }

    def handoff(self, from_agent: str, to_agent: str) -> bool:
        if from_agent in self.registry and to_agent in self.registry:
            self.registry[from_agent]["status"] = "IDLE"
            self.registry[to_agent]["status"] = "ACTIVE"
            return True
        return False
