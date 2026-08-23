from typing import Protocol

from workflow_runtime.domain.agent.entities import AgentDef
from workflow_runtime.domain.workflow.value_objects import RoleId


class IAgentRepository(Protocol):
    def get_agent(self, agent_id: str) -> AgentDef:
        ...

    def find_by_role(self, role_id: RoleId) -> list[AgentDef]:
        ...

    def save_agent(self, agent: AgentDef) -> None:
        ...
