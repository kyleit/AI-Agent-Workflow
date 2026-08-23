import re
from dataclasses import dataclass
from enum import Enum


class RoleCategory(Enum):
    CORE_OWNER = "CORE_OWNER"
    SPECIALIST = "SPECIALIST"


class PermissionLevel(Enum):
    READ = "READ"
    WRITE = "WRITE"
    EXECUTE = "EXECUTE"
    ADMIN = "ADMIN"


@dataclass(frozen=True)
class SystemPrompt:
    template_str: str
    version: str

    def render(self, context: dict[str, str]) -> str:
        res = self.template_str
        for k, v in context.items():
            res = res.replace(f"{{{k}}}", str(v))
        return res


@dataclass(frozen=True)
class ForbiddenAction:
    action_name: str
    reason: str

    def matches(self, command: str) -> bool:
        if not command:
            return False
        if self.action_name in command:
            return True
        try:
            return bool(re.search(self.action_name, command))
        except re.error:
            return False
