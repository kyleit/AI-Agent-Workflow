from __future__ import annotations

from dataclasses import dataclass, field

from workflow_runtime.domain.agent.value_objects import (ForbiddenAction,
                                                         RoleCategory)
from workflow_runtime.domain.workflow.value_objects import RoleId


@dataclass
class Permission:
    name: str
    resource: str
    allowed_actions: list[str]

    def permits(self, action: str, target: str) -> bool:
        if action not in self.allowed_actions:
            return False
        if self.resource == "*" or self.resource == target:
            return True
        return target.startswith(self.resource)


@dataclass
class Role:
    role_id: RoleId
    name: str
    assigned_phase: str
    capabilities: list[str] = field(default_factory=list[str])
    category: RoleCategory = RoleCategory.SPECIALIST

    def can_execute_phase(self, phase_name: str) -> bool:
        return self.assigned_phase == "*" or self.assigned_phase == phase_name


@dataclass
class AgentDef:
    agent_id: str
    role_id: RoleId
    name: str
    description: str
    permissions: list[Permission] = field(default_factory=list[Permission])
    forbidden_actions: list[ForbiddenAction] = field(default_factory=list[ForbiddenAction])

    def has_permission(self, action: str, target: str) -> bool:
        for forbidden in self.forbidden_actions:
            if forbidden.matches(action) or forbidden.matches(target):
                return False
        return any(p.permits(action, target) for p in self.permissions)

    def is_core_owner(self) -> bool:
        core_owners = {"planner", "architect", "coder", "reviewer", "release-manager"}
        return str(self.role_id) in core_owners


__all__ = [
    "Permission",
    "Role",
    "AgentDef",
]
